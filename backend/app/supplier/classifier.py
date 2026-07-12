"""
Phase 6: Supplier Intelligence — Tier Classifier

────────────────────────────────────────────────────────────────────────
ALGORITHM: Tier Classification (Multi-Criteria Rule Engine)
────────────────────────────────────────────────────────────────────────

A supplier is classified into one of three tiers based on a priority-
ordered set of rules.

Tier 1 (Strategic/Critical) — ANY of:
  • revenue_exposure_pct > 30%
  • centrality (degree) > 0.20   (single point of failure)
  • blast_radius_size > 5        (disruption affects 5+ downstream nodes)
  • risk_level in (HIGH, CRITICAL) AND revenue_exposure_pct > 15%

Tier 2 (Important) — ANY of:
  • revenue_exposure_pct between 10% and 30%
  • centrality between 0.10 and 0.20
  • blast_radius_size between 2 and 5

Tier 3 (Commodity) — Default when neither Tier 1 nor Tier 2:
  • revenue_exposure_pct < 10%
  • centrality < 0.10
  • blast_radius_size < 2

Classification is deterministic and auditable — every decision includes
a `classification_reason` string explaining which rule fired.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from app.supplier.models import SupplierTier

logger = logging.getLogger("supplier.classifier")


class TierClassifier:
    """
    Classifies each supplier into Tier 1 / 2 / 3 using a priority-ordered
    rule engine. Rules are checked in priority order; first match wins.
    """

    # ── Thresholds ────────────────────────────────────────────────────────────
    TIER1_REVENUE_THRESHOLD    = 30.0    # % spend
    TIER1_CENTRALITY_THRESHOLD = 0.20
    TIER1_BLAST_THRESHOLD      = 5
    TIER1_RISK_REVENUE_COMBO   = 15.0   # revenue threshold for risk+revenue rule

    TIER2_REVENUE_MIN = 10.0
    TIER2_REVENUE_MAX = 30.0
    TIER2_CENTRALITY_MIN = 0.10
    TIER2_CENTRALITY_MAX = 0.20
    TIER2_BLAST_MIN   = 2
    TIER2_BLAST_MAX   = 5

    def classify(
        self,
        supplier_id:          str,
        revenue_exposure_pct: float,
        centrality:           float         = 0.0,
        blast_radius_size:    int           = 0,
        risk_level:           str           = "LOW",
        current_tier:         SupplierTier  = SupplierTier.UNKNOWN,
    ) -> Tuple[SupplierTier, str]:
        """
        Classify a supplier into a tier.

        Returns:
            (SupplierTier, classification_reason)
        """
        high_risk = risk_level in ("HIGH", "CRITICAL")

        # ── Tier 1 rules (checked in priority order) ──────────────────────────
        if revenue_exposure_pct > self.TIER1_REVENUE_THRESHOLD:
            return (
                SupplierTier.TIER_1,
                f"Revenue exposure {revenue_exposure_pct:.1f}% > {self.TIER1_REVENUE_THRESHOLD}% threshold"
            )

        if centrality > self.TIER1_CENTRALITY_THRESHOLD:
            return (
                SupplierTier.TIER_1,
                f"Graph centrality {centrality:.3f} > {self.TIER1_CENTRALITY_THRESHOLD} (SPOF)"
            )

        if blast_radius_size > self.TIER1_BLAST_THRESHOLD:
            return (
                SupplierTier.TIER_1,
                f"Blast radius {blast_radius_size} nodes > {self.TIER1_BLAST_THRESHOLD} threshold"
            )

        if high_risk and revenue_exposure_pct > self.TIER1_RISK_REVENUE_COMBO:
            return (
                SupplierTier.TIER_1,
                f"Risk level {risk_level} + revenue exposure {revenue_exposure_pct:.1f}% > {self.TIER1_RISK_REVENUE_COMBO}%"
            )

        # ── Tier 2 rules ──────────────────────────────────────────────────────
        if self.TIER2_REVENUE_MIN <= revenue_exposure_pct <= self.TIER2_REVENUE_MAX:
            return (
                SupplierTier.TIER_2,
                f"Revenue exposure {revenue_exposure_pct:.1f}% in Tier 2 range [{self.TIER2_REVENUE_MIN}%, {self.TIER2_REVENUE_MAX}%]"
            )

        if self.TIER2_CENTRALITY_MIN <= centrality <= self.TIER2_CENTRALITY_MAX:
            return (
                SupplierTier.TIER_2,
                f"Graph centrality {centrality:.3f} in Tier 2 range [{self.TIER2_CENTRALITY_MIN}, {self.TIER2_CENTRALITY_MAX}]"
            )

        if self.TIER2_BLAST_MIN <= blast_radius_size <= self.TIER2_BLAST_MAX:
            return (
                SupplierTier.TIER_2,
                f"Blast radius {blast_radius_size} nodes in Tier 2 range [{self.TIER2_BLAST_MIN}, {self.TIER2_BLAST_MAX}]"
            )

        # ── Default: Tier 3 ───────────────────────────────────────────────────
        return (
            SupplierTier.TIER_3,
            f"Revenue {revenue_exposure_pct:.1f}%, centrality {centrality:.3f}, blast {blast_radius_size} — all below Tier 2 thresholds"
        )

    def classify_fleet(
        self,
        suppliers: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Classify all suppliers in a fleet.

        Args:
            suppliers: list of dicts with keys:
              supplier_id, revenue_exposure_pct, centrality,
              blast_radius_size, risk_level

        Returns:
            {supplier_id: {"tier": SupplierTier, "reason": str}}
        """
        results: Dict[str, Dict[str, Any]] = {}
        tier_counts = {SupplierTier.TIER_1: 0, SupplierTier.TIER_2: 0, SupplierTier.TIER_3: 0}

        for s in suppliers:
            tier, reason = self.classify(
                supplier_id          = s.get("supplier_id", ""),
                revenue_exposure_pct = s.get("revenue_exposure_pct", 0.0),
                centrality           = s.get("centrality", 0.0),
                blast_radius_size    = s.get("blast_radius_size", 0),
                risk_level           = s.get("risk_level", "LOW"),
            )
            results[s["supplier_id"]] = {"tier": tier, "reason": reason}
            tier_counts[tier] += 1

        logger.info(
            f"[classifier] Fleet classification: "
            f"T1={tier_counts[SupplierTier.TIER_1]}, "
            f"T2={tier_counts[SupplierTier.TIER_2]}, "
            f"T3={tier_counts[SupplierTier.TIER_3]}"
        )
        return results
