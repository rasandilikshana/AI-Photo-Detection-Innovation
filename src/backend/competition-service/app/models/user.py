"""
User model for authentication and profile management
"""

from sqlalchemy import Column, String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """User roles"""

    PARTICIPANT = "participant"
    JUDGE = "judge"
    ORGANIZER = "organizer"
    ADMIN = "admin"


class User(BaseModel):
    """User model"""

    __tablename__ = "users"

    # Authentication
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Profile
    full_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    bio = Column(String(1000), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Role
    role = Column(SQLEnum(UserRole), default=UserRole.PARTICIPANT, nullable=False)

    # Relationships
    submissions = relationship(
        "Submission", back_populates="user", cascade="all, delete-orphan",
        foreign_keys="[Submission.user_id]"
    )
    competitions_created = relationship(
        "Competition", back_populates="organizer", cascade="all, delete-orphan"
    )
    judge_assignments = relationship(
        "JudgeAssignment", back_populates="judge", cascade="all, delete-orphan"
    )
    scores_given = relationship("Score", back_populates="judge")
    score_audit_logs = relationship("ScoreAuditLog", back_populates="judge")

    def __repr__(self):
        return f"<User {self.username} ({self.email})>"
