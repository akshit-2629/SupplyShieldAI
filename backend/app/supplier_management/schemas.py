"""
app/supplier_management/schemas.py — Pydantic schemas for Module B.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ══════════════════════════════════════════════════════════════════════════════
# Shared
# ══════════════════════════════════════════════════════════════════════════════

class OKResponse(BaseModel):
    success: bool = True
    message: str


# ══════════════════════════════════════════════════════════════════════════════
# Invitation
# ══════════════════════════════════════════════════════════════════════════════

RELATIONSHIP_TYPES = [
    "Strategic", "Preferred", "Standard", "Backup", "Spot"
]

BUSINESS_CATEGORIES = [
    "Electronics & Semiconductors", "Automotive Parts", "Aerospace & Defence",
    "Pharmaceutical", "Chemical", "FMCG / Consumer Goods", "Textile & Apparel",
    "Industrial Machinery", "Packaging", "Raw Materials", "Logistics", "Other",
]


class InviteSupplierRequest(BaseModel):
    supplier_email:        str  = Field(..., min_length=5)
    supplier_company_name: str  = Field(..., min_length=2, max_length=200)
    contact_name:          str  = Field(..., min_length=2, max_length=120)
    phone:                 Optional[str]  = None
    country:               Optional[str]  = None
    business_category:     Optional[str]  = None
    components_expected:   Optional[str]  = None
    relationship_type:     str  = Field(default="Standard")
    is_critical:           bool = False
    invitation_message:    Optional[str]  = None
    expiry_days:           int  = Field(default=7, ge=1, le=90)


class InvitationResponse(BaseModel):
    id:                    UUID
    manufacturer_user_id:  str
    supplier_email:        str
    supplier_company_name: str
    contact_name:          str
    phone:                 Optional[str]
    country:               Optional[str]
    business_category:     Optional[str]
    components_expected:   Optional[str]
    relationship_type:     Optional[str]
    is_critical:           bool
    invitation_message:    Optional[str]
    token:                 str
    status:                str
    expires_at:            datetime
    accepted_at:           Optional[datetime]
    resent_count:          int
    supplier_supabase_uid: Optional[str]
    created_at:            datetime
    updated_at:            datetime

    model_config = {"from_attributes": True}


class InvitationValidationResponse(BaseModel):
    """Returned to supplier's registration page — no sensitive data."""
    valid:                 bool
    invitation_id:         Optional[UUID]  = None
    supplier_email:        Optional[str]   = None
    supplier_company_name: Optional[str]   = None
    contact_name:          Optional[str]   = None
    manufacturer_name:     Optional[str]   = None
    business_category:     Optional[str]   = None
    components_expected:   Optional[str]   = None
    relationship_type:     Optional[str]   = None
    is_critical:           Optional[bool]  = None
    expires_at:            Optional[datetime] = None
    error:                 Optional[str]   = None


class AcceptInvitationRequest(BaseModel):
    token:                str
    supplier_supabase_uid: str


# ══════════════════════════════════════════════════════════════════════════════
# Supplier Directory / Detail
# ══════════════════════════════════════════════════════════════════════════════

class SupplierSummary(BaseModel):
    """Lightweight row for directory listing."""
    id:                    UUID
    supabase_uid:          str
    supplier_code:         Optional[str]
    email:                 str
    company_name:          str
    contact_name:          str
    phone:                 Optional[str]
    status:                str
    risk_rating:           Optional[str]
    is_critical:           bool
    relationship_type:     Optional[str]
    manufacturer_user_id:  Optional[str]
    last_login_at:         Optional[datetime]
    reviewed_at:           Optional[datetime]
    created_at:            datetime

    # From company profile (may be None if not yet filled)
    headquarters_country:  Optional[str]
    headquarters_city:     Optional[str]
    logo_url:              Optional[str]
    manufacturing_categories: Optional[List[Any]]

    model_config = {"from_attributes": True}


class SupplierDetail(SupplierSummary):
    """Full profile for approval panel / profile drawer."""
    website:               Optional[str]
    products:              Optional[List[Any]]
    certifications:        Optional[List[Any]]
    documents:             Optional[List[Any]]
    locations:             Optional[List[Any]]
    contacts:              Optional[List[Any]]
    employee_count:        Optional[int]
    annual_revenue_usd:    Optional[str]
    description:           Optional[str]
    rejection_reason:      Optional[str]

    model_config = {"from_attributes": True}


class SupplierListResponse(BaseModel):
    data:        List[SupplierSummary]
    total:       int
    page:        int
    page_size:   int
    total_pages: int


# ══════════════════════════════════════════════════════════════════════════════
# Actions
# ══════════════════════════════════════════════════════════════════════════════

class ApproveSupplierRequest(BaseModel):
    note: Optional[str] = None


class RejectSupplierRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=2000)


class SuspendSupplierRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=2000)


class AddNoteRequest(BaseModel):
    note_type: str = Field(default="INTERNAL_NOTE")
    content:   str = Field(..., min_length=1, max_length=5000)


class NoteResponse(BaseModel):
    id:                    UUID
    manufacturer_user_id:  str
    supplier_supabase_uid: str
    note_type:             str
    content:               str
    created_by:            Optional[str]
    created_at:            datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Audit
# ══════════════════════════════════════════════════════════════════════════════

class AuditResponse(BaseModel):
    id:                    UUID
    actor_user_id:         str
    actor_role:            str
    supplier_supabase_uid: Optional[str]
    action:                str
    event_data:            Optional[Dict[str, Any]]
    ip_address:            Optional[str]
    created_at:            datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Analytics
# ══════════════════════════════════════════════════════════════════════════════

class SupplierAnalyticsResponse(BaseModel):
    total_suppliers:        int
    pending_approval:       int
    active_suppliers:       int
    suspended_suppliers:    int
    rejected_suppliers:     int
    total_invitations:      int
    pending_invitations:    int
    accepted_invitations:   int
    expired_invitations:    int
    acceptance_rate:        float   # 0–100
    critical_suppliers:     int
    risk_distribution:      Dict[str, int]   # LOW/MEDIUM/HIGH/CRITICAL/UNKNOWN counts
