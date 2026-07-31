"""
News Intelligence REST API Endpoints — Phase 3.

PostgreSQL single source of truth with strict tenant isolation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, UserPrincipal
from app.db.models.news_article import NewsArticle

logger = logging.getLogger("api.news")

router = APIRouter(prefix="/news", tags=["News Intelligence"])


# ── Scheduler dependency ───────────────────────────────────────────────────────

def get_news_scheduler():
    from app.news.scheduler import news_scheduler
    return news_scheduler


# ── 1. Manual pipeline trigger ────────────────────────────────────────────────

@router.post(
    "/collect",
    summary="Manually trigger one news collection pipeline run",
)
async def collect_news(
    current_user: UserPrincipal = Depends(get_current_user),
    scheduler = Depends(get_news_scheduler),
) -> Dict[str, Any]:
    try:
        result = await scheduler.trigger_now()
        return {"success": True, "result": result}
    except Exception as e:
        logger.exception("Manual collect failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ── 2. List all collected articles ───────────────────────────────────────────

@router.get(
    "/articles",
    summary="List collected news articles",
)
def list_articles(
    page:            int            = Query(default=1,     ge=1),
    page_size:       int            = Query(default=20,    ge=1, le=100),
    disruption_only: bool           = Query(default=False),
    severity:        Optional[str]  = Query(default=None,  description="CRITICAL/HIGH/MEDIUM/LOW/NONE"),
    country:         Optional[str]  = Query(default=None,  description="ISO country code e.g. CN"),
    industry:        Optional[str]  = Query(default=None,  description="Industry tag e.g. semiconductor"),
    current_user:    UserPrincipal  = Depends(get_current_user),
    db:              Session        = Depends(get_db),
) -> Dict[str, Any]:
    try:
        query = db.query(NewsArticle)

        if disruption_only:
            query = query.filter(NewsArticle.is_disruption == True)
        if severity:
            query = query.filter(NewsArticle.severity == severity.upper())

        query = query.order_by(NewsArticle.collected_at.desc())
        total = query.count()
        offset = (page - 1) * page_size
        rows = query.offset(offset).limit(page_size).all()

        if country:
            c_upper = country.upper()
            rows = [r for r in rows if c_upper in (r.country_codes or [])]
        if industry:
            ind_lower = industry.lower()
            rows = [r for r in rows if any(ind_lower in i.lower() for i in (r.industry_tags or []))]

        return {
            "total":     total,
            "page":      page,
            "page_size": page_size,
            "pages":     max(1, (total + page_size - 1) // page_size),
            "articles": [
                {
                    "id":             r.id,
                    "title":          r.title,
                    "url":            r.url,
                    "source":         r.source_name,
                    "severity":       r.severity,
                    "severity_score": float(r.severity_score or 0),
                    "event_type":     r.event_type,
                    "countries":      r.country_codes or [],
                    "industries":     r.industry_tags or [],
                    "entities":       r.entities or {},
                    "is_disruption":  r.is_disruption,
                    "is_duplicate":   r.is_duplicate,
                    "published_at":   r.published_at.isoformat() if r.published_at else None,
                    "collected_at":   r.collected_at.isoformat() if r.collected_at else None,
                }
                for r in rows
            ],
        }
    except Exception as e:
        logger.exception("list_articles failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ── 3. Disruption events feed ─────────────────────────────────────────────────

@router.get(
    "/events",
    summary="Get supply chain disruption events",
)
def list_disruption_events(
    limit:        int           = Query(default=50, ge=1, le=200),
    severity:     Optional[str] = Query(default=None),
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    try:
        query = db.query(NewsArticle).filter(NewsArticle.is_disruption == True)
        if severity:
            query = query.filter(NewsArticle.severity == severity.upper())

        rows = query.order_by(NewsArticle.severity_score.desc(), NewsArticle.collected_at.desc()).limit(limit).all()
        return {
            "total":  len(rows),
            "events": [
                {
                    "id":             r.id,
                    "title":          r.title,
                    "url":            r.url,
                    "source":         r.source_name,
                    "severity":       r.severity,
                    "severity_score": float(r.severity_score or 0),
                    "event_type":     r.event_type,
                    "countries":      r.country_codes or [],
                    "industries":     r.industry_tags or [],
                    "entities":       r.entities or {},
                    "published_at":   r.published_at.isoformat() if r.published_at else None,
                    "collected_at":   r.collected_at.isoformat() if r.collected_at else None,
                }
                for r in rows
            ],
        }
    except Exception as e:
        logger.exception("list_disruption_events failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ── 4. Pipeline statistics ────────────────────────────────────────────────────

@router.get(
    "/stats",
    summary="News pipeline statistics",
)
def get_news_stats(
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    try:
        total = db.query(NewsArticle).count()
        disruptions = db.query(NewsArticle).filter(NewsArticle.is_disruption == True).count()
        duplicates  = db.query(NewsArticle).filter(NewsArticle.is_duplicate == True).count()

        rows = db.query(NewsArticle.severity, NewsArticle.event_type).all()
        severity_counts: Dict[str, int] = {}
        event_type_counts: Dict[str, int] = {}
        for s, et in rows:
            sev = s or "NONE"
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            if et:
                event_type_counts[et] = event_type_counts.get(et, 0) + 1

        return {
            "total_articles":      total,
            "disruption_events":   disruptions,
            "duplicates_removed":  duplicates,
            "severity_breakdown":  severity_counts,
            "event_type_breakdown": event_type_counts,
        }
    except Exception as e:
        logger.warning(f"get_news_stats error: {e}")
        return {"total_articles": 0, "error": str(e)}


# ── 5. Configured sources ─────────────────────────────────────────────────────

@router.get(
    "/sources",
    summary="List configured RSS news sources",
)
def list_sources(
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.news.sources import SUPPLY_CHAIN_RSS_SOURCES, TAVILY_SEARCH_QUERIES
    return {
        "rss_sources": [
            {
                "name":              s.name,
                "rss_url":           s.rss_url,
                "category":          s.category,
                "credibility_score": s.credibility_score,
            }
            for s in SUPPLY_CHAIN_RSS_SOURCES
        ],
        "tavily_queries": TAVILY_SEARCH_QUERIES,
    }


# ── 6. Scheduler status ───────────────────────────────────────────────────────

@router.get(
    "/scheduler/status",
    summary="Get background scheduler status",
)
def get_scheduler_status(
    current_user: UserPrincipal = Depends(get_current_user),
    scheduler = Depends(get_news_scheduler),
) -> Dict[str, Any]:
    return scheduler.status()


# ── 7. Scheduler toggle ───────────────────────────────────────────────────────

@router.post(
    "/scheduler/toggle",
    summary="Start or stop the background news collection scheduler",
)
def toggle_scheduler(
    action:       str           = Query(..., description="start | stop | pause | resume"),
    current_user: UserPrincipal = Depends(get_current_user),
    scheduler                   = Depends(get_news_scheduler),
) -> Dict[str, Any]:
    action = action.lower().strip()
    if action == "start":
        scheduler.start()
    elif action == "stop":
        scheduler.stop()
    elif action == "pause":
        scheduler.pause()
    elif action == "resume":
        scheduler.resume()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action '{action}'. Use: start | stop | pause | resume",
        )
    return {"action": action, "status": scheduler.status()}
