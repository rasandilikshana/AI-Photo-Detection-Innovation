"""
Judge scoring routes
"""

import io
import logging
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool
from typing import List, Optional

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole
from app.models.submission import Submission, SubmissionStatus, VerificationVerdict
from app.models.competition import Competition
from app.models.score import Score, ScoreAuditLog, ScoreActionType
from app.models.judge import JudgeAssignment
from app.schemas import ScoreCreate, ScoreResponse, MessageResponse, ScoreAuditLogResponse, ScoreAuditLogListResponse
from app.utils.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


def get_client_info(request: Request) -> dict:
    """Extract client identification info from request"""
    # Get real IP (considering proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else None

    return {
        "ip_address": ip,
        "user_agent": request.headers.get("User-Agent", "")[:500],  # Limit length
        "session_id": request.headers.get("X-Session-ID"),  # Optional custom header
    }


def path_to_url(file_path: Optional[str]) -> Optional[str]:
    """Convert a local file path to a web-accessible URL"""
    if not file_path:
        return None
    filename = os.path.basename(file_path)
    return f"/uploads/{filename}"


RAW_PREVIEW_MAX_EDGE = 1600


def _generate_raw_preview(raw_path: str, preview_path: str) -> None:
    """Derive a JPEG preview from a RAW file (blocking — run in a threadpool).

    Prefers the camera's embedded thumbnail (fast, no demosaic); falls back to
    a half-size demosaic render for RAW files without a usable thumbnail.
    """
    import rawpy
    from PIL import Image, ImageOps

    image = None
    with rawpy.imread(raw_path) as raw:
        try:
            thumb = raw.extract_thumb()
            if thumb.format == rawpy.ThumbFormat.JPEG:
                image = Image.open(io.BytesIO(thumb.data))
                image.load()
            elif thumb.format == rawpy.ThumbFormat.BITMAP:
                image = Image.fromarray(thumb.data)
        except (rawpy.LibRawNoThumbnailError, rawpy.LibRawUnsupportedThumbnailError):
            pass
        if image is None:
            rgb = raw.postprocess(use_camera_wb=True, half_size=True, output_bps=8)
            image = Image.fromarray(rgb)

    image = ImageOps.exif_transpose(image)
    if image.mode != "RGB":
        image = image.convert("RGB")
    image.thumbnail((RAW_PREVIEW_MAX_EDGE, RAW_PREVIEW_MAX_EDGE))
    tmp_path = f"{preview_path}.tmp"
    image.save(tmp_path, "JPEG", quality=85)
    os.replace(tmp_path, preview_path)


