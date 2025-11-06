"""
Score model for judging submissions
"""

from sqlalchemy import Column, Integer, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


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

    def __repr__(self):
        return f"<Score {self.overall_score}/10 by Judge#{self.judge_id}>"

    def calculate_overall_score(self):
        """Calculate weighted overall score"""
        self.overall_score = (
            self.composition_score * 0.4
            + self.technical_score * 0.3
            + self.creativity_score * 0.3
        )
