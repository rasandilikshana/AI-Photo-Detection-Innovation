"""Double-JPEG compression history.

*** NOT WIRED INTO SCORING. Retained as a documented negative result. ***

The idea: a photograph reaching a competition has been compressed at least twice, once
by the camera or RAW converter and again on export, while an image written once by a
generator carries a single-compression signature. Double quantisation leaves periodic
double peaks and empty bins in the DCT coefficient histograms (Lukas & Fridrich 2003;
Popescu & Farid 2004), interpreted via the likelihood-ratio framework of Bianchi &
Piva, IEEE TIFS 2012.

MEASURED RESULT (2026-08-07): this approach does not discriminate on our data.

    SYNTHETIC generated JPEG              DQ strength 0.048
    GENUINE   camera JPEG (Twisted)                   0.054
    GENUINE   camera JPEG (Emerald)                   0.064
    GENUINE   Photoshop export                        0.013   <-- LOWER than the fake
    GENUINE   Emerald edit                            0.119
    GENUINE   meta-transplanted edit                  0.013   <-- LOWER than the fake

The synthetic file sits inside the genuine range, and two genuine Photoshop exports
score below it. On controlled fixtures the metric is actually inverted: a
single-compressed image scored 0.454 and a double-compressed one 0.172.

CAUSE: the double-quantisation signature lives in a JPEG's STORED, quantised DCT
coefficients. This implementation computes the DCT from DECODED PIXELS and divides by
the quantisation table, which is an approximation that loses the periodic structure the
method depends on. Recovering it properly requires coefficient-level access via
jpeglib or jpegio -- a new dependency and a rework of the extraction.

Kept because the negative result is worth recording, and because the module becomes
usable the moment coefficient extraction is added. Its 10 points in the Authenticity
Score were reassigned to raw_provenance and geometric_linkage, the two signals with
measured discriminative power. Do not wire this back in without re-running the
calibration in tests/test_compression_history.py.
"""

import logging
from typing import Dict, List, Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class CompressionHistoryAnalyzer:
    """Decides whether a JPEG shows single- or double-compression history."""

    # Calibrated against single- vs double-compressed fixtures and the real submission
    # files; see the class docstring in tests and the commit message for the measured
    # values. Set from the observed gap, not chosen a priori.
    DQ_THRESHOLD = 0.28

    # Low-frequency AC coefficients carry the clearest double-quantisation signature.
    # DC is excluded because it is dominated by scene brightness rather than
    # quantisation history.
    AC_INDICES = [(0, 1), (1, 0), (1, 1), (0, 2), (2, 0), (1, 2), (2, 1), (2, 2)]

    # Below this coefficient spread there is nothing to build a histogram from.
    MIN_COEFFICIENT_SPAN = 6
    MIN_BLOCKS = 64

    def analyze(self, jpg_path: str) -> Dict:
        """Returns score (0..1), evidence, double_compressed, quality_estimate,
        dq_strength. score is 0.5 and double_compressed is None when undecidable."""
        try:
            with Image.open(jpg_path) as img:
                if img.format != "JPEG":
                    return self._inconclusive(f"not a JPEG ({img.format})")
                tables = getattr(img, "quantization", None)
                gray = np.asarray(img.convert("L"), dtype=np.float32)
        except Exception as e:
            return self._inconclusive(f"unreadable ({type(e).__name__})")

        luma = None
        if tables:
            first = tables.get(0)
            if first is not None and len(first) == 64:
                luma = np.asarray(first, dtype=np.float32).reshape(8, 8)

        quality = self._estimate_quality(luma)
        strength = self._dq_strength(gray, luma)

        if strength is None:
            return self._inconclusive("insufficient texture for histogram analysis")

        if strength >= self.DQ_THRESHOLD:
            return {
                "score": 1.0,
                "evidence": (
                    f"Double-compression signature present (DQ strength {strength:.3f}, "
                    f"quality ~{quality}) - consistent with a camera or editor pipeline"
                ),
                "double_compressed": True,
                "quality_estimate": quality,
                "dq_strength": round(float(strength), 4),
            }

        return {
            "score": 0.2,
            "evidence": (
                f"Single-compression signature (DQ strength {strength:.3f}, quality "
                f"~{quality}) - no evidence this file passed through a camera or editor pipeline"
            ),
            "double_compressed": False,
            "quality_estimate": quality,
            "dq_strength": round(float(strength), 4),
        }

    # ------------------------------------------------------------------

    def _inconclusive(self, reason: str) -> Dict:
        return {
            "score": 0.5,
            "evidence": f"Compression history inconclusive: {reason}",
            "double_compressed": None,
            "quality_estimate": None,
            "dq_strength": 0.0,
        }

    def _estimate_quality(self, luma: Optional[np.ndarray]) -> Optional[int]:
        """Approximate the IJG quality factor from the luminance quantisation table.

        Uses the standard IJG scaling relation between the table sum and the quality
        setting. Approximate by nature -- reported as evidence, never as a threshold.
        """
        if luma is None:
            return None
        total = float(luma.sum())
        if total <= 0 or not np.isfinite(total):
            return None

        # IJG scales the standard table by a factor derived from quality; inverting the
        # relation on the table mean recovers quality to within a few points.
        mean = total / 64.0
        if mean <= 1.0:
            return 100
        quality = 100.0 - (mean - 1.0) * 2.0 if mean < 25 else max(1.0, 5000.0 / mean / 2.0)
        return int(max(1, min(100, round(quality))))

    def _dq_strength(self, gray: np.ndarray, luma: Optional[np.ndarray]) -> Optional[float]:
        """Periodicity of DCT coefficient histograms across low-frequency AC bins.

        Double quantisation makes each histogram periodic, so energy concentrates at a
        single non-zero frequency of the histogram's own spectrum. A singly-compressed
        histogram is smooth and spreads its spectral energy.
        """
        rows = (gray.shape[0] // 8) * 8
        cols = (gray.shape[1] // 8) * 8
        if rows < 64 or cols < 64:
            return None

        blocks = (gray[:rows, :cols]
                  .reshape(rows // 8, 8, cols // 8, 8)
                  .swapaxes(1, 2)
                  .reshape(-1, 8, 8))
        if blocks.shape[0] < self.MIN_BLOCKS:
            return None

        # Block DCT for every block at once via the separable transform.
        dct_blocks = np.stack([cv2.dct(block - 128.0) for block in blocks])

        strengths: List[float] = []
        for u, v in self.AC_INDICES:
            coeffs = dct_blocks[:, u, v]
            if luma is not None and luma[u, v] > 0:
                coeffs = coeffs / float(luma[u, v])
            coeffs = np.round(coeffs).astype(np.int64)

            span = int(coeffs.max() - coeffs.min())
            if span < self.MIN_COEFFICIENT_SPAN:
                continue

            hist = np.bincount(coeffs - coeffs.min(), minlength=span + 1).astype(np.float64)
            if hist.sum() < 32:
                continue
            hist /= hist.sum()

            spectrum = np.abs(np.fft.rfft(hist - hist.mean()))
            if spectrum.size < 3:
                continue
            tail = spectrum[1:]
            total = float(tail.sum())
            if total <= 0 or not np.isfinite(total):
                continue
            strengths.append(float(tail.max() / total))

        if not strengths:
            return None
        return float(np.median(strengths))
