"""
app/supplier_management/router.py — FastAPI router for Module B.

Base prefix: /api/v1/supplier-management   (manufacturer-authenticated)
Public:      /api/v1/supplier-invitations  (no auth — token validation)
"""
from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
import io

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, UserPrincipal
from app.supplier_management.invitation_service import InvitationService
from app.supplier_management.management_service import SupplierManagementService
from app.supplier_management.schemas import (
    AcceptInvitationRequest,
    AddNoteRequest,
    ApproveSupplierRequest,
    AuditResponse,
    InvitationResponse,
    InvitationValidationResponse,
    InviteSupplierRequest,
    NoteResponse,
    OKResponse,
    RejectSupplierRequest,
    SuspendSupplierRequest,
    SupplierAnalyticsResponse,
)

logger = logging.getLogger("supplier_management.router")

# ── Manufacturer-authenticated router ─────────────────────────────────────────
router = APIRouter(prefix="/supplier-management", tags=["Supplier Lifecycle Management"])

# ── Public router (no auth) ───────────────────────────────────────────────────
public_router = APIRouter(prefix="/supplier-invitations", tags=["Supplier Invitations (Public)"])


def _inv_svc(db: Session = Depends(get_db)) -> InvitationService:
    return InvitationService(db)


def _mgmt_svc(db: Session = Depends(get_db)) -> SupplierManagementService:
    return SupplierManagementService(db)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC — token validation (no auth required)
# ═══════════════════════════════════════════════════════════════════════════════

@public_router.get(
    "/validate",
    response_model=InvitationValidationResponse,
    summary="Validate an invitation token (public — no auth)",
    description="Called by the supplier registration page to pre-fill company details.",
)
async def validate_token(
    token: str = Query(..., min_length=64, max_length=64,
                       description="64-char hex token from invitation URL"),
    svc: InvitationService = Depends(_inv_svc),
):
    return svc.validate_token(token)


@public_router.post(
    "/accept",
    response_model=OKResponse,
    summary="Accept invitation (called internally after supplier registration)",
)
async def accept_invitation(
    data: AcceptInvitationRequest,
    svc: InvitationService = Depends(_inv_svc),
):
    svc.accept_invitation(data.token, data.supplier_supabase_uid, None)
    return OKResponse(message="Invitation accepted.")


# ═══════════════════════════════════════════════════════════════════════════════
# INVITATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send supplier invitation",
)
async def send_invitation(
    data: InviteSupplierRequest,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: InvitationService = Depends(_inv_svc),
):
    return svc.send_invitation(current_user.user_id, data)


@router.get(
    "/invitations",
    summary="List invitations (with optional status filter)",
)
async def list_invitations(
    status: Optional[str] = Query(None, description="PENDING|ACCEPTED|EXPIRED|CANCELLED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserPrincipal = Depends(get_current_user),
    svc: InvitationService = Depends(_inv_svc),
):
    rows, total = svc.list_invitations(current_user.user_id, status, page, page_size)
    import math
    return {
        "data":        [_serialize_invitation(r) for r in rows],
        "total":       total,
        "page":        page,
        "page_size":   page_size,
        "total_pages": math.ceil(total / page_size) if total else 0,
    }


@router.post(
    "/invitations/{invitation_id}/resend",
    response_model=InvitationResponse,
    summary="Resend / refresh an invitation",
)
async def resend_invitation(
    invitation_id: UUID,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: InvitationService = Depends(_inv_svc),
):
    return svc.resend_invitation(current_user.user_id, invitation_id)


@router.delete(
    "/invitations/{invitation_id}",
    response_model=OKResponse,
    summary="Cancel an invitation",
)
async def cancel_invitation(
    invitation_id: UUID,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: InvitationService = Depends(_inv_svc),
):
    svc.cancel_invitation(current_user.user_id, invitation_id)
    return OKResponse(message="Invitation cancelled.")


# ═══════════════════════════════════════════════════════════════════════════════
# SUPPLIER DIRECTORY
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/suppliers",
    summary="Supplier directory — search, filter, paginate",
)
async def list_suppliers(
    status: Optional[str]  = Query(None, description="PENDING|APPROVED|REJECTED|SUSPENDED"),
    search: Optional[str]  = Query(None),
    country: Optional[str] = Query(None),
    risk_rating: Optional[str] = Query(None),
    is_critical: Optional[bool] = Query(None),
    sort_by: str   = Query("created_at"),
    sort_dir: str  = Query("desc"),
    page: int      = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserPrincipal = Depends(get_current_user),
    svc: SupplierManagementService = Depends(_mgmt_svc),
):
    import math
    rows, total = svc.list_suppliers(
        current_user.user_id,
        status_filter=status,
        search=search,
        country=country,
        risk_rating=risk_rating,
        is_critical=is_critical,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
    return {
        "data":        rows,
        "total":       total,
        "page":        page,
        "page_size":   page_size,
        "total_pages": math.ceil(total / page_size) if total else 0,
    }


@router.get(
    "/suppliers/{supplier_uid}",
    summary="Get full supplier profile",
)
async def get_supplier(
    supplier_uid: str,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: SupplierManagementService = Depends(_mgmt_svc),
):
    return svc.get_supplier_detail(current_user.user_id, supplier_uid)


# ═══════════════════════════════════════════════════════════════════════════════
# APPROVAL ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/suppliers/{supplier_uid}/approve",
    response_model=OKResponse,
    summary="Approve a supplier",
)
async def approve_supplier(
    supplier_uid: str,
    data: ApproveSupplierRequest = ApproveSupplierRequest(),
    current_user: UserPrincipal = Depends(get_current_user),
    svc: SupplierManagementService = Depends(_mgmt_svc),
):
    result = svc.approve_supplier(current_user.user_id, supplier_uid, data)
    return OKResponse(message=result["message"])


