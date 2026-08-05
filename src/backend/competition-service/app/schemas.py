"""
Pydantic schemas for request/response validation
"""

import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum


def to_naive_utc(v: Optional[datetime]) -> Optional[datetime]:
    """Normalize timezone-aware datetimes (e.g. browser ISO strings ending in 'Z')
    to naive UTC — DB columns are TIMESTAMP WITHOUT TIME ZONE and asyncpg
    rejects aware values for them."""
    if v is not None and v.tzinfo is not None:
        return v.astimezone(timezone.utc).replace(tzinfo=None)
    return v


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


class UserUpdate(BaseModel):
    """Schema for updating user data (admin only)"""
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    full_name: Optional[str] = None


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

    @field_validator('submission_start', 'submission_end')
    @classmethod
    def normalize_datetimes(cls, v: datetime) -> datetime:
        return to_naive_utc(v)

    @field_validator('submission_end')
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        if 'submission_start' in info.data and v <= info.data['submission_start']:
            raise ValueError('submission_end must be after submission_start')
        return v


class CompetitionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=5, max_length=255)
    description: Optional[str] = Field(default=None, min_length=20)
    rules: Optional[str] = None
    status: Optional[CompetitionStatus] = None
    submission_start: Optional[datetime] = None
    submission_end: Optional[datetime] = None
    judging_start: Optional[datetime] = None
    judging_end: Optional[datetime] = None
    results_date: Optional[datetime] = None
    max_submissions_per_user: Optional[int] = Field(default=None, ge=1, le=20)
    require_raw_files: Optional[bool] = None
    allow_ai_generated: Optional[bool] = None
    entry_fee: Optional[int] = Field(default=None, ge=0)
    prize_description: Optional[str] = None
    prize_amount: Optional[int] = Field(default=None, ge=0)

    @field_validator(
        'submission_start', 'submission_end', 'judging_start', 'judging_end', 'results_date'
    )
    @classmethod
    def normalize_datetimes(cls, v: Optional[datetime]) -> Optional[datetime]:
        return to_naive_utc(v)


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


class CompetitionBasic(BaseModel):
    """Minimal competition info for embedding in submissions"""
    id: int
    title: str
    status: CompetitionStatus

    class Config:
        from_attributes = True


class SubmissionResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    jpg_file_url: str
    raw_file_url: Optional[str]
    status: SubmissionStatus
    verification_verdict: Optional[VerificationVerdict]
    verification_confidence: Optional[float]
    verification_details: Optional[dict] = None
    verification_timestamp: Optional[str] = None
    camera_make: Optional[str]
    camera_model: Optional[str]
    iso: Optional[int] = None
    aperture: Optional[str] = None
    shutter_speed: Optional[str] = None
    capture_date: Optional[str] = None
    total_score: float
    score_count: int
    user_id: int
    competition_id: int
    competition: Optional[CompetitionBasic] = None
    created_at: datetime
    # Analysis error (when AI analysis fails)
    analysis_error: Optional[str] = None
    # Review/Rejection info (when judge manually reviews)
    rejection_reason: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    # V2.0 Camera Reputation fields
    camera_trust_score: Optional[float] = None
    prnu_fingerprint_id: Optional[int] = None
    prnu_extracted_energy: Optional[float] = None

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
    judge_identifier: Optional[str] = Field(None, max_length=100, description="Optional identifier for tracking when multiple judges share credentials")


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
# Score Audit Log Schemas
# ============================================================================

class ScoreActionType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ScoreAuditLogResponse(BaseModel):
    id: int
    action_type: ScoreActionType

    # Score values
    composition_score: Optional[float]
    technical_score: Optional[float]
    creativity_score: Optional[float]
    overall_score: Optional[float]
    comments: Optional[str]

    # Previous values (for updates)
    prev_composition_score: Optional[float]
    prev_technical_score: Optional[float]
    prev_creativity_score: Optional[float]
    prev_overall_score: Optional[float]
    prev_comments: Optional[str]

    # Client tracking
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    judge_identifier: Optional[str]

    # References
    score_id: Optional[int]
    submission_id: int
    judge_id: int
    competition_id: int

    created_at: datetime

    class Config:
        from_attributes = True


class ScoreAuditLogListResponse(BaseModel):
    """Response with list of audit logs and summary"""
    logs: List[ScoreAuditLogResponse]
    total_count: int
    unique_sessions: int
    unique_ips: int


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


# ============================================================================
# Camera Reputation Schemas (v2.0)
# ============================================================================

class CameraFingerprintResponse(BaseModel):
    """Camera PRNU fingerprint response"""
    id: int
    submission_id: int
    user_id: int
    camera_make: str
    camera_model: str
    prnu_energy: float
    prnu_hash: str
    similarity_to_profile: Optional[float] = None
    trust_boost_applied: float
    verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CameraTrustProfileResponse(BaseModel):
    """Camera trust profile response"""
    id: int
    camera_make: str
    camera_model: str
    total_submissions: int
    authentic_count: int
    suspicious_count: int
    ai_generated_count: int
    rejected_count: int
    avg_trust_score: float
    prnu_pattern_stability: float
    avg_prnu_energy: Optional[float] = None
    authenticity_rate: float
    rejection_rate: float
    last_updated: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CameraComparisonResponse(BaseModel):
    """PRNU pattern comparison result"""
    fingerprint1_id: int
    fingerprint2_id: int
    similarity_score: float
    correlation: Optional[float] = None
    distance_metric: Optional[str] = None
    same_camera_likely: bool


class TrustScoreResponse(BaseModel):
    """Trust score calculation result"""
    trust_score: float
    boost: float
    message: str
    similarity_to_profile: Optional[float] = None
    max_similarity: Optional[float] = None
    previous_submissions: int
    verdict: str
    verdict_consistency: Optional[float] = None


class FraudDetectionResponse(BaseModel):
    """Camera fraud detection result"""
    fraud_likelihood: float
    verdict: str
    recommendation: str
    indicators: List[str]
    trust_score: float
    explanation: str


class UserCameraHistoryResponse(BaseModel):
    """User's camera usage history"""
    camera_make: str
    camera_model: str
    submission_count: int
    first_used: datetime
    last_used: datetime
    avg_trust_score: float


# ============================================================================
# Judge Analytics Schemas (v2.0)
# ============================================================================

class JudgeScoringProfileResponse(BaseModel):
    """Judge scoring profile response"""
    id: int
    judge_id: int
    competition_id: int
    submission_count: int
    avg_score_given: Optional[float] = None
    score_std_dev: Optional[float] = None
    bias_score: Optional[float] = None
    bias_category: str
    consistency_score: Optional[float] = None
    outlier_count: int
    last_analyzed: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JudgeConsensusAnalysisResponse(BaseModel):
    """Judge consensus analysis response"""
    id: int
    competition_id: int
    submission_id: int
    judge_count: int
    score_mean: Optional[float] = None
    score_std_dev: Optional[float] = None
    icc_value: Optional[float] = None
    consensus_verdict: Optional[str] = None
    consensus_quality: str
    confidence_level: Optional[float] = None
    flagged_for_review: bool
    outlier_judges: Optional[List[int]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CredentialSharingDetectionResponse(BaseModel):
    """Credential sharing detection response"""
    id: int
    competition_id: int
    judge_id: int
    unique_ip_count: Optional[int] = None
    unique_session_count: Optional[int] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    is_suspicious: bool
    alert_triggered: bool
    investigation_status: str
    created_at: datetime

    class Config:
        from_attributes = True
