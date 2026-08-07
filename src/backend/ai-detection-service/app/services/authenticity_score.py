"""Weighted Authenticity Score.

Replaces sequential verdict override. Previously each layer overwrote
confidence_score as the pipeline ran, so the final number reflected whichever layer
spoke last rather than the weight of evidence — a measured, decisive signal could be
erased by a tuned, weak one, and the number itself was not comparable between
submissions.

WEIGHTS come from measured discriminative power on this platform's own data, not from
a generic reference table:

  raw_provenance     35  container / writer-software / sensor-geometry checks. Caught
                         the only successful forgery against this platform
                         (submission 45), on four independent indicators.
  geometric_linkage  30  the only signal with a measured two-orders-of-magnitude
                         separation: 463-883 RANSAC inliers on genuine pairs versus
                         4-5 on substituted ones.
  metadata           15  camera-field completeness and transplant forensics. Caught
                         the earlier metadata-transplant attack.
  prnu               10  sensor-reference correlation by PCE. Reports "not evaluable"
                         until a per-body reference exists, and is excluded then.
  frequency           5  a crude global FFT energy ratio whose thresholds were tuned
                         empirically, not calibrated. Deliberately low.
  third_party         5  Hive AI. Strong, but external, not always consulted, and
                         its verdict already gates escalation elsewhere.

Double-JPEG compression history was implemented, measured, and DELIBERATELY EXCLUDED.
It does not discriminate on this data: the synthetic submission scored a DQ strength of
0.048, inside the genuine range of 0.013-0.119, with two genuine Photoshop exports
scoring LOWER than the fake. It was inverted on controlled fixtures too (single 0.454
versus double 0.172). The cause is that the double-quantisation signature lives in a
JPEG's STORED coefficients, and computing the DCT from decoded pixels loses it. The
module is retained as a documented negative result but is not wired into scoring; its
10 points went to the two measured-strongest signals. See compression_history.py.

THE LOAD-BEARING RULE: a signal that could not be EVALUATED is excluded and the
remaining weights renormalise. It is never scored zero. Scoring an unavailable signal
as zero punishes the photographer for our inability to measure — the single easiest
way to reject a genuine entry. A signal that WAS evaluated and failed keeps its
weight and scores zero, because that is evidence.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AuthenticityScorer:
    """Aggregates layer results into a single 0-100 score with a review band."""

    WEIGHTS = {
        "raw_provenance": 35,
        "geometric_linkage": 30,
        "metadata": 15,
        "prnu": 10,
        "frequency": 5,
        "third_party": 5,
    }

    # Signals whose decisive failure cannot be outvoted by averaging.
    #
    # A weighted mean lets good metadata dilute a fatal finding: a substituted JPEG
    # submitted with a genuine donor RAW has perfect camera fields by construction —
    # that IS the attack — and scored 50/100 before this cap existed, because 15/15
    # metadata plus 5/5 frequency outweighed a linkage score of zero.
    #
    # Both of these mean "this is not a photograph taken by this camera", which is
    # the platform's core disqualifying finding, so a zero on either caps the total
    # in the auto-reject band regardless of what else agrees. Note this fires only on
    # a DECISIVE failure: an inconclusive or unevaluable signal never reaches 0.0.
    CRITICAL_SIGNALS = ("raw_provenance", "geometric_linkage")

    # A critical signal below this is not confirmed, even though it did not fail
    # outright. A submission cannot be auto-approved on a core claim we could not
    # verify, so it is capped into the judge-review band instead. This keeps the score
    # the single source of truth: main.py's separate linkage guard used to force
    # QUARANTINE for submissions the score called AUTHENTIC.
    CONFIRMED_FLOOR = 0.75

    # (low, high, verdict, action) — highest band first, both bounds inclusive.
    # Verdicts stay within AUTHENTIC / QUARANTINE / REJECT so the existing
    # verdict_map in competition-service submissions.py keeps working unchanged.
    BANDS = [
        (90, 100, "AUTHENTIC", "Auto-approve: provenance and forensics agree"),
        (75, 89, "AUTHENTIC", "Approve, flagged for judge visibility"),
        (50, 74, "QUARANTINE", "Judge review required"),
        (25, 49, "QUARANTINE", "High suspicion - request originals or burst frames"),
        (0, 24, "REJECT", "Auto-reject"),
    ]

    def score(self, layer1: Optional[Dict], layer2: Optional[Dict],
              layer3: Optional[Dict], linkage: Optional[Dict]) -> Dict:
        """Aggregate the layer results. Returns score, band, verdict, action, and the
        per-signal breakdown a judge can read."""
        layer1 = layer1 or {}

        # A file that names its own generator is not a weighing exercise.
        if layer1.get("ai_signatures_found", 0) > 0:
            return self._result(
                0, [], [],
                forced="REJECT",
                note="Generator signature present in metadata - rejected outright",
            )

        evaluators = (
            ("raw_provenance", lambda: self._raw_provenance(layer1)),
            ("geometric_linkage", lambda: self._linkage(linkage)),
            ("metadata", lambda: self._metadata(layer1)),
            ("prnu", lambda: self._layer2_signal(layer2, "prnu_score", "Sensor noise (PRNU)")),
            ("frequency", lambda: self._layer2_signal(layer2, "fft_score", "Frequency distribution")),
            ("third_party", lambda: self._third_party(layer3)),
        )

        signals: List[Dict] = []
        missing: List[str] = []

        for name, evaluate in evaluators:
            try:
                outcome = evaluate()
            except Exception as e:
                logger.warning(f"Authenticity signal '{name}' raised {type(e).__name__}: {e}")
                outcome = None

            if outcome is None:
                missing.append(name)
                continue

            value, evidence = outcome
            value = max(0.0, min(1.0, float(value)))
            weight = self.WEIGHTS[name]
            signals.append({
                "name": name,
                "weight": weight,
                "score": round(value, 3),
                "contribution": round(weight * value, 2),
                "evidence": evidence,
            })

        available_weight = sum(s["weight"] for s in signals)
        if available_weight == 0:
            return self._result(0, signals, missing,
                                note="No signal could be evaluated")

        earned = sum(s["contribution"] for s in signals)
        score = int(round(earned / available_weight * 100))

        # A decisive failure on a critical signal cannot be averaged away, and an
        # unconfirmed one cannot be auto-approved.
        critical = [s for s in signals if s["name"] in self.CRITICAL_SIGNALS]
        fatal = [s["name"] for s in critical if s["score"] == 0.0]
        unconfirmed = [s["name"] for s in critical if 0.0 < s["score"] < self.CONFIRMED_FLOOR]

        if fatal:
            ceiling, reason = self.BANDS[-1][1], f"{', '.join(fatal)} failed decisively"
        elif unconfirmed:
            # Top of the judge-review band.
            ceiling, reason = 74, f"{', '.join(unconfirmed)} not confirmed"
        else:
            ceiling, reason = 100, ""

        if score > ceiling:
            logger.info(f"Authenticity score capped {score} -> {ceiling}: {reason}")
            score = ceiling

        return self._result(score, signals, missing)

    # ------------------------------------------------------------------

    def _result(self, score: int, signals: List[Dict], missing: List[str],
                forced: Optional[str] = None, note: str = "") -> Dict:
        score = max(0, min(100, score))
        low, high, verdict, action = next(
            (b for b in self.BANDS if b[0] <= score <= b[1]), self.BANDS[-1]
        )
        return {
            "score": score,
            "band": f"{low}-{high}",
            "verdict": forced or verdict,
            "action": note or action,
            "signals": signals,
            "missing": missing,
            "weight_evaluated": sum(s["weight"] for s in signals),
        }

    # -- individual signals: return (0..1, evidence) or None if unevaluable ----

    def _raw_provenance(self, layer1: Dict) -> Optional[Tuple[float, str]]:
        """RAW is mandatory, so an absent or unusable RAW is evidence, not a gap.

        Only DECISIVE indicators count here: the RAW is not a camera file, or the JPEG
        describes a different capture than the RAW it shipped with. Metadata-hygiene
        indicators are deliberately excluded -- a photographer who copies their own EXIF
        back onto a Photoshop export (which strips it) trips three hygiene checks while
        being entirely honest, and counting those here auto-rejected two legitimate
        submissions during the backfill dry run.
        """
        if not layer1:
            return None
        if layer1.get("metadata_source") != "RAW":
            return 0.0, "No usable RAW metadata - camera fields came from the JPEG"

        # Fall back to the combined count for records written before the counts were
        # separated, so an old payload is never scored as though it were clean.
        decisive = layer1.get("decisive_indicators")
        if decisive is None:
            decisive = layer1.get("forensic_indicators", 0)
        decisive = int(decisive or 0)

        if decisive == 0:
            return 1.0, "RAW passes writer-software, container and sensor-geometry checks"

        # Three indicators is a confident forgery call; scale to zero across that range.
        return max(0.0, 1.0 - decisive / 3.0), (
            f"{decisive} decisive provenance indicator{'s' if decisive != 1 else ''}: "
            "the RAW is not a camera file, or it records a different capture than this JPG"
        )

    def _linkage(self, linkage: Optional[Dict]) -> Optional[Tuple[float, str]]:
        if not linkage or linkage.get("verdict") in (None, "ERROR"):
            return None

        geometry = linkage.get("geometry") or {}
        verdict = linkage["verdict"]

        # Too little texture for keypoint matching: genuinely undecidable, and
        # penalising it would reject fog, minimalism and long exposures.
        if geometry.get("low_texture") and verdict != "PASS":
            return None

        if verdict == "PASS":
            if not geometry:
                return 1.0, "Whole-frame match: the JPG is this RAW, unedited"
            return 1.0, (
                f"Geometrically confirmed: {geometry.get('inliers', 0)} matching sensor "
                f"features, {linkage.get('crop_fraction', 1.0):.0%} of the RAW frame"
            )

        if verdict == "SUSPICIOUS":
            return 0.35, (
                f"Linkage inconclusive: only {geometry.get('inliers', 0)} corresponding "
                "features - a human should compare the files"
            )

        return 0.0, (
            f"No crop of the RAW matches this JPG ({geometry.get('inliers', 0)} "
            "corresponding features)"
        )

    def _metadata(self, layer1: Dict) -> Optional[Tuple[float, str]]:
        """Camera-field completeness, reduced by metadata-hygiene findings.

        Hygiene lands here rather than on raw_provenance because a rewritten metadata
        block is a fact about the METADATA, not about whether the photograph is real. It
        costs points and shows up for the judge, but cannot on its own sink a submission
        whose RAW and geometry both check out.
        """
        if not layer1 or layer1.get("camera_fields_found") is None:
            return None

        fields = int(layer1["camera_fields_found"])
        score = min(1.0, fields / 8.0)
        evidence = f"{fields}/8 camera fields present and self-consistent"

        hygiene = int(layer1.get("hygiene_indicators", 0) or 0)
        if hygiene:
            score *= max(0.0, 1.0 - 0.2 * hygiene)
            evidence += (
                f"; {hygiene} hygiene indicator{'s' if hygiene != 1 else ''} "
                "(metadata block rewritten, e.g. EXIF copied back onto an export)"
            )

        return score, evidence

    def _layer2_signal(self, layer2: Optional[Dict], key: str,
                       label: str) -> Optional[Tuple[float, str]]:
        if not layer2 or layer2.get(key) is None:
            return None
        value = float(layer2[key])
        return value, f"{label} score {value:.2f}"

    def _third_party(self, layer3: Optional[Dict]) -> Optional[Tuple[float, str]]:
        if not layer3 or layer3.get("ai_score") is None:
            return None
        ai_score = float(layer3["ai_score"])
        return 1.0 - ai_score, f"Hive AI generated-probability {ai_score:.2f}"
