"""
SupplierProduct — normalized product catalog per supplier.

Replaces JSON products array in company profile.
Linked to SupplierCategory for hierarchical classification.
hs_code supports customs / SAP / Oracle ERP integrations.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.models.base import Base


class SupplierProduct(Base):
    __tablename__ = "supplier_products"
    __table_args__ = (
        UniqueConstraint("supplier_id", "sku", name="uq_supplier_products_supplier_sku"),
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Soft FK → supplier_accounts.supabase_uid
    supplier_id     = Column(Text, nullable=False, index=True)

    # Hard FK → supplier_categories.id
    category_id     = Column(
        UUID(as_uuid=True),
        ForeignKey("supplier_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    sku             = Column(Text, nullable=False, index=True)
    name            = Column(Text, nullable=False)
    description     = Column(Text, nullable=True)
    unit            = Column(Text, nullable=False, default="units")

    # Procurement fields
    lead_time_days  = Column(Integer, nullable=True)
    moq             = Column(Integer, nullable=True)     # Minimum Order Quantity
    unit_price_usd  = Column(Numeric(14, 4), nullable=True)
    weight_kg       = Column(Numeric(10, 4), nullable=True)
    dimensions_cm   = Column(Text, nullable=True)        # "L x W x H" or JSON string

    # Trade / compliance
    hs_code             = Column(Text, nullable=True)    # Harmonized System code (SAP/Oracle ERP)
    country_of_origin   = Column(Text, nullable=True)

    is_active       = Column(Boolean, nullable=False, default=True, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    category = relationship("SupplierCategory", back_populates="products")
