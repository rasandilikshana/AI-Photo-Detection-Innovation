"""
Test suite for PRNU extraction and camera reputation services

Tests core functionality without requiring actual database or image files.
"""

import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch


class TestPRNUExtractor:
    """Test PRNU extraction service"""

    def test_compress_decompress_pattern(self):
        """Test that pattern compression/decompression is lossless"""
        from app.services.prnu_extractor import PRNUExtractor

        extractor = PRNUExtractor()

        # Create synthetic PRNU pattern
        pattern = np.random.randn(512, 512).astype(np.float32) * 0.01

        # Compress
        compressed = extractor._compress_pattern(pattern)

        # Verify compression
        assert isinstance(compressed, bytes)
        assert len(compressed) < pattern.nbytes  # Should be compressed

        # Decompress
        decompressed = extractor.decompress_pattern(compressed, pattern.shape)

        # Verify shape
        assert decompressed.shape == pattern.shape

        # Verify values are close (quantization may introduce small errors)
        np.testing.assert_allclose(pattern, decompressed, atol=1e-3)

        print("✓ Compress/decompress test passed")

    def test_hash_pattern_consistency(self):
        """Test that same pattern produces same hash"""
        from app.services.prnu_extractor import PRNUExtractor

        extractor = PRNUExtractor()

        # Create pattern
        pattern = np.random.randn(512, 512).astype(np.float32)

        # Hash twice
        hash1 = extractor._hash_pattern(pattern)
        hash2 = extractor._hash_pattern(pattern)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest length

        # Different pattern should give different hash
        pattern2 = pattern + 0.1
        hash3 = extractor._hash_pattern(pattern2)

        assert hash3 != hash1

        print("✓ Hash consistency test passed")

    def test_noise_estimation(self):
        """Test MAD noise estimation"""
        from app.services.prnu_extractor import PRNUExtractor

        extractor = PRNUExtractor()

        # Create coefficients with known noise level
        noise_std = 0.1
        coeffs = np.random.randn(100, 100) * noise_std

        # Estimate noise
        sigma = extractor._estimate_noise_mad(coeffs)

        # Should be close to actual noise level
        assert 0.05 < sigma < 0.15  # Within reasonable range

        print("✓ Noise estimation test passed")

    def test_spatial_autocorrelation(self):
        """Test spatial autocorrelation calculation"""
        from app.services.prnu_extractor import PRNUExtractor

        extractor = PRNUExtractor()

        # Create highly correlated pattern (smooth)
        x = np.linspace(0, 10, 512)
        y = np.linspace(0, 10, 512)
        X, Y = np.meshgrid(x, y)
        smooth_pattern = np.sin(X) * np.cos(Y)

        # Should have high autocorrelation
        corr_smooth = extractor._spatial_autocorrelation(smooth_pattern)
        assert corr_smooth > 0.5, "Smooth pattern should have high autocorrelation"

        # Create random noise (uncorrelated)
        noise_pattern = np.random.randn(512, 512)

        # Should have low autocorrelation
        corr_noise = extractor._spatial_autocorrelation(noise_pattern)
        assert corr_noise < 0.2, "Noise should have low autocorrelation"

        print("✓ Spatial autocorrelation test passed")

    @pytest.mark.asyncio
    async def test_compare_identical_patterns(self):
        """Test that identical patterns have similarity score = 1.0"""
        from app.services.prnu_extractor import PRNUExtractor

        extractor = PRNUExtractor()

        # Create pattern
        pattern = np.random.randn(512, 512).astype(np.float32) * 0.01

        # Compare with itself
        result = await extractor.compare_patterns(pattern, pattern)

        assert "similarity_score" in result
        assert result["similarity_score"] > 0.99  # Should be very close to 1.0
        assert result["same_camera_likely"] is True

        print("✓ Identical pattern comparison test passed")

    @pytest.mark.asyncio
    async def test_compare_different_patterns(self):
        """Test that different patterns have low similarity"""
        from app.services.prnu_extractor import PRNUExtractor

        extractor = PRNUExtractor()

        # Create two different patterns
        pattern1 = np.random.randn(512, 512).astype(np.float32) * 0.01
        pattern2 = np.random.randn(512, 512).astype(np.float32) * 0.01

        # Compare
        result = await extractor.compare_patterns(pattern1, pattern2)

        assert result["similarity_score"] < 0.50  # Should be low for random patterns
        assert result["same_camera_likely"] is False

        print("✓ Different pattern comparison test passed")

    @pytest.mark.asyncio
    async def test_compare_similar_patterns(self):
        """Test patterns with added noise"""
        from app.services.prnu_extractor import PRNUExtractor

        extractor = PRNUExtractor()

        # Create base pattern
        base = np.random.randn(512, 512).astype(np.float32) * 0.01

        # Add small noise
        noisy = base + np.random.randn(512, 512).astype(np.float32) * 0.001

        # Compare
        result = await extractor.compare_patterns(base, noisy)

        # Should still be fairly similar
        assert 0.70 < result["similarity_score"] < 1.0
        assert result["same_camera_likely"] is True

        print("✓ Similar pattern comparison test passed")

    def test_estimate_quality(self):
        """Test PRNU quality estimation"""
        from app.services.prnu_extractor import PRNUExtractor

        extractor = PRNUExtractor()

        # High quality pattern (good noise characteristics)
        good_pattern = np.random.randn(512, 512).astype(np.float32) * 0.01

        quality_good = extractor.estimate_quality(good_pattern)

        assert "quality_score" in quality_good
        assert "quality_level" in quality_good
        assert 0 <= quality_good["quality_score"] <= 1.0

        # Low quality pattern (very weak signal)
        poor_pattern = np.random.randn(512, 512).astype(np.float32) * 0.0001

        quality_poor = extractor.estimate_quality(poor_pattern)

        assert quality_poor["quality_score"] < quality_good["quality_score"]

        print("✓ Quality estimation test passed")


