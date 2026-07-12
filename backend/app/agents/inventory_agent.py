"""
InventoryAgent — Phase 7: Inventory Impact Agent (REAL implementation)

Replaces InventoryAgentStub. Runs the full InventoryPipeline:
  • Loads 10 seed components from the Phase 5 supply chain topology
  • Overlays Phase 4 risk scores, Phase 5 graph data, Phase 6 supplier health
  • Computes days_remaining, safety stock, reorder point for each component
  • Predicts stockout risk with exponential probability model
  • Calculates revenue impact (days_short × daily × margin_per_unit)
  • Generates manufacturing delay timelines (delay × 1.5 recovery factor)
  • Aggregates fleet inventory health (value-weighted average)
  • Persists results to inventory_projections DB table

Data contract (WorkflowState.inventory_projections):
  [
    {
      "evaluated_at":   str (ISO),
      "item":           { component_id, supplier_id, stock levels, KPIs },
      "stockout":       { days_remaining, stockout_risk, probability, date },
      "revenue_impact": { days_short, units_short, revenue_lost_usd },
      "manufacturing_delay": { delay_days, recovery_days, affected_products },
    }
  ]
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.orchestrator.state import WorkflowState

logger = logging.getLogger("agent.inventory")


class InventoryAgent(BaseAgent):
    """Phase 7 Inventory Impact Agent — real implementation."""

    agent_id    = "inventory_agent"
    description = (
        "Predicts inventory stockouts and revenue impact from upstream supply disruptions. "
        "Computes days_remaining = stock / daily_consumption, safety stock via Z×σ×√LT formula, "
        "exponential stockout probability, revenue impact = units_short × margin, "
        "and manufacturing delay timelines with 1.5× recovery factor."
    )
    version = "1.0.0"

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        from app.inventory.pipeline import InventoryPipeline

        risk_assessments: List[Dict[str, Any]] = state.get("risk_assessments", [])
        supplier_scores:  List[Dict[str, Any]] = state.get("supplier_scores", [])
        graph_snapshot:   Dict[str, Any]        = state.get("graph_snapshot", {})
        execution_id:     str                   = state.get("execution_id", "")

        logger.info(
            f"[inventory_agent] Starting — "
            f"risk_assessments={len(risk_assessments)}, "
            f"supplier_scores={len(supplier_scores)}, "
            f"graph_ready={bool(graph_snapshot)}"
        )

        pipeline = InventoryPipeline()
        result   = pipeline.run(
            risk_assessments = risk_assessments,
            supplier_scores  = supplier_scores,
            graph_snapshot   = graph_snapshot,
            execution_id     = execution_id,
        )

        # Push to API in-memory store
        try:
            from app.api.v1.endpoints.inventory import update_latest_result
            update_latest_result(result)
        except Exception:
            pass

        # Persist to DB (non-fatal)
        self._persist(result)

        inventory_projections = result.to_inventory_projections()

        logger.info(
            f"[inventory_agent] Done — "
            f"items={result.total_items}, "
            f"FIH={result.summary.get('fleet_inventory_health', 0):.1f}, "
            f"CRITICAL={result.summary.get('critical_count', 0)}, "
            f"revenue_at_risk=${result.summary.get('total_revenue_at_risk', 0):,.0f}"
        )

        return {
            "inventory_projections": inventory_projections,
            "completed_agents": ["inventory_agent"],
            "failed_agents":    [],
            "errors":           [],
            "agent_results": [{
                "agent_id": "inventory_agent",
                "status":   "success",
                "data": {
                    "total_items":            result.total_items,
                    "fleet_inventory_health": result.summary.get("fleet_inventory_health", 0),
                    "fleet_health_label":     result.summary.get("fleet_health_label", "UNKNOWN"),
                    "critical_count":         result.summary.get("critical_count", 0),
                    "high_risk_count":        result.summary.get("high_risk_count", 0),
                    "total_revenue_at_risk":  result.summary.get("total_revenue_at_risk", 0),
                    "total_financial_impact": result.summary.get("total_financial_impact", 0),
                    "alert_count":            result.summary.get("alert_count", 0),
                },
                "error":       None,
                "duration_ms": 0,
                "retry_count": 0,
                "timestamp":   datetime.now(timezone.utc).isoformat(),
            }],
        }

    def _persist(self, result: Any) -> None:
        """Persist projections to PostgreSQL (graceful non-fatal)."""
        try:
            from app.db.session import SessionLocal
            from app.db.models.inventory_projection import InventoryProjectionRow

            db = SessionLocal()
            try:
                for proj in result.projections:
                    row = InventoryProjectionRow(
                        component_id           = proj.item.component_id,
                        component_name         = proj.item.component_name,
                        supplier_id            = proj.item.supplier_id,
                        execution_id           = result.execution_id,
                        current_stock          = proj.item.current_stock,
                        daily_consumption      = proj.item.daily_consumption,
                        safety_stock           = proj.item.safety_stock,
                        reorder_point          = proj.item.reorder_point,
                        lead_time_days         = proj.item.lead_time_days,
                        days_remaining         = proj.stockout.days_remaining,
                        safety_stock_days      = proj.stockout.safety_stock_days,
                        stockout_risk          = proj.stockout.stockout_risk.value,
                        stockout_probability   = proj.stockout.stockout_probability,
                        stockout_date          = proj.stockout.stockout_date,
                        inventory_health_score = proj.stockout.inventory_health_score,
                        inventory_health_label = proj.stockout.inventory_health_label,
                        coverage_ratio         = proj.stockout.coverage_ratio,
                        days_short             = proj.revenue.days_short,
                        units_short            = proj.revenue.units_short,
                        revenue_lost_usd       = proj.revenue.revenue_lost_usd,
                        cogs_at_risk_usd       = proj.revenue.cogs_at_risk_usd,
                        delay_days             = proj.delay.delay_days,
                        recovery_days          = proj.delay.recovery_days,
                        delay_severity         = proj.delay.severity,
                        affected_products      = proj.item.used_in_products,
                        formula_breakdown      = proj.stockout.formula_breakdown,
                    )
                    db.add(row)
                db.commit()
                logger.info(f"[inventory_agent] Persisted {result.total_items} rows to DB")
            except Exception as e:
                logger.warning(f"[inventory_agent] DB persist failed (non-fatal): {e}")
                try:
                    db.rollback()
                except Exception:
                    pass
            finally:
                db.close()
        except ImportError:
            logger.debug("[inventory_agent] DB model not available — skipping persistence")
