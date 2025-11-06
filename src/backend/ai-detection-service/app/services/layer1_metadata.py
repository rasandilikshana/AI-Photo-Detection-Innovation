"""
Layer 1: Metadata Analysis Service
Forensic EXIF analysis to detect AI-generated images through metadata signatures
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image
from PIL.ExifTags import TAGS

logger = logging.getLogger(__name__)


class MetadataAnalyzer:
    """
    Analyzes EXIF metadata to identify AI-generated images

    Detection Strategy:
    - AI Signatures: Flag known AI tool tags (Midjourney, DALL-E, Stable Diffusion)
    - Camera Signatures: Validate presence of genuine camera metadata
    - Inconsistency Detection: Identify hollow or contradictory metadata
    """

    # Known AI generation tool signatures
    AI_SIGNATURES = [
        "midjourney",
        "dall-e",
        "dall·e",
        "stable diffusion",
        "stablediffusion",
        "ai generated",
        "synthetic",
        "artificial intelligence",
        "generative",
        "openai",
        "midjourney bot",
        "ai-generated",
        "adobe firefly",
        "firefly",
        "leonardo.ai",
        "playground ai",
        "craiyon",
        "nightcafe",
    ]

    # Essential camera metadata fields
    CAMERA_FIELDS = {
        "Make": "Camera manufacturer",
        "Model": "Camera model",
        "LensModel": "Lens model",
        "ExposureTime": "Shutter speed",
        "FNumber": "Aperture",
        "ISO": "ISO speed",
        "FocalLength": "Focal length",
        "DateTimeOriginal": "Original capture date",
    }

    # Critical fields that should exist together
    CONSISTENCY_GROUPS = [["Make", "Model"], ["ExposureTime", "FNumber", "ISO"], ["FocalLength", "LensModel"]]

    def __init__(self):
        self.exiftool_available = self._check_exiftool()

    def _check_exiftool(self) -> bool:
        """Check if exiftool is available in system"""
        try:
            result = subprocess.run(["exiftool", "-ver"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("exiftool not available, falling back to PIL only")
            return False

    async def analyze(self, jpg_path: str, raw_path: Optional[str] = None) -> Dict:
        """
        Perform comprehensive metadata analysis

        Args:
            jpg_path: Path to JPG file
            raw_path: Optional path to RAW file

        Returns:
            Analysis result with verdict and confidence score
        """
        try:
            # Extract metadata from JPG
            jpg_metadata = self._extract_metadata_pil(jpg_path)

            # Try exiftool for more comprehensive data if available
            if self.exiftool_available:
                jpg_metadata_extended = self._extract_metadata_exiftool(jpg_path)
                jpg_metadata.update(jpg_metadata_extended)

            # Extract RAW metadata if provided
            raw_metadata = None
            if raw_path:
                raw_metadata = self._extract_metadata_exiftool(raw_path) if self.exiftool_available else {}

            # Perform analysis
            flags = []
            confidence_score = 1.0
            verdict = "AUTHENTIC"

            # Check 1: AI Signature Detection
            ai_detected, ai_flags = self._detect_ai_signatures(jpg_metadata)
            if ai_detected:
                flags.extend(ai_flags)
                verdict = "REJECT"
                confidence_score = 1.0  # 100% confidence in AI detection

                return {
                    "verdict": verdict,
                    "confidence": confidence_score,
                    "flags": flags,
                    "metadata_present": bool(jpg_metadata),
                    "camera_fields_found": 0,
                    "ai_signatures_found": len(ai_flags),
                    "analysis": "AI generation signatures detected in metadata",
                }

            # Check 2: Camera Signature Validation
            camera_score, camera_flags = self._validate_camera_signatures(jpg_metadata)
            flags.extend(camera_flags)

            # Check 3: Metadata Consistency
            consistency_score, consistency_flags = self._check_metadata_consistency(jpg_metadata)
            flags.extend(consistency_flags)

            # Check 4: RAW-JPG Metadata Correlation (if RAW provided)
            if raw_metadata:
                correlation_score, correlation_flags = self._check_raw_jpg_correlation(jpg_metadata, raw_metadata)
                flags.extend(correlation_flags)
            else:
                correlation_score = 0.5  # Neutral if no RAW provided

            # Calculate overall confidence
            # Weight: Camera signatures (40%), Consistency (30%), Correlation (30%)
            if raw_metadata:
                confidence_score = camera_score * 0.4 + consistency_score * 0.3 + correlation_score * 0.3
            else:
                confidence_score = camera_score * 0.6 + consistency_score * 0.4

            # Determine verdict based on confidence
            if confidence_score < 0.3:
                verdict = "REJECT"
            elif confidence_score < 0.7:
                verdict = "SUSPICIOUS"
            else:
                verdict = "PASS"

            camera_fields_found = sum(1 for field in self.CAMERA_FIELDS if field in jpg_metadata)

            return {
                "verdict": verdict,
                "confidence": confidence_score,
                "flags": flags,
                "metadata_present": bool(jpg_metadata),
                "camera_fields_found": camera_fields_found,
                "ai_signatures_found": 0,
                "camera_score": camera_score,
                "consistency_score": consistency_score,
                "analysis": self._generate_analysis_summary(verdict, camera_fields_found, flags),
            }

        except Exception as e:
            logger.error(f"Metadata analysis failed: {str(e)}", exc_info=True)
            return {
                "verdict": "ERROR",
                "confidence": 0.0,
                "flags": [f"Analysis error: {str(e)}"],
                "metadata_present": False,
                "camera_fields_found": 0,
                "ai_signatures_found": 0,
                "analysis": "Metadata analysis failed",
            }

    def _extract_metadata_pil(self, image_path: str) -> Dict:
        """Extract EXIF metadata using PIL"""
        try:
            image = Image.open(image_path)
            exifdata = image.getexif()

            metadata = {}
            if exifdata:
                for tag_id, value in exifdata.items():
                    tag = TAGS.get(tag_id, tag_id)
                    metadata[tag] = str(value)

            return metadata

        except Exception as e:
            logger.warning(f"PIL metadata extraction failed: {str(e)}")
            return {}

    def _extract_metadata_exiftool(self, file_path: str) -> Dict:
        """Extract comprehensive metadata using exiftool"""
        try:
            result = subprocess.run(
                ["exiftool", "-j", "-a", "-G", file_path], capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data and len(data) > 0:
                    # Flatten the nested structure
                    flattened = {}
                    for key, value in data[0].items():
                        # Remove group prefix (e.g., "EXIF:Make" -> "Make")
                        clean_key = key.split(":")[-1]
                        flattened[clean_key] = value
                    return flattened

            return {}

        except Exception as e:
            logger.warning(f"exiftool extraction failed: {str(e)}")
            return {}

    def _detect_ai_signatures(self, metadata: Dict) -> tuple[bool, List[str]]:
        """
        Detect known AI generation signatures in metadata

        Returns:
            (ai_detected: bool, flags: List[str])
        """
        flags = []

        # Check all metadata values for AI signatures
        for key, value in metadata.items():
            value_lower = str(value).lower()

            for signature in self.AI_SIGNATURES:
                if signature in value_lower:
                    flags.append(f"AI signature detected in {key}: '{signature}'")

        return len(flags) > 0, flags

    def _validate_camera_signatures(self, metadata: Dict) -> tuple[float, List[str]]:
        """
        Validate presence of genuine camera metadata

        Returns:
            (score: float, flags: List[str])
        """
        flags = []
        fields_present = 0
        total_fields = len(self.CAMERA_FIELDS)

        for field, description in self.CAMERA_FIELDS.items():
            if field in metadata and metadata[field]:
                fields_present += 1
            else:
                flags.append(f"Missing {description} ({field})")

        score = fields_present / total_fields

        if fields_present == 0:
            flags.append("No camera metadata found - metadata completely stripped")
        elif fields_present < 3:
            flags.append("Minimal camera metadata - likely stripped or synthetic")

        return score, flags

    def _check_metadata_consistency(self, metadata: Dict) -> tuple[float, List[str]]:
        """
        Check for metadata inconsistencies (hollow or contradictory data)

        Returns:
            (score: float, flags: List[str])
        """
        flags = []
        consistency_checks = 0
        passed_checks = 0

        for group in self.CONSISTENCY_GROUPS:
            consistency_checks += 1
            fields_in_group = [field for field in group if field in metadata and metadata[field]]

            # If some but not all fields in group are present, it's inconsistent
            if 0 < len(fields_in_group) < len(group):
                flags.append(f"Inconsistent metadata group: {group} (only {fields_in_group} present)")
            elif len(fields_in_group) == len(group):
                passed_checks += 1

        # Calculate consistency score
        if consistency_checks > 0:
            score = passed_checks / consistency_checks
        else:
            score = 0.5  # Neutral if no consistency checks possible

        return score, flags

    def _check_raw_jpg_correlation(self, jpg_metadata: Dict, raw_metadata: Dict) -> tuple[float, List[str]]:
        """
        Check if RAW and JPG metadata correlate (same camera/settings)

        Returns:
            (score: float, flags: List[str])
        """
        flags = []

        # Fields that should match between RAW and JPG
        matching_fields = ["Make", "Model", "LensModel", "ExposureTime", "FNumber", "ISO"]

        matches = 0
        comparisons = 0

        for field in matching_fields:
            if field in jpg_metadata and field in raw_metadata:
                comparisons += 1
                if jpg_metadata[field] == raw_metadata[field]:
                    matches += 1
                else:
                    flags.append(
                        f"RAW-JPG mismatch in {field}: RAW='{raw_metadata[field]}' vs JPG='{jpg_metadata[field]}'"
                    )

        if comparisons == 0:
            return 0.5, ["Insufficient metadata for RAW-JPG correlation"]

        score = matches / comparisons

        if score < 0.5:
            flags.append("Critical: RAW and JPG metadata do not match - possible forgery")

        return score, flags

    def _generate_analysis_summary(self, verdict: str, camera_fields_found: int, flags: List[str]) -> str:
        """Generate human-readable analysis summary"""
        if verdict == "REJECT":
            return f"Image rejected: {len(flags)} critical issues detected"
        elif verdict == "SUSPICIOUS":
            return f"Image flagged as suspicious: {camera_fields_found} camera fields found, {len(flags)} warnings"
        else:
            return f"Metadata analysis passed: {camera_fields_found} camera fields verified"
