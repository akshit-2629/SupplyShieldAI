"""
Phase 6: Supplier Intelligence — Fleet Aggregator

────────────────────────────────────────────────────────────────────────
ALGORITHM: Aggregation (Fleet-Wide Statistics)
────────────────────────────────────────────────────────────────────────

Aggregation computes summary statistics across the entire supplier fleet:

1. Score Distributions (buckets):
   Buckets: CRITICAL(0-33), POOR(33-50), FAIR(50-66), GOOD(66-80), EXCELLENT(80-100)
   count_per_bucket = Σ(suppliers where score falls in bucket)

2. Tier Distribution:
   tier_counts = {TIER_1: n, TIER_2: n, TIER_3: n}
   tier_health_avg = mean(health_score) per tier

3. Country Risk Aggregation:
   country_risk_score = weighted_avg(supplier.risk_score, weight=supplier.revenue_exposure_pct)
   per ISO country code

4. Fleet Health Index (FHI):
   FHI = Σ(health_score × revenue_exposure_pct) / Σ(revenue_exposure_pct)
   (revenue-weighted average health — the most meaningful single number)

5. Critical Alerts:
   Trigger when: health_label = CRITICAL  OR  risk_level = CRITICAL
   OR  tier = TIER_1 AND health_score < 50
"""

from __future__ import annotations

import logging
import statistics
from typing import Any, Dict, List

from app.supplier.models import SupplierProfile, SupplierTier

logger = logging.getLogger("supplier.aggregator")


