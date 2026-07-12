"""
Phase 5: Knowledge Graph — Node & Edge Type Definitions

Supply chain graph entities:
  Nodes: SUPPLIER | COMPONENT | PRODUCT | COUNTRY | RISK_EVENT
  Edges: SUPPLIES | MANUFACTURES | SHIPS_TO | DEPENDS_ON | AFFECTED_BY | LOCATED_IN

Each node/edge carries typed attributes for algorithm weighting and UI rendering.

Node ID Convention (to avoid collisions across types):
  Supplier   → "supplier::<name>"
  Component  → "component::<name>"
  Product    → "product::<name>"
  Country    → "country::<iso_code>"
  Risk Event → "risk::<assessment_id>"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class NodeType(str, Enum):
    SUPPLIER    = "supplier"
    COMPONENT   = "component"
    PRODUCT     = "product"
    COUNTRY     = "country"
    RISK_EVENT  = "risk_event"


class EdgeType(str, Enum):
    SUPPLIES     = "supplies"        # Supplier → Component
    MANUFACTURES = "manufactures"    # Supplier → Product
    DEPENDS_ON   = "depends_on"      # Product  → Component
    SHIPS_TO     = "ships_to"        # Supplier → Country (shipping route)
    AFFECTED_BY  = "affected_by"     # Supplier / Component → RiskEvent
    LOCATED_IN   = "located_in"      # Supplier → Country


class NodeStatus(str, Enum):
    ACTIVE   = "active"
    AT_RISK  = "at_risk"
    CRITICAL = "critical"
    OFFLINE  = "offline"
    UNKNOWN  = "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# Typed node & edge dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GraphNode:
    """
    A single node in the supply chain DiGraph.

    node_id: Unique string (use ID convention above, e.g. "supplier::TSMC")
    node_type: One of NodeType enums
    label: Human-readable display name
    risk_score: 0-100 float (inherited from Phase 4 risk_assessments)
    tier: Supplier tier (1/2/3) — only relevant for SUPPLIER nodes
    country_code: ISO-2 code of operating country
    status: Operational status
    metadata: Arbitrary extra data (used by serializer for UI tooltips)
    """
    node_id:      str
    node_type:    NodeType
    label:        str
    risk_score:   float             = 0.0
    tier:         Optional[int]     = None
    country_code: Optional[str]     = None
    status:       NodeStatus        = NodeStatus.ACTIVE
    metadata:     Dict[str, Any]    = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id":      self.node_id,
            "node_type":    self.node_type.value,
            "label":        self.label,
            "risk_score":   self.risk_score,
            "tier":         self.tier,
            "country_code": self.country_code,
            "status":       self.status.value,
            "metadata":     self.metadata,
        }

    @staticmethod
    def make_id(node_type: NodeType, name: str) -> str:
        """Canonical ID: 'supplier::TSMC', 'country::TW', etc."""
        return f"{node_type.value}::{name.strip().upper()}"


@dataclass
class GraphEdge:
    """
    A directed edge in the supply chain DiGraph.

    source_id:    Source node_id
    target_id:    Target node_id
    edge_type:    Relationship type (EdgeType)
    weight:       Routing weight used by Dijkstra (lower = preferred path)
    risk_weight:  Risk-adjusted weight (risk_score on the source node / 100)
    label:        Optional display label for React Flow
    metadata:     Arbitrary extra attributes
    """
    source_id:   str
    target_id:   str
    edge_type:   EdgeType
    weight:      float            = 1.0
    risk_weight: float            = 1.0
    label:       str              = ""
    metadata:    Dict[str, Any]   = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id":   self.source_id,
            "target_id":   self.target_id,
            "edge_type":   self.edge_type.value,
            "weight":      self.weight,
            "risk_weight": self.risk_weight,
            "label":       self.label,
            "metadata":    self.metadata,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Seed data — baseline supply chain graph topology
# ─────────────────────────────────────────────────────────────────────────────
# This provides a minimal seeded graph so the agent has something to work with
# even before real supplier data (Phase 6) is ingested.

SEED_NODES: List[GraphNode] = [
    # ── Tier 1 Suppliers ──────────────────────────────────────────────────────
    GraphNode("supplier::TSMC",        NodeType.SUPPLIER,   "TSMC",             risk_score=55.0, tier=1, country_code="TW"),
    GraphNode("supplier::SAMSUNG",     NodeType.SUPPLIER,   "Samsung",          risk_score=30.0, tier=1, country_code="KR"),
    GraphNode("supplier::ASML",        NodeType.SUPPLIER,   "ASML",             risk_score=25.0, tier=1, country_code="NL"),
    GraphNode("supplier::BOSCH",       NodeType.SUPPLIER,   "Bosch",            risk_score=20.0, tier=1, country_code="DE"),
    GraphNode("supplier::QUALCOMM",    NodeType.SUPPLIER,   "Qualcomm",         risk_score=35.0, tier=1, country_code="US"),
    GraphNode("supplier::CATL",        NodeType.SUPPLIER,   "CATL",             risk_score=45.0, tier=1, country_code="CN"),
    GraphNode("supplier::FOXCONN",     NodeType.SUPPLIER,   "Foxconn",          risk_score=50.0, tier=1, country_code="TW"),
    GraphNode("supplier::MAERSK",      NodeType.SUPPLIER,   "Maersk",           risk_score=40.0, tier=1, country_code="DK"),

    # ── Tier 2 Suppliers ──────────────────────────────────────────────────────
    GraphNode("supplier::SHINKO",      NodeType.SUPPLIER,   "Shinko Electric",  risk_score=30.0, tier=2, country_code="JP"),
    GraphNode("supplier::EVERGREEN",   NodeType.SUPPLIER,   "Evergreen Marine", risk_score=45.0, tier=2, country_code="TW"),
    GraphNode("supplier::MURATA",      NodeType.SUPPLIER,   "Murata Mfg",       risk_score=20.0, tier=2, country_code="JP"),
    GraphNode("supplier::TDK",         NodeType.SUPPLIER,   "TDK Corp",         risk_score=22.0, tier=2, country_code="JP"),

    # ── Components ────────────────────────────────────────────────────────────
    GraphNode("component::ADVANCED_CHIP",   NodeType.COMPONENT, "Advanced Chip (3nm)",  risk_score=60.0),
    GraphNode("component::MEMORY",          NodeType.COMPONENT, "DRAM / NAND Memory",   risk_score=30.0),
    GraphNode("component::BATTERY_CELL",    NodeType.COMPONENT, "Li-Ion Battery Cell",  risk_score=45.0),
    GraphNode("component::MCU",             NodeType.COMPONENT, "Automotive MCU",       risk_score=35.0),
    GraphNode("component::CAPACITOR",       NodeType.COMPONENT, "MLCC Capacitor",       risk_score=20.0),
    GraphNode("component::INDUCTOR",        NodeType.COMPONENT, "Power Inductor",       risk_score=20.0),
    GraphNode("component::EUV_WAFER",       NodeType.COMPONENT, "EUV Lithography Wafer",risk_score=55.0),
    GraphNode("component::NEON_GAS",        NodeType.COMPONENT, "Neon Gas (fab-grade)",  risk_score=70.0),

    # ── Products ──────────────────────────────────────────────────────────────
    GraphNode("product::SMARTPHONE",    NodeType.PRODUCT, "Smartphone",       risk_score=55.0),
    GraphNode("product::EV_CAR",        NodeType.PRODUCT, "Electric Vehicle", risk_score=50.0),
    GraphNode("product::SERVER",        NodeType.PRODUCT, "Data Center Server",risk_score=60.0),
    GraphNode("product::LAPTOP",        NodeType.PRODUCT, "Laptop / PC",      risk_score=45.0),

    # ── Countries ─────────────────────────────────────────────────────────────
    GraphNode("country::TW", NodeType.COUNTRY, "Taiwan",       risk_score=70.0, country_code="TW"),
    GraphNode("country::CN", NodeType.COUNTRY, "China",        risk_score=65.0, country_code="CN"),
    GraphNode("country::KR", NodeType.COUNTRY, "South Korea",  risk_score=35.0, country_code="KR"),
    GraphNode("country::JP", NodeType.COUNTRY, "Japan",        risk_score=30.0, country_code="JP"),
    GraphNode("country::US", NodeType.COUNTRY, "United States",risk_score=20.0, country_code="US"),
    GraphNode("country::DE", NodeType.COUNTRY, "Germany",      risk_score=15.0, country_code="DE"),
    GraphNode("country::NL", NodeType.COUNTRY, "Netherlands",  risk_score=15.0, country_code="NL"),
    GraphNode("country::IN", NodeType.COUNTRY, "India",        risk_score=40.0, country_code="IN"),
]

SEED_EDGES: List[GraphEdge] = [
    # ── Supplier → Component (SUPPLIES) ──────────────────────────────────────
    GraphEdge("supplier::TSMC",      "component::ADVANCED_CHIP",  EdgeType.SUPPLIES,     weight=1.0, risk_weight=0.55),
    GraphEdge("supplier::TSMC",      "component::EUV_WAFER",      EdgeType.SUPPLIES,     weight=1.0, risk_weight=0.55),
    GraphEdge("supplier::SAMSUNG",   "component::MEMORY",         EdgeType.SUPPLIES,     weight=1.0, risk_weight=0.30),
    GraphEdge("supplier::SAMSUNG",   "component::ADVANCED_CHIP",  EdgeType.SUPPLIES,     weight=1.2, risk_weight=0.30),
    GraphEdge("supplier::ASML",      "component::EUV_WAFER",      EdgeType.SUPPLIES,     weight=1.0, risk_weight=0.25),
    GraphEdge("supplier::BOSCH",     "component::MCU",            EdgeType.SUPPLIES,     weight=1.0, risk_weight=0.20),
    GraphEdge("supplier::QUALCOMM",  "component::ADVANCED_CHIP",  EdgeType.SUPPLIES,     weight=1.5, risk_weight=0.35),
    GraphEdge("supplier::CATL",      "component::BATTERY_CELL",   EdgeType.SUPPLIES,     weight=1.0, risk_weight=0.45),
    GraphEdge("supplier::MURATA",    "component::CAPACITOR",      EdgeType.SUPPLIES,     weight=1.0, risk_weight=0.20),
    GraphEdge("supplier::MURATA",    "component::INDUCTOR",       EdgeType.SUPPLIES,     weight=1.0, risk_weight=0.20),
    GraphEdge("supplier::TDK",       "component::CAPACITOR",      EdgeType.SUPPLIES,     weight=1.1, risk_weight=0.22),
    GraphEdge("supplier::SHINKO",    "component::ADVANCED_CHIP",  EdgeType.SUPPLIES,     weight=2.0, risk_weight=0.30),

    # ── Component → Product (DEPENDS_ON) ─────────────────────────────────────
    GraphEdge("component::ADVANCED_CHIP",   "product::SMARTPHONE", EdgeType.DEPENDS_ON, weight=1.0, risk_weight=0.60),
    GraphEdge("component::ADVANCED_CHIP",   "product::LAPTOP",     EdgeType.DEPENDS_ON, weight=1.0, risk_weight=0.60),
    GraphEdge("component::ADVANCED_CHIP",   "product::SERVER",     EdgeType.DEPENDS_ON, weight=1.0, risk_weight=0.60),
    GraphEdge("component::MEMORY",          "product::SMARTPHONE", EdgeType.DEPENDS_ON, weight=1.0, risk_weight=0.30),
    GraphEdge("component::MEMORY",          "product::SERVER",     EdgeType.DEPENDS_ON, weight=1.0, risk_weight=0.30),
    GraphEdge("component::MEMORY",          "product::LAPTOP",     EdgeType.DEPENDS_ON, weight=1.0, risk_weight=0.30),
    GraphEdge("component::BATTERY_CELL",    "product::EV_CAR",     EdgeType.DEPENDS_ON, weight=1.0, risk_weight=0.45),
    GraphEdge("component::BATTERY_CELL",    "product::SMARTPHONE", EdgeType.DEPENDS_ON, weight=1.1, risk_weight=0.45),
    GraphEdge("component::MCU",             "product::EV_CAR",     EdgeType.DEPENDS_ON, weight=1.0, risk_weight=0.35),
    GraphEdge("component::CAPACITOR",       "product::SMARTPHONE", EdgeType.DEPENDS_ON, weight=1.0, risk_weight=0.20),
    GraphEdge("component::CAPACITOR",       "product::EV_CAR",     EdgeType.DEPENDS_ON, weight=1.0, risk_weight=0.20),
    GraphEdge("component::EUV_WAFER",       "component::ADVANCED_CHIP", EdgeType.DEPENDS_ON, weight=1.0, risk_weight=0.55),
    GraphEdge("component::NEON_GAS",        "component::EUV_WAFER",    EdgeType.DEPENDS_ON, weight=1.0, risk_weight=0.70),

    # ── Supplier → Country (LOCATED_IN) ──────────────────────────────────────
    GraphEdge("supplier::TSMC",      "country::TW", EdgeType.LOCATED_IN, weight=1.0),
    GraphEdge("supplier::SAMSUNG",   "country::KR", EdgeType.LOCATED_IN, weight=1.0),
    GraphEdge("supplier::ASML",      "country::NL", EdgeType.LOCATED_IN, weight=1.0),
    GraphEdge("supplier::BOSCH",     "country::DE", EdgeType.LOCATED_IN, weight=1.0),
    GraphEdge("supplier::QUALCOMM",  "country::US", EdgeType.LOCATED_IN, weight=1.0),
    GraphEdge("supplier::CATL",      "country::CN", EdgeType.LOCATED_IN, weight=1.0),
    GraphEdge("supplier::FOXCONN",   "country::TW", EdgeType.LOCATED_IN, weight=1.0),
    GraphEdge("supplier::MAERSK",    "country::DK", EdgeType.LOCATED_IN, weight=1.0),
    GraphEdge("supplier::MURATA",    "country::JP", EdgeType.LOCATED_IN, weight=1.0),
    GraphEdge("supplier::TDK",       "country::JP", EdgeType.LOCATED_IN, weight=1.0),
    GraphEdge("supplier::SHINKO",    "country::JP", EdgeType.LOCATED_IN, weight=1.0),

    # ── Supplier → Country (SHIPS_TO) ─────────────────────────────────────────
    GraphEdge("supplier::TSMC",      "country::US", EdgeType.SHIPS_TO, weight=2.0, risk_weight=0.55),
    GraphEdge("supplier::TSMC",      "country::DE", EdgeType.SHIPS_TO, weight=2.5, risk_weight=0.55),
    GraphEdge("supplier::SAMSUNG",   "country::US", EdgeType.SHIPS_TO, weight=1.5, risk_weight=0.30),
    GraphEdge("supplier::CATL",      "country::DE", EdgeType.SHIPS_TO, weight=2.0, risk_weight=0.45),
    GraphEdge("supplier::FOXCONN",   "country::US", EdgeType.SHIPS_TO, weight=1.5, risk_weight=0.50),
    GraphEdge("supplier::MAERSK",    "country::US", EdgeType.SHIPS_TO, weight=1.0, risk_weight=0.40),
    GraphEdge("supplier::EVERGREEN", "country::US", EdgeType.SHIPS_TO, weight=1.0, risk_weight=0.45),
]
