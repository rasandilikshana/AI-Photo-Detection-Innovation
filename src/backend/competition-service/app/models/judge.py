"""
Judge and JudgeAssignment models
"""

from sqlalchemy import Column, Integer, ForeignKey, Boolean, String, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Judge(BaseModel):
    """Judge model (extends User)"""

    __tablename__ = "judges"

    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    specialization = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Judge User#{self.user_id}>"


class JudgeAssignment(BaseModel):
    """Judge assignment to competitions"""

    __tablename__ = "judge_assignments"

    judge_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    judge = relationship("User", back_populates="judge_assignments")
    competition = relationship("Competition", back_populates="judge_assignments")

    def __repr__(self):
        return f"<JudgeAssignment Judge#{self.judge_id} -> Competition#{self.competition_id}>"
