from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, google_auth, security_placeholder
from app.api.v1.endpoints import orchestrator as orchestrator_router
from app.api.v1.endpoints import news as news_router
from app.api.v1.endpoints import risk as risk_router
from app.api.v1.endpoints import graph as graph_router
from app.api.v1.endpoints import supplier as supplier_router
from app.api.v1.endpoints import inventory as inventory_router
from app.api.v1.endpoints import recommendation as recommendation_router
from app.api.v1.endpoints import dashboard as dashboard_router
from app.api.v1.endpoints import reports as reports_router
from app.api.v1.endpoints import incidents_api as enterprise_incidents_router

api_router = APIRouter()

# Enterprise Incidents endpoint
api_router.include_router(enterprise_incidents_router.router, prefix="/incidents", tags=["Enterprise Incidents"])

# Dashboard endpoints
api_router.include_router(dashboard_router.router, prefix="/dashboard", tags=["Dashboard"])

# Health monitoring endpoints
api_router.include_router(health.router)

# Supabase JWT authentication endpoints
api_router.include_router(auth.router)

# Google OAuth 2.0 endpoints
api_router.include_router(google_auth.router)

# Security — JWT and RBAC validation endpoints
api_router.include_router(security_placeholder.router)

# Phase 2: Master Orchestrator endpoints
api_router.include_router(orchestrator_router.router)

# Phase 3: News Intelligence endpoints
api_router.include_router(news_router.router)

# Phase 4: Risk Assessment endpoints
api_router.include_router(risk_router.router)

# Phase 5: Knowledge Graph endpoints
api_router.include_router(graph_router.router)

# Phase 6: Supplier Intelligence endpoints
api_router.include_router(supplier_router.router)

# Phase 7: Inventory Impact endpoints
api_router.include_router(inventory_router.router)

# Phase 8: Recommendation endpoints
api_router.include_router(recommendation_router.router)

# Phase D: Reports endpoints
api_router.include_router(reports_router.router)

# ── Phase 9: Supplier Portal ───────────────────────────────────────────────────
from app.supplier_portal.routers import (
    auth_router as sp_auth_router,
    admin_router as sp_admin_router,
    profile_router,
    production_router,
    inventory_router as sp_inventory_router,
    lead_time_router,
    shipment_router,
    incident_router,
    forecast_router,
    performance_router,
    notification_router,
    support_router,
    settings_router,
)

_SP_PREFIX = "/supplier-portal"

# Auth — no require_supplier guard (registration is public, login returns JWT from Supabase)
api_router.include_router(sp_auth_router, prefix=_SP_PREFIX)

# Admin approval endpoints (require_admin guard inside router)
api_router.include_router(sp_admin_router)

# Supplier-only module endpoints (require_supplier guard inside each router)
api_router.include_router(profile_router,       prefix=_SP_PREFIX)
api_router.include_router(production_router,    prefix=_SP_PREFIX)
api_router.include_router(sp_inventory_router,  prefix=_SP_PREFIX)
api_router.include_router(lead_time_router,     prefix=_SP_PREFIX)
api_router.include_router(shipment_router,      prefix=_SP_PREFIX)
api_router.include_router(incident_router,      prefix=_SP_PREFIX)
api_router.include_router(forecast_router,      prefix=_SP_PREFIX)
api_router.include_router(performance_router,   prefix=_SP_PREFIX)
api_router.include_router(notification_router,  prefix=_SP_PREFIX)
api_router.include_router(support_router,       prefix=_SP_PREFIX)
api_router.include_router(settings_router,      prefix=_SP_PREFIX)

# ── Module C: Setup Status, Quality Management, Document Center ───────────────
from app.supplier_portal.routers.module_c_routers import (  # noqa: E402
    setup_router, quality_router, documents_router,
)
api_router.include_router(setup_router,     prefix=_SP_PREFIX)
api_router.include_router(quality_router,   prefix=_SP_PREFIX)
api_router.include_router(documents_router, prefix=_SP_PREFIX)

# ── Manufacturer Onboarding (Setup Wizard) ───────────────────────────────────
from app.manufacturer.router import router as manufacturer_router  # noqa: E402
api_router.include_router(manufacturer_router)

# ── Module B: Supplier Lifecycle Management ───────────────────────────────────
from app.supplier_management.router import (       # noqa: E402
    router as slm_router,
    public_router as slm_public_router,
)
api_router.include_router(slm_router)              # /api/v1/supplier-management/...\
api_router.include_router(slm_public_router)       # /api/v1/supplier-invitations/... (no auth)
