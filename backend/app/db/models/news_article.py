"""
NewsArticle — SQLAlchemy DB model for collected news articles.

Stores raw collected articles PLUS all extracted metadata:
  • NLP entities (organizations, people, locations)
  • Country codes (ISO 3166-1 alpha-2)
  • Industry tags
  • Severity score + tier (CRITICAL/HIGH/MEDIUM/LOW/NONE)
  • Event type (GEOPOLITICAL/NATURAL_DISASTER/LABOR/etc.)
  • 384-dim embedding vector (all-MiniLM-L6-v2)
  • Duplicate detection flag
  • is_disruption flag (True when severity >= MEDIUM)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float,
    Integer, JSON, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    # ── Identity ──────────────────────────────────────────────────────────────
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title   = Column(Text, nullable=False)
    content = Column(Text, nullable=True)         # Cleaned text (HTML stripped)
    url     = Column(String(2048), unique=True, nullable=False, index=True)

    # ── Source metadata ───────────────────────────────────────────────────────
    source_name       = Column(String(200), nullable=True)
    source_url        = Column(String(2048), nullable=True)
    credibility_score = Column(Float, default=5.0)

    # ── Timestamps ────────────────────────────────────────────────────────────
    published_at = Column(DateTime(timezone=True), nullable=True)
    collected_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Extracted metadata ────────────────────────────────────────────────────
    # NLP entities: {"organizations": [...], "people": [...], "locations": [...]}
    entities = Column(JSON, nullable=True)

    # List of ISO 3166-1 alpha-2 country codes: ["CN", "US", "TW"]
    country_codes = Column(JSON, nullable=True)

    # Industry tags: ["semiconductor", "logistics", "automotive"]
    industry_tags = Column(JSON, nullable=True)

    # ── Severity ──────────────────────────────────────────────────────────────
    severity       = Column(String(20), default="NONE")    # CRITICAL/HIGH/MEDIUM/LOW/NONE
    severity_score = Column(Float,      default=0.0)       # Continuous 0–10

    # ── Event type classification ─────────────────────────────────────────────
    event_type = Column(String(50), nullable=True)         # GEOPOLITICAL/NATURAL_DISASTER/etc.

    # ── Embedding (384-dim float list, stored as JSON) ────────────────────────
    # Used for cosine-similarity deduplication and semantic search
    embedding = Column(JSON, nullable=True)

    # ── Deduplication ─────────────────────────────────────────────────────────
    is_duplicate = Column(Boolean, default=False)
    duplicate_of = Column(
        UUID(as_uuid=True), nullable=True,
        comment="FK to the original article this is a near-duplicate of",
    )

    # ── Classification flags ──────────────────────────────────────────────────
    # True when severity is MEDIUM, HIGH, or CRITICAL
    is_disruption = Column(Boolean, default=False, index=True)
    is_processed  = Column(Boolean, default=False)
