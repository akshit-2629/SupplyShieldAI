"""
SupplierQualityRecord — defect tracking, inspection reports, corrective actions.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, Boolean, Date, DateTime, Integer, Numeric, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.models.base import Base

JSONType = JSONB().with_variant(JSON(), "sqlite")


class SupplierQualityRecord(Base):
    __tablename__ = "supplier_quality_records"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id     = Column(Text, nullable=False, index=True)
    record_number   = Column(Text, nullable=False)

    # Classification
    record_type     = Column(Text, nullable=False, default="INSPECTION_REPORT")
    severity        = Column(Text, nullable=False, default="MINOR")
    status          = Column(Text, nullable=False, default="OPEN")

    # Core
    title               = Column(Text, nullable=False)
    description         = Column(Text, nullable=True)
    inspection_date     = Column(Date, nullable=True)
    product_sku         = Column(Text, nullable=True)
    product_name        = Column(Text, nullable=True)
    batch_number        = Column(Text, nullable=True)
    quantity_inspected  = Column(Integer, nullable=True)
    quantity_passed     = Column(Integer, nullable=True)
    quantity_failed     = Column(Integer, nullable=True)
    defect_rate_pct     = Column(Numeric(6, 2), nullable=True)

    # Corrective action
    root_cause              = Column(Text, nullable=True)
    corrective_action       = Column(Text, nullable=True)
    corrective_action_date  = Column(Date, nullable=True)
    responsible_person      = Column(Text, nullable=True)

    # Compliance
    standard_reference      = Column(Text, nullable=True)
    customer_notified       = Column(Boolean, nullable=False, default=False)
    regulatory_reportable   = Column(Boolean, nullable=False, default=False)

    # Attachments
    attachments     = Column(JSONType, nullable=False, default=list)

    # Version / audit
    version         = Column(Integer, nullable=False, default=1)
    closed_at       = Column(DateTime(timezone=True), nullable=True)
    closed_by       = Column(Text, nullable=True)
    created_by      = Column(Text, nullable=True)

    # Soft delete
    deleted_at      = Column(DateTime(timezone=True), nullable=True)
    deleted_by      = Column(Text, nullable=True)

    created_at      = Column(DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc))
    updated_at      = Column(DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc),
                             onupdate=lambda: datetime.now(timezone.utc))


class SupplierQualityHistory(Base):
    __tablename__ = "supplier_quality_history"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quality_id      = Column(UUID(as_uuid=True), nullable=False, index=True)
    version         = Column(Integer, nullable=False)
    changed_by      = Column(Text, nullable=True)
    changed_at      = Column(DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc))
    change_summary  = Column(Text, nullable=True)
    snapshot        = Column(JSONType, nullable=False, default=dict)