@router.post("/{submission_id}", response_model=ScoreResponse, status_code=status.HTTP_201_CREATED)
async def create_score(
    submission_id: int,
    score_data: ScoreCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a score for a submission (judges only)

    - **submission_id**: ID of the submission to score
    - **composition_score**: Composition rating (0-10)
    - **technical_score**: Technical skill rating (0-10)
    - **creativity_score**: Creativity rating (0-10)
    - **comments**: Optional judge comments
    - **judge_identifier**: Optional identifier for tracking when multiple judges share credentials
    """
    # Check if user is a judge or admin
    if current_user.role not in [UserRole.JUDGE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges and admins can score submissions",
        )

    # Get submission
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    # Check if judge is assigned to this competition (unless admin)
    if current_user.role == UserRole.JUDGE:
        result = await db.execute(
            select(JudgeAssignment).where(
                JudgeAssignment.judge_id == current_user.id,
                JudgeAssignment.competition_id == submission.competition_id,
                JudgeAssignment.is_active == True,
            )
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to judge this competition",
            )

    # Check if already scored by this judge
    result = await db.execute(
        select(Score).where(
            Score.submission_id == submission_id,
            Score.judge_id == current_user.id,
        )
    )
    existing_score = result.scalar_one_or_none()

    if existing_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already scored this submission",
        )

    # Calculate overall score (weighted average)
    overall_score = (
        score_data.composition_score * 0.4 +
        score_data.technical_score * 0.3 +
        score_data.creativity_score * 0.3
    )

    # Create score
    new_score = Score(
        composition_score=score_data.composition_score,
        technical_score=score_data.technical_score,
        creativity_score=score_data.creativity_score,
        overall_score=overall_score,
        comments=score_data.comments,
        submission_id=submission_id,
        judge_id=current_user.id,
    )

    db.add(new_score)

    # Update submission totals
    submission.total_score += overall_score
    submission.score_count += 1

    await db.commit()
    await db.refresh(new_score)

    # Create audit log entry
    client_info = get_client_info(request)
    audit_log = ScoreAuditLog(
        action_type=ScoreActionType.CREATE,
        composition_score=score_data.composition_score,
        technical_score=score_data.technical_score,
        creativity_score=score_data.creativity_score,
        overall_score=overall_score,
        comments=score_data.comments,
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        session_id=client_info["session_id"],
        judge_identifier=score_data.judge_identifier,
        score_id=new_score.id,
        submission_id=submission_id,
        judge_id=current_user.id,
        competition_id=submission.competition_id,
    )
    db.add(audit_log)
    await db.commit()

    logger.info(f"Judge {current_user.id} scored submission {submission_id} with {overall_score:.2f} from IP {client_info['ip_address']}")

    # === NEW: Judge Consensus Analysis Integration (v2.0) ===
    # Check if all assigned judges have scored this submission
    try:
        from app.services import JudgeConsensusAnalyzer

        # Count total judges assigned
        judge_count_result = await db.execute(
            select(func.count(JudgeAssignment.id))
            .where(
                and_(
                    JudgeAssignment.competition_id == submission.competition_id,
                    JudgeAssignment.is_active == True
                )
            )
        )
        total_judges = judge_count_result.scalar_one()

        # Count scores for this submission
        score_count_result = await db.execute(
            select(func.count(Score.id))
            .where(Score.submission_id == submission_id)
        )
        scores_received = score_count_result.scalar_one()

        logger.info(f"[Score Created] Submission {submission_id}: {scores_received}/{total_judges} judges scored")

        # If all judges have scored, run consensus analysis
        if scores_received >= total_judges and total_judges >= 2:
            logger.info(f"[Consensus] Running analysis for submission {submission_id}")

            analyzer = JudgeConsensusAnalyzer(db)

            # Analyze consensus
            consensus_result = await analyzer.analyze_submission_scores(submission_id)

            # Store consensus analysis
            await analyzer.store_consensus_analysis(
                submission_id,
                submission.competition_id,
                consensus_result
            )

            # Update judge profile
            profile_data = await analyzer.build_judge_profile(
                current_user.id,
                submission.competition_id
            )
            await analyzer.store_judge_profile(
                current_user.id,
                submission.competition_id,
                profile_data
            )

            await db.commit()

            logger.info(
                f"[Consensus] Complete for submission {submission_id}: "
                f"Verdict={consensus_result['verdict']}, "
                f"ICC={consensus_result.get('icc', 'N/A')}"
            )

    except Exception as consensus_err:
        logger.error(f"[Consensus] Analysis failed for submission {submission_id}: {consensus_err}")
        # Don't fail the score creation if consensus fails

    return new_score


@router.get("/submission/{submission_id}", response_model=List[ScoreResponse])
async def get_submission_scores(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all scores for a submission"""
    # Check if user has permission (judge, organizer, admin, or submission owner)
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    # Only allow judges, admins, organizers, or the submission owner to view scores
    if (
        current_user.role not in [UserRole.JUDGE, UserRole.ADMIN, UserRole.ORGANIZER]
        and submission.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view these scores",
        )

    result = await db.execute(
        select(Score).where(Score.submission_id == submission_id)
    )
    scores = result.scalars().all()

    return scores


@router.get("/my-assignments", response_model=List[dict])
async def get_my_judge_assignments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get competitions assigned to the current judge (or all competitions for admins)"""
    if current_user.role not in [UserRole.JUDGE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges and admins can access this endpoint",
        )

    from app.models.competition import Competition

    # Admins can see all competitions
    if current_user.role == UserRole.ADMIN:
        result = await db.execute(select(Competition))
        competitions = result.scalars().all()
        return [
            {
                "assignment_id": 0,  # Admin doesn't need assignment
                "competition_id": comp.id,
                "competition_title": comp.title,
                "competition_status": comp.status.value,
                "submission_start": comp.submission_start,
                "submission_end": comp.submission_end,
            }
            for comp in competitions
        ]

    # Regular judges only see their assigned competitions
    result = await db.execute(
        select(JudgeAssignment, Competition)
        .join(Competition, JudgeAssignment.competition_id == Competition.id)
        .where(
            JudgeAssignment.judge_id == current_user.id,
            JudgeAssignment.is_active == True,
        )
    )
    assignments = result.all()

    return [
        {
            "assignment_id": assignment.JudgeAssignment.id,
            "competition_id": assignment.Competition.id,
            "competition_title": assignment.Competition.title,
            "competition_status": assignment.Competition.status.value,
            "submission_start": assignment.Competition.submission_start,
            "submission_end": assignment.Competition.submission_end,
        }
        for assignment in assignments
    ]


@router.get("/pending/{competition_id}", response_model=List[dict])
async def get_pending_submissions_for_judge(
    competition_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get submissions pending scoring by the current judge"""
    if current_user.role not in [UserRole.JUDGE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges and admins can access this endpoint",
        )

    # Get all submissions for this competition
    result = await db.execute(
        select(Submission).where(
            Submission.competition_id == competition_id,
            Submission.status == "approved",  # Only approved submissions can be scored
        )
    )
    submissions = result.scalars().all()

    # Filter out submissions already scored by this judge
    pending_submissions = []
    for submission in submissions:
        result = await db.execute(
            select(Score).where(
                Score.submission_id == submission.id,
                Score.judge_id == current_user.id,
            )
        )
        if not result.scalar_one_or_none():
            pending_submissions.append({
                "id": submission.id,
                "title": submission.title,
                "description": submission.description,
                "jpg_file_url": path_to_url(submission.jpg_file_url),
                "status": submission.status.value if hasattr(submission.status, 'value') else submission.status,
                "verification_verdict": submission.verification_verdict.value if submission.verification_verdict and hasattr(submission.verification_verdict, 'value') else submission.verification_verdict,
                "verification_confidence": submission.verification_confidence,
                "camera_make": submission.camera_make,
                "camera_model": submission.camera_model,
                "created_at": submission.created_at,
            })

    return pending_submissions


@router.put("/{score_id}", response_model=ScoreResponse)
async def update_score(
    score_id: int,
    score_data: ScoreCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing score (judges only, own scores only)"""
    result = await db.execute(
        select(Score).where(Score.id == score_id)
    )
    score = result.scalar_one_or_none()

    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score not found",
        )

    # Only the judge who created the score (or admin) can update it
    if score.judge_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own scores",
        )

    # Get submission to update totals
    result = await db.execute(
        select(Submission).where(Submission.id == score.submission_id)
    )
    submission = result.scalar_one_or_none()

    # Store previous values for audit log
    prev_composition = score.composition_score
    prev_technical = score.technical_score
    prev_creativity = score.creativity_score
    prev_overall = score.overall_score
    prev_comments = score.comments

    # Calculate new overall score
    new_overall = (
        score_data.composition_score * 0.4 +
        score_data.technical_score * 0.3 +
        score_data.creativity_score * 0.3
    )

    # Update submission totals
    old_overall = score.overall_score
    submission.total_score = submission.total_score - old_overall + new_overall

    # Update score
    score.composition_score = score_data.composition_score
    score.technical_score = score_data.technical_score
    score.creativity_score = score_data.creativity_score
    score.overall_score = new_overall
    score.comments = score_data.comments

    await db.commit()
    await db.refresh(score)

    # Create audit log entry for update
    client_info = get_client_info(request)
    audit_log = ScoreAuditLog(
        action_type=ScoreActionType.UPDATE,
        composition_score=score_data.composition_score,
        technical_score=score_data.technical_score,
        creativity_score=score_data.creativity_score,
        overall_score=new_overall,
        comments=score_data.comments,
        prev_composition_score=prev_composition,
        prev_technical_score=prev_technical,
        prev_creativity_score=prev_creativity,
        prev_overall_score=prev_overall,
        prev_comments=prev_comments,
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        session_id=client_info["session_id"],
        judge_identifier=score_data.judge_identifier,
        score_id=score.id,
        submission_id=score.submission_id,
        judge_id=current_user.id,
        competition_id=submission.competition_id,
    )
    db.add(audit_log)
    await db.commit()

    logger.info(f"Judge {current_user.id} updated score {score_id} from IP {client_info['ip_address']}")

    return score


@router.delete("/{score_id}", response_model=MessageResponse)
async def delete_score(
    score_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a score (admins only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete scores",
        )

    result = await db.execute(
        select(Score).where(Score.id == score_id)
    )
    score = result.scalar_one_or_none()

    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score not found",
        )

    # Store score info for audit log before deletion
    score_submission_id = score.submission_id
    score_judge_id = score.judge_id
    score_composition = score.composition_score
    score_technical = score.technical_score
    score_creativity = score.creativity_score
    score_overall = score.overall_score
    score_comments = score.comments

    # Update submission totals
    result = await db.execute(
        select(Submission).where(Submission.id == score.submission_id)
    )
    submission = result.scalar_one_or_none()

    if submission:
        submission.total_score -= score.overall_score
        submission.score_count -= 1

    # Create audit log entry for delete (before deleting the score)
    client_info = get_client_info(request)
    audit_log = ScoreAuditLog(
        action_type=ScoreActionType.DELETE,
        prev_composition_score=score_composition,
        prev_technical_score=score_technical,
        prev_creativity_score=score_creativity,
        prev_overall_score=score_overall,
        prev_comments=score_comments,
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        session_id=client_info["session_id"],
        score_id=None,  # Score will be deleted
        submission_id=score_submission_id,
        judge_id=score_judge_id,
        competition_id=submission.competition_id if submission else 0,
    )
    db.add(audit_log)

    await db.delete(score)
    await db.commit()

    logger.info(f"Admin {current_user.id} deleted score {score_id} from IP {client_info['ip_address']}")

    return MessageResponse(message="Score deleted successfully")


@router.get("/competition/{competition_id}/stats")
async def get_competition_stats_for_judge(
    competition_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get statistics for a competition (for judges)"""
    if current_user.role not in [UserRole.JUDGE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges and admins can access this endpoint",
        )

    # Verify judge is assigned (or admin)
    if current_user.role == UserRole.JUDGE:
        result = await db.execute(
            select(JudgeAssignment).where(
                JudgeAssignment.judge_id == current_user.id,
                JudgeAssignment.competition_id == competition_id,
                JudgeAssignment.is_active == True,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this competition",
            )

    # Get competition info
    result = await db.execute(
        select(Competition).where(Competition.id == competition_id)
    )
    competition = result.scalar_one_or_none()
    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found",
        )

    # Get total submissions count
    total_result = await db.execute(
        select(func.count(Submission.id)).where(
            Submission.competition_id == competition_id
        )
    )
    total_submissions = total_result.scalar() or 0

    # Get status breakdown
    status_result = await db.execute(
        select(Submission.status, func.count(Submission.id))
        .where(Submission.competition_id == competition_id)
        .group_by(Submission.status)
    )
    status_breakdown = {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in status_result.all()}

    # Get verdict breakdown
    verdict_result = await db.execute(
        select(Submission.verification_verdict, func.count(Submission.id))
        .where(Submission.competition_id == competition_id)
        .group_by(Submission.verification_verdict)
    )
    verdict_breakdown = {}
    for row in verdict_result.all():
        key = row[0].value if row[0] and hasattr(row[0], 'value') else (row[0] or 'none')
        verdict_breakdown[key] = row[1]

    # Get count of submissions scored by current judge
    scored_result = await db.execute(
        select(func.count(Score.id))
        .join(Submission, Score.submission_id == Submission.id)
        .where(
            Submission.competition_id == competition_id,
            Score.judge_id == current_user.id,
        )
    )
    scored_by_me = scored_result.scalar() or 0

    # Get approved submissions count (scoreable)
    approved_result = await db.execute(
        select(func.count(Submission.id)).where(
            Submission.competition_id == competition_id,
            Submission.status == SubmissionStatus.APPROVED,
        )
    )
    approved_count = approved_result.scalar() or 0

    return {
        "competition_id": competition_id,
        "competition_title": competition.title,
        "competition_status": competition.status.value,
        "total_submissions": total_submissions,
        "approved_submissions": approved_count,
        "scored_by_me": scored_by_me,
        "pending_to_score": approved_count - scored_by_me,
        "status_breakdown": status_breakdown,
        "verdict_breakdown": verdict_breakdown,
    }


@router.get("/competition/{competition_id}/submissions")
async def get_competition_submissions_for_judge(
    competition_id: int,
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, analyzing, approved, rejected"),
    verdict_filter: Optional[str] = Query(None, description="Filter by AI verdict: authentic, suspicious, ai_generated, needs_review"),
    scored_filter: Optional[str] = Query(None, description="Filter by scoring status: scored, unscored"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all submissions for a competition with filtering options.
    Returns full submission data including AI analysis results.
    """
    if current_user.role not in [UserRole.JUDGE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges and admins can access this endpoint",
        )

    # Verify judge is assigned (or admin)
    if current_user.role == UserRole.JUDGE:
        result = await db.execute(
            select(JudgeAssignment).where(
                JudgeAssignment.judge_id == current_user.id,
                JudgeAssignment.competition_id == competition_id,
                JudgeAssignment.is_active == True,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this competition",
            )

    # Build query with filters
    query = select(Submission).where(Submission.competition_id == competition_id)

    if status_filter:
        try:
            status_enum = SubmissionStatus(status_filter)
            query = query.where(Submission.status == status_enum)
        except ValueError:
            pass

    if verdict_filter:
        try:
            verdict_enum = VerificationVerdict(verdict_filter)
            query = query.where(Submission.verification_verdict == verdict_enum)
        except ValueError:
            pass

    query = query.order_by(Submission.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    submissions = result.scalars().all()

    # Get scores by current judge for these submissions
    submission_ids = [s.id for s in submissions]
    if submission_ids:
        scores_result = await db.execute(
            select(Score.submission_id).where(
                Score.submission_id.in_(submission_ids),
                Score.judge_id == current_user.id,
            )
        )
        scored_ids = set(row[0] for row in scores_result.all())
    else:
        scored_ids = set()

    # Build response with AI analysis data
    response_list = []
    for sub in submissions:
        # Filter by scored status if requested
        is_scored = sub.id in scored_ids
        if scored_filter == "scored" and not is_scored:
            continue
        if scored_filter == "unscored" and is_scored:
            continue

        # Extract key AI analysis info
        ai_summary = None
        if sub.verification_details:
            details = sub.verification_details
            layer1 = details.get("layer1_result", {})
            layer2 = details.get("layer2_result", {})
            layer3 = details.get("layer3_result", {})
            raw_linkage = details.get("raw_jpg_linkage", {})

            ai_summary = {
                "verdict": details.get("verdict"),
                "confidence_score": details.get("confidence_score"),
                "layer1_verdict": layer1.get("verdict") if layer1 else None,
                "layer2_verdict": layer2.get("verdict") if layer2 else None,
                "layer2_confidence": layer2.get("confidence") if layer2 else None,
                "layer3_verdict": layer3.get("verdict") if layer3 else None,
                "layer3_confidence": layer3.get("confidence") if layer3 else None,
                "raw_linkage_verdict": raw_linkage.get("verdict") if raw_linkage else None,
            }

        response_list.append({
            "id": sub.id,
            "title": sub.title,
            "description": sub.description,
            "jpg_file_url": path_to_url(sub.jpg_file_url),
            "status": sub.status.value if hasattr(sub.status, 'value') else sub.status,
            "verification_verdict": sub.verification_verdict.value if sub.verification_verdict and hasattr(sub.verification_verdict, 'value') else sub.verification_verdict,
            "verification_confidence": sub.verification_confidence,
            "ai_summary": ai_summary,
            "camera_make": sub.camera_make,
            "camera_model": sub.camera_model,
            "iso": sub.iso,
            "aperture": sub.aperture,
            "shutter_speed": sub.shutter_speed,
            "capture_date": sub.capture_date,
            "total_score": sub.total_score,
            "score_count": sub.score_count,
            "is_scored_by_me": is_scored,
            "created_at": sub.created_at,
            # Review/error fields for judge actions
            "analysis_error": sub.analysis_error,
            "rejection_reason": sub.rejection_reason,
            "reviewed_by": sub.reviewed_by,
            "reviewed_at": sub.reviewed_at.isoformat() if sub.reviewed_at else None,
            # V2.0 Camera Reputation fields
            "camera_trust_score": sub.camera_trust_score,
            "prnu_fingerprint_id": sub.prnu_fingerprint_id,
            "prnu_extracted_energy": sub.prnu_extracted_energy,
        })

    return response_list


@router.get("/submission-detail/{submission_id}")
async def get_submission_detail_for_judge(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get full submission details including complete AI analysis for judges.
    """
    if current_user.role not in [UserRole.JUDGE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges and admins can access this endpoint",
        )

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

    # Verify judge is assigned to this competition (or admin)
    if current_user.role == UserRole.JUDGE:
        result = await db.execute(
            select(JudgeAssignment).where(
                JudgeAssignment.judge_id == current_user.id,
                JudgeAssignment.competition_id == sub.competition_id,
                JudgeAssignment.is_active == True,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to judge this competition",
            )

    # Check if scored by current judge
    score_result = await db.execute(
        select(Score).where(
            Score.submission_id == submission_id,
            Score.judge_id == current_user.id,
        )
    )
    my_score = score_result.scalar_one_or_none()

    return {
        "id": sub.id,
        "title": sub.title,
        "description": sub.description,
        "jpg_file_url": path_to_url(sub.jpg_file_url),
        "raw_file_url": path_to_url(sub.raw_file_url),
        "status": sub.status.value if hasattr(sub.status, 'value') else sub.status,
        "verification_verdict": sub.verification_verdict.value if sub.verification_verdict and hasattr(sub.verification_verdict, 'value') else sub.verification_verdict,
        "verification_confidence": sub.verification_confidence,
        "verification_details": sub.verification_details,
        "verification_timestamp": sub.verification_timestamp,
        "camera_make": sub.camera_make,
        "camera_model": sub.camera_model,
        "lens_model": sub.lens_model if hasattr(sub, 'lens_model') else None,
        "iso": sub.iso,
        "aperture": sub.aperture,
        "shutter_speed": sub.shutter_speed,
        "capture_date": sub.capture_date,
        "total_score": sub.total_score,
        "score_count": sub.score_count,
        "competition": {
            "id": sub.competition.id,
            "title": sub.competition.title,
            "status": sub.competition.status.value,
        } if sub.competition else None,
        "my_score": {
            "id": my_score.id,
            "composition_score": my_score.composition_score,
            "technical_score": my_score.technical_score,
            "creativity_score": my_score.creativity_score,
            "overall_score": my_score.overall_score,
            "comments": my_score.comments,
        } if my_score else None,
        "created_at": sub.created_at,
        # Review/error fields for judge actions
        "analysis_error": sub.analysis_error,
        "rejection_reason": sub.rejection_reason,
        "reviewed_by": sub.reviewed_by,
        "reviewed_at": sub.reviewed_at.isoformat() if sub.reviewed_at else None,
        # V2.0 Camera Reputation fields
        "camera_trust_score": sub.camera_trust_score,
        "prnu_fingerprint_id": sub.prnu_fingerprint_id,
        "prnu_extracted_energy": sub.prnu_extracted_energy,
    }


@router.get("/raw-preview/{submission_id}")
async def get_raw_preview_for_judge(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a web-viewable JPEG preview of a submission's RAW file.

    Browsers cannot render RAW formats, so the preview is derived once via
    rawpy, cached under uploads/previews/, and served as a static file the
    same way the JPG is.
    """
    if current_user.role not in [UserRole.JUDGE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges and admins can access this endpoint",
        )

    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    sub = result.scalar_one_or_none()

    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    # Verify judge is assigned to this competition (or admin)
    if current_user.role == UserRole.JUDGE:
        result = await db.execute(
            select(JudgeAssignment).where(
                JudgeAssignment.judge_id == current_user.id,
                JudgeAssignment.competition_id == sub.competition_id,
                JudgeAssignment.is_active == True,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to judge this competition",
            )

    if not sub.raw_file_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This submission has no RAW file",
        )

    uploads_dir = Path(settings.UPLOAD_DIR)
    raw_path = uploads_dir / os.path.basename(sub.raw_file_url)
    if not raw_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RAW file is missing from storage",
        )

    previews_dir = uploads_dir / "previews"
    previews_dir.mkdir(parents=True, exist_ok=True)
    preview_path = previews_dir / f"{raw_path.stem}_raw_preview.jpg"

    if not preview_path.exists():
        try:
            await run_in_threadpool(_generate_raw_preview, str(raw_path), str(preview_path))
        except Exception as exc:
            logger.error(f"RAW preview generation failed for submission {submission_id}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not generate a preview from this RAW file",
            )

    return {"preview_url": f"/uploads/previews/{preview_path.name}"}


# ============================================================================
# Admin endpoints for managing judge assignments
# ============================================================================

@router.get("/admin/judges")
async def list_judges(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users with judge role (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint",
        )

    result = await db.execute(
        select(User).where(User.role == UserRole.JUDGE)
    )
    judges = result.scalars().all()

    return [
        {
            "id": judge.id,
            "username": judge.username,
            "email": judge.email,
            "full_name": judge.full_name,
            "is_active": judge.is_active,
        }
        for judge in judges
    ]


@router.get("/admin/judge-assignments")
async def list_all_judge_assignments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all judge assignments (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint",
        )

    result = await db.execute(
        select(JudgeAssignment, User, Competition)
        .join(User, JudgeAssignment.judge_id == User.id)
        .join(Competition, JudgeAssignment.competition_id == Competition.id)
    )
    assignments = result.all()

    return [
        {
            "id": row.JudgeAssignment.id,
            "judge_id": row.User.id,
            "judge_username": row.User.username,
            "judge_email": row.User.email,
            "competition_id": row.Competition.id,
            "competition_title": row.Competition.title,
            "competition_status": row.Competition.status.value,
            "is_active": row.JudgeAssignment.is_active,
            "created_at": row.JudgeAssignment.created_at,
        }
        for row in assignments
    ]


@router.post("/admin/judge-assignments", status_code=status.HTTP_201_CREATED)
async def create_judge_assignment(
    judge_id: int,
    competition_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign a judge to a competition (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint",
        )

    # Verify judge exists and is a judge
    result = await db.execute(
        select(User).where(User.id == judge_id, User.role == UserRole.JUDGE)
    )
    judge = result.scalar_one_or_none()
    if not judge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Judge not found or user is not a judge",
        )

    # Verify competition exists
    result = await db.execute(
        select(Competition).where(Competition.id == competition_id)
    )
    competition = result.scalar_one_or_none()
    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found",
        )

    # Check if assignment already exists
    result = await db.execute(
        select(JudgeAssignment).where(
            JudgeAssignment.judge_id == judge_id,
            JudgeAssignment.competition_id == competition_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        # Reactivate if inactive
        if not existing.is_active:
            existing.is_active = True
            await db.commit()
            return {"message": "Judge assignment reactivated", "id": existing.id}
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Judge is already assigned to this competition",
        )

    # Create assignment
    assignment = JudgeAssignment(
        judge_id=judge_id,
        competition_id=competition_id,
        is_active=True,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    logger.info(f"Admin {current_user.id} assigned judge {judge_id} to competition {competition_id}")

    return {
        "message": "Judge assigned successfully",
        "id": assignment.id,
        "judge_id": judge_id,
        "competition_id": competition_id,
    }


@router.delete("/admin/judge-assignments/{assignment_id}")
async def remove_judge_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a judge assignment (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint",
        )

    result = await db.execute(
        select(JudgeAssignment).where(JudgeAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    # Soft delete by setting inactive
    assignment.is_active = False
    await db.commit()

    logger.info(f"Admin {current_user.id} removed judge assignment {assignment_id}")

    return {"message": "Judge assignment removed successfully"}


# ============================================================================
# Score Audit Log endpoints
# ============================================================================

@router.get("/audit-logs/competition/{competition_id}", response_model=ScoreAuditLogListResponse)
async def get_competition_score_audit_logs(
    competition_id: int,
    submission_id: Optional[int] = Query(None, description="Filter by specific submission"),
    action_type: Optional[str] = Query(None, description="Filter by action type: create, update, delete"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get score audit logs for a competition.
    Shows all scoring actions with client details (IP, user agent, etc.)
    Useful for tracking when multiple judges share the same credentials.

    Only accessible by judges assigned to the competition, organizers, and admins.
    """
    # Check permissions
    if current_user.role not in [UserRole.JUDGE, UserRole.ADMIN, UserRole.ORGANIZER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges, organizers, and admins can access audit logs",
        )

    # Verify judge is assigned (unless admin/organizer)
    if current_user.role == UserRole.JUDGE:
        result = await db.execute(
            select(JudgeAssignment).where(
                JudgeAssignment.judge_id == current_user.id,
                JudgeAssignment.competition_id == competition_id,
                JudgeAssignment.is_active == True,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this competition",
            )

    # Build query
    query = select(ScoreAuditLog).where(ScoreAuditLog.competition_id == competition_id)

    if submission_id:
        query = query.where(ScoreAuditLog.submission_id == submission_id)

    if action_type:
        try:
            action_enum = ScoreActionType(action_type)
            query = query.where(ScoreAuditLog.action_type == action_enum)
        except ValueError:
            pass

    # Get total count
    count_query = select(func.count(ScoreAuditLog.id)).where(ScoreAuditLog.competition_id == competition_id)
    if submission_id:
        count_query = count_query.where(ScoreAuditLog.submission_id == submission_id)
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0

    # Get unique sessions and IPs
    unique_sessions_result = await db.execute(
        select(func.count(func.distinct(ScoreAuditLog.session_id))).where(
            ScoreAuditLog.competition_id == competition_id,
            ScoreAuditLog.session_id.isnot(None),
        )
    )
    unique_sessions = unique_sessions_result.scalar() or 0

    unique_ips_result = await db.execute(
        select(func.count(func.distinct(ScoreAuditLog.ip_address))).where(
            ScoreAuditLog.competition_id == competition_id,
            ScoreAuditLog.ip_address.isnot(None),
        )
    )
    unique_ips = unique_ips_result.scalar() or 0

    # Get logs with pagination
    query = query.order_by(ScoreAuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return ScoreAuditLogListResponse(
        logs=[ScoreAuditLogResponse.model_validate(log) for log in logs],
        total_count=total_count,
        unique_sessions=unique_sessions,
        unique_ips=unique_ips,
    )


@router.get("/audit-logs/submission/{submission_id}", response_model=List[ScoreAuditLogResponse])
async def get_submission_score_audit_logs(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all score audit logs for a specific submission.
    Shows the complete history of scoring actions.
    """
    # Check permissions
    if current_user.role not in [UserRole.JUDGE, UserRole.ADMIN, UserRole.ORGANIZER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges, organizers, and admins can access audit logs",
        )

    # Get submission to verify competition access
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    # Verify judge is assigned (unless admin/organizer)
    if current_user.role == UserRole.JUDGE:
        result = await db.execute(
            select(JudgeAssignment).where(
                JudgeAssignment.judge_id == current_user.id,
                JudgeAssignment.competition_id == submission.competition_id,
                JudgeAssignment.is_active == True,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this competition",
            )

    # Get audit logs for this submission
    result = await db.execute(
        select(ScoreAuditLog)
        .where(ScoreAuditLog.submission_id == submission_id)
        .order_by(ScoreAuditLog.created_at.desc())
    )
    logs = result.scalars().all()

    return [ScoreAuditLogResponse.model_validate(log) for log in logs]


@router.get("/audit-logs/my-activity", response_model=List[ScoreAuditLogResponse])
async def get_my_scoring_activity(
    competition_id: Optional[int] = Query(None, description="Filter by competition"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the current judge's own scoring activity/history.
    Useful for judges to review their own actions.
    """
    if current_user.role not in [UserRole.JUDGE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges and admins can access this endpoint",
        )

    query = select(ScoreAuditLog).where(ScoreAuditLog.judge_id == current_user.id)

    if competition_id:
        query = query.where(ScoreAuditLog.competition_id == competition_id)

    query = query.order_by(ScoreAuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return [ScoreAuditLogResponse.model_validate(log) for log in logs]


# ============================================================================
# Judge Manual Review endpoints
# ============================================================================

@router.post("/review/{submission_id}")
async def review_submission(
    submission_id: int,
    action: str = Query(..., description="Action: approve or reject"),
    reason: Optional[str] = Query(None, description="Reason for rejection (required for reject)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually approve or reject a submission.
    Used when AI analysis fails or needs manual review.

    - **action**: 'approve' or 'reject'
    - **reason**: Required when rejecting, explains why
    """
    from datetime import datetime

    if current_user.role not in [UserRole.JUDGE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges and admins can review submissions",
        )

    if action not in ['approve', 'reject']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'approve' or 'reject'",
        )

    if action == 'reject' and not reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reason is required when rejecting a submission",
        )

    # Get submission
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    # Verify judge is assigned to this competition (unless admin)
    if current_user.role == UserRole.JUDGE:
        assignment_result = await db.execute(
            select(JudgeAssignment).where(
                JudgeAssignment.judge_id == current_user.id,
                JudgeAssignment.competition_id == submission.competition_id,
                JudgeAssignment.is_active == True,
            )
        )
        if not assignment_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this competition",
            )

    # Update submission status
    if action == 'approve':
        submission.status = SubmissionStatus.APPROVED
        submission.rejection_reason = None
    else:
        submission.status = SubmissionStatus.REJECTED
        submission.rejection_reason = reason

    submission.reviewed_by = current_user.id
    submission.reviewed_at = datetime.utcnow()

    await db.commit()

    logger.info(f"Judge {current_user.id} {action}d submission {submission_id}: {reason or 'No reason'}")

    return {
        "message": f"Submission {action}d successfully",
        "submission_id": submission_id,
        "new_status": submission.status.value,
        "reviewed_by": current_user.id,
        "reason": reason,
    }
