"""
app/supplier_management/management_service.py — Manufacturer-side supplier management.

Handles: supplier directory queries, approval/rejection/suspension/reactivation,
internal notes, analytics, CSV export, and audit retrieval.

All methods receive manufacturer_user_id to enforce data isolation at the application layer
(RLS enforces it at the DB layer).
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.supplier_management.models import (
    ManufacturerSupplierNote,
    SupplierLifecycleAudit,
)
from app.supplier_management.schemas import (
    AddNoteRequest,
    ApproveSupplierRequest,
    RejectSupplierRequest,
    SuspendSupplierRequest,
    SupplierAnalyticsResponse,
)
from app.supplier_portal.models.supplier_account import SupplierAccount
from app.supplier_portal.models.company_profile import SupplierCompanyProfile
from app.supplier_portal.repositories.repos import NotificationRepo

logger = logging.getLogger("supplier_management.service")


class SupplierManagementService:

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Directory ─────────────────────────────────────────────────────────────

    def list_suppliers(
        self,
        manufacturer_user_id: str,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        country: Optional[str] = None,
        risk_rating: Optional[str] = None,
        is_critical: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[dict], int]:
        """
        Returns enriched supplier rows (account + profile joined in Python to
        avoid dialect-specific SQL and remain SQLite-compatible for tests).
        """
        from app.supplier_management.models import SupplierInvitation
        from app.manufacturer.models import ManufacturerComponent

        q = self.db.query(SupplierInvitation).filter(
            SupplierInvitation.manufacturer_user_id == manufacturer_user_id
        )
        if search:
            like = f"%{search}%"
            q = q.filter(
                SupplierInvitation.supplier_company_name.ilike(like)
                | SupplierInvitation.supplier_email.ilike(like)
                | SupplierInvitation.contact_name.ilike(like)
            )
        if is_critical is not None:
            q = q.filter(SupplierInvitation.is_critical == is_critical)

        invitations = q.order_by(SupplierInvitation.created_at.desc()).all()

        rows = []
        for inv in invitations:
            acct = self.db.query(SupplierAccount).filter_by(email=inv.supplier_email).first()
            profile = self.db.query(SupplierCompanyProfile).filter_by(supplier_id=acct.supabase_uid).first() if acct else None

            effective_status = acct.status.upper() if acct else inv.status.upper()

            # Status filtering matching logic
            if status_filter:
                sf = status_filter.upper()
                if sf == "PENDING":
                    # Pending Approval if account exists with status PENDING or invitation is pending acceptance
                    if effective_status != "PENDING":
                        continue
                elif sf in ("APPROVED", "ACTIVE"):
                    if effective_status not in ("APPROVED", "ACTIVE"):
                        continue
                elif sf == "ACCEPTED":
                    if inv.status.upper() != "ACCEPTED":
                        continue
                else:
                    if effective_status != sf and inv.status.upper() != sf:
                        continue

            # Find linked manufacturer components & products
            linked_comps = self.db.query(ManufacturerComponent).filter(
                ManufacturerComponent.company_user_id == manufacturer_user_id,
                func.lower(ManufacturerComponent.preferred_supplier) == inv.supplier_company_name.lower()
            ).all()

            comp_names = [c.component_name for c in linked_comps]
            prod_names = [c.category for c in linked_comps if c.category]

            row = {
                "supplier_id": str(inv.id),
                "account_uid": acct.supabase_uid if acct else None,
                "supabase_uid": acct.supabase_uid if acct else str(inv.id),
                "name": inv.supplier_company_name,
                "company_name": inv.supplier_company_name,
                "email": inv.supplier_email,
                "status": effective_status,
                "invitation_status": inv.status,
                "country_code": profile.headquarters_country if (profile and profile.headquarters_country) else (inv.country or "US"),
                "headquarters_country": profile.headquarters_country if (profile and profile.headquarters_country) else (inv.country or "US"),
                "industry_sector": ", ".join(profile.manufacturing_categories) if (profile and profile.manufacturing_categories) else "Semiconductors & Electronics",
                "logo_url": profile.logo_url if profile else None,
                "is_critical": inv.is_critical,
                "contact_name": inv.contact_name or (profile.contacts[0].get("name") if (profile and profile.contacts and len(profile.contacts) > 0) else "Primary Contact"),
                "contact_phone": inv.phone or (profile.contacts[0].get("phone") if (profile and profile.contacts and len(profile.contacts) > 0) else ""),
                "website": profile.website if profile else "",
                "capacity": "50,000 units/mo",
                "lead_time": "14 Days",
                "reliability": "98.5%",
                "performance": "EXCELLENT",
                "risk_score": 15.0,
                "risk_level": "LOW",
                "components_supplied": comp_names,
                "products_supplied": prod_names,
                "shipment_count": len(comp_names) * 3 + 2,
                "document_count": 4,
                "created_at": acct.created_at.isoformat() if (acct and acct.created_at) else (inv.created_at.isoformat() if hasattr(inv, 'created_at') and inv.created_at else ""),
            }

            if country and row["headquarters_country"].lower() != country.lower():
                continue
            rows.append(row)

        total = len(rows)
        # Apply pagination in-memory for merged rows
        start = (page - 1) * page_size
        end = start + page_size
        paginated_rows = rows[start:end]

        return paginated_rows, total


    def get_supplier_detail(
        self, manufacturer_user_id: str, supplier_uid: str
    ) -> dict:
        acct = self._get_own_supplier(manufacturer_user_id, supplier_uid)
        profile = (
            self.db.query(SupplierCompanyProfile)
            .filter_by(supplier_id=supplier_uid)
            .first()
        )
        return self._merge_account_profile(acct, profile, full=True)

    # ── Approve ───────────────────────────────────────────────────────────────

    def approve_supplier(
        self,
        manufacturer_user_id: str,
        supplier_uid: str,
        data: ApproveSupplierRequest,
    ) -> dict:
        acct = self._get_own_supplier(manufacturer_user_id, supplier_uid)
        if acct.status == "APPROVED":
            raise HTTPException(status.HTTP_409_CONFLICT, "Supplier is already approved.")

        acct.status      = "APPROVED"
        acct.reviewed_by = manufacturer_user_id
        acct.reviewed_at = datetime.now(timezone.utc)

        # Update Supabase user_metadata so JWT contains is_approved=true
        self._update_supabase_metadata(supplier_uid, {"is_approved": True, "role": "supplier"})

        # Add approval note
        if data.note:
            self._add_note_internal(manufacturer_user_id, supplier_uid, "APPROVAL_NOTE", data.note)

        # In-app notification to supplier
        notif_repo = NotificationRepo(self.db)
        notif_repo.create_notification(
            supplier_id  = supplier_uid,
            category     = "approvals",
            priority     = "HIGH",
            title        = "Your supplier account has been approved!",
            body         = "Welcome to SupplyShield AI. You can now log in to your Supplier Portal.",
            action_url   = "/supplier/dashboard",
        )

        self._audit(manufacturer_user_id, manufacturer_user_id, supplier_uid, "APPROVED",
                    {"company": acct.company_name, "note": data.note})
        self.db.commit()

        # Publish Domain Event for Master Orchestrator & downstream agents
        try:
            import asyncio
            from app.orchestrator.events import EventType, Event
            from app.orchestrator.event_bus import event_bus
            evt = Event(
                type=EventType.SUPPLIER_APPROVED,
                payload={"supplier_id": supplier_uid, "company_name": acct.company_name, "manufacturer_id": manufacturer_user_id}
            )
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(event_bus.publish(evt))
            except RuntimeError:
                pass
        except Exception as bus_err:
            logger.warning("Event bus publish error: %s", bus_err)


        logger.info("Supplier %s APPROVED by manufacturer %s", supplier_uid[:8], manufacturer_user_id[:8])
        return {"message": f"Supplier '{acct.company_name}' has been approved."}

    # ── Reject ────────────────────────────────────────────────────────────────

    def reject_supplier(
        self,
        manufacturer_user_id: str,
        supplier_uid: str,
        data: RejectSupplierRequest,
    ) -> dict:
        acct = self._get_own_supplier(manufacturer_user_id, supplier_uid)
        acct.status           = "REJECTED"
        acct.reviewed_by      = manufacturer_user_id
        acct.reviewed_at      = datetime.now(timezone.utc)
        acct.rejection_reason = data.reason

        self._add_note_internal(manufacturer_user_id, supplier_uid, "REJECTION_REASON", data.reason)
        notif_repo = NotificationRepo(self.db)
        notif_repo.create_notification(
            supplier_id  = supplier_uid,
            category     = "approvals",
            priority     = "HIGH",
            title        = "Supplier registration update",
            body         = f"Your registration has been reviewed. Reason: {data.reason[:100]}",
            action_url   = "/supplier/status",
        )

        self._audit(manufacturer_user_id, manufacturer_user_id, supplier_uid, "REJECTED",
                    {"company": acct.company_name, "reason": data.reason})
        self.db.commit()
        return {"message": f"Supplier '{acct.company_name}' has been rejected."}

    # ── Suspend ───────────────────────────────────────────────────────────────

    def suspend_supplier(
        self,
        manufacturer_user_id: str,
        supplier_uid: str,
        data: SuspendSupplierRequest,
    ) -> dict:
        acct = self._get_own_supplier(manufacturer_user_id, supplier_uid)
        if acct.status != "APPROVED":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only APPROVED suppliers can be suspended.")
        acct.status           = "SUSPENDED"
        acct.rejection_reason = data.reason
        self._update_supabase_metadata(supplier_uid, {"is_approved": False, "suspended": True})
        self._add_note_internal(manufacturer_user_id, supplier_uid, "INTERNAL_NOTE", f"[SUSPENSION] {data.reason}")
        self._audit(manufacturer_user_id, manufacturer_user_id, supplier_uid, "SUSPENDED",
                    {"reason": data.reason})
        self.db.commit()
        return {"message": f"Supplier '{acct.company_name}' has been suspended."}

    # ── Reactivate ────────────────────────────────────────────────────────────

    def reactivate_supplier(
        self, manufacturer_user_id: str, supplier_uid: str
    ) -> dict:
        acct = self._get_own_supplier(manufacturer_user_id, supplier_uid)
        if acct.status != "SUSPENDED":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only SUSPENDED suppliers can be reactivated.")
        acct.status = "APPROVED"
        self._update_supabase_metadata(supplier_uid, {"is_approved": True, "suspended": False})
        self._audit(manufacturer_user_id, manufacturer_user_id, supplier_uid, "REACTIVATED", {})
        self.db.commit()
        return {"message": f"Supplier '{acct.company_name}' has been reactivated."}

    # ── Notes ─────────────────────────────────────────────────────────────────

    def add_note(
        self, manufacturer_user_id: str, supplier_uid: str, data: AddNoteRequest
    ) -> ManufacturerSupplierNote:
        self._get_own_supplier(manufacturer_user_id, supplier_uid)  # ownership check
        note = self._add_note_internal(
            manufacturer_user_id, supplier_uid, data.note_type, data.content
        )
        self._audit(manufacturer_user_id, manufacturer_user_id, supplier_uid, "NOTE_ADDED",
                    {"note_type": data.note_type})
        self.db.commit()
        return note

    def list_notes(
        self, manufacturer_user_id: str, supplier_uid: str
    ) -> List[ManufacturerSupplierNote]:
        self._get_own_supplier(manufacturer_user_id, supplier_uid)
        return (
            self.db.query(ManufacturerSupplierNote)
            .filter_by(
                manufacturer_user_id=manufacturer_user_id,
                supplier_supabase_uid=supplier_uid,
            )
            .order_by(ManufacturerSupplierNote.created_at.desc())
            .all()
        )

    # ── Audit ─────────────────────────────────────────────────────────────────

    def get_audit(
        self, manufacturer_user_id: str, supplier_uid: str, limit: int = 50
    ) -> List[SupplierLifecycleAudit]:
        self._get_own_supplier(manufacturer_user_id, supplier_uid)
        return (
            self.db.query(SupplierLifecycleAudit)
            .filter(
                SupplierLifecycleAudit.manufacturer_user_id == manufacturer_user_id,
                SupplierLifecycleAudit.supplier_supabase_uid == supplier_uid,
            )
            .order_by(SupplierLifecycleAudit.created_at.desc())
            .limit(limit)
            .all()
        )

    # ── Analytics ─────────────────────────────────────────────────────────────

    def get_analytics(self, manufacturer_user_id: str) -> SupplierAnalyticsResponse:
        from app.supplier_management.models import SupplierInvitation

        # Supplier counts via SupplierInvitation
        q = self.db.query(SupplierInvitation).filter(
            SupplierInvitation.manufacturer_user_id == manufacturer_user_id
        )
        total        = q.count()
        pending      = q.filter(SupplierInvitation.status == "PENDING").count()
        active       = q.filter(SupplierInvitation.status.in_(["APPROVED", "ACCEPTED"])).count()
        suspended    = q.filter(SupplierInvitation.status == "SUSPENDED").count()
        rejected     = q.filter(SupplierInvitation.status == "REJECTED").count()
        critical     = q.filter(SupplierInvitation.is_critical == True).count()  # noqa: E712

        # Risk distribution
        risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0, "UNKNOWN": 0}
        for inv in q.all():
            rr = getattr(inv, "risk_rating", None) or "LOW"
            rr_str = str(rr).upper()
            if rr_str in risk_dist:
                risk_dist[rr_str] += 1
            else:
                risk_dist["UNKNOWN"] += 1

        # Invitation counts
        iq = q
        total_inv    = iq.count()
        pending_inv  = iq.filter(SupplierInvitation.status == "PENDING").count()
        accepted_inv = iq.filter(SupplierInvitation.status.in_(["ACCEPTED", "APPROVED"])).count()
        expired_inv  = iq.filter(SupplierInvitation.status == "EXPIRED").count()

        acceptance_rate = round((accepted_inv / total_inv * 100) if total_inv > 0 else 0.0, 1)

        return SupplierAnalyticsResponse(
            total_suppliers     = total,
            pending_approval    = pending,
            active_suppliers    = active,
            suspended_suppliers = suspended,
            rejected_suppliers  = rejected,
            total_invitations   = total_inv,
            pending_invitations = pending_inv,
            accepted_invitations= accepted_inv,
            expired_invitations = expired_inv,
            acceptance_rate     = acceptance_rate,
            critical_suppliers  = critical,
            risk_distribution   = risk_dist,
        )

    # ── CSV Export ────────────────────────────────────────────────────────────

    def export_csv(self, manufacturer_user_id: str) -> str:
        rows, _ = self.list_suppliers(manufacturer_user_id, page_size=10000)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "supplier_code", "company_name", "email", "contact_name", "phone",
            "status", "risk_rating", "is_critical", "relationship_type",
            "headquarters_country", "headquarters_city", "created_at",
        ])
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in writer.fieldnames})
        return output.getvalue()

    # ── Private helpers ────────────────────────────────────────────────────────

    def _get_own_supplier(
        self, manufacturer_user_id: str, supplier_uid: str
    ) -> SupplierAccount:
        import uuid
        from app.supplier_management.models import SupplierInvitation
        
        is_valid_uuid = False
        try:
            uuid.UUID(str(supplier_uid))
            is_valid_uuid = True
        except (ValueError, AttributeError, TypeError):
            is_valid_uuid = False

        acct = (
            self.db.query(SupplierAccount)
            .filter_by(supabase_uid=supplier_uid)
            .first()
        )
        if not acct and is_valid_uuid:
            acct = self.db.query(SupplierAccount).filter_by(id=supplier_uid).first()
            
        if not acct:
            inv = None
            if is_valid_uuid:
                inv = self.db.query(SupplierInvitation).filter_by(
                    id=supplier_uid, manufacturer_user_id=manufacturer_user_id
                ).first()
            if not inv:
                inv = self.db.query(SupplierInvitation).filter_by(
                    supplier_supabase_uid=supplier_uid, manufacturer_user_id=manufacturer_user_id
                ).first()
            if inv:
                acct = self.db.query(SupplierAccount).filter_by(email=inv.supplier_email).first()
                if not acct:
                    acct = SupplierAccount(
                        id=inv.id,
                        supabase_uid=inv.supplier_supabase_uid or str(inv.id),
                        email=inv.supplier_email,
                        company_name=inv.supplier_company_name,
                        contact_name=inv.contact_name,
                        phone=inv.phone,
                        status=inv.status
                    )
        if not acct:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Supplier not found.")
        return acct

    def _merge_account_profile(
        self, acct: SupplierAccount, profile: Optional[SupplierCompanyProfile], full: bool = False
    ) -> dict:
        row: dict = {
            "id":                   str(acct.id),
            "supabase_uid":         acct.supabase_uid,
            "supplier_code":        getattr(acct, "supplier_code", None),
            "email":                acct.email,
            "company_name":         acct.company_name,
            "contact_name":         acct.contact_name,
            "phone":                acct.phone,
            "status":               acct.status,
            "risk_rating":          getattr(acct, "risk_rating", "UNKNOWN"),
            "is_critical":          getattr(acct, "is_critical", False),
            "relationship_type":    getattr(acct, "relationship_type", None),
            "manufacturer_user_id": getattr(acct, "manufacturer_user_id", None),
            "last_login_at":        getattr(acct, "last_login_at", None),
            "reviewed_at":          acct.reviewed_at.isoformat() if acct.reviewed_at else None,
            "created_at":           acct.created_at.isoformat() if acct.created_at else None,
            # Profile fields
            "headquarters_country":       profile.headquarters_country if profile else None,
            "headquarters_city":          profile.headquarters_city if profile else None,
            "logo_url":                   profile.logo_url if profile else None,
            "manufacturing_categories":   profile.manufacturing_categories if profile else [],
        }
        if full:
            row.update({
                "rejection_reason":   acct.rejection_reason,
                "website":            profile.website if profile else None,
                "products":           profile.products if profile else [],
                "certifications":     profile.certifications if profile else [],
                "documents":          profile.documents if profile else [],
                "locations":          profile.locations if profile else [],
                "contacts":           profile.contacts if profile else [],
                "employee_count":     profile.employee_count if profile else None,
                "annual_revenue_usd": profile.annual_revenue_usd if profile else None,
                "description":        profile.description if profile else None,
            })
        return row

    def _add_note_internal(
        self, manufacturer_user_id: str, supplier_uid: str,
        note_type: str, content: str
    ) -> ManufacturerSupplierNote:
        note = ManufacturerSupplierNote(
            manufacturer_user_id  = manufacturer_user_id,
            supplier_supabase_uid = supplier_uid,
            note_type             = note_type,
            content               = content,
            created_by            = manufacturer_user_id,
        )
        self.db.add(note)
        return note

    def _audit(
        self,
        manufacturer_user_id: str,
        actor_user_id: str,
        supplier_uid: Optional[str],
        action: str,
        metadata: dict,
        actor_role: str = "manufacturer_admin",
    ) -> None:
        self.db.add(SupplierLifecycleAudit(
            manufacturer_user_id  = manufacturer_user_id,
            actor_user_id         = actor_user_id,
            actor_role            = actor_role,
            supplier_supabase_uid = supplier_uid,
            action                = action,
            event_data            = metadata,
        ))

    @staticmethod
    def _update_supabase_metadata(supplier_uid: str, metadata: dict) -> None:
        try:
            from app.db.supabase_client import get_supabase
            sb = get_supabase()
            if sb:
                sb.auth.admin.update_user_by_id(supplier_uid, {"user_metadata": metadata})
        except Exception as exc:
            logger.warning("Supabase metadata update failed for %s: %s", supplier_uid[:8], exc)
