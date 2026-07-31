"""
OrchestratorEvent — persistent event bus for the MasterOrchestrator.

Enables:
  - Retry queue: status IN ('PENDING','FAILED') AND retry_count < max_retries
  - Event replay: full payload history per entity
  - Audit trail: every supplier action that triggers an AI pipeline run

status machine: PENDING → PROCESSING → COMPLETED | FAILED
  Failed events with retry_count < max_retries are picked up by the retry queue.
  Failed events with retry_count >= max_retries are permanently failed.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.models.base import Base

STATUS_VALUES = ("PENDING", "PROCESSING", "COMPLETED", "FAILED", "SKIPPED")


class OrchestratorEvent(Base):
    __tablename__ = "orchestrator_events"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Event classification
    event_type      = Column(String(80), nullable=False, index=True)
    source          = Column(Text, nullable=False, default="supplier_portal")
    entity_type     = Column(Text, nullable=True)                       # 'inventory' | 'shipment' | ...
    entity_id       = Column(Text, nullable=True)                       # UUID of the entity row
    supplier_id     = Column(Text, nullable=True, index=True)
    execution_id    = Column(Text, nullable=True, index=True)           # links to workflow_runs

    # Payload (event-specific structured data)
    payload         = Column(JSONB, nullable=False, default=dict)

    # Retry state machine
    status          = Column(String(20), nullable=False, default="PENDING", index=True)
    retry_count     = Column(Integer, nullable=False, default=0)
    max_retries     = Column(Integer, nullable=False, default=3)
    error_message   = Column(Text, nullable=True)

    # Timing
    created_at      = Column(DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc), index=True)
    processed_at    = Column(DateTime(timezone=True), nullable=True)
    duration_ms     = Column(Integer, nullable=True)
