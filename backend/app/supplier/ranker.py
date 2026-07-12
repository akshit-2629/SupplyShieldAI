"""
Phase 6: Supplier Intelligence — Supplier Ranker

────────────────────────────────────────────────────────────────────────
ALGORITHM: Supplier Ranking (Composite Score Ranking)
────────────────────────────────────────────────────────────────────────

Ranking is a two-pass algorithm:

PASS 1 — Compute a Composite Rank Score for each supplier:
  composite_rank_score = (
      health_score         × 0.50   # primary driver
    + reliability_score    × 0.25   # operational track record
    + (100 - risk_score)   × 0.15   # safety margin (inverted)
    + compliance_score     × 0.10   # regulatory standing
  )

  Weights sum = 1.00.

PASS 2 — Sort by composite_rank_score DESC:
  Rank 1 = highest composite score = "best" supplier.
  Ties broken by: health_score > reliability_score > risk_score (ascending).

Rank Change:
  rank_change = prev_rank - current_rank
  Positive = moved up (improved), Negative = moved down (worsened).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.supplier.models import SupplierProfile

logger = logging.getLogger("supplier.ranker")

# Composite rank score weights
RANK_WEIGHTS = {
    "health":      0.50,
    "reliability": 0.25,
    "risk_inv":    0.15,
    "compliance":  0.10,
}


class SupplierRanker:
    """
    Ranks all supplier profiles by composite rank score.

    Usage:
        ranker = SupplierRanker()
        ranked = ranker.rank(profiles, prev_ranks=prev_rank_map)
    """

    def compute_composite_score(self, profile: SupplierProfile) -> float:
        """
        Composite Rank Score = weighted average of 4 dimensions.

        Formula:
          score = (
              health_score       × 0.50
            + reliability_score  × 0.25
            + (100 - risk_score) × 0.15
            + compliance_score   × 0.10
          )
        """
        health      = profile.health.health_score
        reliability = profile.kpi.reliability_score
        risk_inv    = max(0.0, 100.0 - profile.risk_score)
        compliance  = profile.kpi.compliance_score

        score = (
            health      * RANK_WEIGHTS["health"]
            + reliability * RANK_WEIGHTS["reliability"]
            + risk_inv    * RANK_WEIGHTS["risk_inv"]
            + compliance  * RANK_WEIGHTS["compliance"]
        )
        return round(min(100.0, max(0.0, score)), 4)

    def rank(
        self,
        profiles:    List[SupplierProfile],
        prev_ranks:  Optional[Dict[str, int]] = None,
    ) -> List[SupplierProfile]:
        """
        Assign ranks to all supplier profiles (in-place update + return sorted list).

        Args:
            profiles:   list of SupplierProfile objects
            prev_ranks: {supplier_id: rank} from the previous run (for rank_change)

        Returns:
            List of profiles sorted by rank (rank 1 = best)
        """
        if not profiles:
            return []

        # PASS 1: compute composite scores
        scored: List[tuple] = []
        for profile in profiles:
            composite = self.compute_composite_score(profile)
            scored.append((composite, profile))

        # PASS 2: sort DESC by composite score,
        # tiebreak: health DESC, reliability DESC, risk ASC
        scored.sort(
            key=lambda x: (
                -x[0],
                -x[1].health.health_score,
                -x[1].kpi.reliability_score,
                x[1].risk_score,
            )
        )

        # Assign ranks
        for i, (composite, profile) in enumerate(scored):
            new_rank = i + 1
            profile.metadata["composite_rank_score"] = composite

            if prev_ranks and profile.supplier_id in prev_ranks:
                profile.rank_change = prev_ranks[profile.supplier_id] - new_rank
            else:
                profile.rank_change = 0

            profile.rank = new_rank

        ranked_profiles = [p for _, p in scored]

        logger.info(
            f"[ranker] Ranked {len(ranked_profiles)} suppliers. "
            f"#1: {ranked_profiles[0].name} "
            f"(health={ranked_profiles[0].health.health_score}, "
            f"composite={ranked_profiles[0].metadata.get('composite_rank_score')})"
        )

        return ranked_profiles

    def get_rank_summary(self, profiles: List[SupplierProfile]) -> Dict[str, Any]:
        """
        Returns a compact ranking summary for API responses.
        """
        return {
            "ranked_suppliers": [
                {
                    "rank":            p.rank,
                    "supplier_id":     p.supplier_id,
                    "name":            p.name,
                    "tier":            p.tier.value,
                    "health_score":    p.health.health_score,
                    "health_label":    p.health.health_label,
                    "composite_score": p.metadata.get("composite_rank_score", 0),
                    "risk_score":      p.risk_score,
                    "risk_level":      p.risk_level,
                    "trend":           p.trend.value,
                    "mom_change":      p.mom_change,
                    "rank_change":     p.rank_change,
                    "country_code":    p.country_code,
                }
                for p in profiles
            ],
            "total": len(profiles),
        }
