"""
app/db/base.py — Master model registry for Alembic autogenerate.

This file must import every SQLAlchemy model so that:
  1. Alembic `autogenerate` detects all tables
  2. `Base.metadata` is fully populated before `create_all()` is called

Import order: Base first → core models → supplier portal models → normalized models
"""

# ── Base (must come first) ────────────────────────────────────────────────────
from app.db.models.base import Base  # noqa: F401

# ── Phase 1–3: Core orchestration & news intelligence ─────────────────────────
from app.db.models.workflow_run import WorkflowRun          # noqa: F401
from app.db.models.agent_execution import AgentExecution    # noqa: F401
from app.db.models.agent_health import AgentHealthRecord      # noqa: F401
from app.db.models.disruption import DisruptionEvent        # noqa: F401
from app.db.models.news_article import NewsArticle          # noqa: F401

# ── Phase 4: Risk Assessment ───────────────────────────────────────────────────
from app.db.models.risk_assessment import RiskAssessment    # noqa: F401
from app.db.models.enterprise_incident import EnterpriseIncident # noqa: F401

# ── Phase 5: Knowledge Graph ───────────────────────────────────────────────────
from app.db.models.graph_snapshot import GraphSnapshot      # noqa: F401

# ── Phase 6: Supplier Intelligence ────────────────────────────────────────────
from app.db.models.supplier_score import SupplierScore      # noqa: F401

# ── Phase 7: Inventory Impact ─────────────────────────────────────────────────
from app.db.models.inventory_projection import InventoryProjectionRow  # noqa: F401

# ── Phase 8: Recommendation Engine ────────────────────────────────────────────
from app.db.models.recommendation import RecommendationRow  # noqa: F401

# ── Phase 9: Supplier Portal (11 models) ──────────────────────────────────────
from app.supplier_portal.models import (                    # noqa: F401
    SupplierAccount,
    SupplierCompanyProfile,
    SupplierProductionCapacity,
    SupplierInventoryItem,
    SupplierLeadTime,
    SupplierShipment,
    SupplierIncident,
    SupplierCapacityForecast,
    SupplierNotification,
    SupplierSupportTicket,
    SupplierAuditLog,
    # Module C additions
    SupplierSetupStatus,
    SupplierQualityRecord,
    SupplierQualityHistory,
    SupplierDocumentRecord,
    SupplierDocumentAudit,
)

# ── Phase 10: Normalized Extension (15 models) ────────────────────────────────
from app.db.models.normalized import (                      # noqa: F401
    SupplierCategory,
    SupplierFactoryLocation,
    SupplierWarehouseLocation,
    SupplierContact,
    SupplierCertification,
    SupplierDocument,
    SupplierProduct,
    SupplierInventoryTransaction,
    SupplierShipmentEvent,
    SupplierIncidentAttachment,
    SupplierForecastAccuracy,
    SupplierScoreExplanation,
    ApiLog,
    OrchestratorEvent,
    DashboardKpiCache,
)

# ── Manufacturer Onboarding (Setup Wizard) ───────────────────────────────────
from app.manufacturer.models import (                    # noqa: F401
    ManufacturerCompany,
    ManufacturerFactory,
    ManufacturerWarehouse,
    ManufacturerProduct,
    ManufacturerComponent,
)

# ── Module B: Supplier Lifecycle Management ───────────────────────────────────
from app.supplier_management.models import (             # noqa: F401
    SupplierInvitation,
    ManufacturerSupplierNote,
    SupplierLifecycleAudit,
)

__all__ = ["Base"]
