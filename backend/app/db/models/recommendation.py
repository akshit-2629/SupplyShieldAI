"""
RecommendationRow — SQLAlchemy DB model for Phase 8.

One row per at-risk supplier per workflow run.
Mirrors the recommendations table in phase8_recommendation.sql.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, JSON, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class RecommendationRow(Base):
    __tablename__ = "recommendations"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # At-risk supplier
    at_risk_supplier_id   = Column(Text, nullable=False, index=True)
    at_risk_supplier_name = Column(Text, nullable=True)
    execution_id          = Column(Text, nullable=False, index=True)
    stockout_risk         = Column(Text, nullable=True, index=True)
    revenue_at_risk_usd   = Column(Float, nullable=True)
    delay_days            = Column(Float, nullable=True)

    # Top recommendation
    top_supplier_id       = Column(Text,  nullable=True, index=True)
    top_supplier_name     = Column(Text,  nullable=True)
    top_recommendation_score = Column(Float, nullable=True, index=True)
    top_topsis_score      = Column(Float, nullable=True)
    top_cosine_sim        = Column(Float, nullable=True)
    top_country_code      = Column(Text,  nullable=True)
    top_tier              = Column(Text,  nullable=True)

    # Procurement action
    procurement_action    = Column(Text, nullable=True, index=True)  # IMMEDIATE_SWITCH etc.
    procurement_priority  = Column(Text, nullable=True)

    # Full algorithm outputs (JSONB)
    explanation           = Column(Text, nullable=True)
    mcdm_ranking          = Column(JSON, nullable=True)
    topsis_ranking        = Column(JSON, nullable=True)

    # Timestamp
    evaluated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
