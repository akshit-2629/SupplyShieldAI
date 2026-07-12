"""
WorkflowState — Single source of truth for the LangGraph DAG.

Each agent node receives this full state and returns only the fields it updates.
LangGraph automatically merges partial returns into the running state.

Fields annotated with Annotated[List, operator.add] are ACCUMULATORS:
multiple agents can safely append to them without overwriting each other.

State Machine positions (current_phase values):
  news_agent → risk_agent → graph_agent → supplier_agent
  → inventory_agent → recommendation_agent → finalize → completed
"""

from __future__ import annotations

import operator
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class WorkflowStatus(str, Enum):
    PENDING              = "pending"
    RUNNING              = "running"
    COMPLETED            = "completed"
    FAILED               = "failed"
    PARTIALLY_COMPLETED  = "partially_completed"


class AgentResult(TypedDict, total=False):
    """Structured result returned by each agent after execution."""
    agent_id:    str
    status:      str          # success | failed | skipped | stub
    data:        Dict[str, Any]
    error:       Optional[str]
    duration_ms: int
    retry_count: int
    timestamp:   str


class WorkflowState(TypedDict):
    """
    The complete state object flowing through the LangGraph state machine.

    This is shared across ALL agents in a single workflow run.
    Agents READ upstream data and WRITE their own output fields.

    LangGraph handles merging via the Annotated[List, operator.add] reducers —
    list fields are appended to, not replaced, on each node return.
    """

    # ── Workflow identity ──────────────────────────────────────────────────────
    execution_id:    str
    trigger_type:    str              # "manual" | "scheduled" | "event"
    trigger_payload: Dict[str, Any]

    # ── State machine position ─────────────────────────────────────────────────
    current_phase:   str
    workflow_status: str              # WorkflowStatus value

    # ── Accumulated lists (operator.add = append, never overwrite) ────────────
    agent_results:     Annotated[List[AgentResult], operator.add]
    completed_agents:  Annotated[List[str], operator.add]
    failed_agents:     Annotated[List[str], operator.add]
    errors:            Annotated[List[str], operator.add]

    # ── Inter-agent data pipeline (written by one agent, read by the next) ────
    # Phase 3 — NewsAgent output
    news_events: List[Dict[str, Any]]

    # Phase 4 — RiskAgent output
    risk_assessments: List[Dict[str, Any]]

    # Phase 5 — GraphAgent output
    graph_snapshot: Dict[str, Any]

    # Phase 6 — SupplierAgent output
    supplier_scores: List[Dict[str, Any]]

    # Phase 7 — InventoryAgent output
    inventory_projections: List[Dict[str, Any]]

    # Phase 8 — RecommendationAgent output
    recommendations: List[Dict[str, Any]]

    # ── Timing ────────────────────────────────────────────────────────────────
    started_at: str
    updated_at: str
