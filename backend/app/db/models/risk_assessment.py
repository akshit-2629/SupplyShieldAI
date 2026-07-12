"""
RiskAssessment — SQLAlchemy model matching the public.risk_assessments table.

Columns are an exact mirror of the schema in database/schema_complete.sql.
Used by RiskAgent (Phase 4) to persist rows and by GraphAgent (Phase 5)
to query risk data for graph construction.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Identity ──────────────────────────────────────────────────────────────
    assessment_id  = Column(Text, unique=True, nullable=False, index=True)
    news_event_id  = Column(Text, nullable=True, index=True)

    # ── Event metadata ────────────────────────────────────────────────────────
    title          = Column(Text, nullable=True)
    url            = Column(Text, nullable=True)
    source         = Column(Text, nullable=True)
    event_type     = Column(Text, nullable=True)
    published_at   = Column(DateTime(timezone=True), nullable=True)

    # ── Geography & industry ──────────────────────────────────────────────────
    countries      = Column(JSON, nullable=True)   # List[str] of ISO-2 codes
    industries     = Column(JSON, nullable=True)   # List[str] of industry tags

    # ── Risk scores ───────────────────────────────────────────────────────────
    risk_score     = Column(Float, nullable=False, default=0.0, index=True)
    risk_level     = Column(Text,  nullable=False, default="LOW", index=True)
    severity_score = Column(Float, nullable=True)
    severity_label = Column(Text,  nullable=True)

    # ── Algorithm audit trail ─────────────────────────────────────────────────
    formula_components    = Column(JSON, nullable=True)   # weighted formula breakdown
    geo_risk              = Column(JSON, nullable=True)   # geo multiplier details
    industry_risk         = Column(JSON, nullable=True)   # industry multiplier details
    supplier_tier         = Column(Text,  nullable=True)
    exposure_weight       = Column(Float, nullable=True)

    # ── Confidence ────────────────────────────────────────────────────────────
    confidence_score      = Column(Float, nullable=True, index=True)
    confidence_label      = Column(Text,  nullable=True)
    confidence_breakdown  = Column(JSON,  nullable=True)

    # ── Rule engine ───────────────────────────────────────────────────────────
    rule_engine_results   = Column(JSON, nullable=True)

    # ── Trajectory ────────────────────────────────────────────────────────────
    trajectory            = Column(Text,  nullable=True, index=True)  # ESCALATING / STABLE / DECLINING
    trend_slope           = Column(Float, nullable=True)

    # ── Timestamp ─────────────────────────────────────────────────────────────
    assessed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
