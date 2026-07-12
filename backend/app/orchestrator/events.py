"""
EventType enum and Event dataclass for the AsyncEventBus.

Every agent publishes an event after completing its work.
The Master Orchestrator and downstream agents subscribe to
relevant event types — this is the core of the event-driven
decoupling architecture.

Event hierarchy:
  Lifecycle: AGENT_STARTED → AGENT_COMPLETED | AGENT_FAILED
  Workflow:  WORKFLOW_STARTED → WORKFLOW_COMPLETED | WORKFLOW_FAILED
  Agent output events carry the agent's computed results as payload.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict


class EventType(str, Enum):
    # ── Agent lifecycle ──────────────────────────────────────────────────────
    AGENT_STARTED        = "agent.started"
    AGENT_COMPLETED      = "agent.completed"
    AGENT_FAILED         = "agent.failed"
    AGENT_RETRYING       = "agent.retrying"
    AGENT_HEALTH_UPDATE  = "agent.health_update"

    # ── Workflow lifecycle ───────────────────────────────────────────────────
    WORKFLOW_STARTED      = "workflow.started"
    WORKFLOW_COMPLETED    = "workflow.completed"
    WORKFLOW_FAILED       = "workflow.failed"
    WORKFLOW_PHASE_CHANGED = "workflow.phase_changed"

    # ── Agent output events (inter-agent communication via event bus) ────────
    # Published after each agent completes; carries computed results in payload
    NEWS_DISRUPTION_DETECTED  = "news.disruption_detected"    # Phase 3
    RISK_SCORE_CALCULATED     = "risk.score_calculated"       # Phase 4
    BLAST_RADIUS_TRACED       = "graph.blast_radius_traced"   # Phase 5
    SUPPLIER_SCORED           = "supplier.scored"             # Phase 6
    STOCK_IMPACT_PROJECTED    = "inventory.stock_impact_projected"  # Phase 7
    RECOMMENDATIONS_GENERATED = "recommendations.generated"   # Phase 8


@dataclass
class Event:
    """
    Immutable event published to the AsyncEventBus.

    Attributes:
        type:         The event category (from EventType enum).
        source_agent: ID of the agent or component that published this event.
        payload:      Event-specific data (agent result, error info, etc.).
        execution_id: The workflow run this event belongs to.
        timestamp:    UTC datetime when the event was created.
        event_id:     Unique identifier for this specific event instance.
    """
    type:         EventType
    source_agent: str
    payload:      Dict[str, Any]
    execution_id: str = ""
    timestamp:    datetime = field(default_factory=datetime.utcnow)
    event_id:     str = field(default_factory=lambda: str(uuid.uuid4()))
