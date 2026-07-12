"""
DB model: AgentExecution — One row per agent run inside a workflow.

Provides a complete audit trail of every agent execution:
which workflow it belonged to, how long it took, how many retries,
whether it succeeded, and what data it produced/consumed.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Links to parent workflow run
    execution_id = Column(
        String(36),
        nullable=False,
        index=True,
        comment="FK reference to workflow_runs.execution_id",
    )
    agent_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Agent identifier, e.g. 'news_agent'",
    )

    # Execution outcome
    status = Column(
        String(50),
        nullable=False,
        comment="success | failed | skipped | stub",
    )
    retry_count = Column(Integer, default=0)
    duration_ms = Column(Integer, nullable=True)

    # Timestamps
    started_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Data snapshots (stored as JSON for flexibility across phases)
    output_data   = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
