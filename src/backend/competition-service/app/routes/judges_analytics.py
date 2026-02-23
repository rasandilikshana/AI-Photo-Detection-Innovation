"""
Judge Analytics API Routes

Endpoints for judge consensus analysis, bias detection, and credential sharing monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
import logging

from app.database import get_db
from app.models.user import User, UserRole
from app.models import (
    JudgeScoringProfile,
    JudgeConsensusAnalysis,
    CredentialSharingDetection,
    Submission,
)
from app.schemas import (
    JudgeScoringProfileResponse,
    JudgeConsensusAnalysisResponse,
    CredentialSharingDetectionResponse,
    MessageResponse,
)
from app.utils.auth import get_current_user
from app.services import JudgeConsensusAnalyzer, CredentialSharingDetector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/judges-analytics", tags=["Judge Analytics"])


@router.get("/profile/{judge_id}/{competition_id}", response_model=JudgeScoringProfileResponse)
async def get_judge_scoring_profile(
    judge_id: int,
    competition_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get judge's scoring profile for a competition.

    Shows:
    - Average score given
    - Bias score (Z-score)
    - Consistency score
    - Score distribution

    Admin/Judge only (judges can view their own profile).
    """
    # Check permissions
    if current_user.role not in ["admin"] and current_user.id != judge_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view other judges' profiles"
        )

    # Get profile
    result = await db.execute(
        select(JudgeScoringProfile).where(
            and_(
                JudgeScoringProfile.judge_id == judge_id,
                JudgeScoringProfile.competition_id == competition_id
            )
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        # Build profile if doesn't exist
        analyzer = JudgeConsensusAnalyzer(db)
        profile_data = await analyzer.build_judge_profile(judge_id, competition_id)

        if profile_data["submission_count"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scoring data found for this judge"
            )

        # Store profile
        await analyzer.store_judge_profile(judge_id, competition_id, profile_data)
        await db.commit()

        # Retrieve stored profile
        result = await db.execute(
            select(JudgeScoringProfile).where(
                and_(
                    JudgeScoringProfile.judge_id == judge_id,
                    JudgeScoringProfile.competition_id == competition_id
                )
            )
        )
        profile = result.scalar_one()

    return profile


@router.post("/profile/{judge_id}/{competition_id}/refresh", response_model=MessageResponse)
async def refresh_judge_profile(
    judge_id: int,
    competition_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Refresh judge's scoring profile.

    Recalculates statistics based on latest scores.
    Admin only.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can refresh profiles"
        )

    # Build and store profile in background
    async def refresh_profile():
        analyzer = JudgeConsensusAnalyzer(db)
        profile_data = await analyzer.build_judge_profile(judge_id, competition_id)
        await analyzer.store_judge_profile(judge_id, competition_id, profile_data)
        await db.commit()

    background_tasks.add_task(refresh_profile)

    return MessageResponse(
        message=f"Profile refresh queued for judge {judge_id}",
        status="success"
    )


@router.get("/consensus/{submission_id}", response_model=JudgeConsensusAnalysisResponse)
async def get_submission_consensus(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get consensus analysis for a submission.

    Shows:
    - ICC (Intraclass Correlation Coefficient)
    - Score agreement ratio
    - Outlier judges
    - Consensus verdict

    Admin/Judge/Organizer only.
    """
    # Check permissions
    if current_user.role not in ["admin", "judge", "organizer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins, judges, and organizers can view consensus"
        )

    # Get submission to check competition
    submission = await db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # Get consensus analysis
    result = await db.execute(
        select(JudgeConsensusAnalysis).where(
            JudgeConsensusAnalysis.submission_id == submission_id
        )
    )
    consensus = result.scalar_one_or_none()

    if not consensus:
        # Calculate consensus if doesn't exist
        analyzer = JudgeConsensusAnalyzer(db)
        consensus_data = await analyzer.analyze_submission_scores(submission_id)

        if consensus_data["verdict"] == "insufficient_data":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough scores for consensus analysis"
            )

        # Store consensus
        await analyzer.store_consensus_analysis(
            submission_id,
            submission.competition_id,
            consensus_data
        )
        await db.commit()

        # Retrieve stored consensus
        result = await db.execute(
            select(JudgeConsensusAnalysis).where(
                JudgeConsensusAnalysis.submission_id == submission_id
            )
        )
        consensus = result.scalar_one()

    return consensus


@router.get("/consensus/competition/{competition_id}", response_model=List[JudgeConsensusAnalysisResponse])
async def list_competition_consensus(
    competition_id: int,
    flagged_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List consensus analyses for a competition.

    Query Parameters:
        flagged_only: Only show submissions flagged for review
        skip: Pagination offset
        limit: Max results

    Admin/Organizer only.
    """
    if current_user.role not in ["admin", "organizer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and organizers can view competition consensus"
        )

    query = select(JudgeConsensusAnalysis).where(
        JudgeConsensusAnalysis.competition_id == competition_id
    )

    if flagged_only:
        query = query.where(JudgeConsensusAnalysis.flagged_for_review == True)

    query = query.offset(skip).limit(limit).order_by(
        JudgeConsensusAnalysis.confidence_level.asc()
    )

    result = await db.execute(query)
    analyses = result.scalars().all()

    return analyses


@router.get("/credential-sharing/{judge_id}/{competition_id}", response_model=CredentialSharingDetectionResponse)
async def get_credential_sharing_status(
    judge_id: int,
    competition_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get credential sharing detection status for a judge.

    Shows:
    - Risk score
    - Risk level (low/medium/high)
    - Suspicious indicators
    - Investigation status

    Admin only.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view credential sharing status"
        )

    # Get detection record
    result = await db.execute(
        select(CredentialSharingDetection).where(
            and_(
                CredentialSharingDetection.judge_id == judge_id,
                CredentialSharingDetection.competition_id == competition_id
            )
        )
    )
    detection = result.scalar_one_or_none()

    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No detection data found for this judge"
        )

    return detection


@router.post("/credential-sharing/{judge_id}/{competition_id}/analyze", response_model=CredentialSharingDetectionResponse)
async def analyze_credential_sharing(
    judge_id: int,
    competition_id: int,
    time_window_days: int = 30,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run credential sharing analysis for a judge.

    Analyzes activity patterns over the specified time window.
    Stores results and triggers alerts if high risk.

    Admin only.

    Query Parameters:
        time_window_days: Analysis window (default 30 days)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can run credential sharing analysis"
        )

    # Run analysis
    detector = CredentialSharingDetector(db)
    detection_result = await detector.analyze_judge_activity(
        judge_id,
        competition_id,
        time_window_days
    )

    # Store result
    await detector.store_detection_result(judge_id, competition_id, detection_result)
    await db.commit()

    # Get stored record
    result = await db.execute(
        select(CredentialSharingDetection).where(
            and_(
                CredentialSharingDetection.judge_id == judge_id,
                CredentialSharingDetection.competition_id == competition_id
            )
        )
    )
    detection = result.scalar_one()

    return detection


@router.get("/credential-sharing/competition/{competition_id}/flagged", response_model=List[CredentialSharingDetectionResponse])
async def list_flagged_judges(
    competition_id: int,
    min_risk_score: float = 0.6,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List judges flagged for credential sharing in a competition.

    Query Parameters:
        min_risk_score: Minimum risk score to include (default 0.6)

    Admin only.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view flagged judges"
        )

    detector = CredentialSharingDetector(db)
    flagged = await detector.get_flagged_judges(competition_id, min_risk_score)

    return flagged


@router.patch("/credential-sharing/{detection_id}/investigate", response_model=MessageResponse)
async def update_investigation_status(
    detection_id: int,
    investigation_status: str,
    investigation_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update investigation status for a credential sharing alert.

    Status values: pending, reviewing, resolved

    Admin only.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update investigation status"
        )

    # Valid statuses
    valid_statuses = ["pending", "reviewing", "resolved", "no_action_needed"]
    if investigation_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    # Get detection record
    detection = await db.get(CredentialSharingDetection, detection_id)
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection record not found"
        )

    # Update status
    detection.investigation_status = investigation_status
    if investigation_notes:
        detection.investigation_notes = investigation_notes
    detection.reviewed_by = current_user.id
    detection.reviewed_at = datetime.utcnow()

    await db.commit()

    return MessageResponse(
        message=f"Investigation status updated to: {investigation_status}",
        status="success"
    )


@router.get("/competition/{competition_id}/bias-report")
async def get_competition_bias_report(
    competition_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive bias report for a competition.

    Shows:
    - All judge profiles
    - Bias distribution
    - Consistency metrics
    - Flagged submissions

    Admin/Organizer only.
    """
    if current_user.role not in ["admin", "organizer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and organizers can view bias reports"
        )

    # Get all judge profiles
    result = await db.execute(
        select(JudgeScoringProfile).where(
            JudgeScoringProfile.competition_id == competition_id
        )
    )
    profiles = result.scalars().all()

    # Get flagged consensus analyses
    flagged_result = await db.execute(
        select(JudgeConsensusAnalysis).where(
            and_(
                JudgeConsensusAnalysis.competition_id == competition_id,
                JudgeConsensusAnalysis.flagged_for_review == True
            )
        )
    )
    flagged_submissions = flagged_result.scalars().all()

    # Calculate summary statistics
    if profiles:
        bias_scores = [p.bias_score for p in profiles if p.bias_score is not None]
        avg_bias = np.mean(bias_scores) if bias_scores else 0.0
        bias_std = np.std(bias_scores) if bias_scores else 0.0

        consistency_scores = [p.consistency_score for p in profiles if p.consistency_score is not None]
        avg_consistency = np.mean(consistency_scores) if consistency_scores else 0.0
    else:
        avg_bias = 0.0
        bias_std = 0.0
        avg_consistency = 0.0

    return {
        "competition_id": competition_id,
        "total_judges": len(profiles),
        "avg_bias_score": float(avg_bias),
        "bias_std_dev": float(bias_std),
        "avg_consistency": float(avg_consistency),
        "flagged_submissions_count": len(flagged_submissions),
        "judge_profiles": [
            {
                "judge_id": p.judge_id,
                "submission_count": p.submission_count,
                "avg_score": p.avg_score_given,
                "bias_score": p.bias_score,
                "bias_category": p.bias_category,
                "consistency_score": p.consistency_score,
            }
            for p in profiles
        ],
        "flagged_submissions": [
            {
                "submission_id": f.submission_id,
                "icc_value": f.icc_value,
                "consensus_verdict": f.consensus_verdict,
                "outlier_judges": f.outlier_judges,
            }
            for f in flagged_submissions
        ],
    }
