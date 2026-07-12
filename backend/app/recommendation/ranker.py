"""
Phase 8: Recommendation Agent — Recommendation Ranker

════════════════════════════════════════════════════════════════════════
ALGORITHM: Weighted Ranking (Final Procurement Score)
════════════════════════════════════════════════════════════════════════

After TOPSIS, Cosine, and Weighted Avg are computed by MCDMEngine, the
RecommendationRanker applies procurement-context adjustments:

1. Country Diversification Bonus:
   If top candidate is in a DIFFERENT country from the at-risk supplier,
   add +0.03 to recommendation_score (diversification premium).

   Rationale: Geographic diversification reduces systemic risk.

2. Tier Penalty:
   TIER_1 candidates get a small bonus (+0.02) — they have proven scale.
   TIER_3 unknown candidates get a small penalty (-0.01).

3. Lead Time Urgency Adjustment:
   If days_remaining < lead_time (critical shortage), weight lead_time_score
   by +0.10 extra in the final sort — urgency demands fast suppliers.

4. Final Score = recommendation_score + diversification_bonus + tier_adj + urgency_adj

5. Rank by final_score DESC.

────────────────────────────────────────────────────────────────────────
Country Comparison:
  Identifies geographic risk concentration. If all top-3 alternatives
  are in the same country as the at-risk supplier → warns of concentration.

────────────────────────────────────────────────────────────────────────
Cost Comparison:
  Reports: cost_efficiency delta between at-risk and top alternative.
  cost_delta = candidate.cost_efficiency - current.cost_efficiency
  Positive = alternative is cheaper. Negative = alternative is pricier.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.recommendation.models import SupplierCandidate

logger = logging.getLogger("recommendation.ranker")


class RecommendationRanker:
    """
    Applies procurement-context adjustments on top of MCDM scores
    and produces the final ranked list with comparison tables.
    """

    TIER_BONUS = {"TIER_1": 0.02, "TIER_2": 0.00, "TIER_3": -0.01}
    DIVERSIFICATION_BONUS = 0.03
    URGENCY_LEAD_WEIGHT   = 0.10

    def rank(
        self,
        candidates:          List[SupplierCandidate],
        at_risk_country:     str  = "",
        at_risk_tier:        str  = "TIER_3",
        days_remaining:      float = 999.0,
        at_risk_lead_time:   int   = 30,
        is_critical:         bool  = False,
    ) -> List[SupplierCandidate]:
        """
        Final ranked list with procurement adjustments.

        Args:
            candidates:        MCDM-scored candidates (mutable, updated in-place)
            at_risk_country:   ISO-2 country code of the at-risk supplier
            at_risk_tier:      tier of at-risk supplier
            days_remaining:    days before stockout (from Phase 7)
            at_risk_lead_time: lead time of the at-risk supplier
            is_critical:       True if stockout_risk == CRITICAL

        Returns:
            Candidates sorted by adjusted final score, rank updated in-place.
        """
        for cand in candidates:
            adj = cand.recommendation_score   # start from MCDM composite

            # 1. Country Diversification Bonus
            if (at_risk_country
                    and cand.country_code
                    and cand.country_code.upper() != at_risk_country.upper()):
                adj += self.DIVERSIFICATION_BONUS
                cand.metadata["diversification_bonus"] = True
            else:
                cand.metadata["diversification_bonus"] = False

            # 2. Tier Adjustment
            tier_adj = self.TIER_BONUS.get(cand.tier, 0.0)
            adj += tier_adj
            cand.metadata["tier_adjustment"] = tier_adj

            # 3. Lead Time Urgency Adjustment (critical shortages)
            if is_critical and days_remaining < at_risk_lead_time:
                lead_norm = cand.lead_time_score / 100.0
                urgency_adj = lead_norm * self.URGENCY_LEAD_WEIGHT
                adj += urgency_adj
                cand.metadata["urgency_adjustment"] = round(urgency_adj, 4)
            else:
                cand.metadata["urgency_adjustment"] = 0.0

            cand.metadata["final_adjusted_score"] = round(min(1.0, max(0.0, adj)), 6)

        # Sort by adjusted score
        ranked = sorted(
            candidates,
            key=lambda c: c.metadata.get("final_adjusted_score", c.recommendation_score),
            reverse=True,
        )

        for i, cand in enumerate(ranked):
            cand.rank = i + 1

        logger.info(
            f"[ranker] Final ranking — #1: {ranked[0].name} "
            f"(adj_score={ranked[0].metadata.get('final_adjusted_score', 0):.4f})"
            if ranked else "[ranker] Empty candidate list"
        )
        return ranked

    def build_comparison_table(
        self,
        candidates:    List[SupplierCandidate],
        at_risk:       Optional[SupplierCandidate] = None,
    ) -> Dict[str, Any]:
        """
        Builds a side-by-side comparison table for API display.

        Compares each candidate against the at-risk supplier on:
          health, reliability, cost, lead_time, compliance, risk, country, tier
        """
        def delta(val_alt: float, val_current: float, is_benefit: bool = True) -> Dict:
            diff = val_alt - val_current
            pct  = round((diff / max(val_current, 0.001)) * 100, 1)
            better = diff > 0 if is_benefit else diff < 0
            return {"delta": round(diff, 2), "delta_pct": pct, "better": better}

        rows = []
        for cand in candidates:
            row: Dict[str, Any] = {
                "rank":         cand.rank,
                "supplier_id":  cand.supplier_id,
                "name":         cand.name,
                "country_code": cand.country_code,
                "tier":         cand.tier,
                "recommendation_score": round(cand.recommendation_score, 4),
                "topsis_score": round(cand.topsis_score, 4),
                "cosine_sim":   round(cand.cosine_sim, 4),
                "scores": {
                    "health":      cand.health_score,
                    "reliability": cand.reliability_score,
                    "quality":     cand.quality_score,
                    "lead_time":   cand.lead_time_score,
                    "cost":        cand.cost_efficiency,
                    "compliance":  cand.compliance_score,
                    "risk":        cand.risk_score,
                },
            }
            if at_risk:
                row["vs_current"] = {
                    "health":      delta(cand.health_score,      at_risk.health_score),
                    "reliability": delta(cand.reliability_score, at_risk.reliability_score),
                    "quality":     delta(cand.quality_score,     at_risk.quality_score),
                    "lead_time":   delta(cand.lead_time_score,   at_risk.lead_time_score),
                    "cost":        delta(cand.cost_efficiency,   at_risk.cost_efficiency),
                    "compliance":  delta(cand.compliance_score,  at_risk.compliance_score),
                    "risk":        delta(cand.risk_score,        at_risk.risk_score, is_benefit=False),
                    "country_same": cand.country_code.upper() == at_risk.country_code.upper(),
                    "tier_up":     cand.tier < at_risk.tier,   # TIER_1 < TIER_2 alphabetically
                }
            rows.append(row)

        # Country concentration warning
        top3_countries = [c.country_code.upper() for c in candidates[:3]]
        at_risk_country = at_risk.country_code.upper() if at_risk else ""
        concentration_warning = all(cc == at_risk_country for cc in top3_countries)

        return {
            "at_risk_supplier": at_risk.to_dict() if at_risk else None,
            "alternatives":     rows,
            "concentration_warning": concentration_warning,
            "top3_countries":   top3_countries,
        }
