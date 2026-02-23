"""
Submission model for photo submissions
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SQLEnum, Text, JSON, Float, DateTime
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

    # Camera Reputation (v2.0)
    prnu_fingerprint_id = Column(Integer, ForeignKey("camera_fingerprints.id"), nullable=True)
    prnu_extracted_energy = Column(Float, nullable=True)
    camera_trust_score = Column(Float, default=0.5, nullable=True)

    # Analysis Error (when AI analysis fails)
    analysis_error = Column(Text, nullable=True)

    # Review/Rejection Info (when judge manually reviews)
    rejection_reason = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="submissions", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    competition = relationship("Competition", back_populates="submissions")
    scores = relationship("Score", back_populates="submission", cascade="all, delete-orphan")
    score_audit_logs = relationship("ScoreAuditLog", back_populates="submission")
    # Removed bidirectional relationship - use camera_fingerprint table to query

    def __repr__(self):
        return f"<Submission {self.title} by User#{self.user_id}>"

    @property
    def average_score(self) -> float:
        """Calculate average score"""
        return self.total_score / self.score_count if self.score_count > 0 else 0.0
