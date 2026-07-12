"""
NewsPipeline — Orchestrates the complete news intelligence pipeline.

Pipeline steps:
  1. Collect  — RSS feeds + Tavily API (concurrent)
  2. Clean    — HTML stripping, text normalization
  3. Extract  — Entities, countries, industries, severity, event_type
  4. Embed    — Generate 384-dim sentence vectors (all-MiniLM-L6-v2)
  5. Deduplicate — Cosine similarity (≥0.85) + URL/title-hash matching
  6. Store    — Persist new articles to PostgreSQL

Returns a PipelineResult with counts and sample disruption events.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("news.pipeline")


@dataclass
class PipelineResult:
    collected:    int = 0
    cleaned:      int = 0
    embedded:     int = 0
    duplicates:   int = 0
    stored:       int = 0
    disruptions:  int = 0
    errors:       List[str] = field(default_factory=list)
    started_at:   str = ""
    completed_at: str = ""


class NewsPipeline:
    """
    Coordinates all news processing components.

    Usage:
        pipeline = NewsPipeline()
        result = await pipeline.run(db=session)
    """

    def __init__(self) -> None:
        from app.core.config import settings
        from app.news.collector    import NewsCollector
        from app.news.cleaner      import NewsArticleCleaner
        from app.news.extractor    import NewsArticleExtractor
        from app.news.embedder     import NewsEmbedder
        from app.news.deduplicator import NewsDeduplicator

        self.collector    = NewsCollector(
            tavily_api_key=getattr(settings, "TAVILY_API_KEY", None) or None
        )
        self.cleaner      = NewsArticleCleaner()
        self.extractor    = NewsArticleExtractor()
        self.embedder     = NewsEmbedder()
        self.deduplicator = NewsDeduplicator()

    async def run(self, db=None) -> PipelineResult:
        """
        Execute full pipeline. If db is None, skip storage step.
        """
        result = PipelineResult(
            started_at=datetime.now(timezone.utc).isoformat()
        )

        try:
            # ── Step 1: Collect ───────────────────────────────────────────────
            logger.info("[pipeline] Step 1: Collecting from all sources...")
            raw_articles = await self.collector.collect_all()
            result.collected = len(raw_articles)
            logger.info(f"[pipeline] Collected {result.collected} articles")

            if not raw_articles:
                logger.info("[pipeline] No articles collected — pipeline complete")
                result.completed_at = datetime.now(timezone.utc).isoformat()
                return result

            # ── Step 2: Clean ─────────────────────────────────────────────────
            logger.info("[pipeline] Step 2: Cleaning articles...")
            cleaned = [self.cleaner.clean_article(a) for a in raw_articles]
            # Drop articles with no title after cleaning
            cleaned = [a for a in cleaned if a.get("title", "").strip()]
            result.cleaned = len(cleaned)
            logger.info(f"[pipeline] {result.cleaned} articles after cleaning")

            # ── Step 3: Extract metadata (NLP, severity, etc.) ────────────────
            logger.info("[pipeline] Step 3: Extracting metadata...")
            enriched = await asyncio.to_thread(
                self._extract_batch, cleaned
            )

            # ── Step 4: Embed ─────────────────────────────────────────────────
            logger.info("[pipeline] Step 4: Generating embeddings...")
            embedded = await asyncio.to_thread(
                self.embedder.embed_batch, enriched
            )
            result.embedded = sum(1 for a in embedded if a.get("embedding") is not None)
            logger.info(f"[pipeline] {result.embedded}/{result.cleaned} articles embedded")

            # ── Step 5: Deduplicate ───────────────────────────────────────────
            logger.info("[pipeline] Step 5: Deduplicating...")
            if db is not None:
                existing_embeddings, existing_urls, existing_titles = \
                    await asyncio.to_thread(
                        self.deduplicator.load_recent_from_db, db
                    )
            else:
                existing_embeddings, existing_urls, existing_titles = [], set(), set()

            new_articles = self.deduplicator.filter_new_articles(
                articles=embedded,
                existing_embeddings=existing_embeddings,
                existing_urls=existing_urls,
                existing_title_hashes=existing_titles,
            )
            result.duplicates = result.cleaned - len(new_articles)
            logger.info(
                f"[pipeline] {len(new_articles)} new articles "
                f"({result.duplicates} duplicates removed)"
            )

            # ── Step 6: Store ─────────────────────────────────────────────────
            if new_articles:
                logger.info("[pipeline] Step 6: Storing to Supabase...")
                stored_ids = await asyncio.to_thread(
                    self._store_articles_supabase, new_articles
                )
                result.stored = len(stored_ids)

                # Fallback: SQLAlchemy direct DB (if Supabase REST fails and db is available)
                if result.stored == 0 and db is not None:
                    logger.info("[pipeline] Step 6b: Falling back to SQLAlchemy store...")
                    stored_ids = await asyncio.to_thread(
                        self._store_articles_sqlalchemy, db, new_articles
                    )
                    result.stored = len(stored_ids)
            else:
                result.stored = 0

            result.disruptions = sum(
                1 for a in new_articles if a.get("is_disruption")
            )
            logger.info(
                f"[pipeline] Complete: stored={result.stored}, "
                f"disruptions={result.disruptions}"
            )

        except Exception as e:
            logger.exception(f"[pipeline] Pipeline error: {e}")
            result.errors.append(str(e))

        result.completed_at = datetime.now(timezone.utc).isoformat()
        return result

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _extract_batch(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run extractor synchronously on all articles."""
        return [self.extractor.enrich(a) for a in articles]

    def _store_articles_supabase(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Primary: store articles via Supabase REST API (no direct DB connection)."""
        from app.news.supabase_storage import supabase_storage
        return supabase_storage.store_articles(articles)

    def _store_articles_sqlalchemy(self, db, articles: List[Dict[str, Any]]) -> List[str]:
        """Fallback: store articles directly via SQLAlchemy (requires DB password)."""
        from app.db.models.news_article import NewsArticle
        from sqlalchemy.exc import IntegrityError

        stored_ids: List[str] = []

        for article in articles:
            try:
                record = NewsArticle(
                    title             = (article.get("title") or "")[:2000],
                    content           = article.get("content") or "",
                    url               = (article.get("url") or "")[:2048],
                    source_name       = (article.get("source_name") or "")[:200],
                    source_url        = (article.get("source_url") or "")[:2048],
                    credibility_score = float(article.get("credibility_score") or 5.0),
                    published_at      = article.get("published_at"),
                    entities          = article.get("entities"),
                    country_codes     = article.get("country_codes"),
                    industry_tags     = article.get("industry_tags"),
                    severity          = article.get("severity", "NONE"),
                    severity_score    = float(article.get("severity_score") or 0.0),
                    event_type        = article.get("event_type"),
                    embedding         = article.get("embedding"),
                    is_duplicate      = article.get("is_duplicate", False),
                    is_disruption     = article.get("is_disruption", False),
                    is_processed      = True,
                )
                db.add(record)
                db.flush()
                stored_ids.append(str(record.id))
            except IntegrityError:
                db.rollback()
            except Exception as e:
                db.rollback()
                logger.warning(f"[pipeline] SQLAlchemy store error: {e}")

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"[pipeline] DB commit failed: {e}")
            return []

        return stored_ids

    def get_recent_disruptions(self, db, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch recent disruption events.
        Primary: Supabase REST API
        Fallback: SQLAlchemy direct query
        """
        # Try Supabase REST first
        try:
            from app.news.supabase_storage import supabase_storage
            rows = supabase_storage.get_disruptions(limit=limit)
            if rows:
                return [
                    {
                        "id":            row.get("id", ""),
                        "title":         row.get("title", ""),
                        "url":           row.get("url", ""),
                        "source":        row.get("source_name", ""),
                        "countries":     row.get("country_codes") or [],
                        "industries":    row.get("industry_tags") or [],
                        "severity":      row.get("severity", "NONE"),
                        "severity_score": float(row.get("severity_score") or 0),
                        "event_type":    row.get("event_type"),
                        "entities":      row.get("entities") or {},
                        "published_at":  row.get("published_at"),
                        "collected_at":  row.get("collected_at"),
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.debug(f"[pipeline] Supabase disruptions fetch error: {e}")

        # Fallback: SQLAlchemy
        try:
            from app.db.models.news_article import NewsArticle
            articles = (
                db.query(NewsArticle)
                .filter(NewsArticle.is_disruption.is_(True))
                .order_by(NewsArticle.collected_at.desc())
                .limit(limit)
                .all()
            )
            return [self._article_to_event(a) for a in articles]
        except Exception as e:
            logger.warning(f"[pipeline] get_recent_disruptions error: {e}")
            return []

    @staticmethod
    def _article_to_event(article) -> Dict[str, Any]:
        """Convert a NewsArticle ORM object to the WorkflowState event dict."""
        return {
            "id":            str(article.id),
            "title":         article.title,
            "url":           article.url,
            "source":        article.source_name,
            "countries":     article.country_codes  or [],
            "industries":    article.industry_tags  or [],
            "severity":      article.severity,
            "severity_score": float(article.severity_score or 0),
            "event_type":    article.event_type,
            "entities":      article.entities       or {},
            "published_at":  article.published_at.isoformat() if article.published_at else None,
            "collected_at":  article.collected_at.isoformat() if article.collected_at else None,
        }
