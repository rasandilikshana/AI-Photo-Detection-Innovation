"""
Judge Analytics and Consensus Models

Tracks judge scoring patterns, detects bias, and identifies credential sharing.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean, Text, DateTime, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

# PostgreSQL-native types with portable fallbacks for other dialects (e.g. SQLite in tests)
PortableJSONB = JSON().with_variant(JSONB(), "postgresql")
PortableIntArray = JSON().with_variant(ARRAY(Integer), "postgresql")
PortableStrArray = JSON().with_variant(ARRAY(String), "postgresql")


class JudgeScoringProfile(BaseModel):
    """
    Statistical profile of each judge's scoring behavior.
    Used for bias detection and fairness analysis.
    """

    __tablename__ = "judge_scoring_profiles"
    __table_args__ = (
        UniqueConstraint('judge_id', 'competition_id', name='uq_judge_competition'),
    )

    # Foreign Keys
    judge_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Scoring Statistics
    submission_count = Column(Integer, default=0)
    avg_score_given = Column(Float, nullable=True)
    score_std_dev = Column(Float, nullable=True)
    score_range_min = Column(Float, nullable=True)
    score_range_max = Column(Float, nullable=True)

    # Bias Metrics
    bias_score = Column(Float, nullable=True)  # Z-score: >0 lenient, <0 harsh, ~0 fair
    consistency_score = Column(Float, nullable=True)  # 0.0 - 1.0 (1.0 = highly consistent)

    # Distribution Analysis
    score_distribution = Column(PortableJSONB, nullable=True)  # {1: count, 2: count, ...}
    outlier_count = Column(Integer, default=0)
    extreme_scores_ratio = Column(Float, nullable=True)  # % of 1s and 10s

    # Timing Patterns
    avg_scoring_time_seconds = Column(Float, nullable=True)
    scoring_time_variance = Column(Float, nullable=True)

    # Update Tracking
    last_analyzed = Column(DateTime, nullable=True)

    # Relationships
    judge = relationship("User")
    competition = relationship("Competition")

    def __repr__(self):
        return f"<JudgeScoringProfile Judge#{self.judge_id} - Competition#{self.competition_id}>"

    @property
    def bias_category(self) -> str:
        """Categorize bias level"""
        if self.bias_score is None:
            return "unknown"
        if abs(self.bias_score) < 0.5:
            return "fair"
        elif self.bias_score > 0.5:
            return "lenient"
        else:
            return "harsh"


class JudgeConsensusAnalysis(BaseModel):
    """
    Consensus analysis for each submission scored by multiple judges.
    Uses ICC (Intraclass Correlation Coefficient) to measure agreement.
    """

    __tablename__ = "judge_consensus_analysis"
    __table_args__ = (
        UniqueConstraint('competition_id', 'submission_id', name='uq_competition_submission'),
    )

    # Foreign Keys
    competition_id = Column(Integer, ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Judge Participation
    judge_count = Column(Integer, nullable=False)
    scores_received = Column(PortableJSONB, nullable=False)  # {judge_id: score}

    # Statistical Measures
    score_mean = Column(Float, nullable=True)
    score_std_dev = Column(Float, nullable=True)
    score_range = Column(Float, nullable=True)  # max - min

    # Consensus Metrics
    icc_value = Column(Float, nullable=True)  # Intraclass Correlation Coefficient
    score_agreement_ratio = Column(Float, nullable=True)  # % of scores within ±1 of mean
    coefficient_of_variation = Column(Float, nullable=True)  # std_dev / mean

    # Outlier Detection
    outlier_judges = Column(PortableIntArray, nullable=True)  # IDs of judges with outlier scores
    outlier_scores = Column(PortableJSONB, nullable=True)  # {judge_id: z_score}

    # Consensus Decision
    consensus_verdict = Column(String(50), nullable=True)  # strong/moderate/weak/poor
    confidence_level = Column(Float, nullable=True)  # 0.0 - 1.0

    # Review Flags
    flagged_for_review = Column(Boolean, default=False)
    review_reason = Column(Text, nullable=True)
    reviewed = Column(Boolean, default=False)

    # Metadata
    analysis_timestamp = Column(DateTime, nullable=True)

    # Relationships
    competition = relationship("Competition")
    submission = relationship("Submission")

    def __repr__(self):
        icc = f"{self.icc_value:.3f}" if self.icc_value is not None else "N/A"
        return f"<JudgeConsensusAnalysis Submission#{self.submission_id} - ICC={icc}>"

    @property
    def consensus_quality(self) -> str:
        """Get human-readable consensus quality"""
        if self.icc_value is None:
            return "Not calculated"
        if self.icc_value >= 0.75:
            return "Excellent"
        elif self.icc_value >= 0.60:
            return "Good"
        elif self.icc_value >= 0.40:
            return "Fair"
        else:
            return "Poor"


class CredentialSharingDetection(BaseModel):
    """
    Monitors judge activity patterns to detect credential sharing.
    Tracks IP addresses, sessions, and geographic inconsistencies.
    """

    __tablename__ = "credential_sharing_detection"

    # Foreign Keys
    competition_id = Column(Integer, ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False, index=True)
    judge_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Activity Metrics
    unique_ip_count = Column(Integer, nullable=True)
    unique_session_count = Column(Integer, nullable=True)
    unique_user_agent_count = Column(Integer, nullable=True)

    # Activity Data
    ip_addresses = Column(PortableStrArray, nullable=True)
    session_ids = Column(PortableStrArray, nullable=True)

    # Anomaly Detection
    time_gap_anomalies = Column(PortableJSONB, nullable=True)  # [{from, to, gap_seconds, expected_min}]
    geographic_inconsistencies = Column(PortableJSONB, nullable=True)  # [{ip1, ip2, distance_km, time_seconds}]

    # Risk Assessment
    risk_score = Column(Float, nullable=True, index=True)  # 0.0 - 1.0
    risk_level = Column(String(50), nullable=True)  # low/medium/high
    risk_factors = Column(PortableStrArray, nullable=True)

    # Alert Management
    alert_triggered = Column(Boolean, default=False)
    investigation_status = Column(String(50), default="pending", index=True)  # pending/reviewing/resolved
    investigation_notes = Column(Text, nullable=True)

    # Review Tracking
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    competition = relationship("Competition")
    judge = relationship("User", foreign_keys=[judge_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<CredentialSharingDetection Judge#{self.judge_id} - Risk={self.risk_level or 'Unknown'}>"

    @property
    def is_suspicious(self) -> bool:
        """Check if activity is suspicious"""
        if self.risk_score is None:
            return False
        return self.risk_score >= 0.6
