"""Weighted Authenticity Score.

Replaces sequential verdict override, where each layer overwrote confidence_score
and the final number reflected whichever layer spoke last rather than the weight of
evidence — so a measured, decisive signal could be erased by a tuned, weak one.

Weights come from measured discriminative power on this platform's own data:
geometric linkage separates genuine from substituted pairs by two orders of
magnitude (463-883 RANSAC inliers versus 4-5), so it outweighs pixel statistics
whose thresholds were relaxed empirically until real photos stopped failing.

The load-bearing rule: a signal that could not be EVALUATED is excluded and the
remaining weights renormalise — never scored zero. Scoring an unavailable signal as
zero punishes the photographer for our inability to measure, which is the single
easiest way to reject a genuine entry. A signal that WAS evaluated and failed keeps
its weight and scores zero.
"""

import json

import pytest

from app.services.authenticity_score import AuthenticityScorer


@pytest.fixture
def scorer():
    return AuthenticityScorer()


def _l1(verdict="PASS", confidence=1.0, forensic=0, source="RAW", fields=8, ai_sigs=0,
        decisive=None, hygiene=0):
    return {"verdict": verdict, "confidence": confidence, "forensic_indicators": forensic,
            "metadata_source": source, "camera_fields_found": fields,
            "ai_signatures_found": ai_sigs,
            "decisive_indicators": forensic if decisive is None else decisive,
            "hygiene_indicators": hygiene}


def _l2(prnu=1.0, ela=1.0, fft=1.0, **extra):
    result = {"verdict": "PASS", "prnu_score": prnu, "ela_score": ela, "fft_score": fft}
    result.update(extra)
    return result


def _linkage(verdict="PASS", inliers=500, crop_like=True, ratio=0.93, low_texture=False,
             crop_fraction=0.8):
    return {"verdict": verdict, "confidence": ratio, "crop_fraction": crop_fraction,
            "geometry": {"inliers": inliers, "crop_like": crop_like, "inlier_ratio": ratio,
                         "low_texture": low_texture}}


# ---------------------------------------------------------------------------
# Structural invariants
# ---------------------------------------------------------------------------

def test_weights_sum_to_one_hundred(scorer):
    assert sum(scorer.WEIGHTS.values()) == 100


def test_bands_are_ordered_and_cover_zero_to_one_hundred(scorer):
    lows = [low for low, _, _, _ in scorer.BANDS]
    assert lows == sorted(lows, reverse=True), "bands must be listed highest first"
    assert scorer.BANDS[0][1] == 100
    assert scorer.BANDS[-1][0] == 0
    # no gaps between adjacent bands: each band's high must abut the next band's low
    for (lower_low, lower_high, _, _), (upper_low, _, _, _) in zip(scorer.BANDS[1:], scorer.BANDS[:-1]):
        assert lower_high + 1 == upper_low, f"gap between {lower_high} and {upper_low}"


def test_every_score_lands_in_exactly_one_band(scorer):
    for value in range(0, 101):
        matches = [b for b in scorer.BANDS if b[0] <= value <= b[1]]
        assert len(matches) == 1, f"score {value} matched {len(matches)} bands"


# ---------------------------------------------------------------------------
# The five real cases this must get right
# ---------------------------------------------------------------------------

def test_a_fully_clean_submission_scores_at_the_top(scorer):
    result = scorer.score(_l1(), _l2(), None, _linkage(crop_fraction=1.0))

    assert result["score"] >= 90, result
    assert result["verdict"] == "AUTHENTIC"


def test_legitimate_heavy_edit_stays_approvable(scorer):
    """Submission 38: a monochrome crop. Linkage confirms it geometrically; pixel
    statistics look unusual because the file was genuinely edited. It must not fall
    out of the approve bands on the strength of the weaker signals."""
    result = scorer.score(_l1(), _l2(prnu=0.5), None, _linkage(inliers=462, ratio=0.93))

    assert result["score"] >= 75, result
    assert result["verdict"] == "AUTHENTIC"


def test_substituted_jpeg_scores_in_the_reject_band(scorer):
    """Wrong-RAW pairing: linkage finds no matching crop and the evidence agrees."""
    result = scorer.score(
        _l1(verdict="SUSPICIOUS", confidence=0.4, forensic=1),
        _l2(prnu=0.5),
        {"verdict": "REJECT", "ai_score": 0.95},
        _linkage(verdict="REJECT", inliers=4, crop_like=False, ratio=0.24, crop_fraction=0.0),
    )

    assert result["score"] <= 49, result
    assert result["verdict"] in ("REJECT", "QUARANTINE")


