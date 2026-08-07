"""
A.V.A.R. AI Detection Service - Main Application
Forensic analysis service for detecting AI-generated images
"""

import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional

from app.services.authenticity_score import AuthenticityScorer
from app.services.layer1_metadata import MetadataAnalyzer
from app.services.layer2_fingerprint import DigitalFingerprintAnalyzer
from app.services.layer3_api import ThirdPartyAPIVerifier
from app.services.raw_jpg_linkage import RAWJPGLinkageAnalyzer
from app.utils.file_handler import FileHandler
from app.utils.logger import setup_logger
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Initialize logger
logger = setup_logger(__name__)

# Configuration from environment
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8080"
)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def get_cors_origins() -> List[str]:
    """Parse CORS origins from environment - no wildcards allowed"""
    origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
    return [o for o in origins if o != "*"]

# Initialize FastAPI app
app = FastAPI(
    title="A.V.A.R. AI Detection Service",
    description="Forensic analysis service for detecting AI-generated synthetic images",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - properly configured with whitelist
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)


# Response Models
class AnalysisResult(BaseModel):
    submission_id: str
    timestamp: datetime
    verdict: str  # "AUTHENTIC", "REJECT", "QUARANTINE"
    confidence_score: float
    layer1_result: dict
    layer2_result: Optional[dict]
    layer3_result: Optional[dict]
    raw_jpg_linkage: Optional[dict]
    # Weighted 0-100 aggregation of every signal, with the review band and the
    # per-signal breakdown a judge reads. Replaces confidence_score as the number
    # that actually decides the verdict; confidence_score is kept as score/100 so
    # existing consumers keep working.
    authenticity: Optional[dict]
    flags: List[str]
    processing_time_ms: float


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime


