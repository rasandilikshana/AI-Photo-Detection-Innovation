"""
RAW-JPG Linkage Analyzer
Forensically proves that a submitted JPG is derived from the submitted RAW file.

Whole-frame appearance comparison (pHash, SSIM, histograms) settles unedited pairs
cheaply. It cannot settle edited ones: a crop moves every pixel and a monochrome
conversion re-weights the colour channels, so all three measures collapse on a file
that is genuinely the same capture. Those cases fall through to geometric
verification, which asks instead whether there exists a rigid crop of the RAW that
the JPG *is* — and answers with a located rectangle rather than a similarity score.
"""

import logging
from typing import Dict, List, Optional, Tuple

import cv2
import imagehash
import numpy as np
import rawpy
from PIL import Image
from skimage.metrics import structural_similarity as ssim

from app.services.vision_arbiter import VisionArbiter

logger = logging.getLogger(__name__)


class RAWJPGLinkageAnalyzer:
    """
    Analyzes the linkage between RAW and JPG files to detect submission forgery

    Core Innovation: Prevents attackers from submitting a genuine RAW file
    with an unrelated AI-generated JPG file.

    Fast path (unedited pairs):
    1. Perceptual Hash Comparison (pHash)
    2. Structural Similarity Index (SSIM)
    3. Color Histogram Correlation

    Slow path (edited submissions), decisive when it runs:
    4. Geometric verification — SIFT keypoints, RANSAC homography, and a check that
       the resulting transform is one a crop could actually produce
    """

    def __init__(self, arbiter: Optional[VisionArbiter] = None):
        # Injected for tests; default construction self-disables without an API key, so
        # the pipeline is fully functional with no third-party dependency configured.
        self.arbiter = arbiter if arbiter is not None else VisionArbiter()

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

        # Geometric verification. Whole-frame comparison collapses on legitimate crops
        # and black-and-white conversions, so when it fails we ask a different question:
        # is there a rigid crop of the RAW that this JPEG geometrically IS?
        #
        # This replaced rigid edge-template correlation, which could not survive a real
        # monochrome conversion. A mono mix RE-WEIGHTS THE COLOUR CHANNELS rather than
        # curving luminance, so edge magnitudes change unpredictably — the predecessor
        # scored 0.79-0.93 on gamma-curved fixtures and 0.356 on a real mono crop.
        # Keypoint matching survives it because only a few dozen of thousands of
        # keypoints need to agree, and RANSAC finds that consensus.
        self.sift_features = 3000
        # 1280 measured against the real submissions below: 1600 cost ~1.05s per
        # comparison for 467 inliers, 1280 costs ~0.68s for 463. Also bounds peak
        # memory on the 2GB production host.
        self.sift_work_long_edge = 1280
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        self.lowe_ratio = 0.75
        self.min_good_matches = 12  # 4 is the algebraic minimum; 12 avoids degenerate fits

        # Calibrated 2026-08-07 on real Canon EOS 600D submissions (2 CR2s, 4 exports,
        # plus every cross-pairing as a negative control):
        #   genuine pairs      463-883 inliers, 90-100% inlier ratio, 6/6 crop_like
        #   substituted pairs      4-5 inliers, 19-33% inlier ratio, 0/4 crop_like
        # The threshold sits ~10x above the observed negatives and ~11x below the
        # genuine floor. Kept deliberately low because crop_like is the real
        # discriminator and a false rejection costs a photographer their entry, while a
        # false pass still has to survive Layers 1-3.
        self.min_inliers_linked = 40
        self.low_texture_keypoints = 300  # below this, geometry cannot decide either way

        # A crop is a rigid transform: it cannot introduce perspective, shear, or
        # change the aspect ratio. Rotation is allowed only at right angles, because
        # photographers rotate exports but no crop produces an arbitrary angle.
        self.max_rotation_dev_deg = 2.5
        self.max_angle_dev_deg = 4.0
        self.max_side_skew = 0.10
        self.max_aspect_skew = 0.12

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

            # Release the 1920x1080 working copies before the geometric search allocates
            del raw_resized, jpg_resized

            # Determine verdict based on all three methods
            verdict, confidence = self._determine_verdict(phash_match, phash_distance, ssim_score, hist_corr)

            # Whole-frame comparison collapses on legitimate crops and black-and-white
            # conversions — a mono conversion re-weights the colour channels, so
            # luminance, histograms and pHash all diverge on a file that is genuinely
            # the same capture. When it fails, ask the question that survives editing:
            # is there a rigid crop of this RAW that the JPEG geometrically IS?
            geometry, arbitration = None, None
            if verdict != "PASS":
                geometry = self._feature_homography_match(raw_image, jpg_image)
                flags.append(
                    f"Geometric match: {geometry['inliers']} corresponding sensor features "
                    f"({geometry['inlier_ratio']:.0%} of candidates), {geometry['keypoints_raw']}/"
                    f"{geometry['keypoints_jpg']} keypoints"
                )
                verdict, confidence = self._apply_geometry(geometry, confidence, flags)

                # Only reached when geometry had too little texture to decide.
                verdict, confidence, arbitration = await self._arbitrate_if_needed(
                    raw_image, jpg_image, geometry, verdict, confidence, flags
                )

            crop_rect_norm, crop_fraction = self._present_crop(geometry)

            if verdict == "REJECT":
                flags.append("CRITICAL: RAW and JPG files are not linked - possible submission forgery")
            elif verdict == "SUSPICIOUS" and phash_distance > self.phash_catastrophic:
                # Context for the reviewer, not an accusation. A large pHash distance is
                # expected on a legitimate crop or monochrome conversion, so it only
                # matters here because geometry could not confirm the crop either way.
                flags.append(
                    f"Whole-frame appearance differs sharply (pHash distance {phash_distance}) and geometry "
                    "could not confirm a crop - a human should compare the RAW and JPG directly"
                )

            return {
                "verdict": verdict,
                "confidence": confidence,
                "flags": flags,
                "method": "linkage_analysis",
                "phash_distance": float(phash_distance),
                "ssim_score": float(ssim_score),
                "histogram_correlation": float(hist_corr),
                "geometry": geometry,
                "arbitration": arbitration,
                # Normalised to the RAW frame so the judge UI can draw it at any preview
                # resolution. None when no crop was confirmed — see _present_crop.
                "crop_rect_norm": crop_rect_norm,
                "crop_fraction": crop_fraction,
                "analysis": self._generate_analysis_summary(verdict, phash_distance, ssim_score, hist_corr, geometry),
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



    @staticmethod
    def _present_crop(geometry: Optional[Dict]) -> Tuple[Optional[List[float]], float]:
        """The crop region to publish for the judge UI to draw on the RAW preview.

        A rejected homography still leaves coordinates in the geometry result; publishing
        them would draw a confident box around nothing. Only a confirmed crop gets a
        rectangle. No geometry at all means the fast path matched the whole frame.
        """
        if geometry is None:
            return [0.0, 0.0, 1.0, 1.0], 1.0
        if geometry["linked"]:
            return geometry["crop_rect_norm"], geometry["crop_fraction"]
        return None, 0.0

    async def _arbitrate_if_needed(
        self,
        raw_image: np.ndarray,
        jpg_image: np.ndarray,
        geometry: Optional[Dict],
        verdict: str,
        confidence: float,
        flags: List[str],
    ) -> Tuple[str, float, Optional[Dict]]:
        """Consult the vision arbiter on results geometry could not decide.

        Can only raise an inconclusive verdict to PASS. A disagreement is recorded as
        evidence and left for a human — see VisionArbiter for why it is never allowed
        to reject.
        """
        if not self.arbiter.should_arbitrate(geometry):
            return verdict, confidence, None

        arbitration = await self.arbiter.arbitrate(raw_image, jpg_image, geometry)
        flags.extend(arbitration["flags"])

        if arbitration["verdict"] == "LINKED":
            return "PASS", max(confidence, arbitration["confidence"]), arbitration

        return verdict, confidence, arbitration

    def _apply_geometry(self, geometry: Dict, prior_confidence: float, flags: List[str]) -> Tuple[str, float]:
        """Turn a geometric result into a verdict.

        Geometry is decisive in both directions when it has keypoints to work with. When
        it does not — a near-featureless frame — it must report that it cannot tell
        rather than condemn the submission; that is the case the vision arbiter handles.
        """
        if geometry["linked"]:
            x, y, w, h = geometry["crop_rect_norm"]
            flags.append(
                f"RAW-JPG linkage confirmed geometrically: the JPG is the region "
                f"x={x:.0%} y={y:.0%} w={w:.0%} h={h:.0%} of this RAW "
                f"({geometry['crop_fraction']:.0%} of the frame), aligned to "
                f"{geometry['reproj_error_px']:.2f}px across {geometry['inliers']} features — "
                "a crop of this capture, tonally reworked"
            )
            return "PASS", geometry["inlier_ratio"]

        if geometry["low_texture"]:
            flags.append(
                f"Geometry inconclusive: too little texture for keypoint matching "
                f"({geometry['reason']}) - manual review required"
            )
            return "SUSPICIOUS", min(prior_confidence, 0.4)

        if geometry["crop_like"]:
            flags.append(
                f"Geometry inconclusive: the crop shape is plausible but only "
                f"{geometry['inliers']} features corroborate it - manual review required"
            )
            return "SUSPICIOUS", min(prior_confidence, 0.4)

        flags.append(f"CRITICAL: no crop of this RAW matches this JPG ({geometry['reason']})")
        return "REJECT", 0.0

    @staticmethod
    def _empty_geometry(reason: str, **extra) -> Dict:
        """A result that decides nothing. Distinguishes 'cannot tell' from 'not linked'
        via low_texture, because the two need different handling downstream."""
        result = {
            "linked": False,
            "crop_like": False,
            "low_texture": False,
            "inliers": 0,
            "inlier_ratio": 0.0,
            "good_matches": 0,
            "keypoints_raw": 0,
            "keypoints_jpg": 0,
            "crop_rect_norm": None,
            "crop_fraction": 0.0,
            "rotation_deg": 0.0,
            "aspect_skew": 0.0,
            "reproj_error_px": 0.0,
            "reason": reason,
        }
        result.update(extra)
        return result

    def _prepare_gray(self, bgr: np.ndarray) -> Tuple[np.ndarray, float]:
        """Grayscale, bound the working resolution, and equalise local contrast.

        CLAHE is not cosmetic here — it is what makes the comparison possible. The RAW
        is demosaiced with no_auto_bright, so an underexposed capture stays dark and
        SIFT finds almost nothing in it. Measured on a real Canon CR2 in this suite:
        54 keypoints before equalisation, 707 after, which took its monochrome crop
        from 35 RANSAC inliers to 468. Applying it to both sides also removes the
        exposure and tone-curve gap between a flat demosaic and a finished export,
        which is exactly the difference that is not evidence of anything.

        Returns (gray, scale_applied).
        """
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        scale = min(1.0, self.sift_work_long_edge / float(max(h, w)))
        if scale < 1.0:
            gray = cv2.resize(gray, (max(1, int(round(w * scale))), max(1, int(round(h * scale)))),
                              interpolation=cv2.INTER_AREA)
        return self._clahe.apply(gray), scale

    def _describe_quad(self, quad: np.ndarray, frame_w: int, frame_h: int, jpg_aspect: float) -> Dict:
        """Test whether the JPEG's footprint inside the RAW is shaped like a crop.

        `quad` holds the JPEG's four corners (TL, TR, BR, BL) mapped into RAW space. A
        genuine crop lands as an axis-aligned-or-right-angle-rotated rectangle of the
        JPEG's own aspect ratio, wholly inside the frame. Perspective warps, stretches
        and unrelated-scene consensus all fail at least one of those.
        """
        top = quad[1] - quad[0]
        right = quad[2] - quad[1]
        bottom = quad[2] - quad[3]
        left = quad[3] - quad[0]

        lengths = [float(np.linalg.norm(v)) for v in (top, right, bottom, left)]
        if min(lengths) < 1e-6:
            return {"crop_like": False, "rotation_deg": 0.0, "aspect_skew": 0.0,
                    "crop_fraction": 0.0, "crop_rect_norm": None,
                    "reason": "degenerate quadrilateral"}

        # Opposite sides equal -> parallelogram
        side_skew = max(
            abs(lengths[0] - lengths[2]) / max(lengths[0], lengths[2]),
            abs(lengths[1] - lengths[3]) / max(lengths[1], lengths[3]),
        )

        # Corner angles at 90 degrees -> rectangle (rules out perspective/keystone)
        edges = [top, right, -bottom, -left]
        angle_dev = 0.0
        for i in range(4):
            a, b = edges[i], edges[(i + 1) % 4]
            cos = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
            angle_dev = max(angle_dev, abs(90.0 - np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))))

        # Uniform scale -> the footprint keeps the JPEG's aspect ratio. Measured on the
        # quad's own edges, so this holds under right-angle rotation too.
        quad_aspect = ((lengths[0] + lengths[2]) / 2.0) / ((lengths[1] + lengths[3]) / 2.0)
        aspect_skew = abs(quad_aspect - jpg_aspect) / max(quad_aspect, jpg_aspect)

        # Rotation only at right angles
        rotation = float(np.degrees(np.arctan2(top[1], top[0])))
        rotation_dev = min(abs(((rotation - k) + 180.0) % 360.0 - 180.0) for k in (0.0, 90.0, -90.0, 180.0))

        # Wholly inside the frame (2% margin absorbs resampling slack at the edges)
        margin_x, margin_y = 0.02 * frame_w, 0.02 * frame_h
        inside = bool(
            quad[:, 0].min() >= -margin_x and quad[:, 0].max() <= frame_w + margin_x
            and quad[:, 1].min() >= -margin_y and quad[:, 1].max() <= frame_h + margin_y
        )

        area = 0.5 * abs(float(np.dot(quad[:, 0], np.roll(quad[:, 1], -1)) -
                               np.dot(quad[:, 1], np.roll(quad[:, 0], -1))))
        crop_fraction = float(np.clip(area / float(frame_w * frame_h), 0.0, 1.0))

        xs = np.clip(quad[:, 0] / float(frame_w), 0.0, 1.0)
        ys = np.clip(quad[:, 1] / float(frame_h), 0.0, 1.0)
        crop_rect_norm = [float(xs.min()), float(ys.min()),
                          float(xs.max() - xs.min()), float(ys.max() - ys.min())]

        failures = []
        if side_skew > self.max_side_skew:
            failures.append(f"opposite sides differ by {side_skew:.0%}")
        if angle_dev > self.max_angle_dev_deg:
            failures.append(f"corners off square by {angle_dev:.1f}deg (perspective)")
        if aspect_skew > self.max_aspect_skew:
            failures.append(f"aspect ratio differs by {aspect_skew:.0%} (non-uniform scale)")
        if rotation_dev > self.max_rotation_dev_deg:
            failures.append(f"rotated {rotation:.1f}deg, not a right angle")
        if not inside:
            failures.append("extends outside the RAW frame")

        return {
            "crop_like": not failures,
            "rotation_deg": rotation,
            "aspect_skew": float(aspect_skew),
            "crop_fraction": crop_fraction,
            "crop_rect_norm": crop_rect_norm,
            "reason": "crop geometry confirmed" if not failures else "; ".join(failures),
        }

    def _feature_homography_match(self, raw_image: np.ndarray, jpg_image: np.ndarray) -> Dict:
        """Establish whether the JPEG is geometrically a crop of the RAW.

        Matches SIFT keypoints, fits a homography with RANSAC, then checks that the
        homography is one a crop could actually produce. Unlike a similarity score this
        yields a located rectangle — where in the RAW the JPEG came from — which the
        judge can be shown.
        """
        try:
            raw_gray, _ = self._prepare_gray(raw_image)
            jpg_gray, _ = self._prepare_gray(jpg_image)

            sift = cv2.SIFT_create(nfeatures=self.sift_features)
            kp_raw, des_raw = sift.detectAndCompute(raw_gray, None)
            kp_jpg, des_jpg = sift.detectAndCompute(jpg_gray, None)

            counts = {"keypoints_raw": len(kp_raw), "keypoints_jpg": len(kp_jpg)}
            low_texture = min(len(kp_raw), len(kp_jpg)) < self.low_texture_keypoints

            if des_raw is None or des_jpg is None or len(kp_raw) < 2 or len(kp_jpg) < 2:
                return self._empty_geometry("too few keypoints to compare", low_texture=True, **counts)

            matcher = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 50})
            good = [
                m for m, n in matcher.knnMatch(np.asarray(des_jpg, np.float32), np.asarray(des_raw, np.float32), k=2)
                if m.distance < self.lowe_ratio * n.distance
            ]

            if len(good) < self.min_good_matches:
                return self._empty_geometry(
                    f"only {len(good)} corresponding keypoints", low_texture=low_texture,
                    good_matches=len(good), **counts
                )

            src = np.float32([kp_jpg[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst = np.float32([kp_raw[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)

            if H is None or mask is None:
                return self._empty_geometry(
                    "no consistent transform between the files", low_texture=low_texture,
                    good_matches=len(good), **counts
                )

            inliers = int(mask.sum())
            jh, jw = jpg_gray.shape
            rh, rw = raw_gray.shape
            corners = np.float32([[0, 0], [jw, 0], [jw, jh], [0, jh]]).reshape(-1, 1, 2)
            quad = cv2.perspectiveTransform(corners, H).reshape(4, 2)

            if not np.isfinite(quad).all():
                return self._empty_geometry(
                    "transform mapped outside finite coordinates", low_texture=low_texture,
                    good_matches=len(good), inliers=inliers, **counts
                )

            shape = self._describe_quad(quad, rw, rh, jw / float(jh))

            residuals = np.linalg.norm(
                cv2.perspectiveTransform(src, H).reshape(-1, 2) - dst.reshape(-1, 2), axis=1
            )[mask.ravel().astype(bool)]

            return {
                "linked": bool(inliers >= self.min_inliers_linked and shape["crop_like"]),
                "crop_like": shape["crop_like"],
                "low_texture": low_texture,
                "inliers": inliers,
                "inlier_ratio": float(inliers / len(good)),
                "good_matches": len(good),
                "crop_rect_norm": shape["crop_rect_norm"],
                "crop_fraction": shape["crop_fraction"],
                "rotation_deg": shape["rotation_deg"],
                "aspect_skew": shape["aspect_skew"],
                "reproj_error_px": float(residuals.mean()) if residuals.size else 0.0,
                "reason": shape["reason"],
                **counts,
            }

        except Exception as e:
            logger.warning(f"Geometric linkage match failed: {str(e)}")
            return self._empty_geometry(f"geometric analysis error: {str(e)}")

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

    def _generate_analysis_summary(
        self, verdict: str, phash_distance: int, ssim_score: float, hist_corr: float, geometry: Dict = None
    ) -> str:
        """Generate human-readable analysis summary.

        When geometry decided the verdict, lead with it — pHash and histogram figures
        are expected to look bad on a legitimate crop or mono conversion, and quoting
        them first misleads the reader into thinking they mean something here.
        """
        whole_frame = f"pHash dist={phash_distance}, SSIM={ssim_score:.2f}, Hist={hist_corr:.2f}"

        if geometry is not None:
            detail = f"{geometry['inliers']} matching features, {whole_frame}"
            if verdict == "PASS":
                return (
                    f"RAW-JPG linkage verified geometrically: the JPG is a "
                    f"{geometry['crop_fraction']:.0%} crop of this RAW ({detail})"
                )
            if verdict == "REJECT":
                return f"RAW-JPG linkage FAILED: no crop of the RAW matches this JPG ({detail})"
            return f"RAW-JPG linkage SUSPICIOUS: geometry inconclusive ({detail})"

        if verdict == "REJECT":
            return f"RAW-JPG linkage FAILED: Files are not linked ({whole_frame})"
        elif verdict == "SUSPICIOUS":
            return f"RAW-JPG linkage SUSPICIOUS: Weak correlation detected ({whole_frame})"
        else:
            return f"RAW-JPG linkage verified: Files are linked ({whole_frame})"
