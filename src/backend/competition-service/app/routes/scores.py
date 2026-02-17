"""
Judge scoring routes
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.user import User, UserRole
from app.models.submission import Submission
from app.models.score import Score
from app.models.judge import JudgeAssignment
from app.schemas import ScoreCreate, ScoreResponse, MessageResponse
from app.utils.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{submission_id}", response_model=ScoreResponse, status_code=status.HTTP_201_CREATED)
async def create_score(
    submission_id: int,
    score_data: ScoreCreate,
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

    logger.info(f"Judge {current_user.id} scored submission {submission_id} with {overall_score:.2f}")

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
    """Get competitions assigned to the current judge"""
    if current_user.role not in [UserRole.JUDGE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges and admins can access this endpoint",
        )

    from app.models.competition import Competition

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
                "jpg_file_url": submission.jpg_file_url,
                "camera_make": submission.camera_make,
                "camera_model": submission.camera_model,
                "created_at": submission.created_at,
            })

    return pending_submissions


@router.put("/{score_id}", response_model=ScoreResponse)
async def update_score(
    score_id: int,
    score_data: ScoreCreate,
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

    return score


@router.delete("/{score_id}", response_model=MessageResponse)
async def delete_score(
    score_id: int,
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

    # Update submission totals
    result = await db.execute(
        select(Submission).where(Submission.id == score.submission_id)
    )
    submission = result.scalar_one_or_none()

    if submission:
        submission.total_score -= score.overall_score
        submission.score_count -= 1

    await db.delete(score)
    await db.commit()

    return MessageResponse(message="Score deleted successfully")
