"""
Phase 8: Recommendation Agent — TOPSIS Algorithm

════════════════════════════════════════════════════════════════════════
ALGORITHM: TOPSIS (Technique for Order of Preference by Similarity to
           Ideal Solution) — Hwang & Yoon, 1981
════════════════════════════════════════════════════════════════════════

Given m alternatives (suppliers) and n criteria (KPIs):

STEP 1 — Build Decision Matrix X (m × n):
  x_ij = score of alternative i on criterion j

STEP 2 — Vector Normalisation:
  r_ij = x_ij / √( Σᵢ x_ij² )
  Transforms raw scores into comparable dimensionless values.
  Each column is divided by the Euclidean norm of that column.

STEP 3 — Weighted Normalised Matrix:
  v_ij = w_j × r_ij
  Weights reflect the relative importance of each criterion (sum = 1.0).

STEP 4 — Ideal Best (A⁺) and Ideal Worst (A⁻):
  For BENEFIT criteria (higher is better):
    A⁺_j = max(v_ij)    A⁻_j = min(v_ij)
  For COST criteria (lower is better — e.g. risk_score):
    A⁺_j = min(v_ij)    A⁻_j = max(v_ij)

STEP 5 — Euclidean Separation Distances:
  D⁺_i = √( Σⱼ (v_ij − A⁺_j)² )   (distance from ideal best)
  D⁻_i = √( Σⱼ (v_ij − A⁻_j)² )   (distance from ideal worst)

STEP 6 — Relative Closeness Coefficient (C*):
  C*_i = D⁻_i / (D⁺_i + D⁻_i)

  Interpretation:
    C* = 1.0  → alternative IS the ideal best (perfect)
    C* = 0.0  → alternative IS the ideal worst
    C* > 0.5  → closer to ideal best than ideal worst

STEP 7 — Rank by C* descending (highest = best alternative).
"""

from __future__ import annotations

import math
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.recommendation.models import MCDMCriteria, SupplierCandidate

logger = logging.getLogger("recommendation.topsis")

_EPSILON = 1e-12   # avoid division by zero in normalisation


