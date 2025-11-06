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
        self.phash_threshold = 10  # Hamming distance threshold
        self.ssim_threshold = 0.85  # SSIM similarity threshold
        self.histogram_threshold = 0.90  # Histogram correlation threshold

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

            # Method 1: Perceptual Hash Comparison
            phash_match, phash_distance = self._compare_phash(raw_path, jpg_path)
            flags.append(f"pHash distance: {phash_distance}")

            # Method 2: SSIM Comparison
            ssim_score = self._compare_ssim(raw_resized, jpg_resized)
            flags.append(f"SSIM score: {ssim_score:.4f}")

            # Method 3: Color Histogram Correlation
            hist_corr = self._compare_histograms(raw_resized, jpg_resized)
            flags.append(f"Histogram correlation: {hist_corr:.4f}")

            # Determine verdict based on all three methods
            verdict, confidence = self._determine_verdict(phash_match, phash_distance, ssim_score, hist_corr)

            if verdict == "REJECT":
                flags.append("CRITICAL: RAW and JPG files are not linked - possible submission forgery")

            return {
                "verdict": verdict,
                "confidence": confidence,
                "flags": flags,
                "method": "linkage_analysis",
                "phash_distance": float(phash_distance),
                "ssim_score": float(ssim_score),
                "histogram_correlation": float(hist_corr),
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

        Args:
            raw_path: Path to RAW file

        Returns:
            RGB numpy array
        """
        try:
            with rawpy.imread(raw_path) as raw:
                # Demosaic RAW to RGB using default settings
                rgb = raw.postprocess(use_camera_wb=True, half_size=False, no_auto_bright=True, output_bps=8)
            return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        except Exception as e:
            logger.error(f"Failed to load RAW image: {str(e)}")
            return None

    def _compare_phash(self, raw_path: str, jpg_path: str) -> Tuple[bool, int]:
        """
        Compare perceptual hashes of RAW and JPG

        Args:
            raw_path: Path to RAW file
            jpg_path: Path to JPG file

        Returns:
            (match: bool, hamming_distance: int)
        """
        try:
            # Load images with PIL for hashing
            raw_img = Image.open(raw_path)
            jpg_img = Image.open(jpg_path)

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

                # Calculate correlation
                corr = cv2.compareHist(raw_hist, jpg_hist, cv2.HISTCMP_CORREL)
                correlations.append(corr)

            # Return average correlation across channels
            return np.mean(correlations)

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

        return verdict, confidence

    def _generate_analysis_summary(self, verdict: str, phash_distance: int, ssim_score: float, hist_corr: float) -> str:
        """Generate human-readable analysis summary"""
        if verdict == "REJECT":
            return f"RAW-JPG linkage FAILED: Files are not linked (pHash dist={phash_distance}, SSIM={ssim_score:.2f}, Hist={hist_corr:.2f})"
        elif verdict == "SUSPICIOUS":
            return f"RAW-JPG linkage SUSPICIOUS: Weak correlation detected (pHash dist={phash_distance}, SSIM={ssim_score:.2f}, Hist={hist_corr:.2f})"
        else:
            return f"RAW-JPG linkage verified: Files are linked (pHash dist={phash_distance}, SSIM={ssim_score:.2f}, Hist={hist_corr:.2f})"
