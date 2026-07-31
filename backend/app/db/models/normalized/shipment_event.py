"""
SupplierShipmentEvent — normalized tracking event per shipment.

Supplements the legacy timeline JSONB column in supplier_shipments.
One row per status change / carrier scan event.

event_type values:
  DISPATCHED | PICKED_UP | IN_TRANSIT | ARRIVED_PORT
  CUSTOMS_HOLD | CUSTOMS_CLEARED | OUT_FOR_DELIVERY
  DELIVERED | EXCEPTION | RETURNED | CANCELLED | UPDATE
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.models.base import Base

EVENT_TYPE_VALUES = (
    "DISPATCHED", "PICKED_UP", "IN_TRANSIT", "ARRIVED_PORT",
    "CUSTOMS_HOLD", "CUSTOMS_CLEARED", "OUT_FOR_DELIVERY",
    "DELIVERED", "EXCEPTION", "RETURNED", "CANCELLED", "UPDATE",
)


class SupplierShipmentEvent(Base):
    __tablename__ = "supplier_shipment_events"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Hard FK → supplier_shipments.id
    shipment_id     = Column(
        UUID(as_uuid=True),
        ForeignKey("supplier_shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Soft FK → supplier_accounts.supabase_uid
    supplier_id     = Column(Text, nullable=False, index=True)

    # Tracking event type
    event_type      = Column(String(40), nullable=False, default="UPDATE", index=True)

    # Location details
    location        = Column(Text, nullable=True)
    city            = Column(Text, nullable=True)
    country         = Column(Text, nullable=True)
    latitude        = Column(Numeric(10, 7), nullable=True)
    longitude       = Column(Numeric(10, 7), nullable=True)

    notes           = Column(Text, nullable=True)
    carrier_message = Column(Text, nullable=True)

    # When the real-world event actually happened (may differ from created_at)
    recorded_at     = Column(DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc), index=True)
    created_at      = Column(DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc))
