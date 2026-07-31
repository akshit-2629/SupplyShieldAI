"""
Supplier Intelligence REST API — Phase 6

12 endpoints:

  GET  /suppliers/                  — Ranked supplier list (latest run)
  GET  /suppliers/fleet             — Fleet aggregation stats + FHI
  GET  /suppliers/{supplier_id}     — Single supplier full profile
  GET  /suppliers/{supplier_id}/history  — MoM score history
  GET  /suppliers/tier/{tier}       — All suppliers in a tier (TIER_1/2/3)
  GET  /suppliers/alerts            — Critical alerts list
  GET  /suppliers/leaderboard       — Top N suppliers by health score
  GET  /suppliers/country/{code}    — Suppliers in a country
  POST /suppliers/score             — Score a single supplier (on-demand)
  GET  /suppliers/ranking           — Compact rank table
  GET  /suppliers/stats             — Quick fleet statistics summary
  POST /suppliers/rebuild           — Force re-run the full supplier pipeline
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db

logger = logging.getLogger("api.supplier")

router = APIRouter(prefix="/suppliers", tags=["Supplier Intelligence"])


from datetime import datetime, timezone
from app.core.security import get_current_user, UserPrincipal
from app.supplier_management.management_service import SupplierManagementService
from app.supplier.pipeline import SupplierPipeline, SupplierPipelineResult

def _get_result(user_id: str, db: Session) -> SupplierPipelineResult:
    svc = SupplierManagementService(db)
    rows, _ = svc.list_suppliers(user_id, status_filter="APPROVED", page_size=500)

    
    if not rows:
        eval_time = datetime.now(timezone.utc).isoformat()
        return SupplierPipelineResult(
            profiles=[],
            ranked=[],
            aggregation={
                "total_suppliers": 0,
                "fleet_health_index": 0.0,
                "fleet_health_label": "NO_DATA",
                "alert_count": 0,
                "critical_alerts": [],
                "tier_distribution": {
                    "TIER_1": {"count": 0, "pct": 0.0},
                    "TIER_2": {"count": 0, "pct": 0.0},
                    "TIER_3": {"count": 0, "pct": 0.0},
                },
            },
            summary={
                "total_scored": 0,
                "fleet_health_index": 0.0,
                "fleet_health_label": "NO_DATA",
                "tier_1_count": 0,
                "tier_2_count": 0,
                "tier_3_count": 0,
                "critical_alerts": 0,
                "top_supplier": "N/A",
                "top_supplier_score": 0.0,
                "execution_id": "tenant_live",
                "evaluated_at": eval_time,
            },
            execution_id="tenant_live",
            evaluated_at=eval_time,
            total_scored=0,
        )

    pipeline = SupplierPipeline()
    return pipeline.run(suppliers_data=rows, execution_id=f"tenant_{user_id[:8]}")


# ─────────────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────────────

class OnDemandScoreRequest(BaseModel):
    supplier_id:          str
    name:                 str
    country_code:         str   = "US"
    revenue_exposure_pct: float = 5.0
    reliability_score:    float = 75.0
    quality_score:        float = 75.0
    lead_time_score:      float = 75.0
    cost_efficiency:      float = 75.0
    compliance_score:     float = 75.0
    responsiveness:       float = 75.0
    flexibility:          float = 75.0
    risk_score:           float = 0.0
    dependency_score:     float = 0.0


class RebuildRequest(BaseModel):
    force: bool = True


# ─────────────────────────────────────────────────────────────────────────────
# Helper — store updater (called by SupplierAgent after each run)
# ─────────────────────────────────────────────────────────────────────────────

def update_latest_result(result: Any) -> None:
    global _latest_result
    _latest_result = result


# ─────────────────────────────────────────────────────────────────────────────
# 1. GET /suppliers/ — Ranked supplier list
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", summary="Ranked supplier list (latest evaluation)")
def list_suppliers(
    tier:         Optional[str]   = Query(default=None, description="Filter: TIER_1, TIER_2, TIER_3"),
    min_health:   Optional[float] = Query(default=None, ge=0, le=100),
    limit:        int             = Query(default=50, ge=1, le=200),
    current_user: UserPrincipal   = Depends(get_current_user),
    db:           Session         = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    profiles = res.ranked

    if tier:
        profiles = [p for p in profiles if p.tier.value == tier.upper()]
    if min_health is not None:
        profiles = [p for p in profiles if p.health.health_score >= min_health]

    return {
        "total":        len(profiles),
        "evaluated_at": res.evaluated_at,
        "suppliers":    [p.to_dict() for p in profiles[:limit]],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. GET /suppliers/fleet — Fleet aggregation + FHI
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/fleet", summary="Fleet Health Index + aggregated statistics")
def get_fleet_stats(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    return {
        "summary":      res.summary,
        "aggregation":  res.aggregation,
        "evaluated_at": res.evaluated_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. GET /suppliers/alerts — Critical alerts
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/alerts", summary="Critical supplier alerts requiring immediate attention")
def get_alerts(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    alerts = res.aggregation.get("critical_alerts", [])
    return {
        "alert_count":  len(alerts),
        "alerts":       alerts,
        "evaluated_at": res.evaluated_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. GET /suppliers/leaderboard — Top N by health score
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/leaderboard", summary="Top N suppliers by health score")
def get_leaderboard(
    top_n:        int           = Query(default=10, ge=1, le=50),
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    top = sorted(res.profiles, key=lambda p: p.health.health_score, reverse=True)[:top_n]
    return {
        "top_n":    top_n,
        "leaders":  [
            {
                "rank":         p.rank,
                "name":         p.name,
                "supplier_id":  p.supplier_id,
                "tier":         p.tier.value,
                "health_score": p.health.health_score,
                "health_label": p.health.health_label,
                "country_code": p.country_code,
                "trend":        p.trend.value,
                "mom_change":   p.mom_change,
            }
            for p in top
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. GET /suppliers/ranking — Compact rank table
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/ranking", summary="Compact ranked supplier table")
def get_ranking(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    from app.supplier.ranker import SupplierRanker
    return SupplierRanker().get_rank_summary(res.ranked)


# ─────────────────────────────────────────────────────────────────────────────
# 6. GET /suppliers/stats — Quick statistics
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/stats", summary="Quick fleet statistics summary")
def get_stats(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    return {
        "summary":             res.summary,
        "avg_scores":          res.aggregation.get("avg_scores", {}),
        "health_distribution": res.aggregation.get("health_distribution", {}),
        "tier_distribution":   res.aggregation.get("tier_distribution", {}),
        "risk_concentration":  res.aggregation.get("risk_concentration", {}),
        "evaluated_at":        res.evaluated_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 7. GET /suppliers/tier/{tier} — Suppliers in a tier
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/tier/{tier}", summary="All suppliers in a specific tier")
def get_by_tier(
    tier:         str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    tier_upper = tier.upper()
    valid = {"TIER_1", "TIER_2", "TIER_3"}
    if tier_upper not in valid:
        raise HTTPException(status_code=400, detail=f"tier must be one of {valid}")

    profiles = [p for p in res.ranked if p.tier.value == tier_upper]
    return {
        "tier":      tier_upper,
        "count":     len(profiles),
        "suppliers": [p.to_dict() for p in profiles],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 8. GET /suppliers/country/{code} — Suppliers in a country
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/country/{code}", summary="Suppliers in a specific country (ISO-2)")
def get_by_country(
    code:         str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    cc  = code.upper()
    profiles = [p for p in res.ranked if p.country_code.upper() == cc]
    return {
        "country_code": cc,
        "count":        len(profiles),
        "suppliers":    [p.to_dict() for p in profiles],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 9. GET /suppliers/{supplier_id} — Single supplier full profile
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{supplier_id}", summary="Full profile for a single supplier")
def get_supplier(
    supplier_id:  str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    profile = next(
        (p for p in res.profiles if p.supplier_id == supplier_id),
        None,
    )
    if not profile:
        # Try case-insensitive / partial match
        sid_lower = supplier_id.lower()
        profile = next(
            (p for p in res.profiles if sid_lower in p.supplier_id.lower() or sid_lower in p.name.lower()),
            None,
        )
    if not profile:
        raise HTTPException(status_code=404, detail=f"Supplier '{supplier_id}' not found")

    full = profile.to_dict()
    full["history"] = from_tracker(profile.supplier_id)
    return full


# ─────────────────────────────────────────────────────────────────────────────
# 10. GET /suppliers/{supplier_id}/history — MoM history
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{supplier_id}/history", summary="Month-over-month score history for a supplier")
def get_history(
    supplier_id: str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    from app.supplier.history import historical_tracker
    history = historical_tracker.get_history(supplier_id)
    trend   = historical_tracker.get_trend_summary(supplier_id)
    return {
        "supplier_id": supplier_id,
        "trend_summary": trend,
        "history":     history,
        "count":       len(history),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 11. POST /suppliers/score — On-demand single supplier scoring
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/score", summary="Score a single supplier on-demand")
def score_supplier(
    req: OnDemandScoreRequest,
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.supplier.models import KPIScore
    from app.supplier.scorer import WeightedKPIScorer

    kpi = KPIScore(
        reliability_score = req.reliability_score,
        quality_score     = req.quality_score,
        lead_time_score   = req.lead_time_score,
        cost_efficiency   = req.cost_efficiency,
        compliance_score  = req.compliance_score,
        responsiveness    = req.responsiveness,
        flexibility       = req.flexibility,
    )
    scorer = WeightedKPIScorer()
    health = scorer.score_health(
        kpi              = kpi,
        risk_score       = req.risk_score,
        dependency_score = req.dependency_score,
    )
    return {
        "supplier_id":   req.supplier_id,
        "name":          req.name,
        "country_code":  req.country_code,
        "kpi":           kpi.to_dict(),
        "health":        health.to_dict(),
        "reliability":   scorer.score_reliability(kpi),
        "performance":   scorer.score_performance(kpi),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 12. POST /suppliers/rebuild — Force re-run pipeline
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/rebuild", summary="Force re-run the full supplier intelligence pipeline")
async def rebuild_suppliers(
    req: RebuildRequest,
    current_user: UserPrincipal = Depends(get_current_user),
    db:  Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        from app.supplier.pipeline import SupplierPipeline
        from app.db.models.risk_assessment import RiskAssessment

        rows = (
            db.query(RiskAssessment)
              .order_by(RiskAssessment.assessed_at.desc())
              .limit(200)
              .all()
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
            for r in rows
        ]

        pipeline = SupplierPipeline()
        result   = pipeline.run(
            risk_assessments = risk_data,
            execution_id     = f"manual_rebuild_{current_user.user_id[:8]}",
        )

        return {
            "success":             True,
            "total_scored":        result.total_scored,
            "fleet_health_index":  result.summary.get("fleet_health_index", 0),
            "tier_1_count":        result.summary.get("tier_1_count", 0),
            "tier_2_count":        result.summary.get("tier_2_count", 0),
            "tier_3_count":        result.summary.get("tier_3_count", 0),
            "critical_alerts":     result.summary.get("critical_alerts", 0),
            "risk_data_used":      len(risk_data),
        }
    except Exception as e:
        logger.exception("rebuild_suppliers failed")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def from_tracker(supplier_id: str) -> List[Dict[str, Any]]:
    from app.supplier.history import historical_tracker
    return historical_tracker.get_history(supplier_id)
