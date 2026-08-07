"""
Tests for metadata transplant forensics and catastrophic pHash handling.

Regression suite for the Gemini-image incident: an AI-generated JPEG carrying
metadata copied verbatim (via exiftool) from a genuine CR2 was approved as
AUTHENTIC because every layer scored the transplanted metadata at face value.
"""

import cv2
import numpy as np
import pytest

from app.services.layer1_metadata import MetadataAnalyzer
from app.services.raw_jpg_linkage import RAWJPGLinkageAnalyzer


@pytest.fixture
def analyzer():
    return MetadataAnalyzer()


@pytest.fixture
def linkage():
    return RAWJPGLinkageAnalyzer()


# ---------------------------------------------------------------------------
# Layer 1: forensic integrity checks
# ---------------------------------------------------------------------------

def test_forensics_detects_transplanted_metadata(analyzer):
    """The exact signature of the incident: dims mismatch + exiftool XMP toolkit
    + RAW-sensor tags inside a small JPEG."""
    grouped = {
        "ExifIFD:ExifImageWidth": 5184,
        "ExifIFD:ExifImageHeight": 3456,
        "XMP-tiff:ImageWidth": 5184,
        "XMP-tiff:ImageHeight": 3456,
        "XMP-x:XMPToolkit": "Image::ExifTool 13.10",
        "MakerNotes:WB_RGGBLevelsAsShot": "2087 1024 1024 1656",
        "MakerNotes:PerChannelBlackLevel": "2048 2048 2048 2048",
        "MakerNotes:NormalWhiteLevel": 12279,
        "MakerNotes:SensorLeftBorder": 168,
        "MakerNotes:DustRemovalData": "(Binary data 1024 bytes)",
    }
    strong, flags = analyzer.forensic_integrity_checks((1264, 842), grouped)

    assert strong >= 3
    assert any("does not belong to this file" in f for f in flags)
    assert any("exiftool CLI" in f for f in flags)
    assert any("RAW-sensor tags" in f for f in flags)


def test_forensics_passes_genuine_camera_jpeg(analyzer):
    """A straight-out-of-camera JPEG: declared dims match actual, no CLI toolkit."""
    grouped = {
        "ExifIFD:ExifImageWidth": 5184,
        "ExifIFD:ExifImageHeight": 3456,
        "IFD0:Make": "Canon",
        "IFD0:Model": "Canon EOS 600D",
    }
    strong, flags = analyzer.forensic_integrity_checks((5184, 3456), grouped)

    assert strong == 0
    assert flags == []


def test_forensics_accepts_rotated_orientation(analyzer):
    """Portrait-orientation files legitimately swap width/height."""
    grouped = {
        "ExifIFD:ExifImageWidth": 3456,
        "ExifIFD:ExifImageHeight": 5184,
    }
    strong, flags = analyzer.forensic_integrity_checks((5184, 3456), grouped)

    assert strong == 0


def test_forensics_flags_stale_dimensions_only_once(analyzer):
    """A sloppy resize (stale EXIF dims, no other indicators) is one indicator —
    enough to quarantine for review, not to hard-reject."""
    grouped = {
        "ExifIFD:ExifImageWidth": 5184,
        "ExifIFD:ExifImageHeight": 3456,
        "XMP-x:XMPToolkit": "Adobe XMP Core 9.1-c001",
    }
    strong, flags = analyzer.forensic_integrity_checks((1264, 842), grouped)

    assert strong == 1
    assert any("does not belong to this file" in f for f in flags)


def test_forensics_ignores_few_raw_tags(analyzer):
    """Fewer than 3 sensor tags alone should not count as a strong indicator
    (some cameras write partial MakerNotes into JPEGs)."""
    grouped = {
        "MakerNotes:NormalWhiteLevel": 12279,
        "MakerNotes:SensorLeftBorder": 168,
    }
    strong, flags = analyzer.forensic_integrity_checks((5184, 3456), grouped)

    assert strong == 0


def test_genuine_camera_jpeg_with_sensor_tags_is_clean(analyzer):
    """Regression: real Canon JPEGs carry the full MakerNotes sensor block. With
    dimensions matching the pixels, that must NOT be flagged (verified against
    IMG_1083.JPG, 5184x3456, Hive AI score 0.0005)."""
    grouped = {
        "ExifIFD:ExifImageWidth": 5184,
        "ExifIFD:ExifImageHeight": 3456,
        "MakerNotes:WB_RGGBLevelsAsShot": "2087 1024 1024 1656",
        "MakerNotes:PerChannelBlackLevel": "2048 2048 2048 2048",
        "MakerNotes:NormalWhiteLevel": 12279,
        "MakerNotes:SpecularWhiteLevel": 13000,
        "MakerNotes:SensorLeftBorder": 168,
        "MakerNotes:SensorTopBorder": 56,
        "MakerNotes:DustRemovalData": "(Binary data 1024 bytes)",
        "MakerNotes:RawMeasuredRGGB": "1 2 3 4",
        "MakerNotes:VignettingCorrVersion": 0,
    }
    strong, flags = analyzer.forensic_integrity_checks((5184, 3456), grouped)

    assert strong == 0, f"genuine camera JPEG must not be flagged, got: {flags}"


