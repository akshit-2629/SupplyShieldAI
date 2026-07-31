"""
SupplierLeadTime — per-product/category lead time components.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from app.db.models.base import Base


class SupplierLeadTime(Base):
    __tablename__ = "supplier_lead_times"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(Text, nullable=False, index=True)

    # What this lead time applies to
    product_sku = Column(Text, nullable=True, index=True)
    product_name = Column(Text, nullable=True)
    category = Column(Text, nullable=True)

    # Lead time components (all in days)
    manufacturing_days = Column(Integer, nullable=True)
    packaging_days = Column(Integer, nullable=True)
    quality_check_days = Column(Integer, nullable=True)
    shipping_days = Column(Integer, nullable=True)
    customs_days = Column(Integer, nullable=True)

    # Computed / reported totals
    total_lead_time_days = Column(Integer, nullable=True)    # sum of components
    average_delay_days = Column(Float, nullable=True)        # historical average delay
    expected_delivery_days = Column(Integer, nullable=True)  # total + buffer

    # Destination context
    destination_country = Column(Text, nullable=True)
    shipping_method = Column(Text, nullable=True)            # "air" | "sea" | "land"

    # Notes
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
