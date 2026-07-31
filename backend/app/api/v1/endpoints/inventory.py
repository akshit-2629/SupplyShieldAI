"""
Inventory Impact REST API — Phase 7

10 endpoints:

  GET  /inventory/                     — All component projections (latest run)
  GET  /inventory/fleet                — Fleet inventory health + financial impact summary
  GET  /inventory/alerts               — CRITICAL + HIGH stockout alerts
  GET  /inventory/{component_id}       — Single component full projection
  GET  /inventory/{component_id}/timeline   — Depletion timeline (base + risk scenario)
  GET  /inventory/risk/{risk_level}    — Components filtered by stockout risk level
  GET  /inventory/supplier/{supplier_id}  — All components from a supplier
  GET  /inventory/product/{product_name}  — Components used in a specific product
  GET  /inventory/stats                — Quick fleet statistics
  POST /inventory/rebuild              — Force re-run the full inventory pipeline
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db

logger = logging.getLogger("api.inventory")

router = APIRouter(prefix="/inventory", tags=["Inventory Impact"])


# ─────────────────────────────────────────────────────────────────────────────
# In-memory result store
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime, timezone
from app.core.security import get_current_user, UserPrincipal
from app.manufacturer.models import ManufacturerComponent
from app.inventory.pipeline import InventoryPipeline, InventoryPipelineResult

# Tenant-scoped result resolver (PostgreSQL single source of truth)
def _get_result(user_id: str, db: Session) -> InventoryPipelineResult:
    components = db.query(ManufacturerComponent).filter_by(company_user_id=user_id).all()
    
    if not components:
        eval_time = datetime.now(timezone.utc).isoformat()
        return InventoryPipelineResult(
            projections=[],
            fleet_forecast={
                "fleet_inventory_health": 0.0,
                "fleet_health_label": "NO_DATA",
                "critical_at_risk_count": 0,
                "high_at_risk_count": 0,
                "total_revenue_at_risk": 0.0,
                "total_financial_impact": 0.0,
            },
            alerts=[],
            summary={
                "total_items": 0,
                "fleet_inventory_health": 0.0,
                "fleet_health_label": "NO_DATA",
                "critical_count": 0,
                "high_risk_count": 0,
                "total_revenue_at_risk": 0.0,
                "total_financial_impact": 0.0,
                "alert_count": 0,
                "execution_id": "tenant_live",
                "evaluated_at": eval_time,
            },
            execution_id="tenant_live",
            evaluated_at=eval_time,
            total_items=0,
        )

    items_data = [
        {
            "component_id": str(c.id),
            "component_name": c.component_name,
            "supplier_id": c.preferred_supplier or "supplier::UNKNOWN",
            "supplier_name": c.preferred_supplier or "Unknown Supplier",
            "unit": c.unit or "units",
            "current_stock": float(c.safety_stock) if c.safety_stock is not None else 1000.0,
            "daily_consumption": (float(c.avg_monthly_usage) / 30.0) if c.avg_monthly_usage else 10.0,
            "monthly_demand": float(c.avg_monthly_usage) if c.avg_monthly_usage else 300.0,
            "lead_time_days": 30,
            "unit_cost": 100.0,
            "revenue_per_unit": 200.0,
        }
        for c in components
    ]

    pipeline = InventoryPipeline()
    return pipeline.run(items_data=items_data, execution_id=f"tenant_{user_id[:8]}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. GET /inventory/ — All projections
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", summary="All inventory component projections (latest run)")
def list_projections(
    risk:         Optional[str]   = Query(default=None, description="Filter: CRITICAL, HIGH, MEDIUM, LOW, SAFE"),
    min_days:     Optional[float] = Query(default=None, ge=0, description="Minimum days remaining"),
    max_days:     Optional[float] = Query(default=None, ge=0, description="Maximum days remaining"),
    limit:        int             = Query(default=50, ge=1, le=200),
    current_user: UserPrincipal   = Depends(get_current_user),
    db:           Session         = Depends(get_db),
) -> Dict[str, Any]:
    res  = _get_result(current_user.user_id, db)
    proj = res.projections

    if risk:
        proj = [p for p in proj if p.stockout.stockout_risk.value == risk.upper()]
    if min_days is not None:
        proj = [p for p in proj if p.stockout.days_remaining >= min_days]
    if max_days is not None:
        proj = [p for p in proj if p.stockout.days_remaining <= max_days]

    # Sort by days_remaining ascending (most urgent first)
    proj = sorted(proj, key=lambda p: p.stockout.days_remaining)

    return {
        "total":        len(proj),
        "evaluated_at": res.evaluated_at,
        "projections":  [p.to_dict() for p in proj[:limit]],
        "components":   [p.to_dict() for p in proj[:limit]],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. GET /inventory/fleet — Fleet summary
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/fleet", summary="Fleet Inventory Health + financial impact summary")
def get_fleet(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    return {
        "summary":        res.summary,
        "fleet_forecast": res.fleet_forecast,
        "evaluated_at":   res.evaluated_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. GET /inventory/alerts — Stockout alerts
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/alerts", summary="CRITICAL + HIGH stockout alerts requiring immediate action")
def get_alerts(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    return {
        "alert_count":  len(res.alerts),
        "alerts":       res.alerts,
        "evaluated_at": res.evaluated_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. GET /inventory/stats — Quick statistics
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/stats", summary="Quick fleet statistics")
def get_stats(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    return {
        "summary":           res.summary,
        "risk_distribution": res.fleet_forecast.get("risk_distribution", {}),
        "products_at_risk":  res.fleet_forecast.get("products_at_risk", {}),
        "evaluated_at":      res.evaluated_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. GET /inventory/risk/{risk_level} — By stockout risk
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/risk/{risk_level}", summary="Components filtered by stockout risk level")
def get_by_risk(
    risk_level:   str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res   = _get_result(current_user.user_id, db)
    valid = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "SAFE"}
    rl    = risk_level.upper()
    if rl not in valid:
        raise HTTPException(status_code=400, detail=f"risk_level must be one of {valid}")

    proj = [p for p in res.projections if p.stockout.stockout_risk.value == rl]
    return {
        "risk_level":  rl,
        "count":       len(proj),
        "projections": [p.to_dict() for p in sorted(proj, key=lambda p: p.stockout.days_remaining)],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. GET /inventory/supplier/{supplier_id} — By supplier
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/supplier/{supplier_id}", summary="All components supplied by a specific supplier")
def get_by_supplier(
    supplier_id:  str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res  = _get_result(current_user.user_id, db)
    proj = [p for p in res.projections if p.item.supplier_id == supplier_id]
    if not proj:
        # partial match
        sid = supplier_id.lower()
        proj = [p for p in res.projections if sid in p.item.supplier_id.lower() or sid in p.item.supplier_name.lower()]
    return {
        "supplier_id":  supplier_id,
        "count":        len(proj),
        "projections":  [p.to_dict() for p in proj],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 7. GET /inventory/product/{product_name} — By product
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/product/{product_name}", summary="Components used in a specific product")
def get_by_product(
    product_name: str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res   = _get_result(current_user.user_id, db)
    pname = product_name.lower()
    proj  = [
        p for p in res.projections
        if any(pname in prod.lower() for prod in p.item.used_in_products)
    ]

    total_revenue_at_risk = sum(p.revenue.revenue_lost_usd for p in proj)

    return {
        "product_name":        product_name,
        "component_count":     len(proj),
        "total_revenue_at_risk": round(total_revenue_at_risk, 2),
        "projections":         [p.to_dict() for p in sorted(proj, key=lambda p: p.stockout.days_remaining)],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 8. GET /inventory/{component_id}/timeline — Depletion timeline
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{component_id}/timeline", summary="Inventory depletion timeline (base + risk scenario)")
def get_timeline(
    component_id: str,
    horizon:      int = Query(default=120, ge=7, le=365),
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res  = _get_result(current_user.user_id, db)
    proj = next((p for p in res.projections if p.item.component_id == component_id), None)
    if not proj:
        cid = component_id.lower()
        proj = next(
            (p for p in res.projections if cid in p.item.component_id.lower() or cid in p.item.component_name.lower()),
            None,
        )
    if not proj:
        raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found")

    from app.inventory.forecaster import InventoryForecaster

    risk_score = proj.item.metadata.get("risk_overlay", {}).get("component_risk_score", 0.0)
    timeline   = InventoryForecaster().timeline(proj.item, risk_score=risk_score, horizon=horizon)
    return timeline


# ─────────────────────────────────────────────────────────────────────────────
# 9. GET /inventory/{component_id} — Single component
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{component_id}", summary="Full projection for a single component")
def get_component(
    component_id: str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res  = _get_result(current_user.user_id, db)
    proj = next((p for p in res.projections if p.item.component_id == component_id), None)
    if not proj:
        cid = component_id.lower()
        proj = next(
            (p for p in res.projections if cid in p.item.component_id.lower() or cid in p.item.component_name.lower()),
            None,
        )
    if not proj:
        raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found")
    return proj.to_dict()


# ─────────────────────────────────────────────────────────────────────────────
# 10. POST /inventory/rebuild — Force re-run
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/rebuild", summary="Force re-run the full inventory pipeline")
async def rebuild_inventory(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    try:
        from app.inventory.pipeline import InventoryPipeline
        from app.db.models.risk_assessment import RiskAssessment
        from app.db.models.supplier_score import SupplierScore

        risk_rows = (
            db.query(RiskAssessment)
              .order_by(RiskAssessment.assessed_at.desc())
              .limit(200).all()
        )
        risk_data = [
            {
                "assessment_id": r.assessment_id,
                "risk_score":    r.risk_score,
                "risk_level":    r.risk_level,
                "countries":     r.countries or [],
                "industries":    r.industries or [],
                "geo_risk":      r.geo_risk or {},
                "industry_risk": r.industry_risk or {},
            }
            for r in risk_rows
        ]

        supplier_rows = (
            db.query(SupplierScore)
              .order_by(SupplierScore.evaluated_at.desc())
              .limit(50).all()
        )
        supplier_data = [
            {
                "supplier_id": s.supplier_id,
                "tier":        s.tier,
                "risk_score":  s.risk_score,
                "risk_level":  s.risk_level,
                "health":      {"health_score": s.health_score},
            }
            for s in supplier_rows
        ]

        pipeline = InventoryPipeline()
        result   = pipeline.run(
            risk_assessments = risk_data,
            supplier_scores  = supplier_data,
            execution_id     = f"manual_rebuild_{current_user.user_id[:8]}",
        )

        return {
            "success":                True,
            "total_items":            result.total_items,
            "fleet_inventory_health": result.summary.get("fleet_inventory_health", 0),
            "critical_count":         result.summary.get("critical_count", 0),
            "high_risk_count":        result.summary.get("high_risk_count", 0),
            "total_revenue_at_risk":  result.summary.get("total_revenue_at_risk", 0),
            "alert_count":            result.summary.get("alert_count", 0),
            "risk_data_used":         len(risk_data),
            "supplier_data_used":     len(supplier_data),
        }
    except Exception as e:
        logger.exception("rebuild_inventory failed")
        raise HTTPException(status_code=500, detail=str(e))

