"""
Supplier Portal — Auth Router
POST /supplier-portal/auth/register
POST /supplier-portal/auth/forgot-password
POST /supplier-portal/auth/reset-password
GET  /supplier-portal/auth/me
GET  /supplier-portal/auth/account-status
PUT  /supplier-portal/auth/password
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, require_supplier, UserPrincipal
from app.supplier_portal.schemas import (
    SupplierRegisterRequest, ForgotPasswordRequest,
    ChangePasswordRequest, SupplierAccountStatusResponse, APIResponse
)
from app.supplier_portal.services.auth_service import SupplierAuthService

logger = logging.getLogger("supplier_portal.auth_router")
router = APIRouter(prefix="/auth", tags=["Supplier Portal — Auth"])


@router.post(
    "/register",
    status_code=201,
    summary="Register a new supplier account",
    description=(
        "Submits a new supplier registration. "
        "The account enters PENDING status until email is verified and an admin approves it. "
        "Suppliers cannot log in until approved."
    ),
)
async def register(request: SupplierRegisterRequest, db: Session = Depends(get_db)):
    service = SupplierAuthService(db)
    result = service.register(request)
    return APIResponse(data=result, message=result.get("message", "Registration successful"))


@router.post("/forgot-password", summary="Send password reset email")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    service = SupplierAuthService(db)
    result = service.send_forgot_password_email(request.email)
    return APIResponse(data=result, message=result["message"])


@router.put("/password", summary="Change password (requires valid JWT)")
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserPrincipal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SupplierAuthService(db)
    result = service.change_password(current_user.user_id, request.new_password)
    return APIResponse(data=result, message=result["message"])


@router.get("/me", summary="Get current supplier profile from JWT")
async def get_me(current_user: UserPrincipal = Depends(require_supplier)):
    return APIResponse(data={
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role,
        "is_approved": current_user.is_approved,
    })


@router.get("/account-status", summary="Check account approval status")
async def account_status(
    current_user: UserPrincipal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SupplierAuthService(db)
    account = service.get_account_status(current_user.user_id)
    if not account:
        return APIResponse(data={"status": "PENDING", "message": "Account not yet created in portal DB"})
    return APIResponse(data=SupplierAccountStatusResponse.model_validate(account).model_dump())
