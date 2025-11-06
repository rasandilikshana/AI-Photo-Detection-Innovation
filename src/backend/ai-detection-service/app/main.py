"""
A.V.A.R. AI Detection Service - Main Application
Forensic analysis service for detecting AI-generated images
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import logging
from datetime import datetime
import uuid

from app.services.layer1_metadata import MetadataAnalyzer
from app.services.layer2_fingerprint import DigitalFingerprintAnalyzer
from app.services.layer3_api import ThirdPartyAPIVerifier
from app.services.raw_jpg_linkage import RAWJPGLinkageAnalyzer
from app.utils.file_handler import FileHandler
from app.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="A.V.A.R. AI Detection Service",
    description="Forensic analysis service for detecting AI-generated synthetic images",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
file_handler = FileHandler()


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "service": "A.V.A.R. AI Detection Service",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "analyze": "/api/v1/analyze"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for container orchestration"""
    return HealthResponse(
        status="healthy",
        service="ai-detection-service",
        timestamp=datetime.utcnow()
    )


@app.post("/api/v1/analyze", response_model=AnalysisResult)
async def analyze_submission(
    jpg_file: UploadFile = File(..., description="JPG submission file"),
    raw_file: Optional[UploadFile] = File(None, description="RAW file (optional but recommended)"),
    background_tasks: BackgroundTasks = None
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
        if not jpg_file.filename.lower().endswith(('.jpg', '.jpeg')):
            raise HTTPException(status_code=400, detail="JPG file must be .jpg or .jpeg")

        if raw_file and not file_handler.is_valid_raw_extension(raw_file.filename):
            raise HTTPException(status_code=400, detail="Invalid RAW file format")

        # Save uploaded files temporarily
        jpg_path = await file_handler.save_upload(jpg_file, submission_id, "jpg")
        raw_path = await file_handler.save_upload(raw_file, submission_id, "raw") if raw_file else None

        flags = []
        verdict = "AUTHENTIC"
        confidence_score = 1.0

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

            return AnalysisResult(
                submission_id=submission_id,
                timestamp=datetime.utcnow(),
                verdict=verdict,
                confidence_score=confidence_score,
                layer1_result=layer1_result,
                layer2_result=None,
                layer3_result=None,
                raw_jpg_linkage=None,
                flags=flags,
                processing_time_ms=processing_time
            )

        # === RAW-JPG LINKAGE ANALYSIS ===
        raw_jpg_linkage = None
        if raw_path:
            logger.info(f"[{submission_id}] Running RAW-JPG Linkage Analysis")
            raw_jpg_linkage = await linkage_analyzer.analyze_linkage(raw_path, jpg_path)

            if raw_jpg_linkage["verdict"] == "REJECT":
                verdict = "REJECT"
                confidence_score = 0.0
                flags.append("RAW-JPG mismatch detected - files are not linked")

                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                if background_tasks:
                    background_tasks.add_task(file_handler.cleanup_files, jpg_path, raw_path)

                return AnalysisResult(
                    submission_id=submission_id,
                    timestamp=datetime.utcnow(),
                    verdict=verdict,
                    confidence_score=confidence_score,
                    layer1_result=layer1_result,
                    layer2_result=None,
                    layer3_result=None,
                    raw_jpg_linkage=raw_jpg_linkage,
                    flags=flags,
                    processing_time_ms=processing_time
                )

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
        layer3_result = None
        if verdict == "QUARANTINE":
            logger.info(f"[{submission_id}] Running Layer 3: Third-Party API Verification")
            layer3_result = await api_verifier.verify(jpg_path)

            if layer3_result["verdict"] == "REJECT":
                verdict = "REJECT"
                confidence_score = layer3_result["confidence"]
                flags.extend(layer3_result.get("flags", []))
            elif layer3_result["verdict"] == "AUTHENTIC":
                verdict = "AUTHENTIC"
                confidence_score = layer3_result["confidence"]

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
            flags=flags,
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"[{submission_id}] Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/v1/analyze/metadata-only")
async def analyze_metadata_only(
    jpg_file: UploadFile = File(..., description="JPG submission file")
):
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
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
