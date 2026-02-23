"""
Test suite for v2.0 database models (Camera Reputation & Judge Analytics)

Validates model structure, relationships, and constraints.
"""

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError


def test_camera_fingerprint_model():
    """Test CameraFingerprint model structure"""
    from app.models import CameraFingerprint

    # Check table name
    assert CameraFingerprint.__tablename__ == "camera_fingerprints"

    # Check required columns exist
    inspector = inspect(CameraFingerprint)
    columns = {col.name for col in inspector.columns}

    required_columns = {
        'id', 'submission_id', 'user_id', 'camera_make', 'camera_model',
        'prnu_signature', 'prnu_energy', 'prnu_hash', 'similarity_to_profile',
        'trust_boost_applied', 'capture_context', 'verified',
        'created_at', 'updated_at'
    }

    assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"
    print(f"✓ CameraFingerprint has all {len(required_columns)} required columns")


def test_camera_trust_profile_model():
    """Test CameraTrustProfile model structure"""
    from app.models import CameraTrustProfile

    assert CameraTrustProfile.__tablename__ == "camera_trust_profiles"

    inspector = inspect(CameraTrustProfile)
    columns = {col.name for col in inspector.columns}

    required_columns = {
        'id', 'camera_make', 'camera_model', 'total_submissions',
        'authentic_count', 'suspicious_count', 'ai_generated_count',
        'rejected_count', 'avg_trust_score', 'prnu_pattern_stability',
        'avg_prnu_energy', 'last_updated', 'created_at', 'updated_at'
    }

    assert required_columns.issubset(columns)
    print(f"✓ CameraTrustProfile has all {len(required_columns)} required columns")

    # Test property methods
    profile = CameraTrustProfile(
        camera_make="Canon",
        camera_model="EOS R5",
        total_submissions=100,
        authentic_count=85,
        rejected_count=10,
        ai_generated_count=5
    )

    assert profile.authenticity_rate == 85.0
    assert profile.rejection_rate == 15.0
    print("✓ CameraTrustProfile properties work correctly")


def test_prnu_comparison_model():
    """Test PRNUComparison model structure"""
    from app.models import PRNUComparison

    assert PRNUComparison.__tablename__ == "prnu_comparisons"

    inspector = inspect(PRNUComparison)
    columns = {col.name for col in inspector.columns}

    required_columns = {
        'id', 'fingerprint1_id', 'fingerprint2_id', 'similarity_score',
        'distance_metric', 'correlation_coefficient', 'same_camera',
        'same_user', 'comparison_details', 'created_at', 'updated_at'
    }

    assert required_columns.issubset(columns)
    print(f"✓ PRNUComparison has all {len(required_columns)} required columns")


def test_judge_scoring_profile_model():
    """Test JudgeScoringProfile model structure"""
    from app.models import JudgeScoringProfile

    assert JudgeScoringProfile.__tablename__ == "judge_scoring_profiles"

    inspector = inspect(JudgeScoringProfile)
    columns = {col.name for col in inspector.columns}

    required_columns = {
        'id', 'judge_id', 'competition_id', 'submission_count',
        'avg_score_given', 'score_std_dev', 'score_range_min',
        'score_range_max', 'bias_score', 'consistency_score',
        'score_distribution', 'outlier_count', 'extreme_scores_ratio',
        'avg_scoring_time_seconds', 'scoring_time_variance',
        'last_analyzed', 'created_at', 'updated_at'
    }

    assert required_columns.issubset(columns)
    print(f"✓ JudgeScoringProfile has all {len(required_columns)} required columns")

    # Test bias category property
    profile = JudgeScoringProfile(bias_score=0.7)
    assert profile.bias_category == "lenient"

    profile.bias_score = -0.7
    assert profile.bias_category == "harsh"

    profile.bias_score = 0.2
    assert profile.bias_category == "fair"

    profile.bias_score = None
    assert profile.bias_category == "unknown"

    print("✓ JudgeScoringProfile bias_category property works correctly")


def test_judge_consensus_analysis_model():
    """Test JudgeConsensusAnalysis model structure"""
    from app.models import JudgeConsensusAnalysis

    assert JudgeConsensusAnalysis.__tablename__ == "judge_consensus_analysis"

    inspector = inspect(JudgeConsensusAnalysis)
    columns = {col.name for col in inspector.columns}

    required_columns = {
        'id', 'competition_id', 'submission_id', 'judge_count',
        'scores_received', 'score_mean', 'score_std_dev', 'score_range',
        'icc_value', 'score_agreement_ratio', 'coefficient_of_variation',
        'outlier_judges', 'outlier_scores', 'consensus_verdict',
        'confidence_level', 'flagged_for_review', 'review_reason',
        'reviewed', 'analysis_timestamp', 'created_at', 'updated_at'
    }

    assert required_columns.issubset(columns)
    print(f"✓ JudgeConsensusAnalysis has all {len(required_columns)} required columns")

    # Test consensus quality property
    analysis = JudgeConsensusAnalysis(icc_value=0.80)
    assert analysis.consensus_quality == "Excellent"

    analysis.icc_value = 0.65
    assert analysis.consensus_quality == "Good"

    analysis.icc_value = 0.45
    assert analysis.consensus_quality == "Fair"

    analysis.icc_value = 0.30
    assert analysis.consensus_quality == "Poor"

    analysis.icc_value = None
    assert analysis.consensus_quality == "Not calculated"

    print("✓ JudgeConsensusAnalysis consensus_quality property works correctly")


