"""
DB model: WorkflowRun — Persists each full orchestration workflow execution.

One row per `orchestrator.trigger()` call. Stores final agent_results JSON
so the entire workflow output is queryable from the database.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    execution_id = Column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        comment="UUID that maps to WorkflowState.execution_id",
    )
    trigger_type = Column(
        String(50),
        nullable=False,
        default="manual",
        comment="manual | scheduled | event",
    )
    status = Column(
        String(50),
        nullable=False,
        default="running",
        comment="WorkflowStatus enum value",
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    # Full list of AgentResult dicts from all agents in this run
    agent_results = Column(JSON, nullable=True)
    # High-level error summary if workflow failed
    error_summary = Column(Text, nullable=True)
    # The payload that triggered this run
    trigger_payload = Column(JSON, nullable=True)
    # Quick access counts (denormalized for fast dashboard queries)
    news_event_count       = Column(String(10), nullable=True)
    risk_assessment_count  = Column(String(10), nullable=True)
    recommendation_count   = Column(String(10), nullable=True)
