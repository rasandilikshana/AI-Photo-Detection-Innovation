"""
Credential Sharing Detection Service

Monitors judge activity patterns to detect credential sharing/account compromise.
Analyzes IP addresses, sessions, timing, and geographic patterns.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter

import numpy as np
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CredentialSharingDetection,
    ScoreAuditLog,
    User,
)

logger = logging.getLogger(__name__)


class CredentialSharingDetector:
    """
    Detects credential sharing and suspicious activity patterns.

    Monitors:
    - Multiple IP addresses
    - Concurrent sessions
    - Geographic inconsistencies
    - Impossible time gaps
    - User agent changes
    """

    def __init__(self, db: AsyncSession):
        self.db = db

        # Risk weights
        self.ip_diversity_weight = 0.4
        self.session_overlap_weight = 0.3
        self.time_gap_weight = 0.2
        self.geo_consistency_weight = 0.1

        # Thresholds
        self.suspicious_ip_count = 3  # More than 3 unique IPs = suspicious
        self.impossible_time_gap = 3600  # <1 hour between distant locations
        self.min_distance_km = 1000  # Distance threshold for geo checks

    async def analyze_judge_activity(
        self,
        judge_id: int,
        competition_id: int,
        time_window_days: int = 30
    ) -> Dict:
        """
        Analyze judge's activity patterns for credential sharing indicators.

        Args:
            judge_id: Judge ID to analyze
            competition_id: Competition ID
            time_window_days: Analysis window (default 30 days)

        Returns:
            Dictionary with risk assessment
        """
        try:
            logger.info(f"Analyzing activity for judge {judge_id} in competition {competition_id}")

            # Get audit logs for this judge in time window
            cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)

            result = await self.db.execute(
                select(ScoreAuditLog)
                .where(
                    and_(
                        ScoreAuditLog.judge_id == judge_id,
                        ScoreAuditLog.created_at >= cutoff_date
                    )
                )
                .order_by(ScoreAuditLog.created_at)
            )
            logs = list(result.scalars().all())

            if not logs:
                return {
                    "risk_score": 0.0,
                    "risk_level": "unknown",
                    "message": "No activity data available",
                    "factors": []
                }

            # Extract activity data
            ip_addresses = [log.ip_address for log in logs if log.ip_address]
            session_ids = [log.session_id for log in logs if log.session_id]
            user_agents = [log.user_agent for log in logs if log.user_agent]
            timestamps = [log.created_at for log in logs]

            # Calculate metrics
            unique_ips = list(set(ip_addresses))
            unique_sessions = list(set(session_ids))
            unique_user_agents = list(set(user_agents))

            # 1. IP Diversity Score
            ip_diversity_score = self._calculate_ip_diversity_score(len(unique_ips))

            # 2. Session Overlap Score
            session_overlap_score = self._calculate_session_overlap_score(logs)

            # 3. Time Gap Anomalies
            time_gap_score, time_gap_anomalies = self._detect_time_gap_anomalies(
                timestamps, ip_addresses
            )

            # 4. Geographic Inconsistencies (placeholder - requires geo-IP service)
            geo_score, geo_anomalies = self._detect_geographic_anomalies(
                unique_ips, timestamps
            )

            # Calculate overall risk score
            risk_score = (
                self.ip_diversity_weight * ip_diversity_score +
                self.session_overlap_weight * session_overlap_score +
                self.time_gap_weight * time_gap_score +
                self.geo_consistency_weight * geo_score
            )

            # Identify risk factors
            risk_factors = []

            if len(unique_ips) >= self.suspicious_ip_count:
                risk_factors.append(f"Multiple IP addresses detected ({len(unique_ips)})")

            if session_overlap_score > 0.5:
                risk_factors.append("Concurrent session patterns detected")

            if time_gap_anomalies:
                risk_factors.append(f"{len(time_gap_anomalies)} impossible time gaps detected")

            if geo_anomalies:
                risk_factors.append(f"{len(geo_anomalies)} geographic inconsistencies")

            if len(unique_user_agents) > 3:
                risk_factors.append(f"Multiple user agents ({len(unique_user_agents)})")

            # Determine risk level
            if risk_score > 0.7:
                risk_level = "high"
            elif risk_score > 0.4:
                risk_level = "medium"
            else:
                risk_level = "low"

            return {
                "risk_score": float(risk_score),
                "risk_level": risk_level,
                "unique_ip_count": len(unique_ips),
                "unique_session_count": len(unique_sessions),
                "unique_user_agent_count": len(unique_user_agents),
                "ip_addresses": unique_ips,
                "session_ids": unique_sessions,
                "time_gap_anomalies": time_gap_anomalies,
                "geographic_inconsistencies": geo_anomalies,
                "risk_factors": risk_factors,
                "total_activities": len(logs),
            }

        except Exception as e:
            logger.error(f"Activity analysis failed: {str(e)}")
            return {
                "risk_score": 0.0,
                "risk_level": "error",
                "message": f"Analysis error: {str(e)}",
                "factors": []
            }

    def _calculate_ip_diversity_score(self, unique_ip_count: int) -> float:
        """
        Calculate risk score based on IP diversity.

        1 IP = 0.0 (normal)
        2 IPs = 0.2 (could be home/work)
        3 IPs = 0.5 (suspicious)
        4+ IPs = 0.8+ (high risk)
        """
        if unique_ip_count == 1:
            return 0.0
        elif unique_ip_count == 2:
            return 0.2
        elif unique_ip_count == 3:
            return 0.5
        else:
            return min(1.0, 0.5 + (unique_ip_count - 3) * 0.1)

    def _calculate_session_overlap_score(self, logs: List[ScoreAuditLog]) -> float:
        """
        Detect concurrent sessions (same time, different IPs).

        Checks if activities happened simultaneously from different locations.
        """
        if len(logs) < 2:
            return 0.0

        overlap_count = 0
        threshold_seconds = 300  # 5 minutes

        for i in range(len(logs) - 1):
            for j in range(i + 1, len(logs)):
                log1, log2 = logs[i], logs[j]

                # Check if same time but different IPs
                if log1.ip_address != log2.ip_address:
                    time_diff = abs((log2.created_at - log1.created_at).total_seconds())

                    if time_diff < threshold_seconds:
                        overlap_count += 1

        # Normalize by total activities
        overlap_ratio = overlap_count / len(logs)

        return min(1.0, overlap_ratio * 10)  # Scale up for visibility

    def _detect_time_gap_anomalies(
        self,
        timestamps: List[datetime],
        ip_addresses: List[str]
    ) -> Tuple[float, List[Dict]]:
        """
        Detect impossible time gaps (e.g., activity in distant locations too quickly).

        For simplicity, we check for very rapid IP changes.
        """
        anomalies = []

        if len(timestamps) < 2:
            return 0.0, anomalies

        prev_time = timestamps[0]
        prev_ip = ip_addresses[0]

        for i in range(1, len(timestamps)):
            current_time = timestamps[i]
            current_ip = ip_addresses[i]

            if current_ip != prev_ip:
                time_gap_seconds = (current_time - prev_time).total_seconds()

                # Suspicious if IP changed within 1 hour
                if time_gap_seconds < self.impossible_time_gap:
                    anomalies.append({
                        "from_ip": prev_ip,
                        "to_ip": current_ip,
                        "gap_seconds": int(time_gap_seconds),
                        "timestamp": current_time.isoformat(),
                    })

            prev_time = current_time
            prev_ip = current_ip

        # Calculate score
        anomaly_ratio = len(anomalies) / max(len(timestamps) - 1, 1)
        score = min(1.0, anomaly_ratio * 5)

        return float(score), anomalies

    def _detect_geographic_anomalies(
        self,
        ip_addresses: List[str],
        timestamps: List[datetime]
    ) -> Tuple[float, List[Dict]]:
        """
        Detect geographic inconsistencies.

        Note: This is a placeholder. Real implementation would use
        a geo-IP service to get lat/lon and calculate distances.
        """
        # Placeholder: Would integrate with geo-IP service
        # For now, just detect if IPs are very different (heuristic)

        anomalies = []

        # Simple heuristic: check if first 2 octets differ significantly
        if len(ip_addresses) > 1:
            ip_prefixes = [".".join(ip.split(".")[:2]) for ip in ip_addresses]
            unique_prefixes = set(ip_prefixes)

            if len(unique_prefixes) > 1:
                # Different network blocks = potentially different locations
                anomalies.append({
                    "ip_count": len(ip_addresses),
                    "unique_prefixes": len(unique_prefixes),
                    "message": "Multiple network blocks detected (may indicate different locations)"
                })

        score = 0.5 if anomalies else 0.0

        return float(score), anomalies

    async def store_detection_result(
        self,
        judge_id: int,
        competition_id: int,
        detection_result: Dict
    ):
        """
        Store credential sharing detection result.

        Args:
            judge_id: Judge ID
            competition_id: Competition ID
            detection_result: Output from analyze_judge_activity()
        """
        try:
            # Check if record exists
            existing = await self.db.execute(
                select(CredentialSharingDetection).where(
                    and_(
                        CredentialSharingDetection.judge_id == judge_id,
                        CredentialSharingDetection.competition_id == competition_id
                    )
                )
            )
            detection = existing.scalar_one_or_none()

            risk_score = detection_result.get("risk_score", 0.0)
            alert_triggered = risk_score > 0.6  # Trigger alert if high risk

            if detection:
                # Update existing
                detection.unique_ip_count = detection_result.get("unique_ip_count")
                detection.unique_session_count = detection_result.get("unique_session_count")
                detection.unique_user_agent_count = detection_result.get("unique_user_agent_count")
                detection.ip_addresses = detection_result.get("ip_addresses")
                detection.session_ids = detection_result.get("session_ids")
                detection.time_gap_anomalies = detection_result.get("time_gap_anomalies")
                detection.geographic_inconsistencies = detection_result.get("geographic_inconsistencies")
                detection.risk_score = risk_score
                detection.risk_level = detection_result.get("risk_level")
                detection.risk_factors = detection_result.get("risk_factors")
                detection.alert_triggered = alert_triggered
            else:
                # Create new
                detection = CredentialSharingDetection(
                    competition_id=competition_id,
                    judge_id=judge_id,
                    unique_ip_count=detection_result.get("unique_ip_count"),
                    unique_session_count=detection_result.get("unique_session_count"),
                    unique_user_agent_count=detection_result.get("unique_user_agent_count"),
                    ip_addresses=detection_result.get("ip_addresses"),
                    session_ids=detection_result.get("session_ids"),
                    time_gap_anomalies=detection_result.get("time_gap_anomalies"),
                    geographic_inconsistencies=detection_result.get("geographic_inconsistencies"),
                    risk_score=risk_score,
                    risk_level=detection_result.get("risk_level"),
                    risk_factors=detection_result.get("risk_factors"),
                    alert_triggered=alert_triggered,
                    investigation_status="pending" if alert_triggered else "no_action_needed",
                )
                self.db.add(detection)

            await self.db.flush()
            logger.info(f"Stored detection result for judge {judge_id}")

        except Exception as e:
            logger.error(f"Failed to store detection result: {str(e)}")

    async def get_flagged_judges(
        self,
        competition_id: int,
        min_risk_score: float = 0.6
    ) -> List[CredentialSharingDetection]:
        """
        Get judges flagged for credential sharing in a competition.

        Args:
            competition_id: Competition ID
            min_risk_score: Minimum risk score to include (default 0.6)

        Returns:
            List of detection records
        """
        result = await self.db.execute(
            select(CredentialSharingDetection)
            .where(
                and_(
                    CredentialSharingDetection.competition_id == competition_id,
                    CredentialSharingDetection.risk_score >= min_risk_score
                )
            )
            .order_by(CredentialSharingDetection.risk_score.desc())
        )

        return list(result.scalars().all())
