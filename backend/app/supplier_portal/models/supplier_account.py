"""
SupplierAccount — core identity and account lifecycle model.

Mirrors auth.users (Supabase) with a one-to-one relationship.
Status machine: PENDING → APPROVED | REJECTED | SUSPENDED
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class SupplierAccount(Base):
    __tablename__ = "supplier_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Links to Supabase auth.users — the JWT sub claim
    supabase_uid = Column(Text, unique=True, nullable=False, index=True)

    # Basic identity (mirrored from auth for fast lookups without Supabase round-trip)
    email = Column(Text, unique=True, nullable=False, index=True)
    company_name = Column(Text, nullable=False)
    contact_name = Column(Text, nullable=False)
    phone = Column(Text, nullable=True)

    # Account lifecycle
    # PENDING | APPROVED | REJECTED | SUSPENDED
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    is_email_verified = Column(Boolean, nullable=False, default=False)
    rejection_reason = Column(Text, nullable=True)

    # Admin who approved/rejected
    reviewed_by = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