# Initialize services
metadata_analyzer = MetadataAnalyzer()
fingerprint_analyzer = DigitalFingerprintAnalyzer()
api_verifier = ThirdPartyAPIVerifier()
linkage_analyzer = RAWJPGLinkageAnalyzer()
scorer = AuthenticityScorer()
file_handler = FileHandler()


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "service": "A.V.A.R. AI Detection Service",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {"health": "/health", "docs": "/docs", "analyze": "/api/v1/analyze"},
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for container orchestration"""
    return HealthResponse(status="healthy", service="ai-detection-service", timestamp=datetime.utcnow())


@app.post("/api/v1/analyze", response_model=AnalysisResult)
async def analyze_submission(
    jpg_file: UploadFile = File(..., description="JPG submission file"),
    raw_file: Optional[UploadFile] = File(None, description="RAW file (optional but recommended)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Main analysis endpoint - Multi-layered AI detection pipeline

    Pipeline:
    1. Layer 1: Metadata Analysis (Fast)
    2. RAW-JPG Linkage (If RAW provided)
    3. Layer 2: Digital Fingerprint Analysis (Medium)
    4. Layer 3: Third-Party API Verification (Slow, if needed)

    Returns verdict: AUTHENTIC, REJECT, or QUARANTINE
    """
    start_time = datetime.utcnow()
    submission_id = str(uuid.uuid4())

    logger.info(f"Starting analysis for submission {submission_id}")

    try:
        # Validate file types
        if not jpg_file.filename.lower().endswith((".jpg", ".jpeg")):
            raise HTTPException(status_code=400, detail="JPG file must be .jpg or .jpeg")

        if raw_file and not file_handler.is_valid_raw_extension(raw_file.filename):
            raise HTTPException(status_code=400, detail="Invalid RAW file format")

        # Validate file size
        jpg_file.file.seek(0, 2)  # Seek to end
        jpg_size = jpg_file.file.tell()
        jpg_file.file.seek(0)  # Reset to beginning

        if jpg_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"JPG file too large. Maximum size is {MAX_FILE_SIZE_MB}MB"
            )

        if raw_file:
            raw_file.file.seek(0, 2)
            raw_size = raw_file.file.tell()
            raw_file.file.seek(0)

            # RAW files can be larger, allow 200MB
            if raw_size > MAX_FILE_SIZE_BYTES * 4:
                raise HTTPException(
                    status_code=413,
                    detail=f"RAW file too large. Maximum size is {MAX_FILE_SIZE_MB * 4}MB"
                )

        # Save uploaded files temporarily
        jpg_path = await file_handler.save_upload(jpg_file, submission_id, "jpg")
        raw_path = await file_handler.save_upload(raw_file, submission_id, "raw") if raw_file else None

        flags = []
        verdict = "AUTHENTIC"
        confidence_score = 1.0
        raw_linkage_suspicious = False  # Track if RAW-JPG linkage is suspicious (spoofing detection)
        layer1_suspicious = False  # Track metadata transplant/laundering indicators

        # === LAYER 1: METADATA ANALYSIS ===
        logger.info(f"[{submission_id}] Running Layer 1: Metadata Analysis")
        layer1_result = await metadata_analyzer.analyze(jpg_path, raw_path)

        if layer1_result["verdict"] == "REJECT":
            verdict = "REJECT"
            confidence_score = layer1_result["confidence"]
            flags.extend(layer1_result.get("flags", []))

            # Early rejection - no need for further analysis
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Cleanup files in background
            if background_tasks:
                background_tasks.add_task(file_handler.cleanup_files, jpg_path, raw_path)

            # Score even on the early return so the judge panel always has a number
            # to show. With only Layer 1 available the scorer reports which signals
            # were not evaluable, so the display stays honest about what was checked.
            authenticity = scorer.score(layer1_result, None, None, None)

            return AnalysisResult(
                submission_id=submission_id,
                timestamp=datetime.utcnow(),
                verdict=verdict,
                confidence_score=confidence_score,
                layer1_result=layer1_result,
                layer2_result=None,
                layer3_result=None,
                raw_jpg_linkage=None,
                authenticity=authenticity,
                flags=flags,
                processing_time_ms=processing_time,
            )

        elif layer1_result["verdict"] == "SUSPICIOUS":
            # Metadata forensics found transplant/laundering indicators — force
            # QUARANTINE so Layer 3 (third-party AI detection) gets to examine the pixels
            verdict = "QUARANTINE"
            layer1_suspicious = True
            confidence_score = min(confidence_score, layer1_result["confidence"])
            flags.extend(layer1_result.get("flags", []))
            logger.warning(f"[{submission_id}] Layer 1 SUSPICIOUS - escalating to quarantine")

        # === RAW-JPG LINKAGE ANALYSIS ===
        raw_jpg_linkage = None
        if raw_path:
            logger.info(f"[{submission_id}] Running RAW-JPG Linkage Analysis")
            raw_jpg_linkage = await linkage_analyzer.analyze_linkage(raw_path, jpg_path)

            if raw_jpg_linkage["verdict"] == "REJECT":
                # Do NOT auto-reject here. A linkage failure means either substitution
                # (fraud) or an edit our matcher could not follow (genuine). Let Layer 3
                # examine the pixels and decide — quarantine is the safe failure mode.
                raw_linkage_suspicious = True
                verdict = "QUARANTINE"
                confidence_score = 0.0
                flags.append("RAW-JPG mismatch detected - files do not appear to be linked")
                flags.extend(raw_jpg_linkage.get("flags", []))
                logger.warning(f"[{submission_id}] RAW-JPG linkage failed - escalating for pixel analysis")

            # SECURITY FIX: Handle SUSPICIOUS RAW linkage (metadata spoofing attack detection)
            # When metadata passes but RAW-JPG linkage is weak, this indicates possible spoofing
            elif raw_jpg_linkage["verdict"] == "SUSPICIOUS":
                raw_linkage_suspicious = True
                flags.append("SECURITY WARNING: RAW-JPG linkage weak despite valid metadata - possible spoofing attack")
                logger.warning(f"[{submission_id}] Suspicious RAW-JPG linkage detected - possible metadata spoofing")

                # Force QUARANTINE when RAW linkage is suspicious
                verdict = "QUARANTINE"
                # Significantly reduce confidence - RAW mismatch is a critical signal
                linkage_confidence = raw_jpg_linkage.get("confidence", 0.3)
                confidence_score = min(confidence_score * 0.5, linkage_confidence)

        # === LAYER 2: DIGITAL FINGERPRINT ANALYSIS ===
        logger.info(f"[{submission_id}] Running Layer 2: Digital Fingerprint Analysis")
        layer2_result = await fingerprint_analyzer.analyze(jpg_path, raw_path)

        if layer2_result["verdict"] == "REJECT":
            verdict = "REJECT"
            confidence_score = min(confidence_score, layer2_result["confidence"])
            flags.extend(layer2_result.get("flags", []))
        elif layer2_result["verdict"] == "SUSPICIOUS":
            verdict = "QUARANTINE"
            confidence_score = layer2_result["confidence"]
            flags.extend(layer2_result.get("flags", []))

        # === LAYER 3: THIRD-PARTY API VERIFICATION ===
        # Escalated for quarantined submissions, and additionally whenever the RAW is a
        # DNG. A DNG is the one RAW container an attacker can readily author, and a
        # fabricated one that is internally consistent with its JPEG passes every
        # metadata and linkage check by construction — that is exactly how production
        # submission 45 reached AUTHENTIC without this layer ever running. Sending those
        # pixels to a detector costs one API call and closes the blind spot.
        layer3_result = None
        raw_needs_pixel_review = layer1_result.get("raw_needs_pixel_review", False)
        if raw_needs_pixel_review and verdict != "QUARANTINE":
            logger.info(f"[{submission_id}] RAW is a DNG - escalating to Layer 3 for pixel analysis")

        if verdict == "QUARANTINE" or raw_needs_pixel_review:
            logger.info(f"[{submission_id}] Running Layer 3: Third-Party API Verification")
            layer3_result = await api_verifier.verify(jpg_path)

            if layer3_result["verdict"] == "REJECT":
                verdict = "REJECT"
                confidence_score = layer3_result["confidence"]
                flags.extend(layer3_result.get("flags", []))
            elif layer3_result["verdict"] == "AUTHENTIC":
                # SECURITY: If RAW linkage was suspicious or metadata transplant indicators
                # were found, don't upgrade to AUTHENTIC — spoofed provenance stays quarantined
                if raw_linkage_suspicious or layer1_suspicious:
                    verdict = "QUARANTINE"
                    confidence_score = min(confidence_score, 0.5)
                    reason = "suspicious RAW-JPG linkage" if raw_linkage_suspicious else "metadata transplant indicators"
                    flags.append(f"Verdict kept as QUARANTINE due to {reason}")
                    logger.warning(f"[{submission_id}] Prevented upgrade to AUTHENTIC due to {reason}")
                else:
                    verdict = "AUTHENTIC"
                    confidence_score = layer3_result["confidence"]

        # === AUTHENTICITY SCORE ===
        # Single weighted aggregation over every signal, replacing the per-layer
        # confidence_score overrides above. Those overrides made the final number
        # reflect whichever layer spoke last rather than the weight of evidence, and
        # made scores incomparable between submissions.
        #
        # The scorer also subsumes the old "final security check" that downgraded
        # AUTHENTIC when RAW linkage was suspicious: an unconfirmed critical signal is
        # capped into the judge-review band by CONFIRMED_FLOOR, so there is now one
        # source of truth instead of a score and a separate guard that could disagree.
        # An explicit REJECT from a layer stands -- a layer that positively identified
        # fraud is not outvoted by an average -- and the score is capped to match, so the
        # judge panel cannot show "84/100, approve" beside a status of REJECTED. That
        # happened on submission 27: Hive AI rejected it above 90% confidence, but
        # third_party carries only 5 of 100 points.
        layer_reject_reason = None
        if verdict == "REJECT":
            if (layer3_result or {}).get("verdict") == "REJECT":
                layer_reject_reason = "third-party detector identified generated content"
            elif (layer2_result or {}).get("verdict") == "REJECT":
                layer_reject_reason = "pixel forensics failed"
            else:
                layer_reject_reason = "a verification layer positively identified fraud"

        authenticity = scorer.score(
            layer1_result, layer2_result, layer3_result, raw_jpg_linkage,
            layer_reject_reason=layer_reject_reason,
        )

        if verdict != "REJECT":
            verdict = authenticity["verdict"]
        confidence_score = authenticity["score"] / 100.0

        flags.append(
            f"Authenticity score {authenticity['score']}/100 "
            f"(band {authenticity['band']}) - {authenticity['action']}"
        )
        if authenticity["missing"]:
            flags.append(
                "Signals not evaluable for this submission (excluded from the score rather "
                f"than counted against it): {', '.join(authenticity['missing'])}"
            )

        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(f"[{submission_id}] Analysis complete: {verdict} (confidence: {confidence_score:.2f})")

        # Cleanup files in background
        if background_tasks:
            background_tasks.add_task(file_handler.cleanup_files, jpg_path, raw_path)

        return AnalysisResult(
            submission_id=submission_id,
            timestamp=datetime.utcnow(),
            verdict=verdict,
            confidence_score=confidence_score,
            layer1_result=layer1_result,
            layer2_result=layer2_result,
            layer3_result=layer3_result,
            raw_jpg_linkage=raw_jpg_linkage,
            authenticity=authenticity,
            flags=flags,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"[{submission_id}] Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/v1/analyze/metadata-only")
async def analyze_metadata_only(jpg_file: UploadFile = File(..., description="JPG submission file")):
    """Quick metadata-only analysis (Layer 1 only)"""
    submission_id = str(uuid.uuid4())

    try:
        jpg_path = await file_handler.save_upload(jpg_file, submission_id, "jpg")
        result = await metadata_analyzer.analyze(jpg_path, None)
        await file_handler.cleanup_files(jpg_path)

        return result

    except Exception as e:
        logger.error(f"Metadata analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler - sanitize errors for production"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    # Don't expose internal error details in production
    error_detail = str(exc) if DEBUG else "An unexpected error occurred"
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": error_detail}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
