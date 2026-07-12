"""
Conditional routing functions for the LangGraph StateGraph.

Each function here is a 'conditional edge router':
  - Receives the current WorkflowState
  - Returns a string key that LangGraph uses to select the next node

This implements the 'Conditional Routing' algorithm:
  - After news_agent:     route on whether events were found
  - After risk_agent:     route on maximum risk severity
  - After graph/supplier/inventory: route on agent failure

State Machine transition logic:
                        ┌── "has_events" ──→ risk_agent
  news_agent ───────────┤
                        └── "no_events"  ──→ finalize
                        └── "error"      ──→ finalize

                        ┌── "high_risk" ──→ graph_agent
  risk_agent ───────────┤── "normal"    ──→ graph_agent
                        └── "error"     ──→ finalize

  graph_agent ──────────┬── "continue" ──→ supplier_agent
                        └── "error"    ──→ finalize

  supplier_agent ───────┬── "continue" ──→ inventory_agent
                        └── "error"    ──→ finalize

  inventory_agent ──────┬── "continue" ──→ recommendation_agent
                        └── "error"    ──→ finalize
"""

from __future__ import annotations

import logging
from typing import Literal

from app.orchestrator.state import WorkflowState

logger = logging.getLogger("orchestrator.router")


def route_after_news(
    state: WorkflowState,
) -> Literal["has_events", "no_events", "error"]:
    """
    After news_agent completes: decide whether to continue the pipeline.

    Phase 2 MVP: news_events is always [] (stub), so we route 'has_events'
    to ensure the full pipeline executes and all infrastructure is validated.

    Phase 3+: returns 'no_events' when the news agent genuinely found nothing.
    """
    if "news_agent" in state.get("failed_agents", []):
        logger.warning("[router] news_agent failed — routing to error path")
        return "error"

    events = state.get("news_events", [])

    # Phase 2 MVP: always continue through the full pipeline
    # (even with empty events) so the entire orchestrator is exercised
    if events:
        logger.info(f"[router] news_agent found {len(events)} event(s) → risk_agent")
    else:
        logger.info("[router] news_agent found 0 events (stub mode) → risk_agent")

    return "has_events"


def route_after_risk(
    state: WorkflowState,
) -> Literal["high_risk", "normal", "error"]:
    """
    After risk_agent: route based on the maximum severity found.

    Score thresholds:
      ≥ 80 → high_risk  (triggers fast-path; Phase 3+ may parallelise here)
      < 80 → normal
    """
    if "risk_agent" in state.get("failed_agents", []):
        logger.warning("[router] risk_agent failed — routing to error path")
        return "error"

    assessments = state.get("risk_assessments", [])
    if not assessments:
        return "normal"

    max_score = max((a.get("score", 0) for a in assessments), default=0)
    if max_score >= 80:
        logger.info(f"[router] High risk detected (max_score={max_score}) → high_risk path")
        return "high_risk"

    return "normal"


def route_after_graph(
    state: WorkflowState,
) -> Literal["continue", "error"]:
    if "graph_agent" in state.get("failed_agents", []):
        logger.warning("[router] graph_agent failed — routing to error path")
        return "error"
    return "continue"


def route_after_supplier(
    state: WorkflowState,
) -> Literal["continue", "error"]:
    if "supplier_agent" in state.get("failed_agents", []):
        logger.warning("[router] supplier_agent failed — routing to error path")
        return "error"
    return "continue"


def route_after_inventory(
    state: WorkflowState,
) -> Literal["continue", "error"]:
    if "inventory_agent" in state.get("failed_agents", []):
        logger.warning("[router] inventory_agent failed — routing to error path")
        return "error"
    return "continue"
