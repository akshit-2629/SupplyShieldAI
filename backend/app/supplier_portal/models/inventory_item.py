"""
SupplierInventoryItem — SKU-level inventory management per supplier.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, Integer, Text, Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from app.db.models.base import Base


class SupplierInventoryItem(Base):
    __tablename__ = "supplier_inventory_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(Text, nullable=False, index=True)

    # Item identity
    sku = Column(Text, nullable=False, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Text, nullable=True, index=True)
    unit = Column(String(50), nullable=False, default="units")

    # Quantities
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    safety_stock_level = Column(Integer, nullable=True, default=0)
    reorder_point = Column(Integer, nullable=True)
    maximum_stock = Column(Integer, nullable=True)

    # Location
    warehouse_id = Column(Text, nullable=True, index=True)
    warehouse_location = Column(Text, nullable=True)  # "Aisle B, Shelf 3"

    # Valuation
    unit_cost_usd = Column(Float, nullable=True)

    # Status flags (computed, stored for fast queries)
    is_low_stock = Column(Boolean, nullable=False, default=False)
    is_critical_component = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