@router.post(
    "/suppliers/{supplier_uid}/reject",
    response_model=OKResponse,
    summary="Reject a supplier",
)
async def reject_supplier(
    supplier_uid: str,
    data: RejectSupplierRequest,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: SupplierManagementService = Depends(_mgmt_svc),
):
    result = svc.reject_supplier(current_user.user_id, supplier_uid, data)
    return OKResponse(message=result["message"])


@router.post(
    "/suppliers/{supplier_uid}/suspend",
    response_model=OKResponse,
    summary="Suspend an active supplier",
)
async def suspend_supplier(
    supplier_uid: str,
    data: SuspendSupplierRequest,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: SupplierManagementService = Depends(_mgmt_svc),
):
    result = svc.suspend_supplier(current_user.user_id, supplier_uid, data)
    return OKResponse(message=result["message"])


@router.post(
    "/suppliers/{supplier_uid}/reactivate",
    response_model=OKResponse,
    summary="Reactivate a suspended supplier",
)
async def reactivate_supplier(
    supplier_uid: str,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: SupplierManagementService = Depends(_mgmt_svc),
):
    result = svc.reactivate_supplier(current_user.user_id, supplier_uid)
    return OKResponse(message=result["message"])


# ═══════════════════════════════════════════════════════════════════════════════
# NOTES
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/suppliers/{supplier_uid}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add internal note",
)
async def add_note(
    supplier_uid: str,
    data: AddNoteRequest,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: SupplierManagementService = Depends(_mgmt_svc),
):
    return svc.add_note(current_user.user_id, supplier_uid, data)


@router.get(
    "/suppliers/{supplier_uid}/notes",
    response_model=List[NoteResponse],
    summary="List internal notes",
)
async def list_notes(
    supplier_uid: str,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: SupplierManagementService = Depends(_mgmt_svc),
):
    return svc.list_notes(current_user.user_id, supplier_uid)


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/suppliers/{supplier_uid}/audit",
    response_model=List[AuditResponse],
    summary="Audit trail for a specific supplier",
)
async def get_audit(
    supplier_uid: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: UserPrincipal = Depends(get_current_user),
    svc: SupplierManagementService = Depends(_mgmt_svc),
):
    return svc.get_audit(current_user.user_id, supplier_uid, limit)


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYTICS & EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/analytics",
    response_model=SupplierAnalyticsResponse,
    summary="Aggregated supplier analytics",
)
async def get_analytics(
    current_user: UserPrincipal = Depends(get_current_user),
    svc: SupplierManagementService = Depends(_mgmt_svc),
):
    return svc.get_analytics(current_user.user_id)


@router.get(
    "/export",
    summary="Export supplier directory as CSV",
    responses={200: {"content": {"text/csv": {}}}},
)
async def export_csv(
    current_user: UserPrincipal = Depends(get_current_user),
    svc: SupplierManagementService = Depends(_mgmt_svc),
):
    csv_data = svc.export_csv(current_user.user_id)
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=suppliers.csv"},
    )


# ── Helper ────────────────────────────────────────────────────────────────────

def _serialize_invitation(inv) -> dict:
    return {
        "id":                    str(inv.id),
        "manufacturer_user_id":  inv.manufacturer_user_id,
        "supplier_email":        inv.supplier_email,
        "supplier_company_name": inv.supplier_company_name,
        "contact_name":          inv.contact_name,
        "phone":                 inv.phone,
        "country":               inv.country,
        "business_category":     inv.business_category,
        "components_expected":   inv.components_expected,
        "relationship_type":     inv.relationship_type,
        "is_critical":           inv.is_critical,
        "invitation_message":    inv.invitation_message,
        "token":                 inv.token,
        "status":                inv.status,
        "expires_at":            inv.expires_at.isoformat() if inv.expires_at else None,
        "accepted_at":           inv.accepted_at.isoformat() if inv.accepted_at else None,
        "resent_count":          inv.resent_count,
        "supplier_supabase_uid": inv.supplier_supabase_uid,
        "created_at":            inv.created_at.isoformat() if inv.created_at else None,
        "updated_at":            inv.updated_at.isoformat() if inv.updated_at else None,
    }