class FleetAggregator:
    """
    Computes fleet-wide aggregated statistics across all supplier profiles.
    """

    def aggregate(self, profiles: List[SupplierProfile]) -> Dict[str, Any]:
        """
        Full fleet aggregation.

        Returns:
            {
              "fleet_health_index":    float,   # revenue-weighted avg health
              "total_suppliers":       int,
              "tier_distribution":     {...},
              "health_distribution":   {...},
              "country_risk":          {...},
              "industry_risk":         {...},
              "critical_alerts":       [...],
              "top_performers":        [...],
              "bottom_performers":     [...],
              "avg_scores":            {...},
              "risk_concentration":    {...},
            }
        """
        if not profiles:
            return {
                "fleet_health_index": 0.0,
                "total_suppliers": 0,
                "message": "No supplier profiles",
            }

        fhi         = self._fleet_health_index(profiles)
        tier_dist   = self._tier_distribution(profiles)
        health_dist = self._health_distribution(profiles)
        country_r   = self._country_risk_aggregation(profiles)
        industry_r  = self._industry_risk_aggregation(profiles)
        alerts      = self._critical_alerts(profiles)
        avg_scores  = self._average_scores(profiles)
        risk_conc   = self._risk_concentration(profiles)

        sorted_by_health = sorted(profiles, key=lambda p: p.health.health_score, reverse=True)

        return {
            "fleet_health_index":    round(fhi, 2),
            "fleet_health_label":    self._fhi_label(fhi),
            "total_suppliers":       len(profiles),
            "tier_distribution":     tier_dist,
            "health_distribution":   health_dist,
            "country_risk":          country_r,
            "industry_risk":         industry_r,
            "critical_alerts":       alerts,
            "alert_count":           len(alerts),
            "top_performers":        [self._mini(p) for p in sorted_by_health[:3]],
            "bottom_performers":     [self._mini(p) for p in sorted_by_health[-3:][::-1]],
            "avg_scores":            avg_scores,
            "risk_concentration":    risk_conc,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _fleet_health_index(self, profiles: List[SupplierProfile]) -> float:
        """
        Fleet Health Index = Σ(health × revenue_exposure) / Σ(revenue_exposure)
        Revenue-weighted average health score.
        """
        total_weight = sum(p.revenue_exposure_pct for p in profiles)
        if total_weight <= 0:
            return statistics.mean(p.health.health_score for p in profiles)

        weighted_sum = sum(
            p.health.health_score * p.revenue_exposure_pct
            for p in profiles
        )
        return weighted_sum / total_weight

    def _tier_distribution(self, profiles: List[SupplierProfile]) -> Dict[str, Any]:
        counts = {t.value: 0 for t in SupplierTier}
        health_sums:  Dict[str, float] = {}
        revenue_sums: Dict[str, float] = {}

        for p in profiles:
            t = p.tier.value
            counts[t] = counts.get(t, 0) + 1
            health_sums[t]  = health_sums.get(t, 0.0)  + p.health.health_score
            revenue_sums[t] = revenue_sums.get(t, 0.0) + p.revenue_exposure_pct

        return {
            t: {
                "count":          counts.get(t, 0),
                "avg_health":     round(health_sums.get(t, 0) / counts[t], 2) if counts.get(t, 0) else 0.0,
                "total_exposure": round(revenue_sums.get(t, 0), 2),
            }
            for t in counts
        }

    def _health_distribution(self, profiles: List[SupplierProfile]) -> Dict[str, int]:
        buckets = {
            "EXCELLENT": 0,   # 80–100
            "GOOD":      0,   # 66–79
            "FAIR":      0,   # 50–65
            "POOR":      0,   # 33–49
            "CRITICAL":  0,   # 0–32
        }
        for p in profiles:
            s = p.health.health_score
            if s >= 80:   buckets["EXCELLENT"] += 1
            elif s >= 66: buckets["GOOD"]      += 1
            elif s >= 50: buckets["FAIR"]      += 1
            elif s >= 33: buckets["POOR"]      += 1
            else:         buckets["CRITICAL"]  += 1
        return buckets

    def _country_risk_aggregation(self, profiles: List[SupplierProfile]) -> Dict[str, Any]:
        """
        Per-country risk: revenue-weighted average risk score.
        country_risk = Σ(risk_score × revenue_exposure) / Σ(revenue_exposure) per country
        """
        country_data: Dict[str, Dict[str, float]] = {}
        for p in profiles:
            cc = p.country_code or "UNKNOWN"
            if cc not in country_data:
                country_data[cc] = {"risk_sum": 0.0, "weight_sum": 0.0, "count": 0}
            country_data[cc]["risk_sum"]    += p.risk_score * p.revenue_exposure_pct
            country_data[cc]["weight_sum"]  += p.revenue_exposure_pct
            country_data[cc]["count"]       += 1

        result = {}
        for cc, data in country_data.items():
            w = data["weight_sum"]
            result[cc] = {
                "avg_risk_score":    round(data["risk_sum"] / w, 2) if w > 0 else 0.0,
                "total_exposure":    round(data["weight_sum"], 2),
                "supplier_count":    int(data["count"]),
            }
        return dict(sorted(result.items(), key=lambda x: x[1]["avg_risk_score"], reverse=True))

    def _industry_risk_aggregation(self, profiles: List[SupplierProfile]) -> Dict[str, Any]:
        """Per-industry average risk score (simple mean)."""
        industry_data: Dict[str, Dict[str, float]] = {}
        for p in profiles:
            for ind in (p.industries or []):
                if ind not in industry_data:
                    industry_data[ind] = {"risk_sum": 0.0, "count": 0}
                industry_data[ind]["risk_sum"] += p.risk_score
                industry_data[ind]["count"]    += 1

        return {
            ind: {
                "avg_risk_score": round(d["risk_sum"] / d["count"], 2),
                "supplier_count": int(d["count"]),
            }
            for ind, d in sorted(
                industry_data.items(),
                key=lambda x: x[1]["risk_sum"] / x[1]["count"],
                reverse=True,
            )
        }

    def _critical_alerts(self, profiles: List[SupplierProfile]) -> List[Dict[str, Any]]:
        """
        Generate critical alerts for suppliers requiring immediate attention.
        Alert triggers:
          • health_label == CRITICAL
          • risk_level == CRITICAL
          • Tier 1 supplier with health_score < 50 (POOR or worse)
          • Trend == DECLINING AND health_score < 50
        """
        alerts = []
        for p in profiles:
            reasons = []

            if p.health.health_label == "CRITICAL":
                reasons.append(f"Health score CRITICAL ({p.health.health_score:.1f})")

            if p.risk_level == "CRITICAL":
                reasons.append(f"Risk level CRITICAL (score={p.risk_score:.1f})")

            if p.tier == SupplierTier.TIER_1 and p.health.health_score < 50:
                reasons.append(
                    f"Tier 1 supplier with POOR health ({p.health.health_score:.1f})"
                )

            if p.trend.value == "DECLINING" and p.health.health_score < 50:
                reasons.append(
                    f"Declining trend + health score {p.health.health_score:.1f}"
                )

            if reasons:
                alerts.append({
                    "supplier_id":  p.supplier_id,
                    "name":         p.name,
                    "tier":         p.tier.value,
                    "health_score": p.health.health_score,
                    "risk_level":   p.risk_level,
                    "trend":        p.trend.value,
                    "reasons":      reasons,
                    "severity":     "CRITICAL" if p.risk_level == "CRITICAL" or p.tier == SupplierTier.TIER_1 else "HIGH",
                })

        return sorted(alerts, key=lambda a: a["health_score"])

    def _average_scores(self, profiles: List[SupplierProfile]) -> Dict[str, float]:
        n = len(profiles)
        if n == 0:
            return {}
        return {
            "avg_health":      round(statistics.mean(p.health.health_score    for p in profiles), 2),
            "avg_reliability": round(statistics.mean(p.kpi.reliability_score  for p in profiles), 2),
            "avg_quality":     round(statistics.mean(p.kpi.quality_score      for p in profiles), 2),
            "avg_lead_time":   round(statistics.mean(p.kpi.lead_time_score    for p in profiles), 2),
            "avg_cost_eff":    round(statistics.mean(p.kpi.cost_efficiency    for p in profiles), 2),
            "avg_compliance":  round(statistics.mean(p.kpi.compliance_score   for p in profiles), 2),
            "avg_risk":        round(statistics.mean(p.risk_score             for p in profiles), 2),
            "avg_dependency":  round(statistics.mean(p.dependency_score       for p in profiles), 2),
        }

    def _risk_concentration(self, profiles: List[SupplierProfile]) -> Dict[str, Any]:
        """
        Risk Concentration Index: measures how concentrated the supply chain risk is.
        High concentration = few suppliers hold most of the risk/exposure.

        Herfindahl-Hirschman Index (HHI) on revenue exposure:
          HHI = Σ(revenue_exposure_pct / 100)^2 × 10000
          HHI < 1500 = low concentration
          HHI 1500-2500 = moderate
          HHI > 2500 = high concentration
        """
        total_exposure = sum(p.revenue_exposure_pct for p in profiles)
        if total_exposure <= 0:
            return {"hhi": 0, "level": "UNKNOWN"}

        hhi = sum(
            ((p.revenue_exposure_pct / total_exposure) * 100) ** 2
            for p in profiles
        )
        if hhi < 1500:
            level = "LOW"
        elif hhi < 2500:
            level = "MODERATE"
        else:
            level = "HIGH"

        return {
            "hhi":             round(hhi, 2),
            "level":           level,
            "total_exposure":  round(total_exposure, 2),
            "supplier_count":  len(profiles),
        }

    def _fhi_label(self, fhi: float) -> str:
        if fhi >= 80:  return "EXCELLENT"
        if fhi >= 66:  return "GOOD"
        if fhi >= 50:  return "FAIR"
        if fhi >= 33:  return "POOR"
        return "CRITICAL"

    def _mini(self, p: SupplierProfile) -> Dict[str, Any]:
        return {
            "supplier_id":  p.supplier_id,
            "name":         p.name,
            "tier":         p.tier.value,
            "health_score": p.health.health_score,
            "health_label": p.health.health_label,
            "risk_score":   p.risk_score,
            "rank":         p.rank,
            "trend":        p.trend.value,
        }