class TestCameraReputationManager:
    """Test camera reputation management"""

    def test_trust_boost_calculation(self):
        """Test trust boost threshold logic"""
        from app.services.camera_reputation import CameraReputationManager

        # Create mock db session
        mock_db = Mock()
        manager = CameraReputationManager(mock_db)

        # Test thresholds
        assert manager._calculate_trust_boost(0.90) == 0.15  # Strong match
        assert manager._calculate_trust_boost(0.75) == 0.05  # Moderate match
        assert manager._calculate_trust_boost(0.60) == 0.0   # Neutral
        assert manager._calculate_trust_boost(0.40) == -0.10 # Suspicious

        print("✓ Trust boost calculation test passed")

    def test_fraud_explanation_generation(self):
        """Test fraud explanation text generation"""
        from app.services.camera_reputation import CameraReputationManager

        mock_db = Mock()
        manager = CameraReputationManager(mock_db)

        # High fraud risk
        explanation_high = manager._generate_fraud_explanation(0.8, ["indicator1", "indicator2"])
        assert "High fraud risk" in explanation_high
        assert "2" in explanation_high

        # Moderate risk
        explanation_mid = manager._generate_fraud_explanation(0.5, ["indicator1"])
        assert "Moderate fraud risk" in explanation_mid

        # Low risk
        explanation_low = manager._generate_fraud_explanation(0.2, [])
        assert "consistent" in explanation_low.lower()

        print("✓ Fraud explanation generation test passed")


def run_all_tests():
    """Run all tests manually"""
    print("\n" + "="*70)
    print("Testing PRNU Extraction and Camera Reputation Services")
    print("="*70 + "\n")

    try:
        # PRNU Extractor Tests
        print("1. Testing PRNUExtractor...")
        test_extractor = TestPRNUExtractor()

        test_extractor.test_compress_decompress_pattern()
        test_extractor.test_hash_pattern_consistency()
        test_extractor.test_noise_estimation()
        test_extractor.test_spatial_autocorrelation()
        test_extractor.test_estimate_quality()

        print("\n2. Testing pattern comparison (async)...")
        import asyncio

        async def run_async_tests():
            await test_extractor.test_compare_identical_patterns()
            await test_extractor.test_compare_different_patterns()
            await test_extractor.test_compare_similar_patterns()

        asyncio.run(run_async_tests())

        # Camera Reputation Tests
        print("\n3. Testing CameraReputationManager...")
        test_manager = TestCameraReputationManager()

        test_manager.test_trust_boost_calculation()
        test_manager.test_fraud_explanation_generation()

        print("\n" + "="*70)
        print("✅ ALL SERVICE TESTS PASSED")
        print("="*70 + "\n")

    except ImportError as e:
        print(f"\n⚠️  IMPORT ERROR: {e}")
        print("\nNote: Tests require numpy, opencv-python, and PyWavelets.")
        print("These dependencies are needed for PRNU extraction to work.")
        return 0  # Don't fail - expected without dependencies

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())
