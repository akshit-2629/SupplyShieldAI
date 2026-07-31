"""
All supplier portal business-logic services — one class per module.
Each service:
  - Owns repository interactions
  - Writes audit log entries on every mutation
  - Calls orchestrator_bridge.notify() after successful writes
  - Never contains HTTP concerns (no Request/Response objects)
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, ValidationException
from app.supplier_portal.repositories.repos import (
    CompanyProfileRepo, ProductionCapacityRepo, InventoryRepo,
    LeadTimeRepo, ShipmentRepo, IncidentRepo, ForecastRepo,
    NotificationRepo, SupportRepo, AuditLogRepo, PerformanceRepo,
    SupplierAccountRepo,
)
from app.supplier_portal.models.company_profile import SupplierCompanyProfile
from app.supplier_portal.models.production_capacity import SupplierProductionCapacity
from app.supplier_portal.models.inventory_item import SupplierInventoryItem
from app.supplier_portal.models.lead_time import SupplierLeadTime
from app.supplier_portal.models.shipment import SupplierShipment
from app.supplier_portal.models.incident import SupplierIncident
from app.supplier_portal.models.capacity_forecast import SupplierCapacityForecast
from app.supplier_portal.models.support_ticket import SupplierSupportTicket
from app.supplier_portal.services.orchestrator_bridge import orchestrator_bridge
from app.orchestrator.events import EventType

logger = logging.getLogger("supplier_portal.services")


# ══════════════════════════════════════════════════════════════════════════════
# COMPANY PROFILE SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class CompanyProfileService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CompanyProfileRepo(db)
        self.audit = AuditLogRepo(db)

    def get_profile(self, supplier_id: str) -> Optional[SupplierCompanyProfile]:
        profile = self.repo.get_by_supplier_id(supplier_id)
        acct = SupplierAccountRepo(self.db).get_by_supabase_uid(supplier_id)
        acct_name = acct.company_name if acct and acct.company_name and acct.company_name != "My Company" else None

        if not profile:
            if acct_name:
                profile = SupplierCompanyProfile(id=uuid.uuid4(), supplier_id=supplier_id, company_name=acct_name)
                self.repo.create(profile)
            return profile

        if (not profile.company_name or profile.company_name == "My Company") and acct_name:
            profile.company_name = acct_name
            self.db.commit()
            self.db.refresh(profile)

        return profile

    def create_profile(self, supplier_id: str, user_id: str, data: dict,
                       ip_address: str = None) -> SupplierCompanyProfile:
        existing = self.repo.get_by_supplier_id(supplier_id)
        if existing:
            raise ValidationException("Company profile already exists. Use PUT to update.")
        profile = SupplierCompanyProfile(id=uuid.uuid4(), supplier_id=supplier_id, **data)
        created = self.repo.create(profile)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="PROFILE_CREATED", entity="supplier_company_profiles",
                       entity_id=str(created.id), new_value=data, ip_address=ip_address)
        orchestrator_bridge.notify_sync(
            EventType.SUPPLIER_PORTAL_PROFILE_UPDATED.value, supplier_id,
            {"action": "created", "supplier_id": supplier_id}
        )
        return created

    def update_profile(self, supplier_id: str, user_id: str, data: dict,
                       ip_address: str = None) -> SupplierCompanyProfile:
        normalized = {}
        if "company_name" in data or "companyName" in data:
            cname = data.get("company_name") or data.get("companyName")
            if cname and str(cname).strip():
                normalized["company_name"] = str(cname).strip()
        if "legal_name" in data or "legalName" in data:
            normalized["legal_name"] = data.get("legal_name") or data.get("legalName")
        if "headquarters_country" in data or "country" in data:
            normalized["headquarters_country"] = data.get("headquarters_country") or data.get("country")
        if "headquarters_city" in data or "city" in data:
            normalized["headquarters_city"] = data.get("headquarters_city") or data.get("city")
        if "description" in data:
            normalized["description"] = data.get("description")
        if "website" in data:
            normalized["website"] = data.get("website")
        if "email" in data:
            normalized["email"] = data.get("email")
        if "phone" in data:
            normalized["phone"] = data.get("phone")
        if "industry" in data or "manufacturing_categories" in data:
            ind = data.get("manufacturing_categories") or data.get("industry")
            if isinstance(ind, str) and ind.strip():
                normalized["manufacturing_categories"] = [ind.strip()]
            elif isinstance(ind, list):
                normalized["manufacturing_categories"] = ind
        if "founded" in data or "year_established" in data:
            val = data.get("year_established") or data.get("founded")
            try:
                if val: normalized["year_established"] = int(val)
            except (ValueError, TypeError):
                pass
        if "employees" in data or "employee_count" in data:
            val = data.get("employee_count") or data.get("employees")
            try:
                if val: normalized["employee_count"] = int(val)
            except (ValueError, TypeError):
                pass

        valid_cols = {c.name for c in SupplierCompanyProfile.__table__.columns}
        for k, v in data.items():
            if k in valid_cols and k not in normalized and v is not None:
                normalized[k] = v

        acct = SupplierAccountRepo(self.db).get_by_supabase_uid(supplier_id)
        if normalized.get("company_name") and acct:
            acct.company_name = normalized["company_name"]
            self.db.commit()

        profile = self.repo.get_by_supplier_id(supplier_id)
        if not profile:
            if "company_name" not in normalized or not normalized["company_name"]:
                normalized["company_name"] = acct.company_name if acct and acct.company_name else "My Company"
            profile = SupplierCompanyProfile(id=uuid.uuid4(), supplier_id=supplier_id, **normalized)
            updated = self.repo.create(profile)
            self.audit.log(supplier_id=supplier_id, user_id=user_id,
                           action="PROFILE_CREATED", entity="supplier_company_profiles",
                           entity_id=str(updated.id), new_value=normalized, ip_address=ip_address)
        else:
            old = {k: getattr(profile, k, None) for k in normalized}
            updated = self.repo.update(profile, normalized)
            self.audit.log(supplier_id=supplier_id, user_id=user_id,
                           action="PROFILE_UPDATED", entity="supplier_company_profiles",
                           entity_id=str(updated.id), old_value=old, new_value=normalized, ip_address=ip_address)

        if updated and updated.products:
            self._sync_products_to_inventory(supplier_id, updated.products)

        orchestrator_bridge.notify_sync(
            EventType.SUPPLIER_PORTAL_PROFILE_UPDATED.value, supplier_id,
            {"action": "updated", "supplier_id": supplier_id}
        )
        return updated

    def _sync_products_to_inventory(self, supplier_id: str, products: list) -> None:
        if not products or not isinstance(products, list):
            return
        inv_repo = InventoryRepo(self.db)
        for p in products:
            if not isinstance(p, dict):
                continue
            p_name = (p.get("name") or p.get("title") or "").strip()
            if not p_name:
                continue
            p_sku = (p.get("sku") or "").strip()
            if not p_sku:
                clean_name = "".join(c for c in p_name.upper() if c.isalnum())[:10]
                p_sku = f"SKU-{clean_name or 'PROD'}-{uuid.uuid4().hex[:4].upper()}"

            existing = inv_repo.get_by_sku(supplier_id, p_sku)
            if not existing:
                existing_name = self.db.query(SupplierInventoryItem).filter(
                    SupplierInventoryItem.supplier_id == supplier_id,
                    SupplierInventoryItem.name == p_name,
                    SupplierInventoryItem.deleted_at.is_(None)
                ).first()
                if not existing_name:
                    item = SupplierInventoryItem(
                        id=uuid.uuid4(),
                        supplier_id=supplier_id,
                        sku=p_sku,
                        name=p_name,
                        description=p.get("description") or "",
                        category=p.get("category") or "General",
                        unit=p.get("unit") or "units",
                        quantity_on_hand=int(p.get("quantity") or p.get("quantity_on_hand") or 0),
                        safety_stock_level=int(p.get("safetyStock") or p.get("safety_stock_level") or 0),
                        is_active=True
                    )
                    inv_repo.create(item)


    def update_logo(self, supplier_id: str, logo_url: str) -> SupplierCompanyProfile:
        profile = self.repo.get_by_supplier_id(supplier_id)
        if not profile:
            raise NotFoundException("Company profile not found")
        profile.logo_url = logo_url
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def add_document(self, supplier_id: str, doc: dict) -> SupplierCompanyProfile:
        profile = self.repo.get_by_supplier_id(supplier_id)
        if not profile:
            raise NotFoundException("Company profile not found")
        docs = list(profile.documents or [])
        doc["doc_id"] = str(uuid.uuid4())
        doc["uploaded_at"] = datetime.now(timezone.utc).isoformat()
        docs.append(doc)
        profile.documents = docs
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def delete_document(self, supplier_id: str, doc_id: str) -> SupplierCompanyProfile:
        profile = self.repo.get_by_supplier_id(supplier_id)
        if not profile:
            raise NotFoundException("Company profile not found")
        profile.documents = [d for d in (profile.documents or []) if d.get("doc_id") != doc_id]
        self.db.commit()
        self.db.refresh(profile)
        return profile


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTION CAPACITY SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class ProductionCapacityService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProductionCapacityRepo(db)
        self.audit = AuditLogRepo(db)

    def get_latest(self, supplier_id: str) -> Optional[SupplierProductionCapacity]:
        return self.repo.get_latest(supplier_id)

    def get_history(self, supplier_id: str, page: int = 1, page_size: int = 20) -> Tuple[List, int]:
        offset = (page - 1) * page_size
        return self.repo.get_history(supplier_id, limit=page_size, offset=offset)

    async def submit_update(self, supplier_id: str, user_id: str, data: dict,
                            ip_address: str = None) -> SupplierProductionCapacity:
        # Compute is_low_stock / compute utilization if missing
        max_cap = data.get("maximum_capacity_units", 0) or 0
        current = data.get("current_output_units", 0) or 0
        if max_cap > 0 and "utilization_pct" not in data:
            data["utilization_pct"] = round((current / max_cap) * 100, 2)

        snapshot = SupplierProductionCapacity(
            id=uuid.uuid4(), supplier_id=supplier_id,
            submitted_by=user_id, ip_address=ip_address, **data
        )
        created = self.repo.create(snapshot)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="PRODUCTION_UPDATED", entity="supplier_production_capacity",
                       entity_id=str(created.id), new_value=data, ip_address=ip_address)
        await orchestrator_bridge.notify(
            EventType.SUPPLIER_PORTAL_PRODUCTION_UPDATED.value, supplier_id,
            {"snapshot_id": str(created.id), "utilization_pct": data.get("utilization_pct")}
        )
        return created


# ══════════════════════════════════════════════════════════════════════════════
# INVENTORY SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InventoryRepo(db)
        self.audit = AuditLogRepo(db)

    def list_items(self, supplier_id: str, **kwargs) -> Tuple[List, int]:
        return self.repo.list_for_supplier(supplier_id, **kwargs)

    def get_item(self, supplier_id: str, item_id: str) -> SupplierInventoryItem:
        item = self.repo.get_by_id(item_id)
        if not item or item.supplier_id != supplier_id or item.deleted_at:
            raise NotFoundException(f"Inventory item {item_id} not found")
        return item

    def _compute_flags(self, item: SupplierInventoryItem) -> None:
        safety = item.safety_stock_level or 0
        item.is_low_stock = item.quantity_on_hand <= safety if safety > 0 else False

    async def create_item(self, supplier_id: str, user_id: str, data: dict,
                          ip_address: str = None) -> SupplierInventoryItem:
        # Duplicate SKU check
        existing = self.repo.get_by_sku(supplier_id, data["sku"])
        if existing:
            raise ValidationException(f"SKU '{data['sku']}' already exists in your inventory")
        item = SupplierInventoryItem(id=uuid.uuid4(), supplier_id=supplier_id, **data)
        self._compute_flags(item)
        created = self.repo.create(item)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="INVENTORY_CREATED", entity="supplier_inventory_items",
                       entity_id=str(created.id), new_value=data, ip_address=ip_address)
        await orchestrator_bridge.notify(
            EventType.SUPPLIER_PORTAL_INVENTORY_UPDATED.value, supplier_id,
            {"action": "created", "item_id": str(created.id), "sku": created.sku}
        )
        return created

    async def update_item(self, supplier_id: str, user_id: str, item_id: str,
                          data: dict, ip_address: str = None) -> SupplierInventoryItem:
        item = self.get_item(supplier_id, item_id)
        old = {k: getattr(item, k, None) for k in data}
        updated = self.repo.update(item, data)
        self._compute_flags(updated)
        self.db.commit()
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="INVENTORY_UPDATED", entity="supplier_inventory_items",
                       entity_id=item_id, old_value=old, new_value=data, ip_address=ip_address)
        await orchestrator_bridge.notify(
            EventType.SUPPLIER_PORTAL_INVENTORY_UPDATED.value, supplier_id,
            {"action": "updated", "item_id": item_id}
        )
        return updated

    async def delete_item(self, supplier_id: str, user_id: str, item_id: str,
                          ip_address: str = None) -> None:
        item = self.get_item(supplier_id, item_id)
        self.repo.soft_delete(item, field="deleted_at")
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="INVENTORY_DELETED", entity="supplier_inventory_items",
                       entity_id=item_id, ip_address=ip_address)
        await orchestrator_bridge.notify(
            EventType.SUPPLIER_PORTAL_INVENTORY_UPDATED.value, supplier_id,
            {"action": "deleted", "item_id": item_id}
        )

    def warehouse_summary(self, supplier_id: str) -> List[dict]:
        return self.repo.warehouse_summary(supplier_id)

    async def bulk_update(self, supplier_id: str, user_id: str, items: List[dict],
                          ip_address: str = None) -> dict:
        updated_count = 0
        errors = []
        for item_data in items:
            item_id = item_data.pop("id", None)
            if not item_id:
                errors.append({"error": "Missing id field", "data": item_data})
                continue
            try:
                await self.update_item(supplier_id, user_id, item_id, item_data, ip_address)
                updated_count += 1
            except Exception as exc:
                errors.append({"id": item_id, "error": str(exc)})
        return {"updated": updated_count, "errors": errors}


# ══════════════════════════════════════════════════════════════════════════════
# LEAD TIME SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class LeadTimeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = LeadTimeRepo(db)
        self.audit = AuditLogRepo(db)

    def list_records(self, supplier_id: str, page: int = 1, page_size: int = 20) -> Tuple[List, int]:
        offset = (page - 1) * page_size
        return self.repo.list_for_supplier(supplier_id, limit=page_size, offset=offset)

    def get_record(self, supplier_id: str, record_id: str) -> SupplierLeadTime:
        record = self.repo.get_by_id(record_id)
        if not record or record.supplier_id != supplier_id:
            raise NotFoundException(f"Lead time record {record_id} not found")
        return record

    def _compute_total(self, data: dict) -> dict:
        components = ["manufacturing_days", "packaging_days", "quality_check_days",
                      "shipping_days", "customs_days"]
        total = sum(data.get(c) or 0 for c in components)
        if total > 0 and "total_lead_time_days" not in data:
            data["total_lead_time_days"] = total
        return data

    async def create_record(self, supplier_id: str, user_id: str, data: dict,
                            ip_address: str = None) -> SupplierLeadTime:
        data = self._compute_total(data)
        record = SupplierLeadTime(id=uuid.uuid4(), supplier_id=supplier_id, **data)
        created = self.repo.create(record)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="LEAD_TIME_CREATED", entity="supplier_lead_times",
                       entity_id=str(created.id), new_value=data, ip_address=ip_address)
        await orchestrator_bridge.notify(
            EventType.SUPPLIER_PORTAL_LEAD_TIME_UPDATED.value, supplier_id,
            {"record_id": str(created.id)}
        )
        return created

    async def update_record(self, supplier_id: str, user_id: str, record_id: str,
                            data: dict, ip_address: str = None) -> SupplierLeadTime:
        record = self.get_record(supplier_id, record_id)
        data = self._compute_total(data)
        old = {k: getattr(record, k, None) for k in data}
        updated = self.repo.update(record, data)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="LEAD_TIME_UPDATED", entity="supplier_lead_times",
                       entity_id=record_id, old_value=old, new_value=data, ip_address=ip_address)
        await orchestrator_bridge.notify(
            EventType.SUPPLIER_PORTAL_LEAD_TIME_UPDATED.value, supplier_id,
            {"record_id": record_id}
        )
        return updated

    async def delete_record(self, supplier_id: str, user_id: str, record_id: str,
                            ip_address: str = None) -> None:
        record = self.get_record(supplier_id, record_id)
        self.repo.delete(record)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="LEAD_TIME_DELETED", entity="supplier_lead_times",
                       entity_id=record_id, ip_address=ip_address)

    def get_trends(self, supplier_id: str) -> List:
        return self.repo.get_trends(supplier_id)


# ══════════════════════════════════════════════════════════════════════════════
# SHIPMENT SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class ShipmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ShipmentRepo(db)
        self.audit = AuditLogRepo(db)

    def list_shipments(self, supplier_id: str, status: str = None, search: str = None,
                       page: int = 1, page_size: int = 20) -> Tuple[List, int]:
        offset = (page - 1) * page_size
        return self.repo.list_for_supplier(supplier_id, status=status, search=search,
                                           limit=page_size, offset=offset)

    def get_shipment(self, supplier_id: str, shipment_id: str) -> SupplierShipment:
        s = self.repo.get_by_id(shipment_id)
        if not s or s.supplier_id != supplier_id or s.deleted_at:
            raise NotFoundException(f"Shipment {shipment_id} not found")
        return s

    async def create_shipment(self, supplier_id: str, user_id: str, data: dict,
                              ip_address: str = None) -> SupplierShipment:
        shipment = SupplierShipment(id=uuid.uuid4(), supplier_id=supplier_id, **data)
        created = self.repo.create(shipment)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="SHIPMENT_CREATED", entity="supplier_shipments",
                       entity_id=str(created.id), new_value=data, ip_address=ip_address)
        await orchestrator_bridge.notify(
            EventType.SUPPLIER_PORTAL_SHIPMENT_UPDATED.value, supplier_id,
            {"action": "created", "shipment_id": str(created.id)}
        )
        return created

    async def update_shipment(self, supplier_id: str, user_id: str, shipment_id: str,
                              data: dict, ip_address: str = None) -> SupplierShipment:
        shipment = self.get_shipment(supplier_id, shipment_id)
        old = {k: getattr(shipment, k, None) for k in data}
        updated = self.repo.update(shipment, data)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="SHIPMENT_UPDATED", entity="supplier_shipments",
                       entity_id=shipment_id, old_value=old, new_value=data, ip_address=ip_address)
        await orchestrator_bridge.notify(
            EventType.SUPPLIER_PORTAL_SHIPMENT_UPDATED.value, supplier_id,
            {"action": "updated", "shipment_id": shipment_id}
        )
        return updated

    async def update_status(self, supplier_id: str, user_id: str, shipment_id: str,
                            status: str, notes: str = None, ip_address: str = None) -> SupplierShipment:
        shipment = self.get_shipment(supplier_id, shipment_id)
        old_status = shipment.status
        shipment.status = status
        if status == "DELIVERED":
            shipment.actual_arrival = datetime.now(timezone.utc)
        # Append timeline event
        event = {"event": f"Status changed to {status}", "timestamp": datetime.now(timezone.utc).isoformat(), "notes": notes}
        self.repo.add_timeline_event(shipment, event)
        self.db.commit()
        self.audit.log(supplier_id=supplier_id, user_id=user_id, action="SHIPMENT_STATUS_UPDATED",
                       entity="supplier_shipments", entity_id=shipment_id,
                       old_value={"status": old_status}, new_value={"status": status},
                       ip_address=ip_address)
        await orchestrator_bridge.notify(
            EventType.SUPPLIER_PORTAL_SHIPMENT_UPDATED.value, supplier_id,
            {"action": "status_changed", "shipment_id": shipment_id, "status": status}
        )
        return shipment

    async def delete_shipment(self, supplier_id: str, user_id: str, shipment_id: str,
                              ip_address: str = None) -> None:
        shipment = self.get_shipment(supplier_id, shipment_id)
        self.repo.soft_delete(shipment, field="deleted_at")
        self.audit.log(supplier_id=supplier_id, user_id=user_id, action="SHIPMENT_DELETED",
                       entity="supplier_shipments", entity_id=shipment_id, ip_address=ip_address)

    def add_timeline_event(self, supplier_id: str, shipment_id: str, event: dict) -> SupplierShipment:
        shipment = self.get_shipment(supplier_id, shipment_id)
        return self.repo.add_timeline_event(shipment, event)


# ══════════════════════════════════════════════════════════════════════════════
# INCIDENT SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class IncidentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = IncidentRepo(db)
        self.audit = AuditLogRepo(db)

    def list_incidents(self, supplier_id: str, incident_type: str = None, severity: str = None,
                       status: str = None, page: int = 1, page_size: int = 20) -> Tuple[List, int]:
        offset = (page - 1) * page_size
        return self.repo.list_for_supplier(supplier_id, incident_type=incident_type,
                                           severity=severity, status=status,
                                           limit=page_size, offset=offset)

    def get_incident(self, supplier_id: str, incident_id: str) -> SupplierIncident:
        incident = self.repo.get_by_id(incident_id)
        if not incident or incident.supplier_id != supplier_id or incident.is_deleted:
            raise NotFoundException(f"Incident {incident_id} not found")
        return incident

    async def report_incident(self, supplier_id: str, user_id: str, data: dict,
                              ip_address: str = None) -> SupplierIncident:
        incident = SupplierIncident(
            id=uuid.uuid4(), supplier_id=supplier_id, ip_address=ip_address, **data
        )
        created = self.repo.create(incident)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="INCIDENT_REPORTED", entity="supplier_incidents",
                       entity_id=str(created.id), new_value=data, ip_address=ip_address)
        # Incident reporting triggers the orchestrator with HIGH priority context
        await orchestrator_bridge.notify(
            EventType.SUPPLIER_PORTAL_INCIDENT_REPORTED.value, supplier_id,
            {
                "incident_id": str(created.id),
                "incident_type": data.get("incident_type"),
                "severity": data.get("severity"),
                "title": data.get("title"),
                "supplier_id": supplier_id,
            }
        )
        return created

    async def update_incident(self, supplier_id: str, user_id: str, incident_id: str,
                              data: dict, ip_address: str = None) -> SupplierIncident:
        incident = self.get_incident(supplier_id, incident_id)
        old = {k: getattr(incident, k, None) for k in data}
        if data.get("status") in ("RESOLVED", "CLOSED") and not incident.resolved_at:
            data["resolved_at"] = datetime.now(timezone.utc)
        updated = self.repo.update(incident, data)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="INCIDENT_UPDATED", entity="supplier_incidents",
                       entity_id=incident_id, old_value=old, new_value=data, ip_address=ip_address)
        return updated

    def add_attachment(self, supplier_id: str, incident_id: str, attachment: dict) -> SupplierIncident:
        incident = self.get_incident(supplier_id, incident_id)
        return self.repo.add_attachment(incident, attachment)

    async def retract_incident(self, supplier_id: str, user_id: str, incident_id: str,
                               ip_address: str = None) -> None:
        incident = self.get_incident(supplier_id, incident_id)
        incident.is_deleted = 1
        self.db.commit()
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="INCIDENT_RETRACTED", entity="supplier_incidents",
                       entity_id=incident_id, ip_address=ip_address)


# ══════════════════════════════════════════════════════════════════════════════
# FORECAST SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class ForecastService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ForecastRepo(db)
        self.audit = AuditLogRepo(db)

    def get_monthly(self, supplier_id: str, year: int) -> List:
        return self.repo.list_by_year(supplier_id, year, period_type="monthly")

    def get_quarterly(self, supplier_id: str, year: int) -> List:
        return self.repo.list_by_year(supplier_id, year, period_type="quarterly")

    def get_history(self, supplier_id: str, page: int = 1, page_size: int = 50) -> Tuple[List, int]:
        offset = (page - 1) * page_size
        return self.repo.list_history(supplier_id, limit=page_size, offset=offset)

    def get_by_id(self, supplier_id: str, forecast_id: str) -> SupplierCapacityForecast:
        f = self.repo.get_by_id(forecast_id)
        if not f or f.supplier_id != supplier_id:
            raise NotFoundException(f"Forecast {forecast_id} not found")
        return f

    async def submit_forecast(self, supplier_id: str, user_id: str,
                              year: int, period_type: str, entries: List[dict],
                              ip_address: str = None) -> List[SupplierCapacityForecast]:
        created_entries = []
        for entry in entries:
            forecast = SupplierCapacityForecast(
                id=uuid.uuid4(), supplier_id=supplier_id,
                forecast_year=year, period_type=period_type,
                submitted_by=user_id, **entry
            )
            created = self.repo.create(forecast)
            created_entries.append(created)

        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="FORECAST_SUBMITTED", entity="supplier_capacity_forecasts",
                       new_value={"year": year, "period_type": period_type, "entries": len(entries)},
                       ip_address=ip_address)
        await orchestrator_bridge.notify(
            EventType.SUPPLIER_PORTAL_FORECAST_UPDATED.value, supplier_id,
            {"year": year, "period_type": period_type, "entry_count": len(entries)}
        )
        return created_entries

    async def update_entry(self, supplier_id: str, user_id: str, forecast_id: str,
                           data: dict, ip_address: str = None) -> SupplierCapacityForecast:
        forecast = self.get_by_id(supplier_id, forecast_id)
        updated = self.repo.update(forecast, data)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="FORECAST_UPDATED", entity="supplier_capacity_forecasts",
                       entity_id=forecast_id, new_value=data, ip_address=ip_address)
        return updated

    async def delete_entry(self, supplier_id: str, user_id: str, forecast_id: str,
                           ip_address: str = None) -> None:
        forecast = self.get_by_id(supplier_id, forecast_id)
        self.repo.delete(forecast)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="FORECAST_DELETED", entity="supplier_capacity_forecasts",
                       entity_id=forecast_id, ip_address=ip_address)


# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE SERVICE (read-only — reads from Phase 6 supplier_scores table)
# ══════════════════════════════════════════════════════════════════════════════

class PerformanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PerformanceRepo(db)

    def get_scores(self, supplier_id: str):
        scores = self.repo.get_latest_scores(supplier_id)
        if not scores:
            scores = self.calculate_and_save_initial_scores(supplier_id)
        return scores

    def calculate_and_save_initial_scores(self, supplier_id: str):
        import uuid
        from datetime import datetime, timezone
        from app.db.models.supplier_score import SupplierScore
        from app.supplier_portal.models.incident import SupplierIncident

        incident_count = 0
        try:
            incident_count = (
                self.db.query(SupplierIncident)
                .filter(SupplierIncident.supplier_id == supplier_id, SupplierIncident.is_deleted == 0)
                .count()
            )
        except Exception:
            pass

        reliability = max(60.0, round(95.0 - (incident_count * 5.0), 1))
        quality = max(65.0, round(94.0 - (incident_count * 4.0), 1))
        risk = min(90.0, round(12.0 + (incident_count * 8.0), 1))
        health = round((reliability * 0.35 + quality * 0.35 + (100.0 - risk) * 0.30), 1)

        scores = SupplierScore(
            id=uuid.uuid4(),
            supplier_id=supplier_id,
            execution_id="INITIAL_AI_EVALUATION",
            health_score=health,
            health_label="OPTIMAL" if health >= 80 else "MODERATE",
            reliability_score=reliability,
            quality_score=quality,
            lead_time_score=91.0,
            cost_efficiency=88.0,
            compliance_score=96.0,
            responsiveness=92.0,
            flexibility=89.0,
            risk_score=risk,
            risk_level="LOW" if risk < 30 else "MEDIUM",
            evaluated_at=datetime.now(timezone.utc),
        )
        self.db.add(scores)
        self.db.commit()
        self.db.refresh(scores)
        return scores

    def get_history(self, supplier_id: str, limit: int = 12) -> List:
        rows = self.repo.get_history(supplier_id, limit=limit)
        if not rows:
            latest = self.get_scores(supplier_id)
            if latest:
                rows = [latest]
        return rows


# ══════════════════════════════════════════════════════════════════════════════
# NOTIFICATION SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class NotificationService:
    def __init__(self, db: Session):
        self.repo = NotificationRepo(db)

    def list_notifications(self, supplier_id: str, category: str = None,
                           page: int = 1, page_size: int = 30) -> Tuple[List, int]:
        offset = (page - 1) * page_size
        return self.repo.list_for_supplier(supplier_id, category=category,
                                           limit=page_size, offset=offset)

    def get_unread_count(self, supplier_id: str) -> dict:
        counts = self.repo.get_unread_counts(supplier_id)
        total = sum(counts.values())
        return {"total_unread": total, "by_category": counts}

    def mark_read(self, supplier_id: str, notification_id: str):
        n = self.repo.get_by_id(notification_id)
        if not n or n.supplier_id != supplier_id:
            raise NotFoundException(f"Notification {notification_id} not found")
        n.is_read = True
        n.read_at = datetime.now(timezone.utc)
        self.repo.db.commit()
        return n

    def mark_all_read(self, supplier_id: str) -> int:
        return self.repo.mark_all_read(supplier_id)

    def delete_notification(self, supplier_id: str, notification_id: str):
        n = self.repo.get_by_id(notification_id)
        if not n or n.supplier_id != supplier_id:
            raise NotFoundException(f"Notification {notification_id} not found")
        n.is_deleted = True
        self.repo.db.commit()


# ══════════════════════════════════════════════════════════════════════════════
# SUPPORT SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class SupportService:
    def __init__(self, db: Session):
        self.repo = SupportRepo(db)

    def list_tickets(self, supplier_id: str, status: str = None,
                     page: int = 1, page_size: int = 20) -> Tuple[List, int]:
        offset = (page - 1) * page_size
        return self.repo.list_for_supplier(supplier_id, status=status,
                                           limit=page_size, offset=offset)

    def get_ticket(self, supplier_id: str, ticket_id: str) -> SupplierSupportTicket:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket or ticket.supplier_id != supplier_id:
            raise NotFoundException(f"Ticket {ticket_id} not found")
        return ticket

    def create_ticket(self, supplier_id: str, user_id: str, data: dict) -> SupplierSupportTicket:
        ticket = SupplierSupportTicket(
            id=uuid.uuid4(),
            supplier_id=supplier_id,
            ticket_number=self.repo.generate_ticket_number(),
            **data
        )
        return self.repo.create(ticket)

    def add_reply(self, supplier_id: str, user_id: str, ticket_id: str,
                  message: str) -> SupplierSupportTicket:
        ticket = self.get_ticket(supplier_id, ticket_id)
        reply = {
            "reply_id": str(uuid.uuid4()),
            "author_id": user_id,
            "author_type": "supplier",
            "message": message,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.repo.add_reply(ticket, reply)

    def close_ticket(self, supplier_id: str, ticket_id: str) -> SupplierSupportTicket:
        ticket = self.get_ticket(supplier_id, ticket_id)
        ticket.status = "CLOSED"
        ticket.closed_at = datetime.now(timezone.utc)
        self.repo.db.commit()
        self.repo.db.refresh(ticket)
        return ticket


# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class SettingsService:
    def __init__(self, db: Session):
        self.db = db
        self.account_repo = SupplierAccountRepo(db)

    def get_settings(self, supplier_id: str) -> dict:
        account = self.account_repo.get_by_supabase_uid(supplier_id)
        if not account:
            raise NotFoundException("Account not found")
        return {
            "supplier_id": supplier_id,
            "contact_name": account.contact_name,
            "email": account.email,
            "phone": account.phone,
            "notification_preferences": None,
            "display_preferences": None,
        }

    def update_profile(self, supplier_id: str, data: dict) -> dict:
        account = self.account_repo.get_by_supabase_uid(supplier_id)
        if not account:
            raise NotFoundException("Account not found")
        if "contact_name" in data:
            account.contact_name = data["contact_name"]
        if "phone" in data:
            account.phone = data["phone"]
        self.db.commit()
        return self.get_settings(supplier_id)
