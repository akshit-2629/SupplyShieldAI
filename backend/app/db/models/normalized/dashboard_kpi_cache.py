"""
DashboardKpiCache — pre-aggregated KPI cache for the executive dashboard.

Refreshed after every MasterOrchestrator workflow run.
Eliminates expensive cross-table joins on the executive dashboard.

cache_key examples:
  'executive_summary'     — overall platform KPIs
  'supplier_health'       — aggregated health scores
  'inventory_risk'        — stockout risk summary
  'incident_heatmap'      — active incident breakdown
  'shipment_status'       — in-transit / overdue summary
  'forecast_accuracy'     — rolling MAPE summary

scope: 'global' | <supplier_id>
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.models.base import Base


class DashboardKpiCache(Base):
    __tablename__ = "dashboard_kpi_cache"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Lookup key — UNIQUE in DB, allows fast upsert
    cache_key       = Column(Text, nullable=False, unique=True)

    # 'global' or supplier_id for per-supplier caches
    scope           = Column(Text, nullable=False, default="global", index=True)

    # Links to the orchestrator run that produced this cache entry
    execution_id    = Column(Text, nullable=True)

    # The aggregated data blob
    data            = Column(JSONB, nullable=False)

    # TTL in seconds (default: 5 minutes)
    ttl_seconds     = Column(Integer, nullable=False, default=300)

    refreshed_at    = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    @property
    def expires_at(self) -> datetime:
        """When this cache entry becomes stale."""
        return self.refreshed_at + timedelta(seconds=self.ttl_seconds)

    @property
    def is_stale(self) -> bool:
        """True if the cache entry has passed its TTL."""
        return datetime.now(timezone.utc) > self.expires_at
