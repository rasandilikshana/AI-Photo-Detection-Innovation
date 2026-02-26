"""
Submission management routes
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import aiofiles
import httpx
import os
from pathlib import Path

from app.database import get_db, AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.competition import Competition, CompetitionStatus
from app.models.submission import Submission, SubmissionStatus, VerificationVerdict
from app.schemas import SubmissionResponse, MessageResponse
from app.utils.auth import get_current_user
from app.utils.security import validate_file_extension, sanitize_filename
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def path_to_url(file_path: Optional[str]) -> Optional[str]:
    """Convert a local file path to a web-accessible URL"""
    if not file_path:
        return None
    # Extract just the filename from the path
    filename = os.path.basename(file_path)
    return f"/uploads/{filename}"

# AI Detection Service URL
AI_DETECTION_SERVICE_URL = os.getenv("AI_DETECTION_SERVICE_URL", "http://localhost:8001")


async def integrate_camera_reputation(
    submission_id: int,
    submission: Submission,
    jpg_path: str,
    db: AsyncSession
):
    """
    Integrate camera reputation system after AI analysis completes.

    Steps:
    1. Extract PRNU fingerprint
    2. Calculate trust score
    3. Apply trust boost
    4. Detect fraud
    5. Update camera profile
    """
    from app.services import PRNUExtractor, CameraReputationManager

    logger.info(f"[Submission {submission_id}] Integrating camera reputation...")

    # 1. Extract PRNU fingerprint
    extractor = PRNUExtractor()
    prnu_result = await extractor.extract_prnu_fingerprint(
        jpg_path,
        submission.camera_make,
        submission.camera_model
    )

    if not prnu_result["valid"]:
        logger.warning(f"[Submission {submission_id}] PRNU fingerprint invalid (energy too low)")
        return

    # 2. Store fingerprint and calculate trust score
    manager = CameraReputationManager(db)

    capture_context = {
        "iso": submission.iso,
        "aperture": submission.aperture,
        "shutter_speed": submission.shutter_speed,
        "capture_date": submission.capture_date,
    }

    fingerprint = await manager.store_fingerprint(
        submission_id=submission_id,
        prnu_data=prnu_result,
        camera_make=submission.camera_make,
        camera_model=submission.camera_model,
        user_id=submission.user_id,
        capture_context=capture_context
    )

    # 3. Calculate trust score
    trust_result = await manager.calculate_trust_score(
        prnu_result["pattern"],
        submission.camera_make,
        submission.camera_model,
        submission.user_id
    )

    # 4. Apply trust boost to verification confidence
    original_confidence = submission.verification_confidence
    submission.verification_confidence += trust_result["boost"]
    submission.verification_confidence = min(1.0, max(0.0, submission.verification_confidence))

    # 5. Update submission with camera reputation data
    submission.prnu_fingerprint_id = fingerprint.id
    submission.prnu_extracted_energy = prnu_result["energy"]
    submission.camera_trust_score = trust_result["trust_score"]

    logger.info(
        f"[Submission {submission_id}] Camera reputation applied: "
        f"Trust={trust_result['trust_score']:.2f}, "
        f"Boost={trust_result['boost']:+.2%}, "
        f"Confidence={original_confidence:.2%} → {submission.verification_confidence:.2%}"
    )

    # 6. Detect fraud
    fraud_result = await manager.detect_camera_fraud(
        submission_id,
        prnu_result["pattern"],
        submission.camera_make,
        submission.camera_model,
        submission.user_id
    )

    if fraud_result["fraud_likelihood"] > 0.7:
        logger.warning(
            f"[Submission {submission_id}] HIGH FRAUD RISK DETECTED: "
            f"{fraud_result['fraud_likelihood']:.1%} - {fraud_result['explanation']}"
        )
        submission.status = SubmissionStatus.REJECTED
        submission.rejection_reason = f"Camera fraud detected: {fraud_result['explanation']}"
    elif fraud_result["fraud_likelihood"] > 0.4:
        logger.info(
            f"[Submission {submission_id}] Moderate fraud risk: "
            f"{fraud_result['fraud_likelihood']:.1%}"
        )
        submission.verification_verdict = VerificationVerdict.NEEDS_REVIEW

    # 7. Update camera profile statistics
    await manager.update_profile_stats(
        submission.camera_make,
        submission.camera_model,
        str(submission.verification_verdict.value) if submission.verification_verdict else "pending",
        prnu_result["energy"]
    )

    await db.commit()
    logger.info(f"[Submission {submission_id}] Camera reputation integration complete")


async def run_ai_analysis(submission_id: int, jpg_path: str, raw_path: Optional[str]):
    """
    Background task to run AI detection analysis on a submission.
    Updates the submission with verification results.
    """
    logger.info(f"[Submission {submission_id}] Starting AI analysis...")

    try:
        async with AsyncSessionLocal() as db:
            # Get submission
            result = await db.execute(
                select(Submission).where(Submission.id == submission_id)
            )
            submission = result.scalar_one_or_none()

            if not submission:
                logger.error(f"[Submission {submission_id}] Submission not found")
                return

            # Update status to ANALYZING
            submission.status = SubmissionStatus.ANALYZING
            await db.commit()

            # Prepare files for AI Detection Service
            files = {}

            # Open JPG file
            with open(jpg_path, 'rb') as jpg_file:
                files['jpg_file'] = (os.path.basename(jpg_path), jpg_file.read(), 'image/jpeg')

            # Open RAW file if provided
            if raw_path and os.path.exists(raw_path):
                with open(raw_path, 'rb') as raw_file:
                    files['raw_file'] = (os.path.basename(raw_path), raw_file.read(), 'application/octet-stream')

            # Call AI Detection Service
            logger.info(f"[Submission {submission_id}] Calling AI Detection Service at {AI_DETECTION_SERVICE_URL}")

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{AI_DETECTION_SERVICE_URL}/api/v1/analyze",
                    files=files
                )

                if response.status_code == 200:
                    ai_result = response.json()
                    logger.info(f"[Submission {submission_id}] AI Analysis complete: {ai_result['verdict']}")

                    # Map AI verdict to submission status and verification
                    verdict_map = {
                        "AUTHENTIC": (SubmissionStatus.APPROVED, VerificationVerdict.AUTHENTIC),
                        "REJECT": (SubmissionStatus.REJECTED, VerificationVerdict.AI_GENERATED),
                        "QUARANTINE": (SubmissionStatus.PENDING, VerificationVerdict.SUSPICIOUS),
                    }

                    new_status, verification_verdict = verdict_map.get(
                        ai_result['verdict'],
                        (SubmissionStatus.PENDING, VerificationVerdict.NEEDS_REVIEW)
                    )

                    # Update submission with results
                    submission.status = new_status
                    submission.verification_verdict = verification_verdict
                    submission.verification_confidence = ai_result.get('confidence_score', 0.0)
                    submission.verification_details = ai_result
                    submission.verification_timestamp = ai_result.get('timestamp', '')

                    # Extract camera info from metadata if available
                    layer1 = ai_result.get('layer1_result', {})
                    if layer1:
                        metadata = layer1.get('metadata', {})
                        submission.camera_make = str(metadata.get('Make', '') or '')
                        submission.camera_model = str(metadata.get('Model', '') or '')
                        # ISO should be integer, others should be strings
                        iso_val = metadata.get('ISO')
                        submission.iso = int(iso_val) if iso_val and str(iso_val).isdigit() else None
                        submission.aperture = str(metadata.get('FNumber', '') or '')
                        submission.shutter_speed = str(metadata.get('ExposureTime', '') or '')
                        submission.capture_date = str(metadata.get('DateTimeOriginal', '') or '')

                    await db.commit()
                    logger.info(f"[Submission {submission_id}] Updated with verdict: {verification_verdict}")

                    # === NEW: Camera Reputation Integration (v2.0) ===
                    if submission.camera_make and submission.camera_model and new_status == SubmissionStatus.APPROVED:
                        try:
                            await integrate_camera_reputation(submission_id, submission, jpg_path, db)
                        except Exception as rep_err:
                            logger.error(f"[Submission {submission_id}] Camera reputation integration failed: {rep_err}")
                            # Don't fail submission if reputation fails

                else:
                    # Extract error message from response
                    try:
                        error_detail = response.json().get('detail', 'Unknown error')
                    except Exception:
                        error_detail = response.text or 'Unknown error'

                    logger.error(f"[Submission {submission_id}] AI Detection failed: {response.status_code} - {error_detail}")
                    submission.status = SubmissionStatus.PENDING
                    submission.verification_verdict = VerificationVerdict.NEEDS_REVIEW
                    submission.analysis_error = f"AI Analysis failed: {error_detail}"
                    await db.commit()

    except Exception as e:
        logger.error(f"[Submission {submission_id}] AI analysis error: {str(e)}", exc_info=True)
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Submission).where(Submission.id == submission_id)
                )
                submission = result.scalar_one_or_none()
                if submission:
                    submission.status = SubmissionStatus.PENDING
                    submission.verification_verdict = VerificationVerdict.NEEDS_REVIEW
                    submission.analysis_error = f"Analysis error: {str(e)}"
                    await db.commit()
        except Exception as db_err:
            logger.error(f"[Submission {submission_id}] Failed to update status: {db_err}")


@router.post("", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    competition_id: int = Form(...),
    description: Optional[str] = Form(None),
    jpg_file: UploadFile = File(...),
    raw_file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a photo to a competition

    - **title**: Submission title
    - **competition_id**: ID of the competition
    - **description**: Optional description
    - **jpg_file**: JPG/JPEG image file (required)
    - **raw_file**: RAW image file (required if competition requires it)
    """
    # Get competition
    result = await db.execute(
        select(Competition).where(Competition.id == competition_id)
    )
    competition = result.scalar_one_or_none()

    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found",
        )

    # Check if competition is accepting submissions
    if not competition.is_accepting_submissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Competition is not accepting submissions at this time",
        )

    # Check if user has reached submission limit (using COUNT for efficiency)
    count_result = await db.execute(
        select(func.count(Submission.id)).where(
            Submission.user_id == current_user.id,
            Submission.competition_id == competition_id,
        )
    )
    user_submission_count = count_result.scalar() or 0

    if user_submission_count >= competition.max_submissions_per_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {competition.max_submissions_per_user} submissions per user reached",
        )

    # Validate JPG file
    if not validate_file_extension(jpg_file.filename, ['jpg', 'jpeg']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JPG file format",
        )

    # Check if RAW file is required
    if competition.require_raw_files and not raw_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RAW file is required for this competition",
        )

    # Validate RAW file extension if provided
    ALLOWED_RAW_EXTENSIONS = ['cr2', 'cr3', 'nef', 'arw', 'dng', 'raf', 'orf', 'rw2', 'pef', 'srw', 'raw']
    if raw_file:
        if not validate_file_extension(raw_file.filename, ALLOWED_RAW_EXTENSIONS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid RAW file format. Supported formats: {', '.join([ext.upper() for ext in ALLOWED_RAW_EXTENSIONS])}",
            )

    # Validate file sizes before saving
    jpg_file.file.seek(0, 2)
    jpg_file_size = jpg_file.file.tell()
    jpg_file.file.seek(0)

    if jpg_file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"JPG file too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    raw_file_size = 0
    if raw_file:
        raw_file.file.seek(0, 2)
        raw_file_size = raw_file.file.tell()
        raw_file.file.seek(0)

        # Allow larger RAW files (4x JPG limit)
        if raw_file_size > settings.MAX_UPLOAD_SIZE_BYTES * 4:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"RAW file too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB * 4}MB",
            )

    # Save JPG file with error handling
    jpg_filename = sanitize_filename(jpg_file.filename)
    jpg_path = Path(settings.UPLOAD_DIR) / f"{current_user.id}_{competition_id}_{jpg_filename}"

    try:
        async with aiofiles.open(jpg_path, 'wb') as f:
            content = await jpg_file.read()
            await f.write(content)
    except IOError as e:
        logger.error(f"Failed to save JPG file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save JPG file",
        )

    # Save RAW file if provided
    raw_path = None

    if raw_file:
        raw_filename = sanitize_filename(raw_file.filename)
        raw_path = Path(settings.UPLOAD_DIR) / f"{current_user.id}_{competition_id}_{raw_filename}"

        try:
            async with aiofiles.open(raw_path, 'wb') as f:
                content = await raw_file.read()
                await f.write(content)
        except IOError as e:
            # Clean up JPG file if RAW save fails
            try:
                os.remove(jpg_path)
            except OSError:
                pass
            logger.error(f"Failed to save RAW file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save RAW file",
            )

    # Create submission
    new_submission = Submission(
        title=title,
        description=description,
        jpg_file_url=str(jpg_path),
        jpg_file_size=jpg_file_size,
        raw_file_url=str(raw_path) if raw_path else None,
        raw_file_size=raw_file_size if raw_file_size > 0 else None,
        status=SubmissionStatus.PENDING,
        user_id=current_user.id,
        competition_id=competition_id,
    )

    db.add(new_submission)
    await db.commit()
    await db.refresh(new_submission)

    # Trigger AI analysis in background
    logger.info(f"[Submission {new_submission.id}] Triggering AI analysis in background")
    background_tasks.add_task(
        run_ai_analysis,
        new_submission.id,
        str(jpg_path),
        str(raw_path) if raw_path else None
    )

    # Re-query with competition relationship loaded to avoid greenlet error
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.competition))
        .where(Submission.id == new_submission.id)
    )
    submission_with_competition = result.scalar_one()

    return SubmissionResponse(
        id=submission_with_competition.id,
        title=submission_with_competition.title,
        description=submission_with_competition.description,
        jpg_file_url=path_to_url(submission_with_competition.jpg_file_url) or "",
        raw_file_url=path_to_url(submission_with_competition.raw_file_url),
        status=submission_with_competition.status,
        verification_verdict=submission_with_competition.verification_verdict,
        verification_confidence=submission_with_competition.verification_confidence,
        verification_details=submission_with_competition.verification_details,
        verification_timestamp=submission_with_competition.verification_timestamp,
        camera_make=submission_with_competition.camera_make,
        camera_model=submission_with_competition.camera_model,
        iso=submission_with_competition.iso,
        aperture=submission_with_competition.aperture,
        shutter_speed=submission_with_competition.shutter_speed,
        capture_date=submission_with_competition.capture_date,
        total_score=submission_with_competition.total_score,
        score_count=submission_with_competition.score_count,
        user_id=submission_with_competition.user_id,
        competition_id=submission_with_competition.competition_id,
        competition=submission_with_competition.competition,
        created_at=submission_with_competition.created_at,
        # V2.0 Camera Reputation fields
        camera_trust_score=submission_with_competition.camera_trust_score,
        prnu_fingerprint_id=submission_with_competition.prnu_fingerprint_id,
        prnu_extracted_energy=submission_with_competition.prnu_extracted_energy,
    )


