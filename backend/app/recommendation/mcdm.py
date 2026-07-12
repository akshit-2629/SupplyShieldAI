"""
Phase 8: Recommendation Agent — MCDM Engine

════════════════════════════════════════════════════════════════════════
ALGORITHM: Multi-Criteria Decision Making (MCDM)
════════════════════════════════════════════════════════════════════════

The MCDMEngine combines three scoring signals into a unified
recommendation_score:

  1. TOPSIS score (C*)      — geometric closeness to ideal solution
  2. Cosine Similarity      — KPI profile similarity
  3. Weighted Criteria Avg  — direct weighted average of normalised criteria

Final Composite Formula:
  recommendation_score = (topsis × 0.50) + (cosine × 0.20) + (weighted × 0.30)

Weight rationale:
  • TOPSIS (50%): Most mathematically rigorous, considers ideal/worst simultaneously
  • Weighted Avg (30%): Direct criterion scoring — intuitive for business users
  • Cosine Sim (20%): Profile compatibility — ensures "drop-in" substitutability

────────────────────────────────────────────────────────────────────────
ALGORITHM: Weighted Criteria Average
────────────────────────────────────────────────────────────────────────
For each candidate i:

  weighted_score_i = Σⱼ ( w_j × normalised_score_ij )

Where:
  w_j               = criterion weight (e.g. 0.25 for health_score)
  normalised_score  = score / 100.0    (puts all criteria on 0–1 scale)
  For COST criteria: normalised = (100 - score) / 100.0  (invert)

  weighted_score ∈ [0.0, 1.0]

────────────────────────────────────────────────────────────────────────
ALGORITHM: Criteria Sensitivity Analysis
────────────────────────────────────────────────────────────────────────
Runs TOPSIS three times with shifted weight distributions:
  scenario A: health-heavy (health=0.40, rest proportional)
  scenario B: cost-heavy   (cost=0.35,  rest proportional)
  scenario C: risk-heavy   (risk=0.35,  rest proportional)

Reports whether the top-ranked candidate changes across scenarios.
Stable top-rank = robust recommendation.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Optional

from app.recommendation.models import MCDMCriteria, SupplierCandidate, DEFAULT_CRITERIA
from app.recommendation.topsis import TOPSISSolver
from app.recommendation.cosine_sim import CosineSimilarityMatcher

logger = logging.getLogger("recommendation.mcdm")

# Composite weight of each signal
COMPOSITE_WEIGHTS = {
    "topsis":  0.50,
    "weighted": 0.30,
    "cosine":  0.20,
}


class MCDMEngine:
    """
    MCDM orchestrator combining TOPSIS + Weighted Avg + Cosine Similarity.
    """

    def __init__(self, criteria: Optional[List[MCDMCriteria]] = None) -> None:
        self.criteria = criteria or DEFAULT_CRITERIA
        self.topsis   = TOPSISSolver()
        self.cosine   = CosineSimilarityMatcher()

    def evaluate(
        self,
        candidates: List[SupplierCandidate],
    ) -> Dict[str, Any]:
        """
        Full MCDM evaluation pipeline.

        Returns:
          {
            "topsis_ranking":  [...],
            "cosine_ranking":  [...],
            "mcdm_ranking":    [...],   ← final composite ranking
            "sensitivity":     {...},
            "criteria":        [...],
            "composite_weights": {...},
          }
        """
        if not candidates:
            return {"error": "No candidates provided"}

        # ── Step A: TOPSIS ────────────────────────────────────────────────────
        topsis_results = self.topsis.solve(
            candidates = candidates,
            criteria   = self.criteria,
        )

        # ── Step B: Cosine Similarity ─────────────────────────────────────────
        ideal_vec     = self.cosine.ideal_vector(candidates)
        cosine_results = self.cosine.rank_by_similarity(candidates, target_vector=ideal_vec)

        # ── Step C: Weighted Criteria Average ─────────────────────────────────
        weighted_scores = self._weighted_avg(candidates)

        # ── Step D: Composite Recommendation Score ────────────────────────────
        for cand in candidates:
            cand.weighted_score     = weighted_scores.get(cand.supplier_id, 0.0)
            cand.recommendation_score = (
                cand.topsis_score  * COMPOSITE_WEIGHTS["topsis"]
                + cand.cosine_sim  * COMPOSITE_WEIGHTS["cosine"]
                + cand.weighted_score * COMPOSITE_WEIGHTS["weighted"]
            )
            cand.recommendation_score = round(cand.recommendation_score, 6)

        # ── Step E: Final MCDM Ranking ────────────────────────────────────────
        candidates_sorted = sorted(
            candidates,
            key=lambda c: c.recommendation_score,
            reverse=True,
        )
        for rank, cand in enumerate(candidates_sorted, start=1):
            cand.rank = rank

        mcdm_ranking = [
            {
                "rank":                 cand.rank,
                "supplier_id":          cand.supplier_id,
                "name":                 cand.name,
                "recommendation_score": round(cand.recommendation_score, 4),
                "topsis_score":         round(cand.topsis_score, 4),
                "cosine_similarity":    round(cand.cosine_sim, 4),
                "weighted_score":       round(cand.weighted_score, 4),
                "country_code":         cand.country_code,
                "tier":                 cand.tier,
                "risk_score":           cand.risk_score,
                "health_score":         cand.health_score,
                "is_current":           cand.is_current,
            }
            for cand in candidates_sorted
        ]

        # ── Step F: Comparison Matrix ─────────────────────────────────────────
        comparison = self.topsis.build_comparison_matrix(candidates, self.criteria)

        # ── Step G: Sensitivity Analysis ─────────────────────────────────────
        sensitivity = self._sensitivity_analysis(candidates)

        return {
            "topsis_ranking":    topsis_results,
            "cosine_ranking":    cosine_results,
            "mcdm_ranking":      mcdm_ranking,
            "comparison_matrix": comparison,
            "sensitivity":       sensitivity,
            "criteria":          [c.to_dict() for c in self.criteria],
            "composite_weights": COMPOSITE_WEIGHTS,
            "ideal_vector":      [round(v, 2) for v in ideal_vec],
        }

    def _weighted_avg(
        self,
        candidates: List[SupplierCandidate],
    ) -> Dict[str, float]:
        """
        Weighted average for each candidate.

        weighted_score = Σ( w_j × normalised_score_ij )
        normalised = score/100 for benefit; (100-score)/100 for cost
        """
        scores: Dict[str, float] = {}
        for cand in candidates:
            total = 0.0
            for crit in self.criteria:
                raw = getattr(cand, crit.name, 75.0)
                if crit.is_benefit:
                    norm = raw / 100.0
                else:
                    norm = (100.0 - raw) / 100.0  # invert cost criterion
                total += crit.weight * norm
            scores[cand.supplier_id] = round(min(1.0, max(0.0, total)), 6)
        return scores

    def _sensitivity_analysis(
        self,
        candidates: List[SupplierCandidate],
    ) -> Dict[str, Any]:
        """
        Runs TOPSIS under 3 alternative weight scenarios to test stability.

        Scenario A (health-heavy): health=0.40, reliability=0.20, rest proportional
        Scenario B (cost-heavy):   cost=0.30, health=0.20, rest proportional
        Scenario C (risk-focus):   risk=0.30, health=0.20, rest proportional
        """
        results = {}

        scenarios = {
            "A_health_heavy": {"health_score": 0.40, "reliability_score": 0.20,
                                "cost_efficiency": 0.10, "lead_time_score": 0.10,
                                "risk_score": 0.10, "compliance_score": 0.10},
            "B_cost_heavy":   {"health_score": 0.15, "reliability_score": 0.15,
                                "cost_efficiency": 0.35, "lead_time_score": 0.15,
                                "risk_score": 0.10, "compliance_score": 0.10},
            "C_risk_focus":   {"health_score": 0.15, "reliability_score": 0.15,
                                "cost_efficiency": 0.10, "lead_time_score": 0.10,
                                "risk_score": 0.40, "compliance_score": 0.10},
        }

        for scenario_name, weight_map in scenarios.items():
            alt_criteria = [
                MCDMCriteria(
                    name       = c.name,
                    weight     = weight_map.get(c.name, c.weight),
                    is_benefit = c.is_benefit,
                )
                for c in self.criteria
            ]
            # Normalise weights to sum = 1.0
            total_w = sum(c.weight for c in alt_criteria)
            if total_w > 0:
                for c in alt_criteria:
                    c.weight = round(c.weight / total_w, 4)

            # Deep-copy candidates to avoid mutating originals
            cands_copy = copy.deepcopy(candidates)
            topsis_alt = TOPSISSolver().solve(cands_copy, alt_criteria)

            if topsis_alt:
                results[scenario_name] = {
                    "top_supplier":   topsis_alt[0]["name"],
                    "top_score":      topsis_alt[0]["topsis_score"],
                    "weights_used":   {c.name: c.weight for c in alt_criteria},
                    "ranking":        [{"rank": r["rank"], "name": r["name"],
                                        "score": r["topsis_score"]}
                                       for r in topsis_alt[:3]],
                }

        # Determine stability: does the same supplier win all 3 scenarios?
        top_names = {v["top_supplier"] for v in results.values()}
        stable = len(top_names) == 1

        return {
            "scenarios":      results,
            "is_stable":      stable,
            "stable_winner":  list(top_names)[0] if stable else None,
            "disagreement":   list(top_names) if not stable else [],
        }
