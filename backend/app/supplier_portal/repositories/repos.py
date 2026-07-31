"""
All supplier portal repositories — one per model.
Split into one file per model for clarity but kept cohesive here.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.supplier_portal.repositories.base_repo import BaseRepository
from app.supplier_portal.models.supplier_account import SupplierAccount
from app.supplier_portal.models.company_profile import SupplierCompanyProfile
from app.supplier_portal.models.production_capacity import SupplierProductionCapacity
from app.supplier_portal.models.inventory_item import SupplierInventoryItem
from app.supplier_portal.models.lead_time import SupplierLeadTime
from app.supplier_portal.models.shipment import SupplierShipment
from app.supplier_portal.models.incident import SupplierIncident
from app.supplier_portal.models.capacity_forecast import SupplierCapacityForecast
from app.supplier_portal.models.notification import SupplierNotification
from app.supplier_portal.models.support_ticket import SupplierSupportTicket
from app.supplier_portal.models.audit_log import SupplierAuditLog


# ── Supplier Account ───────────────────────────────────────────────────────────

class SupplierAccountRepo(BaseRepository[SupplierAccount]):
    model_class = SupplierAccount

    def get_by_supabase_uid(self, uid: str) -> Optional[SupplierAccount]:
        return self.db.query(SupplierAccount).filter(
            SupplierAccount.supabase_uid == uid
        ).first()

    def get_by_email(self, email: str) -> Optional[SupplierAccount]:
        return self.db.query(SupplierAccount).filter(
            SupplierAccount.email == email
        ).first()

    def list_by_status(self, status: str, limit: int = 50, offset: int = 0) -> Tuple[List[SupplierAccount], int]:
        q = self.db.query(SupplierAccount).filter(SupplierAccount.status == status)
        total = q.count()
        rows = q.order_by(SupplierAccount.created_at.desc()).offset(offset).limit(limit).all()
        return rows, total

    def update_status(self, account: SupplierAccount, status: str,
                      reviewed_by: str = None, rejection_reason: str = None) -> SupplierAccount:
        account.status = status
        account.reviewed_by = reviewed_by
        account.reviewed_at = datetime.now(timezone.utc)
        if rejection_reason:
            account.rejection_reason = rejection_reason
        self.db.commit()
        self.db.refresh(account)
        return account


# ── Company Profile ────────────────────────────────────────────────────────────

class CompanyProfileRepo(BaseRepository[SupplierCompanyProfile]):
    model_class = SupplierCompanyProfile

    def get_by_supplier_id(self, supplier_id: str) -> Optional[SupplierCompanyProfile]:
        return self.db.query(SupplierCompanyProfile).filter(
            SupplierCompanyProfile.supplier_id == supplier_id
        ).first()


# ── Production Capacity ────────────────────────────────────────────────────────

class ProductionCapacityRepo(BaseRepository[SupplierProductionCapacity]):
    model_class = SupplierProductionCapacity

    def get_latest(self, supplier_id: str) -> Optional[SupplierProductionCapacity]:
        return self.db.query(SupplierProductionCapacity).filter(
            SupplierProductionCapacity.supplier_id == supplier_id
        ).order_by(SupplierProductionCapacity.created_at.desc()).first()

    def get_history(self, supplier_id: str, limit: int = 20, offset: int = 0) -> Tuple[List, int]:
        q = self.db.query(SupplierProductionCapacity).filter(
            SupplierProductionCapacity.supplier_id == supplier_id
        ).order_by(SupplierProductionCapacity.created_at.desc())
        total = q.count()
        return q.offset(offset).limit(limit).all(), total


# ── Inventory ──────────────────────────────────────────────────────────────────

class InventoryRepo(BaseRepository[SupplierInventoryItem]):
    model_class = SupplierInventoryItem

    def list_for_supplier(
        self, supplier_id: str, category: str = None, warehouse_id: str = None,
        search: str = None, low_stock_only: bool = False, critical_only: bool = False,
        limit: int = 20, offset: int = 0, page: int = None, page_size: int = None, **kwargs
    ) -> Tuple[List[SupplierInventoryItem], int]:
        if page_size is not None:
            limit = page_size
        if page is not None:
            offset = (page - 1) * limit
        q = self.db.query(SupplierInventoryItem).filter(
            SupplierInventoryItem.supplier_id == supplier_id,
            SupplierInventoryItem.deleted_at == None,
            SupplierInventoryItem.is_active == True,
        )
        if category:
            q = q.filter(SupplierInventoryItem.category == category)
        if warehouse_id:
            q = q.filter(SupplierInventoryItem.warehouse_id == warehouse_id)
        if search:
            q = q.filter(
                SupplierInventoryItem.name.ilike(f"%{search}%") |
                SupplierInventoryItem.sku.ilike(f"%{search}%")
            )
        if low_stock_only:
            q = q.filter(SupplierInventoryItem.is_low_stock == True)
        if critical_only:
            q = q.filter(SupplierInventoryItem.is_critical_component == True)
        total = q.count()
        return q.order_by(SupplierInventoryItem.updated_at.desc()).offset(offset).limit(limit).all(), total

    def get_by_sku(self, supplier_id: str, sku: str) -> Optional[SupplierInventoryItem]:
        return self.db.query(SupplierInventoryItem).filter(
            SupplierInventoryItem.supplier_id == supplier_id,
            SupplierInventoryItem.sku == sku,
            SupplierInventoryItem.deleted_at == None,
        ).first()

    def warehouse_summary(self, supplier_id: str) -> List[Dict]:
        from sqlalchemy import func
        rows = (
            self.db.query(
                SupplierInventoryItem.warehouse_id,
                func.count(SupplierInventoryItem.id).label("item_count"),
                func.sum(SupplierInventoryItem.quantity_on_hand).label("total_qty"),
                func.sum(SupplierInventoryItem.quantity_on_hand * SupplierInventoryItem.unit_cost_usd).label("total_value"),
            )
            .filter(SupplierInventoryItem.supplier_id == supplier_id, SupplierInventoryItem.deleted_at == None)
            .group_by(SupplierInventoryItem.warehouse_id)
            .all()
        )
        return [{"warehouse_id": r[0], "item_count": r[1], "total_qty": r[2], "total_value": r[3]} for r in rows]


# ── Lead Times ─────────────────────────────────────────────────────────────────

class LeadTimeRepo(BaseRepository[SupplierLeadTime]):
    model_class = SupplierLeadTime

    def list_for_supplier(self, supplier_id: str, limit: int = 20, offset: int = 0, page: int = None, page_size: int = None, **kwargs) -> Tuple[List, int]:
        if page_size is not None:
            limit = page_size
        if page is not None:
            offset = (page - 1) * limit
        q = self.db.query(SupplierLeadTime).filter(
            SupplierLeadTime.supplier_id == supplier_id
        ).order_by(SupplierLeadTime.updated_at.desc())
        total = q.count()
        return q.offset(offset).limit(limit).all(), total

    def get_trends(self, supplier_id: str, limit: int = 12) -> List[SupplierLeadTime]:
        return self.db.query(SupplierLeadTime).filter(
            SupplierLeadTime.supplier_id == supplier_id
        ).order_by(SupplierLeadTime.created_at.desc()).limit(limit).all()


# ── Shipments ──────────────────────────────────────────────────────────────────

class ShipmentRepo(BaseRepository[SupplierShipment]):
    model_class = SupplierShipment

    def list_for_supplier(
        self, supplier_id: str, status: str = None, search: str = None,
        limit: int = 20, offset: int = 0, page: int = None, page_size: int = None, **kwargs
    ) -> Tuple[List[SupplierShipment], int]:
        if page_size is not None:
            limit = page_size
        if page is not None:
            offset = (page - 1) * limit
        q = self.db.query(SupplierShipment).filter(
            SupplierShipment.supplier_id == supplier_id,
            SupplierShipment.deleted_at == None,
        )
        if status:
            q = q.filter(SupplierShipment.status == status)
        if search:
            q = q.filter(
                SupplierShipment.shipment_number.ilike(f"%{search}%") |
                SupplierShipment.tracking_number.ilike(f"%{search}%")
            )
        total = q.count()
        return q.order_by(SupplierShipment.created_at.desc()).offset(offset).limit(limit).all(), total

    def add_timeline_event(self, shipment: SupplierShipment, event: Dict) -> SupplierShipment:
        timeline = list(shipment.timeline or [])
        timeline.append(event)
        shipment.timeline = timeline
        self.db.commit()
        self.db.refresh(shipment)
        return shipment


# ── Incidents ──────────────────────────────────────────────────────────────────

class IncidentRepo(BaseRepository[SupplierIncident]):
    model_class = SupplierIncident

    def list_for_supplier(
        self, supplier_id: str, incident_type: str = None, severity: str = None,
        status: str = None, limit: int = 20, offset: int = 0, page: int = None, page_size: int = None, **kwargs
    ) -> Tuple[List[SupplierIncident], int]:
        if page_size is not None:
            limit = page_size
        if page is not None:
            offset = (page - 1) * limit
        q = self.db.query(SupplierIncident).filter(
            SupplierIncident.supplier_id == supplier_id,
            SupplierIncident.is_deleted == 0,
        )
        if incident_type:
            q = q.filter(SupplierIncident.incident_type == incident_type)
        if severity:
            q = q.filter(SupplierIncident.severity == severity)
        if status:
            q = q.filter(SupplierIncident.status == status)
        total = q.count()
        return q.order_by(SupplierIncident.reported_at.desc()).offset(offset).limit(limit).all(), total

    def add_attachment(self, incident: SupplierIncident, attachment: Dict) -> SupplierIncident:
        attachments = list(incident.attachments or [])
        attachments.append(attachment)
        incident.attachments = attachments
        self.db.commit()
        self.db.refresh(incident)
        return incident


# ── Capacity Forecast ──────────────────────────────────────────────────────────

class ForecastRepo(BaseRepository[SupplierCapacityForecast]):
    model_class = SupplierCapacityForecast

    def list_by_year(self, supplier_id: str, year: int, period_type: str = None) -> List[SupplierCapacityForecast]:
        q = self.db.query(SupplierCapacityForecast).filter(
            SupplierCapacityForecast.supplier_id == supplier_id,
            SupplierCapacityForecast.forecast_year == year,
        )
        if period_type:
            q = q.filter(SupplierCapacityForecast.period_type == period_type)
        return q.order_by(SupplierCapacityForecast.forecast_month.asc()).all()

    def list_history(self, supplier_id: str, limit: int = 50, offset: int = 0) -> Tuple[List, int]:
        q = self.db.query(SupplierCapacityForecast).filter(
            SupplierCapacityForecast.supplier_id == supplier_id
        ).order_by(SupplierCapacityForecast.created_at.desc())
        total = q.count()
        return q.offset(offset).limit(limit).all(), total


# ── Notifications ──────────────────────────────────────────────────────────────

class NotificationRepo(BaseRepository[SupplierNotification]):
    model_class = SupplierNotification

    def list_for_supplier(
        self, supplier_id: str, category: str = None, unread_only: bool = False,
        limit: int = 30, offset: int = 0, page: int = None, page_size: int = None, **kwargs
    ) -> Tuple[List[SupplierNotification], int]:
        if page_size is not None:
            limit = page_size
        if page is not None:
            offset = (page - 1) * limit
        q = self.db.query(SupplierNotification).filter(
            SupplierNotification.supplier_id == supplier_id,
            SupplierNotification.is_deleted == False,
        )
        if category:
            q = q.filter(SupplierNotification.category == category)
        if unread_only:
            q = q.filter(SupplierNotification.is_read == False)
        total = q.count()
        return q.order_by(SupplierNotification.created_at.desc()).offset(offset).limit(limit).all(), total

    def get_unread_counts(self, supplier_id: str) -> Dict[str, int]:
        from sqlalchemy import func
        rows = (
            self.db.query(SupplierNotification.category, func.count(SupplierNotification.id))
            .filter(
                SupplierNotification.supplier_id == supplier_id,
                SupplierNotification.is_read == False,
                SupplierNotification.is_deleted == False,
            )
            .group_by(SupplierNotification.category)
            .all()
        )
        return {r[0]: r[1] for r in rows}

    def mark_all_read(self, supplier_id: str) -> int:
        count = (
            self.db.query(SupplierNotification)
            .filter(
                SupplierNotification.supplier_id == supplier_id,
                SupplierNotification.is_read == False,
                SupplierNotification.is_deleted == False,
            )
            .update({"is_read": True, "read_at": datetime.now(timezone.utc)})
        )
        self.db.commit()
        return count

    def create_notification(self, supplier_id: str, category: str, priority: str,
                            title: str, body: str = None, action_url: str = None,
                            metadata: dict = None) -> SupplierNotification:
        notif = SupplierNotification(
            id=uuid.uuid4(),
            supplier_id=supplier_id,
            category=category,
            priority=priority,
            title=title,
            body=body,
            action_url=action_url,
            extra_metadata=metadata,
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        return notif


# ── Support Tickets ────────────────────────────────────────────────────────────

class SupportRepo(BaseRepository[SupplierSupportTicket]):
    model_class = SupplierSupportTicket

    def list_for_supplier(self, supplier_id: str, status: str = None,
                          limit: int = 20, offset: int = 0, page: int = None, page_size: int = None, **kwargs) -> Tuple[List, int]:
        if page_size is not None:
            limit = page_size
        if page is not None:
            offset = (page - 1) * limit
        q = self.db.query(SupplierSupportTicket).filter(
            SupplierSupportTicket.supplier_id == supplier_id
        )
        if status:
            q = q.filter(SupplierSupportTicket.status == status)
        total = q.count()
        return q.order_by(SupplierSupportTicket.created_at.desc()).offset(offset).limit(limit).all(), total

    def generate_ticket_number(self) -> str:
        import random, string
        return "TKT-" + "".join(random.choices(string.digits, k=8))

    def add_reply(self, ticket: SupplierSupportTicket, reply: Dict) -> SupplierSupportTicket:
        replies = list(ticket.replies or [])
        replies.append(reply)
        ticket.replies = replies
        self.db.commit()
        self.db.refresh(ticket)
        return ticket


# ── Audit Log ─────────────────────────────────────────────────────────────────

from app.core.json_utils import sanitize_json_payload


class AuditLogRepo:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        supplier_id: str,
        user_id: str,
        action: str,
        entity: str,
        entity_id: str = None,
        old_value: dict = None,
        new_value: dict = None,
        ip_address: str = None,
        user_agent: str = None,
        notes: str = None,
    ) -> SupplierAuditLog:
        entry = SupplierAuditLog(
            id=uuid.uuid4(),
            supplier_id=supplier_id,
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=str(entity_id) if entity_id else None,
            old_value=sanitize_json_payload(old_value),
            new_value=sanitize_json_payload(new_value),
            ip_address=ip_address,
            user_agent=user_agent,
            notes=notes,
        )
        self.db.add(entry)
        self.db.commit()
        return entry

    def list_for_supplier(self, supplier_id: str, limit: int = 50, offset: int = 0):
        return (
            self.db.query(SupplierAuditLog)
            .filter(SupplierAuditLog.supplier_id == supplier_id)
            .order_by(SupplierAuditLog.created_at.desc())
            .offset(offset).limit(limit).all()
        )


# ── Performance (reads from existing Phase 6 table) ───────────────────────────

class PerformanceRepo:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest_scores(self, supplier_id: str):
        from app.db.models.supplier_score import SupplierScore
        return (
            self.db.query(SupplierScore)
            .filter(SupplierScore.supplier_id == supplier_id)
            .order_by(SupplierScore.evaluated_at.desc())
            .first()
        )

    def get_history(self, supplier_id: str, limit: int = 12):
        from app.db.models.supplier_score import SupplierScore
        return (
            self.db.query(SupplierScore)
            .filter(SupplierScore.supplier_id == supplier_id)
            .order_by(SupplierScore.evaluated_at.desc())
            .limit(limit).all()
        )
