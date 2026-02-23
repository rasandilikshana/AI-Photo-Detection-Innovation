"""
Camera Reputation System Models

Tracks camera PRNU fingerprints and builds trust profiles over time.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean, LargeBinary, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class CameraFingerprint(BaseModel):
    """
    Stores PRNU (Photo Response Non-Uniformity) fingerprints for each submission.
    Used for camera authenticity verification and trust scoring.
    """

    __tablename__ = "camera_fingerprints"

    # Foreign Keys
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Camera Information
    camera_make = Column(String(100), nullable=False, index=True)
    camera_model = Column(String(100), nullable=False, index=True)

    # PRNU Data
    prnu_signature = Column(LargeBinary, nullable=False)  # Compressed PRNU pattern
    prnu_energy = Column(Float, nullable=False)
    prnu_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA256 hash

    # Trust Metrics
    similarity_to_profile = Column(Float, nullable=True)  # Similarity to camera's global profile
    trust_boost_applied = Column(Float, default=0.0)

    # Capture Context
    capture_context = Column(JSONB, nullable=True)  # {iso, aperture, shutter, etc.}

    # Verification Status
    verified = Column(Boolean, default=False)

    # Relationships
    submission = relationship("Submission", back_populates="camera_fingerprint")
    user = relationship("User")
    comparisons_as_fingerprint1 = relationship(
        "PRNUComparison",
        foreign_keys="PRNUComparison.fingerprint1_id",
        back_populates="fingerprint1"
    )
    comparisons_as_fingerprint2 = relationship(
        "PRNUComparison",
        foreign_keys="PRNUComparison.fingerprint2_id",
        back_populates="fingerprint2"
    )

    def __repr__(self):
        return f"<CameraFingerprint {self.camera_make} {self.camera_model} - Submission#{self.submission_id}>"


class CameraTrustProfile(BaseModel):
    """
    Aggregated trust profile for each camera make/model.
    Tracks historical performance and authenticity patterns.
    """

    __tablename__ = "camera_trust_profiles"
    __table_args__ = (
        UniqueConstraint('camera_make', 'camera_model', name='uq_camera_make_model'),
    )

    # Camera Identifier (unique combination)
    camera_make = Column(String(100), nullable=False)
    camera_model = Column(String(100), nullable=False)

    # Submission Statistics
    total_submissions = Column(Integer, default=0)
    authentic_count = Column(Integer, default=0)
    suspicious_count = Column(Integer, default=0)
    ai_generated_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)

    # Trust Metrics
    avg_trust_score = Column(Float, default=0.5)  # 0.0 - 1.0
    prnu_pattern_stability = Column(Float, default=0.0)  # Std dev of similarities
    avg_prnu_energy = Column(Float, nullable=True)

    # Metadata
    last_updated = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<CameraTrustProfile {self.camera_make} {self.camera_model} - {self.total_submissions} submissions>"

    @property
    def authenticity_rate(self) -> float:
        """Calculate percentage of authentic submissions"""
        if self.total_submissions == 0:
            return 0.0
        return (self.authentic_count / self.total_submissions) * 100

    @property
    def rejection_rate(self) -> float:
        """Calculate percentage of rejected submissions"""
        if self.total_submissions == 0:
            return 0.0
        return ((self.rejected_count + self.ai_generated_count) / self.total_submissions) * 100


class PRNUComparison(BaseModel):
    """
    Records pairwise PRNU pattern comparisons.
    Used for tracking similarity history and fraud detection.
    """

    __tablename__ = "prnu_comparisons"

    # Foreign Keys
    fingerprint1_id = Column(Integer, ForeignKey("camera_fingerprints.id", ondelete="CASCADE"), nullable=False, index=True)
    fingerprint2_id = Column(Integer, ForeignKey("camera_fingerprints.id", ondelete="CASCADE"), nullable=False, index=True)

    # Comparison Metrics
    similarity_score = Column(Float, nullable=False)  # 0.0 - 1.0
    distance_metric = Column(String(50), nullable=True)  # e.g., "cosine", "euclidean"
    correlation_coefficient = Column(Float, nullable=True)

    # Camera Context
    same_camera = Column(Boolean, nullable=False)  # Same make/model?
    same_user = Column(Boolean, nullable=False)

    # Detailed Results
    comparison_details = Column(JSONB, nullable=True)  # Full comparison data

    # Relationships
    fingerprint1 = relationship("CameraFingerprint", foreign_keys=[fingerprint1_id], back_populates="comparisons_as_fingerprint1")
    fingerprint2 = relationship("CameraFingerprint", foreign_keys=[fingerprint2_id], back_populates="comparisons_as_fingerprint2")

    def __repr__(self):
        return f"<PRNUComparison FP#{self.fingerprint1_id} vs FP#{self.fingerprint2_id} - {self.similarity_score:.3f}>"
