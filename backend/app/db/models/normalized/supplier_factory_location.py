"""
SupplierFactoryLocation — normalized factory location record.

Replaces the JSON locations array in supplier_company_profiles.
One row per physical factory site. A supplier may have many factories.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class SupplierFactoryLocation(Base):
    __tablename__ = "supplier_factory_locations"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Soft FK → supplier_accounts.supabase_uid  (TEXT, not hard FK — Supabase auth boundary)
    supplier_id     = Column(Text, nullable=False, index=True)

    # Identity
    location_name   = Column(Text, nullable=False)
    address         = Column(Text, nullable=True)
    city            = Column(Text, nullable=True)
    state_province  = Column(Text, nullable=True)
    country         = Column(Text, nullable=False, index=True)
    postal_code     = Column(Text, nullable=True)

    # Flags
    is_primary      = Column(Boolean, nullable=False, default=False, index=True)
    is_active       = Column(Boolean, nullable=False, default=True,  index=True)

    # Geo-coordinates (for map integration / IoT sensor grid)
    latitude        = Column(Numeric(10, 7), nullable=True)
    longitude       = Column(Numeric(10, 7), nullable=True)

    # Operational metadata
    capacity_sqft   = Column(Integer, nullable=True)
    employee_count  = Column(Integer, nullable=True)
    phone           = Column(Text, nullable=True)
    email           = Column(Text, nullable=True)
    notes           = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
