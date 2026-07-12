"""
Recommendation REST API — Phase 8

10 endpoints:

  GET  /recommendations/                 — All recommendations (latest run)
  GET  /recommendations/summary          — Pipeline summary + fleet-level stats
  GET  /recommendations/alerts           — IMMEDIATE_SWITCH + DUAL_SOURCE actions
  GET  /recommendations/{supplier_id}    — Full recommendation for one at-risk supplier
  GET  /recommendations/{supplier_id}/topsis   — TOPSIS ranking table
  GET  /recommendations/{supplier_id}/cosine   — Cosine similarity ranking
  GET  /recommendations/{supplier_id}/mcdm     — MCDM composite ranking
  GET  /recommendations/{supplier_id}/comparison — Side-by-side comparison matrix
  POST /recommendations/evaluate         — On-demand MCDM evaluation for custom candidates
  POST /recommendations/rebuild          — Force re-run the full recommendation pipeline
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db

logger = logging.getLogger("api.recommendation")

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# ─────────────────────────────────────────────────────────────────────────────
# In-memory result store
# ─────────────────────────────────────────────────────────────────────────────

_latest_result: Optional[Any] = None


def _get_result():
    if _latest_result is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Recommendations not yet computed. "
                "Trigger via POST /orchestrator/trigger or POST /recommendations/rebuild"
            ),
        )
    return _latest_result


def update_latest_result(result: Any) -> None:
    global _latest_result
    _latest_result = result


# ─────────────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────────────

class CandidateInput(BaseModel):
    supplier_id:      str
    name:             str
    country_code:     str   = "US"
    tier:             str   = "TIER_2"
    health_score:     float = 75.0
    reliability_score: float = 75.0
    quality_score:    float = 75.0
    lead_time_score:  float = 75.0
    cost_efficiency:  float = 75.0
    compliance_score: float = 75.0
    responsiveness:   float = 75.0
    flexibility:      float = 75.0
    risk_score:       float = 0.0
    is_current:       bool  = False


class EvaluateRequest(BaseModel):
    candidates: List[CandidateInput]


# ─────────────────────────────────────────────────────────────────────────────
# 1. GET /recommendations/ — All recommendations
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", summary="All supplier recommendations (latest run)")
def list_recommendations(
    action:   Optional[str] = Query(default=None, description="Filter: IMMEDIATE_SWITCH, DUAL_SOURCE, QUALIFY, MONITOR"),
    risk:     Optional[str] = Query(default=None, description="Filter: CRITICAL, HIGH, MEDIUM, LOW"),
    limit:    int           = Query(default=20, ge=1, le=100),
) -> Dict[str, Any]:
    res  = _get_result()
    recs = res.recommendations

    if action:
        recs = [r for r in recs if any(n.action == action.upper() for n in r.procurement_notes)]
    if risk:
        recs = [r for r in recs if r.stockout_risk == risk.upper()]

    recs = sorted(recs, key=lambda r: r.revenue_at_risk_usd, reverse=True)

    return {
        "total":        len(recs),
        "evaluated_at": res.evaluated_at,
        "recommendations": [_mini_rec(r) for r in recs[:limit]],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. GET /recommendations/summary
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/summary", summary="Recommendation pipeline summary and fleet-level statistics")
def get_summary() -> Dict[str, Any]:
    res = _get_result()
    return {
        "summary":      res.summary,
        "evaluated_at": res.evaluated_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. GET /recommendations/alerts — Urgent actions
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/alerts", summary="IMMEDIATE_SWITCH and DUAL_SOURCE procurement actions")
def get_alerts() -> Dict[str, Any]:
    res = _get_result()
    urgent_actions = ["IMMEDIATE_SWITCH", "DUAL_SOURCE"]

    alerts = []
    for rec in res.recommendations:
        for note in rec.procurement_notes:
            if note.action in urgent_actions:
                alerts.append({
                    "at_risk_supplier_id":   rec.at_risk_supplier_id,
                    "at_risk_supplier_name": rec.at_risk_supplier_name,
                    "stockout_risk":         rec.stockout_risk,
                    "revenue_at_risk_usd":   rec.revenue_at_risk_usd,
                    "action":                note.action,
                    "priority":              note.priority,
                    "timeline":              note.timeline,
                    "note":                  note.note,
                    "top_alternative":       rec.top_recommendation.name if rec.top_recommendation else None,
                    "top_alternative_score": rec.top_recommendation.recommendation_score if rec.top_recommendation else 0.0,
                })

    alerts = sorted(alerts, key=lambda a: a["revenue_at_risk_usd"], reverse=True)

    return {
        "alert_count":  len(alerts),
        "alerts":       alerts,
        "evaluated_at": res.evaluated_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. GET /recommendations/{supplier_id} — Full recommendation
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{supplier_id}", summary="Full recommendation for one at-risk supplier")
def get_recommendation(supplier_id: str) -> Dict[str, Any]:
    res = _get_result()
    rec = _find_rec(res, supplier_id)
    return rec.to_dict()


# ─────────────────────────────────────────────────────────────────────────────
# 5. GET /recommendations/{supplier_id}/topsis — TOPSIS ranking
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{supplier_id}/topsis", summary="TOPSIS ranking table for a supplier")
def get_topsis(supplier_id: str) -> Dict[str, Any]:
    res = _get_result()
    rec = _find_rec(res, supplier_id)
    return {
        "at_risk_supplier_id": rec.at_risk_supplier_id,
        "algorithm":           "TOPSIS — Relative Closeness Coefficient C* = D⁻/(D⁺+D⁻)",
        "topsis_ranking":      rec.topsis_ranking,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. GET /recommendations/{supplier_id}/cosine — Cosine similarity ranking
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{supplier_id}/cosine", summary="Cosine similarity ranking for a supplier")
def get_cosine(supplier_id: str) -> Dict[str, Any]:
    res = _get_result()
    rec = _find_rec(res, supplier_id)
    return {
        "at_risk_supplier_id": rec.at_risk_supplier_id,
        "algorithm":           "Cosine Similarity: cos(θ) = (A·B)/(‖A‖×‖B‖)",
        "cosine_ranking":      rec.cosine_ranking,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 7. GET /recommendations/{supplier_id}/mcdm — MCDM composite ranking
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{supplier_id}/mcdm", summary="MCDM composite ranking for a supplier")
def get_mcdm(supplier_id: str) -> Dict[str, Any]:
    res = _get_result()
    rec = _find_rec(res, supplier_id)
    return {
        "at_risk_supplier_id": rec.at_risk_supplier_id,
        "algorithm":           "MCDM: TOPSIS×0.50 + Weighted×0.30 + Cosine×0.20",
        "mcdm_ranking":        rec.mcdm_ranking,
        "criteria":            rec.comparison_matrix.get("criteria", []),
        "sensitivity":         rec.comparison_matrix.get("sensitivity", {}),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 8. GET /recommendations/{supplier_id}/comparison — Side-by-side matrix
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{supplier_id}/comparison", summary="Side-by-side KPI comparison matrix")
def get_comparison(supplier_id: str) -> Dict[str, Any]:
    res = _get_result()
    rec = _find_rec(res, supplier_id)
    return {
        "at_risk_supplier_id": rec.at_risk_supplier_id,
        "comparison_matrix":   rec.comparison_matrix.get("comparison", {}),
        "explanation":         rec.explanation,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 9. POST /recommendations/evaluate — On-demand MCDM
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/evaluate", summary="On-demand MCDM evaluation for custom supplier candidates")
def evaluate_custom(req: EvaluateRequest) -> Dict[str, Any]:
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


# ─────────────────────────────────────────────────────────────────────────────
# 10. POST /recommendations/rebuild — Force re-run
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/rebuild", summary="Force re-run the full recommendation pipeline")
async def rebuild_recommendations(db: Session = Depends(get_db)) -> Dict[str, Any]:
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
                    "stockout_risk":       r.stockout_risk,
                    "days_remaining":      r.days_remaining,
                    "stockout_probability": r.stockout_probability,
                },
                "item": {
                    "supplier_id":   r.supplier_id,
                    "supplier_name": r.component_name,
                    "lead_time_days": r.lead_time_days,
                    "metadata": {},
                },
                "revenue_impact": {"revenue_lost_usd": r.revenue_lost_usd},
                "manufacturing_delay": {"delay_days": r.delay_days},
            }
            for r in inv_rows
            if r.stockout_risk in ("CRITICAL", "HIGH")
        ]

        pipeline = RecommendationPipeline()
        result   = pipeline.run(
            supplier_scores       = supplier_data,
            inventory_projections = inv_data,
            execution_id          = "manual_rebuild",
        )
        _latest_result = result

        return {
            "success":                True,
            "total_recommendations":  len(result.recommendations),
            "immediate_switches":     result.summary.get("immediate_switches", 0),
            "total_revenue_protected": result.summary.get("total_revenue_protected", 0),
            "supplier_data_used":     len(supplier_data),
            "inventory_data_used":    len(inv_data),
        }
    except Exception as e:
        logger.exception("rebuild_recommendations failed")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _find_rec(res: Any, supplier_id: str):
    rec = next((r for r in res.recommendations if r.at_risk_supplier_id == supplier_id), None)
    if not rec:
        sid = supplier_id.lower()
        rec = next(
            (r for r in res.recommendations
             if sid in r.at_risk_supplier_id.lower() or sid in r.at_risk_supplier_name.lower()),
            None,
        )
    if not rec:
        raise HTTPException(status_code=404, detail=f"No recommendation found for supplier '{supplier_id}'")
    return rec


def _mini_rec(r: Any) -> Dict[str, Any]:
    top = r.top_recommendation
    return {
        "at_risk_supplier_id":   r.at_risk_supplier_id,
        "at_risk_supplier_name": r.at_risk_supplier_name,
        "stockout_risk":         r.stockout_risk,
        "revenue_at_risk_usd":   r.revenue_at_risk_usd,
        "delay_days":            r.delay_days,
        "top_recommendation": {
            "supplier_id":          top.supplier_id,
            "name":                 top.name,
            "country_code":         top.country_code,
            "tier":                 top.tier,
            "recommendation_score": round(top.recommendation_score, 4),
            "topsis_score":         round(top.topsis_score, 4),
            "cosine_similarity":    round(top.cosine_sim, 4),
        } if top else None,
        "procurement_action":  r.procurement_notes[0].action if r.procurement_notes else None,
        "procurement_timeline": r.procurement_notes[0].timeline if r.procurement_notes else None,
    }
