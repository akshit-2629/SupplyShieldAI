"""
Phase 7: Inventory Impact — Core Calculator

Implements all inventory algorithms with exact formulas.

────────────────────────────────────────────────────────────────────────
ALGORITHM 1: Days Remaining
────────────────────────────────────────────────────────────────────────
  days_remaining = current_stock / daily_consumption

  Edge case: if daily_consumption == 0 → days_remaining = ∞ (no consumption)

────────────────────────────────────────────────────────────────────────
ALGORITHM 2: Safety Stock (Statistical — Normal Distribution)
────────────────────────────────────────────────────────────────────────
  Safety stock accounts for demand variability and lead time variability:

  safety_stock = Z × σ_demand × √(lead_time)

  Where:
    Z          = service level z-score
                   95%  → 1.645
                   99%  → 2.326
                   99.9% → 3.090
    σ_demand   = standard deviation of daily demand (demand_std_dev)
    lead_time  = supplier lead time in days

  If σ_demand is 0 (deterministic demand):
    safety_stock = 0.10 × (avg_daily_consumption × lead_time)  [10% buffer]

────────────────────────────────────────────────────────────────────────
ALGORITHM 3: Reorder Point
────────────────────────────────────────────────────────────────────────
  reorder_point = (avg_daily_consumption × lead_time) + safety_stock

  Interpretation: When stock hits this level, place a new order immediately.

────────────────────────────────────────────────────────────────────────
ALGORITHM 4: Stockout Risk Classification
────────────────────────────────────────────────────────────────────────
  safety_stock_days  = safety_stock / daily_consumption

  CRITICAL if: days_remaining < lead_time
               (no time to reorder before stockout)
  HIGH     if: days_remaining < lead_time + safety_stock_days
               (safety buffer exhausted)
  MEDIUM   if: days_remaining < lead_time × 1.5
               (approaching risk zone)
  LOW      if: days_remaining < lead_time × 2.0
  SAFE     if: days_remaining >= lead_time × 2.0

────────────────────────────────────────────────────────────────────────
ALGORITHM 5: Stockout Probability (Exponential Model)
────────────────────────────────────────────────────────────────────────
  shortage_gap = max(0, lead_time - days_remaining)

  stockout_probability = 1 - exp(- shortage_gap / lead_time)

  This gives:
    gap = 0  → probability = 0.0   (no risk)
    gap = lead_time → probability ≈ 0.632  (one full lead time behind)
    gap = 2×lead_time → probability ≈ 0.865

  Clamped to [0.0, 1.0].

────────────────────────────────────────────────────────────────────────
ALGORITHM 6: Inventory Health Score (Weighted Composite)
────────────────────────────────────────────────────────────────────────
  coverage_score = min(100, (days_remaining / (lead_time × 2)) × 100)
  safety_score   = 100 if current_stock > reorder_point
                   else (current_stock / reorder_point) × 100

  health_score = (coverage_score × 0.60) + (safety_score × 0.40)
  health_score clamped to [0, 100]

────────────────────────────────────────────────────────────────────────
ALGORITHM 7: Revenue Impact
────────────────────────────────────────────────────────────────────────
  days_short      = max(0, lead_time - days_remaining)
  units_short     = days_short × daily_consumption
  revenue_lost    = units_short × margin_per_unit
  cogs_at_risk    = units_short × unit_cost

────────────────────────────────────────────────────────────────────────
ALGORITHM 8: Manufacturing Delay
────────────────────────────────────────────────────────────────────────
  delay_days      = max(0, lead_time - days_remaining)
  recovery_factor = 1.5  (50% extra for ramp-up after shortage)
  recovery_days   = delay_days × recovery_factor
  impact_window   = delay_days + recovery_days

  Severity:
    NONE     → delay = 0
    LOW      → 0 < delay ≤ 7
    MEDIUM   → 7 < delay ≤ 21
    HIGH     → 21 < delay ≤ 60
    CRITICAL → delay > 60
"""

from __future__ import annotations

import math
import logging
from datetime import date, timedelta
from typing import Any, Dict, Optional

from app.inventory.models import (
    InventoryItem,
    InventoryHealthLabel,
    ManufacturingDelay,
    RevenueImpact,
    StockoutPrediction,
    StockoutRisk,
)

logger = logging.getLogger("inventory.calculator")

# Z-scores for service levels
SERVICE_LEVEL_Z = {
    0.90: 1.282,
    0.95: 1.645,
    0.99: 2.326,
    0.999: 3.090,
}

DEFAULT_SERVICE_LEVEL = 0.95
RECOVERY_FACTOR = 1.5


