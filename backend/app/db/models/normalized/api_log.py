"""
ApiLog — structured per-request API log for security auditing.

APPEND-ONLY: Never UPDATE or DELETE.
Request body is NEVER stored raw — only SHA-256 hash for integrity.
ip_address uses PostgreSQL INET type (stored as Text in SQLAlchemy for simplicity).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class ApiLog(Base):
    __tablename__ = "api_logs"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Actor identity
    user_id             = Column(Text, nullable=True, index=True)
    supplier_id         = Column(Text, nullable=True, index=True)

    # Request details
    method              = Column(String(10), nullable=False)            # GET | POST | PUT | DELETE | PATCH
    path                = Column(Text, nullable=False, index=True)
    query_params        = Column(Text, nullable=True)

    # Response
    status_code         = Column(Integer, nullable=False, index=True)
    duration_ms         = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)

    # Security
    ip_address          = Column(Text, nullable=True)                   # stored as TEXT (INET in DB)
    user_agent          = Column(Text, nullable=True)
    request_body_hash   = Column(Text, nullable=True)                   # SHA-256 only, never raw body

    error               = Column(Text, nullable=True)

    # No updated_at — APPEND-ONLY
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
