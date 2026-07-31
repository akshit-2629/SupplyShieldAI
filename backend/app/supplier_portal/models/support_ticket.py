"""
SupplierSupportTicket — help desk ticket with threaded replies stored as JSON.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Text, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.db.models.base import Base


class SupplierSupportTicket(Base):
    __tablename__ = "supplier_support_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(Text, nullable=False, index=True)

    # Ticket metadata
    ticket_number = Column(Text, nullable=False, unique=True, index=True)
    subject = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    # Category: General Inquiry | Account Issue | Technical Problem |
    #           Data Dispute | Integration Support | Billing | Other
    category = Column(String(40), nullable=True)

    # Priority: LOW | MEDIUM | HIGH | URGENT
    priority = Column(String(20), nullable=False, default="MEDIUM")

    # Status: OPEN | IN_PROGRESS | WAITING_ON_SUPPLIER | RESOLVED | CLOSED
    status = Column(String(30), nullable=False, default="OPEN", index=True)

    # Who the ticket is assigned to (admin user_id)
    assigned_to = Column(Text, nullable=True)

    # Threaded replies as JSON array
    # [{"reply_id": str, "author_id": str, "author_type": "supplier"|"admin",
    #   "message": str, "attachments": [...], "created_at": str}]
    replies = Column(JSON, nullable=True, default=list)

    # Attachments [{"file_id": str, "name": str, "url": str}]
    attachments = Column(JSON, nullable=True, default=list)

    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
