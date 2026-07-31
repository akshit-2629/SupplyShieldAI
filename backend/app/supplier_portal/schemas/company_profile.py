"""
Company profile schemas.
"""
from __future__ import annotations
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field, field_validator, ConfigDict


class LocationItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=200)
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    capacity_units: Optional[int] = Field(None, ge=0)

    @field_validator("type", "name", "country", "city", "address", mode="before")
    @classmethod
    def sanitize_empty_strings(cls, v: Any) -> Any:
        if v == "" or v is None:
            return None
        return v


class ContactItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=200)
    title: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=100)

    @field_validator("type", "name", "title", "email", "phone", mode="before")
    @classmethod
    def sanitize_empty_strings(cls, v: Any) -> Any:
        if v == "" or v is None:
            return None
        return v


class CertificationItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: Optional[str] = Field(None, max_length=200)
    issuing_body: Optional[str] = Field(None, max_length=200)
    issued_date: Optional[str] = None   # ISO date string
    expiry_date: Optional[str] = None
    cert_url: Optional[str] = None

    @field_validator("name", "issuing_body", "issued_date", "expiry_date", "cert_url", mode="before")
    @classmethod
    def sanitize_empty_strings(cls, v: Any) -> Any:
        if v == "" or v is None:
            return None
        return v


class ProductItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    sku: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    unit: Optional[str] = Field(None, max_length=50)

    @field_validator("sku", "name", "description", "unit", mode="before")
    @classmethod
    def sanitize_empty_strings(cls, v: Any) -> Any:
        if v == "" or v is None:
            return None
        return v


class CompanyProfileCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    company_name: Optional[str] = Field(None, max_length=200)
    legal_name: Optional[str] = Field(None, max_length=200)
    registration_number: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=100)
    year_established: Optional[int] = Field(None, ge=1800, le=2100)
    employee_count: Optional[int] = Field(None, ge=1)
    annual_revenue_usd: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    headquarters_address: Optional[str] = Field(None, max_length=500)
    headquarters_country: Optional[str] = Field(None, max_length=100)
    headquarters_city: Optional[str] = Field(None, max_length=100)
    locations: Optional[List[LocationItem]] = None
    contacts: Optional[List[ContactItem]] = None
    manufacturing_categories: Optional[List[str]] = None
    products: Optional[List[ProductItem]] = None
    certifications: Optional[List[CertificationItem]] = None

    @field_validator(
        "company_name", "legal_name", "registration_number", "tax_id",
        "year_established", "employee_count", "annual_revenue_usd",
        "description", "website", "email", "phone", "headquarters_address",
        "headquarters_country", "headquarters_city",
        mode="before"
    )
    @classmethod
    def sanitize_empty_strings(cls, v: Any) -> Any:
        if v == "" or v is None:
            return None
        return v


class CompanyProfileUpdateRequest(CompanyProfileCreateRequest):
    """Same fields, all optional for PATCH-style updates."""
    model_config = ConfigDict(extra="allow")



from typing import Any

class CompanyProfileResponse(BaseModel):
    id: Any
    supplier_id: Any
    company_name: Optional[str] = "My Company"
    legal_name: Optional[str] = None
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    year_established: Optional[int] = None
    employee_count: Optional[int] = None
    annual_revenue_usd: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    headquarters_address: Optional[str] = None
    headquarters_country: Optional[str] = None
    headquarters_city: Optional[str] = None
    logo_url: Optional[str] = None
    locations: Optional[list] = None
    contacts: Optional[list] = None
    manufacturing_categories: Optional[list] = None
    products: Optional[list] = None
    certifications: Optional[list] = None
    documents: Optional[list] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    @field_validator("id", "supplier_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        if v is not None:
            return str(v)
        return v

