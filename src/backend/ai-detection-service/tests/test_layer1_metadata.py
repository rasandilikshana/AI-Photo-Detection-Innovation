"""
Tests for Layer 1: Metadata Analysis
"""

import pytest
from app.services.layer1_metadata import MetadataAnalyzer


@pytest.fixture
def analyzer():
    return MetadataAnalyzer()


def test_ai_signature_detection(analyzer):
    """Test detection of AI generation signatures"""
    metadata = {
        "Software": "Midjourney Bot v5",
        "Comment": "Generated with DALL-E"
    }

    ai_detected, flags = analyzer._detect_ai_signatures(metadata)

    assert ai_detected is True
    assert len(flags) > 0
    assert any("midjourney" in flag.lower() for flag in flags)


def test_camera_signature_validation(analyzer):
    """Test validation of camera metadata"""
    # Complete camera metadata
    complete_metadata = {
        "Make": "Canon",
        "Model": "EOS R5",
        "LensModel": "RF 24-70mm F2.8",
        "ExposureTime": "1/1000",
        "FNumber": "2.8",
        "ISO": "100",
        "FocalLength": "50mm",
        "DateTimeOriginal": "2024:01:15 10:30:00"
    }

    score, flags = analyzer._validate_camera_signatures(complete_metadata)

    assert score == 1.0
    assert len(flags) == 0


def test_missing_camera_metadata(analyzer):
    """Test handling of missing camera metadata"""
    empty_metadata = {}

    score, flags = analyzer._validate_camera_signatures(empty_metadata)

    assert score == 0.0
    assert len(flags) > 0
    assert any("no camera metadata" in flag.lower() for flag in flags)


def test_metadata_consistency_check(analyzer):
    """Test metadata consistency validation"""
    # Inconsistent: has Make but no Model
    inconsistent_metadata = {
        "Make": "Canon",
        "ExposureTime": "1/1000"
    }

    score, flags = analyzer._check_metadata_consistency(inconsistent_metadata)

    assert score < 1.0
    assert len(flags) > 0


def test_raw_jpg_correlation(analyzer):
    """Test RAW-JPG metadata correlation"""
    jpg_metadata = {
        "Make": "Canon",
        "Model": "EOS R5",
        "ISO": "100"
    }

    raw_metadata = {
        "Make": "Canon",
        "Model": "EOS R5",
        "ISO": "100"
    }

    score, flags = analyzer._check_raw_jpg_correlation(jpg_metadata, raw_metadata)

    assert score == 1.0
    assert len(flags) == 0


def test_raw_jpg_mismatch(analyzer):
    """Test detection of RAW-JPG metadata mismatch"""
    jpg_metadata = {
        "Make": "Canon",
        "Model": "EOS R5"
    }

    raw_metadata = {
        "Make": "Nikon",
        "Model": "Z9"
    }

    score, flags = analyzer._check_raw_jpg_correlation(jpg_metadata, raw_metadata)

    assert score < 0.5
    assert len(flags) > 0
    assert any("mismatch" in flag.lower() for flag in flags)


@pytest.mark.asyncio
async def test_full_metadata_analysis(analyzer, sample_jpg_image):
    """Test complete metadata analysis workflow"""
    result = await analyzer.analyze(sample_jpg_image, None)

    assert "verdict" in result
    assert "confidence" in result
    assert "flags" in result
    assert result["verdict"] in ["AUTHENTIC", "SUSPICIOUS", "REJECT", "PASS", "ERROR"]
    assert 0.0 <= result["confidence"] <= 1.0
