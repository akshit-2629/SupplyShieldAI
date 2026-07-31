"""
Admin router — supplier account approval/rejection/suspension.
Requires admin role.
"""
from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import require_admin, UserPrincipal
from app.supplier_portal.schemas import APIResponse, PaginatedResponse, paginate
from app.supplier_portal.repositories.repos import SupplierAccountRepo, NotificationRepo

logger = logging.getLogger("supplier_portal.admin_router")
router = APIRouter(prefix="/admin/supplier-approvals", tags=["Admin — Supplier Approvals"])


@router.get("", summary="List pending supplier registrations [admin]")
async def list_pending(
    status: str = Query("PENDING", description="PENDING | APPROVED | REJECTED | SUSPENDED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserPrincipal = Depends(require_admin),
    db: Session = Depends(get_db),
):
    repo = SupplierAccountRepo(db)
    rows, total = repo.list_by_status(status, limit=page_size, offset=(page - 1) * page_size)
    data = [
        {
            "id": str(r.id),
            "supabase_uid": r.supabase_uid,
            "email": r.email,
            "company_name": r.company_name,
            "contact_name": r.contact_name,
            "phone": r.phone,
            "status": r.status,
            "is_email_verified": r.is_email_verified,
            "rejection_reason": r.rejection_reason,
            "reviewed_by": r.reviewed_by,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return PaginatedResponse(data=data, **paginate(total, page, page_size))


@router.post("/{supplier_id}/approve", summary="Approve a supplier account [admin]")
async def approve_supplier(
    supplier_id: str,
    current_user: UserPrincipal = Depends(require_admin),
    db: Session = Depends(get_db),
):
    repo = SupplierAccountRepo(db)
    notif_repo = NotificationRepo(db)

    account = repo.get_by_supabase_uid(supplier_id)
    if not account:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"Supplier account {supplier_id} not found")

    # Update account status
    repo.update_status(account, "APPROVED", reviewed_by=current_user.user_id)

    # Update Supabase user_metadata
    from app.db.supabase_client import get_supabase
    supabase = get_supabase()
    if supabase:
        try:
            supabase.auth.admin.update_user_by_id(
                supplier_id,
                {"user_metadata": {"role": "supplier", "is_approved": True}}
            )
        except Exception as exc:
            logger.warning(f"[admin_router] Supabase metadata update failed: {exc}")

    # Send notification to supplier
    notif_repo.create_notification(
        supplier_id=supplier_id,
        category="approvals",
        priority="HIGH",
        title="Your supplier account has been approved!",
        body="Welcome to SupplyShield AI. You can now log in and access your supplier portal.",
        action_url="/supplier/dashboard",
    )

    logger.info(f"[admin_router] Supplier {supplier_id[:8]} approved by {current_user.user_id[:8]}")
    return APIResponse(message=f"Supplier account approved for {account.company_name}")


@router.post("/{supplier_id}/reject", summary="Reject a supplier account [admin]")
async def reject_supplier(
    supplier_id: str,
    reason: Optional[str] = None,
    current_user: UserPrincipal = Depends(require_admin),
    db: Session = Depends(get_db),
):
    repo = SupplierAccountRepo(db)
    account = repo.get_by_supabase_uid(supplier_id)
    if not account:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"Supplier account {supplier_id} not found")

    repo.update_status(account, "REJECTED",
                       reviewed_by=current_user.user_id,
                       rejection_reason=reason)
    return APIResponse(message=f"Supplier account rejected for {account.company_name}")


@router.post("/{supplier_id}/suspend", summary="Suspend an active supplier account [admin]")
async def suspend_supplier(
    supplier_id: str,
    reason: Optional[str] = None,
    current_user: UserPrincipal = Depends(require_admin),
    db: Session = Depends(get_db),
):
    repo = SupplierAccountRepo(db)
    account = repo.get_by_supabase_uid(supplier_id)
    if not account:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"Supplier account {supplier_id} not found")

    repo.update_status(account, "SUSPENDED",
                       reviewed_by=current_user.user_id,
                       rejection_reason=reason)

    # Revoke Supabase approval
    from app.db.supabase_client import get_supabase
    supabase = get_supabase()
    if supabase:
        try:
            supabase.auth.admin.update_user_by_id(
                supplier_id,
                {"user_metadata": {"role": "supplier", "is_approved": False, "suspended": True}}
            )
        except Exception as exc:
            logger.warning(f"[admin_router] Supabase suspension update failed: {exc}")

    logger.info(f"[admin_router] Supplier {supplier_id[:8]} suspended by {current_user.user_id[:8]}")
    return APIResponse(message=f"Supplier account suspended for {account.company_name}")
