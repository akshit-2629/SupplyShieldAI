"""
SupplierProductionCapacity — snapshot of production capability at a point in time.
Each supplier update creates a new row (history preserved).
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, Integer, Text, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from app.db.models.base import Base


class SupplierProductionCapacity(Base):
    __tablename__ = "supplier_production_capacity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(Text, nullable=False, index=True)

    # Capacity metrics
    maximum_capacity_units = Column(Integer, nullable=True)   # per month
    current_output_units = Column(Integer, nullable=True)     # current actual
    utilization_pct = Column(Float, nullable=True)            # 0-100
    production_rate_per_day = Column(Float, nullable=True)

    # Workforce
    workforce_count = Column(Integer, nullable=True)
    shifts_per_day = Column(Integer, nullable=True)           # 1, 2, or 3

    # Status
    # OPERATIONAL | PARTIAL | MAINTENANCE | OFFLINE
    factory_status = Column(String(20), nullable=False, default="OPERATIONAL")

    # Downtime / maintenance
    planned_downtime_days = Column(Integer, nullable=True)    # days per month
    next_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    maintenance_notes = Column(Text, nullable=True)

    # Machine utilization breakdown — JSON array of machines/lines
    # [{"machine_id": str, "name": str, "utilization_pct": float, "status": str}]
    machine_utilization = Column(JSON, nullable=True, default=list)

    # Notes / context
    notes = Column(Text, nullable=True)

    # Audit
    submitted_by = Column(Text, nullable=True)     # user_id who submitted
    ip_address = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc), index=True)
