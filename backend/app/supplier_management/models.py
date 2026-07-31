"""
app/supplier_management/models.py — SQLAlchemy ORM models for Module B.

New tables:
  SupplierInvitation        → supplier_invitations
  ManufacturerSupplierNote  → manufacturer_supplier_notes
  SupplierLifecycleAudit    → supplier_lifecycle_audit

Also patches SupplierAccount with new columns (handled via ALTER TABLE in SQL;
these columns are declared here for ORM awareness).
"""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    SmallInteger, String, Text, JSON, func,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


# ── Invitation ─────────────────────────────────────────────────────────────────

class SupplierInvitation(Base):
    __tablename__ = "supplier_invitations"

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Issuer
    manufacturer_user_id  = Column(Text, nullable=False, index=True)

    # Recipient info
    supplier_email        = Column(Text, nullable=False)
    supplier_company_name = Column(Text, nullable=False)
    contact_name          = Column(Text, nullable=False)
    phone                 = Column(Text)
    country               = Column(Text)
    business_category     = Column(Text)
    components_expected   = Column(Text)
    relationship_type     = Column(Text, default="Standard")
    is_critical           = Column(Boolean, nullable=False, default=False)
    invitation_message    = Column(Text)

    # Token
    token                 = Column(Text, nullable=False, unique=True)

    # Lifecycle
    status                = Column(String(20), nullable=False, default="PENDING", index=True)
    expires_at            = Column(DateTime(timezone=True), nullable=False)
    accepted_at           = Column(DateTime(timezone=True))
    resent_count          = Column(SmallInteger, nullable=False, default=0)
    last_resent_at        = Column(DateTime(timezone=True))

    # Result
    supplier_account_id   = Column(UUID(as_uuid=True))
    supplier_supabase_uid = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    @staticmethod
    def generate_token() -> str:
        """Generate a 64-char hex token (256-bit entropy)."""
        return secrets.token_hex(32)

    def is_valid(self) -> bool:
        """True if token is PENDING and not yet expired."""
        return (
            self.status == "PENDING"
            and datetime.now(timezone.utc) < self.expires_at
        )

    def __repr__(self) -> str:
        return f"<SupplierInvitation {self.supplier_email!r} status={self.status}>"


# ── Internal Notes ─────────────────────────────────────────────────────────────

class ManufacturerSupplierNote(Base):
    __tablename__ = "manufacturer_supplier_notes"

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manufacturer_user_id  = Column(Text, nullable=False, index=True)
    supplier_supabase_uid = Column(Text, nullable=False, index=True)

    note_type = Column(String(40), nullable=False, default="INTERNAL_NOTE")
    # INTERNAL_NOTE | APPROVAL_NOTE | REJECTION_REASON | REQUEST_MORE_INFO | RISK_OBSERVATION

    content    = Column(Text, nullable=False)
    created_by = Column(Text)   # manufacturer admin user_id
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ManufacturerSupplierNote {self.note_type} on {self.supplier_supabase_uid!r}>"


# ── Audit Log ──────────────────────────────────────────────────────────────────

class SupplierLifecycleAudit(Base):
    __tablename__ = "supplier_lifecycle_audit"

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manufacturer_user_id  = Column(Text, index=True)
    actor_user_id         = Column(Text, nullable=False)
    actor_role            = Column(String(40), nullable=False, default="manufacturer_admin")
    supplier_supabase_uid = Column(Text, index=True)

    action     = Column(String(50), nullable=False, index=True)
    event_data = Column(JSON, default=dict)   # renamed from 'metadata' (SQLAlchemy reserved)
    ip_address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<SupplierLifecycleAudit {self.action} by {self.actor_user_id!r}>"
