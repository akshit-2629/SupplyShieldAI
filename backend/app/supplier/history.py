"""
Phase 6: Supplier Intelligence — Historical Performance Tracker

────────────────────────────────────────────────────────────────────────
ALGORITHM: Historical MoM (Month-over-Month) Trend Tracking
────────────────────────────────────────────────────────────────────────

For each supplier we maintain a rolling window of score snapshots.
The MoM delta and trend direction are computed each time a new score is recorded.

MoM Change Formula:
  mom_change = current_health - prev_health   (absolute delta, 0-100 scale)

  If |mom_change| >= 3 → IMPROVING or DECLINING
  If |mom_change| <  3 → STABLE
  If no history        → NEW_ENTRY

Trend Streak:
  streak_count: how many consecutive runs the same trend direction has been observed.
  Provides "momentum" signal:
    streak 1-2 = early signal
    streak 3+  = confirmed trend

Rolling Window:
  Kept in-memory (max 30 snapshots per supplier).
  Oldest snapshot dropped when window is full.

Peak / Trough Detection:
  peak_score:  highest health score ever recorded (max)
  trough_score: lowest health score ever recorded (min)
  distance_from_peak: current - peak (negative = below peak)
"""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

from app.supplier.models import PerformanceTrend

logger = logging.getLogger("supplier.history")

MAX_WINDOW = 30          # max snapshots per supplier
TREND_THRESHOLD = 3.0   # absolute delta >= 3 → trend change


class SupplierHistoryEntry:
    """One snapshot in a supplier's score history."""
    __slots__ = ("health_score", "risk_score", "reliability_score", "recorded_at")

    def __init__(self, health_score: float, risk_score: float, reliability_score: float) -> None:
        self.health_score      = health_score
        self.risk_score        = risk_score
        self.reliability_score = reliability_score
        self.recorded_at       = datetime.now(timezone.utc).isoformat()


class HistoricalTracker:
    """
    Tracks rolling score history for all suppliers.
    Singleton — one instance maintained per process lifetime.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Deque[SupplierHistoryEntry]] = {}

    def record(
        self,
        supplier_id:       str,
        health_score:      float,
        risk_score:        float        = 0.0,
        reliability_score: float        = 0.0,
    ) -> Dict[str, Any]:
        """
        Record a new score snapshot and compute trend metrics.

        Returns trend metrics for this recording:
          {
            "supplier_id": str,
            "trend":       PerformanceTrend,
            "mom_change":  float,
            "prev_health": float | None,
            "streak":      int,
            "peak_score":  float,
            "trough_score": float,
          }
        """
        window = self._store.setdefault(supplier_id, deque(maxlen=MAX_WINDOW))
        entry  = SupplierHistoryEntry(health_score, risk_score, reliability_score)

        if not window:
            # First ever recording
            window.append(entry)
            return {
                "supplier_id": supplier_id,
                "trend":       PerformanceTrend.NEW_ENTRY,
                "mom_change":  0.0,
                "prev_health": None,
                "streak":      1,
                "peak_score":  health_score,
                "trough_score": health_score,
                "snapshot_count": 1,
            }

        prev_entry  = window[-1]
        prev_health = prev_entry.health_score
        mom_change  = health_score - prev_health

        # Compute trend direction
        if mom_change >= TREND_THRESHOLD:
            trend = PerformanceTrend.IMPROVING
        elif mom_change <= -TREND_THRESHOLD:
            trend = PerformanceTrend.DECLINING
        else:
            trend = PerformanceTrend.STABLE

        # Streak counting — how many consecutive same-direction trends
        streak = self._compute_streak(window, trend)

        # Peak / trough from full window
        all_scores  = [e.health_score for e in window] + [health_score]
        peak_score  = max(all_scores)
        trough_score = min(all_scores)

        window.append(entry)

        return {
            "supplier_id":    supplier_id,
            "trend":          trend,
            "mom_change":     round(mom_change, 2),
            "prev_health":    round(prev_health, 2),
            "streak":         streak,
            "peak_score":     round(peak_score, 2),
            "trough_score":   round(trough_score, 2),
            "distance_from_peak": round(health_score - peak_score, 2),
            "snapshot_count": len(window),
        }

    def get_history(self, supplier_id: str) -> List[Dict[str, Any]]:
        """Return full snapshot history for one supplier."""
        window = self._store.get(supplier_id, deque())
        return [
            {
                "health_score":      e.health_score,
                "risk_score":        e.risk_score,
                "reliability_score": e.reliability_score,
                "recorded_at":       e.recorded_at,
            }
            for e in window
        ]

    def get_trend_summary(self, supplier_id: str) -> Dict[str, Any]:
        """Quick trend summary for a supplier."""
        window = self._store.get(supplier_id)
        if not window or len(window) < 2:
            return {"supplier_id": supplier_id, "trend": PerformanceTrend.NEW_ENTRY.value, "data_points": len(window) if window else 0}

        scores    = [e.health_score for e in window]
        latest    = scores[-1]
        previous  = scores[-2]
        mom_delta = latest - previous
        trend     = (
            PerformanceTrend.IMPROVING if mom_delta >= TREND_THRESHOLD
            else PerformanceTrend.DECLINING if mom_delta <= -TREND_THRESHOLD
            else PerformanceTrend.STABLE
        )
        return {
            "supplier_id":   supplier_id,
            "trend":         trend.value,
            "mom_change":    round(mom_delta, 2),
            "latest_health": round(latest, 2),
            "peak_score":    round(max(scores), 2),
            "trough_score":  round(min(scores), 2),
            "data_points":   len(window),
        }

    def _compute_streak(
        self,
        window: Deque[SupplierHistoryEntry],
        current_trend: PerformanceTrend,
    ) -> int:
        """Count consecutive snapshots with the same trend direction."""
        if len(window) < 2:
            return 1

        entries  = list(window)
        streak   = 1

        for i in range(len(entries) - 1, 0, -1):
            delta = entries[i].health_score - entries[i - 1].health_score
            if current_trend == PerformanceTrend.IMPROVING and delta >= TREND_THRESHOLD:
                streak += 1
            elif current_trend == PerformanceTrend.DECLINING and delta <= -TREND_THRESHOLD:
                streak += 1
            elif current_trend == PerformanceTrend.STABLE and abs(delta) < TREND_THRESHOLD:
                streak += 1
            else:
                break

        return streak

    def all_supplier_ids(self) -> List[str]:
        return list(self._store.keys())

    def clear(self, supplier_id: str) -> None:
        self._store.pop(supplier_id, None)


# Module-level singleton
historical_tracker = HistoricalTracker()
