from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, google_auth
from app.api.v1.endpoints import orchestrator as orchestrator_router
from app.api.v1.endpoints import news as news_router
from app.api.v1.endpoints import risk as risk_router
from app.api.v1.endpoints import graph as graph_router
from app.api.v1.endpoints import supplier as supplier_router
from app.api.v1.endpoints import inventory as inventory_router
from app.api.v1.endpoints import recommendation as recommendation_router
from app.api.v1.endpoints import dashboard as dashboard_router

api_router = APIRouter()

# Dashboard endpoints
api_router.include_router(dashboard_router.router, prefix="/dashboard", tags=["Dashboard"])

# Health monitoring endpoints
api_router.include_router(health.router)

# Supabase JWT authentication endpoints
api_router.include_router(auth.router)

# Google OAuth 2.0 endpoints
api_router.include_router(google_auth.router)

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
