"""
SupplierNotification — in-portal notification inbox.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Text, Boolean, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.db.models.base import Base


class SupplierNotification(Base):
    __tablename__ = "supplier_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(Text, nullable=False, index=True)

    # Category: risk | approvals | shipments | inventory | recommendations | admin
    category = Column(String(30), nullable=False, default="admin", index=True)

    # Priority: LOW | MEDIUM | HIGH | CRITICAL
    priority = Column(String(20), nullable=False, default="MEDIUM", index=True)

    title = Column(Text, nullable=False)
    body = Column(Text, nullable=True)

    action_url = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)  # mapped to DB column 'metadata'



    # State
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc), index=True)
