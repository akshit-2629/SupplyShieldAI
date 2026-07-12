"""
Phase 8: Recommendation Agent — Recommendation Pipeline

Orchestrates the complete recommendation workflow for all at-risk suppliers:

  Step 1: Identify at-risk suppliers from Phase 7 (CRITICAL + HIGH stockout risk)
  Step 2: For each at-risk supplier, load its alternative pool from ALTERNATIVE_POOL
  Step 3: Overlay Phase 6 supplier scores for candidates already in fleet
  Step 4: Build SupplierCandidate objects (current + alternatives)
  Step 5: Run MCDMEngine (TOPSIS + Cosine + Weighted Avg → composite score)
  Step 6: Apply RecommendationRanker (diversification bonus, tier adj, urgency)
  Step 7: Generate explanation via RecommendationExplainer
  Step 8: Generate structured ProcurementNote action items
  Step 9: Build RecommendationResult for each at-risk supplier
  Step 10: Return RecommendationPipelineResult
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.recommendation.cosine_sim import CosineSimilarityMatcher
from app.recommendation.explainer import RecommendationExplainer
from app.recommendation.mcdm import MCDMEngine
from app.recommendation.models import (
    ALTERNATIVE_POOL,
    DEFAULT_CRITERIA,
    RecommendationResult,
    SupplierCandidate,
)
from app.recommendation.ranker import RecommendationRanker

logger = logging.getLogger("recommendation.pipeline")


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RecommendationPipelineResult:
    recommendations: List[RecommendationResult]
    summary:         Dict[str, Any]
    execution_id:    str = ""
    evaluated_at:    str = ""
    total_at_risk:   int = 0

    def to_recommendations(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.recommendations]


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────────────

class RecommendationPipeline:
    """
    Runs the full MCDM-based recommendation pipeline.
    """

    def __init__(self) -> None:
        self.mcdm      = MCDMEngine(criteria=DEFAULT_CRITERIA)
        self.ranker    = RecommendationRanker()
        self.explainer = RecommendationExplainer()
        self.cosine    = CosineSimilarityMatcher()

    def run(
        self,
        supplier_scores:      Optional[List[Dict[str, Any]]] = None,
        inventory_projections: Optional[List[Dict[str, Any]]] = None,
        execution_id:         str = "",
    ) -> RecommendationPipelineResult:

        evaluated_at = datetime.now(timezone.utc).isoformat()

        # ── Step 1: Identify at-risk suppliers ───────────────────────────────
        at_risk_items = self._identify_at_risk(inventory_projections or [])

        if not at_risk_items:
            # If no CRITICAL/HIGH from Phase 7, run recommendations for all
            # suppliers with score < 85 using supplier_scores from Phase 6
            at_risk_items = self._fallback_at_risk(supplier_scores or [])

        # Build supplier score lookup from Phase 6
        score_lookup = {
            s["supplier_id"]: s
            for s in (supplier_scores or [])
        }

        # ── Steps 2–9: Evaluate each at-risk supplier ─────────────────────────
        recommendations: List[RecommendationResult] = []
        for item in at_risk_items:
            try:
                rec = self._evaluate_one(item, score_lookup)
                recommendations.append(rec)
            except Exception as e:
                logger.warning(f"[recommendation_pipeline] Skipping {item.get('supplier_id')}: {e}")

        # ── Step 10: Summary ───────────────────────────────────────────────────
        immediate_switches = sum(
            1 for rec in recommendations
            for note in rec.procurement_notes
            if note.action == "IMMEDIATE_SWITCH"
        )
        total_revenue_protected = sum(
            rec.revenue_at_risk_usd for rec in recommendations
            if rec.top_recommendation is not None
        )

        summary = {
            "total_at_risk":        len(at_risk_items),
            "total_recommendations": len(recommendations),
            "immediate_switches":   immediate_switches,
            "total_revenue_protected": round(total_revenue_protected, 2),
            "execution_id":         execution_id,
            "evaluated_at":         evaluated_at,
        }

        logger.info(
            f"[recommendation_pipeline] Done — "
            f"at_risk={len(at_risk_items)}, recs={len(recommendations)}, "
            f"immediate_switches={immediate_switches}"
        )

        return RecommendationPipelineResult(
            recommendations = recommendations,
            summary         = summary,
            execution_id    = execution_id,
            evaluated_at    = evaluated_at,
            total_at_risk   = len(at_risk_items),
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _evaluate_one(
        self,
        at_risk_item:  Dict[str, Any],
        score_lookup:  Dict[str, Any],
    ) -> RecommendationResult:
        """
        Run the full MCDM pipeline for one at-risk supplier.
        """
        supplier_id   = at_risk_item["supplier_id"]
        supplier_name = at_risk_item["supplier_name"]
        stockout_risk = at_risk_item.get("stockout_risk", "MEDIUM")
        rev_at_risk   = float(at_risk_item.get("revenue_at_risk_usd", 0.0))
        delay_days    = float(at_risk_item.get("delay_days", 0.0))
        days_remaining = float(at_risk_item.get("days_remaining", 99.0))
        lead_time     = int(at_risk_item.get("lead_time_days", 30))
        country_code  = at_risk_item.get("country_code", "")

        # ── Step 2: Build current supplier candidate ──────────────────────────
        current_candidate = self._build_candidate(
            supplier_id  = supplier_id,
            supplier_name = supplier_name,
            score_data   = score_lookup.get(supplier_id, {}),
            is_current   = True,
            country_code = country_code,
        )

        # ── Step 3: Load alternative pool ─────────────────────────────────────
        alt_pool_data = ALTERNATIVE_POOL.get(supplier_id, [])
        if not alt_pool_data:
            # Try partial match
            for key in ALTERNATIVE_POOL:
                if supplier_id.lower() in key.lower() or key.lower() in supplier_id.lower():
                    alt_pool_data = ALTERNATIVE_POOL[key]
                    break

        # Build alternative candidates
        alt_candidates: List[SupplierCandidate] = []
        for alt_data in alt_pool_data:
            # Overlay Phase 6 data if the alt is in the fleet
            overlay = score_lookup.get(alt_data["supplier_id"], {})
            cand = self._build_candidate_from_pool(alt_data, overlay)
            alt_candidates.append(cand)

        if not alt_candidates:
            logger.warning(f"[recommendation_pipeline] No alternatives for {supplier_id} — using generic pool")
            alt_candidates = self._generic_alternatives(current_candidate)

        # All candidates = alternatives (current not included in MCDM ranking)
        all_candidates = alt_candidates

        # ── Steps 4–5: MCDM evaluation ────────────────────────────────────────
        mcdm_result = self.mcdm.evaluate(all_candidates)

        # ── Step 6: Ranker adjustments ────────────────────────────────────────
        ranked = self.ranker.rank(
            candidates        = all_candidates,
            at_risk_country   = country_code,
            at_risk_tier      = at_risk_item.get("tier", "TIER_3"),
            days_remaining    = days_remaining,
            at_risk_lead_time = lead_time,
            is_critical       = stockout_risk == "CRITICAL",
        )

        top = ranked[0] if ranked else None

        # ── Build result ──────────────────────────────────────────────────────
        result = RecommendationResult(
            at_risk_supplier_id   = supplier_id,
            at_risk_supplier_name = supplier_name,
            risk_reason           = f"Stockout risk: {stockout_risk}. Days remaining: {days_remaining:.0f}d vs lead time: {lead_time}d",
            stockout_risk         = stockout_risk,
            revenue_at_risk_usd   = rev_at_risk,
            delay_days            = delay_days,
            candidates            = [current_candidate] + ranked,
            top_recommendation    = top,
            topsis_ranking        = mcdm_result.get("topsis_ranking", []),
            cosine_ranking        = mcdm_result.get("cosine_ranking", []),
            mcdm_ranking          = mcdm_result.get("mcdm_ranking", []),
            comparison_matrix     = {
                "criteria":    mcdm_result.get("criteria", []),
                "sensitivity": mcdm_result.get("sensitivity", {}),
                "comparison":  self.ranker.build_comparison_table(ranked[:5], current_candidate),
            },
            evaluated_at = evaluated_at,
        )

        # ── Steps 7–8: Explanation + procurement notes ────────────────────────
        result.procurement_notes = self.explainer.generate_procurement_notes(result)
        result.explanation       = self.explainer.explain(result)

        return result

    def _build_candidate(
        self,
        supplier_id:   str,
        supplier_name: str,
        score_data:    Dict[str, Any],
        is_current:    bool = False,
        country_code:  str = "",
    ) -> SupplierCandidate:
        """Build a SupplierCandidate from Phase 6 score data."""
        health = score_data.get("health", {}) or {}
        kpi    = score_data.get("kpi", {}) or {}
        return SupplierCandidate(
            supplier_id       = supplier_id,
            name              = supplier_name,
            country_code      = score_data.get("country_code", country_code) or country_code,
            tier              = score_data.get("tier", "TIER_3"),
            industries        = score_data.get("industries", []),
            is_current        = is_current,
            health_score      = float(health.get("health_score", score_data.get("health_score", 75.0))),
            reliability_score = float(kpi.get("reliability_score", score_data.get("reliability_score", 75.0))),
            quality_score     = float(kpi.get("quality_score",     score_data.get("quality_score", 75.0))),
            lead_time_score   = float(kpi.get("lead_time_score",   score_data.get("lead_time_score", 75.0))),
            cost_efficiency   = float(kpi.get("cost_efficiency",   score_data.get("cost_efficiency", 75.0))),
            compliance_score  = float(kpi.get("compliance_score",  score_data.get("compliance_score", 75.0))),
            responsiveness    = float(kpi.get("responsiveness",    score_data.get("responsiveness", 75.0))),
            flexibility       = float(kpi.get("flexibility",       score_data.get("flexibility", 75.0))),
            risk_score        = float(score_data.get("risk_score", 0.0)),
            revenue_exposure_pct = float(score_data.get("revenue_exposure_pct", 5.0)),
        )

    def _build_candidate_from_pool(
        self,
        pool_data: Dict[str, Any],
        overlay:   Dict[str, Any],
    ) -> SupplierCandidate:
        """Build a SupplierCandidate from alternative pool data with optional Phase 6 overlay."""
        health  = overlay.get("health", {}) or {}
        kpi     = overlay.get("kpi", {}) or {}
        return SupplierCandidate(
            supplier_id       = pool_data["supplier_id"],
            name              = pool_data["name"],
            country_code      = pool_data.get("country_code", "US"),
            tier              = pool_data.get("tier", "TIER_3"),
            industries        = pool_data.get("industries", []),
            is_current        = False,
            health_score      = float(health.get("health_score", pool_data.get("health_score", 75.0))),
            reliability_score = float(kpi.get("reliability_score", pool_data.get("reliability_score", 75.0))),
            quality_score     = float(kpi.get("quality_score",    pool_data.get("quality_score", 75.0))),
            lead_time_score   = float(kpi.get("lead_time_score",  pool_data.get("lead_time_score", 75.0))),
            cost_efficiency   = float(kpi.get("cost_efficiency",  pool_data.get("cost_efficiency", 75.0))),
            compliance_score  = float(kpi.get("compliance_score", pool_data.get("compliance_score", 75.0))),
            responsiveness    = float(kpi.get("responsiveness",   pool_data.get("responsiveness", 75.0))),
            flexibility       = float(kpi.get("flexibility",      pool_data.get("flexibility", 75.0))),
            risk_score        = float(overlay.get("risk_score",   pool_data.get("risk_score", 0.0))),
            revenue_exposure_pct = float(pool_data.get("revenue_exposure_pct", 0.0)),
        )

    def _identify_at_risk(
        self,
        inventory_projections: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Extract CRITICAL and HIGH risk suppliers from Phase 7 projections.
        """
        at_risk = []
        for proj in inventory_projections:
            stockout = proj.get("stockout", {}) or {}
            item     = proj.get("item",    {}) or {}
            revenue  = proj.get("revenue_impact", {}) or {}
            delay    = proj.get("manufacturing_delay", {}) or {}

            risk = stockout.get("stockout_risk", "SAFE")
            if risk in ("CRITICAL", "HIGH"):
                at_risk.append({
                    "supplier_id":      item.get("supplier_id", ""),
                    "supplier_name":    item.get("supplier_name", ""),
                    "stockout_risk":    risk,
                    "days_remaining":   stockout.get("days_remaining", 99.0),
                    "lead_time_days":   item.get("lead_time_days", 30),
                    "revenue_at_risk_usd": revenue.get("revenue_lost_usd", 0.0),
                    "delay_days":       delay.get("delay_days", 0.0),
                    "country_code":     item.get("metadata", {}).get("risk_overlay", {}).get("country_code", ""),
                    "tier":             item.get("metadata", {}).get("risk_overlay", {}).get("supplier_tier", "TIER_3"),
                })

        # Deduplicate by supplier_id (take worst risk per supplier)
        seen: Dict[str, Dict] = {}
        for item in at_risk:
            sid = item["supplier_id"]
            if sid not in seen or item["stockout_risk"] == "CRITICAL":
                seen[sid] = item
        return list(seen.values())

    def _fallback_at_risk(
        self,
        supplier_scores: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        When no inventory projections available, use Phase 6 supplier data
        and flag any supplier with health < 85 as needing a recommendation.
        """
        at_risk = []
        for s in supplier_scores:
            health = s.get("health", {}) or {}
            h_score = float(health.get("health_score", s.get("health_score", 100.0)))
            if h_score < 88.0:
                at_risk.append({
                    "supplier_id":      s["supplier_id"],
                    "supplier_name":    s.get("name", s["supplier_id"]),
                    "stockout_risk":    "MEDIUM",
                    "days_remaining":   60.0,
                    "lead_time_days":   30,
                    "revenue_at_risk_usd": 0.0,
                    "delay_days":       0.0,
                    "country_code":     s.get("country_code", ""),
                    "tier":             s.get("tier", "TIER_3"),
                })
        return at_risk[:6]  # cap at 6 for performance

    def _generic_alternatives(
        self,
        current: SupplierCandidate,
    ) -> List[SupplierCandidate]:
        """
        Fallback: generate 3 synthetic alternatives with slightly varied profiles.
        Used when no alternatives are in the pool.
        """
        alts = []
        deltas = [(5, -3), (-2, 8), (8, -5)]
        for i, (health_d, cost_d) in enumerate(deltas):
            alts.append(SupplierCandidate(
                supplier_id       = f"generic::ALT_{i+1}",
                name              = f"Alternative Supplier {i+1}",
                country_code      = "US",
                tier              = "TIER_2",
                health_score      = min(100, max(0, current.health_score + health_d)),
                reliability_score = min(100, max(0, current.reliability_score + health_d * 0.5)),
                quality_score     = min(100, max(0, current.quality_score + health_d * 0.3)),
                lead_time_score   = min(100, max(0, current.lead_time_score + cost_d * 0.5)),
                cost_efficiency   = min(100, max(0, current.cost_efficiency + cost_d)),
                compliance_score  = min(100, max(0, current.compliance_score + 2)),
                responsiveness    = min(100, max(0, current.responsiveness + health_d * 0.4)),
                flexibility       = min(100, max(0, current.flexibility + cost_d * 0.4)),
                risk_score        = max(0, current.risk_score - 5),
            ))
        return alts
