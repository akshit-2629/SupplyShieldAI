"""
SupplierCompanyProfile — full company data submitted by the supplier.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.db.models.base import Base


class SupplierCompanyProfile(Base):
    __tablename__ = "supplier_company_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(Text, nullable=False, unique=True, index=True)  # FK → supplier_accounts.supabase_uid

    # Core info
    company_name = Column(Text, nullable=False)
    legal_name = Column(Text, nullable=True)
    registration_number = Column(Text, nullable=True)
    tax_id = Column(Text, nullable=True)
    year_established = Column(Integer, nullable=True)
    employee_count = Column(Integer, nullable=True)
    annual_revenue_usd = Column(Text, nullable=True)  # stored as string to avoid float precision issues
    description = Column(Text, nullable=True)
    website = Column(Text, nullable=True)

    # Contact
    email = Column(Text, nullable=True)
    phone = Column(Text, nullable=True)
    headquarters_address = Column(Text, nullable=True)
    headquarters_country = Column(Text, nullable=True)
    headquarters_city = Column(Text, nullable=True)

    # Assets (Supabase Storage URLs)
    logo_url = Column(Text, nullable=True)

    # Structured JSON fields
    # [{"type": "factory"|"warehouse", "name": str, "country": str, "city": str, "capacity_units": int}]
    locations = Column(JSON, nullable=True, default=list)

    # [{"name": str, "title": str, "email": str, "phone": str}]
    contacts = Column(JSON, nullable=True, default=list)

    # ["Automotive", "Electronics", "Chemicals", ...]
    manufacturing_categories = Column(JSON, nullable=True, default=list)

    # [{"sku": str, "name": str, "description": str, "unit": str}]
    products = Column(JSON, nullable=True, default=list)

    # [{"name": str, "issuing_body": str, "issued_date": str, "expiry_date": str, "cert_url": str}]
    certifications = Column(JSON, nullable=True, default=list)

    # [{"doc_id": str, "name": str, "type": str, "url": str, "uploaded_at": str}]
    documents = Column(JSON, nullable=True, default=list)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
