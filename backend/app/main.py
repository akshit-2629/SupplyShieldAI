import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import setup_logging, RequestLoggingMiddleware
from app.core.exceptions import register_exception_handlers
from app.api.v1.api import api_router

# Initialize application-wide logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("app.main")


# ── FastAPI Lifespan (startup + shutdown) ─────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup:
      - Initialize MasterOrchestrator singleton
      - Register all agents
      - Compile LangGraph DAG
      - Validate workflow DAG (Kahn's algorithm)

    Shutdown:
      - Clean up orchestrator memory
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    # Phase 2: Master Orchestrator
    try:
        from app.orchestrator.orchestrator import MasterOrchestrator
        orchestrator = MasterOrchestrator.get_instance()
        await orchestrator.initialize()
        logger.info("[startup] MasterOrchestrator initialized ✓")
    except Exception as exc:
        logger.error(f"[startup] MasterOrchestrator initialization failed: {exc}")
        # Non-fatal: server still starts; orchestrator endpoints will return 503

    # Phase 3: News Scheduler
    try:
        if settings.NEWS_SCHEDULER_AUTO_START:
            from app.news.scheduler import news_scheduler
            news_scheduler.start()
            logger.info("[startup] News scheduler started ✓")
        else:
            logger.info("[startup] News scheduler auto-start disabled (NEWS_SCHEDULER_AUTO_START=False)")
    except Exception as exc:
        logger.error(f"[startup] News scheduler failed to start: {exc}")
        # Non-fatal: pipeline can still be triggered manually via REST API

    # Phase 4: Server startup complete
    logger.info("[startup] Server initialization complete. Multi-tenant database mode active.")

    try:
        yield
    finally:
        logger.info("[shutdown] Server shutdown complete.")

    # ── Shutdown ──────────────────────────────────────────────────────────────
    # Phase 3: Stop news scheduler first
    try:
        from app.news.scheduler import news_scheduler
        news_scheduler.stop()
        logger.info("[shutdown] News scheduler stopped ✓")
    except Exception as exc:
        logger.warning(f"[shutdown] News scheduler stop error (non-fatal): {exc}")

    # Phase 2: Orchestrator cleanup
    try:
        from app.orchestrator.orchestrator import MasterOrchestrator
        orchestrator = MasterOrchestrator.get_instance()
        await orchestrator.shutdown()
        logger.info("[shutdown] MasterOrchestrator shut down cleanly ✓")
    except Exception as exc:
        logger.warning(f"[shutdown] Orchestrator shutdown error (non-fatal): {exc}")


# ── Application factory ───────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs"  if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# ── CORS Policy ───────────────────────────────────────────────────────────────
# allow_origins must be explicit (never "*") when allow_credentials=True —
# browsers reject that combination per the CORS spec.
#
# In production  → only FRONTEND_URL (+ any ADDITIONAL_CORS_ORIGINS) is allowed.
# In development → also accept the standard Vite localhost ports.
#
# ADDITIONAL_CORS_ORIGINS: comma-separated extra origins set in Render dashboard.
# e.g.  https://supply-shield-ai-seven.vercel.app,https://supply-shield-ai.vercel.app
_allowed_origins: list[str] = []

# Primary frontend URL
if settings.FRONTEND_URL:
    _allowed_origins.append(settings.FRONTEND_URL)

# Extra origins from env (handles preview deployments, custom domains, etc.)
import os as _os
_extra = _os.environ.get("ADDITIONAL_CORS_ORIGINS", "")
for _o in _extra.split(","):
    _o = _o.strip()
    if _o and _o not in _allowed_origins:
        _allowed_origins.append(_o)

# Dev: also allow local Vite ports
if settings.ENVIRONMENT != "production":
    for _local in [
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
        "http://localhost:5175", "http://127.0.0.1:5175",
    ]:
        if _local not in _allowed_origins:
            _allowed_origins.append(_local)

logger.info(f"[cors] Allowed origins: {_allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Fallback CORS middleware ───────────────────────────────────────────────────
# Starlette's CORSMiddleware does NOT add headers when the app crashes with
# an unhandled 500 before the route executes, or when Render's proxy returns
# 502/503 during startup. This low-level middleware ensures the header is
# always present so browsers show the real error instead of a generic CORS block.
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse

class FallbackCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        origin = request.headers.get("origin", "")
        response: StarletteResponse = await call_next(request)
        if origin in _allowed_origins:
            response.headers.setdefault("Access-Control-Allow-Origin", origin)
            response.headers.setdefault("Access-Control-Allow-Credentials", "true")
            response.headers.setdefault("Vary", "Origin")
        return response

app.add_middleware(FallbackCORSMiddleware)

# Request performance logger
app.add_middleware(RequestLoggingMiddleware)


# Global exception handlers
register_exception_handlers(app)

# Mount all API routes under /api/v1
app.include_router(api_router, prefix="/api/v1")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Favicon endpoint — prevents browser 404 warnings."""
    from fastapi.responses import Response
    from fastapi import status
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/", tags=["Root"])
@app.head("/", tags=["Root"], include_in_schema=False)
def read_root():
    """Root entrypoint — service identity and docs URL."""
    return {
        "service":  settings.APP_NAME,
        "version":  settings.APP_VERSION,
        "status":   "production-ready",
        "phases":   "Phases 0–9 complete — All 6 AI agents operational",
        "docs_url": "/docs" if settings.ENVIRONMENT != "production" else None,
    }

