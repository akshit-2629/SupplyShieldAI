"""
SupplierShipment — shipment tracking with full timeline events.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, Text, JSON, String, Float
from sqlalchemy.dialects.postgresql import UUID
from app.db.models.base import Base


class SupplierShipment(Base):
    __tablename__ = "supplier_shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(Text, nullable=False, index=True)

    # Shipment identity
    shipment_number = Column(Text, nullable=False, index=True)  # supplier's own reference
    tracking_number = Column(Text, nullable=True, index=True)
    purchase_order_number = Column(Text, nullable=True)

    # Status
    # PREPARING | IN_TRANSIT | CUSTOMS | DELIVERED | DELAYED | CANCELLED
    status = Column(String(30), nullable=False, default="PREPARING", index=True)

    # Carrier
    carrier_name = Column(Text, nullable=True)
    carrier_code = Column(Text, nullable=True)
    shipping_method = Column(Text, nullable=True)   # "air" | "sea" | "land" | "courier"

    # Origin / destination
    origin_country = Column(Text, nullable=True)
    origin_city = Column(Text, nullable=True)
    destination_country = Column(Text, nullable=True)
    destination_city = Column(Text, nullable=True)
    destination_address = Column(Text, nullable=True)

    # Dates
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    estimated_arrival = Column(DateTime(timezone=True), nullable=True, index=True)
    actual_arrival = Column(DateTime(timezone=True), nullable=True)

    # Cargo
    quantity = Column(Integer, nullable=True)
    unit = Column(Text, nullable=True)
    weight_kg = Column(Float, nullable=True)
    volume_m3 = Column(Float, nullable=True)

    # Items in this shipment [{"sku": str, "name": str, "quantity": int}]
    items = Column(JSON, nullable=True, default=list)

    # Timeline events  [{"event": str, "location": str, "timestamp": str, "notes": str}]
    timeline = Column(JSON, nullable=True, default=list)

    # Notes / customs info
    notes = Column(Text, nullable=True)
    customs_status = Column(Text, nullable=True)
    incoterms = Column(Text, nullable=True)  # "FOB", "CIF", "DDP", etc.

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True)
