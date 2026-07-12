"""
Phase 7: Inventory Impact — Inventory Forecaster

Extends the core calculator with:

────────────────────────────────────────────────────────────────────────
ALGORITHM: Linear Demand Forecasting
────────────────────────────────────────────────────────────────────────
Generates a day-by-day inventory depletion timeline:

  stock_t = max(0, current_stock - (daily_consumption × t))

Where:
  t = number of days from today (0, 1, 2, …, horizon)

Stockout occurs at:
  t_stockout = current_stock / daily_consumption = days_remaining

────────────────────────────────────────────────────────────────────────
ALGORITHM: Risk-Adjusted Demand Forecasting
────────────────────────────────────────────────────────────────────────
When supply risk is elevated (from Phase 4), daily consumption is
adjusted upward via a risk demand multiplier:

  risk_demand_factor = 1 + (risk_score / 200)    [max +50% at score=100]
  adjusted_daily = daily_consumption × risk_demand_factor

  stock_risk_t = max(0, current_stock - (adjusted_daily × t))

────────────────────────────────────────────────────────────────────────
ALGORITHM: Inventory Timeline (Day-by-Day)
────────────────────────────────────────────────────────────────────────
Returns a list of {day, date, stock_level, risk_adjusted_stock} objects
at configurable intervals (every N days).

Milestone markers are injected at:
  • Reorder Point crossing
  • Safety Stock crossing
  • Base Stockout date
  • Risk-Adjusted Stockout date
────────────────────────────────────────────────────────────────────────
ALGORITHM: Fleet Inventory Score (Aggregation)
────────────────────────────────────────────────────────────────────────
  fleet_inventory_health = Σ(health_score × weight) / Σ(weight)
  weight = unit_cost × daily_consumption   (high-value/high-volume = higher weight)

  total_revenue_at_risk = Σ(revenue_lost_usd for all at-risk components)
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.inventory.models import (
    InventoryItem,
    InventoryProjection,
    StockoutRisk,
)

logger = logging.getLogger("inventory.forecaster")

FORECAST_HORIZON_DAYS = 120    # 4 months forward
TIMELINE_INTERVAL_DAYS = 7    # snapshot every 7 days in timeline


class InventoryForecaster:
    """
    Generates inventory depletion timelines and fleet-level forecasts.
    """

    def timeline(
        self,
        item:           InventoryItem,
        risk_score:     float = 0.0,
        horizon:        int   = FORECAST_HORIZON_DAYS,
        interval:       int   = TIMELINE_INTERVAL_DAYS,
    ) -> Dict[str, Any]:
        """
        Day-by-day inventory depletion timeline with risk-adjusted scenario.

        Args:
            item:       the inventory item
            risk_score: 0–100 from Phase 4 (higher → more demand pressure)
            horizon:    forecast horizon in days
            interval:   report every N days

        Returns:
            {
              "component_id": str,
              "base_scenario": [{"day": int, "date": str, "stock": float}],
              "risk_scenario":  [{"day": int, "date": str, "stock": float}],
              "base_stockout_day":  int | None,
              "risk_stockout_day":  int | None,
              "milestones":         [...],
            }
        """
        if item.daily_consumption <= 0:
            return {
                "component_id": item.component_id,
                "message": "No consumption — no depletion forecast",
            }

        risk_factor = 1.0 + (risk_score / 200.0)   # 1.0x at risk=0, 1.5x at risk=100
        adjusted_daily = item.daily_consumption * risk_factor

        from app.inventory.calculator import InventoryCalculator
        calc = InventoryCalculator()
        rop  = calc.reorder_point(item)
        ss   = calc.safety_stock(item)

        today = date.today()
        base_timeline  = []
        risk_timeline  = []
        milestones     = []

        base_stockout_day = None
        risk_stockout_day = None
        base_rop_crossed  = False
        base_ss_crossed   = False
        risk_rop_crossed  = False

        days = range(0, horizon + 1, interval)

        for t in days:
            base_stock = max(0.0, item.current_stock - (item.daily_consumption * t))
            risk_stock = max(0.0, item.current_stock - (adjusted_daily * t))
            day_date   = (today + timedelta(days=t)).isoformat()

            base_timeline.append({
                "day":   t,
                "date":  day_date,
                "stock": round(base_stock, 1),
            })
            risk_timeline.append({
                "day":   t,
                "date":  day_date,
                "stock": round(risk_stock, 1),
            })

            # Milestone: base stockout
            if base_stock == 0 and base_stockout_day is None:
                base_stockout_day = t
                milestones.append({"day": t, "date": day_date, "event": "BASE_STOCKOUT", "scenario": "base"})

            # Milestone: risk stockout
            if risk_stock == 0 and risk_stockout_day is None:
                risk_stockout_day = t
                milestones.append({"day": t, "date": day_date, "event": "RISK_STOCKOUT", "scenario": "risk"})

            # Milestone: reorder point crossed (base)
            if not base_rop_crossed and base_stock <= rop and base_stock > 0:
                base_rop_crossed = True
                milestones.append({"day": t, "date": day_date, "event": "REORDER_POINT_CROSSED", "scenario": "base"})

            # Milestone: safety stock crossed (base)
            if not base_ss_crossed and base_stock <= ss and base_stock > 0:
                base_ss_crossed = True
                milestones.append({"day": t, "date": day_date, "event": "SAFETY_STOCK_CROSSED", "scenario": "base"})

            # Milestone: risk scenario reorder point crossed
            if not risk_rop_crossed and risk_stock <= rop and risk_stock > 0:
                risk_rop_crossed = True
                milestones.append({"day": t, "date": day_date, "event": "REORDER_POINT_CROSSED", "scenario": "risk"})

        return {
            "component_id":       item.component_id,
            "component_name":     item.component_name,
            "horizon_days":       horizon,
            "interval_days":      interval,
            "risk_demand_factor": round(risk_factor, 3),
            "adjusted_daily_consumption": round(adjusted_daily, 2),
            "base_scenario":      base_timeline,
            "risk_scenario":      risk_timeline,
            "base_stockout_day":  base_stockout_day,
            "risk_stockout_day":  risk_stockout_day,
            "reorder_point":      round(rop, 2),
            "safety_stock":       round(ss, 2),
            "milestones":         sorted(milestones, key=lambda m: m["day"]),
        }

    def fleet_forecast(
        self,
        projections: List[InventoryProjection],
    ) -> Dict[str, Any]:
        """
        Fleet-wide inventory aggregation.

        Metrics:
          fleet_inventory_health = weighted avg health (weight = unit_cost × daily_consumption)
          total_revenue_at_risk  = Σ revenue_lost_usd for CRITICAL + HIGH risk items
          total_cogs_at_risk     = Σ cogs_at_risk_usd
        """
        if not projections:
            return {"message": "No projections available"}

        # Weighted health
        total_weight   = 0.0
        weighted_sum   = 0.0
        for proj in projections:
            weight = max(0.01, proj.item.unit_cost * proj.item.daily_consumption)
            total_weight += weight
            weighted_sum += proj.stockout.inventory_health_score * weight

        fleet_health = round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0

        # Risk breakdown
        risk_counts: Dict[str, int] = {r.value: 0 for r in StockoutRisk}
        at_risk_revenue = 0.0
        at_risk_cogs    = 0.0
        critical_items  = []

        for proj in projections:
            risk_counts[proj.stockout.stockout_risk.value] += 1

            if proj.stockout.stockout_risk in (StockoutRisk.CRITICAL, StockoutRisk.HIGH):
                at_risk_revenue += proj.revenue.revenue_lost_usd
                at_risk_cogs    += proj.revenue.cogs_at_risk_usd
                critical_items.append({
                    "component_id":     proj.item.component_id,
                    "component_name":   proj.item.component_name,
                    "supplier_id":      proj.item.supplier_id,
                    "days_remaining":   proj.stockout.days_remaining,
                    "stockout_risk":    proj.stockout.stockout_risk.value,
                    "revenue_lost_usd": proj.revenue.revenue_lost_usd,
                    "delay_days":       proj.delay.delay_days,
                    "affected_products": proj.item.used_in_products,
                })

        # Products at risk
        products_at_risk: Dict[str, float] = {}
        for proj in projections:
            for prod, impact in proj.revenue.affected_revenues.items():
                products_at_risk[prod] = products_at_risk.get(prod, 0.0) + impact

        fleet_label = self._fleet_label(fleet_health)

        return {
            "fleet_inventory_health":  fleet_health,
            "fleet_health_label":      fleet_label,
            "total_components":        len(projections),
            "risk_distribution":       risk_counts,
            "total_revenue_at_risk":   round(at_risk_revenue, 2),
            "total_cogs_at_risk":      round(at_risk_cogs, 2),
            "total_financial_impact":  round(at_risk_revenue + at_risk_cogs, 2),
            "critical_at_risk_count":  risk_counts.get("CRITICAL", 0),
            "high_at_risk_count":      risk_counts.get("HIGH", 0),
            "critical_components":     sorted(critical_items, key=lambda x: x["days_remaining"]),
            "products_at_risk":        dict(sorted(products_at_risk.items(), key=lambda x: x[1], reverse=True)),
        }

    def _fleet_label(self, score: float) -> str:
        if score >= 80:  return "EXCELLENT"
        if score >= 60:  return "GOOD"
        if score >= 40:  return "FAIR"
        if score >= 20:  return "POOR"
        return "CRITICAL"
