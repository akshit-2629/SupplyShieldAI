"""
SupplierIncidentAttachment — normalized file attachment per incident.

Replaces JSON attachments array in supplier_incidents.
Files are stored in object storage (Supabase Storage / S3);
only the URL and metadata are stored here.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.models.base import Base


class SupplierIncidentAttachment(Base):
    __tablename__ = "supplier_incident_attachments"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Hard FK → supplier_incidents.id
    incident_id     = Column(
        UUID(as_uuid=True),
        ForeignKey("supplier_incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Soft FK → supplier_accounts.supabase_uid
    supplier_id     = Column(Text, nullable=False, index=True)

    file_name       = Column(Text, nullable=False)
    file_url        = Column(Text, nullable=False)
    mime_type       = Column(Text, nullable=True)
    size_bytes      = Column(BigInteger, nullable=True)
    description     = Column(Text, nullable=True)
    uploaded_by     = Column(Text, nullable=True)   # supabase_uid of uploader

    uploaded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
