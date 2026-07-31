"""
SupplierInventoryTransaction — immutable stock movement ledger.

APPEND-ONLY: Never UPDATE or DELETE rows.
quantity_delta: positive = added; negative = removed.
quantity_after: post-transaction snapshot for replay and audit.

transaction_type values:
  INBOUND      — goods received from supplier / PO
  OUTBOUND     — goods shipped to customer / consumed
  ADJUSTMENT   — manual correction (requires notes)
  RESERVE      — soft reservation for pending order
  RELEASE      — release of a prior reservation
  WRITE_OFF    — damaged / expired stock written off
  RETURN       — goods returned from customer
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.models.base import Base

TRANSACTION_TYPE_VALUES = (
    "INBOUND", "OUTBOUND", "ADJUSTMENT", "RESERVE",
    "RELEASE", "WRITE_OFF", "RETURN",
)


class SupplierInventoryTransaction(Base):
    __tablename__ = "supplier_inventory_transactions"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Hard FK → supplier_inventory_items.id
    item_id         = Column(
        UUID(as_uuid=True),
        ForeignKey("supplier_inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Soft FK → supplier_accounts.supabase_uid
    supplier_id     = Column(Text, nullable=False, index=True)

    # INBOUND | OUTBOUND | ADJUSTMENT | RESERVE | RELEASE | WRITE_OFF | RETURN
    transaction_type = Column(String(30), nullable=False, index=True)

    # positive = stock in; negative = stock out
    quantity_delta  = Column(Integer, nullable=False)
    quantity_after  = Column(Integer, nullable=False)  # immutable snapshot

    # Reference to source event
    reference_id    = Column(Text, nullable=True)       # PO#, shipment_id, ticket_id …
    reference_type  = Column(Text, nullable=True)       # PURCHASE_ORDER | SHIPMENT | MANUAL …

    unit_cost_usd   = Column(Numeric(14, 4), nullable=True)
    notes           = Column(Text, nullable=True)
    created_by      = Column(Text, nullable=True)       # supabase_uid of actor

    # No updated_at — immutable ledger
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
