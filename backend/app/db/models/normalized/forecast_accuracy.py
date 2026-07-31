"""
SupplierForecastAccuracy — forecast vs actuals comparison.

Computes MAPE (Mean Absolute Percentage Error) and accuracy_pct per period.
Populated by the MasterOrchestrator after actual production data arrives.

variance and accuracy_pct are computed columns in PostgreSQL.
In Python, compute them via properties for service-layer use.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class SupplierForecastAccuracy(Base):
    __tablename__ = "supplier_forecast_accuracy"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Soft FK → supplier_accounts.supabase_uid
    supplier_id     = Column(Text, nullable=False, index=True)

    # Soft FK → supplier_capacity_forecasts.id (SET NULL on delete)
    forecast_id     = Column(
        UUID(as_uuid=True),
        ForeignKey("supplier_capacity_forecasts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    forecast_year   = Column(Integer, nullable=False, index=True)
    forecast_month  = Column(SmallInteger, nullable=True)
    period_type     = Column(String(20), nullable=False, default="monthly")

    forecasted_output = Column(Integer, nullable=True)
    actual_output     = Column(Integer, nullable=True)

    # variance and accuracy_pct are GENERATED ALWAYS columns in the DB.
    # In Python we expose them as nullable for SQLAlchemy reads.
    # Do NOT set these directly; they are computed by Postgres.
    mape_pct        = Column(Numeric(8, 4), nullable=True)   # Mean Absolute % Error
    accuracy_pct    = Column(Numeric(8, 4), nullable=True)   # 100 - MAPE

    computed_by     = Column(Text, nullable=True)   # 'system' | user_id
    computed_at     = Column(DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc), index=True)

    @property
    def variance(self) -> Optional[int]:
        """Python-side variance (mirrors DB GENERATED column)."""
        if self.actual_output is not None and self.forecasted_output is not None:
            return self.actual_output - self.forecasted_output
        return None
