"""
Submission management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import aiofiles
import os
from pathlib import Path

from app.database import get_db
from app.models.user import User
from app.models.competition import Competition, CompetitionStatus
from app.models.submission import Submission, SubmissionStatus
from app.schemas import SubmissionResponse, MessageResponse
from app.utils.auth import get_current_user
from app.utils.security import validate_file_extension, sanitize_filename
from app.config import settings

router = APIRouter()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(
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

    # Check if user has reached submission limit
    result = await db.execute(
        select(Submission).where(
            Submission.user_id == current_user.id,
            Submission.competition_id == competition_id,
        )
    )
    user_submissions = result.scalars().all()

    if len(user_submissions) >= competition.max_submissions_per_user:
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

    # Save JPG file
    jpg_filename = sanitize_filename(jpg_file.filename)
    jpg_path = Path(settings.UPLOAD_DIR) / f"{current_user.id}_{competition_id}_{jpg_filename}"
    jpg_file_size = 0

    async with aiofiles.open(jpg_path, 'wb') as f:
        content = await jpg_file.read()
        jpg_file_size = len(content)
        await f.write(content)

    # Save RAW file if provided
    raw_path = None
    raw_file_size = 0

    if raw_file:
        raw_filename = sanitize_filename(raw_file.filename)
        raw_path = Path(settings.UPLOAD_DIR) / f"{current_user.id}_{competition_id}_{raw_filename}"

        async with aiofiles.open(raw_path, 'wb') as f:
            content = await raw_file.read()
            raw_file_size = len(content)
            await f.write(content)

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

    # TODO: Trigger AI analysis asynchronously

    return new_submission


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
    query = select(Submission)

    if competition_id:
        query = query.where(Submission.competition_id == competition_id)

    if user_id:
        query = query.where(Submission.user_id == user_id)

    query = query.offset(skip).limit(limit).order_by(Submission.created_at.desc())

    result = await db.execute(query)
    submissions = result.scalars().all()

    return submissions


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
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    return submission


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

    # Check permissions
    if submission.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this submission",
        )

    # Delete files
    if os.path.exists(submission.jpg_file_url):
        os.remove(submission.jpg_file_url)

    if submission.raw_file_url and os.path.exists(submission.raw_file_url):
        os.remove(submission.raw_file_url)

    await db.delete(submission)
    await db.commit()

    return MessageResponse(message="Submission deleted successfully")
