"""
Layer 3: Third-Party API Verification Service
Integration with professional AI detection APIs for final verdict
"""

import base64
import logging
import os
from pathlib import Path
from typing import Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class ThirdPartyAPIVerifier:
    """
    Integrates with third-party AI detection APIs for final verification

    Supported APIs:
    - Hive AI (Content Moderation & AI Detection)
    - Optic AI or Image Integrity
    - Content at Scale AI Detector

    This layer is only invoked for QUARANTINE cases from Layer 2
    """

    def __init__(self):
        self.hive_api_key = os.getenv("HIVE_AI_API_KEY", "")
        self.optic_api_key = os.getenv("OPTIC_API_KEY", "")
        self.timeout = 60.0  # API timeout in seconds

        # Log API key status (without exposing the actual key)
        if self.hive_api_key:
            logger.info(f"Hive AI API key configured (length: {len(self.hive_api_key)})")
        else:
            logger.warning("Hive AI API key not configured")

    async def verify(self, image_path: str) -> Dict:
        """
        Verify image authenticity using third-party APIs

        Args:
            image_path: Path to image file

        Returns:
            Analysis result with verdict
        """
        try:
            logger.info("Starting third-party API verification")

            # Try primary API (Hive AI)
            if self.hive_api_key:
                result = await self._verify_hive_ai(image_path)
                if result["verdict"] != "ERROR":
                    return result

            # Fallback to secondary API (Optic)
            if self.optic_api_key:
                result = await self._verify_optic(image_path)
                if result["verdict"] != "ERROR":
                    return result

            # No API configured
            logger.warning("No third-party API keys configured")
            return {
                "verdict": "QUARANTINE",
                "confidence": 0.5,
                "flags": ["No third-party API configured - manual review required"],
                "api_used": None,
                "analysis": "Third-party verification unavailable",
            }

        except Exception as e:
            logger.error(f"Third-party verification failed: {str(e)}", exc_info=True)
            return {
                "verdict": "ERROR",
                "confidence": 0.0,
                "flags": [f"API verification error: {str(e)}"],
                "api_used": None,
                "analysis": "Third-party verification failed",
            }

    async def _verify_hive_ai(self, image_path: str) -> Dict:
        """
        Verify using Hive AI API V3 (Playground)

        Hive AI provides AI-generated content detection
        API Docs: https://docs.thehive.ai/

        Authentication: Bearer <SECRET_KEY>
        Format: access_key_id:secret_key - we use the secret_key part

        Returns:
            Analysis result
        """
        try:
            logger.info("Attempting Hive AI V3 verification")

            # Hive AI V3 API endpoint for AI-generated content detection
            url = "https://api.thehive.ai/api/v3/hive/ai-generated-and-deepfake-content-detection"

            # Extract secret key if format is "access_key:secret_key"
            if ":" in self.hive_api_key:
                secret_key = self.hive_api_key.split(":")[1]
            else:
                secret_key = self.hive_api_key

            # V3 uses Bearer authentication with the Secret Key
            auth_header = f"Bearer {secret_key}"
            logger.info("Using Bearer authentication with Secret Key")

            # Prepare request with multipart form data
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                with open(image_path, "rb") as f:
                    files = {"media": (Path(image_path).name, f, "image/jpeg")}
                    headers = {"authorization": auth_header}

                    response = await client.post(url, headers=headers, files=files)

                if response.status_code != 200:
                    logger.error(f"Hive AI API error: {response.status_code} - {response.text}")
                    return {"verdict": "ERROR"}

                result = response.json()
                logger.info(f"Hive AI response: {result}")

                # Parse Hive AI V3 response
                # Response structure: { "output": [{ "classes": [...] }] }
                ai_generated_score = 0.0
                deepfake_score = 0.0

                if "output" in result and result["output"]:
                    for output in result["output"]:
                        if "classes" in output:
                            for cls in output["classes"]:
                                if cls.get("class") == "ai_generated":
                                    ai_generated_score = cls.get("value", 0.0)
                                elif cls.get("class") == "deepfake":
                                    deepfake_score = cls.get("value", 0.0)

                # Determine verdict
                flags = []
                if ai_generated_score > 0.7:
                    verdict = "REJECT"
                    confidence = ai_generated_score
                    flags.append(f"Hive AI detected AI-generated content (score={ai_generated_score:.2f})")
                elif ai_generated_score > 0.4:
                    verdict = "QUARANTINE"
                    confidence = ai_generated_score
                    flags.append(f"Hive AI uncertain (score={ai_generated_score:.2f}) - manual review required")
                else:
                    verdict = "AUTHENTIC"
                    confidence = 1.0 - ai_generated_score
                    flags.append(f"Hive AI verified authentic (AI score={ai_generated_score:.2f})")

                return {
                    "verdict": verdict,
                    "confidence": confidence,
                    "flags": flags,
                    "api_used": "Hive AI",
                    "ai_score": ai_generated_score,
                    "analysis": f"Hive AI verification: {verdict}",
                }

        except Exception as e:
            logger.error(f"Hive AI verification failed: {str(e)}")
            return {"verdict": "ERROR"}

    async def _verify_optic(self, image_path: str) -> Dict:
        """
        Verify using Optic AI or similar API

        Placeholder for alternative AI detection API
        Replace with actual API implementation

        Returns:
            Analysis result
        """
        try:
            logger.info("Attempting Optic AI verification")

            # Placeholder implementation
            # Replace with actual Optic API integration

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Example API call structure (adjust based on actual API)
                with open(image_path, "rb") as f:
                    files = {"image": (Path(image_path).name, f, "image/jpeg")}

                    headers = {"Authorization": f"Bearer {self.optic_api_key}"}

                    # Placeholder endpoint - replace with actual
                    url = "https://api.optic.example/v1/detect"

                    response = await client.post(url, headers=headers, files=files)

                if response.status_code != 200:
                    logger.error(f"Optic API error: {response.status_code}")
                    return {"verdict": "ERROR"}

                result = response.json()

                # Parse response (adjust based on actual API)
                ai_probability = result.get("ai_probability", 0.5)

                if ai_probability > 0.7:
                    verdict = "REJECT"
                    confidence = ai_probability
                elif ai_probability > 0.4:
                    verdict = "QUARANTINE"
                    confidence = ai_probability
                else:
                    verdict = "AUTHENTIC"
                    confidence = 1.0 - ai_probability

                return {
                    "verdict": verdict,
                    "confidence": confidence,
                    "flags": [f"Optic AI score: {ai_probability:.2f}"],
                    "api_used": "Optic AI",
                    "ai_probability": ai_probability,
                    "analysis": f"Optic AI verification: {verdict}",
                }

        except Exception as e:
            logger.error(f"Optic AI verification failed: {str(e)}")
            return {"verdict": "ERROR"}

    async def verify_batch(self, image_paths: list[str]) -> list[Dict]:
        """
        Batch verification for multiple images

        Args:
            image_paths: List of image file paths

        Returns:
            List of analysis results
        """
        results = []

        for image_path in image_paths:
            result = await self.verify(image_path)
            results.append(result)

        return results
