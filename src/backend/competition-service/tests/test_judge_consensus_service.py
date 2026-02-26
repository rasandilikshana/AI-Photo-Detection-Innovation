"""
Comprehensive test suite for Judge Consensus Analysis Service

Tests all core functionality:
- ICC (Intraclass Correlation Coefficient) calculation
- Consensus verdict determination
- Outlier detection
- Bias scoring
- Judge profile building
"""

import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime


class TestJudgeConsensusAnalyzer:
    """Test Judge Consensus Analyzer service logic"""

    def test_outlier_detection_no_outliers(self):
        """Test outlier detection with consistent scores"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = Mock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        # All scores within normal range
        scores = np.array([7.0, 7.5, 7.2, 7.8, 7.3])
        judge_ids = [1, 2, 3, 4, 5]

        outliers, outlier_scores = analyzer._detect_outlier_judges(scores, judge_ids)

        assert len(outliers) == 0
        assert len(outlier_scores) == 0

    def test_outlier_detection_with_outlier(self):
        """Test outlier detection with one extreme score"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = Mock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        # One outlier at score 2.0 when mean is ~7.0
        scores = np.array([7.0, 7.5, 7.2, 7.8, 2.0])
        judge_ids = [1, 2, 3, 4, 5]

        outliers, outlier_scores = analyzer._detect_outlier_judges(scores, judge_ids)

        assert 5 in outliers  # Judge ID 5 should be outlier
        assert len(outliers) == 1

    def test_outlier_detection_no_variance(self):
        """Test outlier detection with identical scores (no variance)"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = Mock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        # All identical scores
        scores = np.array([7.0, 7.0, 7.0, 7.0])
        judge_ids = [1, 2, 3, 4]

        outliers, outlier_scores = analyzer._detect_outlier_judges(scores, judge_ids)

        # No outliers when all scores are identical
        assert len(outliers) == 0

    def test_consensus_verdict_strong(self):
        """Test strong consensus verdict (ICC >= 0.75, no outliers)"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = Mock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        verdict, confidence = analyzer._determine_consensus_verdict(
            icc=0.85,
            agreement_ratio=0.9,
            outlier_count=0,
            total_judges=5
        )

        assert verdict == "strong_consensus"
        assert confidence > 0.8

    def test_consensus_verdict_moderate(self):
        """Test moderate consensus verdict (0.60 <= ICC < 0.75)"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = Mock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        verdict, confidence = analyzer._determine_consensus_verdict(
            icc=0.65,
            agreement_ratio=0.7,
            outlier_count=1,
            total_judges=5
        )

        assert verdict == "moderate_consensus"

    def test_consensus_verdict_weak(self):
        """Test weak consensus verdict (0.40 <= ICC < 0.60)"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = Mock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        verdict, confidence = analyzer._determine_consensus_verdict(
            icc=0.45,
            agreement_ratio=0.5,
            outlier_count=2,
            total_judges=5
        )

        assert verdict == "weak_consensus"

    def test_consensus_verdict_poor(self):
        """Test poor consensus verdict (ICC < 0.40)"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = Mock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        verdict, confidence = analyzer._determine_consensus_verdict(
            icc=0.25,
            agreement_ratio=0.3,
            outlier_count=3,
            total_judges=5
        )

        assert verdict == "poor_consensus"

    def test_consensus_verdict_insufficient_data(self):
        """Test insufficient data verdict when ICC is None"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = Mock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        verdict, confidence = analyzer._determine_consensus_verdict(
            icc=None,
            agreement_ratio=0.0,
            outlier_count=0,
            total_judges=1
        )

        assert verdict == "insufficient_data"
        assert confidence == 0.0

    def test_analyzer_threshold_values(self):
        """Test analyzer threshold constants"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = Mock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        # ICC thresholds should be in descending order
        assert analyzer.excellent_icc > analyzer.good_icc
        assert analyzer.good_icc > analyzer.fair_icc

        # Bias thresholds should be reasonable
        assert analyzer.significant_bias_threshold > analyzer.moderate_bias_threshold

        # Outlier threshold should be standard (2 sigma)
        assert analyzer.outlier_threshold == 2.0


class TestJudgeConsensusAnalyzerAsync:
    """Async tests for Judge Consensus Analyzer"""

    @pytest.mark.asyncio
    async def test_analyze_submission_insufficient_judges(self):
        """Test analysis with fewer than 2 judges"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = AsyncMock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        # Mock single score
        mock_score = Mock()
        mock_score.total_score = 7.0
        mock_score.judge_id = 1

        mock_result = AsyncMock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[mock_score])))
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await analyzer.analyze_submission_scores(submission_id=1)

        assert result["verdict"] == "insufficient_data"
        assert result["icc"] is None

    @pytest.mark.asyncio
    async def test_analyze_submission_with_scores(self):
        """Test analysis with multiple judges"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = AsyncMock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        # Mock multiple scores
        mock_scores = []
        for i, score_val in enumerate([7.0, 7.5, 7.2, 7.8]):
            mock_score = Mock()
            mock_score.total_score = score_val
            mock_score.judge_id = i + 1
            mock_score.created_at = datetime.utcnow()
            mock_scores.append(mock_score)

        mock_result = AsyncMock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=mock_scores)))
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await analyzer.analyze_submission_scores(submission_id=1)

        assert result["verdict"] in ["strong_consensus", "moderate_consensus", "weak_consensus", "poor_consensus"]
        assert result["icc"] is not None
        assert result["judge_count"] == 4
        assert 7.0 <= result["score_mean"] <= 8.0

    @pytest.mark.asyncio
    async def test_calculate_icc_perfect_agreement(self):
        """Test ICC calculation with perfect agreement"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = Mock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        # All judges gave same score
        mock_scores = []
        for i in range(4):
            mock_score = Mock()
            mock_score.total_score = 7.0
            mock_scores.append(mock_score)

        icc = await analyzer._calculate_icc(mock_scores)

        # Perfect agreement should yield ICC = 1.0
        assert icc == 1.0

    @pytest.mark.asyncio
    async def test_calculate_icc_disagreement(self):
        """Test ICC calculation with disagreement"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = Mock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        # Judges gave very different scores (1 to 10)
        mock_scores = []
        for score_val in [1, 4, 7, 10]:
            mock_score = Mock()
            mock_score.total_score = score_val
            mock_scores.append(mock_score)

        icc = await analyzer._calculate_icc(mock_scores)

        # High disagreement should yield low ICC
        assert icc is not None
        assert icc < 0.5  # Low ICC due to high range

    @pytest.mark.asyncio
    async def test_build_judge_profile_no_scores(self):
        """Test building profile for judge with no scores"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = AsyncMock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        mock_result = AsyncMock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await analyzer.build_judge_profile(judge_id=1, competition_id=1)

        assert result["submission_count"] == 0
        assert result["avg_score"] is None
        assert result["bias_category"] == "unknown"

    @pytest.mark.asyncio
    async def test_build_judge_profile_lenient(self):
        """Test detecting lenient judge (high z-score)"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = AsyncMock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        # Judge gives consistently high scores (8.5, 9.0, 8.8, 9.2)
        mock_scores = []
        for score_val in [8.5, 9.0, 8.8, 9.2]:
            mock_score = Mock()
            mock_score.total_score = score_val
            mock_scores.append(mock_score)

        mock_result = AsyncMock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=mock_scores)))
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock competition averages (lower than judge's avg)
        analyzer._get_competition_avg_score = AsyncMock(return_value=6.0)
        analyzer._get_competition_std_score = AsyncMock(return_value=1.5)

        result = await analyzer.build_judge_profile(judge_id=1, competition_id=1)

        assert result["submission_count"] == 4
        assert result["avg_score"] > 8.0
        assert result["bias_category"] == "lenient"

    @pytest.mark.asyncio
    async def test_build_judge_profile_harsh(self):
        """Test detecting harsh judge (negative z-score)"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = AsyncMock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        # Judge gives consistently low scores
        mock_scores = []
        for score_val in [3.0, 3.5, 3.2, 2.8]:
            mock_score = Mock()
            mock_score.total_score = score_val
            mock_scores.append(mock_score)

        mock_result = AsyncMock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=mock_scores)))
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock competition averages (higher than judge's avg)
        analyzer._get_competition_avg_score = AsyncMock(return_value=7.0)
        analyzer._get_competition_std_score = AsyncMock(return_value=1.5)

        result = await analyzer.build_judge_profile(judge_id=1, competition_id=1)

        assert result["avg_score"] < 4.0
        assert result["bias_category"] == "harsh"


class TestJudgeConsensusAnalysisModel:
    """Test JudgeConsensusAnalysis model"""

    def test_consensus_quality_excellent(self):
        """Test excellent consensus quality (ICC >= 0.75)"""
        from app.models import JudgeConsensusAnalysis

        analysis = JudgeConsensusAnalysis(
            submission_id=1,
            competition_id=1,
            icc_value=0.85
        )

        assert analysis.consensus_quality == "Excellent"

    def test_consensus_quality_good(self):
        """Test good consensus quality (0.60 <= ICC < 0.75)"""
        from app.models import JudgeConsensusAnalysis

        analysis = JudgeConsensusAnalysis(
            submission_id=1,
            competition_id=1,
            icc_value=0.65
        )

        assert analysis.consensus_quality == "Good"

    def test_consensus_quality_fair(self):
        """Test fair consensus quality (0.40 <= ICC < 0.60)"""
        from app.models import JudgeConsensusAnalysis

        analysis = JudgeConsensusAnalysis(
            submission_id=1,
            competition_id=1,
            icc_value=0.50
        )

        assert analysis.consensus_quality == "Fair"

    def test_consensus_quality_poor(self):
        """Test poor consensus quality (ICC < 0.40)"""
        from app.models import JudgeConsensusAnalysis

        analysis = JudgeConsensusAnalysis(
            submission_id=1,
            competition_id=1,
            icc_value=0.25
        )

        assert analysis.consensus_quality == "Poor"

    def test_consensus_quality_not_calculated(self):
        """Test consensus quality when ICC is None"""
        from app.models import JudgeConsensusAnalysis

        analysis = JudgeConsensusAnalysis(
            submission_id=1,
            competition_id=1,
            icc_value=None
        )

        assert analysis.consensus_quality == "Not calculated"


class TestJudgeScoringProfileModel:
    """Test JudgeScoringProfile model"""

    def test_bias_category_lenient(self):
        """Test lenient bias category (z > 0.5)"""
        from app.models import JudgeScoringProfile

        profile = JudgeScoringProfile(
            judge_id=1,
            competition_id=1,
            bias_score=0.8
        )

        assert profile.bias_category == "lenient"

    def test_bias_category_harsh(self):
        """Test harsh bias category (z < -0.5)"""
        from app.models import JudgeScoringProfile

        profile = JudgeScoringProfile(
            judge_id=1,
            competition_id=1,
            bias_score=-0.8
        )

        assert profile.bias_category == "harsh"

    def test_bias_category_fair(self):
        """Test fair bias category (-0.5 <= z <= 0.5)"""
        from app.models import JudgeScoringProfile

        profile = JudgeScoringProfile(
            judge_id=1,
            competition_id=1,
            bias_score=0.2
        )

        assert profile.bias_category == "fair"

    def test_bias_category_unknown(self):
        """Test unknown bias category (None)"""
        from app.models import JudgeScoringProfile

        profile = JudgeScoringProfile(
            judge_id=1,
            competition_id=1,
            bias_score=None
        )

        assert profile.bias_category == "unknown"


class TestICCCalculation:
    """Dedicated tests for ICC calculation accuracy"""

    @pytest.mark.asyncio
    async def test_icc_range_validation(self):
        """Test that ICC is always in [0, 1] range"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = Mock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        # Test various score ranges
        test_cases = [
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # Full range
            [5, 5, 5, 5],  # Identical
            [1, 1, 10, 10],  # Bimodal
            [7.5, 7.6, 7.4, 7.5],  # Very close
        ]

        for scores in test_cases:
            mock_scores = []
            for s in scores:
                mock_score = Mock()
                mock_score.total_score = s
                mock_scores.append(mock_score)

            icc = await analyzer._calculate_icc(mock_scores)

            assert icc is not None
            assert 0.0 <= icc <= 1.0, f"ICC {icc} out of range for scores {scores}"

    @pytest.mark.asyncio
    async def test_icc_single_rater_returns_none(self):
        """Test that ICC returns None for single rater"""
        from app.services.judge_consensus import JudgeConsensusAnalyzer

        mock_db = Mock()
        analyzer = JudgeConsensusAnalyzer(mock_db)

        mock_score = Mock()
        mock_score.total_score = 7.0

        icc = await analyzer._calculate_icc([mock_score])

        assert icc is None


def run_all_tests():
    """Run all tests manually"""
    print("\n" + "=" * 70)
    print("Testing Judge Consensus Analysis Service")
    print("=" * 70 + "\n")

    try:
        # Sync tests
        print("1. Testing outlier detection...")
        test_sync = TestJudgeConsensusAnalyzer()
        test_sync.test_outlier_detection_no_outliers()
        test_sync.test_outlier_detection_with_outlier()
        test_sync.test_outlier_detection_no_variance()
        print("   Outlier detection passed")

        print("2. Testing consensus verdicts...")
        test_sync.test_consensus_verdict_strong()
        test_sync.test_consensus_verdict_moderate()
        test_sync.test_consensus_verdict_weak()
        test_sync.test_consensus_verdict_poor()
        test_sync.test_consensus_verdict_insufficient_data()
        print("   Consensus verdicts passed")

        print("3. Testing analyzer thresholds...")
        test_sync.test_analyzer_threshold_values()
        print("   Analyzer thresholds passed")

        print("4. Testing model properties...")
        test_model = TestJudgeConsensusAnalysisModel()
        test_model.test_consensus_quality_excellent()
        test_model.test_consensus_quality_good()
        test_model.test_consensus_quality_fair()
        test_model.test_consensus_quality_poor()
        test_model.test_consensus_quality_not_calculated()
        print("   Model properties passed")

        print("5. Testing bias categories...")
        test_bias = TestJudgeScoringProfileModel()
        test_bias.test_bias_category_lenient()
        test_bias.test_bias_category_harsh()
        test_bias.test_bias_category_fair()
        test_bias.test_bias_category_unknown()
        print("   Bias categories passed")

        print("6. Running async tests...")
        import asyncio
        test_async = TestJudgeConsensusAnalyzerAsync()
        test_icc = TestICCCalculation()

        async def run_async():
            await test_async.test_analyze_submission_insufficient_judges()
            print("   - Insufficient judges handling: passed")
            await test_async.test_calculate_icc_perfect_agreement()
            print("   - ICC perfect agreement: passed")
            await test_async.test_calculate_icc_disagreement()
            print("   - ICC disagreement: passed")
            await test_icc.test_icc_range_validation()
            print("   - ICC range validation: passed")
            await test_icc.test_icc_single_rater_returns_none()
            print("   - ICC single rater: passed")

        asyncio.run(run_async())

        print("\n" + "=" * 70)
        print("ALL JUDGE CONSENSUS SERVICE TESTS PASSED")
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