def test_synthetic_raw_submission_is_rejected(scorer):
    """Submission 45: four provenance indicators, and Hive rejects the pixels."""
    result = scorer.score(
        _l1(verdict="SUSPICIOUS", confidence=0.4, forensic=4),
        _l2(prnu=0.5),
        {"verdict": "REJECT", "ai_score": 0.97},
        _linkage(crop_fraction=1.0),
    )

    assert result["score"] <= 49, result


# ---------------------------------------------------------------------------
# The renormalisation rule
# ---------------------------------------------------------------------------

def test_an_unavailable_signal_is_excluded_not_scored_zero(scorer):
    """Layer 3 not run is the normal case for a clean submission. It must not cost
    the submission its weight."""
    with_l3 = scorer.score(_l1(), _l2(), {"verdict": "AUTHENTIC", "ai_score": 0.01}, _linkage())
    without_l3 = scorer.score(_l1(), _l2(), None, _linkage())

    assert "third_party" in without_l3["missing"]
    assert "third_party" not in with_l3["missing"]
    assert without_l3["score"] == pytest.approx(with_l3["score"], abs=2)


def test_low_texture_linkage_is_excluded_not_penalised(scorer):
    """Fog, minimalism, long exposures: geometry genuinely cannot decide. That is an
    absence of information, not evidence against the photographer."""
    result = scorer.score(_l1(), _l2(), None,
                          _linkage(verdict="SUSPICIOUS", inliers=6, crop_like=False,
                                   low_texture=True))

    assert "geometric_linkage" in result["missing"]
    assert result["score"] >= 75, result


def test_a_failed_signal_keeps_its_weight_and_scores_zero(scorer):
    """Distinguishes 'could not measure' from 'measured and failed'."""
    failed = scorer.score(_l1(), _l2(), None, _linkage(verdict="REJECT", inliers=3,
                                                       crop_like=False, ratio=0.1))

    assert "geometric_linkage" not in failed["missing"]
    assert any(s["name"] == "geometric_linkage" and s["score"] == 0.0 for s in failed["signals"])


def test_metadata_hygiene_alone_does_not_reject_a_genuine_edit(scorer):
    """Production submissions 33 and 36. A photographer exports from Photoshop (which
    strips EXIF), copies their own metadata back, and trips three hygiene checks: stale
    dimensions, an exiftool XMP toolkit, and RAW-sensor tags. The RAW passes provenance
    and geometry confirms the crop, so this is honest work.

    Caught by a backfill dry run, which would have written REJECTED onto both."""
    result = scorer.score(
        _l1(verdict="SUSPICIOUS", confidence=0.4, forensic=3, decisive=0, hygiene=3),
        _l2(), None, _linkage(inliers=462, ratio=0.93),
    )

    assert result["verdict"] != "REJECT", result
    assert result["score"] >= 50, result


def test_hygiene_still_costs_points_and_is_visible(scorer):
    """It must not be free either - a judge should see it in the evidence."""
    clean = scorer.score(_l1(), _l2(), None, _linkage())
    dirty = scorer.score(_l1(forensic=3, decisive=0, hygiene=3), _l2(), None, _linkage())

    assert dirty["score"] < clean["score"]
    metadata_signal = next(s for s in dirty["signals"] if s["name"] == "metadata")
    assert "hygiene" in metadata_signal["evidence"]


def test_a_decisive_indicator_still_rejects(scorer):
    """The separation must not weaken the real detection: three decisive indicators on
    the RAW is submission 45, and it stays rejected."""
    result = scorer.score(
        _l1(verdict="SUSPICIOUS", confidence=0.4, forensic=4, decisive=4, hygiene=0),
        _l2(), None, _linkage(),
    )

    assert result["score"] <= 24, result
    assert result["verdict"] == "REJECT"


def test_an_old_payload_without_separated_counts_is_not_scored_as_clean(scorer):
    """Records written before the counts were separated have only
    forensic_indicators. Falling back to it prevents an old payload from being
    silently treated as having zero decisive indicators."""
    legacy = {"verdict": "SUSPICIOUS", "confidence": 0.4, "forensic_indicators": 4,
              "metadata_source": "RAW", "camera_fields_found": 8, "ai_signatures_found": 0}

    result = scorer.score(legacy, _l2(), None, _linkage())

    assert result["score"] <= 24, result