class TOPSISSolver:
    """
    Pure TOPSIS implementation. Stateless — call solve() for each problem.
    """

    def solve(
        self,
        candidates: List[SupplierCandidate],
        criteria:   List[MCDMCriteria],
    ) -> List[Dict[str, Any]]:
        """
        Run TOPSIS on a list of SupplierCandidates.

        Args:
            candidates: list of SupplierCandidate (m alternatives)
            criteria:   list of MCDMCriteria      (n criteria)

        Returns:
            List of result dicts sorted by topsis_score DESC, each containing:
            {
              "supplier_id":    str,
              "topsis_score":   float (C*, 0–1),
              "d_plus":         float (dist from ideal best),
              "d_minus":        float (dist from ideal worst),
              "rank":           int,
              "weighted_normalized_vector": List[float],
            }
        """
        if not candidates or not criteria:
            return []

        m = len(candidates)
        n = len(criteria)

        # ── STEP 1: Build raw decision matrix ─────────────────────────────────
        matrix: List[List[float]] = []
        for cand in candidates:
            row = self._extract_scores(cand, criteria)
            matrix.append(row)

        logger.debug(f"[TOPSIS] Decision matrix: {m}×{n}")

        # ── STEP 2: Vector normalisation ──────────────────────────────────────
        # Compute Euclidean norm of each column
        col_norms: List[float] = []
        for j in range(n):
            col_sq_sum = sum(matrix[i][j] ** 2 for i in range(m))
            col_norms.append(math.sqrt(col_sq_sum) or _EPSILON)

        # r_ij = x_ij / col_norm_j
        r_matrix: List[List[float]] = [
            [matrix[i][j] / col_norms[j] for j in range(n)]
            for i in range(m)
        ]

        # ── STEP 3: Weighted normalised matrix ────────────────────────────────
        weights = [c.weight for c in criteria]
        v_matrix: List[List[float]] = [
            [r_matrix[i][j] * weights[j] for j in range(n)]
            for i in range(m)
        ]

        # ── STEP 4: Ideal Best (A+) and Ideal Worst (A-) ─────────────────────
        a_plus:  List[float] = []
        a_minus: List[float] = []

        for j, crit in enumerate(criteria):
            col_vals = [v_matrix[i][j] for i in range(m)]
            if crit.is_benefit:
                a_plus.append(max(col_vals))
                a_minus.append(min(col_vals))
            else:
                # Cost criterion: best = minimum, worst = maximum
                a_plus.append(min(col_vals))
                a_minus.append(max(col_vals))

        # ── STEP 5: Euclidean separation distances ────────────────────────────
        d_plus_list:  List[float] = []
        d_minus_list: List[float] = []

        for i in range(m):
            d_plus  = math.sqrt(sum((v_matrix[i][j] - a_plus[j])  ** 2 for j in range(n)))
            d_minus = math.sqrt(sum((v_matrix[i][j] - a_minus[j]) ** 2 for j in range(n)))
            d_plus_list.append(d_plus)
            d_minus_list.append(d_minus)

        # ── STEP 6: Relative closeness coefficient ────────────────────────────
        closeness: List[float] = []
        for i in range(m):
            denom = d_plus_list[i] + d_minus_list[i]
            c_star = d_minus_list[i] / denom if denom > _EPSILON else 0.0
            closeness.append(round(c_star, 6))

        # ── STEP 7: Rank descending ───────────────────────────────────────────
        indexed = sorted(
            enumerate(closeness),
            key=lambda x: x[1],
            reverse=True,
        )

        results = []
        for rank, (i, c_star) in enumerate(indexed, start=1):
            results.append({
                "supplier_id":    candidates[i].supplier_id,
                "name":           candidates[i].name,
                "topsis_score":   c_star,
                "d_plus":         round(d_plus_list[i], 6),
                "d_minus":        round(d_minus_list[i], 6),
                "rank":           rank,
                "weighted_normalized_vector": [round(v, 6) for v in v_matrix[i]],
                "ideal_best":     [round(v, 6) for v in a_plus],
                "ideal_worst":    [round(v, 6) for v in a_minus],
            })

        # Update candidates in-place with topsis_score
        for res in results:
            for cand in candidates:
                if cand.supplier_id == res["supplier_id"]:
                    cand.topsis_score = res["topsis_score"]
                    break

        logger.info(
            f"[TOPSIS] Solved for {m} alternatives, {n} criteria. "
            f"Winner: {results[0]['name']} (C*={results[0]['topsis_score']:.4f})"
        )
        return results

    def _extract_scores(
        self,
        candidate: SupplierCandidate,
        criteria:  List[MCDMCriteria],
    ) -> List[float]:
        """
        Extract the score for each criterion from a SupplierCandidate.
        Maps criterion name → attribute name on the candidate.
        """
        score_map = {
            "health_score":      candidate.health_score,
            "reliability_score": candidate.reliability_score,
            "quality_score":     candidate.quality_score,
            "lead_time_score":   candidate.lead_time_score,
            "cost_efficiency":   candidate.cost_efficiency,
            "compliance_score":  candidate.compliance_score,
            "responsiveness":    candidate.responsiveness,
            "flexibility":       candidate.flexibility,
            "risk_score":        candidate.risk_score,
        }
        return [max(0.0, score_map.get(c.name, 75.0)) for c in criteria]

    def build_comparison_matrix(
        self,
        candidates: List[SupplierCandidate],
        criteria:   List[MCDMCriteria],
    ) -> Dict[str, Any]:
        """
        Returns a comparison matrix dict for API display.
        Shows raw scores per supplier per criterion.
        """
        return {
            "criteria": [c.to_dict() for c in criteria],
            "alternatives": [
                {
                    "supplier_id": cand.supplier_id,
                    "name":        cand.name,
                    "scores":      {c.name: self._extract_scores(cand, criteria)[j]
                                   for j, c in enumerate(criteria)},
                }
                for cand in candidates
            ],
        }
