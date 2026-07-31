"""
SupplierDocumentCenter — enterprise document management with Supabase Storage.
File bytes are NEVER stored in Postgres; only metadata + Storage URL.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.models.base import Base

JSONType = JSONB().with_variant(JSON(), "sqlite")


class SupplierDocumentRecord(Base):
    __tablename__ = "supplier_documents"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id     = Column(Text, nullable=False, index=True)

    # File identity
    file_name       = Column(Text, nullable=False)
    display_name    = Column(Text, nullable=True)
    description     = Column(Text, nullable=True)

    # Classification
    category        = Column(Text, nullable=False, default="GENERAL")
    tags            = Column(JSONType, nullable=False, default=list)

    # Supabase Storage
    storage_bucket  = Column(Text, nullable=False, default="supplier-documents")
    storage_path    = Column(Text, nullable=False)
    public_url      = Column(Text, nullable=False)
    content_type    = Column(Text, nullable=True)
    size_bytes      = Column(BigInteger, nullable=True)

    # Document metadata
    document_date   = Column(Date, nullable=True)
    expiry_date     = Column(Date, nullable=True)
    issuing_body    = Column(Text, nullable=True)

    # Version control
    version         = Column(Integer, nullable=False, default=1)
    is_latest       = Column(Boolean, nullable=False, default=True)
    parent_doc_id   = Column(UUID(as_uuid=True), nullable=True)

    # Status
    status          = Column(Text, nullable=False, default="ACTIVE")

    # Audit
    uploaded_by     = Column(Text, nullable=True)
    deleted_at      = Column(DateTime(timezone=True), nullable=True)
    deleted_by      = Column(Text, nullable=True)

    uploaded_at     = Column(DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc))
    updated_at      = Column(DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc),
                             onupdate=lambda: datetime.now(timezone.utc))


class SupplierDocumentAudit(Base):
    __tablename__ = "supplier_document_audit"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_id = Column(Text, nullable=False, index=True)
    action      = Column(Text, nullable=False)   # UPLOAD|VIEW|DOWNLOAD|UPDATE|DELETE|VERSION_CREATED
    actor_id    = Column(Text, nullable=True)
    ip_address  = Column(Text, nullable=True)
    event_data  = Column(JSONType, nullable=True)   # renamed from 'metadata' (SQLAlchemy reserved)
    created_at  = Column(DateTime(timezone=True), nullable=False,
                         default=lambda: datetime.now(timezone.utc))