def test_a_decisive_critical_failure_cannot_be_outvoted_by_averaging(scorer):
    """The flaw a weighted mean introduces: a substituted JPEG shipped with a genuine
    donor RAW has perfect camera metadata by construction — that IS the attack — so
    15/15 metadata plus 5/5 frequency scored it 50/100 until the cap existed.

    A zero on provenance or linkage means 'not a photograph from this camera', which
    no amount of agreement elsewhere can offset."""
    everything_else_perfect = scorer.score(
        _l1(fields=8),                    # metadata: full marks
        _l2(prnu=1.0, ela=1.0, fft=1.0),  # pixel stats: full marks
        {"verdict": "AUTHENTIC", "ai_score": 0.0},  # Hive: full marks
        _linkage(verdict="REJECT", inliers=4, crop_like=False, ratio=0.2),  # fatal
    )

    assert everything_else_perfect["score"] <= 24, everything_else_perfect
    assert everything_else_perfect["verdict"] == "REJECT"


def test_a_layer_reject_caps_the_score_so_the_panel_cannot_contradict_itself(scorer):
    """Production submission 27. Hive AI rejected it above 90% AI-generated confidence,
    but third_party carries only 5 of 100 points, so the score stayed at 84 - inside the
    approve band - while the status read REJECTED. A judge saw both."""
    result = scorer.score(
        _l1(), _l2(), {"verdict": "REJECT", "ai_score": 0.95}, _linkage(),
        layer_reject_reason="third-party detector identified generated content",
    )

    assert result["score"] <= 24, result
    assert result["verdict"] == "REJECT"
    assert "third-party detector" in result["action"]


def test_no_reject_reason_leaves_the_score_alone(scorer):
    with_reason = scorer.score(_l1(), _l2(), None, _linkage(), layer_reject_reason="x")
    without = scorer.score(_l1(), _l2(), None, _linkage())

    assert with_reason["score"] <= 24
    assert without["score"] >= 90


def test_the_cap_does_not_fire_on_an_inconclusive_signal(scorer):
    """Only a decisive zero caps. Inconclusive (0.35) must stay reviewable, or every
    hard-to-match legitimate edit becomes an auto-rejection."""
    result = scorer.score(_l1(), _l2(), None,
                          _linkage(verdict="SUSPICIOUS", inliers=20, crop_like=True, ratio=0.4))

    assert result["score"] > 24, result
    assert result["verdict"] == "QUARANTINE"


def test_missing_raw_metadata_is_a_hard_failure_not_a_gap(scorer):
    """RAW is mandatory as of Task 2, so its absence is evidence rather than an
    inability to measure."""
    result = scorer.score(_l1(source="JPG"), _l2(), None, None)

    assert "raw_provenance" not in result["missing"]
    assert result["score"] <= 49, result


# ---------------------------------------------------------------------------
# Overrides and evidence
# ---------------------------------------------------------------------------

def test_ai_signature_forces_rejection_regardless_of_other_signals(scorer):
    """A file naming its own generator is not a weighing exercise."""
    result = scorer.score(_l1(verdict="REJECT", ai_sigs=2), _l2(), None, _linkage())

    assert result["verdict"] == "REJECT"
    assert result["score"] == 0


def test_every_signal_reports_evidence_a_judge_can_read(scorer):
    result = scorer.score(_l1(), _l2(), {"verdict": "AUTHENTIC", "ai_score": 0.02}, _linkage())

    assert len(result["signals"]) >= 5
    for signal in result["signals"]:
        assert signal["evidence"], f"{signal['name']} must explain itself to a judge"
        assert 0.0 <= signal["score"] <= 1.0
        assert signal["weight"] > 0


def test_contributions_and_weights_are_consistent(scorer):
    result = scorer.score(_l1(), _l2(), None, _linkage())

    for signal in result["signals"]:
        assert signal["contribution"] == pytest.approx(signal["weight"] * signal["score"], abs=0.01)


def test_score_is_bounded(scorer):
    """Even absurd inputs must not escape 0..100."""
    high = scorer.score(_l1(fields=99), _l2(prnu=5.0, ela=5.0, fft=5.0), None, _linkage(ratio=3.0))
    assert 0 <= high["score"] <= 100


def test_all_signals_unavailable_scores_zero_rather_than_dividing_by_zero(scorer):
    result = scorer.score({}, None, None, None)

    assert result["score"] == 0
    assert result["verdict"] == "REJECT"


def test_result_is_json_serialisable(scorer):
    json.dumps(scorer.score(_l1(), _l2(), {"verdict": "AUTHENTIC", "ai_score": 0.02}, _linkage()))


def test_band_reports_an_action_for_the_judge(scorer):
    result = scorer.score(_l1(), _l2(), None, _linkage())

    assert result["action"]
    assert result["band"]
