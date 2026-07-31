"""
Package init for Phase 10 normalized SQLAlchemy models.

Imports all 8 new normalized models so that Alembic autogenerate
and app.db.base can pick them up in a single import.
"""
from app.db.models.normalized.supplier_category import SupplierCategory
from app.db.models.normalized.supplier_factory_location import SupplierFactoryLocation
from app.db.models.normalized.supplier_warehouse_location import SupplierWarehouseLocation
from app.db.models.normalized.supplier_contact import SupplierContact
from app.db.models.normalized.supplier_certification import SupplierCertification
from app.db.models.normalized.supplier_document import SupplierDocument
from app.db.models.normalized.supplier_product import SupplierProduct
from app.db.models.normalized.inventory_transaction import SupplierInventoryTransaction
from app.db.models.normalized.shipment_event import SupplierShipmentEvent
from app.db.models.normalized.incident_attachment import SupplierIncidentAttachment
from app.db.models.normalized.forecast_accuracy import SupplierForecastAccuracy
from app.db.models.normalized.score_explanation import SupplierScoreExplanation
from app.db.models.normalized.api_log import ApiLog
from app.db.models.normalized.orchestrator_event import OrchestratorEvent
from app.db.models.normalized.dashboard_kpi_cache import DashboardKpiCache

__all__ = [
    "SupplierCategory",
    "SupplierFactoryLocation",
    "SupplierWarehouseLocation",
    "SupplierContact",
    "SupplierCertification",
    "SupplierDocument",
    "SupplierProduct",
    "SupplierInventoryTransaction",
    "SupplierShipmentEvent",
    "SupplierIncidentAttachment",
    "SupplierForecastAccuracy",
    "SupplierScoreExplanation",
    "ApiLog",
    "OrchestratorEvent",
    "DashboardKpiCache",
]
