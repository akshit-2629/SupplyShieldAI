"""
Phase 8: Recommendation Agent — Data Models

Typed dataclasses for every concept in the recommendation domain.

MCDMCriteria:        One criterion in the decision matrix (name, weight, benefit/cost)
SupplierCandidate:   A supplier being evaluated as a potential alternative
RecommendationResult: Final ranked recommendation for one at-risk supplier
ProcurementNote:     Human-readable procurement action item

────────────────────────────────────────────────────────────────────────
MCDM Criteria Weights (must sum to 1.0)
────────────────────────────────────────────────────────────────────────
  health_score      (benefit) 0.25  — overall supplier health from Phase 6
  reliability_score (benefit) 0.20  — on-time delivery + quality
  cost_efficiency   (benefit) 0.15  — cost competitiveness
  lead_time_score   (benefit) 0.15  — supply speed
  risk_score        (cost)    0.15  — inverted: lower risk = better
  compliance_score  (benefit) 0.10  — regulatory adherence

Sum: 0.25 + 0.20 + 0.15 + 0.15 + 0.15 + 0.10 = 1.00

────────────────────────────────────────────────────────────────────────
Alternative Supplier Pool (matches Phase 5/6 seed topology)
────────────────────────────────────────────────────────────────────────
Each at-risk supplier is compared against all other suppliers in the
fleet + a set of curated alternative suppliers for the same industry.

Alternative supplier pool is seeded with realistic alternatives for
the 12 primary suppliers, organised by industry sector:
  semiconductor: GlobalFoundries, Intel, Samsung, UMC, SMIC
  automotive:    Continental, Denso, ZF, Aptiv
  logistics:     MSC, CMA CGM, COSCO, DHL
  electronics:   TDK, Murata, Vishay, AVX
  battery:       LG Energy, Panasonic, BYD, SK Innovation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# MCDM Criteria
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MCDMCriteria:
    """One criterion dimension in the MCDM decision matrix."""
    name:        str
    weight:      float          # 0.0 – 1.0, all weights sum to 1.0
    is_benefit:  bool = True    # True = higher is better; False = lower is better (cost)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name":       self.name,
            "weight":     self.weight,
            "is_benefit": self.is_benefit,
            "direction":  "BENEFIT (↑)" if self.is_benefit else "COST (↓)",
        }


# Default MCDM criteria for supplier comparison
DEFAULT_CRITERIA: List[MCDMCriteria] = [
    MCDMCriteria("health_score",      weight=0.25, is_benefit=True),
    MCDMCriteria("reliability_score", weight=0.20, is_benefit=True),
    MCDMCriteria("cost_efficiency",   weight=0.15, is_benefit=True),
    MCDMCriteria("lead_time_score",   weight=0.15, is_benefit=True),
    MCDMCriteria("risk_score",        weight=0.15, is_benefit=False),  # lower = better
    MCDMCriteria("compliance_score",  weight=0.10, is_benefit=True),
]


# ─────────────────────────────────────────────────────────────────────────────
# Supplier Candidate
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SupplierCandidate:
    """
    A supplier being evaluated as a potential alternative.
    All score fields are on a 0–100 scale (higher = better),
    EXCEPT risk_score (higher = worse).
    """
    supplier_id:      str
    name:             str
    country_code:     str   = "US"
    tier:             str   = "TIER_3"
    industries:       List[str] = field(default_factory=list)
    is_current:       bool  = False   # True = current/at-risk supplier

    # MCDM criteria scores
    health_score:     float = 75.0
    reliability_score: float = 75.0
    quality_score:    float = 75.0
    lead_time_score:  float = 75.0
    cost_efficiency:  float = 75.0
    compliance_score: float = 75.0
    responsiveness:   float = 75.0
    flexibility:      float = 75.0
    risk_score:       float = 0.0    # from Phase 4
    revenue_exposure_pct: float = 5.0

    # Computed by algorithms
    topsis_score:     float = 0.0    # 0–1 (relative closeness)
    cosine_sim:       float = 0.0    # 0–1 (similarity to ideal)
    weighted_score:   float = 0.0    # weighted criteria avg
    recommendation_score: float = 0.0  # master composite

    # Ranking
    rank:             int   = 0

    # Metadata
    metadata:         Dict[str, Any] = field(default_factory=dict)

    def feature_vector(self) -> List[float]:
        """8-dimensional feature vector for cosine similarity."""
        return [
            self.health_score,
            self.reliability_score,
            self.quality_score,
            self.lead_time_score,
            self.cost_efficiency,
            self.compliance_score,
            self.responsiveness,
            self.flexibility,
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "supplier_id":          self.supplier_id,
            "name":                 self.name,
            "country_code":         self.country_code,
            "tier":                 self.tier,
            "industries":           self.industries,
            "is_current":           self.is_current,
            "scores": {
                "health_score":     round(self.health_score, 2),
                "reliability_score": round(self.reliability_score, 2),
                "quality_score":    round(self.quality_score, 2),
                "lead_time_score":  round(self.lead_time_score, 2),
                "cost_efficiency":  round(self.cost_efficiency, 2),
                "compliance_score": round(self.compliance_score, 2),
                "responsiveness":   round(self.responsiveness, 2),
                "flexibility":      round(self.flexibility, 2),
                "risk_score":       round(self.risk_score, 2),
            },
            "recommendation_score": round(self.recommendation_score, 4),
            "topsis_score":         round(self.topsis_score, 4),
            "cosine_similarity":    round(self.cosine_sim, 4),
            "weighted_score":       round(self.weighted_score, 4),
            "rank":                 self.rank,
            "revenue_exposure_pct": self.revenue_exposure_pct,
            "metadata":             self.metadata,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Procurement Note
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ProcurementNote:
    """Human-readable procurement recommendation action item."""
    priority:    str          # CRITICAL / HIGH / MEDIUM / LOW
    action:      str          # IMMEDIATE_SWITCH / DUAL_SOURCE / QUALIFY / MONITOR
    supplier_id: str
    note:        str          # detailed text
    reasoning:   List[str]    = field(default_factory=list)
    timeline:    str          = "Within 30 days"
    impact:      str          = "Medium"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "priority":    self.priority,
            "action":      self.action,
            "supplier_id": self.supplier_id,
            "note":        self.note,
            "reasoning":   self.reasoning,
            "timeline":    self.timeline,
            "impact":      self.impact,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation Result
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RecommendationResult:
    """
    Full recommendation for one at-risk supplier.
    Contains ranked alternative candidates and procurement notes.
    """
    at_risk_supplier_id:   str
    at_risk_supplier_name: str
    risk_reason:           str
    stockout_risk:         str = "UNKNOWN"
    revenue_at_risk_usd:   float = 0.0
    delay_days:            float = 0.0

    candidates:            List[SupplierCandidate] = field(default_factory=list)
    top_recommendation:    Optional[SupplierCandidate] = None
    procurement_notes:     List[ProcurementNote] = field(default_factory=list)

    topsis_ranking:        List[Dict[str, Any]] = field(default_factory=list)
    cosine_ranking:        List[Dict[str, Any]] = field(default_factory=list)
    mcdm_ranking:          List[Dict[str, Any]] = field(default_factory=list)
    comparison_matrix:     Dict[str, Any] = field(default_factory=dict)

    explanation:           str = ""
    evaluated_at:          str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "at_risk_supplier_id":   self.at_risk_supplier_id,
            "at_risk_supplier_name": self.at_risk_supplier_name,
            "risk_reason":           self.risk_reason,
            "stockout_risk":         self.stockout_risk,
            "revenue_at_risk_usd":   round(self.revenue_at_risk_usd, 2),
            "delay_days":            round(self.delay_days, 1),
            "top_recommendation":    self.top_recommendation.to_dict() if self.top_recommendation else None,
            "candidates":            [c.to_dict() for c in self.candidates],
            "procurement_notes":     [n.to_dict() for n in self.procurement_notes],
            "topsis_ranking":        self.topsis_ranking,
            "cosine_ranking":        self.cosine_ranking,
            "mcdm_ranking":          self.mcdm_ranking,
            "comparison_matrix":     self.comparison_matrix,
            "explanation":           self.explanation,
            "evaluated_at":          self.evaluated_at,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Alternative Supplier Pool (seeded for all 12 primary suppliers)
# ─────────────────────────────────────────────────────────────────────────────
# Maps each at-risk supplier → list of realistic alternative candidates.
# KPI scores are realistic industry heuristics.

ALTERNATIVE_POOL: Dict[str, List[Dict[str, Any]]] = {
    "supplier::TSMC": [
        {"supplier_id": "alt::GLOBALFOUNDRIES", "name": "GlobalFoundries", "country_code": "US",
         "industries": ["semiconductor"], "tier": "TIER_2",
         "health_score": 78.0, "reliability_score": 80.0, "quality_score": 82.0,
         "lead_time_score": 68.0, "cost_efficiency": 75.0, "compliance_score": 85.0,
         "responsiveness": 78.0, "flexibility": 72.0, "risk_score": 12.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::INTEL_FOUNDRY", "name": "Intel Foundry Services", "country_code": "US",
         "industries": ["semiconductor"], "tier": "TIER_2",
         "health_score": 75.0, "reliability_score": 76.0, "quality_score": 80.0,
         "lead_time_score": 65.0, "cost_efficiency": 70.0, "compliance_score": 88.0,
         "responsiveness": 74.0, "flexibility": 68.0, "risk_score": 10.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::SAMSUNG_FOUNDRY", "name": "Samsung Foundry", "country_code": "KR",
         "industries": ["semiconductor"], "tier": "TIER_1",
         "health_score": 85.0, "reliability_score": 84.0, "quality_score": 88.0,
         "lead_time_score": 76.0, "cost_efficiency": 79.0, "compliance_score": 86.0,
         "responsiveness": 80.0, "flexibility": 74.0, "risk_score": 15.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::UMC", "name": "United Microelectronics (UMC)", "country_code": "TW",
         "industries": ["semiconductor"], "tier": "TIER_2",
         "health_score": 72.0, "reliability_score": 74.0, "quality_score": 76.0,
         "lead_time_score": 72.0, "cost_efficiency": 82.0, "compliance_score": 80.0,
         "responsiveness": 70.0, "flexibility": 76.0, "risk_score": 28.0, "revenue_exposure_pct": 0.0},
    ],
    "supplier::CATL": [
        {"supplier_id": "alt::LG_ENERGY", "name": "LG Energy Solution", "country_code": "KR",
         "industries": ["energy", "automotive"], "tier": "TIER_2",
         "health_score": 82.0, "reliability_score": 84.0, "quality_score": 86.0,
         "lead_time_score": 72.0, "cost_efficiency": 76.0, "compliance_score": 88.0,
         "responsiveness": 80.0, "flexibility": 72.0, "risk_score": 14.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::PANASONIC_ENERGY", "name": "Panasonic Energy", "country_code": "JP",
         "industries": ["energy", "automotive"], "tier": "TIER_2",
         "health_score": 83.0, "reliability_score": 86.0, "quality_score": 89.0,
         "lead_time_score": 68.0, "cost_efficiency": 70.0, "compliance_score": 90.0,
         "responsiveness": 78.0, "flexibility": 64.0, "risk_score": 8.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::BYD_BATTERY", "name": "BYD Battery", "country_code": "CN",
         "industries": ["energy", "automotive"], "tier": "TIER_2",
         "health_score": 79.0, "reliability_score": 78.0, "quality_score": 80.0,
         "lead_time_score": 74.0, "cost_efficiency": 88.0, "compliance_score": 74.0,
         "responsiveness": 72.0, "flexibility": 80.0, "risk_score": 30.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::SK_INNOVATION", "name": "SK Innovation", "country_code": "KR",
         "industries": ["energy", "automotive"], "tier": "TIER_2",
         "health_score": 80.0, "reliability_score": 81.0, "quality_score": 83.0,
         "lead_time_score": 70.0, "cost_efficiency": 74.0, "compliance_score": 82.0,
         "responsiveness": 76.0, "flexibility": 70.0, "risk_score": 12.0, "revenue_exposure_pct": 0.0},
    ],
    "supplier::SAMSUNG": [
        {"supplier_id": "alt::BOE_DISPLAY", "name": "BOE Technology", "country_code": "CN",
         "industries": ["electronics"], "tier": "TIER_2",
         "health_score": 74.0, "reliability_score": 73.0, "quality_score": 75.0,
         "lead_time_score": 76.0, "cost_efficiency": 88.0, "compliance_score": 72.0,
         "responsiveness": 70.0, "flexibility": 80.0, "risk_score": 32.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::LG_DISPLAY", "name": "LG Display", "country_code": "KR",
         "industries": ["electronics"], "tier": "TIER_2",
         "health_score": 81.0, "reliability_score": 82.0, "quality_score": 84.0,
         "lead_time_score": 72.0, "cost_efficiency": 76.0, "compliance_score": 85.0,
         "responsiveness": 79.0, "flexibility": 70.0, "risk_score": 10.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::TIANMA", "name": "Tianma Microelectronics", "country_code": "CN",
         "industries": ["electronics"], "tier": "TIER_3",
         "health_score": 70.0, "reliability_score": 71.0, "quality_score": 72.0,
         "lead_time_score": 74.0, "cost_efficiency": 86.0, "compliance_score": 70.0,
         "responsiveness": 68.0, "flexibility": 78.0, "risk_score": 28.0, "revenue_exposure_pct": 0.0},
    ],
    "supplier::ASML": [
        {"supplier_id": "alt::CANON_SEMI", "name": "Canon Semiconductor Equipment", "country_code": "JP",
         "industries": ["semiconductor", "equipment"], "tier": "TIER_2",
         "health_score": 76.0, "reliability_score": 78.0, "quality_score": 82.0,
         "lead_time_score": 60.0, "cost_efficiency": 65.0, "compliance_score": 86.0,
         "responsiveness": 72.0, "flexibility": 52.0, "risk_score": 8.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::NIKON_PREC", "name": "Nikon Precision", "country_code": "JP",
         "industries": ["semiconductor", "equipment"], "tier": "TIER_2",
         "health_score": 74.0, "reliability_score": 76.0, "quality_score": 80.0,
         "lead_time_score": 58.0, "cost_efficiency": 62.0, "compliance_score": 84.0,
         "responsiveness": 70.0, "flexibility": 50.0, "risk_score": 7.0, "revenue_exposure_pct": 0.0},
    ],
    "supplier::BOSCH": [
        {"supplier_id": "alt::CONTINENTAL", "name": "Continental AG", "country_code": "DE",
         "industries": ["automotive", "electronics"], "tier": "TIER_2",
         "health_score": 82.0, "reliability_score": 84.0, "quality_score": 86.0,
         "lead_time_score": 78.0, "cost_efficiency": 75.0, "compliance_score": 88.0,
         "responsiveness": 82.0, "flexibility": 74.0, "risk_score": 9.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::DENSO", "name": "Denso Corporation", "country_code": "JP",
         "industries": ["automotive"], "tier": "TIER_2",
         "health_score": 86.0, "reliability_score": 88.0, "quality_score": 91.0,
         "lead_time_score": 76.0, "cost_efficiency": 72.0, "compliance_score": 90.0,
         "responsiveness": 84.0, "flexibility": 68.0, "risk_score": 7.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::ZF_GROUP", "name": "ZF Friedrichshafen", "country_code": "DE",
         "industries": ["automotive"], "tier": "TIER_2",
         "health_score": 80.0, "reliability_score": 82.0, "quality_score": 84.0,
         "lead_time_score": 74.0, "cost_efficiency": 76.0, "compliance_score": 86.0,
         "responsiveness": 78.0, "flexibility": 72.0, "risk_score": 10.0, "revenue_exposure_pct": 0.0},
    ],
    "supplier::QUALCOMM": [
        {"supplier_id": "alt::MEDIATEK", "name": "MediaTek", "country_code": "TW",
         "industries": ["semiconductor", "telecom"], "tier": "TIER_2",
         "health_score": 80.0, "reliability_score": 78.0, "quality_score": 80.0,
         "lead_time_score": 76.0, "cost_efficiency": 84.0, "compliance_score": 80.0,
         "responsiveness": 76.0, "flexibility": 80.0, "risk_score": 22.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::SAMSUNG_LSI", "name": "Samsung System LSI", "country_code": "KR",
         "industries": ["semiconductor"], "tier": "TIER_2",
         "health_score": 82.0, "reliability_score": 82.0, "quality_score": 85.0,
         "lead_time_score": 74.0, "cost_efficiency": 78.0, "compliance_score": 84.0,
         "responsiveness": 78.0, "flexibility": 72.0, "risk_score": 14.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::APPLE_CHIP", "name": "Apple Silicon (alt.)", "country_code": "US",
         "industries": ["semiconductor"], "tier": "TIER_1",
         "health_score": 88.0, "reliability_score": 90.0, "quality_score": 94.0,
         "lead_time_score": 65.0, "cost_efficiency": 60.0, "compliance_score": 88.0,
         "responsiveness": 72.0, "flexibility": 55.0, "risk_score": 8.0, "revenue_exposure_pct": 0.0},
    ],
    "supplier::CATL": [
        {"supplier_id": "alt::LG_ENERGY", "name": "LG Energy Solution", "country_code": "KR",
         "industries": ["energy", "automotive"], "tier": "TIER_2",
         "health_score": 82.0, "reliability_score": 84.0, "quality_score": 86.0,
         "lead_time_score": 72.0, "cost_efficiency": 76.0, "compliance_score": 88.0,
         "responsiveness": 80.0, "flexibility": 72.0, "risk_score": 14.0, "revenue_exposure_pct": 0.0},
    ],
    "supplier::FOXCONN": [
        {"supplier_id": "alt::FLEXTRONICS", "name": "Flex Ltd", "country_code": "SG",
         "industries": ["electronics", "manufacturing"], "tier": "TIER_2",
         "health_score": 76.0, "reliability_score": 78.0, "quality_score": 80.0,
         "lead_time_score": 76.0, "cost_efficiency": 84.0, "compliance_score": 78.0,
         "responsiveness": 74.0, "flexibility": 84.0, "risk_score": 12.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::JABIL", "name": "Jabil Circuit", "country_code": "US",
         "industries": ["electronics", "manufacturing"], "tier": "TIER_2",
         "health_score": 78.0, "reliability_score": 79.0, "quality_score": 80.0,
         "lead_time_score": 74.0, "cost_efficiency": 80.0, "compliance_score": 80.0,
         "responsiveness": 76.0, "flexibility": 80.0, "risk_score": 8.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::PEGATRON", "name": "Pegatron", "country_code": "TW",
         "industries": ["electronics", "manufacturing"], "tier": "TIER_2",
         "health_score": 75.0, "reliability_score": 76.0, "quality_score": 78.0,
         "lead_time_score": 78.0, "cost_efficiency": 88.0, "compliance_score": 74.0,
         "responsiveness": 72.0, "flexibility": 82.0, "risk_score": 25.0, "revenue_exposure_pct": 0.0},
    ],
    "supplier::MAERSK": [
        {"supplier_id": "alt::MSC_SHIPPING", "name": "MSC Mediterranean Shipping", "country_code": "CH",
         "industries": ["logistics", "shipping"], "tier": "TIER_2",
         "health_score": 77.0, "reliability_score": 78.0, "quality_score": 79.0,
         "lead_time_score": 75.0, "cost_efficiency": 78.0, "compliance_score": 82.0,
         "responsiveness": 72.0, "flexibility": 70.0, "risk_score": 10.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::CMA_CGM", "name": "CMA CGM Group", "country_code": "FR",
         "industries": ["logistics", "shipping"], "tier": "TIER_2",
         "health_score": 75.0, "reliability_score": 76.0, "quality_score": 78.0,
         "lead_time_score": 73.0, "cost_efficiency": 76.0, "compliance_score": 80.0,
         "responsiveness": 70.0, "flexibility": 72.0, "risk_score": 12.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::DHL_SUPPLY", "name": "DHL Supply Chain", "country_code": "DE",
         "industries": ["logistics"], "tier": "TIER_2",
         "health_score": 80.0, "reliability_score": 82.0, "quality_score": 82.0,
         "lead_time_score": 80.0, "cost_efficiency": 72.0, "compliance_score": 86.0,
         "responsiveness": 80.0, "flexibility": 76.0, "risk_score": 7.0, "revenue_exposure_pct": 0.0},
    ],
    "supplier::MURATA": [
        {"supplier_id": "alt::TDK_ALT", "name": "TDK Corp (passive)", "country_code": "JP",
         "industries": ["electronics", "components"], "tier": "TIER_2",
         "health_score": 87.0, "reliability_score": 88.0, "quality_score": 90.0,
         "lead_time_score": 76.0, "cost_efficiency": 72.0, "compliance_score": 90.0,
         "responsiveness": 80.0, "flexibility": 58.0, "risk_score": 6.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::VISHAY", "name": "Vishay Intertechnology", "country_code": "US",
         "industries": ["electronics", "components"], "tier": "TIER_2",
         "health_score": 80.0, "reliability_score": 82.0, "quality_score": 84.0,
         "lead_time_score": 74.0, "cost_efficiency": 78.0, "compliance_score": 84.0,
         "responsiveness": 78.0, "flexibility": 72.0, "risk_score": 8.0, "revenue_exposure_pct": 0.0},
    ],
    "supplier::TDK": [
        {"supplier_id": "alt::MURATA_ALT", "name": "Murata Mfg (magnetic)", "country_code": "JP",
         "industries": ["electronics", "components"], "tier": "TIER_2",
         "health_score": 89.0, "reliability_score": 90.0, "quality_score": 93.0,
         "lead_time_score": 78.0, "cost_efficiency": 70.0, "compliance_score": 92.0,
         "responsiveness": 82.0, "flexibility": 60.0, "risk_score": 5.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::AVX_KYOCERA", "name": "AVX (Kyocera)", "country_code": "US",
         "industries": ["electronics", "components"], "tier": "TIER_3",
         "health_score": 78.0, "reliability_score": 80.0, "quality_score": 82.0,
         "lead_time_score": 72.0, "cost_efficiency": 76.0, "compliance_score": 82.0,
         "responsiveness": 76.0, "flexibility": 68.0, "risk_score": 8.0, "revenue_exposure_pct": 0.0},
    ],
    "supplier::SHINKO": [
        {"supplier_id": "alt::IBIDEN", "name": "Ibiden Co.", "country_code": "JP",
         "industries": ["semiconductor", "components"], "tier": "TIER_2",
         "health_score": 84.0, "reliability_score": 86.0, "quality_score": 88.0,
         "lead_time_score": 70.0, "cost_efficiency": 72.0, "compliance_score": 86.0,
         "responsiveness": 78.0, "flexibility": 60.0, "risk_score": 7.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::UNIMICRON", "name": "Unimicron Technology", "country_code": "TW",
         "industries": ["semiconductor", "components"], "tier": "TIER_2",
         "health_score": 79.0, "reliability_score": 80.0, "quality_score": 82.0,
         "lead_time_score": 72.0, "cost_efficiency": 80.0, "compliance_score": 80.0,
         "responsiveness": 74.0, "flexibility": 68.0, "risk_score": 22.0, "revenue_exposure_pct": 0.0},
    ],
    "supplier::EVERGREEN": [
        {"supplier_id": "alt::COSCO_SHIP", "name": "COSCO Shipping", "country_code": "CN",
         "industries": ["logistics", "shipping"], "tier": "TIER_2",
         "health_score": 74.0, "reliability_score": 73.0, "quality_score": 75.0,
         "lead_time_score": 72.0, "cost_efficiency": 82.0, "compliance_score": 72.0,
         "responsiveness": 68.0, "flexibility": 76.0, "risk_score": 30.0, "revenue_exposure_pct": 0.0},
        {"supplier_id": "alt::HAPAG_LLOYD", "name": "Hapag-Lloyd", "country_code": "DE",
         "industries": ["logistics", "shipping"], "tier": "TIER_2",
         "health_score": 76.0, "reliability_score": 78.0, "quality_score": 80.0,
         "lead_time_score": 74.0, "cost_efficiency": 74.0, "compliance_score": 82.0,
         "responsiveness": 74.0, "flexibility": 72.0, "risk_score": 10.0, "revenue_exposure_pct": 0.0},
    ],
}
