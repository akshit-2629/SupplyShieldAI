"""
SupplierAuthService — registration, login, account management via Supabase Auth.

All auth operations delegate to Supabase — we never store passwords.
Our DB tracks account metadata (status, approval) alongside Supabase auth.users.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.db.supabase_client import get_supabase
from app.core.exceptions import (
    DuplicateSupplierRegistrationException,
    SupplierAccountPendingException,
    SupplierAccountSuspendedException,
    SupplierAccountRejectedException,
    ValidationException,
)
from app.supplier_portal.models.supplier_account import SupplierAccount
from app.supplier_portal.repositories.repos import SupplierAccountRepo
from app.supplier_portal.schemas.auth import SupplierRegisterRequest

logger = logging.getLogger("supplier_portal.auth_service")


class SupplierAuthService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = SupplierAccountRepo(db)

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, request: SupplierRegisterRequest) -> dict:
        """
        Register a new supplier:
          1. Check for duplicate email in our DB
          2. Call Supabase auth.sign_up with role in user_metadata
          3. Create SupplierAccount row (status=PENDING)
          4. Return confirmation message
        """
        # 1. Duplicate check
        existing = self.repo.get_by_email(request.email)
        if existing:
            raise DuplicateSupplierRegistrationException()

        supabase = get_supabase()
        if not supabase:
            raise ValidationException("Authentication service unavailable")

        # 2. Supabase sign_up
        try:
            result = supabase.auth.admin.create_user({
                "email": request.email,
                "password": request.password,
                "email_confirm": True,   # Auto-confirm invited supplier email
                "user_metadata": {
                    "role": "supplier",
                    "is_approved": False,
                    "company_name": request.company_name,
                    "contact_name": request.contact_name,
                    "phone": request.phone,
                },
            })

        except Exception as exc:
            logger.error(f"[auth_service] Supabase sign_up failed: {exc}")
            error_msg = str(exc).lower()
            if "already registered" in error_msg or "already exists" in error_msg:
                raise DuplicateSupplierRegistrationException()
            raise ValidationException(f"Registration failed: {exc}")

        supabase_uid = result.user.id if result.user else None
        if not supabase_uid:
            raise ValidationException("Registration failed — no user ID returned")

        # 3. Create account record
        account = SupplierAccount(
            supabase_uid=supabase_uid,
            email=request.email,
            company_name=request.company_name,
            contact_name=request.contact_name,
            phone=request.phone,
            status="PENDING",
            is_email_verified=False,
        )
        self.repo.create(account)

        # 4. Module B — if an invitation token was provided, accept it (links to manufacturer)
        if getattr(request, "invitation_token", None):
            try:
                from app.supplier_management.invitation_service import InvitationService
                inv_svc = InvitationService(self.db)
                inv_svc.accept_invitation(request.invitation_token, supabase_uid, account.id)
            except Exception as inv_exc:
                logger.warning("[auth_service] invitation accept failed (non-fatal): %s", inv_exc)

        logger.info(f"[auth_service] Supplier registered: {request.email} uid={supabase_uid[:8]}")
        return {
            "message": "Registration successful. Please check your email to verify your account. An administrator will review and approve your account.",
            "email": request.email,
            "status": "PENDING",
        }

    # ── Account Status ────────────────────────────────────────────────────────

    def get_account_status(self, supabase_uid: str) -> Optional[SupplierAccount]:
        return self.repo.get_by_supabase_uid(supabase_uid)

    def check_account_access(self, supabase_uid: str) -> SupplierAccount:
        """
        Validate the supplier account is active.
        Raises descriptive exception for each disallowed state.
        """
        account = self.repo.get_by_supabase_uid(supabase_uid)
        if not account:
            return None   # No account row — newly registered before approval
        if account.status == "PENDING":
            raise SupplierAccountPendingException()
        if account.status == "REJECTED":
            raise SupplierAccountRejectedException()
        if account.status == "SUSPENDED":
            raise SupplierAccountSuspendedException()
        return account

    # ── Password ──────────────────────────────────────────────────────────────

    def send_forgot_password_email(self, email: str) -> dict:
        """Trigger Supabase password reset email."""
        supabase = get_supabase()
        if supabase:
            try:
                supabase.auth.reset_password_email(email)
            except Exception as exc:
                logger.warning(f"[auth_service] reset_password_email failed: {exc}")
        # Always return success to avoid email enumeration
        return {"message": "If that email is registered, a password reset link has been sent."}

    def change_password(self, supabase_uid: str, new_password: str) -> dict:
        """Update password via Supabase admin API."""
        supabase = get_supabase()
        if not supabase:
            raise ValidationException("Authentication service unavailable")
        try:
            supabase.auth.admin.update_user_by_id(
                supabase_uid,
                {"password": new_password}
            )
        except Exception as exc:
            raise ValidationException(f"Password change failed: {exc}")
        return {"message": "Password updated successfully"}

    # ── Logout ────────────────────────────────────────────────────────────────

    def logout(self, access_token: str) -> dict:
        """Invalidate token via Supabase (best-effort)."""
        supabase = get_supabase()
        if supabase:
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
        return {"message": "Logged out successfully"}
