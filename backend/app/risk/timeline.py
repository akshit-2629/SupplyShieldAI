"""
Risk Trajectory & Timeline — Phase 4

Tracks risk score trends over time using historical assessments.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("risk.timeline")


class RiskTimeline:
    """
    Computes trajectory (ESCALATING/STABLE/DECLINING/RECOVERING/NEW)
    from historical risk score data for the same event/topic.
    """

    def compute(
        self,
        current_score: float,
        history: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Compute risk trajectory.

        Args:
            current_score: current risk_score (0–100)
            history: optional list of previous scores (oldest first)

        Returns:
            dict with trajectory, trend_slope, history_length
        """
        if not history or len(history) < 2:
            return {
                "trajectory": "NEW",
                "trend_slope": 0.0,
                "history_length": len(history) if history else 0,
            }

        # Simple linear regression slope over last N points
        recent = history[-5:]  # last 5 periods
        n = len(recent)
        x_mean = (n - 1) / 2
        y_mean = sum(recent) / n
        numerator   = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(recent))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator else 0.0

        if slope > 3.0:
            trajectory = "ESCALATING"
        elif slope > 0.5:
            trajectory = "WORSENING"
        elif slope < -3.0:
            trajectory = "DECLINING"
        elif slope < -0.5:
            trajectory = "RECOVERING"
        else:
            trajectory = "STABLE"

        return {
            "trajectory":   trajectory,
            "trend_slope":  round(slope, 3),
            "history_length": len(history),
        }
