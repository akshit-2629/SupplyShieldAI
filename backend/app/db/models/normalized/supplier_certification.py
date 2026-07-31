"""
SupplierCertification — normalized certification record per supplier.

Replaces JSON certifications array in company profile.
Supports ISO, SA8000, SMETA, RoHS, REACH, CE, FDA and custom types.
is_expired is a computed database column (expiry_date < CURRENT_DATE).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base

CERT_TYPE_VALUES = (
    "ISO_9001", "ISO_14001", "ISO_45001", "ISO_50001",
    "ISO_27001", "SA8000", "SMETA", "BSCI",
    "RoHS", "REACH", "CE", "FDA", "OTHER",
)


class SupplierCertification(Base):
    __tablename__ = "supplier_certifications"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Soft FK → supplier_accounts.supabase_uid
    supplier_id     = Column(Text, nullable=False, index=True)

    # ISO_9001 | ISO_14001 | ... | OTHER
    cert_type       = Column(String(50), nullable=False, index=True)
    cert_name       = Column(Text, nullable=True)
    cert_number     = Column(Text, nullable=True)
    issuing_body    = Column(Text, nullable=True)

    issued_date     = Column(Date, nullable=True)
    expiry_date     = Column(Date, nullable=True, index=True)
    # is_expired is a generated column in Postgres — not mapped in Python
    # Query via: SELECT * WHERE is_expired = TRUE or expiry_date < CURRENT_DATE

    document_url    = Column(Text, nullable=True)
    is_active       = Column(Boolean, nullable=False, default=True, index=True)
    notes           = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    @property
    def is_expired(self) -> bool:
        """Python-side expiry check (mirrors the DB GENERATED ALWAYS column)."""
        return self.expiry_date is not None and self.expiry_date < date.today()
