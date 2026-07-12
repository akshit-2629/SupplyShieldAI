"""
SupplierAgent — Phase 6: Supplier Intelligence Agent (REAL implementation)

Replaces SupplierAgentStub. Runs the full SupplierPipeline:
  1. Build profiles from seed topology (12 suppliers)
  2. Overlay Phase 4 risk_assessments (country/industry risk)
  3. Overlay Phase 5 graph_snapshot (centrality, blast radius)
  4. Score all 7 KPI dimensions + composite health score
  5. Classify Tier 1/2/3 by revenue exposure + centrality
  6. Track MoM trend history
  7. Rank all suppliers by composite score
  8. Aggregate fleet-wide statistics
  9. Persist to supplier_scores DB table
  10. Return supplier_scores to WorkflowState

Data contract (WorkflowState.supplier_scores):
  [
    {
      "supplier_id":          str,
      "name":                 str,
      "country_code":         str,
      "tier":                 "TIER_1" | "TIER_2" | "TIER_3",
      "industries":           List[str],
      "revenue_exposure_pct": float,
      "kpi":                  { reliability, quality, lead_time, cost, compliance, responsiveness, flexibility },
      "health":               { health_score, health_label, component breakdown, formula },
      "risk_score":           float,
      "risk_level":           str,
      "geo_risk":             float,
      "industry_risk":        float,
      "dependency_score":     float,
      "centrality":           float,
      "products_supplied":    int,
      "blast_radius_size":    int,
      "rank":                 int,
      "rank_change":          int,
      "trend":                str,
      "mom_change":           float,
      "evaluated_at":         str (ISO),
    }
  ]
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.orchestrator.state import WorkflowState

logger = logging.getLogger("agent.supplier")


class SupplierAgent(BaseAgent):
    """
    Phase 6 Supplier Intelligence Agent.

    Consumes:
      - state["risk_assessments"]  (Phase 4 output)
      - state["graph_snapshot"]    (Phase 5 output)

    Produces:
      - state["supplier_scores"]   (ranked + profiled suppliers for Phase 7)
    """

    agent_id    = "supplier_agent"
    description = (
        "Evaluates all suppliers across 7 KPI dimensions (reliability, quality, "
        "lead time, cost, compliance, responsiveness, flexibility). "
        "Applies Phase 4 risk overlay and Phase 5 graph dependency overlay. "
        "Classifies Tier 1/2/3, tracks MoM trends, ranks by composite health score, "
        "and aggregates fleet-wide statistics."
    )
    version = "1.0.0"

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        from app.supplier.pipeline import SupplierPipeline

        risk_assessments: List[Dict[str, Any]] = state.get("risk_assessments", [])
        graph_snapshot:   Dict[str, Any]        = state.get("graph_snapshot", {})
        execution_id:     str                   = state.get("execution_id", "")

        logger.info(
            f"[supplier_agent] Starting — "
            f"risk_assessments={len(risk_assessments)}, "
            f"graph_ready={bool(graph_snapshot)}"
        )

        pipeline = SupplierPipeline()
        result   = pipeline.run(
            risk_assessments = risk_assessments,
            graph_snapshot   = graph_snapshot,
            execution_id     = execution_id,
        )

        # Push result to the API in-memory store so endpoints respond immediately
        try:
            from app.api.v1.endpoints.supplier import update_latest_result
            update_latest_result(result)
        except Exception:
            pass

        # Persist to DB (non-fatal)
        self._persist_scores(result)

        supplier_scores = result.to_supplier_scores()

        logger.info(
            f"[supplier_agent] Done — "
            f"scored={result.total_scored}, "
            f"FHI={result.summary.get('fleet_health_index', 0):.1f}, "
            f"alerts={result.summary.get('critical_alerts', 0)}, "
            f"#1={result.summary.get('top_supplier', 'N/A')}"
        )

        return {
            "supplier_scores":  supplier_scores,
            "completed_agents": ["supplier_agent"],
            "failed_agents":    [],
            "errors":           [],
            "agent_results": [{
                "agent_id": "supplier_agent",
                "status":   "success",
                "data": {
                    "total_scored":        result.total_scored,
                    "fleet_health_index":  result.summary.get("fleet_health_index", 0),
                    "tier_1_count":        result.summary.get("tier_1_count", 0),
                    "tier_2_count":        result.summary.get("tier_2_count", 0),
                    "tier_3_count":        result.summary.get("tier_3_count", 0),
                    "critical_alerts":     result.summary.get("critical_alerts", 0),
                    "top_supplier":        result.summary.get("top_supplier", "N/A"),
                    "aggregation_summary": {
                        "health_distribution": result.aggregation.get("health_distribution", {}),
                        "risk_concentration":  result.aggregation.get("risk_concentration", {}),
                    },
                },
                "error":       None,
                "duration_ms": 0,
                "retry_count": 0,
                "timestamp":   datetime.now(timezone.utc).isoformat(),
            }],
        }

    def _persist_scores(self, result: Any) -> None:
        """Persist supplier scores to PostgreSQL (graceful non-fatal)."""
        try:
            from app.db.session import SessionLocal
            from app.db.models.supplier_score import SupplierScore

            db = SessionLocal()
            try:
                for profile in result.profiles:
                    row = SupplierScore(
                        supplier_id          = profile.supplier_id,
                        execution_id         = result.execution_id,
                        name                 = profile.name,
                        country_code         = profile.country_code,
                        tier                 = profile.tier.value,
                        revenue_exposure_pct = profile.revenue_exposure_pct,
                        health_score         = profile.health.health_score,
                        health_label         = profile.health.health_label,
                        reliability_score    = profile.kpi.reliability_score,
                        quality_score        = profile.kpi.quality_score,
                        lead_time_score      = profile.kpi.lead_time_score,
                        cost_efficiency      = profile.kpi.cost_efficiency,
                        compliance_score     = profile.kpi.compliance_score,
                        responsiveness       = profile.kpi.responsiveness,
                        flexibility          = profile.kpi.flexibility,
                        risk_score           = profile.risk_score,
                        risk_level           = profile.risk_level,
                        geo_risk             = profile.geo_risk,
                        industry_risk        = profile.industry_risk,
                        dependency_score     = profile.dependency_score,
                        centrality           = profile.centrality,
                        blast_radius_size    = profile.blast_radius_size,
                        products_supplied    = profile.products_supplied,
                        rank                 = profile.rank,
                        rank_change          = profile.rank_change,
                        trend                = profile.trend.value,
                        mom_change           = profile.mom_change,
                        formula_breakdown    = profile.health.formula_breakdown,
                    )
                    db.add(row)
                db.commit()
                logger.info(f"[supplier_agent] Persisted {result.total_scored} rows to DB")
            except Exception as e:
                logger.warning(f"[supplier_agent] DB persist failed (non-fatal): {e}")
                try:
                    db.rollback()
                except Exception:
                    pass
            finally:
                db.close()
        except ImportError:
            logger.debug("[supplier_agent] DB model not available — skipping persistence")
