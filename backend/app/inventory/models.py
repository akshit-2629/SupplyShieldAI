"""
Phase 7: Inventory Impact — Data Models

All typed dataclasses and seed inventory data for the 7 key components
tracked across the Phase 5 supply chain graph topology.

Stock quantities and consumption rates are realistic industry approximations.

────────────────────────────────────────────────────────────────────────
Seed Inventory Topology (matches Phase 5 SEED_NODES)
────────────────────────────────────────────────────────────────────────
  Component         Supplier    Product(s)
  ─────────────────────────────────────────────
  Advanced Chip (3nm)  TSMC     → Smartphone, Laptop
  Battery Cell         CATL     → Electric Vehicle
  OLED Display         Samsung  → Smartphone
  EUV Machine          ASML     → (capital equipment)
  Sensor Module        Bosch    → Electric Vehicle, Industrial Robot
  Modem Chip           Qualcomm → Smartphone, Laptop
  PCB Assembly         Foxconn  → Smartphone, Laptop, Industrial Robot
  Container Slot       Maersk   → (logistics capacity)
  Passive Component    Murata   → Smartphone, Laptop
  Magnetic Component   TDK      → Smartphone, Electric Vehicle
  IC Substrate         Shinko   → Advanced Chip pipeline
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class StockoutRisk(str, Enum):
    CRITICAL   = "CRITICAL"    # days_remaining < lead_time (already stockout risk)
    HIGH       = "HIGH"        # days_remaining < lead_time + safety_stock_days
    MEDIUM     = "MEDIUM"      # days_remaining < lead_time × 1.5
    LOW        = "LOW"         # days_remaining >= lead_time × 1.5
    SAFE       = "SAFE"        # days_remaining >= lead_time × 2


class InventoryHealthLabel(str, Enum):
    EXCELLENT  = "EXCELLENT"   # health ≥ 80
    GOOD       = "GOOD"        # health 60–79
    FAIR       = "FAIR"        # health 40–59
    POOR       = "POOR"        # health 20–39
    CRITICAL   = "CRITICAL"    # health < 20


# ─────────────────────────────────────────────────────────────────────────────
# Core domain models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class InventoryItem:
    """
    One component/SKU in the inventory tracking system.

    All quantities in standardised units (chips, cells, panels, etc.).
    Monetary values in USD.
    """
    component_id:       str
    component_name:     str
    supplier_id:        str
    supplier_name:      str
    unit:               str     = "units"

    # Stock levels
    current_stock:      float   = 0.0      # units on hand
    safety_stock:       float   = 0.0      # computed safety buffer
    reorder_point:      float   = 0.0      # computed reorder threshold

    # Demand
    daily_consumption:  float   = 1.0      # avg units consumed per day
    demand_std_dev:     float   = 0.0      # std deviation of daily demand
    monthly_demand:     float   = 0.0      # avg monthly demand

    # Supply
    lead_time_days:     int     = 30       # supplier delivery lead time
    min_order_qty:      float   = 100.0    # minimum order quantity

    # Revenue
    unit_cost:          float   = 0.0      # USD per unit (cost of goods)
    margin_per_unit:    float   = 0.0      # USD gross margin per unit sold
    revenue_per_unit:   float   = 0.0      # USD selling price per unit

    # Mappings
    used_in_products:   List[str] = field(default_factory=list)  # product names
    product_ids:        List[str] = field(default_factory=list)   # product IDs

    # Metadata
    metadata:           Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id":      self.component_id,
            "component_name":    self.component_name,
            "supplier_id":       self.supplier_id,
            "supplier_name":     self.supplier_name,
            "unit":              self.unit,
            "current_stock":     self.current_stock,
            "safety_stock":      round(self.safety_stock, 2),
            "reorder_point":     round(self.reorder_point, 2),
            "daily_consumption": self.daily_consumption,
            "demand_std_dev":    self.demand_std_dev,
            "monthly_demand":    self.monthly_demand,
            "lead_time_days":    self.lead_time_days,
            "min_order_qty":     self.min_order_qty,
            "unit_cost":         self.unit_cost,
            "margin_per_unit":   self.margin_per_unit,
            "revenue_per_unit":  self.revenue_per_unit,
            "used_in_products":  self.used_in_products,
            "product_ids":       self.product_ids,
        }


@dataclass
class StockoutPrediction:
    """
    Stockout risk assessment for one inventory item.

    days_remaining:     current_stock / daily_consumption
    safety_stock_days:  safety_stock / daily_consumption
    reorder_days:       reorder_point / daily_consumption
    stockout_date:      today + days_remaining
    """
    component_id:           str
    component_name:         str
    supplier_id:            str
    days_remaining:         float           # primary KPI
    safety_stock_days:      float
    reorder_days:           float
    lead_time_days:         int
    stockout_risk:          StockoutRisk
    stockout_probability:   float           # 0.0 – 1.0
    stockout_date:          Optional[str]   # ISO date
    reorder_urgency_days:   float           # how many days overdue for reorder
    inventory_health_score: float           # 0–100
    inventory_health_label: str
    coverage_ratio:         float           # days_remaining / lead_time
    formula_breakdown:      Dict[str, Any]  = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id":           self.component_id,
            "component_name":         self.component_name,
            "supplier_id":            self.supplier_id,
            "days_remaining":         round(self.days_remaining, 1),
            "safety_stock_days":      round(self.safety_stock_days, 1),
            "reorder_days":           round(self.reorder_days, 1),
            "lead_time_days":         self.lead_time_days,
            "stockout_risk":          self.stockout_risk.value,
            "stockout_probability":   round(self.stockout_probability, 4),
            "stockout_probability_pct": round(self.stockout_probability * 100, 1),
            "stockout_date":          self.stockout_date,
            "reorder_urgency_days":   round(self.reorder_urgency_days, 1),
            "inventory_health_score": round(self.inventory_health_score, 2),
            "inventory_health_label": self.inventory_health_label,
            "coverage_ratio":         round(self.coverage_ratio, 3),
            "formula_breakdown":      self.formula_breakdown,
        }


@dataclass
class RevenueImpact:
    """
    Financial impact of a potential stockout event.

    Formula:
      days_short    = max(0, lead_time - days_remaining)
      units_short   = days_short × daily_consumption
      revenue_lost  = units_short × margin_per_unit
      cogs_at_risk  = units_short × unit_cost
    """
    component_id:       str
    component_name:     str
    days_short:         float
    units_short:        float
    revenue_lost_usd:   float
    cogs_at_risk_usd:   float
    affected_products:  List[str]
    affected_revenues:  Dict[str, float]    # product → revenue impact USD
    formula:            Dict[str, Any]      = field(default_factory=dict)

    @property
    def total_impact_usd(self) -> float:
        return self.revenue_lost_usd + self.cogs_at_risk_usd

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id":       self.component_id,
            "component_name":     self.component_name,
            "days_short":         round(self.days_short, 1),
            "units_short":        round(self.units_short, 0),
            "revenue_lost_usd":   round(self.revenue_lost_usd, 2),
            "cogs_at_risk_usd":   round(self.cogs_at_risk_usd, 2),
            "total_impact_usd":   round(self.total_impact_usd, 2),
            "affected_products":  self.affected_products,
            "affected_revenues":  {k: round(v, 2) for k, v in self.affected_revenues.items()},
            "formula":            self.formula,
        }


@dataclass
class ManufacturingDelay:
    """
    Manufacturing delay projection for products affected by a shortage.

    delay_days     = max(0, lead_time - days_remaining)
    recovery_days  = delay_days × recovery_factor (1.5× default)
    impact_window  = delay_days + recovery_days
    """
    component_id:       str
    component_name:     str
    delay_days:         float
    recovery_days:      float
    impact_window_days: float
    affected_products:  List[str]
    product_delays:     Dict[str, float]   # product → delay_days
    severity:           str                # NONE / LOW / MEDIUM / HIGH / CRITICAL
    earliest_recovery:  Optional[str]      # ISO date
    formula:            Dict[str, Any]     = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id":       self.component_id,
            "component_name":     self.component_name,
            "delay_days":         round(self.delay_days, 1),
            "recovery_days":      round(self.recovery_days, 1),
            "impact_window_days": round(self.impact_window_days, 1),
            "affected_products":  self.affected_products,
            "product_delays":     {k: round(v, 1) for k, v in self.product_delays.items()},
            "severity":           self.severity,
            "earliest_recovery":  self.earliest_recovery,
            "formula":            self.formula,
        }


@dataclass
class InventoryProjection:
    """Full inventory projection for one component — combines all sub-analyses."""
    item:          InventoryItem
    stockout:      StockoutPrediction
    revenue:       RevenueImpact
    delay:         ManufacturingDelay
    evaluated_at:  str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluated_at":  self.evaluated_at,
            "item":          self.item.to_dict(),
            "stockout":      self.stockout.to_dict(),
            "revenue_impact": self.revenue.to_dict(),
            "manufacturing_delay": self.delay.to_dict(),
            # Flat helpers for frontend compatibility
            "component_id":         str(self.item.component_id),
            "component_name":       self.item.component_name,
            "supplier_id":          self.item.supplier_id,
            "supplier_name":        self.item.supplier_name,
            "current_stock":        self.item.current_stock,
            "days_remaining":       round(self.stockout.days_remaining, 1),
            "stockout_risk":        self.stockout.stockout_risk.value,
            "stockout_probability": round(self.stockout.stockout_probability, 4),
            "revenue_lost_usd":     round(self.revenue.revenue_lost_usd, 2),
            "delay_days":           round(self.delay.delay_days, 1),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Seed inventory data (matches Phase 5 component topology)
# ─────────────────────────────────────────────────────────────────────────────

SEED_INVENTORY: List[Dict[str, Any]] = [
    {
        "component_id":     "component::ADVANCED_CHIP",
        "component_name":   "Advanced Chip (3nm)",
        "supplier_id":      "supplier::TSMC",
        "supplier_name":    "TSMC",
        "unit":             "wafers",
        "current_stock":    2800,
        "daily_consumption": 120,
        "demand_std_dev":   18.0,
        "monthly_demand":   3600,
        "lead_time_days":   90,
        "min_order_qty":    500,
        "unit_cost":        3500.0,
        "margin_per_unit":  1200.0,
        "revenue_per_unit": 4700.0,
        "used_in_products": ["Smartphone", "Laptop"],
        "product_ids":      ["product::SMARTPHONE", "product::LAPTOP"],
    },
    {
        "component_id":     "component::BATTERY_CELL",
        "component_name":   "Battery Cell (LFP)",
        "supplier_id":      "supplier::CATL",
        "supplier_name":    "CATL",
        "unit":             "cells",
        "current_stock":    95000,
        "daily_consumption": 3200,
        "demand_std_dev":   480.0,
        "monthly_demand":   96000,
        "lead_time_days":   45,
        "min_order_qty":    10000,
        "unit_cost":        85.0,
        "margin_per_unit":  28.0,
        "revenue_per_unit": 113.0,
        "used_in_products": ["Electric Vehicle"],
        "product_ids":      ["product::EV"],
    },
    {
        "component_id":     "component::OLED_DISPLAY",
        "component_name":   "OLED Display Panel",
        "supplier_id":      "supplier::SAMSUNG",
        "supplier_name":    "Samsung",
        "unit":             "panels",
        "current_stock":    18000,
        "daily_consumption": 850,
        "demand_std_dev":   110.0,
        "monthly_demand":   25500,
        "lead_time_days":   30,
        "min_order_qty":    2000,
        "unit_cost":        220.0,
        "margin_per_unit":  75.0,
        "revenue_per_unit": 295.0,
        "used_in_products": ["Smartphone"],
        "product_ids":      ["product::SMARTPHONE"],
    },
    {
        "component_id":     "component::EUV_MACHINE",
        "component_name":   "EUV Lithography Machine",
        "supplier_id":      "supplier::ASML",
        "supplier_name":    "ASML",
        "unit":             "machines",
        "current_stock":    3,
        "daily_consumption": 0.05,      # ~1 machine every 20 days
        "demand_std_dev":   0.02,
        "monthly_demand":   1.5,
        "lead_time_days":   365,        # 12–18 month lead time
        "min_order_qty":    1,
        "unit_cost":        150000000.0,
        "margin_per_unit":  8000000.0,
        "revenue_per_unit": 158000000.0,
        "used_in_products": ["Semiconductor Fab"],
        "product_ids":      ["product::SEMICONDUCTOR_FAB"],
    },
    {
        "component_id":     "component::SENSOR_MODULE",
        "component_name":   "Sensor Module (ADAS)",
        "supplier_id":      "supplier::BOSCH",
        "supplier_name":    "Bosch",
        "unit":             "modules",
        "current_stock":    42000,
        "daily_consumption": 1800,
        "demand_std_dev":   220.0,
        "monthly_demand":   54000,
        "lead_time_days":   21,
        "min_order_qty":    5000,
        "unit_cost":        145.0,
        "margin_per_unit":  52.0,
        "revenue_per_unit": 197.0,
        "used_in_products": ["Electric Vehicle", "Industrial Robot"],
        "product_ids":      ["product::EV", "product::INDUSTRIAL_ROBOT"],
    },
    {
        "component_id":     "component::MODEM_CHIP",
        "component_name":   "5G Modem Chip",
        "supplier_id":      "supplier::QUALCOMM",
        "supplier_name":    "Qualcomm",
        "unit":             "chips",
        "current_stock":    58000,
        "daily_consumption": 2400,
        "demand_std_dev":   300.0,
        "monthly_demand":   72000,
        "lead_time_days":   60,
        "min_order_qty":    10000,
        "unit_cost":        42.0,
        "margin_per_unit":  18.0,
        "revenue_per_unit": 60.0,
        "used_in_products": ["Smartphone", "Laptop"],
        "product_ids":      ["product::SMARTPHONE", "product::LAPTOP"],
    },
    {
        "component_id":     "component::PCB_ASSEMBLY",
        "component_name":   "PCB Assembly",
        "supplier_id":      "supplier::FOXCONN",
        "supplier_name":    "Foxconn",
        "unit":             "boards",
        "current_stock":    31000,
        "daily_consumption": 1500,
        "demand_std_dev":   190.0,
        "monthly_demand":   45000,
        "lead_time_days":   14,
        "min_order_qty":    2000,
        "unit_cost":        28.0,
        "margin_per_unit":  9.0,
        "revenue_per_unit": 37.0,
        "used_in_products": ["Smartphone", "Laptop", "Industrial Robot"],
        "product_ids":      ["product::SMARTPHONE", "product::LAPTOP", "product::INDUSTRIAL_ROBOT"],
    },
    {
        "component_id":     "component::PASSIVE_COMPONENT",
        "component_name":   "Passive Components (MLCC)",
        "supplier_id":      "supplier::MURATA",
        "supplier_name":    "Murata Mfg",
        "unit":             "K units",
        "current_stock":    9500,
        "daily_consumption": 420,
        "demand_std_dev":   55.0,
        "monthly_demand":   12600,
        "lead_time_days":   28,
        "min_order_qty":    1000,
        "unit_cost":        0.08,
        "margin_per_unit":  0.03,
        "revenue_per_unit": 0.11,
        "used_in_products": ["Smartphone", "Laptop"],
        "product_ids":      ["product::SMARTPHONE", "product::LAPTOP"],
    },
    {
        "component_id":     "component::MAGNETIC_COMPONENT",
        "component_name":   "Magnetic Component (Inductor)",
        "supplier_id":      "supplier::TDK",
        "supplier_name":    "TDK Corp",
        "unit":             "K units",
        "current_stock":    6200,
        "daily_consumption": 280,
        "demand_std_dev":   38.0,
        "monthly_demand":   8400,
        "lead_time_days":   35,
        "min_order_qty":    500,
        "unit_cost":        0.12,
        "margin_per_unit":  0.04,
        "revenue_per_unit": 0.16,
        "used_in_products": ["Smartphone", "Electric Vehicle"],
        "product_ids":      ["product::SMARTPHONE", "product::EV"],
    },
    {
        "component_id":     "component::IC_SUBSTRATE",
        "component_name":   "IC Substrate (BGA)",
        "supplier_id":      "supplier::SHINKO",
        "supplier_name":    "Shinko Electric",
        "unit":             "pieces",
        "current_stock":    15000,
        "daily_consumption": 600,
        "demand_std_dev":   80.0,
        "monthly_demand":   18000,
        "lead_time_days":   55,
        "min_order_qty":    3000,
        "unit_cost":        18.0,
        "margin_per_unit":  6.5,
        "revenue_per_unit": 24.5,
        "used_in_products": ["Smartphone", "Laptop"],
        "product_ids":      ["product::SMARTPHONE", "product::LAPTOP"],
    },
]