@router.get("", response_model=List[SubmissionResponse])
async def list_submissions(
    competition_id: Optional[int] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List submissions

    - **competition_id**: Filter by competition (optional)
    - **user_id**: Filter by user (optional)
    - **skip**: Pagination offset
    - **limit**: Maximum results
    """
    query = select(Submission).options(selectinload(Submission.competition))

    if competition_id:
        query = query.where(Submission.competition_id == competition_id)

    if user_id:
        query = query.where(Submission.user_id == user_id)

    query = query.offset(skip).limit(limit).order_by(Submission.created_at.desc())

    result = await db.execute(query)
    submissions = result.scalars().all()

    # Convert file paths to URLs and build response
    response_list = []
    for sub in submissions:
        response_list.append(SubmissionResponse(
            id=sub.id,
            title=sub.title,
            description=sub.description,
            jpg_file_url=path_to_url(sub.jpg_file_url) or "",
            raw_file_url=path_to_url(sub.raw_file_url),
            status=sub.status,
            verification_verdict=sub.verification_verdict,
            verification_confidence=sub.verification_confidence,
            verification_details=sub.verification_details,
            verification_timestamp=sub.verification_timestamp,
            camera_make=sub.camera_make,
            camera_model=sub.camera_model,
            iso=sub.iso,
            aperture=sub.aperture,
            shutter_speed=sub.shutter_speed,
            capture_date=sub.capture_date,
            total_score=sub.total_score,
            score_count=sub.score_count,
            user_id=sub.user_id,
            competition_id=sub.competition_id,
            competition=sub.competition,
            created_at=sub.created_at,
            # Review/error fields
            analysis_error=sub.analysis_error,
            rejection_reason=sub.rejection_reason,
            reviewed_by=sub.reviewed_by,
            reviewed_at=sub.reviewed_at,
            # V2.0 Camera Reputation fields
            camera_trust_score=sub.camera_trust_score,
            prnu_fingerprint_id=sub.prnu_fingerprint_id,
            prnu_extracted_energy=sub.prnu_extracted_energy,
        ))

    return response_list


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get submission by ID
    """
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.competition))
        .where(Submission.id == submission_id)
    )
    sub = result.scalar_one_or_none()

    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    return SubmissionResponse(
        id=sub.id,
        title=sub.title,
        description=sub.description,
        jpg_file_url=path_to_url(sub.jpg_file_url) or "",
        raw_file_url=path_to_url(sub.raw_file_url),
        status=sub.status,
        verification_verdict=sub.verification_verdict,
        verification_confidence=sub.verification_confidence,
        verification_details=sub.verification_details,
        verification_timestamp=sub.verification_timestamp,
        camera_make=sub.camera_make,
        camera_model=sub.camera_model,
        iso=sub.iso,
        aperture=sub.aperture,
        shutter_speed=sub.shutter_speed,
        capture_date=sub.capture_date,
        total_score=sub.total_score,
        score_count=sub.score_count,
        user_id=sub.user_id,
        competition_id=sub.competition_id,
        competition=sub.competition,
        created_at=sub.created_at,
        # Review/error fields
        analysis_error=sub.analysis_error,
        rejection_reason=sub.rejection_reason,
        reviewed_by=sub.reviewed_by,
        reviewed_at=sub.reviewed_at,
        # V2.0 Camera Reputation fields
        camera_trust_score=sub.camera_trust_score,
        prnu_fingerprint_id=sub.prnu_fingerprint_id,
        prnu_extracted_energy=sub.prnu_extracted_energy,
    )


@router.delete("/{submission_id}", response_model=MessageResponse)
async def delete_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete submission

    Only the submission owner can delete it (or admin)
    """
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    # Check permissions - use proper enum comparison
    if submission.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this submission",
        )

    # Delete files with proper error handling
    files_to_delete = []
    if submission.jpg_file_url:
        files_to_delete.append(submission.jpg_file_url)
    if submission.raw_file_url:
        files_to_delete.append(submission.raw_file_url)

    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        except OSError as e:
            # Log error but continue with database deletion
            logger.error(f"Failed to delete file {file_path}: {e}")

    # Delete from database
    try:
        await db.delete(submission)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to delete submission from database: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete submission",
        )

    return MessageResponse(message="Submission deleted successfully")
