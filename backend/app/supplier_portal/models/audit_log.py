"""
SupplierAuditLog — immutable audit trail for all supplier portal write operations.
Never updated or deleted. Append-only.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.db.models.base import Base


class SupplierAuditLog(Base):
    __tablename__ = "supplier_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who
    supplier_id = Column(Text, nullable=False, index=True)
    user_id = Column(Text, nullable=False, index=True)      # Supabase UID

    # What
    action = Column(Text, nullable=False, index=True)        # e.g. "INVENTORY_UPDATED"
    entity = Column(Text, nullable=False, index=True)        # table name / entity type
    entity_id = Column(Text, nullable=True, index=True)      # UUID of the affected row

    # Change detail (JSON snapshots)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)

    # Context
    ip_address = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # When
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
