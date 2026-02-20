"""
Competition model for managing photo competitions
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.models.base import BaseModel


class CompetitionStatus(str, enum.Enum):
    """Competition status"""

    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    JUDGING = "judging"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Competition(BaseModel):
    """Competition model"""

    __tablename__ = "competitions"

    # Basic Info
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    rules = Column(Text, nullable=True)
    slug = Column(String(255), unique=True, index=True, nullable=False)

    # Dates
    submission_start = Column(DateTime, nullable=False)
    submission_end = Column(DateTime, nullable=False)
    judging_start = Column(DateTime, nullable=True)
    judging_end = Column(DateTime, nullable=True)
    results_date = Column(DateTime, nullable=True)

    # Status
    status = Column(SQLEnum(CompetitionStatus), default=CompetitionStatus.DRAFT, nullable=False)

    # Settings
    max_submissions_per_user = Column(Integer, default=5, nullable=False)
    require_raw_files = Column(Boolean, default=True, nullable=False)
    allow_ai_generated = Column(Boolean, default=False, nullable=False)
    entry_fee = Column(Integer, default=0, nullable=False)  # in cents

    # Media
    banner_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)

    # Prizes
    prize_description = Column(Text, nullable=True)
    prize_amount = Column(Integer, nullable=True)  # in cents

    # Organizer
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organizer = relationship("User", back_populates="competitions_created")

    # Relationships
    submissions = relationship("Submission", back_populates="competition", cascade="all, delete-orphan")
    judge_assignments = relationship("JudgeAssignment", back_populates="competition", cascade="all, delete-orphan")
    score_audit_logs = relationship("ScoreAuditLog", back_populates="competition")

    def __repr__(self):
        return f"<Competition {self.title} ({self.status})>"

    @property
    def is_accepting_submissions(self) -> bool:
        """Check if competition is accepting submissions"""
        now = datetime.utcnow()
        return (
            self.status == CompetitionStatus.OPEN
            and self.submission_start <= now <= self.submission_end
        )

    @property
    def is_in_judging_phase(self) -> bool:
        """Check if competition is in judging phase"""
        now = datetime.utcnow()
        return (
            self.status == CompetitionStatus.JUDGING
            and self.judging_start
            and self.judging_end
            and self.judging_start <= now <= self.judging_end
        )
