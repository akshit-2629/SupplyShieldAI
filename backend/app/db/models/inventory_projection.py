"""
InventoryProjectionRow — SQLAlchemy DB model for Phase 7.

One row per component per workflow run.
Mirrors the inventory_projections table in phase7_inventory.sql.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class InventoryProjectionRow(Base):
    __tablename__ = "inventory_projections"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identity
    component_id   = Column(Text, nullable=False, index=True)
    component_name = Column(Text, nullable=True)
    supplier_id    = Column(Text, nullable=True, index=True)
    execution_id   = Column(Text, nullable=False, index=True)

    # Stock levels
    current_stock          = Column(Float, nullable=True)
    daily_consumption      = Column(Float, nullable=True)
    safety_stock           = Column(Float, nullable=True)
    reorder_point          = Column(Float, nullable=True)
    lead_time_days         = Column(Integer, nullable=True)

    # Stockout prediction (Algorithm 1–5)
    days_remaining         = Column(Float, nullable=True, index=True)
    safety_stock_days      = Column(Float, nullable=True)
    stockout_risk          = Column(Text,  nullable=True, index=True)    # CRITICAL/HIGH/MEDIUM/LOW/SAFE
    stockout_probability   = Column(Float, nullable=True)
    stockout_date          = Column(Text,  nullable=True)

    # Inventory health (Algorithm 6)
    inventory_health_score = Column(Float, nullable=True, index=True)
    inventory_health_label = Column(Text,  nullable=True)
    coverage_ratio         = Column(Float, nullable=True)

    # Revenue impact (Algorithm 7)
    days_short             = Column(Float, nullable=True)
    units_short            = Column(Float, nullable=True)
    revenue_lost_usd       = Column(Float, nullable=True)
    cogs_at_risk_usd       = Column(Float, nullable=True)

    # Manufacturing delay (Algorithm 8)
    delay_days             = Column(Float,   nullable=True)
    recovery_days          = Column(Float,   nullable=True)
    delay_severity         = Column(Text,    nullable=True)
    affected_products      = Column(JSON,    nullable=True)

    # Algorithm audit trail
    formula_breakdown      = Column(JSON, nullable=True)

    # Timestamp
    evaluated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
