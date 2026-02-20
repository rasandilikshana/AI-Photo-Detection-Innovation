"""
Submission model for photo submissions
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SQLEnum, Text, JSON, Float
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class SubmissionStatus(str, enum.Enum):
    """Submission status"""

    PENDING = "pending"
    ANALYZING = "analyzing"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISQUALIFIED = "disqualified"


class VerificationVerdict(str, enum.Enum):
    """AI verification verdict"""

    AUTHENTIC = "authentic"
    SUSPICIOUS = "suspicious"
    AI_GENERATED = "ai_generated"
    NEEDS_REVIEW = "needs_review"


class Submission(BaseModel):
    """Photo submission model"""

    __tablename__ = "submissions"

    # Basic Info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Files
    jpg_file_url = Column(String(500), nullable=False)
    jpg_file_size = Column(Integer, nullable=False)  # in bytes
    raw_file_url = Column(String(500), nullable=True)
    raw_file_size = Column(Integer, nullable=True)  # in bytes

    # Status
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False)

    # AI Verification Results
    verification_verdict = Column(SQLEnum(VerificationVerdict), nullable=True)
    verification_confidence = Column(Float, nullable=True)  # 0.0 - 1.0
    verification_details = Column(JSON, nullable=True)  # Full verification report
    verification_timestamp = Column(String(50), nullable=True)

    # Metadata
    camera_make = Column(String(100), nullable=True)
    camera_model = Column(String(100), nullable=True)
    lens_model = Column(String(100), nullable=True)
    iso = Column(Integer, nullable=True)
    aperture = Column(String(20), nullable=True)
    shutter_speed = Column(String(20), nullable=True)
    capture_date = Column(String(50), nullable=True)

    # Scoring
    total_score = Column(Float, default=0.0, nullable=False)
    score_count = Column(Integer, default=0, nullable=False)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="submissions")
    competition = relationship("Competition", back_populates="submissions")
    scores = relationship("Score", back_populates="submission", cascade="all, delete-orphan")
    score_audit_logs = relationship("ScoreAuditLog", back_populates="submission")

    def __repr__(self):
        return f"<Submission {self.title} by User#{self.user_id}>"

    @property
    def average_score(self) -> float:
        """Calculate average score"""
        return self.total_score / self.score_count if self.score_count > 0 else 0.0
