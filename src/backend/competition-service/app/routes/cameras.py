"""
Camera Reputation API Routes

Endpoints for camera PRNU fingerprinting, trust scoring, and fraud detection.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
import logging

from app.database import get_db
from app.models.user import User
from app.models import (
    CameraFingerprint,
    CameraTrustProfile,
    PRNUComparison,
    Submission,
)
from app.schemas import (
    CameraFingerprintResponse,
    CameraTrustProfileResponse,
    CameraComparisonResponse,
    TrustScoreResponse,
    FraudDetectionResponse,
    UserCameraHistoryResponse,
    MessageResponse,
)
from app.utils.auth import get_current_user
from app.services import PRNUExtractor, CameraReputationManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.post("/fingerprints/{submission_id}", response_model=CameraFingerprintResponse)
async def store_camera_fingerprint(
    submission_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Extract and store PRNU fingerprint for a submission.

    This endpoint is called after AI verification completes.
    PRNU extraction runs in background to avoid blocking.

    Returns:
        Stored fingerprint record
    """
    # Get submission
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # Check permissions (only submission owner, judges, or admins)
    if submission.user_id != current_user.id and current_user.role not in ["judge", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this submission"
        )

    # Check if fingerprint already exists
    existing = await db.execute(
        select(CameraFingerprint).where(
            CameraFingerprint.submission_id == submission_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fingerprint already exists for this submission"
        )

    # Extract PRNU (this is the heavy operation)
    extractor = PRNUExtractor()
    try:
        prnu_result = await extractor.extract_prnu_fingerprint(
            submission.jpg_file_url,
            submission.camera_make,
            submission.camera_model
        )
    except Exception as e:
        logger.error(f"PRNU extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PRNU extraction failed: {str(e)}"
        )

    # Store fingerprint
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

    # Calculate trust score
    trust_result = await manager.calculate_trust_score(
        prnu_result["pattern"],
        submission.camera_make,
        submission.camera_model,
        submission.user_id
    )

    # Update submission with fingerprint and trust score
    submission.prnu_fingerprint_id = fingerprint.id
    submission.prnu_extracted_energy = prnu_result["energy"]
    submission.camera_trust_score = trust_result["trust_score"]

    # Apply trust boost to verification confidence
    if submission.verification_confidence:
        submission.verification_confidence += trust_result["boost"]
        submission.verification_confidence = min(1.0, submission.verification_confidence)

    # Update camera profile (background task)
    background_tasks.add_task(
        manager.update_profile_stats,
        submission.camera_make,
        submission.camera_model,
        submission.verification_verdict or "pending",
        prnu_result["energy"]
    )

    await db.commit()
    await db.refresh(fingerprint)

    return fingerprint


@router.get("/trust-profile/{camera_make}/{camera_model}", response_model=CameraTrustProfileResponse)
async def get_camera_trust_profile(
    camera_make: str,
    camera_model: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get trust profile for a specific camera make/model.

    Returns aggregated statistics:
    - Total submissions
    - Authenticity rate
    - Rejection rate
    - Average trust score
    - PRNU pattern stability
    """
    result = await db.execute(
        select(CameraTrustProfile).where(
            and_(
                CameraTrustProfile.camera_make == camera_make,
                CameraTrustProfile.camera_model == camera_model
            )
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No profile found for {camera_make} {camera_model}"
        )

    return profile


@router.get("/user-cameras/{user_id}", response_model=List[UserCameraHistoryResponse])
async def get_user_camera_history(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's camera usage history.

    Returns list of cameras used with statistics.
    Users can only view their own history unless they're admin/judge.
    """
    # Check permissions
    if user_id != current_user.id and current_user.role not in ["judge", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's camera history"
        )

    # Query camera usage
    query = (
        select(
            CameraFingerprint.camera_make,
            CameraFingerprint.camera_model,
            func.count(CameraFingerprint.id).label("submission_count"),
            func.min(CameraFingerprint.created_at).label("first_used"),
            func.max(CameraFingerprint.created_at).label("last_used"),
            func.avg(CameraFingerprint.trust_boost_applied).label("avg_trust_score")
        )
        .where(CameraFingerprint.user_id == user_id)
        .group_by(CameraFingerprint.camera_make, CameraFingerprint.camera_model)
        .order_by(func.max(CameraFingerprint.created_at).desc())
    )

    result = await db.execute(query)
    cameras = []

    for row in result:
        cameras.append(UserCameraHistoryResponse(
            camera_make=row.camera_make,
            camera_model=row.camera_model,
            submission_count=row.submission_count,
            first_used=row.first_used,
            last_used=row.last_used,
            avg_trust_score=row.avg_trust_score or 0.5
        ))

    return cameras


@router.get("/comparison/{fingerprint1_id}/{fingerprint2_id}", response_model=CameraComparisonResponse)
async def compare_fingerprints(
    fingerprint1_id: int,
    fingerprint2_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compare two PRNU fingerprints directly.

    Admin/Judge only endpoint for forensic analysis.

    Returns:
        Similarity score and metrics
    """
    # Check permissions
    if current_user.role not in ["judge", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges and admins can compare fingerprints"
        )

    # Get fingerprints
    fp1 = await db.get(CameraFingerprint, fingerprint1_id)
    fp2 = await db.get(CameraFingerprint, fingerprint2_id)

    if not fp1 or not fp2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both fingerprints not found"
        )

    # Check if comparison already exists
    existing = await db.execute(
        select(PRNUComparison).where(
            and_(
                PRNUComparison.fingerprint1_id == fingerprint1_id,
                PRNUComparison.fingerprint2_id == fingerprint2_id
            )
        )
    )
    comparison_record = existing.scalar_one_or_none()

    if comparison_record:
        # Return cached result
        return CameraComparisonResponse(
            fingerprint1_id=fingerprint1_id,
            fingerprint2_id=fingerprint2_id,
            similarity_score=comparison_record.similarity_score,
            correlation=comparison_record.correlation_coefficient,
            distance_metric=comparison_record.distance_metric,
            same_camera_likely=comparison_record.same_camera
        )

    # Decompress patterns
    extractor = PRNUExtractor()
    pattern1 = extractor.decompress_pattern(fp1.prnu_signature, (512, 512))
    pattern2 = extractor.decompress_pattern(fp2.prnu_signature, (512, 512))

    # Compare
    comparison = await extractor.compare_patterns(pattern1, pattern2)

    # Store comparison
    same_camera = (fp1.camera_make == fp2.camera_make and fp1.camera_model == fp2.camera_model)
    same_user = (fp1.user_id == fp2.user_id)

    comparison_record = PRNUComparison(
        fingerprint1_id=fingerprint1_id,
        fingerprint2_id=fingerprint2_id,
        similarity_score=comparison["similarity_score"],
        distance_metric=comparison.get("distance_metric"),
        correlation_coefficient=comparison.get("correlation"),
        same_camera=same_camera,
        same_user=same_user,
        comparison_details=comparison
    )

    db.add(comparison_record)
    await db.commit()

    return CameraComparisonResponse(
        fingerprint1_id=fingerprint1_id,
        fingerprint2_id=fingerprint2_id,
        similarity_score=comparison["similarity_score"],
        correlation=comparison.get("correlation"),
        distance_metric=comparison.get("distance_metric"),
        same_camera_likely=comparison.get("same_camera_likely", False)
    )


@router.get("/fraud-check/{submission_id}", response_model=FraudDetectionResponse)
async def check_camera_fraud(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check submission for camera fraud.

    Detects:
    - PRNU pattern mismatch
    - Energy deviation
    - Cross-camera fraud (same PRNU, different EXIF)

    Admin/Judge only endpoint.

    Returns:
        Fraud likelihood, verdict, and recommendation
    """
    # Check permissions
    if current_user.role not in ["judge", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges and admins can check for fraud"
        )

    # Get submission
    submission = await db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # Get fingerprint
    if not submission.prnu_fingerprint_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission has no PRNU fingerprint"
        )

    fingerprint = await db.get(CameraFingerprint, submission.prnu_fingerprint_id)
    if not fingerprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fingerprint record not found"
        )

    # Decompress pattern
    extractor = PRNUExtractor()
    pattern = extractor.decompress_pattern(fingerprint.prnu_signature, (512, 512))

    # Run fraud detection
    manager = CameraReputationManager(db)
    fraud_result = await manager.detect_camera_fraud(
        submission_id,
        pattern,
        submission.camera_make,
        submission.camera_model,
        submission.user_id
    )

    return FraudDetectionResponse(**fraud_result)


@router.get("/fingerprint/{submission_id}", response_model=CameraFingerprintResponse)
async def get_submission_fingerprint(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get PRNU fingerprint for a submission.

    Returns fingerprint metadata (not the actual pattern).
    """
    # Get submission to check permissions
    submission = await db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # Check permissions
    if submission.user_id != current_user.id and current_user.role not in ["judge", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this submission"
        )

    # Get fingerprint
    result = await db.execute(
        select(CameraFingerprint).where(
            CameraFingerprint.submission_id == submission_id
        )
    )
    fingerprint = result.scalar_one_or_none()

    if not fingerprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No fingerprint found for this submission"
        )

    return fingerprint


@router.get("/profiles", response_model=List[CameraTrustProfileResponse])
async def list_camera_profiles(
    skip: int = 0,
    limit: int = 50,
    min_submissions: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """
    List camera trust profiles.

    Returns profiles sorted by authenticity rate.
    Useful for identifying most trusted cameras.

    Query Parameters:
        skip: Pagination offset
        limit: Max results (max 100)
        min_submissions: Minimum submissions to include (default 5)
    """
    limit = min(limit, 100)  # Cap at 100

    query = (
        select(CameraTrustProfile)
        .where(CameraTrustProfile.total_submissions >= min_submissions)
        .order_by(CameraTrustProfile.avg_trust_score.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    profiles = result.scalars().all()

    return profiles
