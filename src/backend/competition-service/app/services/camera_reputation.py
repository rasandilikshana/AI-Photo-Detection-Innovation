"""
Camera Reputation Management Service

Builds trust profiles for cameras over time based on PRNU fingerprint consistency.
Detects camera fraud and credential manipulation.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CameraFingerprint,
    CameraTrustProfile,
    PRNUComparison,
    Submission,
    User,
)
from app.services.prnu_extractor import PRNUExtractor

logger = logging.getLogger(__name__)


class CameraReputationManager:
    """
    Manages camera reputation system based on PRNU fingerprint analysis.

    Key features:
    - Stores and retrieves camera fingerprints
    - Calculates trust scores based on pattern consistency
    - Detects camera fraud (wrong camera claimed)
    - Builds reputation profiles over time
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.prnu_extractor = PRNUExtractor()

        # Trust scoring weights
        self.similarity_weight = 0.5
        self.history_weight = 0.3
        self.consistency_weight = 0.2

        # Similarity thresholds for trust boost
        self.strong_match_threshold = 0.85  # +15% boost
        self.moderate_match_threshold = 0.70  # +5% boost
        self.weak_match_threshold = 0.50  # 0% boost
        # Below 0.50 = penalty

    async def store_fingerprint(
        self,
        submission_id: int,
        prnu_data: Dict,
        camera_make: str,
        camera_model: str,
        user_id: int,
        capture_context: Optional[Dict] = None
    ) -> CameraFingerprint:
        """
        Store PRNU fingerprint for a submission.

        Args:
            submission_id: ID of the submission
            prnu_data: Output from PRNUExtractor.extract_prnu_fingerprint()
            camera_make: Camera manufacturer
            camera_model: Camera model
            user_id: User who submitted
            capture_context: Optional EXIF data (ISO, aperture, etc.)

        Returns:
            Created CameraFingerprint record
        """
        try:
            logger.info(f"Storing fingerprint for submission {submission_id}")

            # Create fingerprint record
            fingerprint = CameraFingerprint(
                submission_id=submission_id,
                user_id=user_id,
                camera_make=camera_make,
                camera_model=camera_model,
                prnu_signature=prnu_data["signature"],
                prnu_energy=prnu_data["energy"],
                prnu_hash=prnu_data["hash"],
                capture_context=capture_context,
                verified=prnu_data["valid"]
            )

            self.db.add(fingerprint)
            await self.db.flush()  # Get ID without committing

            logger.info(f"Fingerprint stored with ID {fingerprint.id}")

            return fingerprint

        except Exception as e:
            logger.error(f"Failed to store fingerprint: {str(e)}")
            raise

    async def calculate_trust_score(
        self,
        current_prnu: np.ndarray,
        camera_make: str,
        camera_model: str,
        user_id: int
    ) -> Dict:
        """
        Calculate trust score by comparing with historical fingerprints.

        Trust Score Formula:
        trust_score = (
            0.5 * overall_similarity +
            0.3 * (authentic_count / total_count) +
            0.2 * verdict_consistency
        )

        Args:
            current_prnu: Current PRNU pattern
            camera_make: Camera manufacturer
            camera_model: Camera model
            user_id: User ID

        Returns:
            Dictionary with trust score and analysis
        """
        try:
            logger.info(f"Calculating trust score for {camera_make} {camera_model}")

            # Get user's previous submissions with this camera
            user_fingerprints = await self._get_user_camera_fingerprints(
                user_id, camera_make, camera_model
            )

            # Get global camera profile
            camera_profile = await self._get_or_create_profile(camera_make, camera_model)

            if not user_fingerprints:
                # First submission with this camera
                logger.info("First submission with this camera - baseline trust score")
                return {
                    "trust_score": 0.5,  # Neutral baseline
                    "boost": 0.0,
                    "message": "First submission with this camera",
                    "similarity_to_profile": None,
                    "previous_submissions": 0,
                    "verdict": "baseline"
                }

            # Compare with previous fingerprints
            similarities = []
            for prev_fp in user_fingerprints:
                # Decompress previous pattern
                prev_pattern = self.prnu_extractor.decompress_pattern(
                    prev_fp.prnu_signature,
                    (512, 512)  # Target size from extractor
                )

                # Compare patterns
                comparison = await self.prnu_extractor.compare_patterns(
                    current_prnu, prev_pattern
                )

                similarities.append(comparison["similarity_score"])

                # Store comparison record
                await self._store_comparison(
                    None,  # Will be set after current fingerprint is stored
                    prev_fp.id,
                    comparison
                )

            # Calculate average similarity
            avg_similarity = np.mean(similarities) if similarities else 0.0
            max_similarity = np.max(similarities) if similarities else 0.0

            # Calculate trust boost based on similarity
            trust_boost = self._calculate_trust_boost(avg_similarity)

            # Get historical verdict consistency
            verdict_consistency = await self._get_verdict_consistency(
                user_id, camera_make, camera_model
            )

            # Calculate final trust score
            trust_score = (
                self.similarity_weight * avg_similarity +
                self.history_weight * (camera_profile.authentic_count / max(camera_profile.total_submissions, 1)) +
                self.consistency_weight * verdict_consistency
            )

            # Determine verdict
            if max_similarity > self.strong_match_threshold:
                verdict = "strong_match"
                message = f"Strong camera match (similarity: {max_similarity:.1%})"
            elif max_similarity > self.moderate_match_threshold:
                verdict = "moderate_match"
                message = f"Moderate camera match (similarity: {max_similarity:.1%})"
            elif max_similarity > self.weak_match_threshold:
                verdict = "weak_match"
                message = f"Weak camera match (similarity: {max_similarity:.1%})"
            else:
                verdict = "suspicious"
                message = f"Camera fingerprint mismatch (similarity: {max_similarity:.1%})"

            return {
                "trust_score": float(min(1.0, max(0.0, trust_score))),
                "boost": float(trust_boost),
                "message": message,
                "similarity_to_profile": float(avg_similarity),
                "max_similarity": float(max_similarity),
                "previous_submissions": len(user_fingerprints),
                "verdict": verdict,
                "verdict_consistency": float(verdict_consistency),
            }

        except Exception as e:
            logger.error(f"Trust score calculation failed: {str(e)}")
            return {
                "trust_score": 0.5,
                "boost": 0.0,
                "message": f"Error calculating trust score: {str(e)}",
                "verdict": "error"
            }

    def _calculate_trust_boost(self, similarity: float) -> float:
        """
        Calculate trust boost based on similarity threshold.

        Similarity Thresholds:
        > 0.85: +15% boost (strong match)
        0.70-0.85: +5% boost (moderate match)
        0.50-0.70: 0% (neutral)
        < 0.50: -10% penalty (suspicious)
        """
        if similarity > self.strong_match_threshold:
            return 0.15
        elif similarity > self.moderate_match_threshold:
            return 0.05
        elif similarity > self.weak_match_threshold:
            return 0.0
        else:
            return -0.10

    async def detect_camera_fraud(
        self,
        submission_id: int,
        current_prnu: np.ndarray,
        claimed_camera_make: str,
        claimed_camera_model: str,
        user_id: int
    ) -> Dict:
        """
        Detect if submitted image doesn't match claimed camera.

        Checks against:
        1. User's previous submissions with claimed camera
        2. Global camera profile
        3. Known camera PRNU ranges

        Args:
            submission_id: Current submission ID
            current_prnu: Extracted PRNU pattern
            claimed_camera_make: Camera make from EXIF
            claimed_camera_model: Camera model from EXIF
            user_id: User ID

        Returns:
            Fraud detection result
        """
        try:
            logger.info(f"Checking for camera fraud: submission {submission_id}")

            # Get trust score analysis
            trust_analysis = await self.calculate_trust_score(
                current_prnu, claimed_camera_make, claimed_camera_model, user_id
            )

            fraud_indicators = []
            fraud_likelihood = 0.0

            # Check 1: Low similarity to previous submissions
            if trust_analysis.get("max_similarity", 1.0) < 0.40:
                fraud_indicators.append(
                    f"PRNU pattern doesn't match previous {claimed_camera_make} {claimed_camera_model} submissions"
                )
                fraud_likelihood += 0.4

            # Check 2: Energy level mismatch with camera profile
            camera_profile = await self._get_or_create_profile(
                claimed_camera_make, claimed_camera_model
            )

            current_energy = np.var(current_prnu)

            if camera_profile.avg_prnu_energy and camera_profile.total_submissions > 5:
                energy_deviation = abs(current_energy - camera_profile.avg_prnu_energy) / camera_profile.avg_prnu_energy

                if energy_deviation > 2.0:  # More than 2x deviation
                    fraud_indicators.append(
                        f"PRNU energy significantly different from typical {claimed_camera_make} {claimed_camera_model}"
                    )
                    fraud_likelihood += 0.3

            # Check 3: User has submitted with different camera before
            user_cameras = await self._get_user_camera_models(user_id)

            if len(user_cameras) > 1:
                # User has multiple cameras - check for suspicious patterns
                for prev_camera in user_cameras:
                    if (prev_camera["camera_make"], prev_camera["camera_model"]) != (claimed_camera_make, claimed_camera_model):
                        # Compare with different camera's fingerprints
                        # If similarity is HIGH, it suggests same physical camera but different EXIF
                        prev_fingerprints = await self._get_user_camera_fingerprints(
                            user_id,
                            prev_camera["camera_make"],
                            prev_camera["camera_model"]
                        )

                        for prev_fp in prev_fingerprints[:3]:  # Check up to 3 samples
                            prev_pattern = self.prnu_extractor.decompress_pattern(
                                prev_fp.prnu_signature, (512, 512)
                            )

                            comparison = await self.prnu_extractor.compare_patterns(
                                current_prnu, prev_pattern
                            )

                            if comparison["similarity_score"] > 0.75:
                                fraud_indicators.append(
                                    f"PRNU matches previous camera ({prev_camera['camera_make']} {prev_camera['camera_model']}) "
                                    f"but EXIF claims {claimed_camera_make} {claimed_camera_model}"
                                )
                                fraud_likelihood += 0.5
                                break

            # Determine verdict
            if fraud_likelihood > 0.7:
                verdict = "high_fraud_risk"
                recommendation = "reject"
            elif fraud_likelihood > 0.4:
                verdict = "moderate_fraud_risk"
                recommendation = "manual_review"
            else:
                verdict = "low_fraud_risk"
                recommendation = "approve"

            return {
                "fraud_likelihood": float(min(1.0, fraud_likelihood)),
                "verdict": verdict,
                "recommendation": recommendation,
                "indicators": fraud_indicators,
                "trust_score": trust_analysis["trust_score"],
                "explanation": self._generate_fraud_explanation(fraud_likelihood, fraud_indicators)
            }

        except Exception as e:
            logger.error(f"Fraud detection failed: {str(e)}")
            return {
                "fraud_likelihood": 0.0,
                "verdict": "error",
                "recommendation": "manual_review",
                "indicators": [f"Error during fraud detection: {str(e)}"],
                "explanation": "Unable to complete fraud detection"
            }

    def _generate_fraud_explanation(self, likelihood: float, indicators: List[str]) -> str:
        """Generate human-readable fraud explanation"""
        if likelihood > 0.7:
            return f"High fraud risk detected. {len(indicators)} suspicious indicator(s) found. " + \
                   "Image may be from a different camera than claimed."
        elif likelihood > 0.4:
            return f"Moderate fraud risk. {len(indicators)} indicator(s) suggest potential issues. " + \
                   "Manual review recommended."
        else:
            return "Camera fingerprint appears consistent with claimed camera."

    async def update_profile_stats(
        self,
        camera_make: str,
        camera_model: str,
        verdict: str,
        prnu_energy: float
    ):
        """
        Update camera trust profile statistics.

        Args:
            camera_make: Camera manufacturer
            camera_model: Camera model
            verdict: Verification verdict (authentic/suspicious/ai_generated/rejected)
            prnu_energy: PRNU energy of this submission
        """
        try:
            profile = await self._get_or_create_profile(camera_make, camera_model)

            # Update submission counts
            profile.total_submissions += 1

            if verdict == "authentic":
                profile.authentic_count += 1
            elif verdict == "suspicious":
                profile.suspicious_count += 1
            elif verdict == "ai_generated":
                profile.ai_generated_count += 1
            elif verdict == "rejected":
                profile.rejected_count += 1

            # Update average PRNU energy
            if profile.avg_prnu_energy is None:
                profile.avg_prnu_energy = prnu_energy
            else:
                # Running average
                profile.avg_prnu_energy = (
                    (profile.avg_prnu_energy * (profile.total_submissions - 1) + prnu_energy) /
                    profile.total_submissions
                )

            # Update average trust score
            authenticity_rate = profile.authentic_count / profile.total_submissions
            profile.avg_trust_score = authenticity_rate

            profile.last_updated = datetime.utcnow()

            await self.db.flush()

            logger.info(f"Updated profile for {camera_make} {camera_model}: "
                       f"{profile.total_submissions} submissions, "
                       f"{authenticity_rate:.1%} authentic")

        except Exception as e:
            logger.error(f"Failed to update profile stats: {str(e)}")

    async def _get_or_create_profile(
        self,
        camera_make: str,
        camera_model: str
    ) -> CameraTrustProfile:
        """Get existing profile or create new one"""
        result = await self.db.execute(
            select(CameraTrustProfile).where(
                and_(
                    CameraTrustProfile.camera_make == camera_make,
                    CameraTrustProfile.camera_model == camera_model
                )
            )
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = CameraTrustProfile(
                camera_make=camera_make,
                camera_model=camera_model
            )
            self.db.add(profile)
            await self.db.flush()

        return profile

    async def _get_user_camera_fingerprints(
        self,
        user_id: int,
        camera_make: str,
        camera_model: str,
        limit: int = 10
    ) -> List[CameraFingerprint]:
        """Get user's previous fingerprints for specific camera"""
        result = await self.db.execute(
            select(CameraFingerprint)
            .where(
                and_(
                    CameraFingerprint.user_id == user_id,
                    CameraFingerprint.camera_make == camera_make,
                    CameraFingerprint.camera_model == camera_model,
                    CameraFingerprint.verified == True
                )
            )
            .order_by(desc(CameraFingerprint.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _get_user_camera_models(self, user_id: int) -> List[Dict]:
        """Get distinct camera models used by user"""
        result = await self.db.execute(
            select(
                CameraFingerprint.camera_make,
                CameraFingerprint.camera_model,
                func.count(CameraFingerprint.id).label("count")
            )
            .where(CameraFingerprint.user_id == user_id)
            .group_by(CameraFingerprint.camera_make, CameraFingerprint.camera_model)
        )

        cameras = []
        for row in result:
            cameras.append({
                "camera_make": row.camera_make,
                "camera_model": row.camera_model,
                "submission_count": row.count
            })

        return cameras

    async def _get_verdict_consistency(
        self,
        user_id: int,
        camera_make: str,
        camera_model: str
    ) -> float:
        """
        Calculate verdict consistency for user's camera submissions.

        Returns ratio of authentic submissions (0.0 - 1.0)
        """
        result = await self.db.execute(
            select(Submission)
            .join(CameraFingerprint, Submission.prnu_fingerprint_id == CameraFingerprint.id)
            .where(
                and_(
                    CameraFingerprint.user_id == user_id,
                    CameraFingerprint.camera_make == camera_make,
                    CameraFingerprint.camera_model == camera_model
                )
            )
        )
        submissions = list(result.scalars().all())

        if not submissions:
            return 0.5  # Neutral for no history

        authentic_count = sum(1 for s in submissions if s.verification_verdict == "authentic")
        consistency = authentic_count / len(submissions)

        return consistency

    async def _store_comparison(
        self,
        fingerprint1_id: Optional[int],
        fingerprint2_id: int,
        comparison: Dict
    ):
        """Store PRNU comparison result"""
        try:
            # Skip if fingerprint1_id not set yet (will be created later)
            if fingerprint1_id is None:
                return

            comparison_record = PRNUComparison(
                fingerprint1_id=fingerprint1_id,
                fingerprint2_id=fingerprint2_id,
                similarity_score=comparison["similarity_score"],
                distance_metric=comparison.get("distance_metric", "euclidean"),
                correlation_coefficient=comparison.get("correlation"),
                same_camera=comparison.get("same_camera_likely", False),
                same_user=True,  # Since we're comparing same user's fingerprints
                comparison_details=comparison
            )

            self.db.add(comparison_record)
            await self.db.flush()

        except Exception as e:
            logger.warning(f"Failed to store comparison: {str(e)}")
