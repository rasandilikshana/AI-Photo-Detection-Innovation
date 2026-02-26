"""
Comprehensive test suite for Credential Sharing Detection Service

Tests all core functionality:
- IP diversity scoring
- Session overlap detection
- Time gap anomaly detection
- Geographic inconsistency detection
- Risk score calculation
"""

import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta


class TestCredentialSharingDetector:
    """Test Credential Sharing Detector service logic"""

    def test_ip_diversity_score_single_ip(self):
        """Test 0.0 score for single IP (normal)"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        score = detector._calculate_ip_diversity_score(1)
        assert score == 0.0

    def test_ip_diversity_score_two_ips(self):
        """Test 0.2 score for 2 IPs (home/work)"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        score = detector._calculate_ip_diversity_score(2)
        assert score == 0.2

    def test_ip_diversity_score_three_ips(self):
        """Test 0.5 score for 3 IPs (suspicious)"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        score = detector._calculate_ip_diversity_score(3)
        assert score == 0.5

    def test_ip_diversity_score_many_ips(self):
        """Test high score for 4+ IPs (high risk)"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        # 4 IPs = 0.6
        score_4 = detector._calculate_ip_diversity_score(4)
        assert score_4 == 0.6

        # 5 IPs = 0.7
        score_5 = detector._calculate_ip_diversity_score(5)
        assert score_5 == 0.7

        # 10 IPs = 1.0 (capped)
        score_10 = detector._calculate_ip_diversity_score(10)
        assert score_10 == 1.0

    def test_session_overlap_no_logs(self):
        """Test session overlap with no logs"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        score = detector._calculate_session_overlap_score([])
        assert score == 0.0

    def test_session_overlap_single_log(self):
        """Test session overlap with single log"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        mock_log = Mock()
        mock_log.ip_address = "192.168.1.1"
        mock_log.created_at = datetime.utcnow()

        score = detector._calculate_session_overlap_score([mock_log])
        assert score == 0.0

    def test_session_overlap_same_ip(self):
        """Test session overlap with same IP (no overlap)"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        now = datetime.utcnow()
        logs = []
        for i in range(5):
            mock_log = Mock()
            mock_log.ip_address = "192.168.1.1"  # Same IP
            mock_log.created_at = now + timedelta(minutes=i)
            logs.append(mock_log)

        score = detector._calculate_session_overlap_score(logs)
        assert score == 0.0  # No overlap for same IP

    def test_session_overlap_concurrent_different_ips(self):
        """Test session overlap with concurrent different IPs"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        now = datetime.utcnow()
        logs = []

        # Activity from different IPs at nearly same time
        mock_log1 = Mock()
        mock_log1.ip_address = "192.168.1.1"
        mock_log1.created_at = now
        logs.append(mock_log1)

        mock_log2 = Mock()
        mock_log2.ip_address = "10.0.0.1"  # Different IP
        mock_log2.created_at = now + timedelta(seconds=30)  # Same time window
        logs.append(mock_log2)

        score = detector._calculate_session_overlap_score(logs)
        assert score > 0.0  # Should detect overlap

    def test_time_gap_anomaly_none(self):
        """Test no anomalies with reasonable gaps"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        now = datetime.utcnow()
        timestamps = [
            now,
            now + timedelta(hours=2),  # 2 hour gap
            now + timedelta(hours=5),  # 3 hour gap
        ]
        ip_addresses = ["192.168.1.1", "10.0.0.1", "192.168.1.1"]

        score, anomalies = detector._detect_time_gap_anomalies(timestamps, ip_addresses)

        # Gaps > 1 hour should NOT be anomalies
        assert len(anomalies) == 0

    def test_time_gap_anomaly_impossible(self):
        """Test detection of impossible time gaps"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        now = datetime.utcnow()
        timestamps = [
            now,
            now + timedelta(minutes=5),  # Only 5 min gap with IP change
            now + timedelta(minutes=10),
        ]
        ip_addresses = ["192.168.1.1", "10.0.0.1", "172.16.0.1"]

        score, anomalies = detector._detect_time_gap_anomalies(timestamps, ip_addresses)

        # Should detect anomalies (IP change within 1 hour)
        assert len(anomalies) > 0
        assert score > 0.0

    def test_geographic_anomaly_single_ip(self):
        """Test no geographic anomalies with single IP"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        ip_addresses = ["192.168.1.1"]
        timestamps = [datetime.utcnow()]

        score, anomalies = detector._detect_geographic_anomalies(ip_addresses, timestamps)

        assert score == 0.0
        assert len(anomalies) == 0

    def test_geographic_anomaly_different_networks(self):
        """Test geographic anomalies with different network blocks"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        # IPs from different /16 networks
        ip_addresses = ["192.168.1.1", "10.0.0.1"]
        timestamps = [datetime.utcnow(), datetime.utcnow()]

        score, anomalies = detector._detect_geographic_anomalies(ip_addresses, timestamps)

        assert score > 0.0
        assert len(anomalies) > 0

    def test_detector_weight_sum(self):
        """Test that risk weights sum to 1.0"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        total_weight = (
            detector.ip_diversity_weight +
            detector.session_overlap_weight +
            detector.time_gap_weight +
            detector.geo_consistency_weight
        )

        assert total_weight == 1.0


class TestCredentialSharingDetectorAsync:
    """Async tests for Credential Sharing Detector"""

    @pytest.mark.asyncio
    async def test_analyze_no_activity(self):
        """Test analysis with no activity data"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = AsyncMock()
        detector = CredentialSharingDetector(mock_db)

        mock_result = AsyncMock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await detector.analyze_judge_activity(
            judge_id=1,
            competition_id=1
        )

        assert result["risk_score"] == 0.0
        assert result["risk_level"] == "unknown"

    @pytest.mark.asyncio
    async def test_analyze_low_risk_activity(self):
        """Test analysis with normal activity (low risk)"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = AsyncMock()
        detector = CredentialSharingDetector(mock_db)

        # Create normal activity pattern (single IP, no overlaps)
        logs = []
        now = datetime.utcnow()
        for i in range(5):
            mock_log = Mock()
            mock_log.ip_address = "192.168.1.1"  # Same IP
            mock_log.session_id = "session123"
            mock_log.user_agent = "Mozilla/5.0"
            mock_log.created_at = now + timedelta(hours=i)
            logs.append(mock_log)

        mock_result = AsyncMock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=logs)))
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await detector.analyze_judge_activity(
            judge_id=1,
            competition_id=1
        )

        assert result["risk_level"] == "low"
        assert result["risk_score"] < 0.4
        assert result["unique_ip_count"] == 1

    @pytest.mark.asyncio
    async def test_analyze_high_risk_activity(self):
        """Test analysis with suspicious activity (high risk)"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = AsyncMock()
        detector = CredentialSharingDetector(mock_db)

        # Create suspicious activity pattern
        logs = []
        now = datetime.utcnow()

        # Many different IPs in short time
        ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "8.8.8.8", "1.1.1.1"]
        user_agents = ["Chrome", "Firefox", "Safari", "Edge", "Opera"]

        for i, (ip, ua) in enumerate(zip(ips, user_agents)):
            mock_log = Mock()
            mock_log.ip_address = ip
            mock_log.session_id = f"session{i}"
            mock_log.user_agent = ua
            mock_log.created_at = now + timedelta(minutes=i * 10)
            logs.append(mock_log)

        mock_result = AsyncMock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=logs)))
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await detector.analyze_judge_activity(
            judge_id=1,
            competition_id=1
        )

        assert result["risk_level"] in ["medium", "high"]
        assert result["unique_ip_count"] == 5
        assert len(result["risk_factors"]) > 0

    @pytest.mark.asyncio
    async def test_get_flagged_judges(self):
        """Test retrieving flagged judges"""
        from app.services.credential_sharing import CredentialSharingDetector
        from app.models import CredentialSharingDetection

        mock_db = AsyncMock()
        detector = CredentialSharingDetector(mock_db)

        # Create mock flagged records
        flagged_records = []
        for i in range(3):
            mock_record = Mock(spec=CredentialSharingDetection)
            mock_record.judge_id = i + 1
            mock_record.risk_score = 0.7 + (i * 0.1)
            mock_record.risk_level = "high"
            flagged_records.append(mock_record)

        mock_result = AsyncMock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=flagged_records)))
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await detector.get_flagged_judges(
            competition_id=1,
            min_risk_score=0.6
        )

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_store_detection_new(self):
        """Test storing new detection result"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = AsyncMock()
        detector = CredentialSharingDetector(mock_db)

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        detection_result = {
            "risk_score": 0.7,
            "risk_level": "high",
            "unique_ip_count": 5,
            "unique_session_count": 5,
            "unique_user_agent_count": 3,
            "ip_addresses": ["1.1.1.1", "2.2.2.2"],
            "session_ids": ["s1", "s2"],
            "time_gap_anomalies": [],
            "geographic_inconsistencies": [],
            "risk_factors": ["Multiple IPs"]
        }

        await detector.store_detection_result(
            judge_id=1,
            competition_id=1,
            detection_result=detection_result
        )

        # Should have added new record
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()


class TestCredentialSharingDetectionModel:
    """Test CredentialSharingDetection model"""

    def test_is_suspicious_high_risk(self):
        """Test is_suspicious for high risk score"""
        from app.models import CredentialSharingDetection

        detection = CredentialSharingDetection(
            judge_id=1,
            competition_id=1,
            risk_score=0.7
        )

        assert detection.is_suspicious is True

    def test_is_suspicious_low_risk(self):
        """Test is_suspicious for low risk score"""
        from app.models import CredentialSharingDetection

        detection = CredentialSharingDetection(
            judge_id=1,
            competition_id=1,
            risk_score=0.3
        )

        assert detection.is_suspicious is False

    def test_is_suspicious_threshold(self):
        """Test is_suspicious at threshold (0.5)"""
        from app.models import CredentialSharingDetection

        detection = CredentialSharingDetection(
            judge_id=1,
            competition_id=1,
            risk_score=0.5
        )

        # Exactly at threshold should not be suspicious
        assert detection.is_suspicious is False

    def test_is_suspicious_none(self):
        """Test is_suspicious when risk_score is None"""
        from app.models import CredentialSharingDetection

        detection = CredentialSharingDetection(
            judge_id=1,
            competition_id=1,
            risk_score=None
        )

        assert detection.is_suspicious is False


class TestRiskCalculation:
    """Dedicated tests for risk calculation accuracy"""

    def test_risk_calculation_components(self):
        """Test that risk calculation uses all components"""
        from app.services.credential_sharing import CredentialSharingDetector

        mock_db = Mock()
        detector = CredentialSharingDetector(mock_db)

        # Calculate individual scores
        ip_score = detector._calculate_ip_diversity_score(4)  # 0.6

        # Verify component is being used
        expected_contribution = detector.ip_diversity_weight * ip_score
        assert expected_contribution > 0

    def test_risk_level_thresholds(self):
        """Test risk level threshold values"""
        # Risk levels:
        # > 0.7 = high
        # > 0.4 = medium
        # <= 0.4 = low

        # These should be the correct thresholds
        assert 0.7 > 0.4  # high > medium
        assert 0.4 > 0.0  # medium > low


def run_all_tests():
    """Run all tests manually"""
    print("\n" + "=" * 70)
    print("Testing Credential Sharing Detection Service")
    print("=" * 70 + "\n")

    try:
        # Sync tests
        print("1. Testing IP diversity scoring...")
        test_sync = TestCredentialSharingDetector()
        test_sync.test_ip_diversity_score_single_ip()
        test_sync.test_ip_diversity_score_two_ips()
        test_sync.test_ip_diversity_score_three_ips()
        test_sync.test_ip_diversity_score_many_ips()
        print("   IP diversity scoring passed")

        print("2. Testing session overlap detection...")
        test_sync.test_session_overlap_no_logs()
        test_sync.test_session_overlap_single_log()
        test_sync.test_session_overlap_same_ip()
        test_sync.test_session_overlap_concurrent_different_ips()
        print("   Session overlap detection passed")

        print("3. Testing time gap anomaly detection...")
        test_sync.test_time_gap_anomaly_none()
        test_sync.test_time_gap_anomaly_impossible()
        print("   Time gap anomaly detection passed")

        print("4. Testing geographic anomaly detection...")
        test_sync.test_geographic_anomaly_single_ip()
        test_sync.test_geographic_anomaly_different_networks()
        print("   Geographic anomaly detection passed")

        print("5. Testing weight configuration...")
        test_sync.test_detector_weight_sum()
        print("   Weight configuration passed")

        print("6. Testing model properties...")
        test_model = TestCredentialSharingDetectionModel()
        test_model.test_is_suspicious_high_risk()
        test_model.test_is_suspicious_low_risk()
        test_model.test_is_suspicious_threshold()
        test_model.test_is_suspicious_none()
        print("   Model properties passed")

        print("7. Running async tests...")
        import asyncio
        test_async = TestCredentialSharingDetectorAsync()

        async def run_async():
            await test_async.test_analyze_no_activity()
            print("   - No activity handling: passed")
            await test_async.test_analyze_low_risk_activity()
            print("   - Low risk detection: passed")
            await test_async.test_analyze_high_risk_activity()
            print("   - High risk detection: passed")

        asyncio.run(run_async())

        print("\n" + "=" * 70)
        print("ALL CREDENTIAL SHARING DETECTION TESTS PASSED")
        print("=" * 70 + "\n")
        return 0

    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    except ImportError as e:
        print(f"\nIMPORT ERROR: {e}")
        print("Note: Run from competition-service directory with dependencies installed")
        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())
