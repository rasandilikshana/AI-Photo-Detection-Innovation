"""PRNU as sensor-reference correlation, not residual energy.

The previous implementation measured var(image - denoised) and called it PRNU. That
is high-frequency residual energy and it could not discriminate at all. Measured on
real files:

    genuine Canon camera JPEG    2.26e-05  scored 0.5 "weak"
    synthetic AI image           1.39e-05  scored 0.5 "weak"
    Photoshop-edited real photo  2.53e-04  scored 1.0 "valid"

The real photo and the AI image were indistinguishable, and the edited file beat the
genuine camera file by 11x, because editing adds high-frequency content.

PRNU is a per-sensor hardware fingerprint (Lukas, Fridrich & Goljan 2006). Detecting
it means CORRELATING a noise residual against a reference pattern from that specific
camera body. The decision statistic is PCE (Peak-to-Correlation Energy); a threshold
of 60 corresponds to a false-accept rate near 1e-5 (Goljan, Fridrich & Filler,
"Large scale test of sensor fingerprint camera identification", SPIE 2009).

Without a reference there is nothing to correlate against. That is an absence of
information, not evidence, so prnu_score must be None so the Authenticity Score
EXCLUDES it and renormalises. Returning a middling 0.5 instead would drag every
submission toward the centre — the genuine unedited pair scored 94 instead of 100 for
exactly that reason.
"""

import numpy as np
import pytest

from app.services.layer2_fingerprint import DigitalFingerprintAnalyzer


@pytest.fixture
def analyzer():
    return DigitalFingerprintAnalyzer()


# ---------------------------------------------------------------------------
# The published threshold
# ---------------------------------------------------------------------------

def test_pce_threshold_matches_the_published_value(analyzer):
    """60 is not tunable to taste - it is the value the literature ties to a
    false-accept rate near 1e-5."""
    assert analyzer.pce_threshold == 60.0


def test_there_is_no_intermediate_band(analyzer):
    """PCE below the threshold is statistically consistent with a different sensor, so
    a 'weakly consistent' grade would invent a gradation the statistic cannot support.
    Measured: unrelated white noise scores ~24, which an intermediate band would have
    reported as partially matching."""
    assert not hasattr(analyzer, "pce_floor")


# ---------------------------------------------------------------------------
# PCE behaviour
# ---------------------------------------------------------------------------

def test_a_pattern_correlates_with_itself(analyzer):
    rng = np.random.default_rng(0)
    pattern = rng.standard_normal((256, 256)).astype(np.float32)

    pce = analyzer._peak_to_correlation_energy(pattern, pattern.copy())

    assert pce > analyzer.pce_threshold, f"a pattern must match itself, got PCE={pce:.1f}"


def test_unrelated_patterns_do_not_correlate(analyzer):
    """Measured at PCE ~24 versus 66,592 for an identical pattern - four orders of
    magnitude of separation, with the threshold sitting between them."""
    rng = np.random.default_rng(1)
    a = rng.standard_normal((256, 256)).astype(np.float32)
    b = rng.standard_normal((256, 256)).astype(np.float32)

    pce = analyzer._peak_to_correlation_energy(a, b)

    assert pce < analyzer.pce_threshold, f"unrelated noise should not match, got PCE={pce:.1f}"


def test_a_pattern_survives_partial_corruption(analyzer):
    """A real residual is the reference plus scene content and compression noise, so
    the statistic must tolerate a substantially degraded copy."""
    rng = np.random.default_rng(2)
    reference = rng.standard_normal((256, 256)).astype(np.float32)
    noisy = reference + rng.standard_normal((256, 256)).astype(np.float32) * 1.5

    pce = analyzer._peak_to_correlation_energy(noisy, reference)

    assert pce > analyzer.pce_threshold, f"degraded copy lost the match, PCE={pce:.1f}"


def test_mismatched_shapes_are_resized_not_rejected(analyzer):
    rng = np.random.default_rng(3)
    reference = rng.standard_normal((256, 256)).astype(np.float32)

    pce = analyzer._peak_to_correlation_energy(reference[:128, :128], reference)

    assert np.isfinite(pce)


def test_a_flat_residual_yields_zero_rather_than_nan(analyzer):
    flat = np.zeros((64, 64), dtype=np.float32)

    pce = analyzer._peak_to_correlation_energy(flat, flat)

    assert np.isfinite(pce)
    assert pce == 0.0


# ---------------------------------------------------------------------------
# Scoring bands
# ---------------------------------------------------------------------------

def test_no_reference_is_not_evaluable_rather_than_middling(analyzer):
    """The common case: a photographer's first submission from a camera. Scoring it
    0.5 would drag every such submission toward the centre of the band."""
    result = analyzer._score_prnu(pce=None, reference_available=False)

    assert result["score"] is None, "must be excluded from the Authenticity Score"
    assert result["reference_available"] is False
    assert "no reference" in " ".join(result["flags"]).lower()


def test_pce_above_threshold_confirms_the_camera(analyzer):
    result = analyzer._score_prnu(pce=140.0, reference_available=True)

    assert result["score"] == 1.0
    assert "matches" in " ".join(result["flags"]).lower()


@pytest.mark.parametrize("pce", [59.9, 25.0, 3.0, 0.0])
def test_any_pce_below_the_threshold_fails(analyzer, pce):
    """No partial credit: below 60 is consistent with a different sensor."""
    result = analyzer._score_prnu(pce=pce, reference_available=True)

    assert result["score"] == 0.0
    assert "does not match" in " ".join(result["flags"]).lower()


def test_the_reported_pce_is_carried_through(analyzer):
    assert analyzer._score_prnu(pce=88.5, reference_available=True)["pce"] == 88.5


# ---------------------------------------------------------------------------
# Integration with the analyzer, and with the score
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_analyze_reports_prnu_as_not_evaluable_without_a_reference(analyzer, tmp_path):
    from PIL import Image
    path = tmp_path / "photo.jpg"
    rng = np.random.default_rng(4)
    Image.fromarray(rng.integers(0, 255, (256, 384, 3), dtype=np.uint8)).save(str(path), "JPEG")

    result = await analyzer.analyze(str(path))

    assert result["prnu_score"] is None
    assert result["prnu_reference_available"] is False


def test_the_authenticity_score_excludes_an_unevaluable_prnu():
    """Closes the loop: a None prnu_score must renormalise, not count as a failure."""
    from app.services.authenticity_score import AuthenticityScorer

    scorer = AuthenticityScorer()
    result = scorer.score(
        {"verdict": "PASS", "metadata_source": "RAW", "forensic_indicators": 0,
         "camera_fields_found": 8, "ai_signatures_found": 0},
        {"verdict": "PASS", "prnu_score": None, "ela_score": 1.0, "fft_score": 1.0},
        None,
        {"verdict": "PASS", "confidence": 1.0, "crop_fraction": 1.0, "geometry": None},
    )

    assert "prnu" in result["missing"]
    assert result["score"] == 100, result


def test_the_dead_ela_threshold_is_gone(analyzer):
    """self.ela_threshold was never read - _analyze_ela hardcodes 50.0 and 30.0."""
    assert not hasattr(analyzer, "ela_threshold")
