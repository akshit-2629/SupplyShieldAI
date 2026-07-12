"""
Phase 8: Recommendation Agent — Cosine Similarity Matcher

════════════════════════════════════════════════════════════════════════
ALGORITHM: Cosine Similarity
════════════════════════════════════════════════════════════════════════

For two supplier feature vectors A and B (each 8-dimensional):

  cosine_similarity(A, B) = (A · B) / (‖A‖ × ‖B‖)

Where:
  A · B   = Σᵢ (Aᵢ × Bᵢ)       (dot product)
  ‖A‖    = √(Σᵢ Aᵢ²)            (Euclidean magnitude)
  ‖B‖    = √(Σᵢ Bᵢ²)

Interpretation:
  sim = 1.0  → identical performance profile
  sim = 0.0  → orthogonal (completely different profile)
  sim > 0.85 → strong substitute candidate

Feature Vector (8-dimensional, all on 0–100 scale):
  [health, reliability, quality, lead_time, cost, compliance, responsiveness, flexibility]

Usage in Phase 8:
  1. Build feature vector for the "ideal supplier" (all criteria at best
     score among the fleet, or user-defined target)
  2. Compute cosine similarity of each candidate vs the ideal vector
  3. Rank candidates by similarity descending
  4. High similarity → candidate's KPI profile closely matches what we need

Why Cosine vs. Euclidean?
  Cosine similarity measures PROFILE SHAPE (direction), not magnitude.
  A supplier with scores [60,60,60,60,60,60,60,60] and one with
  [80,80,80,80,80,80,80,80] have cosine similarity = 1.0 (same profile,
  different scale). This is useful for "similar type of supplier" matching.
"""

from __future__ import annotations

import math
import logging
from typing import Any, Dict, List, Optional

from app.recommendation.models import SupplierCandidate

logger = logging.getLogger("recommendation.cosine_sim")

_EPSILON = 1e-12


class CosineSimilarityMatcher:
    """
    Computes cosine similarity between supplier feature vectors.

    Supports:
      - Similarity to an explicit ideal vector
      - Pairwise similarity between candidates
      - Top-N most similar alternatives
    """

    def cosine_similarity(
        self,
        vec_a: List[float],
        vec_b: List[float],
    ) -> float:
        """
        cosine_similarity(A, B) = (A · B) / (‖A‖ × ‖B‖)

        Returns value in [0.0, 1.0].
        Handles zero-vectors gracefully (returns 0.0).
        """
        if len(vec_a) != len(vec_b):
            raise ValueError(f"Vector length mismatch: {len(vec_a)} vs {len(vec_b)}")

        dot_product  = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a  = math.sqrt(sum(a ** 2 for a in vec_a))
        magnitude_b  = math.sqrt(sum(b ** 2 for b in vec_b))

        denominator  = magnitude_a * magnitude_b
        if denominator < _EPSILON:
            return 0.0

        similarity = dot_product / denominator
        return round(min(1.0, max(0.0, similarity)), 6)

    def ideal_vector(
        self,
        candidates: List[SupplierCandidate],
    ) -> List[float]:
        """
        Build the ideal feature vector = maximum score in each dimension
        across all candidates.

        For cost dimensions (risk_score), this naturally produces the lowest
        risk — but since risk is not in the feature vector, all dimensions
        here are benefit-oriented.
        """
        if not candidates:
            return [100.0] * 8

        n = len(candidates[0].feature_vector())
        ideal = []
        for j in range(n):
            max_val = max(cand.feature_vector()[j] for cand in candidates)
            ideal.append(max_val)
        return ideal

    def rank_by_similarity(
        self,
        candidates:    List[SupplierCandidate],
        target_vector: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rank all candidates by cosine similarity to a target vector.

        Args:
            candidates:    list of SupplierCandidate
            target_vector: if None, uses the ideal_vector (best in pool)

        Returns:
            List of {supplier_id, name, cosine_similarity, rank} dicts,
            sorted by cosine_similarity DESC.
        """
        if not candidates:
            return []

        target = target_vector if target_vector is not None else self.ideal_vector(candidates)

        results = []
        for cand in candidates:
            sim = self.cosine_similarity(cand.feature_vector(), target)
            results.append({
                "supplier_id":        cand.supplier_id,
                "name":               cand.name,
                "cosine_similarity":  sim,
                "feature_vector":     [round(v, 2) for v in cand.feature_vector()],
            })
            cand.cosine_sim = sim

        results.sort(key=lambda x: x["cosine_similarity"], reverse=True)

        for rank, res in enumerate(results, start=1):
            res["rank"] = rank

        logger.info(
            f"[CosineSim] Ranked {len(results)} candidates. "
            f"Top: {results[0]['name']} (sim={results[0]['cosine_similarity']:.4f})"
        )
        return results

    def pairwise_similarity_matrix(
        self,
        candidates: List[SupplierCandidate],
    ) -> Dict[str, Any]:
        """
        Compute full pairwise similarity matrix between all candidates.
        Useful for API display and clustering.

        Returns:
          {
            "suppliers": [supplier_id, ...],
            "matrix":    [[sim_ij, ...], ...],
          }
        """
        n = len(candidates)
        matrix = []
        for i in range(n):
            row = []
            for j in range(n):
                sim = self.cosine_similarity(
                    candidates[i].feature_vector(),
                    candidates[j].feature_vector(),
                )
                row.append(round(sim, 4))
            matrix.append(row)

        return {
            "suppliers": [c.supplier_id for c in candidates],
            "names":     [c.name for c in candidates],
            "matrix":    matrix,
        }

    def find_closest_alternatives(
        self,
        at_risk:    SupplierCandidate,
        pool:       List[SupplierCandidate],
        top_n:      int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find the top N alternatives most similar to the at-risk supplier's
        KPI profile. These are the easiest "drop-in" substitutes.

        Args:
            at_risk:  the supplier we need to replace
            pool:     list of alternative candidates
            top_n:    how many to return

        Returns:
            Sorted list of {supplier_id, name, cosine_similarity, rank}
        """
        target = at_risk.feature_vector()
        results = self.rank_by_similarity(pool, target_vector=target)
        return results[:top_n]
