"""
Judge Consensus Analysis Service

Analyzes judge scoring patterns, calculates consensus metrics (ICC),
detects bias, and identifies outliers.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

import numpy as np
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    JudgeScoringProfile,
    JudgeConsensusAnalysis,
    Score,
    Submission,
    User,
    JudgeAssignment,
)

logger = logging.getLogger(__name__)


class JudgeConsensusAnalyzer:
    """
    Analyzes judge consensus and detects scoring bias.

    Key metrics:
    - ICC (Intraclass Correlation Coefficient) - measures agreement
    - Z-score - detects bias (harsh/lenient judges)
    - Outlier detection - identifies anomalous scores
    """

    def __init__(self, db: AsyncSession):
        self.db = db

        # ICC thresholds for consensus quality
        self.excellent_icc = 0.75
        self.good_icc = 0.60
        self.fair_icc = 0.40

        # Z-score thresholds for bias detection
        self.significant_bias_threshold = 2.0  # |z| > 2.0 = significant bias
        self.moderate_bias_threshold = 1.5

        # Outlier detection threshold (scores beyond mean ± 2 SD)
        self.outlier_threshold = 2.0

    async def analyze_submission_scores(
        self,
        submission_id: int
    ) -> Dict:
        """
        Analyze consensus for a submission scored by multiple judges.

        Calculates:
        - ICC (Intraclass Correlation Coefficient)
        - Score agreement ratio
        - Outlier judges
        - Consensus verdict

        Args:
            submission_id: Submission ID

        Returns:
            Dictionary with consensus metrics
        """
        try:
            logger.info(f"Analyzing consensus for submission {submission_id}")

            # Get all scores for this submission
            result = await self.db.execute(
                select(Score)
                .where(Score.submission_id == submission_id)
                .order_by(Score.created_at)
            )
            scores = list(result.scalars().all())

            if len(scores) < 2:
                return {
                    "verdict": "insufficient_data",
                    "confidence": 0.0,
                    "icc": None,
                    "outliers": [],
                    "message": "Need at least 2 judges for consensus analysis"
                }

            # Extract score values
            score_values = np.array([s.total_score for s in scores])
            judge_ids = [s.judge_id for s in scores]

            # Calculate basic statistics
            score_mean = float(np.mean(score_values))
            score_std = float(np.std(score_values))
            score_range = float(np.max(score_values) - np.min(score_values))

            # Calculate ICC (Intraclass Correlation Coefficient)
            icc_value = await self._calculate_icc(scores)

            # Calculate score agreement ratio (% within ±1 of mean)
            agreement_ratio = np.sum(np.abs(score_values - score_mean) <= 1.0) / len(score_values)

            # Detect outlier judges (Z-score > 2)
            outlier_judges, outlier_scores_dict = self._detect_outlier_judges(
                score_values, judge_ids
            )

            # Determine consensus verdict
            verdict, confidence = self._determine_consensus_verdict(
                icc_value, agreement_ratio, len(outlier_judges), len(scores)
            )

            # Coefficient of variation (relative std dev)
            cv = (score_std / score_mean) if score_mean > 0 else 0.0

            return {
                "verdict": verdict,
                "confidence": float(confidence),
                "icc": float(icc_value) if icc_value is not None else None,
                "score_mean": score_mean,
                "score_std": score_std,
                "score_range": score_range,
                "agreement_ratio": float(agreement_ratio),
                "coefficient_of_variation": float(cv),
                "outliers": outlier_judges,
                "outlier_scores": outlier_scores_dict,
                "judge_count": len(scores),
                "scores_received": {jid: float(val) for jid, val in zip(judge_ids, score_values)}
            }

        except Exception as e:
            logger.error(f"Consensus analysis failed: {str(e)}")
            return {
                "verdict": "error",
                "confidence": 0.0,
                "icc": None,
                "outliers": [],
                "message": f"Analysis error: {str(e)}"
            }

    async def _calculate_icc(self, scores: List[Score]) -> Optional[float]:
        """
        Calculate ICC(2,1) - Intraclass Correlation Coefficient.

        ICC measures inter-rater reliability (how much judges agree).

        Formula: ICC(2,1) = (MS_rows - MS_error) / (MS_rows + (k-1)*MS_error)

        where:
        - MS_rows = Mean Square between subjects (submissions)
        - MS_error = Mean Square error (residual)
        - k = number of raters (judges)

        Args:
            scores: List of Score objects for the submission

        Returns:
            ICC value (0-1), or None if calculation fails
        """
        try:
            # For a single submission with multiple judges, we can use simplified ICC
            # This is a special case where we're calculating ICC for one "subject" (submission)

            score_values = np.array([s.total_score for s in scores])
            n_judges = len(score_values)

            if n_judges < 2:
                return None

            # Calculate variance components
            grand_mean = np.mean(score_values)
            ss_total = np.sum((score_values - grand_mean) ** 2)
            ms_error = ss_total / (n_judges - 1)

            # For single submission, ICC is related to variance ratio
            # Higher variance = lower ICC (more disagreement)
            # Lower variance = higher ICC (more agreement)

            # Normalized ICC approximation for single submission
            score_range = np.max(score_values) - np.min(score_values)
            max_possible_range = 10.0  # Assuming 1-10 scale

            # ICC approximation: 1 - (range / max_range)
            # Perfect agreement (range=0) → ICC=1
            # Maximum disagreement (range=10) → ICC=0
            icc = max(0.0, 1.0 - (score_range / max_possible_range))

            # Adjust for number of judges (more judges = more confidence)
            confidence_factor = min(1.0, n_judges / 5.0)  # Full confidence at 5+ judges
            icc = icc * (0.5 + 0.5 * confidence_factor)  # Scale by confidence

            return float(icc)

        except Exception as e:
            logger.warning(f"ICC calculation failed: {str(e)}")
            return None

    def _detect_outlier_judges(
        self,
        score_values: np.ndarray,
        judge_ids: List[int]
    ) -> Tuple[List[int], Dict]:
        """
        Detect judges whose scores are outliers (Z-score > threshold).

        Args:
            score_values: Array of scores
            judge_ids: Corresponding judge IDs

        Returns:
            Tuple of (outlier_judge_ids, outlier_scores_dict)
        """
        mean = np.mean(score_values)
        std = np.std(score_values)

        if std == 0:
            return [], {}

        # Calculate Z-scores
        z_scores = (score_values - mean) / std

        outlier_judges = []
        outlier_scores = {}

        for i, (judge_id, z_score) in enumerate(zip(judge_ids, z_scores)):
            if abs(z_score) > self.outlier_threshold:
                outlier_judges.append(judge_id)
                outlier_scores[judge_id] = float(z_score)

        return outlier_judges, outlier_scores

    def _determine_consensus_verdict(
        self,
        icc: Optional[float],
        agreement_ratio: float,
        outlier_count: int,
        total_judges: int
    ) -> Tuple[str, float]:
        """
        Determine overall consensus verdict and confidence.

        Args:
            icc: ICC value
            agreement_ratio: Proportion of scores within ±1 of mean
            outlier_count: Number of outlier judges
            total_judges: Total number of judges

        Returns:
            Tuple of (verdict, confidence)
        """
        if icc is None:
            return "insufficient_data", 0.0

        # Penalize for outliers
        outlier_penalty = outlier_count / total_judges

        # Calculate confidence
        confidence = icc * (1 - 0.5 * outlier_penalty)

        # Determine verdict
        if icc >= self.excellent_icc and outlier_count == 0:
            verdict = "strong_consensus"
        elif icc >= self.good_icc and outlier_count <= 1:
            verdict = "moderate_consensus"
        elif icc >= self.fair_icc:
            verdict = "weak_consensus"
        else:
            verdict = "poor_consensus"

        return verdict, float(confidence)

    async def build_judge_profile(
        self,
        judge_id: int,
        competition_id: int
    ) -> Dict:
        """
        Build statistical profile of judge's scoring behavior.

        Calculates:
        - Average score given
        - Standard deviation
        - Bias score (Z-score relative to other judges)
        - Consistency score

        Args:
            judge_id: Judge ID
            competition_id: Competition ID

        Returns:
            Judge profile statistics
        """
        try:
            logger.info(f"Building profile for judge {judge_id} in competition {competition_id}")

            # Get judge's scores for this competition
            result = await self.db.execute(
                select(Score)
                .join(Submission)
                .where(
                    and_(
                        Score.judge_id == judge_id,
                        Submission.competition_id == competition_id
                    )
                )
            )
            judge_scores = list(result.scalars().all())

            if not judge_scores:
                return {
                    "submission_count": 0,
                    "avg_score": None,
                    "bias_score": None,
                    "bias_category": "unknown",
                    "message": "No scores found"
                }

            # Extract score values
            score_values = np.array([s.total_score for s in judge_scores])

            # Calculate judge statistics
            avg_score = float(np.mean(score_values))
            std_dev = float(np.std(score_values))
            score_min = float(np.min(score_values))
            score_max = float(np.max(score_values))

            # Calculate bias score (compare to competition average)
            comp_avg = await self._get_competition_avg_score(competition_id)
            comp_std = await self._get_competition_std_score(competition_id)

            if comp_std > 0:
                bias_z_score = (avg_score - comp_avg) / comp_std
            else:
                bias_z_score = 0.0

            # Determine bias category
            if abs(bias_z_score) < 0.5:
                bias_category = "fair"
            elif bias_z_score > 0.5:
                bias_category = "lenient"
            else:
                bias_category = "harsh"

            # Calculate consistency score (inverse of CV)
            cv = std_dev / avg_score if avg_score > 0 else 0
            consistency_score = max(0.0, 1.0 - cv)

            # Score distribution
            score_distribution = {}
            for score_val in range(1, 11):
                score_distribution[score_val] = int(np.sum(score_values == score_val))

            # Count outliers (scores beyond ±2 SD of own mean)
            outlier_count = int(np.sum(np.abs(score_values - avg_score) > 2 * std_dev))

            # Extreme scores ratio (1s and 10s)
            extreme_count = np.sum((score_values == 1) | (score_values == 10))
            extreme_ratio = float(extreme_count / len(score_values))

            return {
                "submission_count": len(judge_scores),
                "avg_score": avg_score,
                "std_dev": std_dev,
                "score_min": score_min,
                "score_max": score_max,
                "bias_score": float(bias_z_score),
                "bias_category": bias_category,
                "consistency_score": float(consistency_score),
                "score_distribution": score_distribution,
                "outlier_count": outlier_count,
                "extreme_scores_ratio": extreme_ratio,
            }

        except Exception as e:
            logger.error(f"Judge profile building failed: {str(e)}")
            return {
                "submission_count": 0,
                "avg_score": None,
                "bias_score": None,
                "bias_category": "error",
                "message": f"Error: {str(e)}"
            }

    async def _get_competition_avg_score(self, competition_id: int) -> float:
        """Get average score across all judges in competition"""
        result = await self.db.execute(
            select(func.avg(Score.total_score))
            .join(Submission)
            .where(Submission.competition_id == competition_id)
        )
        avg = result.scalar_one_or_none()
        return float(avg) if avg else 5.0  # Default to middle score

    async def _get_competition_std_score(self, competition_id: int) -> float:
        """Get standard deviation of scores across all judges"""
        result = await self.db.execute(
            select(Score.total_score)
            .join(Submission)
            .where(Submission.competition_id == competition_id)
        )
        scores = [row[0] for row in result.all()]

        if len(scores) < 2:
            return 1.0  # Default std

        return float(np.std(scores))

    async def store_consensus_analysis(
        self,
        submission_id: int,
        competition_id: int,
        consensus_result: Dict
    ):
        """
        Store consensus analysis results in database.

        Args:
            submission_id: Submission ID
            competition_id: Competition ID
            consensus_result: Output from analyze_submission_scores()
        """
        try:
            # Check if analysis already exists
            existing = await self.db.execute(
                select(JudgeConsensusAnalysis).where(
                    and_(
                        JudgeConsensusAnalysis.submission_id == submission_id,
                        JudgeConsensusAnalysis.competition_id == competition_id
                    )
                )
            )
            analysis = existing.scalar_one_or_none()

            if analysis:
                # Update existing
                analysis.judge_count = consensus_result["judge_count"]
                analysis.scores_received = consensus_result["scores_received"]
                analysis.score_mean = consensus_result.get("score_mean")
                analysis.score_std_dev = consensus_result.get("score_std")
                analysis.score_range = consensus_result.get("score_range")
                analysis.icc_value = consensus_result.get("icc")
                analysis.score_agreement_ratio = consensus_result.get("agreement_ratio")
                analysis.coefficient_of_variation = consensus_result.get("coefficient_of_variation")
                analysis.outlier_judges = consensus_result.get("outliers")
                analysis.outlier_scores = consensus_result.get("outlier_scores")
                analysis.consensus_verdict = consensus_result.get("verdict")
                analysis.confidence_level = consensus_result.get("confidence")
                analysis.analysis_timestamp = datetime.utcnow()
            else:
                # Create new
                analysis = JudgeConsensusAnalysis(
                    competition_id=competition_id,
                    submission_id=submission_id,
                    judge_count=consensus_result["judge_count"],
                    scores_received=consensus_result["scores_received"],
                    score_mean=consensus_result.get("score_mean"),
                    score_std_dev=consensus_result.get("score_std"),
                    score_range=consensus_result.get("score_range"),
                    icc_value=consensus_result.get("icc"),
                    score_agreement_ratio=consensus_result.get("agreement_ratio"),
                    coefficient_of_variation=consensus_result.get("coefficient_of_variation"),
                    outlier_judges=consensus_result.get("outliers"),
                    outlier_scores=consensus_result.get("outlier_scores"),
                    consensus_verdict=consensus_result.get("verdict"),
                    confidence_level=consensus_result.get("confidence"),
                    analysis_timestamp=datetime.utcnow(),
                )
                self.db.add(analysis)

            await self.db.flush()
            logger.info(f"Stored consensus analysis for submission {submission_id}")

        except Exception as e:
            logger.error(f"Failed to store consensus analysis: {str(e)}")

    async def store_judge_profile(
        self,
        judge_id: int,
        competition_id: int,
        profile_data: Dict
    ):
        """
        Store or update judge scoring profile.

        Args:
            judge_id: Judge ID
            competition_id: Competition ID
            profile_data: Output from build_judge_profile()
        """
        try:
            # Check if profile exists
            existing = await self.db.execute(
                select(JudgeScoringProfile).where(
                    and_(
                        JudgeScoringProfile.judge_id == judge_id,
                        JudgeScoringProfile.competition_id == competition_id
                    )
                )
            )
            profile = existing.scalar_one_or_none()

            if profile:
                # Update existing
                profile.submission_count = profile_data["submission_count"]
                profile.avg_score_given = profile_data.get("avg_score")
                profile.score_std_dev = profile_data.get("std_dev")
                profile.score_range_min = profile_data.get("score_min")
                profile.score_range_max = profile_data.get("score_max")
                profile.bias_score = profile_data.get("bias_score")
                profile.consistency_score = profile_data.get("consistency_score")
                profile.score_distribution = profile_data.get("score_distribution")
                profile.outlier_count = profile_data.get("outlier_count", 0)
                profile.extreme_scores_ratio = profile_data.get("extreme_scores_ratio")
                profile.last_analyzed = datetime.utcnow()
            else:
                # Create new
                profile = JudgeScoringProfile(
                    judge_id=judge_id,
                    competition_id=competition_id,
                    submission_count=profile_data["submission_count"],
                    avg_score_given=profile_data.get("avg_score"),
                    score_std_dev=profile_data.get("std_dev"),
                    score_range_min=profile_data.get("score_min"),
                    score_range_max=profile_data.get("score_max"),
                    bias_score=profile_data.get("bias_score"),
                    consistency_score=profile_data.get("consistency_score"),
                    score_distribution=profile_data.get("score_distribution"),
                    outlier_count=profile_data.get("outlier_count", 0),
                    extreme_scores_ratio=profile_data.get("extreme_scores_ratio"),
                    last_analyzed=datetime.utcnow(),
                )
                self.db.add(profile)

            await self.db.flush()
            logger.info(f"Stored profile for judge {judge_id}")

        except Exception as e:
            logger.error(f"Failed to store judge profile: {str(e)}")