class InventoryCalculator:
    """
    Core inventory mathematics engine.
    All methods are stateless and deterministic.
    """

    def __init__(self, service_level: float = DEFAULT_SERVICE_LEVEL) -> None:
        self.z = SERVICE_LEVEL_Z.get(service_level, 1.645)
        self.service_level = service_level

    # ── Algorithm 1: Days Remaining ───────────────────────────────────────────

    def days_remaining(self, item: InventoryItem) -> float:
        """
        days_remaining = current_stock / daily_consumption

        Returns float('inf') if daily_consumption is zero (no demand).
        """
        if item.daily_consumption <= 0:
            return float("inf")
        return item.current_stock / item.daily_consumption

    # ── Algorithm 2: Safety Stock ─────────────────────────────────────────────

    def safety_stock(self, item: InventoryItem) -> float:
        """
        safety_stock = Z × σ_demand × √(lead_time)

        Falls back to 10% buffer if σ_demand = 0.
        """
        if item.demand_std_dev > 0:
            ss = self.z * item.demand_std_dev * math.sqrt(item.lead_time_days)
        else:
            # Deterministic demand — simple percentage buffer
            ss = 0.10 * item.daily_consumption * item.lead_time_days

        return round(max(0.0, ss), 2)

    # ── Algorithm 3: Reorder Point ────────────────────────────────────────────

    def reorder_point(self, item: InventoryItem) -> float:
        """
        reorder_point = (avg_daily_consumption × lead_time) + safety_stock
        """
        ss = self.safety_stock(item)
        rop = (item.daily_consumption * item.lead_time_days) + ss
        return round(max(0.0, rop), 2)

    # ── Algorithm 4: Stockout Risk ────────────────────────────────────────────

    def stockout_risk(
        self,
        days_rem:         float,
        lead_time:        int,
        safety_stock_days: float,
    ) -> StockoutRisk:
        """
        Priority-ordered risk classification.
        """
        if days_rem == float("inf"):
            return StockoutRisk.SAFE
        if days_rem < lead_time:
            return StockoutRisk.CRITICAL
        if days_rem < lead_time + safety_stock_days:
            return StockoutRisk.HIGH
        if days_rem < lead_time * 1.5:
            return StockoutRisk.MEDIUM
        if days_rem < lead_time * 2.0:
            return StockoutRisk.LOW
        return StockoutRisk.SAFE

    # ── Algorithm 5: Stockout Probability ────────────────────────────────────

    def stockout_probability(self, days_rem: float, lead_time: int) -> float:
        """
        stockout_probability = 1 - exp(-shortage_gap / lead_time)

        shortage_gap = max(0, lead_time - days_remaining)
        """
        if days_rem == float("inf") or lead_time <= 0:
            return 0.0
        gap = max(0.0, lead_time - days_rem)
        prob = 1.0 - math.exp(-gap / lead_time)
        return round(min(1.0, max(0.0, prob)), 6)

    # ── Algorithm 6: Inventory Health Score ──────────────────────────────────

    def inventory_health(
        self,
        item:      InventoryItem,
        days_rem:  float,
        rop:       float,
    ) -> tuple[float, str]:
        """
        health_score = coverage × 0.60 + safety × 0.40   (0–100)

        Returns: (health_score, health_label)
        """
        # Coverage component
        coverage_denominator = item.lead_time_days * 2
        if coverage_denominator <= 0:
            coverage = 100.0
        elif days_rem == float("inf"):
            coverage = 100.0
        else:
            coverage = min(100.0, (days_rem / coverage_denominator) * 100.0)

        # Safety component: how close are we to the reorder point?
        if rop <= 0 or item.current_stock >= rop:
            safety = 100.0
        else:
            safety = min(100.0, (item.current_stock / rop) * 100.0)

        health = round((coverage * 0.60) + (safety * 0.40), 2)
        health = min(100.0, max(0.0, health))

        label = self._health_label(health)
        return health, label

    # ── Algorithm 7: Revenue Impact ───────────────────────────────────────────

    def revenue_impact(self, item: InventoryItem, days_rem: float) -> RevenueImpact:
        """
        days_short   = max(0, lead_time - days_remaining)
        units_short  = days_short × daily_consumption
        revenue_lost = units_short × margin_per_unit
        cogs_at_risk = units_short × unit_cost
        """
        days_short = max(0.0, item.lead_time_days - days_rem) if days_rem != float("inf") else 0.0
        units_short = days_short * item.daily_consumption

        revenue_lost = units_short * item.margin_per_unit
        cogs_at_risk = units_short * item.unit_cost

        # Distribute revenue impact across products
        n_products = max(1, len(item.used_in_products))
        affected_revenues = {
            prod: round(revenue_lost / n_products, 2)
            for prod in item.used_in_products
        }

        return RevenueImpact(
            component_id      = item.component_id,
            component_name    = item.component_name,
            days_short        = round(days_short, 1),
            units_short       = round(units_short, 0),
            revenue_lost_usd  = round(revenue_lost, 2),
            cogs_at_risk_usd  = round(cogs_at_risk, 2),
            affected_products = item.used_in_products,
            affected_revenues = affected_revenues,
            formula = {
                "days_short":          round(days_short, 2),
                "units_short":         round(units_short, 2),
                "margin_per_unit":     item.margin_per_unit,
                "unit_cost":           item.unit_cost,
                "revenue_formula":     "days_short × daily_consumption × margin_per_unit",
                "cogs_formula":        "days_short × daily_consumption × unit_cost",
            },
        )

    # ── Algorithm 8: Manufacturing Delay ─────────────────────────────────────

    def manufacturing_delay(self, item: InventoryItem, days_rem: float) -> ManufacturingDelay:
        """
        delay_days      = max(0, lead_time - days_remaining)
        recovery_days   = delay_days × 1.5
        impact_window   = delay_days + recovery_days
        """
        delay = max(0.0, item.lead_time_days - days_rem) if days_rem != float("inf") else 0.0
        recovery = delay * RECOVERY_FACTOR
        impact_window = delay + recovery

        severity = self._delay_severity(delay)

        earliest_recovery = None
        if delay > 0:
            recovery_date = date.today() + timedelta(days=int(impact_window))
            earliest_recovery = recovery_date.isoformat()

        # Each product gets the same delay
        product_delays = {prod: round(delay, 1) for prod in item.used_in_products}

        return ManufacturingDelay(
            component_id       = item.component_id,
            component_name     = item.component_name,
            delay_days         = round(delay, 1),
            recovery_days      = round(recovery, 1),
            impact_window_days = round(impact_window, 1),
            affected_products  = item.used_in_products,
            product_delays     = product_delays,
            severity           = severity,
            earliest_recovery  = earliest_recovery,
            formula = {
                "delay_formula":       "max(0, lead_time - days_remaining)",
                "recovery_formula":    f"delay × {RECOVERY_FACTOR}",
                "impact_window":       "delay + recovery",
                "recovery_factor":     RECOVERY_FACTOR,
            },
        )

    # ── Full projection for one item ──────────────────────────────────────────

    def project(self, item: InventoryItem) -> StockoutPrediction:
        """
        Compute the full StockoutPrediction for one InventoryItem.
        """
        days_rem  = self.days_remaining(item)
        ss        = self.safety_stock(item)
        rop       = self.reorder_point(item)

        safety_stock_days = ss / item.daily_consumption if item.daily_consumption > 0 else 0.0
        reorder_days      = rop / item.daily_consumption if item.daily_consumption > 0 else 0.0

        risk     = self.stockout_risk(days_rem, item.lead_time_days, safety_stock_days)
        prob     = self.stockout_probability(days_rem, item.lead_time_days)
        health, health_label = self.inventory_health(item, days_rem, rop)

        coverage_ratio = (days_rem / item.lead_time_days) if item.lead_time_days > 0 and days_rem != float("inf") else (99.0 if days_rem == float("inf") else 0.0)

        reorder_urgency = max(0.0, rop - item.current_stock) / item.daily_consumption if item.daily_consumption > 0 else 0.0

        # Stockout date
        stockout_date = None
        if days_rem != float("inf") and days_rem >= 0:
            stockout_date = (date.today() + timedelta(days=int(days_rem))).isoformat()

        formula_breakdown = {
            "days_remaining":      round(days_rem, 2) if days_rem != float("inf") else "∞",
            "formula":             "current_stock / daily_consumption",
            "current_stock":       item.current_stock,
            "daily_consumption":   item.daily_consumption,
            "safety_stock":        round(ss, 2),
            "safety_stock_formula":"Z × σ_demand × √(lead_time)",
            "Z_score":             self.z,
            "sigma_demand":        item.demand_std_dev,
            "reorder_point":       round(rop, 2),
            "rop_formula":         "(daily × lead_time) + safety_stock",
            "stockout_prob_formula":"1 - exp(-gap / lead_time)",
            "coverage_score":      round(min(100.0, (days_rem / (item.lead_time_days * 2)) * 100), 2) if days_rem != float("inf") else 100.0,
            "health_formula":      "coverage×0.60 + safety×0.40",
        }

        return StockoutPrediction(
            component_id           = item.component_id,
            component_name         = item.component_name,
            supplier_id            = item.supplier_id,
            days_remaining         = days_rem if days_rem != float("inf") else 9999.0,
            safety_stock_days      = round(safety_stock_days, 2),
            reorder_days           = round(reorder_days, 2),
            lead_time_days         = item.lead_time_days,
            stockout_risk          = risk,
            stockout_probability   = prob,
            stockout_date          = stockout_date,
            reorder_urgency_days   = round(reorder_urgency, 2),
            inventory_health_score = health,
            inventory_health_label = health_label,
            coverage_ratio         = round(coverage_ratio, 3),
            formula_breakdown      = formula_breakdown,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _health_label(self, score: float) -> str:
        if score >= 80:  return InventoryHealthLabel.EXCELLENT.value
        if score >= 60:  return InventoryHealthLabel.GOOD.value
        if score >= 40:  return InventoryHealthLabel.FAIR.value
        if score >= 20:  return InventoryHealthLabel.POOR.value
        return InventoryHealthLabel.CRITICAL.value

    def _delay_severity(self, delay: float) -> str:
        if delay <= 0:   return "NONE"
        if delay <= 7:   return "LOW"
        if delay <= 21:  return "MEDIUM"
        if delay <= 60:  return "HIGH"
        return "CRITICAL"
