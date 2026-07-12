"""
Stub agents for Phase 2 MVP.

These stubs return the correct data STRUCTURE with empty results.
They:
  • Log clearly that they are Phase N stubs
  • Emit real events on the event bus  
  • Track real execution metrics (status, timing)
  • Return properly shaped partial WorkflowState dicts

Full real implementations replace each stub in Phases 3–8 respectively.
No stub is "mock data" — they are honest placeholders with valid data contracts.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

from app.agents.base import BaseAgent
from app.orchestrator.state import WorkflowState

logger = logging.getLogger("agents.stubs")


# ─────────────────────────────────────────────────────────────────────────────
class NewsAgentStub(BaseAgent):
    """
    Phase 3: News Intelligence Agent  [STUB]

    Real Phase 3 implementation will:
    ─ Scrape RSS feeds (Reuters, BBC, FT, Bloomberg via Tavily)
    ─ Extract disruption events with country / industry / severity
    ─ Deduplicate via cosine similarity on text embeddings
    ─ Classify: NATURAL_DISASTER | GEOPOLITICAL | LABOR | REGULATORY | LOGISTICS
    """
    agent_id    = "news_agent"
    description = "Collects and classifies global supply chain disruption signals from news sources"
    version     = "0.1.0-stub"

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        logger.info("[news_agent] STUB — awaiting Phase 3 implementation")
        return {
            "news_events":      [],
            "completed_agents": ["news_agent"],
            "failed_agents":    [],
            "errors":           [],
            "agent_results": [{
                "agent_id":    "news_agent",
                "status":      "stub",
                "data":        {"events": [], "stub_phase": 3},
                "error":       None,
                "duration_ms": 0,
                "retry_count": 0,
                "timestamp":   datetime.utcnow().isoformat(),
            }],
        }


# ─────────────────────────────────────────────────────────────────────────────
class RiskAgentStub(BaseAgent):
    """
    Phase 4: Risk Assessment Agent  [STUB]

    Real Phase 4 implementation will:
    ─ Score each news event: severity × likelihood × exposure
    ─ Apply geographic / industry / dependency weights
    ─ Classify: LOW (<33) | MEDIUM (33-66) | HIGH (67-85) | CRITICAL (>85)
    ─ Track risk trajectory over time (trending up/down)
    """
    agent_id    = "risk_agent"
    description = "Converts raw disruption events into quantified business risk scores"
    version     = "0.1.0-stub"

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        logger.info("[risk_agent] STUB — awaiting Phase 4 implementation")
        return {
            "risk_assessments": [],
            "completed_agents": ["risk_agent"],
            "failed_agents":    [],
            "errors":           [],
            "agent_results": [{
                "agent_id":    "risk_agent",
                "status":      "stub",
                "data":        {"assessments": [], "stub_phase": 4},
                "error":       None,
                "duration_ms": 0,
                "retry_count": 0,
                "timestamp":   datetime.utcnow().isoformat(),
            }],
        }


# ─────────────────────────────────────────────────────────────────────────────
class GraphAgentStub(BaseAgent):
    """
    Phase 5: Knowledge Graph Agent  [STUB]

    Real Phase 5 implementation will:
    ─ Build a NetworkX DiGraph: Supplier → Component → Product → Customer
    ─ BFS/DFS blast-radius tracing from impacted supplier nodes
    ─ Degree centrality to find single-points-of-failure
    ─ Dijkstra critical path analysis for procurement lead-time
    """
    agent_id    = "graph_agent"
    description = "Builds the supply chain knowledge graph and traces disruption blast-radius"
    version     = "0.1.0-stub"

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        logger.info("[graph_agent] STUB — awaiting Phase 5 implementation")
        return {
            "graph_snapshot":   {"nodes": [], "edges": [], "stub_phase": 5},
            "completed_agents": ["graph_agent"],
            "failed_agents":    [],
            "errors":           [],
            "agent_results": [{
                "agent_id":    "graph_agent",
                "status":      "stub",
                "data":        {"node_count": 0, "edge_count": 0, "stub_phase": 5},
                "error":       None,
                "duration_ms": 0,
                "retry_count": 0,
                "timestamp":   datetime.utcnow().isoformat(),
            }],
        }


# ─────────────────────────────────────────────────────────────────────────────
class SupplierAgentStub(BaseAgent):
    """
    Phase 6: Supplier Intelligence Agent  [STUB]

    Real Phase 6 implementation will:
    ─ Evaluate supplier KPIs: reliability, cost index, lead time, compliance
    ─ Classify into Tier 1 / 2 / 3 based on revenue exposure
    ─ Apply geographic and industry risk multipliers
    ─ Track historical score trends (MoM change)
    """
    agent_id    = "supplier_agent"
    description = "Continuously evaluates and scores supplier health, reliability, and geographic risk"
    version     = "0.1.0-stub"

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        logger.info("[supplier_agent] STUB — awaiting Phase 6 implementation")
        return {
            "supplier_scores":  [],
            "completed_agents": ["supplier_agent"],
            "failed_agents":    [],
            "errors":           [],
            "agent_results": [{
                "agent_id":    "supplier_agent",
                "status":      "stub",
                "data":        {"scored": 0, "stub_phase": 6},
                "error":       None,
                "duration_ms": 0,
                "retry_count": 0,
                "timestamp":   datetime.utcnow().isoformat(),
            }],
        }


# ─────────────────────────────────────────────────────────────────────────────
class InventoryAgentStub(BaseAgent):
    """
    Phase 7: Inventory Impact Agent  [STUB]

    Real Phase 7 implementation will:
    ─ Stock Depletion: days_remaining = stock / daily_consumption
    ─ Stockout prediction when days_remaining < supplier_lead_time
    ─ Revenue impact in USD: units_short × margin_per_unit
    ─ Manufacturing delay timeline for affected product lines
    """
    agent_id    = "inventory_agent"
    description = "Predicts inventory stockouts and revenue impact from upstream supply disruptions"
    version     = "0.1.0-stub"

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        logger.info("[inventory_agent] STUB — awaiting Phase 7 implementation")
        return {
            "inventory_projections": [],
            "completed_agents":      ["inventory_agent"],
            "failed_agents":         [],
            "errors":                [],
            "agent_results": [{
                "agent_id":    "inventory_agent",
                "status":      "stub",
                "data":        {"projections": 0, "stub_phase": 7},
                "error":       None,
                "duration_ms": 0,
                "retry_count": 0,
                "timestamp":   datetime.utcnow().isoformat(),
            }],
        }


# ─────────────────────────────────────────────────────────────────────────────
class RecommendationAgentStub(BaseAgent):
    """
    Phase 8: Recommendation Agent  [STUB]

    Real Phase 8 implementation will:
    ─ TOPSIS (Multi-Criteria Decision Making): rank alternatives on n dimensions
    ─ Cosine similarity to identify matching alternative suppliers
    ─ Cost / lead-time / reliability / compliance / country-risk weight matrix
    ─ Gemini LLM for natural-language procurement recommendations
    """
    agent_id    = "recommendation_agent"
    description = "Ranks alternative suppliers using TOPSIS/MCDM and generates actionable recommendations"
    version     = "0.1.0-stub"

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        logger.info("[recommendation_agent] STUB — awaiting Phase 8 implementation")
        return {
            "recommendations":  [],
            "completed_agents": ["recommendation_agent"],
            "failed_agents":    [],
            "errors":           [],
            "agent_results": [{
                "agent_id":    "recommendation_agent",
                "status":      "stub",
                "data":        {"recommendations": 0, "stub_phase": 8},
                "error":       None,
                "duration_ms": 0,
                "retry_count": 0,
                "timestamp":   datetime.utcnow().isoformat(),
            }],
        }
