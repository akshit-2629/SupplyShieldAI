"""
app/supplier_management/invitation_service.py — Invitation lifecycle business logic.

Responsibilities:
  • Generate cryptographically secure tokens
  • CRUD on supplier_invitations table
  • Validate tokens for the public registration page
  • Mark invitations accepted on supplier registration
  • Format invitation email bodies (actual SMTP handled by email_service)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.supplier_management.models import SupplierInvitation, SupplierLifecycleAudit
from app.supplier_management.schemas import (
    InviteSupplierRequest,
    AcceptInvitationRequest,
    InvitationValidationResponse,
)
from app.manufacturer.models import ManufacturerCompany

logger = logging.getLogger("supplier_management.invitation")


class InvitationService:

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Send invitation ────────────────────────────────────────────────────────

    def send_invitation(
        self, manufacturer_user_id: str, data: InviteSupplierRequest
    ) -> SupplierInvitation:
        # Check for duplicate PENDING invitation to same email from same manufacturer
        existing = (
            self.db.query(SupplierInvitation)
            .filter_by(
                manufacturer_user_id=manufacturer_user_id,
                supplier_email=data.supplier_email.lower().strip(),
                status="PENDING",
            )
            .first()
        )
        if existing and existing.is_valid():
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"A pending invitation already exists for {data.supplier_email}. "
                "Cancel or resend the existing invitation.",
            )

        token = SupplierInvitation.generate_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expiry_days)

        invitation = SupplierInvitation(
            manufacturer_user_id  = manufacturer_user_id,
            supplier_email        = data.supplier_email.lower().strip(),
            supplier_company_name = data.supplier_company_name,
            contact_name          = data.contact_name,
            phone                 = data.phone,
            country               = data.country,
            business_category     = data.business_category,
            components_expected   = data.components_expected,
            relationship_type     = data.relationship_type,
            is_critical           = data.is_critical,
            invitation_message    = data.invitation_message,
            token                 = token,
            expires_at            = expires_at,
        )
        self.db.add(invitation)

        # Audit
        self._audit(
            manufacturer_user_id  = manufacturer_user_id,
            actor_user_id         = manufacturer_user_id,
            supplier_supabase_uid = None,
            action                = "INVITED",
            metadata              = {
                "email":   data.supplier_email,
                "company": data.supplier_company_name,
            },
        )
        self.db.commit()
        self.db.refresh(invitation)

        # Dispatch email
        from app.core.config import settings
        from app.core.email_service import email_service

        base_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        payload = self.format_email_body(invitation, base_url)
        email_sent = email_service.send_email(
            to_email=payload["to"],
            subject=payload["subject"],
            html_content=payload["html"],
        )
        logger.info(
            "Invitation created for %s by manufacturer %s (Email Dispatched=%s)",
            data.supplier_email, manufacturer_user_id[:8], email_sent
        )
        return invitation

    # ── Resend invitation ──────────────────────────────────────────────────────

    def resend_invitation(
        self, manufacturer_user_id: str, invitation_id: UUID
    ) -> SupplierInvitation:
        inv = self._get_own_invitation(manufacturer_user_id, invitation_id)
        if inv.status not in ("PENDING", "EXPIRED"):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Cannot resend an invitation with status '{inv.status}'."
            )
        # Regenerate token and reset expiry
        inv.token      = SupplierInvitation.generate_token()
        inv.status     = "PENDING"
        inv.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        inv.resent_count    = (inv.resent_count or 0) + 1
        inv.last_resent_at  = datetime.now(timezone.utc)
        self._audit(manufacturer_user_id, manufacturer_user_id, None, "INVITATION_RESENT",
                    {"email": inv.supplier_email, "resent_count": inv.resent_count})
        self.db.commit()
        self.db.refresh(inv)

        # Dispatch email
        from app.core.config import settings
        from app.core.email_service import email_service

        base_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        payload = self.format_email_body(inv, base_url)
        email_service.send_email(
            to_email=payload["to"],
            subject=payload["subject"],
            html_content=payload["html"],
        )
        return inv


    # ── Cancel invitation ──────────────────────────────────────────────────────

    def cancel_invitation(
        self, manufacturer_user_id: str, invitation_id: UUID
    ) -> None:
        inv = self._get_own_invitation(manufacturer_user_id, invitation_id)
        if inv.status != "PENDING":
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Only PENDING invitations can be cancelled (current: {inv.status})."
            )
        inv.status = "CANCELLED"
        self._audit(manufacturer_user_id, manufacturer_user_id, None, "INVITATION_CANCELLED",
                    {"email": inv.supplier_email})
        self.db.commit()

    # ── List invitations ───────────────────────────────────────────────────────

    def list_invitations(
        self,
        manufacturer_user_id: str,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[SupplierInvitation], int]:
        self._expire_stale(manufacturer_user_id)
        q = self.db.query(SupplierInvitation).filter(
            SupplierInvitation.manufacturer_user_id == manufacturer_user_id
        )
        if status_filter:
            q = q.filter(SupplierInvitation.status == status_filter.upper())
        total = q.count()
        rows = q.order_by(SupplierInvitation.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return rows, total

    # ── Validate token (public, no auth) ──────────────────────────────────────

    def validate_token(self, token: str) -> InvitationValidationResponse:
        clean_token = (token or "").strip()
        inv = self.db.query(SupplierInvitation).filter_by(token=clean_token).first()
        if not inv:
            return InvitationValidationResponse(
                valid=False,
                error="Invitation link not found or superseded by a newer link. Please open the latest invitation email sent to your inbox."
            )

        if inv.status == "CANCELLED":
            return InvitationValidationResponse(valid=False, error="Invitation has been cancelled.")
        if inv.status == "ACCEPTED":
            return InvitationValidationResponse(valid=False, error="Invitation has already been used.")
        if inv.status == "EXPIRED" or not inv.is_valid():
            inv.status = "EXPIRED"
            self.db.commit()
            return InvitationValidationResponse(valid=False, error="Invitation has expired.")

        # Fetch manufacturer name
        mfr = self.db.get(ManufacturerCompany, inv.manufacturer_user_id)
        manufacturer_name = mfr.name if mfr else "SupplyShield AI Manufacturer"

        return InvitationValidationResponse(
            valid                 = True,
            invitation_id         = inv.id,
            supplier_email        = inv.supplier_email,
            supplier_company_name = inv.supplier_company_name,
            contact_name          = inv.contact_name,
            manufacturer_name     = manufacturer_name,
            business_category     = inv.business_category,
            components_expected   = inv.components_expected,
            relationship_type     = inv.relationship_type,
            is_critical           = inv.is_critical,
            expires_at            = inv.expires_at,
        )

    # ── Accept invitation (called during supplier registration) ───────────────

    def accept_invitation(self, token: str, supplier_supabase_uid: str, account_id) -> None:
        """
        Mark invitation as ACCEPTED and link it to the new supplier account.
        Called from SupplierAuthService.register() after account creation.
        Does not raise — failure is logged but not fatal to registration.
        """
        try:
            inv = self.db.query(SupplierInvitation).filter_by(token=token).first()
            if not inv or not inv.is_valid():
                logger.warning("accept_invitation: invalid/expired token for uid=%s", supplier_supabase_uid[:8])
                return

            inv.status                = "ACCEPTED"
            inv.accepted_at           = datetime.now(timezone.utc)
            inv.supplier_supabase_uid = supplier_supabase_uid
            inv.supplier_account_id   = account_id

            # Update supplier_accounts with manufacturer linkage
            from app.supplier_portal.models.supplier_account import SupplierAccount
            acct = self.db.query(SupplierAccount).filter_by(
                supabase_uid=supplier_supabase_uid
            ).first()
            if acct:
                acct.manufacturer_user_id = inv.manufacturer_user_id
                acct.invitation_id        = inv.id
                acct.is_critical          = inv.is_critical
                acct.relationship_type    = inv.relationship_type

            self._audit(
                manufacturer_user_id  = inv.manufacturer_user_id,
                actor_user_id         = supplier_supabase_uid,
                actor_role            = "supplier",
                supplier_supabase_uid = supplier_supabase_uid,
                action                = "REGISTRATION_SUBMITTED",
                metadata              = {"email": inv.supplier_email},
            )
            self.db.commit()
        except Exception as exc:
            logger.error("accept_invitation error: %s", exc)
            self.db.rollback()

    # ── Format invitation email body ───────────────────────────────────────────

    def format_email_body(
        self, invitation: SupplierInvitation, base_url: str
    ) -> dict:
        """
        Returns a dict with subject + html body.
        Actual sending is handled by email_service.py (SMTP or Supabase Edge Function).
        """
        registration_url = f"{base_url}/supplier/register?token={invitation.token}"
        subject = f"Invitation to join SupplyShield AI Supplier Network — {invitation.supplier_company_name}"
        html = f"""
        <div style="font-family: Inter, sans-serif; max-width: 600px; margin: 0 auto; color: #111827;">
          <div style="background: linear-gradient(135deg, #2563EB, #7C3AED); padding: 32px; border-radius: 12px 12px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 22px;">SupplyShield AI</h1>
            <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0; font-size: 14px;">Supplier Network Invitation</p>
          </div>
          <div style="background: white; padding: 32px; border: 1px solid #E5E7EB; border-top: none; border-radius: 0 0 12px 12px;">
            <h2 style="font-size: 18px; color: #111827;">Hello {invitation.contact_name},</h2>
            <p style="font-size: 14px; color: #374151; line-height: 1.7;">
              You have been invited to join the <strong>SupplyShield AI</strong> supplier network
              as a <strong>{invitation.relationship_type or 'Standard'}</strong> supplier for
              <strong>{invitation.business_category or 'your business category'}</strong>.
            </p>
            {f'<div style="background: #F0FDF4; border-left: 4px solid #10B981; padding: 12px 16px; margin: 20px 0; font-size: 13px; color: #065F46; font-style: italic;">{invitation.invitation_message}</div>' if invitation.invitation_message else ''}
            <div style="background: #F9FAFB; border-radius: 8px; padding: 16px; margin: 20px 0;">
              <p style="margin: 0 0 4px; font-size: 12px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Expected Components</p>
              <p style="margin: 0; font-size: 14px; color: #111827;">{invitation.components_expected or '—'}</p>
            </div>
            <a href="{registration_url}" style="display: inline-block; background: linear-gradient(135deg, #2563EB, #1D4ED8); color: white; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-weight: 700; font-size: 14px; margin: 16px 0;">
              Complete Registration →
            </a>
            <p style="font-size: 12px; color: #9CA3AF; margin-top: 24px;">
              This invitation expires on <strong>{invitation.expires_at.strftime('%d %b %Y')}</strong>.
              If you did not expect this email, please ignore it.
            </p>
          </div>
        </div>
        """
        return {"subject": subject, "html": html, "to": invitation.supplier_email}

    # ── Private helpers ────────────────────────────────────────────────────────

    def _get_own_invitation(
        self, manufacturer_user_id: str, invitation_id: UUID
    ) -> SupplierInvitation:
        inv = (
            self.db.query(SupplierInvitation)
            .filter_by(id=invitation_id, manufacturer_user_id=manufacturer_user_id)
            .first()
        )
        if not inv:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Invitation not found.")
        return inv

    def _expire_stale(self, manufacturer_user_id: str) -> None:
        """Expire all overdue PENDING invitations in one UPDATE."""
        self.db.query(SupplierInvitation).filter(
            SupplierInvitation.manufacturer_user_id == manufacturer_user_id,
            SupplierInvitation.status == "PENDING",
            SupplierInvitation.expires_at < datetime.now(timezone.utc),
        ).update({"status": "EXPIRED"})
        self.db.commit()

    def _audit(
        self,
        manufacturer_user_id: str,
        actor_user_id: str,
        supplier_supabase_uid: Optional[str],
        action: str,
        metadata: dict = None,
        actor_role: str = "manufacturer_admin",
    ) -> None:
        log = SupplierLifecycleAudit(
            manufacturer_user_id  = manufacturer_user_id,
            actor_user_id         = actor_user_id,
            actor_role            = actor_role,
            supplier_supabase_uid = supplier_supabase_uid,
            action                = action,
            event_data            = metadata or {},
        )
        self.db.add(log)