def test_credential_sharing_detection_model():
    """Test CredentialSharingDetection model structure"""
    from app.models import CredentialSharingDetection

    assert CredentialSharingDetection.__tablename__ == "credential_sharing_detection"

    inspector = inspect(CredentialSharingDetection)
    columns = {col.name for col in inspector.columns}

    required_columns = {
        'id', 'competition_id', 'judge_id', 'unique_ip_count',
        'unique_session_count', 'unique_user_agent_count', 'ip_addresses',
        'session_ids', 'time_gap_anomalies', 'geographic_inconsistencies',
        'risk_score', 'risk_level', 'risk_factors', 'alert_triggered',
        'investigation_status', 'investigation_notes', 'reviewed_by',
        'reviewed_at', 'created_at', 'updated_at'
    }

    assert required_columns.issubset(columns)
    print(f"✓ CredentialSharingDetection has all {len(required_columns)} required columns")

    # Test is_suspicious property
    detection = CredentialSharingDetection(risk_score=0.7)
    assert detection.is_suspicious is True

    detection.risk_score = 0.4
    assert detection.is_suspicious is False

    detection.risk_score = None
    assert detection.is_suspicious is False

    print("✓ CredentialSharingDetection is_suspicious property works correctly")


def test_submission_model_updated():
    """Test that Submission model has new v2.0 columns"""
    from app.models import Submission

    inspector = inspect(Submission)
    columns = {col.name for col in inspector.columns}

    new_columns = {
        'prnu_fingerprint_id',
        'prnu_extracted_energy',
        'camera_trust_score'
    }

    assert new_columns.issubset(columns), f"Missing v2.0 columns: {new_columns - columns}"
    print("✓ Submission model has all v2.0 camera reputation columns")


def test_model_relationships():
    """Test that relationships are properly defined"""
    from app.models import CameraFingerprint, Submission, PRNUComparison

    # Check CameraFingerprint relationships
    assert hasattr(CameraFingerprint, 'submission'), "Missing 'submission' relationship"
    assert hasattr(CameraFingerprint, 'user'), "Missing 'user' relationship"
    assert hasattr(CameraFingerprint, 'comparisons_as_fingerprint1'), "Missing comparison relationships"
    assert hasattr(CameraFingerprint, 'comparisons_as_fingerprint2'), "Missing comparison relationships"

    # Check Submission relationship
    assert hasattr(Submission, 'camera_fingerprint'), "Missing 'camera_fingerprint' relationship"

    # Check PRNUComparison relationships
    assert hasattr(PRNUComparison, 'fingerprint1'), "Missing 'fingerprint1' relationship"
    assert hasattr(PRNUComparison, 'fingerprint2'), "Missing 'fingerprint2' relationship"

    print("✓ All model relationships are properly defined")


def test_model_repr_methods():
    """Test that __repr__ methods work"""
    from app.models import (
        CameraFingerprint, CameraTrustProfile, PRNUComparison,
        JudgeScoringProfile, JudgeConsensusAnalysis, CredentialSharingDetection
    )

    # Test each repr
    fp = CameraFingerprint(camera_make="Canon", camera_model="EOS R5", submission_id=1)
    assert "Canon" in repr(fp) and "EOS R5" in repr(fp)

    profile = CameraTrustProfile(camera_make="Sony", camera_model="A7R IV", total_submissions=50)
    assert "Sony" in repr(profile) and "50" in repr(profile)

    comparison = PRNUComparison(fingerprint1_id=1, fingerprint2_id=2, similarity_score=0.87)
    assert "0.87" in repr(comparison)

    judge_profile = JudgeScoringProfile(judge_id=5, competition_id=10)
    assert "5" in repr(judge_profile) and "10" in repr(judge_profile)

    consensus = JudgeConsensusAnalysis(submission_id=20, icc_value=0.75)
    assert "20" in repr(consensus)

    detection = CredentialSharingDetection(judge_id=3, risk_level="high")
    assert "high" in repr(detection) or "Unknown" in repr(detection)

    print("✓ All __repr__ methods work correctly")


if __name__ == "__main__":
    """Run all tests manually"""
    print("\n" + "="*60)
    print("Testing v2.0 Database Models")
    print("="*60 + "\n")

    try:
        test_camera_fingerprint_model()
        test_camera_trust_profile_model()
        test_prnu_comparison_model()
        test_judge_scoring_profile_model()
        test_judge_consensus_analysis_model()
        test_credential_sharing_detection_model()
        test_submission_model_updated()
        test_model_relationships()
        test_model_repr_methods()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
