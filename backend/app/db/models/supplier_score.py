"""
SupplierScore — SQLAlchemy DB model for Phase 6 supplier evaluations.

One row per supplier per workflow run.
Mirrors the supplier_scores table defined in phase6_supplier.sql.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class SupplierScore(Base):
    __tablename__ = "supplier_scores"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identity
    supplier_id    = Column(Text, nullable=False, index=True)
    execution_id   = Column(Text, nullable=False, index=True)
    name           = Column(Text, nullable=True)
    country_code   = Column(String(10), nullable=True, index=True)
    tier           = Column(Text, nullable=True, index=True)      # TIER_1 / TIER_2 / TIER_3
    revenue_exposure_pct = Column(Float, nullable=True)

    # Health
    health_score   = Column(Float, nullable=False, default=0.0, index=True)
    health_label   = Column(Text,  nullable=True)

    # KPI dimensions
    reliability_score = Column(Float, nullable=True)
    quality_score     = Column(Float, nullable=True)
    lead_time_score   = Column(Float, nullable=True)
    cost_efficiency   = Column(Float, nullable=True)
    compliance_score  = Column(Float, nullable=True)
    responsiveness    = Column(Float, nullable=True)
    flexibility       = Column(Float, nullable=True)

    # Risk (from Phase 4)
    risk_score     = Column(Float, nullable=True, index=True)
    risk_level     = Column(Text,  nullable=True)
    geo_risk       = Column(Float, nullable=True)
    industry_risk  = Column(Float, nullable=True)

    # Graph (from Phase 5)
    dependency_score  = Column(Float,   nullable=True)
    centrality        = Column(Float,   nullable=True)
    blast_radius_size = Column(Integer, nullable=True)
    products_supplied = Column(Integer, nullable=True)

    # Ranking & trend
    rank           = Column(Integer, nullable=True, index=True)
    rank_change    = Column(Integer, nullable=True)
    trend          = Column(Text,    nullable=True, index=True)
    mom_change     = Column(Float,   nullable=True)

    # Algorithm audit
    formula_breakdown = Column(JSON, nullable=True)

    # Timestamp
    evaluated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
