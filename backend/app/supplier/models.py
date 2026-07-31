"""
Phase 6: Supplier Intelligence — Data Models

Typed dataclasses for every concept in the supplier intelligence domain.

SupplierTier: Tier 1 (critical/strategic), Tier 2 (important), Tier 3 (commodity)
KPIScore:     Raw KPI measurements (reliability, cost, lead time, compliance)
HealthScore:  Composite weighted health score (0–100) + component breakdown
SupplierProfile: Full supplier intelligence record
PerformanceTrend: Historical MoM comparison & direction signal

Score ranges (consistent across all components):
  CRITICAL:  0  – 33   (red)
  POOR:      33 – 50   (orange)
  FAIR:      50 – 66   (yellow)
  GOOD:      66 – 80   (light green)
  EXCELLENT: 80 – 100  (green)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class SupplierTier(str, Enum):
    TIER_1   = "TIER_1"    # >30% revenue exposure OR centrality > 0.20
    TIER_2   = "TIER_2"    # 10–30% revenue exposure
    TIER_3   = "TIER_3"    # <10% revenue exposure (commodity)
    UNKNOWN  = "UNKNOWN"


class PerformanceTrend(str, Enum):
    IMPROVING   = "IMPROVING"    # MoM score delta >= +3
    STABLE      = "STABLE"       # MoM score delta within ±3
    DECLINING   = "DECLINING"    # MoM score delta <= -3
    NEW_ENTRY   = "NEW_ENTRY"    # No historical data


class HealthLabel(str, Enum):
    EXCELLENT = "EXCELLENT"   # ≥ 80
    GOOD      = "GOOD"        # 66–79
    FAIR      = "FAIR"        # 50–65
    POOR      = "POOR"        # 33–49
    CRITICAL  = "CRITICAL"    # < 33


# ─────────────────────────────────────────────────────────────────────────────
# KPI Score (raw measurements, all 0–100 scale)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class KPIScore:
    """
    Raw KPI measurements for one supplier.
    All values are on a 0–100 scale (higher = better performance).

    reliability_score:  On-time delivery rate  (from delivery history)
    quality_score:      Defect-free rate        (1 - defect_rate) × 100
    lead_time_score:    Lead time performance   (ideal / actual × 100, capped)
    cost_efficiency:    Cost index performance  (benchmark / actual × 100, capped)
    compliance_score:   Regulatory + contractual compliance
    responsiveness:     Response-to-incident speed (0–100, survey / SLA-based)
    flexibility:        Ability to absorb demand spikes (0–100)
    """
    reliability_score: float = 75.0
    quality_score:     float = 75.0
    lead_time_score:   float = 75.0
    cost_efficiency:   float = 75.0
    compliance_score:  float = 75.0
    responsiveness:    float = 75.0
    flexibility:       float = 75.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reliability_score": round(self.reliability_score, 2),
            "quality_score":     round(self.quality_score,     2),
            "lead_time_score":   round(self.lead_time_score,   2),
            "cost_efficiency":   round(self.cost_efficiency,   2),
            "compliance_score":  round(self.compliance_score,  2),
            "responsiveness":    round(self.responsiveness,    2),
            "flexibility":       round(self.flexibility,       2),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Health Score (composite weighted output)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HealthScore:
    """
    Composite supplier health score (0–100).

    Formula (WeightedKPIScorer):
      reliability_component  = reliability_score  × 0.30
      performance_component  = performance_score  × 0.25
      risk_component         = (100 - risk_score) × 0.25    # inverted: lower risk = better
      dependency_component   = (100 - dependency_score) × 0.20  # inverted: lower dep = better

      health_score = Σ above components   (clamped 0–100)

    Weights sum: 0.30 + 0.25 + 0.25 + 0.20 = 1.00
    """
    health_score:          float = 50.0
    health_label:          str   = "FAIR"
    reliability_component: float = 0.0
    performance_component: float = 0.0
    risk_component:        float = 0.0
    dependency_component:  float = 0.0
    formula_breakdown:     Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "health_score":          round(self.health_score,          2),
            "health_label":          self.health_label,
            "reliability_component": round(self.reliability_component, 2),
            "performance_component": round(self.performance_component, 2),
            "risk_component":        round(self.risk_component,        2),
            "dependency_component":  round(self.dependency_component,  2),
            "formula_breakdown":     self.formula_breakdown,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Full Supplier Profile
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SupplierProfile:
    """
    Full intelligence record for one supplier.

    Combines:
      - Identity (name, country, tier, industry)
      - KPI scores
      - Composite health score
      - Risk data (from Phase 4)
      - Dependency data (from Phase 5)
      - Historical trend (MoM)
      - Rank within fleet
    """
    # Identity
    supplier_id:    str
    name:           str
    country_code:   str              = "US"
    tier:           SupplierTier     = SupplierTier.TIER_3
    industries:     List[str]        = field(default_factory=list)
    revenue_exposure_pct: float      = 5.0   # % of total spend

    # KPI measurements
    kpi:            KPIScore         = field(default_factory=KPIScore)

    # Composite health
    health:         HealthScore      = field(default_factory=HealthScore)

    # From Phase 4 — Risk Assessment
    risk_score:     float            = 0.0
    risk_level:     str              = "LOW"
    geo_risk:       float            = 1.0   # geo multiplier
    industry_risk:  float            = 1.0   # industry multiplier

    # From Phase 5 — Graph Agent
    dependency_score:   float        = 0.0   # degree_centrality × 100
    centrality:         float        = 0.0
    products_supplied:  int          = 0
    blast_radius_size:  int          = 0

    # Ranking
    rank:           int              = 0     # 1 = highest health, N = lowest
    rank_change:    int              = 0     # vs previous run (+/- positions)

    # Historical trend
    trend:          PerformanceTrend = PerformanceTrend.NEW_ENTRY
    mom_change:     float            = 0.0   # month-over-month score delta
    prev_health:    Optional[float]  = None

    # Metadata
    evaluated_at:   str              = ""
    metadata:       Dict[str, Any]   = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "supplier_id":          self.supplier_id,
            "name":                 self.name,
            "company_name":         self.name,
            "country_code":         self.country_code,
            "tier":                 self.tier.value,
            "industries":           self.industries,
            "revenue_exposure_pct": round(self.revenue_exposure_pct, 2),
            "kpi":                  self.kpi.to_dict(),
            "health":               self.health.to_dict(),
            # Flat helpers for frontend compatibility
            "health_score":         round(self.health.health_score, 2),
            "reliability_score":    round(self.kpi.reliability_score, 2),
            "formula_breakdown":    self.health.formula_breakdown,
            "risk_score":           round(self.risk_score, 2),
            "risk_level":           self.risk_level,
            "geo_risk":             round(self.geo_risk, 3),
            "industry_risk":        round(self.industry_risk, 3),
            "dependency_score":     round(self.dependency_score, 2),
            "centrality":           round(self.centrality, 4),
            "products_supplied":    self.products_supplied,
            "blast_radius_size":    self.blast_radius_size,
            "rank":                 self.rank,
            "rank_change":          self.rank_change,
            "trend":                self.trend.value,
            "mom_change":           round(self.mom_change, 2),
            "prev_health":          round(self.prev_health, 2) if self.prev_health is not None else None,
            "evaluated_at":         self.evaluated_at,
            "metadata":             self.metadata,
        }
        if isinstance(self.metadata, dict):
            for k, v in self.metadata.items():
                if k not in d or d[k] is None:
                    d[k] = v
        return d



# ─────────────────────────────────────────────────────────────────────────────
# Seed supplier data (same topology as Phase 5 SEED_NODES)
# ─────────────────────────────────────────────────────────────────────────────
# Revenue exposure and KPI baselines derived from public data heuristics.

SEED_SUPPLIERS = [
    {
        "supplier_id":          "supplier::TSMC",
        "name":                 "TSMC",
        "country_code":         "TW",
        "revenue_exposure_pct": 42.0,   # Tier 1 — >30%
        "industries":           ["semiconductor"],
        "kpi": {
            "reliability_score": 88.0,
            "quality_score":     96.0,
            "lead_time_score":   72.0,
            "cost_efficiency":   65.0,
            "compliance_score":  90.0,
            "responsiveness":    78.0,
            "flexibility":       55.0,
        },
    },
    {
        "supplier_id":          "supplier::SAMSUNG",
        "name":                 "Samsung",
        "country_code":         "KR",
        "revenue_exposure_pct": 28.0,   # Tier 2 — 10–30%
        "industries":           ["semiconductor", "electronics"],
        "kpi": {
            "reliability_score": 85.0,
            "quality_score":     91.0,
            "lead_time_score":   78.0,
            "cost_efficiency":   80.0,
            "compliance_score":  88.0,
            "responsiveness":    82.0,
            "flexibility":       70.0,
        },
    },
    {
        "supplier_id":          "supplier::ASML",
        "name":                 "ASML",
        "country_code":         "NL",
        "revenue_exposure_pct": 15.0,   # Tier 2
        "industries":           ["semiconductor", "equipment"],
        "kpi": {
            "reliability_score": 92.0,
            "quality_score":     97.0,
            "lead_time_score":   55.0,
            "cost_efficiency":   50.0,
            "compliance_score":  95.0,
            "responsiveness":    80.0,
            "flexibility":       40.0,
        },
    },
    {
        "supplier_id":          "supplier::BOSCH",
        "name":                 "Bosch",
        "country_code":         "DE",
        "revenue_exposure_pct": 12.0,   # Tier 2
        "industries":           ["automotive", "electronics"],
        "kpi": {
            "reliability_score": 90.0,
            "quality_score":     93.0,
            "lead_time_score":   82.0,
            "cost_efficiency":   78.0,
            "compliance_score":  92.0,
            "responsiveness":    85.0,
            "flexibility":       72.0,
        },
    },
    {
        "supplier_id":          "supplier::QUALCOMM",
        "name":                 "Qualcomm",
        "country_code":         "US",
        "revenue_exposure_pct": 18.0,   # Tier 2
        "industries":           ["semiconductor", "telecom"],
        "kpi": {
            "reliability_score": 82.0,
            "quality_score":     89.0,
            "lead_time_score":   75.0,
            "cost_efficiency":   72.0,
            "compliance_score":  85.0,
            "responsiveness":    76.0,
            "flexibility":       65.0,
        },
    },
    {
        "supplier_id":          "supplier::CATL",
        "name":                 "CATL",
        "country_code":         "CN",
        "revenue_exposure_pct": 35.0,   # Tier 1 — >30%
        "industries":           ["energy", "automotive"],
        "kpi": {
            "reliability_score": 80.0,
            "quality_score":     85.0,
            "lead_time_score":   70.0,
            "cost_efficiency":   88.0,
            "compliance_score":  72.0,
            "responsiveness":    68.0,
            "flexibility":       75.0,
        },
    },
    {
        "supplier_id":          "supplier::FOXCONN",
        "name":                 "Foxconn",
        "country_code":         "TW",
        "revenue_exposure_pct": 22.0,   # Tier 2
        "industries":           ["electronics", "manufacturing"],
        "kpi": {
            "reliability_score": 78.0,
            "quality_score":     81.0,
            "lead_time_score":   80.0,
            "cost_efficiency":   90.0,
            "compliance_score":  70.0,
            "responsiveness":    72.0,
            "flexibility":       82.0,
        },
    },
    {
        "supplier_id":          "supplier::MAERSK",
        "name":                 "Maersk",
        "country_code":         "DK",
        "revenue_exposure_pct": 8.0,    # Tier 3 — <10%
        "industries":           ["logistics", "shipping"],
        "kpi": {
            "reliability_score": 76.0,
            "quality_score":     80.0,
            "lead_time_score":   73.0,
            "cost_efficiency":   75.0,
            "compliance_score":  88.0,
            "responsiveness":    70.0,
            "flexibility":       68.0,
        },
    },
    {
        "supplier_id":          "supplier::MURATA",
        "name":                 "Murata Mfg",
        "country_code":         "JP",
        "revenue_exposure_pct": 6.0,    # Tier 3
        "industries":           ["electronics", "components"],
        "kpi": {
            "reliability_score": 91.0,
            "quality_score":     95.0,
            "lead_time_score":   79.0,
            "cost_efficiency":   71.0,
            "compliance_score":  93.0,
            "responsiveness":    83.0,
            "flexibility":       60.0,
        },
    },
    {
        "supplier_id":          "supplier::TDK",
        "name":                 "TDK Corp",
        "country_code":         "JP",
        "revenue_exposure_pct": 4.0,    # Tier 3
        "industries":           ["electronics", "components"],
        "kpi": {
            "reliability_score": 89.0,
            "quality_score":     93.0,
            "lead_time_score":   77.0,
            "cost_efficiency":   73.0,
            "compliance_score":  91.0,
            "responsiveness":    80.0,
            "flexibility":       58.0,
        },
    },
    {
        "supplier_id":          "supplier::SHINKO",
        "name":                 "Shinko Electric",
        "country_code":         "JP",
        "revenue_exposure_pct": 3.5,    # Tier 3
        "industries":           ["semiconductor", "components"],
        "kpi": {
            "reliability_score": 83.0,
            "quality_score":     88.0,
            "lead_time_score":   74.0,
            "cost_efficiency":   76.0,
            "compliance_score":  86.0,
            "responsiveness":    75.0,
            "flexibility":       55.0,
        },
    },
    {
        "supplier_id":          "supplier::EVERGREEN",
        "name":                 "Evergreen Marine",
        "country_code":         "TW",
        "revenue_exposure_pct": 3.0,    # Tier 3
        "industries":           ["logistics", "shipping"],
        "kpi": {
            "reliability_score": 71.0,
            "quality_score":     75.0,
            "lead_time_score":   68.0,
            "cost_efficiency":   80.0,
            "compliance_score":  78.0,
            "responsiveness":    65.0,
            "flexibility":       62.0,
        },
    },
]
