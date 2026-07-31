"""
SupplierCategory — hierarchical product/manufacturing category tree.

Supports unlimited depth via parent_id self-join.
Root categories have parent_id = NULL.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.models.base import Base


class SupplierCategory(Base):
    __tablename__ = "supplier_categories"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id   = Column(
        UUID(as_uuid=True),
        ForeignKey("supplier_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name        = Column(Text, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active   = Column(Boolean, nullable=False, default=True, index=True)
    created_at  = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Self-referential relationships
    parent   = relationship("SupplierCategory", remote_side="SupplierCategory.id",
                             back_populates="children", foreign_keys=[parent_id])
    children = relationship("SupplierCategory", back_populates="parent",
                             foreign_keys=[parent_id])
    products = relationship("SupplierProduct", back_populates="category")
