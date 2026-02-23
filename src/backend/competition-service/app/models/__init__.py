"""
Database Models for Competition Service
"""

from app.models.user import User
from app.models.competition import Competition
from app.models.submission import Submission
from app.models.judge import Judge, JudgeAssignment
from app.models.score import Score, ScoreAuditLog, ScoreActionType
from app.models.camera_reputation import CameraFingerprint, CameraTrustProfile, PRNUComparison
from app.models.judge_analytics import JudgeScoringProfile, JudgeConsensusAnalysis, CredentialSharingDetection

__all__ = [
    "User",
    "Competition",
    "Submission",
    "Judge",
    "JudgeAssignment",
    "Score",
    "ScoreAuditLog",
    "ScoreActionType",
    "CameraFingerprint",
    "CameraTrustProfile",
    "PRNUComparison",
    "JudgeScoringProfile",
    "JudgeConsensusAnalysis",
    "CredentialSharingDetection",
]
