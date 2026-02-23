"""
Enhanced PRNU Extraction Service

Extracts, stores, and compares Photo Response Non-Uniformity (PRNU) fingerprints
from camera sensor data for building camera reputation profiles.

Based on wavelet denoising method using Discrete Wavelet Transform (DWT).
"""

import hashlib
import logging
import zlib
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
import pywt

logger = logging.getLogger(__name__)


class PRNUExtractor:
    """
    Extracts PRNU fingerprints from images for camera identification.

    PRNU (Photo Response Non-Uniformity) is a unique noise pattern created by
    manufacturing imperfections in camera sensors. Each camera has a unique PRNU
    pattern that acts as its "fingerprint".
    """

    def __init__(self):
        # Wavelet type for decomposition (Daubechies 8)
        self.wavelet = "db8"

        # Target size for PRNU extraction (balance between accuracy and storage)
        self.target_size = (512, 512)

        # Minimum PRNU energy threshold for validity
        self.min_energy_threshold = 0.00001

        # Compression level for storage (1-9, higher = more compression)
        self.compression_level = 6

    async def extract_prnu_fingerprint(
        self,
        image_path: str,
        camera_make: Optional[str] = None,
        camera_model: Optional[str] = None
    ) -> Dict:
        """
        Extract PRNU fingerprint from an image.

        Args:
            image_path: Path to the image file
            camera_make: Camera manufacturer (optional, for metadata)
            camera_model: Camera model (optional, for metadata)

        Returns:
            Dictionary containing:
            - pattern: PRNU noise pattern (2D numpy array)
            - energy: PRNU energy metric (variance)
            - hash: SHA256 hash of the pattern
            - signature: Compressed binary representation
            - valid: Whether the pattern is valid
            - metadata: Additional extraction metadata
        """
        try:
            logger.info(f"Extracting PRNU fingerprint from: {image_path}")

            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")

            # Convert to grayscale for noise analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

            # Resize to target size for consistency and efficiency
            if gray.shape[0] > self.target_size[0] or gray.shape[1] > self.target_size[1]:
                gray = cv2.resize(gray, self.target_size)

            # Normalize to [0, 1] float range
            img_float = gray.astype(np.float32) / 255.0

            # Extract PRNU pattern using wavelet denoising
            prnu_pattern, denoised_image = self._extract_prnu_pattern(img_float)

            # Calculate PRNU metrics
            prnu_energy = np.var(prnu_pattern)
            prnu_mean = np.mean(np.abs(prnu_pattern))
            prnu_std = np.std(prnu_pattern)

            # Validate pattern
            is_valid = prnu_energy >= self.min_energy_threshold

            # Compress pattern for storage
            compressed_signature = self._compress_pattern(prnu_pattern)

            # Generate hash for deduplication
            pattern_hash = self._hash_pattern(prnu_pattern)

            # Build result
            result = {
                "pattern": prnu_pattern,
                "energy": float(prnu_energy),
                "hash": pattern_hash,
                "signature": compressed_signature,
                "valid": is_valid,
                "metadata": {
                    "image_path": image_path,
                    "original_size": f"{gray.shape[0]}x{gray.shape[1]}",
                    "pattern_size": f"{prnu_pattern.shape[0]}x{prnu_pattern.shape[1]}",
                    "energy": float(prnu_energy),
                    "mean": float(prnu_mean),
                    "std_dev": float(prnu_std),
                    "camera_make": camera_make,
                    "camera_model": camera_model,
                    "wavelet_type": self.wavelet,
                }
            }

            logger.info(
                f"PRNU extraction complete: energy={prnu_energy:.6f}, "
                f"valid={is_valid}, hash={pattern_hash[:16]}..."
            )

            return result

        except Exception as e:
            logger.error(f"PRNU extraction failed: {str(e)}", exc_info=True)
            raise

    def _extract_prnu_pattern(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract PRNU noise pattern using wavelet denoising.

        Process:
        1. Apply 2D Discrete Wavelet Transform (DWT)
        2. Denoise wavelet coefficients using soft thresholding
        3. Reconstruct denoised image
        4. Extract residual noise (PRNU) = original - denoised

        Args:
            image: Normalized grayscale image [0, 1]

        Returns:
            Tuple of (prnu_pattern, denoised_image)
        """
        # Apply 2D Discrete Wavelet Transform
        coeffs = pywt.dwt2(image, self.wavelet)
        cA, (cH, cV, cD) = coeffs  # Approximation and Details

        # Estimate noise level using MAD (Median Absolute Deviation)
        sigma = self._estimate_noise_mad(cD)

        # Calculate soft threshold using universal threshold formula
        threshold = sigma * np.sqrt(2 * np.log(image.size))

        # Apply soft thresholding to detail coefficients
        cH_denoised = pywt.threshold(cH, threshold, mode="soft")
        cV_denoised = pywt.threshold(cV, threshold, mode="soft")
        cD_denoised = pywt.threshold(cD, threshold, mode="soft")

        # Reconstruct denoised image
        denoised_coeffs = (cA, (cH_denoised, cV_denoised, cD_denoised))
        denoised = pywt.idwt2(denoised_coeffs, self.wavelet)

        # Handle size mismatch after reconstruction
        if denoised.shape != image.shape:
            denoised = cv2.resize(denoised, (image.shape[1], image.shape[0]))

        # Extract PRNU residual (sensor noise)
        prnu_pattern = image - denoised

        return prnu_pattern, denoised

    def _estimate_noise_mad(self, coeffs: np.ndarray) -> float:
        """
        Estimate noise level using Median Absolute Deviation (MAD).

        MAD is robust to outliers and works well for noise estimation.

        Args:
            coeffs: Wavelet detail coefficients

        Returns:
            Estimated noise standard deviation
        """
        mad = np.median(np.abs(coeffs))
        sigma = mad / 0.6745  # Convert MAD to standard deviation
        return sigma

    def _compress_pattern(self, pattern: np.ndarray) -> bytes:
        """
        Compress PRNU pattern for efficient database storage.

        Uses zlib compression on the quantized pattern bytes.

        Args:
            pattern: PRNU noise pattern

        Returns:
            Compressed binary data
        """
        # Quantize to 16-bit signed integers (-32768 to 32767)
        # Most PRNU values are small, so this preserves precision
        quantized = (pattern * 32767).astype(np.int16)

        # Convert to bytes
        pattern_bytes = quantized.tobytes()

        # Compress using zlib
        compressed = zlib.compress(pattern_bytes, level=self.compression_level)

        return compressed

    def decompress_pattern(self, compressed_data: bytes, shape: Tuple[int, int]) -> np.ndarray:
        """
        Decompress stored PRNU pattern.

        Args:
            compressed_data: Compressed binary data
            shape: Original pattern shape (height, width)

        Returns:
            Decompressed PRNU pattern
        """
        # Decompress
        pattern_bytes = zlib.decompress(compressed_data)

        # Convert back to numpy array
        quantized = np.frombuffer(pattern_bytes, dtype=np.int16).reshape(shape)

        # Dequantize to float
        pattern = quantized.astype(np.float32) / 32767.0

        return pattern

    def _hash_pattern(self, pattern: np.ndarray) -> str:
        """
        Generate SHA256 hash of PRNU pattern for deduplication.

        Args:
            pattern: PRNU noise pattern

        Returns:
            64-character hex hash string
        """
        # Quantize for consistent hashing
        quantized = (pattern * 32767).astype(np.int16)

        # Generate SHA256 hash
        pattern_bytes = quantized.tobytes()
        hash_obj = hashlib.sha256(pattern_bytes)

        return hash_obj.hexdigest()

    async def compare_patterns(
        self,
        pattern1: np.ndarray,
        pattern2: np.ndarray
    ) -> Dict:
        """
        Compare two PRNU patterns for similarity.

        Uses multiple metrics:
        - Correlation coefficient (primary metric)
        - Normalized cross-correlation (NCC)
        - Euclidean distance (normalized)

        Args:
            pattern1: First PRNU pattern
            pattern2: Second PRNU pattern

        Returns:
            Dictionary with similarity metrics
        """
        try:
            # Ensure patterns are same size
            if pattern1.shape != pattern2.shape:
                pattern2 = cv2.resize(pattern2, (pattern1.shape[1], pattern1.shape[0]))

            # Flatten patterns for correlation
            p1_flat = pattern1.flatten()
            p2_flat = pattern2.flatten()

            # Calculate correlation coefficient (range: -1 to 1)
            correlation = np.corrcoef(p1_flat, p2_flat)[0, 1]

            # Calculate normalized cross-correlation (NCC)
            ncc = np.sum(p1_flat * p2_flat) / (np.linalg.norm(p1_flat) * np.linalg.norm(p2_flat))

            # Calculate normalized Euclidean distance
            euclidean_dist = np.linalg.norm(p1_flat - p2_flat)
            max_dist = np.sqrt(2)  # Maximum possible distance for normalized patterns
            normalized_distance = euclidean_dist / max_dist

            # Convert distance to similarity (0 = different, 1 = identical)
            distance_similarity = 1.0 - normalized_distance

            # Combined similarity score (weighted average)
            # Correlation is most important, then NCC, then distance
            similarity_score = (
                0.5 * (correlation + 1) / 2 +  # Convert [-1,1] to [0,1]
                0.3 * (ncc + 1) / 2 +           # Convert [-1,1] to [0,1]
                0.2 * distance_similarity
            )

            return {
                "similarity_score": float(similarity_score),
                "correlation": float(correlation),
                "ncc": float(ncc),
                "euclidean_distance": float(euclidean_dist),
                "normalized_distance": float(normalized_distance),
                "distance_metric": "euclidean",
                "same_camera_likely": similarity_score > 0.70,  # 70% threshold
            }

        except Exception as e:
            logger.error(f"Pattern comparison failed: {str(e)}")
            return {
                "similarity_score": 0.0,
                "error": str(e)
            }

    def estimate_quality(self, prnu_pattern: np.ndarray) -> Dict:
        """
        Estimate the quality of a PRNU fingerprint.

        Higher quality fingerprints provide more reliable identification.

        Args:
            prnu_pattern: PRNU noise pattern

        Returns:
            Dictionary with quality metrics
        """
        energy = np.var(prnu_pattern)
        snr = self._calculate_snr(prnu_pattern)
        spatial_correlation = self._spatial_autocorrelation(prnu_pattern)

        # Quality score (0-1, higher is better)
        quality_score = min(1.0, energy * 10000)  # Scale energy to [0,1]
        quality_score *= (1 - spatial_correlation)  # Penalize high correlation (not noise-like)

        quality_level = "excellent" if quality_score > 0.7 else \
                       "good" if quality_score > 0.5 else \
                       "fair" if quality_score > 0.3 else "poor"

        return {
            "quality_score": float(quality_score),
            "quality_level": quality_level,
            "energy": float(energy),
            "snr": float(snr),
            "spatial_correlation": float(spatial_correlation),
        }

    def _calculate_snr(self, pattern: np.ndarray) -> float:
        """Calculate Signal-to-Noise Ratio"""
        signal_power = np.mean(pattern ** 2)
        noise_power = np.var(pattern)

        if noise_power == 0:
            return 0.0

        snr = 10 * np.log10(signal_power / noise_power)
        return snr

    def _spatial_autocorrelation(self, pattern: np.ndarray, lag: int = 1) -> float:
        """
        Calculate spatial autocorrelation (should be low for good noise).

        True noise should be uncorrelated spatially.
        """
        # Shift pattern and calculate correlation
        shifted = np.roll(pattern, lag, axis=0)
        correlation = np.corrcoef(pattern.flatten(), shifted.flatten())[0, 1]

        return abs(correlation)
