"""
Phase 6: Supplier Intelligence — Weighted KPI Scorer

Implements all scoring algorithms for supplier health evaluation.

────────────────────────────────────────────────────────────────────────
ALGORITHM 1: Reliability Score (Weighted Average)
────────────────────────────────────────────────────────────────────────
Inputs: on_time_delivery_rate, quality_rate, defect_rate
Formula:
  reliability_score = (
      on_time_delivery_rate × 0.45
    + quality_score          × 0.35
    + (1 - defect_rate)      × 0.20
  ) × 100

────────────────────────────────────────────────────────────────────────
ALGORITHM 2: Performance Score (Weighted Average)
────────────────────────────────────────────────────────────────────────
Inputs: KPI dimensions
Formula:
  performance_score = (
      reliability_score × 0.35
    + cost_efficiency   × 0.25
    + lead_time_score   × 0.20
    + responsiveness    × 0.20
  )

────────────────────────────────────────────────────────────────────────
ALGORITHM 3: Risk Score Integration (from Phase 4)
────────────────────────────────────────────────────────────────────────
  risk_component = 100 - risk_score
  (inverted: lower risk → higher contribution to health)

────────────────────────────────────────────────────────────────────────
ALGORITHM 4: Dependency Score Integration (from Phase 5)
────────────────────────────────────────────────────────────────────────
  dependency_score = centrality × 100   (0–100)
  dependency_component = 100 - dependency_score
  (inverted: lower centrality → less fragile → higher contribution)

────────────────────────────────────────────────────────────────────────
ALGORITHM 5: Health Score (Master Weighted Average)
────────────────────────────────────────────────────────────────────────
  health_score = (
      reliability_component  × 0.30
    + performance_component  × 0.25
    + risk_component         × 0.25
    + dependency_component   × 0.20
  )

  Weights sum = 1.00, output clamped to [0, 100].
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.supplier.models import HealthLabel, HealthScore, KPIScore

logger = logging.getLogger("supplier.scorer")

# ─────────────────────────────────────────────────────────────────────────────
# Weight tables
# ─────────────────────────────────────────────────────────────────────────────

# Reliability sub-components
RELIABILITY_WEIGHTS = {
    "on_time_rate":  0.45,
    "quality_score": 0.35,
    "defect_inv":    0.20,   # inverted defect rate
}

# Performance sub-components
PERFORMANCE_WEIGHTS = {
    "reliability": 0.35,
    "cost":        0.25,
    "lead_time":   0.20,
    "responsive":  0.20,
}

# Health master formula weights
HEALTH_WEIGHTS = {
    "reliability": 0.30,
    "performance": 0.25,
    "risk":        0.25,
    "dependency":  0.20,
}


class WeightedKPIScorer:
    """
    Computes all KPI and health scores for a single supplier.

    All methods return values on a 0–100 scale.
    """

    def score_reliability(self, kpi: KPIScore) -> float:
        """
        Reliability Score (Weighted Average of 3 KPIs).

        Formula:
          reliability = (
              kpi.reliability_score × 0.45   # on-time delivery dominant
            + kpi.quality_score     × 0.35   # quality contribution
            + kpi.compliance_score  × 0.20   # compliance as proxy for defect control
          )
        """
        score = (
            kpi.reliability_score * RELIABILITY_WEIGHTS["on_time_rate"]
            + kpi.quality_score   * RELIABILITY_WEIGHTS["quality_score"]
            + kpi.compliance_score * RELIABILITY_WEIGHTS["defect_inv"]
        )
        return round(min(100.0, max(0.0, score)), 2)

    def score_performance(self, kpi: KPIScore) -> float:
        """
        Performance Score (Weighted Average of 4 KPIs).

        Formula:
          performance = (
              reliability_score × 0.35
            + cost_efficiency   × 0.25
            + lead_time_score   × 0.20
            + responsiveness    × 0.20
          )
        """
        score = (
            kpi.reliability_score * PERFORMANCE_WEIGHTS["reliability"]
            + kpi.cost_efficiency * PERFORMANCE_WEIGHTS["cost"]
            + kpi.lead_time_score * PERFORMANCE_WEIGHTS["lead_time"]
            + kpi.responsiveness  * PERFORMANCE_WEIGHTS["responsive"]
        )
        return round(min(100.0, max(0.0, score)), 2)

    def score_health(
        self,
        kpi:              KPIScore,
        risk_score:       float = 0.0,
        dependency_score: float = 0.0,
    ) -> HealthScore:
        """
        Master Health Score — Weighted Average of 4 components.

        Formula:
          reliability_component  = reliability_score(kpi)  × 0.30
          performance_component  = performance_score(kpi)  × 0.25
          risk_component         = (100 - risk_score)      × 0.25
          dependency_component   = (100 - dep_score)       × 0.20
          health = Σ (clamped 0–100)

        risk_score:       0–100 from Phase 4 (higher = worse)
        dependency_score: 0–100 from Phase 5 centrality × 100 (higher = more fragile)
        """
        rel_raw  = self.score_reliability(kpi)
        perf_raw = self.score_performance(kpi)

        rel_component  = rel_raw                   * HEALTH_WEIGHTS["reliability"]
        perf_component = perf_raw                  * HEALTH_WEIGHTS["performance"]
        risk_component = (100.0 - risk_score)      * HEALTH_WEIGHTS["risk"]
        dep_component  = (100.0 - dependency_score) * HEALTH_WEIGHTS["dependency"]

        raw_health = rel_component + perf_component + risk_component + dep_component
        health     = round(min(100.0, max(0.0, raw_health)), 2)

        label = self._health_label(health)

        breakdown = {
            "reliability_raw":         round(rel_raw, 2),
            "performance_raw":         round(perf_raw, 2),
            "risk_raw":                round(risk_score, 2),
            "dependency_raw":          round(dependency_score, 2),
            "reliability_weighted":    round(rel_component, 4),
            "performance_weighted":    round(perf_component, 4),
            "risk_weighted":           round(risk_component, 4),
            "dependency_weighted":     round(dep_component, 4),
            "weights": HEALTH_WEIGHTS,
            "formula": (
                "health = reliability×0.30 + performance×0.25 "
                "+ (100-risk)×0.25 + (100-dependency)×0.20"
            ),
        }

        return HealthScore(
            health_score          = health,
            health_label          = label,
            reliability_component = round(rel_component, 4),
            performance_component = round(perf_component, 4),
            risk_component        = round(risk_component, 4),
            dependency_component  = round(dep_component, 4),
            formula_breakdown     = breakdown,
        )

    def apply_risk_overlay(
        self,
        base_score:    float,
        geo_risk:      float = 1.0,
        industry_risk: float = 1.0,
    ) -> float:
        """
        Apply geographic + industry risk multiplier overlay to a base score.

        The risk multipliers from Phase 4 are inverted (>1 = bad) so we
        use them to REDUCE the supplier health score:

          adjusted_score = base_score / (geo_risk × industry_risk)
          (clamped to [0, 100])

        Example:
          base_score = 80, geo_risk = 1.4, industry_risk = 1.2
          adjusted = 80 / (1.4 × 1.2) = 80 / 1.68 ≈ 47.6
        """
        combined_risk = geo_risk * industry_risk
        if combined_risk <= 0:
            return base_score
        adjusted = base_score / combined_risk
        return round(min(100.0, max(0.0, adjusted)), 2)

    def _health_label(self, score: float) -> str:
        if score >= 80:  return HealthLabel.EXCELLENT.value
        if score >= 66:  return HealthLabel.GOOD.value
        if score >= 50:  return HealthLabel.FAIR.value
        if score >= 33:  return HealthLabel.POOR.value
        return HealthLabel.CRITICAL.value
