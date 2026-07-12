"""
RecommendationAgent — Phase 8: Recommendation Agent (REAL implementation)

Replaces RecommendationAgentStub. Runs the full RecommendationPipeline:
  • Identifies at-risk suppliers from Phase 7 inventory projections
  • Loads curated alternative supplier pool for each at-risk supplier
  • Overlays Phase 6 supplier scores for realistic KPI comparison
  • Runs TOPSIS (7-step algorithm) on all alternatives
  • Computes cosine similarity between candidate profiles and ideal vector
  • Applies weighted MCDM composite score = TOPSIS×0.50 + Weighted×0.30 + Cosine×0.20
  • Applies procurement context adjustments (diversification, tier, urgency)
  • Generates rule-based explanations + Gemini-enhanced narratives (if API key)
  • Generates structured ProcurementNote action items (IMMEDIATE_SWITCH / DUAL_SOURCE / QUALIFY / MONITOR)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.orchestrator.state import WorkflowState

logger = logging.getLogger("agent.recommendation")


class RecommendationAgent(BaseAgent):
    """Phase 8 Recommendation Agent — real MCDM implementation."""

    agent_id    = "recommendation_agent"
    description = (
        "Suggests best alternative suppliers using TOPSIS, cosine similarity, and "
        "MCDM. Evaluates candidates across 6 KPI dimensions, applies procurement "
        "context adjustments, and generates actionable procurement notes with "
        "IMMEDIATE_SWITCH / DUAL_SOURCE / QUALIFY / MONITOR guidance."
    )
    version = "1.0.0"

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        from app.recommendation.pipeline import RecommendationPipeline

        supplier_scores       = state.get("supplier_scores", [])
        inventory_projections = state.get("inventory_projections", [])
        execution_id          = state.get("execution_id", "")

        logger.info(
            f"[recommendation_agent] Starting — "
            f"supplier_scores={len(supplier_scores)}, "
            f"inventory_projections={len(inventory_projections)}"
        )

        pipeline = RecommendationPipeline()
        result   = pipeline.run(
            supplier_scores       = supplier_scores,
            inventory_projections = inventory_projections,
            execution_id          = execution_id,
        )

        # Push to API in-memory store
        try:
            from app.api.v1.endpoints.recommendation import update_latest_result
            update_latest_result(result)
        except Exception:
            pass

        # Persist to DB (non-fatal)
        self._persist(result)

        recommendations = result.to_recommendations()

        logger.info(
            f"[recommendation_agent] Done — "
            f"recommendations={len(recommendations)}, "
            f"immediate_switches={result.summary.get('immediate_switches', 0)}, "
            f"revenue_protected=${result.summary.get('total_revenue_protected', 0):,.0f}"
        )

        return {
            "recommendations": recommendations,
            "completed_agents": ["recommendation_agent"],
            "failed_agents":    [],
            "errors":           [],
            "agent_results": [{
                "agent_id": "recommendation_agent",
                "status":   "success",
                "data": {
                    "total_at_risk":          result.total_at_risk,
                    "total_recommendations":   result.summary.get("total_recommendations", 0),
                    "immediate_switches":      result.summary.get("immediate_switches", 0),
                    "total_revenue_protected": result.summary.get("total_revenue_protected", 0),
                },
                "error":       None,
                "duration_ms": 0,
                "retry_count": 0,
                "timestamp":   datetime.now(timezone.utc).isoformat(),
            }],
        }

    def _persist(self, result: Any) -> None:
        """Persist recommendations to PostgreSQL (graceful non-fatal)."""
        try:
            from app.db.session import SessionLocal
            from app.db.models.recommendation import RecommendationRow

            db = SessionLocal()
            try:
                for rec in result.recommendations:
                    top = rec.top_recommendation
                    row = RecommendationRow(
                        at_risk_supplier_id   = rec.at_risk_supplier_id,
                        at_risk_supplier_name = rec.at_risk_supplier_name,
                        execution_id          = result.execution_id,
                        stockout_risk         = rec.stockout_risk,
                        revenue_at_risk_usd   = rec.revenue_at_risk_usd,
                        delay_days            = rec.delay_days,
                        top_supplier_id       = top.supplier_id if top else None,
                        top_supplier_name     = top.name if top else None,
                        top_recommendation_score = top.recommendation_score if top else 0.0,
                        top_topsis_score      = top.topsis_score if top else 0.0,
                        top_cosine_sim        = top.cosine_sim if top else 0.0,
                        top_country_code      = top.country_code if top else None,
                        top_tier              = top.tier if top else None,
                        procurement_action    = rec.procurement_notes[0].action if rec.procurement_notes else None,
                        procurement_priority  = rec.procurement_notes[0].priority if rec.procurement_notes else None,
                        explanation           = rec.explanation,
                        mcdm_ranking          = rec.mcdm_ranking,
                        topsis_ranking        = rec.topsis_ranking,
                    )
                    db.add(row)
                db.commit()
                logger.info(f"[recommendation_agent] Persisted {len(result.recommendations)} rows to DB")
            except Exception as e:
                logger.warning(f"[recommendation_agent] DB persist failed (non-fatal): {e}")
                try:
                    db.rollback()
                except Exception:
                    pass
            finally:
                db.close()
        except ImportError:
            logger.debug("[recommendation_agent] DB model not available — skipping persistence")
