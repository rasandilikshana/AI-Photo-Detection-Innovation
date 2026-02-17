"""
Submission management routes
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import aiofiles
import os
from pathlib import Path

from app.database import get_db
from app.models.user import User, UserRole
from app.models.competition import Competition, CompetitionStatus
from app.models.submission import Submission, SubmissionStatus
from app.schemas import SubmissionResponse, MessageResponse
from app.utils.auth import get_current_user
from app.utils.security import validate_file_extension, sanitize_filename
from app.config import settings

logger = logging.getLogger(__name__)

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
