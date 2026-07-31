"""
supplier_portal/models/__init__.py
Exports all ORM models so Alembic can auto-detect them.
"""
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

# ── Module C ──────────────────────────────────────────────────────────────────
from app.supplier_portal.models.setup_status import SupplierSetupStatus
from app.supplier_portal.models.quality_record import SupplierQualityRecord, SupplierQualityHistory
from app.supplier_portal.models.document_center import SupplierDocumentRecord, SupplierDocumentAudit

__all__ = [
    "SupplierAccount",
    "SupplierCompanyProfile",
    "SupplierProductionCapacity",
    "SupplierInventoryItem",
    "SupplierLeadTime",
    "SupplierShipment",
    "SupplierIncident",
    "SupplierCapacityForecast",
    "SupplierNotification",
    "SupplierSupportTicket",
    "SupplierAuditLog",
    # Module C
    "SupplierSetupStatus",
    "SupplierQualityRecord",
    "SupplierQualityHistory",
    "SupplierDocumentRecord",
    "SupplierDocumentAudit",
]
