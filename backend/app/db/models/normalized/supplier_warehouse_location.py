"""
SupplierWarehouseLocation — normalized warehouse record per supplier.

Replaces warehouse data stored in company profile JSON.
Tracks storage type for cold-chain, hazmat, bonded-warehouse compliance.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class SupplierWarehouseLocation(Base):
    __tablename__ = "supplier_warehouse_locations"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Soft FK → supplier_accounts.supabase_uid
    supplier_id     = Column(Text, nullable=False, index=True)

    name            = Column(Text, nullable=False)
    address         = Column(Text, nullable=True)
    city            = Column(Text, nullable=True)
    state_province  = Column(Text, nullable=True)
    country         = Column(Text, nullable=False, index=True)
    postal_code     = Column(Text, nullable=True)

    # AMBIENT | COLD_CHAIN | HAZMAT | BONDED | GENERAL
    storage_type    = Column(String(30), nullable=True, index=True)

    capacity_units  = Column(Integer, nullable=True)
    capacity_sqft   = Column(Integer, nullable=True)
    phone           = Column(Text, nullable=True)
    is_active       = Column(Boolean, nullable=False, default=True, index=True)
    notes           = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
