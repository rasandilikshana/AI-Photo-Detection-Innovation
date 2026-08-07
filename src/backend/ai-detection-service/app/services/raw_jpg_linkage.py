"""
RAW-JPG Linkage Analyzer
Forensically proves that a submitted JPG is derived from the submitted RAW file
Uses PRNU (Photo Response Non-Uniformity) analysis and perceptual hashing
"""

import logging
from typing import Dict, Tuple

import cv2
import imagehash
import numpy as np
import rawpy
from PIL import Image
from skimage.metrics import structural_similarity as ssim

logger = logging.getLogger(__name__)


class RAWJPGLinkageAnalyzer:
    """
    Analyzes the linkage between RAW and JPG files to detect submission forgery

    Core Innovation: Prevents attackers from submitting a genuine RAW file
    with an unrelated AI-generated JPG file.

    Methods:
    1. Perceptual Hash Comparison (pHash)
    2. Structural Similarity Index (SSIM)
    3. Color Histogram Correlation
    """

    def __init__(self):
        self.phash_threshold = 15  # Hamming distance threshold (increased for RAW processing differences)

        # Lowered thresholds to account for differences between:
        # - Camera's internal JPG processing (proprietary color science, tone curves)
        # - Basic RAW demosaicing (rawpy with camera white balance)
        # These will never be identical, but should still be visually similar
        self.ssim_threshold = 0.45  # SSIM similarity threshold (was 0.85)
        self.histogram_threshold = 0.40  # Histogram correlation threshold (was 0.90)

        # Above this Hamming distance the images are effectively different scenes
        # (256-bit hash: unrelated images average ~128). SSIM/histogram votes must
        # not outvote a failure this decisive — heavy editing lands well below it.
        self.phash_catastrophic = 45

        # Gradient crop-search thresholds. Whole-frame luminance comparison collapses
        # on legitimate crops and black-and-white conversions, so when it fails we
        # search the RAW for the crop window whose EDGE STRUCTURE matches the JPEG.
        # Edges survive tonal remapping; they do not survive scene substitution.
        # Calibrated 2026-08-07: genuine crops+heavy edits 0.79-0.93,
        # AI substitution and unrelated pairs 0.19-0.33.
        self.gradient_linked_threshold = 0.55
        self.gradient_weak_threshold = 0.35
        self.min_crop_fraction = 0.40  # smaller windows invite spurious correlation

    async def analyze_linkage(self, raw_path: str, jpg_path: str) -> Dict:
        """
        Analyze if JPG is derived from RAW file

        Args:
            raw_path: Path to RAW file
            jpg_path: Path to JPG file

        Returns:
            Analysis result with verdict
        """
        try:
            logger.info("Starting RAW-JPG linkage analysis")

            # Load and process RAW file
            raw_image = self._load_raw_image(raw_path)
            if raw_image is None:
                return {
                    "verdict": "ERROR",
                    "confidence": 0.0,
                    "flags": ["Failed to load RAW file"],
                    "method": "linkage_analysis",
                }

            # Load JPG file
            jpg_image = cv2.imread(jpg_path)
            if jpg_image is None:
                return {
                    "verdict": "ERROR",
                    "confidence": 0.0,
                    "flags": ["Failed to load JPG file"],
                    "method": "linkage_analysis",
                }

            # Resize images to same dimensions for comparison
            target_size = (1920, 1080)  # Standard comparison size
            raw_resized = cv2.resize(raw_image, target_size)
            jpg_resized = cv2.resize(jpg_image, target_size)

            flags = []

            # Method 1: Perceptual Hash Comparison (reuses the demosaiced array —
            # re-reading the RAW here previously doubled peak memory and OOM-killed
            # the worker on the 2GB production host)
            phash_match, phash_distance = self._compare_phash(raw_image, jpg_image)
            flags.append(f"pHash distance: {phash_distance}")

            # Method 2: SSIM Comparison
            ssim_score = self._compare_ssim(raw_resized, jpg_resized)
            flags.append(f"SSIM score: {ssim_score:.4f}")

            # Method 3: Color Histogram Correlation
            hist_corr = self._compare_histograms(raw_resized, jpg_resized)
            flags.append(f"Histogram correlation: {hist_corr:.4f}")

            # Release the 1920x1080 working copies before the gradient search allocates
            del raw_resized, jpg_resized

            # Determine verdict based on all three methods
            verdict, confidence = self._determine_verdict(phash_match, phash_distance, ssim_score, hist_corr)

            # Whole-frame comparison collapses on legitimate crops and black-and-white
            # conversions. Before condemning a submission, look for the crop window in
            # the RAW whose edge structure matches the JPEG.
            gradient_score, gradient_frac = 0.0, 0.0
            if verdict != "PASS":
                gradient_score, gradient_frac = self._gradient_crop_match(raw_image, jpg_image)
                flags.append(f"Gradient crop-match: {gradient_score:.4f} (crop {gradient_frac:.0%} of frame)")

                if gradient_score >= self.gradient_linked_threshold:
                    verdict = "PASS"
                    confidence = gradient_score
                    flags.append(
                        f"RAW-JPG linkage confirmed by edge-structure match ({gradient_score:.2f}) despite "
                        f"heavy editing — the JPG is a {gradient_frac:.0%} crop of this RAW, tonally reworked"
                    )
                elif gradient_score >= self.gradient_weak_threshold:
                    verdict = "SUSPICIOUS"
                    confidence = min(confidence, gradient_score)
                    flags.append("Edge-structure match inconclusive - manual review required")
                else:
                    verdict = "REJECT"
                    confidence = 0.0

            if verdict == "REJECT":
                flags.append("CRITICAL: RAW and JPG files are not linked - possible submission forgery")
            elif verdict == "SUSPICIOUS" and phash_distance > self.phash_catastrophic:
                flags.append(
                    f"CRITICAL: perceptual hash distance {phash_distance} indicates the JPG may depict a "
                    "different scene than the RAW - possible AI substitution with transplanted metadata"
                )

            return {
                "verdict": verdict,
                "confidence": confidence,
                "flags": flags,
                "method": "linkage_analysis",
                "phash_distance": float(phash_distance),
                "ssim_score": float(ssim_score),
                "histogram_correlation": float(hist_corr),
                "gradient_match": float(gradient_score),
                "gradient_crop_fraction": float(gradient_frac),
                "analysis": self._generate_analysis_summary(verdict, phash_distance, ssim_score, hist_corr),
            }

        except Exception as e:
            logger.error(f"RAW-JPG linkage analysis failed: {str(e)}", exc_info=True)
            return {
                "verdict": "ERROR",
                "confidence": 0.0,
                "flags": [f"Analysis error: {str(e)}"],
                "method": "linkage_analysis",
            }

    def _load_raw_image(self, raw_path: str) -> np.ndarray:
        """
        Load and demosaic RAW file to RGB image

        Uses half-resolution demosaicing: every comparison downstream (pHash, SSIM,
        histogram, gradient search) resizes well below full sensor resolution anyway,
        while a full-size demosaic peaks at ~284MB and exhausts the production host.

        Args:
            raw_path: Path to RAW file

        Returns:
            BGR numpy array
        """
        try:
            with rawpy.imread(raw_path) as raw:
                rgb = raw.postprocess(use_camera_wb=True, half_size=True, no_auto_bright=True, output_bps=8)
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            del rgb
            return bgr

        except Exception as e:
            logger.error(f"Failed to load RAW image: {str(e)}")
            return None

    def _compare_phash(self, raw_image: np.ndarray, jpg_image: np.ndarray) -> Tuple[bool, int]:
        """
        Compare perceptual hashes of the already-decoded RAW and JPG.

        pHash downsamples internally, so it is unaffected by the half-resolution
        demosaic and does not need a second read of the RAW file.

        Args:
            raw_image: Demosaiced RAW as a BGR array
            jpg_image: JPG as a BGR array

        Returns:
            (match: bool, hamming_distance: int)
        """
        try:
            raw_img = Image.fromarray(cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGB))
            jpg_img = Image.fromarray(cv2.cvtColor(jpg_image, cv2.COLOR_BGR2RGB))

            # Calculate perceptual hashes
            raw_hash = imagehash.phash(raw_img, hash_size=16)
            jpg_hash = imagehash.phash(jpg_img, hash_size=16)

            # Calculate Hamming distance
            distance = raw_hash - jpg_hash

            # Match if distance is below threshold
            match = distance <= self.phash_threshold

            return match, distance

        except Exception as e:
            logger.warning(f"pHash comparison failed: {str(e)}")
            return False, 999

    def _edge_map(self, gray: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
        """Normalized Sobel gradient magnitude — the structural signature of a scene,
        invariant to exposure, curves and black-and-white conversion.

        Heavily crushed images (e.g. 90%+ pure black) can yield a flat gradient field;
        normalizing that divides by zero, so it is handled explicitly."""
        g = cv2.resize(gray, size, interpolation=cv2.INTER_AREA)
        g = cv2.GaussianBlur(g, (3, 3), 0)
        gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(gx, gy)

        span = float(mag.max()) - float(mag.min())
        if span < 1e-6:
            return np.zeros_like(mag, dtype=np.float32)

        normalized = cv2.normalize(mag, None, 0, 1, cv2.NORM_MINMAX)
        return np.nan_to_num(normalized, nan=0.0, posinf=0.0, neginf=0.0)

    def _gradient_crop_match(self, raw_image: np.ndarray, jpg_image: np.ndarray) -> Tuple[float, float]:
        """Search the RAW for the crop window whose edge structure matches the JPEG.

        Handles the cases whole-frame comparison cannot: the photographer cropped,
        converted to black and white, crushed the tones, or upscaled the export.

        Returns:
            (best_correlation, best_crop_fraction)
        """
        try:
            raw_gray = cv2.cvtColor(raw_image, cv2.COLOR_BGR2GRAY)
            jpg_gray = cv2.cvtColor(jpg_image, cv2.COLOR_BGR2GRAY)

            scale_w = 1000
            rh, rw = raw_gray.shape
            small = cv2.resize(raw_gray, (scale_w, int(rh * scale_w / rw)), interpolation=cv2.INTER_AREA)
            haystack = self._edge_map(small, (small.shape[1], small.shape[0]))

            aspect = jpg_gray.shape[1] / jpg_gray.shape[0]
            best_score, best_frac = 0.0, 0.0

            for frac in [1.0, 0.95, 0.9, 0.8, 0.7, 0.6, 0.55, 0.5, 0.45, 0.40]:
                if frac < self.min_crop_fraction:
                    continue
                tw = int(small.shape[1] * frac)
                th = int(tw / aspect)
                if th > small.shape[0] or tw < 60 or th < 60:
                    continue

                template = self._edge_map(jpg_gray, (tw, th))
                if float(template.std()) < 1e-6:
                    continue  # featureless template: correlation is undefined

                result = cv2.matchTemplate(haystack, template, cv2.TM_CCOEFF_NORMED)
                result = np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)
                score = float(result.max())
                if score > best_score:
                    best_score, best_frac = score, frac

            return best_score, best_frac

        except Exception as e:
            logger.warning(f"Gradient crop match failed: {str(e)}")
            return 0.0, 0.0

    def _compare_ssim(self, raw_image: np.ndarray, jpg_image: np.ndarray) -> float:
        """
        Calculate Structural Similarity Index between images

        Args:
            raw_image: RAW image as numpy array
            jpg_image: JPG image as numpy array

        Returns:
            SSIM score (0-1)
        """
        try:
            # Convert to grayscale for SSIM calculation
            raw_gray = cv2.cvtColor(raw_image, cv2.COLOR_BGR2GRAY)
            jpg_gray = cv2.cvtColor(jpg_image, cv2.COLOR_BGR2GRAY)

            # Calculate SSIM
            score, _ = ssim(raw_gray, jpg_gray, full=True)

            # Near-constant images (heavy black crush) can yield NaN
            if not np.isfinite(score):
                return 0.0

            return score

        except Exception as e:
            logger.warning(f"SSIM comparison failed: {str(e)}")
            return 0.0

    def _compare_histograms(self, raw_image: np.ndarray, jpg_image: np.ndarray) -> float:
        """
        Compare color histograms of images

        Args:
            raw_image: RAW image as numpy array
            jpg_image: JPG image as numpy array

        Returns:
            Correlation coefficient (0-1)
        """
        try:
            # Calculate histograms for each channel
            correlations = []

            for i in range(3):  # BGR channels
                raw_hist = cv2.calcHist([raw_image], [i], None, [256], [0, 256])
                jpg_hist = cv2.calcHist([jpg_image], [i], None, [256], [0, 256])

                # Normalize histograms
                cv2.normalize(raw_hist, raw_hist)
                cv2.normalize(jpg_hist, jpg_hist)

                # Calculate correlation (undefined for a zero-variance histogram)
                corr = cv2.compareHist(raw_hist, jpg_hist, cv2.HISTCMP_CORREL)
                correlations.append(corr if np.isfinite(corr) else 0.0)

            # Return average correlation across channels
            mean_corr = float(np.mean(correlations))
            return mean_corr if np.isfinite(mean_corr) else 0.0

        except Exception as e:
            logger.warning(f"Histogram comparison failed: {str(e)}")
            return 0.0

    def _determine_verdict(
        self, phash_match: bool, phash_distance: int, ssim_score: float, hist_corr: float
    ) -> Tuple[str, float]:
        """
        Determine verdict based on all three comparison methods

        Args:
            phash_match: Whether pHash matched
            phash_distance: pHash Hamming distance
            ssim_score: SSIM score
            hist_corr: Histogram correlation

        Returns:
            (verdict: str, confidence: float)
        """
        # All three methods should indicate linkage
        matches = 0

        if phash_match:
            matches += 1

        if ssim_score >= self.ssim_threshold:
            matches += 1

        if hist_corr >= self.histogram_threshold:
            matches += 1

        # Calculate confidence based on matches
        if matches >= 3:
            # All methods agree - strong linkage
            verdict = "PASS"
            confidence = min(ssim_score, hist_corr)  # Use lower of the two scores
        elif matches >= 2:
            # Two methods agree - probable linkage
            verdict = "PASS"
            confidence = (ssim_score + hist_corr) / 2
        elif matches == 1:
            # Only one method agrees - suspicious
            verdict = "SUSPICIOUS"
            confidence = max(ssim_score, hist_corr) * 0.5
        else:
            # No methods agree - reject
            verdict = "REJECT"
            confidence = 0.0

        # A catastrophic pHash failure means the images depict different scenes —
        # global color/structure similarity (SSIM, histograms) must not outvote it.
        if phash_distance > self.phash_catastrophic and verdict == "PASS":
            verdict = "SUSPICIOUS"
            confidence = min(confidence, 0.4)

        return verdict, confidence

    def _generate_analysis_summary(self, verdict: str, phash_distance: int, ssim_score: float, hist_corr: float) -> str:
        """Generate human-readable analysis summary"""
        if verdict == "REJECT":
            return f"RAW-JPG linkage FAILED: Files are not linked (pHash dist={phash_distance}, SSIM={ssim_score:.2f}, Hist={hist_corr:.2f})"
        elif verdict == "SUSPICIOUS":
            return f"RAW-JPG linkage SUSPICIOUS: Weak correlation detected (pHash dist={phash_distance}, SSIM={ssim_score:.2f}, Hist={hist_corr:.2f})"
        else:
            return f"RAW-JPG linkage verified: Files are linked (pHash dist={phash_distance}, SSIM={ssim_score:.2f}, Hist={hist_corr:.2f})"
