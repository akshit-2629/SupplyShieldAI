"""
DB model: AgentHealthRecord — Tracks the live health and execution statistics
of each registered agent.

One row per agent_id (primary key). Updated in-place on every agent execution.
Provides the data powering the "Agent Health" endpoint and the
AI Orchestration Center UI (Phase 16).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.db.models.base import Base


class AgentHealthRecord(Base):
    __tablename__ = "agent_health"

    # PK: the string agent ID (e.g. "news_agent", "risk_agent")
    agent_id = Column(String(100), primary_key=True)

    # Current operational state
    status  = Column(String(50), default="idle", nullable=False)
    enabled = Column(Boolean, default=True,  nullable=False)

    # Execution statistics (updated on every run)
    success_count  = Column(Integer, default=0,   nullable=False)
    failure_count  = Column(Integer, default=0,   nullable=False)
    avg_duration_ms = Column(Float,  default=0.0, nullable=False)

    # Last known error (for debugging)
    last_error = Column(Text, nullable=True)

    # Heartbeat — last time the agent reported status
    last_heartbeat = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Metadata
    description = Column(String(500), nullable=True)
    version     = Column(String(50),  nullable=True)
