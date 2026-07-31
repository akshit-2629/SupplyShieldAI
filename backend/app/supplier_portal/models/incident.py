"""
SupplierIncident — disruption and incident reports submitted by suppliers.
Automatically triggers the News, Risk, and Graph agents via orchestrator.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, Text, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from app.db.models.base import Base


class SupplierIncident(Base):
    __tablename__ = "supplier_incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(Text, nullable=False, index=True)

    # Classification
    # MACHINE_FAILURE | FLOOD | EARTHQUAKE | STRIKE | POWER_FAILURE |
    # CYBER_ATTACK | MATERIAL_SHORTAGE | QUALITY_ISSUE | TRANSPORTATION_DELAY | OTHER
    incident_type = Column(String(40), nullable=False, index=True)

    # CRITICAL | HIGH | MEDIUM | LOW
    severity = Column(String(20), nullable=False, default="MEDIUM", index=True)

    # Current state: ACTIVE | RECOVERING | RESOLVED | CLOSED
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)

    # Free-form description
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    # Impact
    affected_products = Column(JSON, nullable=True, default=list)   # [{"sku": str, "name": str}]
    affected_countries = Column(JSON, nullable=True, default=list)  # ISO-2 codes
    estimated_recovery_days = Column(Integer, nullable=True)
    capacity_impact_pct = Column(Integer, nullable=True)           # 0-100

    # Attachments [{"file_id": str, "name": str, "url": str, "type": str}]
    attachments = Column(JSON, nullable=True, default=list)

    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Metadata
    ip_address = Column(Text, nullable=True)
    is_deleted = Column(Integer, nullable=False, default=0)  # soft delete flag

    reported_at = Column(DateTime(timezone=True), nullable=False,
                         default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
