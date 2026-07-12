"""
SupabaseNewsStorage — Stores news articles via the Supabase REST API.

Uses the supabase-py client (service role key) to upsert articles directly
into the `news_articles` table via PostgREST. This works without a direct
PostgreSQL connection string or password — only the SUPABASE_URL and
SUPABASE_SERVICE_ROLE_KEY are needed (already configured in .env).

Deduplication: Uses `on_conflict=url` upsert, so re-inserting the same URL
safely updates in place rather than creating a duplicate.

Prerequisites (one-time setup):
  Run the SQL from backend/app/db/migrations/phase3_news_articles.sql
  in your Supabase SQL Editor:
  https://supabase.com/dashboard/project/<your-project>/sql/new
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("news.supabase_storage")

# Batch size for upsert calls (PostgREST has a default row limit)
BATCH_SIZE = 50


class SupabaseNewsStorage:
    """Stores news articles via Supabase PostgREST (no direct DB connection)."""

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        """Lazy-load Supabase admin client (service role key bypasses RLS)."""
        if self._client is not None:
            return self._client
        try:
            from app.core.config import settings
            from supabase import create_client
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
                logger.warning("[supabase_storage] Missing SUPABASE_URL or SERVICE_ROLE_KEY")
                return None
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
        except Exception as e:
            logger.warning(f"[supabase_storage] Client init failed: {e}")
            return None
        return self._client

    def store_articles(self, articles: List[Dict[str, Any]]) -> List[str]:
        """
        Upsert articles into the news_articles table via Supabase REST API.
        Skips articles whose URL already exists (conflict on url column).
        Returns list of successfully stored article IDs.
        """
        client = self._get_client()
        if client is None:
            logger.warning("[supabase_storage] No client — skipping storage")
            return []

        stored_ids: List[str] = []

        # Build rows for upsert
        rows = []
        for article in articles:
            url = (article.get("url") or "").strip()
            title = (article.get("title") or "").strip()
            if not url or not title:
                continue

            # Serialize published_at datetime to ISO string
            pub_at = article.get("published_at")
            if isinstance(pub_at, datetime):
                pub_at = pub_at.isoformat()

            row = {
                "title":             title[:2000],
                "content":           (article.get("content") or "")[:5000],
                "url":               url[:2048],
                "source_name":       (article.get("source_name") or "")[:200],
                "source_url":        (article.get("source_url") or "")[:2048],
                "credibility_score": float(article.get("credibility_score") or 5.0),
                "published_at":      pub_at,
                "entities":          article.get("entities"),
                "country_codes":     article.get("country_codes"),
                "industry_tags":     article.get("industry_tags"),
                "severity":          article.get("severity", "NONE"),
                "severity_score":    float(article.get("severity_score") or 0.0),
                "event_type":        article.get("event_type"),
                # Omit embedding in REST API calls to keep payload small
                # (384-dim float array is large; use direct DB for embeddings)
                "is_duplicate":      article.get("is_duplicate", False),
                "is_disruption":     article.get("is_disruption", False),
                "is_processed":      True,
            }
            rows.append(row)

        if not rows:
            return []

        # Upsert in batches
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            try:
                result = (
                    client.table("news_articles")
                    .upsert(batch, on_conflict="url", ignore_duplicates=True)
                    .execute()
                )
                if result.data:
                    stored_ids.extend(
                        row.get("id", "") for row in result.data if row.get("id")
                    )
                    logger.info(
                        f"[supabase_storage] Batch {i//BATCH_SIZE + 1}: "
                        f"stored {len(result.data)} articles"
                    )
            except Exception as e:
                err_msg = str(e)
                if "news_articles" in err_msg and "not found" in err_msg.lower():
                    logger.error(
                        "[supabase_storage] ❌ Table 'news_articles' does not exist!\n"
                        "  → Run this SQL in Supabase SQL Editor:\n"
                        "  https://supabase.com/dashboard/project/qcmypkzxtbbkyyjbjisw/sql/new\n"
                        "  File: backend/app/db/migrations/phase3_news_articles.sql"
                    )
                else:
                    logger.warning(f"[supabase_storage] Batch upsert error: {e}")

        logger.info(
            f"[supabase_storage] Total stored: {len(stored_ids)}/{len(rows)} articles"
        )
        return stored_ids

    def get_disruptions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch recent disruption events from Supabase."""
        client = self._get_client()
        if client is None:
            return []
        try:
            result = (
                client.table("news_articles")
                .select(
                    "id,title,url,source_name,severity,severity_score,"
                    "event_type,country_codes,industry_tags,entities,"
                    "published_at,collected_at"
                )
                .eq("is_disruption", True)
                .order("severity_score", desc=True)
                .order("collected_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.warning(f"[supabase_storage] get_disruptions error: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get summary statistics from news_articles table."""
        client = self._get_client()
        if client is None:
            return {"error": "No Supabase client"}
        try:
            # Total count
            total_result = (
                client.table("news_articles")
                .select("id", count="exact")
                .execute()
            )
            total = total_result.count or 0

            # Disruption count
            disruption_result = (
                client.table("news_articles")
                .select("id", count="exact")
                .eq("is_disruption", True)
                .execute()
            )
            disruptions = disruption_result.count or 0

            return {
                "total_articles":    total,
                "disruption_events": disruptions,
            }
        except Exception as e:
            logger.warning(f"[supabase_storage] get_stats error: {e}")
            return {"error": str(e)}


# Module-level singleton
supabase_storage = SupabaseNewsStorage()
