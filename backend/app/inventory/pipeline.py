"""
Phase 7: Inventory Impact — Inventory Pipeline

Orchestrates the full inventory analysis workflow:

  Step 1:  Load seed inventory items (10 components from Phase 5 topology)
  Step 2:  Enrich each item with Phase 4 risk, Phase 5 graph, Phase 6 supplier overlays
  Step 3:  Compute safety_stock and reorder_point for each item
  Step 4:  Run InventoryCalculator.project() → StockoutPrediction per item
  Step 5:  Compute RevenueImpact per item
  Step 6:  Compute ManufacturingDelay per item
  Step 7:  Build InventoryProjection (combines steps 4–6)
  Step 8:  Run InventoryForecaster.fleet_forecast() → fleet aggregation
  Step 9:  Build critical alerts (CRITICAL + HIGH risk items)
  Step 10: Return InventoryPipelineResult
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.inventory.calculator import InventoryCalculator
from app.inventory.forecaster import InventoryForecaster
from app.inventory.mapper import InventoryMapper
from app.inventory.models import (
    SEED_INVENTORY,
    InventoryItem,
    InventoryProjection,
    StockoutRisk,
)

logger = logging.getLogger("inventory.pipeline")


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class InventoryPipelineResult:
    projections:    List[InventoryProjection]
    fleet_forecast: Dict[str, Any]
    alerts:         List[Dict[str, Any]]
    summary:        Dict[str, Any]
    execution_id:   str = ""
    evaluated_at:   str = ""
    total_items:    int = 0

    def to_inventory_projections(self) -> List[Dict[str, Any]]:
        """Serialise projections to WorkflowState.inventory_projections format."""
        return [p.to_dict() for p in self.projections]


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────────────

class InventoryPipeline:
    """
    Full inventory evaluation pipeline for Phase 7.

    Usage:
        pipeline = InventoryPipeline()
        result = pipeline.run(
            risk_assessments = state["risk_assessments"],
            supplier_scores  = state["supplier_scores"],
            graph_snapshot   = state["graph_snapshot"],
            execution_id     = state["execution_id"],
        )
    """

    def __init__(self) -> None:
        self.calculator = InventoryCalculator()
        self.forecaster = InventoryForecaster()
        self.mapper     = InventoryMapper()

    def run(
        self,
        risk_assessments: Optional[List[Dict[str, Any]]] = None,
        supplier_scores:  Optional[List[Dict[str, Any]]] = None,
        graph_snapshot:   Optional[Dict[str, Any]]       = None,
        execution_id:     str                            = "",
    ) -> InventoryPipelineResult:

        evaluated_at = datetime.now(timezone.utc).isoformat()

        # ── Step 1 + 2: Load and enrich seed items ────────────────────────────
        items = self._build_items(
            risk_assessments = risk_assessments or [],
            supplier_scores  = supplier_scores  or [],
            graph_snapshot   = graph_snapshot   or {},
        )

        # ── Steps 3–7: Project each item ─────────────────────────────────────
        projections: List[InventoryProjection] = []
        for item in items:
            # Update computed fields on item
            item.safety_stock  = self.calculator.safety_stock(item)
            item.reorder_point = self.calculator.reorder_point(item)

            days_rem  = self.calculator.days_remaining(item)
            stockout  = self.calculator.project(item)
            revenue   = self.calculator.revenue_impact(item, days_rem)
            delay     = self.calculator.manufacturing_delay(item, days_rem)

            proj = InventoryProjection(
                item         = item,
                stockout     = stockout,
                revenue      = revenue,
                delay        = delay,
                evaluated_at = evaluated_at,
            )
            projections.append(proj)

        # ── Step 8: Fleet forecast ────────────────────────────────────────────
        fleet = self.forecaster.fleet_forecast(projections)

        # ── Step 9: Alerts ────────────────────────────────────────────────────
        alerts = self._build_alerts(projections)

        # ── Step 10: Summary ──────────────────────────────────────────────────
        summary = {
            "total_items":             len(projections),
            "fleet_inventory_health":  fleet.get("fleet_inventory_health", 0),
            "fleet_health_label":      fleet.get("fleet_health_label", "UNKNOWN"),
            "critical_count":          fleet.get("critical_at_risk_count", 0),
            "high_risk_count":         fleet.get("high_at_risk_count", 0),
            "total_revenue_at_risk":   fleet.get("total_revenue_at_risk", 0),
            "total_financial_impact":  fleet.get("total_financial_impact", 0),
            "alert_count":             len(alerts),
            "execution_id":            execution_id,
            "evaluated_at":            evaluated_at,
        }

        logger.info(
            f"[inventory_pipeline] Done — "
            f"items={len(projections)}, "
            f"FIH={fleet.get('fleet_inventory_health', 0):.1f}, "
            f"CRITICAL={fleet.get('critical_at_risk_count', 0)}, "
            f"revenue_at_risk=${fleet.get('total_revenue_at_risk', 0):,.0f}"
        )

        return InventoryPipelineResult(
            projections    = projections,
            fleet_forecast = fleet,
            alerts         = alerts,
            summary        = summary,
            execution_id   = execution_id,
            evaluated_at   = evaluated_at,
            total_items    = len(projections),
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_items(
        self,
        risk_assessments: List[Dict[str, Any]],
        supplier_scores:  List[Dict[str, Any]],
        graph_snapshot:   Dict[str, Any],
    ) -> List[InventoryItem]:
        items = []
        for seed in SEED_INVENTORY:
            enriched = self.mapper.enrich_item(
                item_dict        = seed,
                risk_assessments = risk_assessments,
                supplier_scores  = supplier_scores,
                graph_snapshot   = graph_snapshot,
            )
            item = InventoryItem(
                component_id      = enriched["component_id"],
                component_name    = enriched["component_name"],
                supplier_id       = enriched["supplier_id"],
                supplier_name     = enriched["supplier_name"],
                unit              = enriched.get("unit", "units"),
                current_stock     = float(enriched.get("current_stock", 0)),
                daily_consumption = float(enriched.get("daily_consumption", 1)),
                demand_std_dev    = float(enriched.get("demand_std_dev", 0)),
                monthly_demand    = float(enriched.get("monthly_demand", 0)),
                lead_time_days    = int(enriched.get("lead_time_days", 30)),
                min_order_qty     = float(enriched.get("min_order_qty", 100)),
                unit_cost         = float(enriched.get("unit_cost", 0)),
                margin_per_unit   = float(enriched.get("margin_per_unit", 0)),
                revenue_per_unit  = float(enriched.get("revenue_per_unit", 0)),
                used_in_products  = enriched.get("used_in_products", []),
                product_ids       = enriched.get("product_ids", []),
                metadata          = enriched.get("metadata", {}),
            )
            items.append(item)
        return items

    def _build_alerts(self, projections: List[InventoryProjection]) -> List[Dict[str, Any]]:
        alerts = []
        for proj in projections:
            risk = proj.stockout.stockout_risk
            if risk not in (StockoutRisk.CRITICAL, StockoutRisk.HIGH):
                continue
            alerts.append({
                "component_id":         proj.item.component_id,
                "component_name":       proj.item.component_name,
                "supplier_id":          proj.item.supplier_id,
                "supplier_name":        proj.item.supplier_name,
                "stockout_risk":        risk.value,
                "days_remaining":       round(proj.stockout.days_remaining, 1),
                "lead_time_days":       proj.item.lead_time_days,
                "stockout_probability": proj.stockout.stockout_probability,
                "stockout_date":        proj.stockout.stockout_date,
                "revenue_at_risk_usd":  proj.revenue.revenue_lost_usd,
                "delay_days":           proj.delay.delay_days,
                "affected_products":    proj.item.used_in_products,
                "severity":             "CRITICAL" if risk == StockoutRisk.CRITICAL else "HIGH",
            })
        return sorted(alerts, key=lambda a: a["days_remaining"])
