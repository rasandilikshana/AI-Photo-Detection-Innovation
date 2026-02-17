"""
Pydantic schemas for request/response validation
"""

import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================================================
# User Schemas
# ============================================================================

class UserRole(str, Enum):
    PARTICIPANT = "participant"
    JUDGE = "judge"
    ORGANIZER = "organizer"
    ADMIN = "admin"


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """
        Validate password complexity:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*...)")

        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============================================================================
# Competition Schemas
# ============================================================================

class CompetitionStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    JUDGING = "judging"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CompetitionCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=20)
    rules: Optional[str] = None
    submission_start: datetime
    submission_end: datetime
    max_submissions_per_user: int = Field(default=5, ge=1, le=20)
    require_raw_files: bool = True
    allow_ai_generated: bool = False
    entry_fee: int = Field(default=0, ge=0)
    prize_description: Optional[str] = None
    prize_amount: Optional[int] = Field(default=None, ge=0)

    @field_validator('submission_end')
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        if 'submission_start' in info.data and v <= info.data['submission_start']:
            raise ValueError('submission_end must be after submission_start')
        return v


class CompetitionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[str] = None
    status: Optional[CompetitionStatus] = None
    judging_start: Optional[datetime] = None
    judging_end: Optional[datetime] = None
    results_date: Optional[datetime] = None


class CompetitionResponse(BaseModel):
    id: int
    title: str
    description: str
    slug: str
    status: CompetitionStatus
    submission_start: datetime
    submission_end: datetime
    max_submissions_per_user: int
    require_raw_files: bool
    allow_ai_generated: bool
    entry_fee: int
    prize_description: Optional[str]
    prize_amount: Optional[int]
    organizer_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Submission Schemas
# ============================================================================

class SubmissionStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISQUALIFIED = "disqualified"


class VerificationVerdict(str, Enum):
    AUTHENTIC = "authentic"
    SUSPICIOUS = "suspicious"
    AI_GENERATED = "ai_generated"
    NEEDS_REVIEW = "needs_review"


class SubmissionCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: Optional[str] = None
    competition_id: int


class SubmissionResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    jpg_file_url: str
    raw_file_url: Optional[str]
    status: SubmissionStatus
    verification_verdict: Optional[VerificationVerdict]
    verification_confidence: Optional[float]
    camera_make: Optional[str]
    camera_model: Optional[str]
    total_score: float
    score_count: int
    user_id: int
    competition_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Score Schemas
# ============================================================================

class ScoreCreate(BaseModel):
    composition_score: float = Field(..., ge=0, le=10)
    technical_score: float = Field(..., ge=0, le=10)
    creativity_score: float = Field(..., ge=0, le=10)
    comments: Optional[str] = None


class ScoreResponse(BaseModel):
    id: int
    composition_score: float
    technical_score: float
    creativity_score: float
    overall_score: float
    comments: Optional[str]
    submission_id: int
    judge_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Generic Response Schemas
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    database: str = "connected"


class MessageResponse(BaseModel):
    message: str
    status: str = "success"


class PaginatedResponse(BaseModel):
    items: List[BaseModel]
    total: int
    page: int
    page_size: int
    total_pages: int
