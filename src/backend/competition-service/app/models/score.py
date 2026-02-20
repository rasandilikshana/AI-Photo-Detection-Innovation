"""
Score model for judging submissions
"""

from sqlalchemy import Column, Integer, ForeignKey, Float, Text, String, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class ScoreActionType(str, enum.Enum):
    """Types of scoring actions"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ScoreAuditLog(BaseModel):
    """
    Audit log for tracking all scoring actions.
    Records each scoring action with client details for tracking
    when multiple judges share the same credentials.
    """

    __tablename__ = "score_audit_logs"

    # Action details
    action_type = Column(Enum(ScoreActionType), nullable=False)

    # Score snapshot (what was submitted)
    composition_score = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)
    creativity_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    comments = Column(Text, nullable=True)

    # Previous values (for updates)
    prev_composition_score = Column(Float, nullable=True)
    prev_technical_score = Column(Float, nullable=True)
    prev_creativity_score = Column(Float, nullable=True)
    prev_overall_score = Column(Float, nullable=True)
    prev_comments = Column(Text, nullable=True)

    # Client identification
    ip_address = Column(String(45), nullable=True)  # IPv6 can be up to 45 chars
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(100), nullable=True)

    # Optional: Judge identifier (for when friends test with same account)
    judge_identifier = Column(String(100), nullable=True)  # Optional name/identifier

    # Foreign Keys
    score_id = Column(Integer, ForeignKey("scores.id"), nullable=True)  # Nullable for deletes
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    judge_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)

    # Relationships
    score = relationship("Score", back_populates="audit_logs")
    submission = relationship("Submission", back_populates="score_audit_logs")
    judge = relationship("User", back_populates="score_audit_logs")
    competition = relationship("Competition", back_populates="score_audit_logs")

    def __repr__(self):
        return f"<ScoreAuditLog {self.action_type} by Judge#{self.judge_id} from {self.ip_address}>"


class Score(BaseModel):
    """Score model for judge ratings"""

    __tablename__ = "scores"

    # Score Details
    composition_score = Column(Float, nullable=False)  # 0-10
    technical_score = Column(Float, nullable=False)  # 0-10
    creativity_score = Column(Float, nullable=False)  # 0-10
    overall_score = Column(Float, nullable=False)  # 0-10
    comments = Column(Text, nullable=True)

    # Foreign Keys
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    judge_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    submission = relationship("Submission", back_populates="scores")
    judge = relationship("User", back_populates="scores_given")
    audit_logs = relationship("ScoreAuditLog", back_populates="score", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Score {self.overall_score}/10 by Judge#{self.judge_id}>"

    def calculate_overall_score(self):
        """Calculate weighted overall score"""
        self.overall_score = (
            self.composition_score * 0.4
            + self.technical_score * 0.3
            + self.creativity_score * 0.3
        )
