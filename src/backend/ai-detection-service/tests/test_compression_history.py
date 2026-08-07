"""Double-JPEG compression history — a documented NEGATIVE result.

This module is not wired into the Authenticity Score. These tests exist to record why,
and to keep the calibration reproducible so the finding can be re-checked if anyone
tries to enable it.

The idea was sound and citable: a photograph reaching a competition has been compressed
twice (camera or converter, then export), while a generated image is written once.
Double quantisation leaves periodic peaks and empty bins in DCT coefficient histograms
(Lukas & Fridrich 2003; Popescu & Farid 2004; Bianchi & Piva, IEEE TIFS 2012).

MEASURED on our real files, the metric does not separate:

    SYNTHETIC generated JPEG              0.048
    GENUINE   camera JPEG (Twisted)       0.054
    GENUINE   camera JPEG (Emerald)       0.064
    GENUINE   Photoshop export            0.013   <-- LOWER than the fake
    GENUINE   Emerald edit                0.119
    GENUINE   meta-transplanted edit      0.013   <-- LOWER than the fake

And on controlled fixtures it is inverted: single-compressed 0.454, double-compressed
0.172.

CAUSE: the signature lives in a JPEG's STORED quantised coefficients. Computing the DCT
from decoded pixels and dividing by the quantisation table loses the periodic structure.
Coefficient-level access (jpeglib / jpegio) is required.

This is the same trap that caught the predecessor of the geometric linkage check:
fixtures that appear to validate a statistic which fails on real files. Here the
calibration caught it before it shipped, which is the only reason it is not now
silently mis-scoring submissions.

What these tests DO assert: the module runs without crashing, returns finite
JSON-serialisable values, and treats every degenerate input as inconclusive rather than
accusatory. That is the contract needed for it to sit in the tree safely.
"""

import json
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

from app.services.authenticity_score import AuthenticityScorer
from app.services.compression_history import CompressionHistoryAnalyzer


@pytest.fixture
def analyzer():
    return CompressionHistoryAnalyzer()


def _scene(seed=0, size=(512, 512)):
    rng = np.random.default_rng(seed)
    return cv2.GaussianBlur(rng.integers(0, 255, (*size, 3), dtype=np.uint8), (0, 0), 2.0)


def _save(image, quality, path):
    Image.fromarray(image).save(str(path), "JPEG", quality=quality)
    return str(path)


# ---------------------------------------------------------------------------
# The exclusion is deliberate and must stay deliberate
# ---------------------------------------------------------------------------

def test_compression_is_not_a_scored_signal():
    """If someone adds it back, this fails and sends them to the calibration above."""
    assert "compression" not in AuthenticityScorer.WEIGHTS, (
        "compression history does not discriminate on our data - see the module "
        "docstring for the measurements before re-enabling it"
    )


def test_the_reassigned_weights_still_total_one_hundred():
    assert sum(AuthenticityScorer.WEIGHTS.values()) == 100


def test_its_points_went_to_the_measured_strongest_signals():
    """The 10 points went to the two signals with demonstrated separation, not to the
    empirically-tuned ones."""
    weights = AuthenticityScorer.WEIGHTS
    assert weights["raw_provenance"] == 35
    assert weights["geometric_linkage"] == 30
    assert weights["frequency"] == 5, "a tuned threshold must not gain weight"


# ---------------------------------------------------------------------------
# Reproducing the negative result
# ---------------------------------------------------------------------------

REAL_FILES = Path("/home/rasan/Downloads/test")


def test_the_metric_does_not_separate_real_files(analyzer):
    """The calibration that killed this signal. Skips when fixtures are absent."""
    synthetic = REAL_FILES / "1_5_AVAR_high_realism_synthetic_Canon_R5_test.jpg.jpeg"
    genuine = [
        REAL_FILES / "Twisted Crowns-2511305-Mono.JPG",
        REAL_FILES / "Emerald Edge-2511305-Colour.JPG",
        REAL_FILES / "original-photoshop-edit-Twisted Crowns-2511305-Monocrom.jpg",
        REAL_FILES / "Emerald Dialogue.jpg",
    ]
    if not synthetic.exists() or not all(p.exists() for p in genuine):
        pytest.skip("real fixtures not present on this machine")

    fake = analyzer.analyze(str(synthetic))["dq_strength"]
    real = [analyzer.analyze(str(p))["dq_strength"] for p in genuine]

    # The finding: the fake is NOT below every genuine file.
    assert not all(fake < value for value in real), (
        "the metric now separates - re-run the full calibration and consider "
        f"re-enabling the signal (fake={fake:.4f}, genuine={sorted(real)})"
    )


def test_the_metric_is_inverted_on_controlled_fixtures(analyzer, tmp_path):
    """Single-compressed scores HIGHER than double-compressed, which is backwards."""
    single = _save(_scene(3), 95, tmp_path / "single.jpg")
    first = _save(_scene(3), 70, tmp_path / "first.jpg")
    double = _save(np.array(Image.open(first).convert("RGB")), 92, tmp_path / "double.jpg")

    single_strength = analyzer.analyze(single)["dq_strength"]
    double_strength = analyzer.analyze(double)["dq_strength"]

    assert single_strength > double_strength, (
        "the inversion is gone - the metric may now work; re-run the real-file "
        f"calibration (single={single_strength:.4f}, double={double_strength:.4f})"
    )


# ---------------------------------------------------------------------------
# Safety contract: it must sit in the tree harmlessly
# ---------------------------------------------------------------------------

def test_a_readable_jpeg_returns_finite_serialisable_values(analyzer, tmp_path):
    result = analyzer.analyze(_save(_scene(7), 90, tmp_path / "ok.jpg"))

    json.dumps(result)
    assert np.isfinite(result["score"])
    assert np.isfinite(result["dq_strength"])
    assert result["evidence"]


@pytest.mark.parametrize("make_input,label", [
    (lambda p: (p / "broken.jpg").write_bytes(b"not a jpeg") or str(p / "broken.jpg"), "corrupt"),
    (lambda p: str(p / "absent.jpg"), "missing"),
])
def test_unusable_input_is_inconclusive_not_accusatory(analyzer, tmp_path, make_input, label):
    result = analyzer.analyze(make_input(tmp_path))

    assert result["score"] == 0.5, label
    assert result["double_compressed"] is None, label


def test_non_jpeg_is_inconclusive(analyzer, tmp_path):
    path = tmp_path / "image.png"
    Image.fromarray(_scene(6)).save(str(path), "PNG")

    result = analyzer.analyze(str(path))

    assert result["score"] == 0.5
    assert result["double_compressed"] is None


def test_a_flat_image_is_inconclusive(analyzer, tmp_path):
    """No texture means no coefficient spread to build a histogram from."""
    path = _save(np.full((256, 256, 3), 128, dtype=np.uint8), 90, tmp_path / "flat.jpg")

    result = analyzer.analyze(path)

    assert result["score"] == 0.5
    assert result["double_compressed"] is None
