"""
SupplierContact — normalized contact person record per supplier.

Replaces JSON contacts array in supplier_company_profiles.
contact_type enum: PRIMARY | SALES | TECHNICAL | LEGAL | EMERGENCY | GENERAL
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base

CONTACT_TYPE_VALUES = ("PRIMARY", "SALES", "TECHNICAL", "LEGAL", "EMERGENCY", "GENERAL")


class SupplierContact(Base):
    __tablename__ = "supplier_contacts"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Soft FK → supplier_accounts.supabase_uid
    supplier_id     = Column(Text, nullable=False, index=True)

    # PRIMARY | SALES | TECHNICAL | LEGAL | EMERGENCY | GENERAL
    contact_type    = Column(String(30), nullable=False, default="GENERAL", index=True)

    name            = Column(Text, nullable=False)
    email           = Column(Text, nullable=True, index=True)
    phone           = Column(Text, nullable=True)
    title           = Column(Text, nullable=True)
    department      = Column(Text, nullable=True)

    is_primary      = Column(Boolean, nullable=False, default=False)
    is_active       = Column(Boolean, nullable=False, default=True, index=True)
    notes           = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
