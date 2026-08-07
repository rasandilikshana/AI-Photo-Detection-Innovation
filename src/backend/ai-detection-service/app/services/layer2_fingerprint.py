"""
Layer 2: Digital Fingerprint Analysis Service
Core innovation: PRNU, ELA, and FFT analysis for detecting AI-generated images
"""

import logging
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pywt
from PIL import Image
from scipy import fftpack
from skimage.filters import wiener

logger = logging.getLogger(__name__)


class DigitalFingerprintAnalyzer:
    """
    Performs pixel-level forensic analysis using three techniques:

    1. PRNU (Photo Response Non-Uniformity) - Camera sensor fingerprinting
    2. ELA (Error Level Analysis) - Compression artifact detection
    3. FFT (Fast Fourier Transform) - Frequency domain analysis

    AI-generated images lack genuine sensor noise patterns and have
    characteristic frequency signatures that differ from real photographs.
    """

    def __init__(self):
        # PCE (Peak-to-Correlation Energy) is the decision statistic for sensor
        # fingerprint matching. 60 corresponds to a false-accept rate near 1e-5
        # (Goljan, Fridrich & Filler, "Large scale test of sensor fingerprint camera
        # identification", SPIE Media Forensics 2009). It is a published value, not a
        # tunable one.
        #
        # This replaced a residual-energy threshold (var(image - denoised) > 0.0001)
        # that could not discriminate at all: a genuine Canon JPEG measured 2.26e-05
        # and a synthetic AI image 1.39e-05 -- both scored "weak" -- while a
        # Photoshop-edited real photo measured 2.53e-04 and scored "valid", because
        # editing adds high-frequency content. It was measuring sharpness, not silicon.
        # Measured with this implementation on 256x256 patterns:
        #   identical pattern           PCE = 66,592
        #   heavily degraded copy       PCE = 20,108   (reference + 1.5x noise)
        #   unrelated white noise       PCE =     23.8
        # So 60 separates cleanly, with four orders of magnitude of margin on genuine
        # matches. There is deliberately NO intermediate "weakly consistent" band: PCE
        # below the threshold is statistically consistent with a different sensor, so
        # grading it would invent a gradation the statistic does not support.
        self.pce_threshold = 60.0

        # Empirically tuned, not calibrated against labelled data. Weighted low in the
        # Authenticity Score for that reason.
        self.fft_threshold = 0.15  # High-frequency content threshold

    async def analyze(self, jpg_path: str, raw_path: Optional[str] = None,
                      reference_pattern: Optional[np.ndarray] = None) -> Dict:
        """
        Perform comprehensive digital fingerprint analysis

        Args:
            jpg_path: Path to JPG file
            raw_path: Optional path to RAW file
            reference_pattern: This camera body's accumulated PRNU reference, supplied by
                the caller (this service has no database access). Without it, PRNU is
                reported as not evaluable rather than guessed at.

        Returns:
            Analysis result with verdict and confidence
        """
        try:
            logger.info("Starting digital fingerprint analysis")

            flags = []
            scores = {}

            # Load image
            image = cv2.imread(jpg_path)
            if image is None:
                return self._error_result("Failed to load image")

            # === Analysis 1: PRNU Extraction and Analysis ===
            prnu_result = await self._analyze_prnu(image, reference_pattern)
            scores["prnu"] = prnu_result["score"]
            flags.extend(prnu_result["flags"])

            # === Analysis 2: Error Level Analysis (ELA) ===
            ela_result = await self._analyze_ela(jpg_path)
            scores["ela"] = ela_result["score"]
            flags.extend(ela_result["flags"])

            # === Analysis 3: Frequency Domain Analysis (FFT) ===
            fft_result = await self._analyze_fft(image)
            scores["fft"] = fft_result["score"]
            flags.extend(fft_result["flags"])

            # Calculate overall confidence and verdict
            verdict, confidence = self._calculate_verdict(scores)

            def finite(value) -> Optional[float]:
                """NaN/Inf is not JSON-serializable and must never reach the API response.
                None passes through: it means 'not evaluable', which the Authenticity
                Score reads as an instruction to exclude the signal and renormalise."""
                if value is None:
                    return None
                return float(value) if np.isfinite(value) else 0.0

            return {
                "verdict": verdict,
                "confidence": finite(confidence),
                "flags": flags,
                "prnu_score": finite(scores["prnu"]),
                "ela_score": finite(scores["ela"]),
                "fft_score": finite(scores["fft"]),
                "prnu_energy": finite(prnu_result.get("energy", 0.0)),
                "prnu_pce": finite(prnu_result.get("pce")),
                "prnu_reference_available": bool(prnu_result.get("reference_available", False)),
                "ela_uniformity": finite(ela_result.get("uniformity", 0.0)),
                "fft_high_freq_ratio": finite(fft_result.get("high_freq_ratio", 0.0)),
                "analysis": self._generate_summary(verdict, scores),
            }

        except Exception as e:
            logger.error(f"Digital fingerprint analysis failed: {str(e)}", exc_info=True)
            return self._error_result(str(e))

    async def _analyze_prnu(self, image: np.ndarray,
                            reference_pattern: Optional[np.ndarray] = None) -> Dict:
        """
        PRNU (Photo Response Non-Uniformity) Analysis

        Extracts the sensor noise residual, then correlates it against this camera
        body's reference fingerprint. The residual alone is not a fingerprint: its
        energy rises with editing and an AI image can match a real camera's value.
        Identifying WHICH sensor produced an image requires correlation.

        Returns:
            Analysis result with score (None when not evaluable) and flags
        """
        try:
            # Convert to grayscale for noise analysis
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Resize for computational efficiency (optional)
            if gray.shape[0] > 1024 or gray.shape[1] > 1024:
                gray = cv2.resize(gray, (1024, int(1024 * gray.shape[0] / gray.shape[1])))

            # Convert to float
            img_float = gray.astype(np.float32) / 255.0

            # === PRNU Extraction using Wavelet Denoising ===

            # 1. Apply 2D Discrete Wavelet Transform
            coeffs = pywt.dwt2(img_float, "db8")
            cA, (cH, cV, cD) = coeffs

            # 2. Denoise using soft thresholding
            sigma = self._estimate_noise(cD)
            threshold = sigma * np.sqrt(2 * np.log(img_float.size))

            cH_denoised = pywt.threshold(cH, threshold, mode="soft")
            cV_denoised = pywt.threshold(cV, threshold, mode="soft")
            cD_denoised = pywt.threshold(cD, threshold, mode="soft")

            # 3. Reconstruct denoised image
            denoised_coeffs = (cA, (cH_denoised, cV_denoised, cD_denoised))
            denoised = pywt.idwt2(denoised_coeffs, "db8")

            # Handle size mismatch after reconstruction
            if denoised.shape != img_float.shape:
                denoised = cv2.resize(denoised, (img_float.shape[1], img_float.shape[0]))

            # 4. Extract PRNU noise residual
            prnu = img_float - denoised

            # Calculate PRNU energy (variance of noise pattern)
            prnu_energy = np.var(prnu)

            # Wavelet soft-thresholding divides by the coefficient magnitude, which is
            # zero across the flat regions of a heavily crushed image (e.g. a 90%-black
            # monochrome conversion), producing NaN. Every comparison against NaN is
            # False, so an unguarded NaN would fall through to a perfect PRNU score.
            if not np.isfinite(prnu_energy):
                logger.warning("PRNU residual non-finite (flat/crushed image) - not evaluable")
                return {
                    "score": None,
                    "flags": ["PRNU not evaluable: image too flat for sensor-noise analysis "
                              "(heavy tonal crush or large uniform areas)"],
                    "energy": 0.0,
                    "pce": None,
                    "reference_available": False,
                }

            # Correlate the residual against this camera body's reference fingerprint.
            # Residual energy alone says nothing about WHICH sensor produced it -- see
            # _score_prnu and the pce_threshold comment for the measurements that
            # established this.
            if reference_pattern is None:
                outcome = self._score_prnu(None, reference_available=False)
            else:
                pce = self._peak_to_correlation_energy(prnu, reference_pattern)
                outcome = self._score_prnu(pce, reference_available=True)

            return {
                "score": outcome["score"],
                "flags": outcome["flags"],
                # Retained as descriptive evidence only. It is NOT a verdict input:
                # editing raises it and AI images can match a real camera's value.
                "energy": float(prnu_energy),
                "pce": outcome["pce"],
                "reference_available": outcome["reference_available"],
            }

        except Exception as e:
            logger.error(f"PRNU analysis failed: {str(e)}")
            return {"score": None, "flags": [f"PRNU not evaluable: {str(e)}"],
                    "energy": 0.0, "pce": None, "reference_available": False}

    def _estimate_noise(self, coeffs: np.ndarray) -> float:
        """Estimate noise level using MAD (Median Absolute Deviation)"""
        return np.median(np.abs(coeffs)) / 0.6745

    def _peak_to_correlation_energy(self, residual: np.ndarray, reference: np.ndarray) -> float:
        """PCE: the squared correlation peak divided by the mean energy of the
        correlation surface, excluding a small neighbourhood around the peak.

        PCE rather than raw correlation because it is scale-free and its distribution
        under the null hypothesis is known, which is what makes a fixed threshold
        meaningful across images of different size and content.
        """
        a = np.asarray(residual, dtype=np.float32)
        b = np.asarray(reference, dtype=np.float32)
        if a.shape != b.shape:
            b = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)

        a = a - a.mean()
        b = b - b.mean()
        if not np.any(a) or not np.any(b):
            return 0.0

        # Normalised circular cross-correlation via FFT.
        spectrum = np.fft.rfft2(a) * np.conj(np.fft.rfft2(b))
        correlation = np.fft.irfft2(spectrum, s=a.shape)
        denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
        if denominator <= 0 or not np.isfinite(denominator):
            return 0.0
        correlation = correlation / denominator

        flat = correlation.ravel()
        peak_index = int(np.argmax(np.abs(flat)))
        peak_squared = float(flat[peak_index]) ** 2

        # Exclude an 11x11 neighbourhood of the peak from the energy estimate, so the
        # peak is not compared against itself.
        rows, cols = correlation.shape
        peak_row, peak_col = divmod(peak_index, cols)
        mask = np.ones_like(correlation, dtype=bool)
        half = 5
        for dy in range(-half, half + 1):
            row = (peak_row + dy) % rows
            for dx in range(-half, half + 1):
                mask[row, (peak_col + dx) % cols] = False

        remaining = correlation[mask]
        if remaining.size == 0:
            return 0.0
        energy = float(np.mean(remaining.astype(np.float64) ** 2))
        if energy <= 0 or not np.isfinite(energy):
            return 0.0

        pce = peak_squared / energy
        return float(pce) if np.isfinite(pce) else 0.0

    def _score_prnu(self, pce: Optional[float], reference_available: bool) -> Dict:
        """Map a PCE value to a 0..1 signal score.

        With no reference there is nothing to correlate against, so the score is None
        and the Authenticity Score excludes it rather than counting it against the
        photographer. Returning a middling 0.5 instead dragged every submission toward
        the centre of the band -- the genuine unedited pair scored 94 instead of 100.
        """
        if not reference_available or pce is None:
            return {
                "score": None,
                "flags": ["PRNU not evaluable: no reference fingerprint stored for this "
                          "camera body yet (first submission from this camera)"],
                "pce": None,
                "reference_available": False,
            }

        if pce >= self.pce_threshold:
            return {
                "score": 1.0,
                "flags": [f"PRNU matches this camera body's sensor fingerprint "
                          f"(PCE={pce:.1f}, threshold {self.pce_threshold:.0f})"],
                "pce": pce,
                "reference_available": True,
            }

        # Below the threshold is statistically consistent with a different sensor.
        # Note the failure mode this accepts: a reference built from too few images can
        # push a GENUINE match below 60 and score it zero. That is tolerable because
        # PRNU carries only 10 of 100 points and is not a critical signal, so a false
        # zero moves a score by 10 points and can never by itself cause a rejection.
        return {
            "score": 0.0,
            "flags": [f"PRNU does not match this camera body's stored fingerprint "
                      f"(PCE={pce:.1f}, threshold {self.pce_threshold:.0f})"],
            "pce": pce,
            "reference_available": True,
        }

    async def _analyze_ela(self, jpg_path: str) -> Dict:
        """
        Error Level Analysis (ELA)

        Detect compression inconsistencies. AI-generated images often show
        uniform high compression errors across the entire image.

        Returns:
            Analysis result with score and flags
        """
        try:
            # Load original image
            original = Image.open(jpg_path)

            # Re-save at fixed quality
            import io

            buffer = io.BytesIO()
            original.save(buffer, format="JPEG", quality=95)
            buffer.seek(0)

            # Load re-saved image
            resaved = Image.open(buffer)

            # Convert to numpy arrays
            orig_array = np.array(original).astype(np.float32)
            resaved_array = np.array(resaved).astype(np.float32)

            # Ensure same dimensions
            if orig_array.shape != resaved_array.shape:
                resaved_array = cv2.resize(resaved_array, (orig_array.shape[1], orig_array.shape[0]))

            # Calculate absolute difference (ELA image)
            ela = np.abs(orig_array - resaved_array)

            # Calculate ELA metrics
            ela_mean = np.mean(ela)
            ela_std = np.std(ela)
            ela_max = np.max(ela)

            # Uniformity measure (high std = non-uniform, low std = uniform/suspicious)
            uniformity = ela_std

            flags = []
            score = 1.0

            # ELA Logic Fix:
            # - Genuine photos saved once at high quality have LOW and UNIFORM compression differences
            # - Manipulated/composite images have HIGH and NON-UNIFORM compression differences
            # - AI-generated images often have unusual patterns but not necessarily high uniformity

            # Check for manipulation indicators (high non-uniformity suggests edits/composites)
            if uniformity > 50.0:
                flags.append(f"SUSPICIOUS: High ELA non-uniformity detected (std={uniformity:.2f})")
                flags.append("Image shows inconsistent compression - possible manipulation")
                score = 0.3
            elif uniformity > 30.0:
                flags.append(f"WARNING: Elevated ELA non-uniformity (std={uniformity:.2f})")
                score = 0.6
            else:
                # Low uniformity is NORMAL for genuine unedited photos
                flags.append(f"Normal ELA pattern (std={uniformity:.2f})")
                score = 1.0

            # Check for suspiciously high overall error (could indicate heavy editing)
            if ela_mean > 30:
                flags.append(f"Elevated compression error detected (mean={ela_mean:.2f})")
                score *= 0.8

            return {
                "score": score,
                "flags": flags,
                "uniformity": float(uniformity),
                "mean_error": float(ela_mean),
                "max_error": float(ela_max),
            }

        except Exception as e:
            logger.error(f"ELA analysis failed: {str(e)}")
            return {"score": 0.5, "flags": [f"ELA analysis error: {str(e)}"], "uniformity": 0.0}

    async def _analyze_fft(self, image: np.ndarray) -> Dict:
        """
        Fast Fourier Transform (FFT) Frequency Domain Analysis

        AI-generated images often lack high-frequency detail/noise that
        real photographs contain due to sensor characteristics and scene textures.

        Returns:
            Analysis result with score and flags
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Resize for efficiency
            if gray.shape[0] > 512 or gray.shape[1] > 512:
                gray = cv2.resize(gray, (512, 512))

            # Apply 2D FFT
            fft = fftpack.fft2(gray)
            fft_shifted = fftpack.fftshift(fft)

            # Calculate magnitude spectrum
            magnitude = np.abs(fft_shifted)
            magnitude = np.log1p(magnitude)  # Log scale for better visualization

            # Analyze frequency distribution
            h, w = magnitude.shape
            center_y, center_x = h // 2, w // 2

            # Define regions: center (low freq) vs edges (high freq)
            # Low frequency: center 25%
            # High frequency: outer 25%

            low_freq_radius = int(min(h, w) * 0.125)
            high_freq_radius_inner = int(min(h, w) * 0.375)

            # Create masks
            y, x = np.ogrid[:h, :w]
            distance = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)

            low_freq_mask = distance <= low_freq_radius
            high_freq_mask = distance >= high_freq_radius_inner

            # Calculate energy in each region
            low_freq_energy = np.sum(magnitude[low_freq_mask])
            high_freq_energy = np.sum(magnitude[high_freq_mask])

            # Calculate ratio (real photos have significant high-freq content)
            total_energy = low_freq_energy + high_freq_energy
            if total_energy > 0:
                high_freq_ratio = high_freq_energy / total_energy
            else:
                high_freq_ratio = 0.0

            flags = []
            score = 1.0

            if high_freq_ratio < self.fft_threshold:
                flags.append(f"SUSPICIOUS: Low high-frequency content (ratio={high_freq_ratio:.4f})")
                flags.append("Image lacks natural high-frequency detail - AI smoothing detected")
                score = 0.1
            elif high_freq_ratio < self.fft_threshold * 1.5:
                flags.append(f"WARNING: Below-normal high-frequency content (ratio={high_freq_ratio:.4f})")
                score = 0.5
            else:
                flags.append(f"Normal frequency distribution (high-freq ratio={high_freq_ratio:.4f})")
                score = 1.0

            return {
                "score": score,
                "flags": flags,
                "high_freq_ratio": float(high_freq_ratio),
                "low_freq_energy": float(low_freq_energy),
                "high_freq_energy": float(high_freq_energy),
            }

        except Exception as e:
            logger.error(f"FFT analysis failed: {str(e)}")
            return {"score": 0.5, "flags": [f"FFT analysis error: {str(e)}"], "high_freq_ratio": 0.0}

    def _calculate_verdict(self, scores: Dict[str, float]) -> Tuple[str, float]:
        """
        Calculate overall verdict based on all three analysis methods

        Weighting:
        - PRNU: 50% (most reliable indicator)
        - ELA: 25%
        - FFT: 25%

        Returns:
            (verdict: str, confidence: float)
        """
        # A None score means not evaluable. Exclude it and renormalise over the
        # remaining weights rather than counting it as a failure -- the same rule the
        # Authenticity Score applies. PRNU is unevaluable for every first submission
        # from a camera, so treating it as zero would fail most honest photographers.
        weights = {"prnu": 0.50, "ela": 0.25, "fft": 0.25}
        usable = {k: w for k, w in weights.items() if scores.get(k) is not None}

        if not usable:
            return "SUSPICIOUS", 0.5

        total_weight = sum(usable.values())
        weighted_score = sum(scores[k] * w for k, w in usable.items()) / total_weight

        if weighted_score < 0.3:
            verdict = "REJECT"
        elif weighted_score < 0.6:
            verdict = "SUSPICIOUS"
        else:
            verdict = "PASS"

        return verdict, weighted_score

    def _generate_summary(self, verdict: str, scores: Dict[str, Optional[float]]) -> str:
        """Generate human-readable analysis summary. A None score is reported as n/a
        rather than as a number, because 'not evaluable' and 'scored zero' are
        different findings and a judge must be able to tell them apart."""
        def show(key: str) -> str:
            value = scores.get(key)
            return "n/a" if value is None else f"{value:.2f}"

        return (
            f"Digital fingerprint analysis: {verdict} "
            f"(PRNU={show('prnu')}, ELA={show('ela')}, FFT={show('fft')})"
        )

    def _error_result(self, error_msg: str) -> Dict:
        """Return error result structure"""
        return {
            "verdict": "ERROR",
            "confidence": 0.0,
            "flags": [f"Analysis error: {error_msg}"],
            "prnu_score": 0.0,
            "ela_score": 0.0,
            "fft_score": 0.0,
            "analysis": "Digital fingerprint analysis failed",
        }
