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
        self.prnu_threshold = 0.02  # Minimum PRNU energy
        self.ela_threshold = 30.0  # ELA uniformity threshold
        self.fft_threshold = 0.15  # High-frequency content threshold

    async def analyze(self, jpg_path: str, raw_path: Optional[str] = None) -> Dict:
        """
        Perform comprehensive digital fingerprint analysis

        Args:
            jpg_path: Path to JPG file
            raw_path: Optional path to RAW file

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
            prnu_result = await self._analyze_prnu(image)
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

            return {
                "verdict": verdict,
                "confidence": confidence,
                "flags": flags,
                "prnu_score": scores["prnu"],
                "ela_score": scores["ela"],
                "fft_score": scores["fft"],
                "prnu_energy": prnu_result.get("energy", 0.0),
                "ela_uniformity": ela_result.get("uniformity", 0.0),
                "fft_high_freq_ratio": fft_result.get("high_freq_ratio", 0.0),
                "analysis": self._generate_summary(verdict, scores),
            }

        except Exception as e:
            logger.error(f"Digital fingerprint analysis failed: {str(e)}", exc_info=True)
            return self._error_result(str(e))

    async def _analyze_prnu(self, image: np.ndarray) -> Dict:
        """
        PRNU (Photo Response Non-Uniformity) Analysis

        Extract sensor noise pattern. AI-generated images lack genuine
        sensor noise and will have flat/null PRNU patterns.

        Returns:
            Analysis result with score and flags
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

            # Analyze PRNU pattern
            flags = []
            score = 1.0

            if prnu_energy < self.prnu_threshold:
                flags.append(f"CRITICAL: Null/flat PRNU pattern detected (energy={prnu_energy:.6f})")
                flags.append("Image lacks genuine sensor noise - likely AI-generated")
                score = 0.0
            elif prnu_energy < self.prnu_threshold * 2:
                flags.append(f"WARNING: Weak PRNU pattern (energy={prnu_energy:.6f})")
                score = 0.3
            else:
                flags.append(f"Valid PRNU pattern detected (energy={prnu_energy:.6f})")
                score = min(1.0, prnu_energy / (self.prnu_threshold * 5))

            return {
                "score": score,
                "flags": flags,
                "energy": float(prnu_energy),
                "pattern_valid": prnu_energy >= self.prnu_threshold,
            }

        except Exception as e:
            logger.error(f"PRNU analysis failed: {str(e)}")
            return {"score": 0.5, "flags": [f"PRNU analysis error: {str(e)}"], "energy": 0.0, "pattern_valid": False}

    def _estimate_noise(self, coeffs: np.ndarray) -> float:
        """Estimate noise level using MAD (Median Absolute Deviation)"""
        return np.median(np.abs(coeffs)) / 0.6745

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

            if uniformity < self.ela_threshold:
                flags.append(f"SUSPICIOUS: Highly uniform ELA pattern (uniformity={uniformity:.2f})")
                flags.append("Entire image shows consistent compression signature - AI generation indicator")
                score = 0.2
            elif uniformity < self.ela_threshold * 1.5:
                flags.append(f"WARNING: Somewhat uniform ELA (uniformity={uniformity:.2f})")
                score = 0.5
            else:
                flags.append(f"Normal ELA pattern (uniformity={uniformity:.2f})")
                score = 1.0

            # Check for suspiciously high overall error
            if ela_mean > 50:
                flags.append(f"High compression error detected (mean={ela_mean:.2f})")
                score *= 0.7

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
        weighted_score = scores["prnu"] * 0.50 + scores["ela"] * 0.25 + scores["fft"] * 0.25

        if weighted_score < 0.3:
            verdict = "REJECT"
        elif weighted_score < 0.6:
            verdict = "SUSPICIOUS"
        else:
            verdict = "PASS"

        return verdict, weighted_score

    def _generate_summary(self, verdict: str, scores: Dict[str, float]) -> str:
        """Generate human-readable analysis summary"""
        return (
            f"Digital fingerprint analysis: {verdict} "
            f"(PRNU={scores['prnu']:.2f}, ELA={scores['ela']:.2f}, FFT={scores['fft']:.2f})"
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
