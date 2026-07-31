"""
SupplierCapacityForecast — monthly production forecast submissions.
Each row = one month's forecast for a supplier.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, Text, String
from sqlalchemy.dialects.postgresql import UUID
from app.db.models.base import Base


class SupplierCapacityForecast(Base):
    __tablename__ = "supplier_capacity_forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(Text, nullable=False, index=True)

    # Period
    forecast_year = Column(Integer, nullable=False, index=True)
    forecast_month = Column(Integer, nullable=True)   # 1-12; NULL for annual forecast
    # monthly | quarterly | annual
    period_type = Column(String(20), nullable=False, default="monthly")
    quarter = Column(Integer, nullable=True)           # 1-4; set for quarterly forecasts

    # Forecast values (units)
    forecasted_output = Column(Integer, nullable=True)
    maximum_capacity = Column(Integer, nullable=True)
    planned_downtime_days = Column(Integer, nullable=True)

    # Status: DRAFT | SUBMITTED | APPROVED | SUPERSEDED
    status = Column(String(20), nullable=False, default="SUBMITTED")

    # Submission metadata
    submitted_by = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
