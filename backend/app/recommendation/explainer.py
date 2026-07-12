"""
Phase 8: Recommendation Agent — Explanation Generator

Generates human-readable procurement recommendations and explanations
based on MCDM scores, algorithm outputs, and inventory context.

Two modes:
  1. Rule-based (always available, deterministic)
  2. Gemini-enhanced (calls Gemini 1.5 Flash if API key is configured)
     Falls back to rule-based if Gemini is unavailable.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from app.recommendation.models import (
    ProcurementNote,
    RecommendationResult,
    SupplierCandidate,
)

logger = logging.getLogger("recommendation.explainer")


class RecommendationExplainer:
    """
    Generates human-readable procurement explanations.

    Priority:
      1. If GEMINI_API_KEY is set, attempt Gemini 1.5 Flash
      2. Fallback: deterministic rule-based explanation
    """

    def explain(self, result: RecommendationResult) -> str:
        """
        Generate a full natural-language explanation for a recommendation.
        """
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key:
            try:
                return self._gemini_explanation(result, gemini_key)
            except Exception as e:
                logger.warning(f"[explainer] Gemini failed ({e}), using rule-based fallback")

        return self._rule_based_explanation(result)

    def generate_procurement_notes(
        self,
        result:   RecommendationResult,
        top_n:    int = 3,
    ) -> List[ProcurementNote]:
        """
        Generate structured procurement action items.

        Action types:
          IMMEDIATE_SWITCH  — CRITICAL risk, best alternative available
          DUAL_SOURCE       — HIGH risk, qualified alternative available
          QUALIFY           — MEDIUM risk, candidate needs qualification
          MONITOR           — LOW/SAFE, continue monitoring
        """
        notes = []
        candidates = result.candidates[:top_n]

        for cand in candidates:
            if cand.is_current:
                continue

            risk = result.stockout_risk
            rev  = result.revenue_at_risk_usd

            if risk == "CRITICAL":
                action   = "IMMEDIATE_SWITCH"
                priority = "CRITICAL"
                timeline = "Within 7 days"
                impact   = "Critical — stockout imminent"
                reasoning = [
                    f"Current supplier ({result.at_risk_supplier_name}) has CRITICAL stockout risk",
                    f"Days remaining: {result.delay_days:.0f}d — below lead time threshold",
                    f"Revenue at risk: ${rev:,.0f}",
                    f"{cand.name} ranked #{cand.rank} by TOPSIS (C*={cand.topsis_score:.3f})",
                    f"MCDM recommendation score: {cand.recommendation_score:.3f}",
                ]
                note_text = (
                    f"URGENT: Initiate immediate supplier switch to {cand.name} ({cand.country_code}). "
                    f"TOPSIS closeness coefficient {cand.topsis_score:.3f} qualifies as the strongest "
                    f"alternative. Cosine similarity {cand.cosine_sim:.3f} confirms comparable KPI profile. "
                    f"Estimated ${rev:,.0f} revenue protected by switching within 7 days."
                )

            elif risk == "HIGH":
                action   = "DUAL_SOURCE"
                priority = "HIGH"
                timeline = "Within 14 days"
                impact   = "High — safety buffer exhausted"
                reasoning = [
                    f"Current supplier at HIGH stockout risk (safety buffer exhausted)",
                    f"{cand.name} has TOPSIS score {cand.topsis_score:.3f} vs current supplier",
                    f"Recommend dual-sourcing: 60% current / 40% {cand.name}",
                    f"Weighted criteria score: {cand.weighted_score:.3f}",
                ]
                note_text = (
                    f"Begin dual-sourcing with {cand.name} ({cand.country_code}). "
                    f"Allocate 40% of volume to this alternative while maintaining current supplier. "
                    f"MCDM analysis shows recommendation score {cand.recommendation_score:.3f}. "
                    f"Run parallel qualification within 14 days."
                )

            elif risk == "MEDIUM":
                action   = "QUALIFY"
                priority = "MEDIUM"
                timeline = "Within 30 days"
                impact   = "Medium — approaching risk zone"
                reasoning = [
                    f"Current supplier approaching risk threshold",
                    f"{cand.name} is a strong backup with TOPSIS score {cand.topsis_score:.3f}",
                    f"Initiate supplier qualification process",
                    f"Cost efficiency delta: {cand.cost_efficiency - 75:.1f} points vs average",
                ]
                note_text = (
                    f"Begin qualification of {cand.name} ({cand.country_code}) as contingency supplier. "
                    f"TOPSIS analysis ranks it #{cand.rank} among {len(result.candidates)} alternatives. "
                    f"Complete supplier audit within 30 days."
                )

            else:
                action   = "MONITOR"
                priority = "LOW"
                timeline = "Quarterly review"
                impact   = "Low — informational"
                reasoning = [
                    f"{cand.name} identified as preferred alternative if needed",
                    f"Maintain in approved supplier list",
                ]
                note_text = (
                    f"Add {cand.name} ({cand.country_code}) to approved alternative supplier list. "
                    f"MCDM score: {cand.recommendation_score:.3f}. Review quarterly."
                )

            notes.append(ProcurementNote(
                priority    = priority,
                action      = action,
                supplier_id = cand.supplier_id,
                note        = note_text,
                reasoning   = reasoning,
                timeline    = timeline,
                impact      = impact,
            ))

        return notes

    # ── Private helpers ───────────────────────────────────────────────────────

    def _rule_based_explanation(self, result: RecommendationResult) -> str:
        top = result.top_recommendation
        if not top:
            return "No suitable alternatives found in the current supplier pool."

        lines = [
            f"## Supplier Recommendation: {result.at_risk_supplier_name}",
            "",
            f"**Risk Status:** {result.stockout_risk}",
            f"**Revenue at Risk:** ${result.revenue_at_risk_usd:,.0f}",
            f"**Manufacturing Delay:** {result.delay_days:.0f} days",
            "",
            f"### Top Alternative: {top.name} ({top.country_code}) — Rank #{top.rank}",
            "",
            "**MCDM Analysis Results:**",
            f"- TOPSIS Closeness (C*): {top.topsis_score:.4f} — "
            + ("Strong alternative" if top.topsis_score > 0.6 else "Moderate alternative"),
            f"- Cosine Similarity:      {top.cosine_sim:.4f} — "
            + ("High KPI profile match" if top.cosine_sim > 0.95 else "Moderate profile match"),
            f"- Weighted Criteria:      {top.weighted_score:.4f}",
            f"- **Composite Score:      {top.recommendation_score:.4f}**",
            "",
            "**Criteria Comparison vs Current Supplier:**",
        ]

        if result.candidates:
            current = next((c for c in result.candidates if c.is_current), None)
            if current:
                for attr, label in [
                    ("health_score",      "Health Score"),
                    ("reliability_score", "Reliability"),
                    ("cost_efficiency",   "Cost Efficiency"),
                    ("lead_time_score",   "Lead Time Score"),
                    ("risk_score",        "Risk Score (↓ better)"),
                    ("compliance_score",  "Compliance"),
                ]:
                    current_val = getattr(current, attr, 0.0)
                    alt_val     = getattr(top, attr, 0.0)
                    diff        = alt_val - current_val
                    arrow = "✅ +" if diff > 0 else ("❌ " if diff < 0 else "→ ")
                    lines.append(f"  {label:25s} Current: {current_val:.1f}  →  Alternative: {alt_val:.1f}  {arrow}{abs(diff):.1f}")

        lines += [
            "",
            "**Sensitivity Analysis:**",
        ]

        if result.comparison_matrix.get("sensitivity"):
            sens = result.comparison_matrix["sensitivity"]
            if sens.get("is_stable"):
                lines.append(f"  ✅ Recommendation is STABLE across all 3 weight scenarios. "
                             f"Winner: {sens.get('stable_winner', top.name)}")
            else:
                lines.append(f"  ⚠️ Recommendation varies across weight scenarios: {sens.get('disagreement', [])}")

        lines += [
            "",
            "**Procurement Action:**",
        ]
        for note in result.procurement_notes[:1]:
            lines.append(f"  [{note.priority}] {note.action}: {note.note}")

        return "\n".join(lines)

    def _gemini_explanation(self, result: RecommendationResult, api_key: str) -> str:
        """
        Call Gemini 1.5 Flash to generate a business-grade narrative explanation.
        Falls back gracefully if the API is unavailable.
        """
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        top = result.top_recommendation
        if not top:
            return self._rule_based_explanation(result)

        prompt = f"""You are a supply chain risk analyst at a Fortune 500 company.

Generate a concise, professional procurement recommendation (150-200 words) based on this analysis:

AT-RISK SUPPLIER:
- Name: {result.at_risk_supplier_name}
- Stockout Risk: {result.stockout_risk}
- Revenue at Risk: ${result.revenue_at_risk_usd:,.0f}
- Manufacturing Delay: {result.delay_days:.0f} days

TOP ALTERNATIVE (MCDM Analysis):
- Name: {top.name} ({top.country_code})
- TOPSIS Score (C*): {top.topsis_score:.4f}
- Cosine Similarity: {top.cosine_sim:.4f}
- Composite Recommendation Score: {top.recommendation_score:.4f}
- Health Score: {top.health_score:.1f}
- Reliability: {top.reliability_score:.1f}
- Risk Score: {top.risk_score:.1f}
- Tier: {top.tier}

Include: urgency assessment, why this alternative was selected, key tradeoffs, and recommended action.
Format as a professional business memo paragraph. No markdown headers.
"""

        response = model.generate_content(prompt)
        return response.text.strip()
