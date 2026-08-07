"""Hive AI decision bands.

A false rejection costs a photographer their competition entry, while a false pass
still has to survive the metadata, provenance and linkage layers. So auto-rejection
requires high precision and anything short of it goes to a human rather than being
decided automatically. Was 0.7 reject / 0.4 quarantine before 2026-08-07.
"""

import pytest

from app.services.layer3_api import ThirdPartyAPIVerifier


@pytest.fixture
def verifier():
    return ThirdPartyAPIVerifier()


@pytest.mark.parametrize("score,expected", [
    (0.99, "REJECT"),
    (0.90, "REJECT"),
    (0.89, "QUARANTINE"),
    (0.50, "QUARANTINE"),
    (0.49, "AUTHENTIC"),
    (0.01, "AUTHENTIC"),
])
def test_hive_score_bands(verifier, score, expected):
    assert verifier.classify_hive_score(score)[0] == expected


def test_authentic_confidence_is_the_complement_of_the_ai_score(verifier):
    verdict, confidence = verifier.classify_hive_score(0.02)

    assert verdict == "AUTHENTIC"
    assert confidence == pytest.approx(0.98)


def test_reject_confidence_is_the_ai_score_itself(verifier):
    verdict, confidence = verifier.classify_hive_score(0.97)

    assert verdict == "REJECT"
    assert confidence == pytest.approx(0.97)


def test_the_old_thresholds_no_longer_auto_reject(verifier):
    """0.75 used to be an automatic rejection. It is now a human decision."""
    assert verifier.classify_hive_score(0.75)[0] == "QUARANTINE"


def test_bands_are_ordered(verifier):
    assert verifier.HIVE_REJECT_AT > verifier.HIVE_QUARANTINE_AT
