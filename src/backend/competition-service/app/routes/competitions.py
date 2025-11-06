"""
Competition management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.user import User, UserRole
from app.models.competition import Competition, CompetitionStatus
from app.schemas import (
    CompetitionCreate,
    CompetitionUpdate,
    CompetitionResponse,
    MessageResponse,
)
from app.utils.auth import get_current_user
from app.utils.security import generate_slug

router = APIRouter()


@router.post("", response_model=CompetitionResponse, status_code=status.HTTP_201_CREATED)
async def create_competition(
    competition_data: CompetitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new competition

    Requires authentication. User must have ORGANIZER or ADMIN role.
    """
    # Check if user has permission
    if current_user.role not in [UserRole.ORGANIZER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organizers and admins can create competitions",
        )

    # Generate slug from title
    slug = generate_slug(competition_data.title)

    # Check if slug already exists
    result = await db.execute(select(Competition).where(Competition.slug == slug))
    if result.scalar_one_or_none():
        # Append timestamp to make unique
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    # Create competition
    new_competition = Competition(
        title=competition_data.title,
        description=competition_data.description,
        rules=competition_data.rules,
        slug=slug,
        submission_start=competition_data.submission_start,
        submission_end=competition_data.submission_end,
        max_submissions_per_user=competition_data.max_submissions_per_user,
        require_raw_files=competition_data.require_raw_files,
        allow_ai_generated=competition_data.allow_ai_generated,
        entry_fee=competition_data.entry_fee,
        prize_description=competition_data.prize_description,
        prize_amount=competition_data.prize_amount,
        organizer_id=current_user.id,
    )

    db.add(new_competition)
    await db.commit()
    await db.refresh(new_competition)

    return new_competition


@router.get("", response_model=List[CompetitionResponse])
async def list_competitions(
    skip: int = 0,
    limit: int = 50,
    status: CompetitionStatus = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List all competitions

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **status**: Filter by competition status (optional)
    """
    query = select(Competition)

    if status:
        query = query.where(Competition.status == status)

    query = query.offset(skip).limit(limit).order_by(Competition.created_at.desc())

    result = await db.execute(query)
    competitions = result.scalars().all()

    return competitions


@router.get("/{competition_id}", response_model=CompetitionResponse)
async def get_competition(
    competition_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get competition by ID
    """
    result = await db.execute(
        select(Competition).where(Competition.id == competition_id)
    )
    competition = result.scalar_one_or_none()

    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found",
        )

    return competition


@router.get("/slug/{slug}", response_model=CompetitionResponse)
async def get_competition_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get competition by slug (URL-friendly identifier)
    """
    result = await db.execute(select(Competition).where(Competition.slug == slug))
    competition = result.scalar_one_or_none()

    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found",
        )

    return competition


@router.patch("/{competition_id}", response_model=CompetitionResponse)
async def update_competition(
    competition_id: int,
    competition_data: CompetitionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update competition

    Only the organizer or admin can update a competition.
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

    # Check permissions
    if (
        competition.organizer_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this competition",
        )

    # Update fields
    update_data = competition_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(competition, field, value)

    await db.commit()
    await db.refresh(competition)

    return competition


@router.delete("/{competition_id}", response_model=MessageResponse)
async def delete_competition(
    competition_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete competition

    Only the organizer or admin can delete a competition.
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

    # Check permissions
    if (
        competition.organizer_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this competition",
        )

    await db.delete(competition)
    await db.commit()

    return MessageResponse(message="Competition deleted successfully")
