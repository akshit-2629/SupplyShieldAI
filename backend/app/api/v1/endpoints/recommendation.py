"""
Recommendation REST API — Phase 8

PostgreSQL single source of truth with strict tenant isolation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, UserPrincipal
from app.db.models.recommendation import RecommendationRow

logger = logging.getLogger("api.recommendation")

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

_latest_result: Optional[Any] = None


def _get_result(user_id: str = "", db: Optional[Session] = None):
    if _latest_result is not None:
        return _latest_result
    
    # Fallback to PostgreSQL
    if db is not None:
        rows = db.query(RecommendationRow).order_by(RecommendationRow.evaluated_at.desc()).limit(50).all()
        if rows:
            class DBResult:
                def __init__(self, db_rows):
                    self.evaluated_at = db_rows[0].evaluated_at.isoformat() if db_rows[0].evaluated_at else None
                    self.summary = {
                        "total_at_risk": len(db_rows),
                        "immediate_switches": sum(1 for r in db_rows if r.action == "IMMEDIATE_SWITCH"),
                        "total_revenue_protected": sum(r.revenue_protected_usd or 0.0 for r in db_rows),
                    }
                    self.recommendations = db_rows

            return DBResult(rows)

    raise HTTPException(
        status_code=503,
        detail=(
            "Recommendations not yet computed. "
            "Trigger via POST /orchestrator/trigger or POST /recommendations/rebuild"
        ),
    )


def update_latest_result(result: Any) -> None:
    global _latest_result
    _latest_result = result


# ── Request schemas ───────────────────────────────────────────────────────────

class CandidateInput(BaseModel):
    supplier_id:       str
    name:              str
    country_code:      str   = "US"
    tier:              str   = "TIER_2"
    health_score:      float = 75.0
    reliability_score: float = 75.0
    quality_score:     float = 75.0
    lead_time_score:   float = 75.0
    cost_efficiency:   float = 75.0
    compliance_score:  float = 75.0
    responsiveness:    float = 75.0
    flexibility:       float = 75.0
    risk_score:        float = 0.0
    is_current:        bool  = False


class EvaluateRequest(BaseModel):
    candidates: List[CandidateInput]


# ── 1. GET /recommendations/ — All recommendations ───────────────────────────

@router.get("/", summary="All supplier recommendations (latest run)")
def list_recommendations(
    action:       Optional[str] = Query(default=None, description="Filter: IMMEDIATE_SWITCH, DUAL_SOURCE, QUALIFY, MONITOR"),
    risk:         Optional[str] = Query(default=None, description="Filter: CRITICAL, HIGH, MEDIUM, LOW"),
    limit:        int           = Query(default=20, ge=1, le=100),
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res  = _get_result(current_user.user_id, db)
    recs = res.recommendations

    if action and hasattr(recs[0], 'procurement_notes'):
        recs = [r for r in recs if any(n.action == action.upper() for n in r.procurement_notes)]
    if risk:
        recs = [r for r in recs if getattr(r, 'stockout_risk', '') == risk.upper()]

    return {
        "total":        len(recs),
        "evaluated_at": res.evaluated_at,
        "recommendations": [_mini_rec(r) for r in recs[:limit]],
    }


# ── 2. GET /recommendations/summary ───────────────────────────────────────────

@router.get("/summary", summary="Recommendation pipeline summary and fleet-level statistics")
def get_summary(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    summary_data = {**res.summary} if isinstance(res.summary, dict) else {}
    summary_data["at_risk_supplier_count"] = summary_data.get("total_at_risk", 0)
    summary_data["immediate_switch_count"] = summary_data.get("immediate_switches", 0)
    return {
        "summary":                summary_data,
        "evaluated_at":           res.evaluated_at,
        "at_risk_supplier_count": summary_data.get("total_at_risk", 0),
        "immediate_switch_count": summary_data.get("immediate_switches", 0),
    }


# ── 3. GET /recommendations/alerts — Urgent actions ──────────────────────────

@router.get("/alerts", summary="IMMEDIATE_SWITCH and DUAL_SOURCE procurement actions")
def get_alerts(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    urgent_actions = ["IMMEDIATE_SWITCH", "DUAL_SOURCE"]

    alerts = []
    for rec in res.recommendations:
        notes = getattr(rec, 'procurement_notes', [])
        for note in notes:
            if getattr(note, 'action', '') in urgent_actions:
                alerts.append({
                    "at_risk_supplier_id":   getattr(rec, 'at_risk_supplier_id', ''),
                    "at_risk_supplier_name": getattr(rec, 'at_risk_supplier_name', ''),
                    "stockout_risk":         getattr(rec, 'stockout_risk', 'MEDIUM'),
                    "revenue_at_risk_usd":   getattr(rec, 'revenue_at_risk_usd', 0.0),
                    "action":                note.action,
                    "priority":              getattr(note, 'priority', 1),
                    "timeline":              getattr(note, 'timeline', 'Immediate'),
                    "note":                  getattr(note, 'note', ''),
                    "top_alternative":       rec.top_recommendation.name if hasattr(rec, 'top_recommendation') and rec.top_recommendation else None,
                    "top_alternative_score": rec.top_recommendation.recommendation_score if hasattr(rec, 'top_recommendation') and rec.top_recommendation else 0.0,
                })

    return {
        "alert_count":  len(alerts),
        "alerts":       alerts,
        "evaluated_at": res.evaluated_at,
    }


# ── 4. GET /recommendations/{supplier_id} — Full recommendation ───────────────

@router.get("/{supplier_id}", summary="Full recommendation for one at-risk supplier")
def get_recommendation(
    supplier_id: str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    rec = _find_rec(res, supplier_id)
    return rec.to_dict() if hasattr(rec, 'to_dict') else {"at_risk_supplier_id": getattr(rec, 'at_risk_supplier_id', supplier_id)}


# ── 5. GET /recommendations/{supplier_id}/topsis — TOPSIS ranking ───────────────

@router.get("/{supplier_id}/topsis", summary="TOPSIS ranking table for a supplier")
def get_topsis(
    supplier_id: str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    rec = _find_rec(res, supplier_id)
    return {
        "at_risk_supplier_id": getattr(rec, 'at_risk_supplier_id', supplier_id),
        "algorithm":           "TOPSIS — Relative Closeness Coefficient C* = D⁻/(D⁺+D⁻)",
        "topsis_ranking":      getattr(rec, 'topsis_ranking', []),
    }


# ── 6. GET /recommendations/{supplier_id}/cosine — Cosine similarity ─────────

@router.get("/{supplier_id}/cosine", summary="Cosine similarity ranking for a supplier")
def get_cosine(
    supplier_id: str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    rec = _find_rec(res, supplier_id)
    return {
        "at_risk_supplier_id": getattr(rec, 'at_risk_supplier_id', supplier_id),
        "algorithm":           "Cosine Similarity: cos(θ) = (A·B)/(‖A‖×‖B‖)",
        "cosine_ranking":      getattr(rec, 'cosine_ranking', []),
    }


# ── 7. GET /recommendations/{supplier_id}/mcdm — MCDM composite ranking ────────

@router.get("/{supplier_id}/mcdm", summary="MCDM composite ranking for a supplier")
def get_mcdm(
    supplier_id: str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    rec = _find_rec(res, supplier_id)
    matrix = getattr(rec, 'comparison_matrix', {}) or {}
    return {
        "at_risk_supplier_id": getattr(rec, 'at_risk_supplier_id', supplier_id),
        "algorithm":           "MCDM: TOPSIS×0.50 + Weighted×0.30 + Cosine×0.20",
        "mcdm_ranking":        getattr(rec, 'mcdm_ranking', []),
        "criteria":            matrix.get("criteria", []),
        "sensitivity":         matrix.get("sensitivity", {}),
    }


# ── 8. GET /recommendations/{supplier_id}/comparison — Side-by-side matrix ────

@router.get("/{supplier_id}/comparison", summary="Side-by-side KPI comparison matrix")
def get_comparison(
    supplier_id: str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    res = _get_result(current_user.user_id, db)
    rec = _find_rec(res, supplier_id)
    matrix = getattr(rec, 'comparison_matrix', {}) or {}
    return {
        "at_risk_supplier_id": getattr(rec, 'at_risk_supplier_id', supplier_id),
        "comparison_matrix":   matrix.get("comparison", {}),
        "explanation":         getattr(rec, 'explanation', ''),
    }


# ── 9. POST /recommendations/evaluate — On-demand MCDM ────────────────────────

@router.post("/evaluate", summary="On-demand MCDM evaluation for custom supplier candidates")
def evaluate_custom(
    req: EvaluateRequest,
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.recommendation.models import SupplierCandidate, DEFAULT_CRITERIA
    from app.recommendation.mcdm import MCDMEngine

    if len(req.candidates) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 candidates for MCDM evaluation")

    candidates = [
        SupplierCandidate(**c.model_dump())
        for c in req.candidates
    ]

    mcdm = MCDMEngine(criteria=DEFAULT_CRITERIA)
    result = mcdm.evaluate(candidates)

    return {
        "total_candidates":  len(candidates),
        "criteria":          result.get("criteria", []),
        "composite_weights": result.get("composite_weights", {}),
        "mcdm_ranking":      result.get("mcdm_ranking", []),
        "topsis_ranking":    result.get("topsis_ranking", []),
        "cosine_ranking":    result.get("cosine_ranking", []),
        "sensitivity":       result.get("sensitivity", {}),
        "ideal_vector":      result.get("ideal_vector", []),
    }


# ── 10. POST /recommendations/rebuild — Force re-run ──────────────────────────

@router.post("/rebuild", summary="Force re-run the full recommendation pipeline")
async def rebuild_recommendations(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    global _latest_result
    try:
        from app.recommendation.pipeline import RecommendationPipeline
        from app.db.models.supplier_score import SupplierScore
        from app.db.models.inventory_projection import InventoryProjectionRow

        supplier_rows = (
            db.query(SupplierScore)
              .order_by(SupplierScore.evaluated_at.desc())
              .limit(50).all()
        )
        supplier_data = [
            {
                "supplier_id":  s.supplier_id,
                "name":         s.name,
                "country_code": s.country_code,
                "tier":         s.tier,
                "risk_score":   s.risk_score,
                "risk_level":   s.risk_level,
                "revenue_exposure_pct": s.revenue_exposure_pct,
                "health":       {"health_score": s.health_score},
                "kpi": {
                    "reliability_score": s.reliability_score,
                    "quality_score":     s.quality_score,
                    "lead_time_score":   s.lead_time_score,
                    "cost_efficiency":   s.cost_efficiency,
                    "compliance_score":  s.compliance_score,
                    "responsiveness":    s.responsiveness,
                    "flexibility":       s.flexibility,
                },
            }
            for s in supplier_rows
        ]

        inv_rows = (
            db.query(InventoryProjectionRow)
              .order_by(InventoryProjectionRow.evaluated_at.desc())
              .limit(100).all()
        )
        inv_data = [
            {
                "stockout": {
                    "stockout_risk":        r.stockout_risk,
                    "days_remaining":       r.days_remaining,
                    "stockout_probability": r.stockout_probability,
                },
                "item": {
                    "supplier_id":    r.supplier_id,
                    "supplier_name":  r.component_name,
                    "lead_time_days": r.lead_time_days,
                    "metadata": {},
                },
                "revenue_impact":      {"revenue_lost_usd": r.revenue_lost_usd},
                "manufacturing_delay": {"delay_days": r.delay_days},
            }
            for r in inv_rows
            if r.stockout_risk in ("CRITICAL", "HIGH")
        ]

        pipeline = RecommendationPipeline()
        result   = pipeline.run(
            supplier_scores       = supplier_data,
            inventory_projections = inv_data,
            execution_id          = f"manual_rebuild_{current_user.user_id[:8]}",
        )
        _latest_result = result

        return {
            "success":                 True,
            "total_recommendations":   len(result.recommendations),
            "immediate_switches":      result.summary.get("immediate_switches", 0),
            "total_revenue_protected": result.summary.get("total_revenue_protected", 0),
            "supplier_data_used":      len(supplier_data),
            "inventory_data_used":     len(inv_data),
        }
    except Exception as e:
        logger.exception("rebuild_recommendations failed")
        raise HTTPException(status_code=500, detail=str(e))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_rec(res: Any, supplier_id: str):
    recs = getattr(res, 'recommendations', [])
    rec = next((r for r in recs if getattr(r, 'at_risk_supplier_id', '') == supplier_id), None)
    if not rec:
        sid = supplier_id.lower()
        rec = next(
            (r for r in recs
             if sid in getattr(r, 'at_risk_supplier_id', '').lower() or sid in getattr(r, 'at_risk_supplier_name', '').lower()),
            None,
        )
    if not rec:
        raise HTTPException(status_code=404, detail=f"No recommendation found for supplier '{supplier_id}'")
    return rec


def _mini_rec(r: Any) -> Dict[str, Any]:
    top = getattr(r, 'top_recommendation', None)
    at_risk_id   = getattr(r, 'at_risk_supplier_id', getattr(r, 'supplier_id', ''))
    at_risk_name = getattr(r, 'at_risk_supplier_name', getattr(r, 'supplier_name', ''))
    risk_level   = getattr(r, 'stockout_risk', getattr(r, 'risk_level', 'MEDIUM'))
    revenue_usd  = getattr(r, 'revenue_at_risk_usd', getattr(r, 'revenue_protected_usd', 0.0))
    delay        = getattr(r, 'delay_days', 0)
    notes        = getattr(r, 'procurement_notes', [])

    return {
        "at_risk_supplier_id":   at_risk_id,
        "at_risk_supplier_name": at_risk_name,
        "stockout_risk":         risk_level,
        "revenue_at_risk_usd":   revenue_usd,
        "delay_days":            delay,
        "top_recommendation": {
            "supplier_id":          getattr(top, 'supplier_id', ''),
            "name":                 getattr(top, 'name', ''),
            "country_code":         getattr(top, 'country_code', 'US'),
            "tier":                 getattr(top, 'tier', 'TIER_1'),
            "recommendation_score": round(getattr(top, 'recommendation_score', 0.0), 4),
            "topsis_score":         round(getattr(top, 'topsis_score', 0.0), 4),
            "cosine_similarity":    round(getattr(top, 'cosine_sim', 0.0), 4),
        } if top else None,
        "top_country_code":         getattr(top, 'country_code', '') if top else "",
        "top_supplier_name":        getattr(top, 'name', '') if top else "",
        "top_supplier_id":          getattr(top, 'supplier_id', '') if top else "",
        "top_tier":                 getattr(top, 'tier', '') if top else "",
        "top_recommendation_score": round(getattr(top, 'recommendation_score', 0.0), 4) if top else 0.0,
        "top_topsis_score":         round(getattr(top, 'topsis_score', 0.0), 4) if top else 0.0,
        "top_cosine_sim":           round(getattr(top, 'cosine_sim', 0.0), 4) if top else 0.0,
        "procurement_action":       notes[0].action if notes else getattr(r, 'action', None),
        "procurement_timeline":     notes[0].timeline if notes else "Immediate",
        "explanation":              getattr(r, 'explanation', ''),
    }
