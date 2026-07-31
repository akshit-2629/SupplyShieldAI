"""supplier_portal/routers/__init__.py — exports the master router assembly"""
from app.supplier_portal.routers.auth_router import router as auth_router
from app.supplier_portal.routers.admin_router import router as admin_router
from app.supplier_portal.routers.module_routers import (
    profile_router,
    production_router,
    inventory_router,
    lead_time_router,
    shipment_router,
    incident_router,
    forecast_router,
    performance_router,
    notification_router,
    support_router,
    settings_router,
)
