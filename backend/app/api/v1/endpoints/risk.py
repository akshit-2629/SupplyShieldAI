"""
Risk Assessment REST API Endpoints — Phase 4.

PostgreSQL single source of truth with strict tenant isolation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, UserPrincipal
from app.db.models.risk_assessment import RiskAssessment
from app.risk.pipeline import RiskPipeline

logger = logging.getLogger("api.risk")

router = APIRouter(prefix="/risk", tags=["Risk Assessment"])


# ── 1. List all risk assessments ──────────────────────────────────────────────

@router.get("/assessments", summary="List risk assessments")
def list_risk_assessments(
    page:        int            = Query(default=1,   ge=1),
    page_size:   int            = Query(default=20,  ge=1, le=100),
    risk_level:  Optional[str]  = Query(default=None, description="LOW/MEDIUM/HIGH/CRITICAL"),
    country:     Optional[str]  = Query(default=None, description="ISO code e.g. CN"),
    industry:    Optional[str]  = Query(default=None, description="e.g. semiconductor"),
    event_type:  Optional[str]  = Query(default=None, description="e.g. GEOPOLITICAL"),
    min_score:   Optional[float] = Query(default=None, ge=0, le=100),
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    try:
        query = db.query(RiskAssessment)

        if risk_level:
            query = query.filter(RiskAssessment.risk_level == risk_level.upper())
        if event_type:
            query = query.filter(RiskAssessment.event_type == event_type.upper())
        if min_score is not None:
            query = query.filter(RiskAssessment.risk_score >= min_score)

        query = query.order_by(RiskAssessment.risk_score.desc(), RiskAssessment.assessed_at.desc())
        total = query.count()
        offset = (page - 1) * page_size
        rows = query.offset(offset).limit(page_size).all()

        if country:
            c_upper = country.upper()
            rows = [r for r in rows if c_upper in (r.countries or [])]
        if industry:
            ind_lower = industry.lower()
            rows = [r for r in rows if any(ind_lower in i.lower() for i in (r.industries or []))]

        return {
            "total":     total,
            "page":      page,
            "page_size": page_size,
            "pages":     max(1, (total + page_size - 1) // page_size),
            "assessments": [
                {
                    "assessment_id": r.assessment_id,
                    "news_event_id": r.news_event_id,
                    "title": r.title,
                    "url": r.url,
                    "source": r.source,
                    "event_type": r.event_type,
                    "published_at": r.published_at,
                    "assessed_at": r.assessed_at.isoformat() if r.assessed_at else None,
                    "countries": r.countries or [],
                    "industries": r.industries or [],
                    "risk_score": r.risk_score,
                    "risk_level": r.risk_level,
                    "severity_score": r.severity_score,
                    "severity_label": r.severity_label,
                    "formula_components": r.formula_components or {},
                    "geo_risk": r.geo_risk or {},
                    "industry_risk": r.industry_risk or {},
                    "supplier_tier": r.supplier_tier,
                    "exposure_weight": r.exposure_weight,
                    "confidence_score": r.confidence_score,
                    "confidence_label": r.confidence_label,
                    "confidence_breakdown": r.confidence_breakdown or {},
                    "rule_engine_results": r.rule_engine_results or {},
                    "trajectory": r.trajectory or [],
                    "trend_slope": r.trend_slope,
                }
                for r in rows
            ],
        }
    except Exception as e:
        logger.exception("list_risk_assessments failed")
        raise HTTPException(status_code=500, detail=str(e))


# ── 2. Get single assessment by ID ────────────────────────────────────────────

@router.get("/assessments/{assessment_id}", summary="Get single risk assessment by ID")
def get_risk_assessment(
    assessment_id: str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    r = db.query(RiskAssessment).filter(
        (RiskAssessment.assessment_id == assessment_id) | (RiskAssessment.id == assessment_id)
    ).first()

    if not r:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found")

    return {
        "assessment_id": r.assessment_id,
        "news_event_id": r.news_event_id,
        "title": r.title,
        "url": r.url,
        "source": r.source,
        "event_type": r.event_type,
        "published_at": r.published_at,
        "assessed_at": r.assessed_at.isoformat() if r.assessed_at else None,
        "countries": r.countries or [],
        "industries": r.industries or [],
        "risk_score": r.risk_score,
        "risk_level": r.risk_level,
        "severity_score": r.severity_score,
        "severity_label": r.severity_label,
        "formula_components": r.formula_components or {},
        "geo_risk": r.geo_risk or {},
        "industry_risk": r.industry_risk or {},
        "supplier_tier": r.supplier_tier,
        "exposure_weight": r.exposure_weight,
        "confidence_score": r.confidence_score,
        "confidence_label": r.confidence_label,
        "confidence_breakdown": r.confidence_breakdown or {},
        "rule_engine_results": r.rule_engine_results or {},
        "trajectory": r.trajectory or [],
        "trend_slope": r.trend_slope,
    }


# ── 3. Score a single event on demand ─────────────────────────────────────────

@router.post("/score", summary="Score a single disruption event on demand")
def score_event(
    event: Dict[str, Any],
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    try:
        from app.risk.scorer import RiskScorer
        scorer = RiskScorer()
        assessment = scorer.evaluate(event)
        return assessment.to_dict()
    except Exception as e:
        logger.exception("score_event failed")
        raise HTTPException(status_code=400, detail=str(e))


# ── 4. Risk stats ─────────────────────────────────────────────────────────────

@router.get("/stats", summary="Risk statistics and level breakdown")
def get_risk_stats(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    try:
        total = db.query(RiskAssessment).count()
        critical = db.query(RiskAssessment).filter_by(risk_level="CRITICAL").count()
        high = db.query(RiskAssessment).filter_by(risk_level="HIGH").count()
        medium = db.query(RiskAssessment).filter_by(risk_level="MEDIUM").count()
        low = db.query(RiskAssessment).filter_by(risk_level="LOW").count()

        return {
            "total_assessments": total,
            "by_level": {
                "CRITICAL": critical,
                "HIGH": high,
                "MEDIUM": medium,
                "LOW": low,
            },
            "critical_count": critical,
            "high_count": high,
        }
    except Exception as e:
        logger.exception("get_risk_stats failed")
        raise HTTPException(status_code=500, detail=str(e))


# ── 5. Timelines ──────────────────────────────────────────────────────────────

@router.get("/timeline", summary="All tracked risk trajectories")
def get_all_timelines(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    rows = db.query(RiskAssessment).order_by(RiskAssessment.assessed_at.desc()).limit(20).all()
    return {
        "count": len(rows),
        "timelines": [
            {
                "assessment_id": r.assessment_id,
                "title": r.title,
                "trajectory": r.trajectory or [],
                "trend_slope": r.trend_slope,
            }
            for r in rows
        ]
    }


@router.get("/timeline/{assessment_id}", summary="Trajectory for specific event")
def get_event_timeline(
    assessment_id: str,
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    r = db.query(RiskAssessment).filter(
        (RiskAssessment.assessment_id == assessment_id) | (RiskAssessment.id == assessment_id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found")
    return {
        "assessment_id": r.assessment_id,
        "title": r.title,
        "trajectory": r.trajectory or [],
        "trend_slope": r.trend_slope,
    }


# ── 6. High risk ──────────────────────────────────────────────────────────────

@router.get("/high", summary="High + Critical assessments only")
def get_high_risk_assessments(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    rows = db.query(RiskAssessment).filter(RiskAssessment.risk_level.in_(["HIGH", "CRITICAL"])).order_by(RiskAssessment.risk_score.desc()).all()
    return {
        "total": len(rows),
        "assessments": [
            {
                "assessment_id": r.assessment_id,
                "title": r.title,
                "risk_score": r.risk_score,
                "risk_level": r.risk_level,
                "countries": r.countries or [],
                "assessed_at": r.assessed_at.isoformat() if r.assessed_at else None,
            }
            for r in rows
        ]
    }


# ── 7. Rules ──────────────────────────────────────────────────────────────────

@router.get("/rules", summary="List all active rule engine rules")
def list_risk_rules(
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.risk.rule_engine import RuleEngine
    rules = RuleEngine().get_rules()
    return {
        "total": len(rules),
        "rules": rules,
    }


# ── 8. Multipliers ────────────────────────────────────────────────────────────

@router.get("/geo", summary="Geographic risk multiplier lookup")
def get_geo_risk(
    country: Optional[str] = Query(default=None),
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.risk.geo_engine import GeoRiskEngine
    geo = GeoRiskEngine()
    if country:
        return geo.get_country_risk(country.upper())
    return geo.get_all_country_risks()


@router.get("/industry", summary="Industry risk multiplier lookup")
def get_industry_risk(
    industry: Optional[str] = Query(default=None),
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.risk.industry_engine import IndustryRiskEngine
    ind = IndustryRiskEngine()
    if industry:
        return ind.get_industry_risk(industry.lower())
    return ind.get_all_industry_risks()


# ── 9. Pipeline trigger ───────────────────────────────────────────────────────

@router.post("/pipeline/run", summary="Manually trigger full risk pipeline")
def run_risk_pipeline(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    try:
        from app.news.pipeline import NewsPipeline
        news_pipeline = NewsPipeline()
        events = news_pipeline.get_recent_disruptions(db, limit=50)

        risk_pipeline = RiskPipeline()
        result = risk_pipeline.run(events, execution_id=f"manual_{current_user.user_id[:8]}")

        # Store results to DB
        for a in result.assessments:
            existing = db.query(RiskAssessment).filter_by(assessment_id=a.assessment_id).first()
            if not existing:
                db.add(RiskAssessment(
                    assessment_id=a.assessment_id,
                    news_event_id=a.news_event_id,
                    title=a.title,
                    url=a.url,
                    source=a.source,
                    event_type=a.event_type,
                    published_at=a.published_at,
                    countries=a.countries,
                    industries=a.industries,
                    risk_score=a.risk_score,
                    risk_level=a.risk_level,
                    severity_score=a.severity_score,
                    severity_label=a.severity_label,
                    formula_components=a.formula_components,
                    geo_risk=a.geo_risk,
                    industry_risk=a.industry_risk,
                    supplier_tier=a.supplier_tier,
                    exposure_weight=a.exposure_weight,
                    confidence_score=a.confidence_score,
                    confidence_label=a.confidence_label,
                    confidence_breakdown=a.confidence_breakdown,
                    rule_engine_results=a.rule_engine_results,
                    trajectory=a.trajectory,
                    trend_slope=a.trend_slope,
                ))
        db.commit()

        return {
            "success": True,
            "total_assessed": len(result.assessments),
            "critical_count": result.summary.get("critical_count", 0),
            "high_count": result.summary.get("high_count", 0),
        }
    except Exception as e:
        db.rollback()
        logger.exception("run_risk_pipeline failed")
        raise HTTPException(status_code=500, detail=str(e))
