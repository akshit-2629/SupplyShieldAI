"""
GraphSnapshot — SQLAlchemy DB model for Phase 5 graph snapshots.

Stores one row per workflow run summarizing the knowledge graph state:
  • node/edge counts
  • SPOF count
  • blast radius impact count
  • react_flow JSON (full serialized graph for UI)
  • centrality, blast_radius, graph_stats JSON blobs
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class GraphSnapshot(Base):
    __tablename__ = "graph_snapshots"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id   = Column(String(64), nullable=False, index=True)

    # Summary counts (denormalized for fast queries)
    node_count     = Column(Integer, default=0)
    edge_count     = Column(Integer, default=0)
    spof_count     = Column(Integer, default=0)
    blast_impacted = Column(Integer, default=0)
    critical_paths = Column(Integer, default=0)

    # Full JSON blobs
    react_flow_json    = Column(JSON, nullable=True)  # React Flow nodes + edges
    centrality_json    = Column(JSON, nullable=True)  # Degree centrality results
    blast_radius_json  = Column(JSON, nullable=True)  # Blast radius report
    graph_stats_json   = Column(JSON, nullable=True)  # Graph statistics

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
