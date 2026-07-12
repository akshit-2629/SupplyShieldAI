"""
Phase 6: Supplier Intelligence — Supplier Pipeline

Orchestrates the full supplier evaluation workflow for every run:

  1. Load supplier seed data (topology from Phase 5 SEED_SUPPLIERS)
  2. Overlay Phase 4 risk_assessments → update risk_score, geo_risk, industry_risk per country/industry
  3. Overlay Phase 5 graph_snapshot → update centrality, dependency_score, blast_radius_size
  4. Score each supplier (WeightedKPIScorer)
  5. Apply geo + industry risk overlay (adjusts health score)
  6. Classify each supplier into Tier 1/2/3 (TierClassifier)
  7. Record history + compute MoM trend (HistoricalTracker)
  8. Rank all suppliers (SupplierRanker)
  9. Aggregate fleet-wide statistics (FleetAggregator)
  10. Return SupplierPipelineResult

SupplierPipelineResult contains:
  • profiles:        List[SupplierProfile]   — all 12 scored suppliers
  • ranked:          List[SupplierProfile]   — sorted by rank
  • aggregation:     Dict                    — fleet-wide stats
  • summary:         Dict                    — quick KPIs for API
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.supplier.aggregator import FleetAggregator
from app.supplier.classifier import TierClassifier
from app.supplier.history import historical_tracker
from app.supplier.models import (
    SEED_SUPPLIERS,
    KPIScore,
    PerformanceTrend,
    SupplierProfile,
    SupplierTier,
)
from app.supplier.ranker import SupplierRanker
from app.supplier.scorer import WeightedKPIScorer

logger = logging.getLogger("supplier.pipeline")


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SupplierPipelineResult:
    profiles:     List[SupplierProfile]
    ranked:       List[SupplierProfile]
    aggregation:  Dict[str, Any]
    summary:      Dict[str, Any]
    execution_id: str = ""
    evaluated_at: str = ""
    total_scored: int = 0

    def to_supplier_scores(self) -> List[Dict[str, Any]]:
        """Serialise ranked profiles to WorkflowState.supplier_scores format."""
        return [p.to_dict() for p in self.ranked]


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────────────

class SupplierPipeline:
    """
    Full supplier evaluation pipeline for Phase 6.

    Usage:
        pipeline = SupplierPipeline()
        result = pipeline.run(
            risk_assessments = state["risk_assessments"],
            graph_snapshot   = state["graph_snapshot"],
            execution_id     = state["execution_id"],
        )
    """

    def __init__(self) -> None:
        self.scorer     = WeightedKPIScorer()
        self.classifier = TierClassifier()
        self.ranker     = SupplierRanker()
        self.aggregator = FleetAggregator()

    def run(
        self,
        risk_assessments: Optional[List[Dict[str, Any]]] = None,
        graph_snapshot:   Optional[Dict[str, Any]]       = None,
        execution_id:     str                            = "",
    ) -> SupplierPipelineResult:
        """Run the full pipeline and return a SupplierPipelineResult."""

        evaluated_at = datetime.now(timezone.utc).isoformat()

        # ── Step 1: Build base profiles from seed ─────────────────────────────
        profiles = self._build_base_profiles()

        # ── Step 2: Overlay Phase 4 risk data ────────────────────────────────
        risk_map = self._build_risk_map(risk_assessments or [])
        for p in profiles:
            self._apply_risk_overlay(p, risk_map)

        # ── Step 3: Overlay Phase 5 graph data ───────────────────────────────
        graph_map = self._build_graph_map(graph_snapshot or {})
        for p in profiles:
            self._apply_graph_overlay(p, graph_map)

        # ── Step 4 & 5: Score each supplier ──────────────────────────────────
        for p in profiles:
            health = self.scorer.score_health(
                kpi              = p.kpi,
                risk_score       = p.risk_score,
                dependency_score = p.dependency_score,
            )
            # Apply geo + industry risk overlay on raw health
            adjusted_health = self.scorer.apply_risk_overlay(
                base_score    = health.health_score,
                geo_risk      = p.geo_risk,
                industry_risk = p.industry_risk,
            )
            health.health_score  = adjusted_health
            health.health_label  = self.scorer._health_label(adjusted_health)
            health.formula_breakdown["geo_industry_overlay"] = {
                "geo_risk":       p.geo_risk,
                "industry_risk":  p.industry_risk,
                "pre_overlay":    health.formula_breakdown.get("reliability_raw", 0),
                "post_overlay":   adjusted_health,
            }
            p.health      = health
            p.evaluated_at = evaluated_at

        # ── Step 6: Classify tiers ────────────────────────────────────────────
        for p in profiles:
            tier, reason = self.classifier.classify(
                supplier_id          = p.supplier_id,
                revenue_exposure_pct = p.revenue_exposure_pct,
                centrality           = p.centrality,
                blast_radius_size    = p.blast_radius_size,
                risk_level           = p.risk_level,
            )
            p.tier = tier
            p.metadata["tier_reason"] = reason

        # ── Step 7: Record history + MoM trend ───────────────────────────────
        for p in profiles:
            trend_data = historical_tracker.record(
                supplier_id       = p.supplier_id,
                health_score      = p.health.health_score,
                risk_score        = p.risk_score,
                reliability_score = p.kpi.reliability_score,
            )
            p.trend      = trend_data["trend"]
            p.mom_change = trend_data["mom_change"]
            p.prev_health = trend_data.get("prev_health")
            p.metadata["history"] = {
                "streak":           trend_data.get("streak", 1),
                "peak_score":       trend_data.get("peak_score"),
                "trough_score":     trend_data.get("trough_score"),
                "distance_from_peak": trend_data.get("distance_from_peak"),
                "snapshot_count":   trend_data.get("snapshot_count", 1),
            }

        # ── Step 8: Rank ──────────────────────────────────────────────────────
        ranked = self.ranker.rank(profiles)

        # ── Step 9: Aggregate ─────────────────────────────────────────────────
        aggregation = self.aggregator.aggregate(profiles)

        # ── Step 10: Build summary ────────────────────────────────────────────
        summary = {
            "total_scored":      len(profiles),
            "fleet_health_index": aggregation["fleet_health_index"],
            "fleet_health_label": aggregation["fleet_health_label"],
            "tier_1_count":      aggregation["tier_distribution"].get("TIER_1", {}).get("count", 0),
            "tier_2_count":      aggregation["tier_distribution"].get("TIER_2", {}).get("count", 0),
            "tier_3_count":      aggregation["tier_distribution"].get("TIER_3", {}).get("count", 0),
            "critical_alerts":   aggregation["alert_count"],
            "top_supplier":      ranked[0].name if ranked else "N/A",
            "top_supplier_score": ranked[0].health.health_score if ranked else 0.0,
            "execution_id":      execution_id,
            "evaluated_at":      evaluated_at,
        }

        logger.info(
            f"[supplier_pipeline] Done — "
            f"scored={len(profiles)}, FHI={aggregation['fleet_health_index']:.1f}, "
            f"alerts={aggregation['alert_count']}, #1={ranked[0].name if ranked else 'N/A'}"
        )

        return SupplierPipelineResult(
            profiles     = profiles,
            ranked       = ranked,
            aggregation  = aggregation,
            summary      = summary,
            execution_id = execution_id,
            evaluated_at = evaluated_at,
            total_scored = len(profiles),
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_base_profiles(self) -> List[SupplierProfile]:
        profiles = []
        for seed in SEED_SUPPLIERS:
            kpi = KPIScore(**seed["kpi"])
            p   = SupplierProfile(
                supplier_id          = seed["supplier_id"],
                name                 = seed["name"],
                country_code         = seed["country_code"],
                revenue_exposure_pct = seed["revenue_exposure_pct"],
                industries           = seed.get("industries", []),
                kpi                  = kpi,
            )
            profiles.append(p)
        return profiles

    def _build_risk_map(self, risk_assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build a lookup map from Phase 4 risk assessments.
        key: country code (ISO-2) → {"risk_score": max, "risk_level": highest, "geo_multiplier": max}
        key: industry tag         → {"risk_score": max, "industry_multiplier": max}
        """
        country_risk: Dict[str, Dict] = {}
        industry_risk: Dict[str, Dict] = {}

        for ra in risk_assessments:
            rs    = float(ra.get("risk_score", 0.0))
            level = ra.get("risk_level", "LOW")
            geo   = ra.get("geo_risk", {}) or {}
            ind   = ra.get("industry_risk", {}) or {}

            for cc in (ra.get("countries") or []):
                cc = cc.upper()
                existing = country_risk.get(cc, {"risk_score": 0.0, "risk_level": "LOW", "geo_multiplier": 1.0})
                if rs > existing["risk_score"]:
                    country_risk[cc] = {
                        "risk_score":    rs,
                        "risk_level":    level,
                        "geo_multiplier": float(geo.get("max_multiplier", 1.0)),
                    }

            for industry in (ra.get("industries") or []):
                existing = industry_risk.get(industry, {"risk_score": 0.0, "industry_multiplier": 1.0})
                if rs > existing["risk_score"]:
                    industry_risk[industry] = {
                        "risk_score":          rs,
                        "industry_multiplier": float(ind.get("max_multiplier", 1.0)),
                    }

        return {"country": country_risk, "industry": industry_risk}

    def _apply_risk_overlay(self, profile: SupplierProfile, risk_map: Dict) -> None:
        """Apply Phase 4 risk scores to a supplier profile."""
        country_data = risk_map["country"].get(profile.country_code.upper(), {})
        if country_data:
            profile.risk_score  = max(profile.risk_score, country_data["risk_score"] * 0.70)
            profile.geo_risk    = max(1.0, country_data.get("geo_multiplier", 1.0))
            profile.risk_level  = self._score_to_level(profile.risk_score)

        # Industry risk — take max across all industries of this supplier
        for ind in profile.industries:
            ind_data = risk_map["industry"].get(ind, {})
            if ind_data:
                profile.risk_score   = max(profile.risk_score, ind_data["risk_score"] * 0.50)
                profile.industry_risk = max(profile.industry_risk, ind_data.get("industry_multiplier", 1.0))
                profile.risk_level   = self._score_to_level(profile.risk_score)

    def _build_graph_map(self, graph_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Extract per-supplier graph data from Phase 5 snapshot."""
        centrality_data: Dict[str, Any] = {}

        centrality = graph_snapshot.get("centrality", {})
        for node in (centrality.get("top_nodes") or []):
            nid = node.get("node_id", "")
            centrality_data[nid] = {
                "centrality":   node.get("centrality", 0.0),
                "in_degree":    node.get("in_degree", 0),
                "out_degree":   node.get("out_degree", 0),
            }

        blast = graph_snapshot.get("blast_radius_report", {})
        blast_sizes: Dict[str, int] = {}
        for report in (blast.get("blast_radius_reports") or []):
            nid = report.get("disrupted_node", "")
            blast_sizes[nid] = report.get("total_nodes_impacted", 0)

        products_map: Dict[str, int] = {}
        for report in (blast.get("blast_radius_reports") or []):
            nid = report.get("disrupted_node", "")
            products = sum(
                1 for n in (report.get("direct_impacts", []) + report.get("indirect_impacts", []))
                if n.get("node_type") == "product"
            )
            products_map[nid] = products

        return {
            "centrality":    centrality_data,
            "blast_sizes":   blast_sizes,
            "products_map":  products_map,
        }

    def _apply_graph_overlay(self, profile: SupplierProfile, graph_map: Dict) -> None:
        """Apply Phase 5 graph metrics to a supplier profile."""
        nid = profile.supplier_id

        cent_data = graph_map["centrality"].get(nid, {})
        if cent_data:
            profile.centrality       = cent_data.get("centrality", 0.0)
            profile.dependency_score = round(profile.centrality * 100, 2)

        profile.blast_radius_size = graph_map["blast_sizes"].get(nid, 0)
        profile.products_supplied = graph_map["products_map"].get(nid, 0)

    def _score_to_level(self, score: float) -> str:
        if score >= 85:  return "CRITICAL"
        if score >= 67:  return "HIGH"
        if score >= 33:  return "MEDIUM"
        return "LOW"