# ---------------------------------------------------------------------------
# Layer 1: AI signature list covers Google/Gemini tooling
# ---------------------------------------------------------------------------

def test_ai_signatures_detect_gemini_and_google(analyzer):
    for value in ["Made with Google AI", "Gemini 2.0 Flash", "Imagen 3", "SynthID watermarked"]:
        detected, flags = analyzer._detect_ai_signatures({"Credit": value})
        assert detected is True, f"should detect: {value}"


# ---------------------------------------------------------------------------
# RAW-JPG linkage: catastrophic pHash cannot be outvoted
# ---------------------------------------------------------------------------

def test_catastrophic_phash_downgrades_pass(linkage):
    """The incident's numbers: pHash 118 with passing SSIM/histogram must NOT pass."""
    verdict, confidence = linkage._determine_verdict(
        phash_match=False, phash_distance=118, ssim_score=0.64, hist_corr=0.69
    )
    assert verdict == "SUSPICIOUS"
    assert confidence <= 0.4


def test_heavy_edit_still_passes(linkage):
    """A legitimate heavy edit: pHash beyond match threshold but below catastrophic,
    strong SSIM/histogram agreement -> still PASS."""
    verdict, _ = linkage._determine_verdict(
        phash_match=False, phash_distance=30, ssim_score=0.72, hist_corr=0.80
    )
    assert verdict == "PASS"


def test_full_agreement_passes(linkage):
    verdict, _ = linkage._determine_verdict(
        phash_match=True, phash_distance=8, ssim_score=0.9, hist_corr=0.95
    )
    assert verdict == "PASS"


def test_no_agreement_rejects(linkage):
    verdict, confidence = linkage._determine_verdict(
        phash_match=False, phash_distance=120, ssim_score=0.2, hist_corr=0.1
    )
    assert verdict == "REJECT"
    assert confidence == 0.0


# ---------------------------------------------------------------------------
# Crop-aware, tone-invariant matching (genuine heavy edits must not be rejected)
# ---------------------------------------------------------------------------

def test_edge_map_handles_flat_image(linkage):
    """A 90%-black monochrome conversion yields flat regions; normalizing a
    zero-span gradient field must not produce NaN (it broke JSON serialization
    and silently scored as a perfect match)."""
    flat = np.zeros((200, 300), dtype=np.uint8)
    result = linkage._edge_map(flat, (150, 100))

    assert np.isfinite(result).all()
    assert result.shape == (100, 150)


def test_gradient_match_finds_cropped_and_tone_crushed_derivative(linkage):
    """The submission-32 scenario: the JPG is a crop of the RAW, converted to
    black and white with the tones crushed. Structure survives; luminance does not."""
    rng = np.random.default_rng(42)
    scene = rng.integers(0, 255, size=(600, 900), dtype=np.uint8)
    scene = cv2.GaussianBlur(scene, (9, 9), 0)  # give it real structure
    raw_bgr = cv2.cvtColor(scene, cv2.COLOR_GRAY2BGR)

    # crop 60% of the frame, then crush the tones hard (gamma 3.0)
    crop = scene[100:460, 150:690]
    crushed = np.clip(((crop / 255.0) ** 3.0) * 255, 0, 255).astype(np.uint8)
    jpg_bgr = cv2.cvtColor(crushed, cv2.COLOR_GRAY2BGR)

    score, frac = linkage._gradient_crop_match(raw_bgr, jpg_bgr)

    assert score >= linkage.gradient_linked_threshold, f"genuine crop+crush scored only {score:.3f}"
    assert 0.0 < frac <= 1.0


def test_gradient_match_rejects_unrelated_scene(linkage):
    """A different scene must not match, however similar its tonality."""
    rng = np.random.default_rng(1)
    raw = cv2.GaussianBlur(rng.integers(0, 255, size=(600, 900), dtype=np.uint8), (9, 9), 0)
    other = cv2.GaussianBlur(rng.integers(0, 255, size=(400, 600), dtype=np.uint8), (9, 9), 0)

    score, _ = linkage._gradient_crop_match(
        cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR), cv2.cvtColor(other, cv2.COLOR_GRAY2BGR)
    )

    assert score < linkage.gradient_weak_threshold, f"unrelated scene scored {score:.3f}"


def test_gradient_thresholds_are_ordered(linkage):
    """Guard the calibration: linked > weak, and crops below 40% are not searched."""
    assert linkage.gradient_linked_threshold > linkage.gradient_weak_threshold
    assert linkage.min_crop_fraction >= 0.40
