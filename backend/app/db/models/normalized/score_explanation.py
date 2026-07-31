"""
SupplierScoreExplanation — AI-generated textual explanation per score dimension.

APPEND-ONLY: AI writes are immutable. Never UPDATE or DELETE.
Linked to supplier_scores via score_id FK.

dimension values: reliability | quality | lead_time | cost_efficiency |
                  compliance | responsiveness | flexibility | risk | overall
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class SupplierScoreExplanation(Base):
    __tablename__ = "supplier_score_explanations"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Soft FK → supplier_accounts.supabase_uid
    supplier_id     = Column(Text, nullable=False, index=True)

    execution_id    = Column(Text, nullable=False, index=True)

    # Hard FK → supplier_scores.id  (cascade delete if score batch is purged)
    score_id        = Column(
        UUID(as_uuid=True),
        ForeignKey("supplier_scores.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Which KPI dimension this explanation covers
    dimension       = Column(String(50), nullable=False, index=True)

    explanation_text = Column(Text, nullable=False)
    confidence       = Column(Float, nullable=True)     # 0.0 – 1.0

    generated_by    = Column(Text, nullable=False, default="gemini-1.5-pro")
    model_version   = Column(Text, nullable=True)

    # No updated_at — APPEND-ONLY
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
