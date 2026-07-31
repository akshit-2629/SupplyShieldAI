"""
NewsCollector — Fetches articles from RSS feeds and Tavily API.

Sources:
  1. RSS feeds (feedparser): Reuters, BBC, Google News supply-chain queries
  2. Tavily Search API (httpx): targeted semantic queries (requires API key)

All sources run concurrently via asyncio.gather for speed.

Each returned article dict has the following structure:
  {
    "title":            str,
    "url":              str,
    "content":          str,  # may contain HTML — cleaned by cleaner.py
    "published_at":     datetime (UTC, timezone-aware),
    "source_name":      str,
    "source_url":       str,
    "credibility_score": float,
  }
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("news.collector")

MAX_ARTICLES_PER_FEED  = 25    # Cap per RSS feed
HTTP_TIMEOUT           = 20.0  # seconds


class NewsCollector:
    """Gathers articles from configured RSS sources and Tavily API."""

    def __init__(self, tavily_api_key: Optional[str] = None) -> None:
        self.tavily_api_key = tavily_api_key

    # ── Public interface ──────────────────────────────────────────────────────

    async def collect_all(self, tenant_context: Optional[dict] = None) -> List[Dict[str, Any]]:
        """
        Collect from all configured sources concurrently.
        Uses tenant_context (industry, components) to fetch targeted feeds.
        Returns a URL-deduplicated list of raw article dicts.
        """
        rss_task    = self._collect_all_rss(tenant_context=tenant_context)
        tavily_task = self._collect_tavily()

        rss_articles, tavily_articles = await asyncio.gather(
            rss_task, tavily_task, return_exceptions=True
        )

        all_articles: List[Dict[str, Any]] = []
        if isinstance(rss_articles, list):
            all_articles.extend(rss_articles)
        if isinstance(tavily_articles, list):
            all_articles.extend(tavily_articles)

        # URL-level dedup before passing to pipeline
        seen_urls: set = set()
        unique: List[Dict[str, Any]] = []
        for article in all_articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(article)

        logger.info(
            f"[collector] Collected {len(unique)} unique articles "
            f"(RSS: {len(rss_articles) if isinstance(rss_articles, list) else 0}, "
            f"Tavily: {len(tavily_articles) if isinstance(tavily_articles, list) else 0})"
        )
        return unique

    # ── RSS Collection ────────────────────────────────────────────────────────

    async def _collect_all_rss(self, tenant_context: Optional[dict] = None) -> List[Dict[str, Any]]:
        from app.news.sources import SUPPLY_CHAIN_RSS_SOURCES, get_industry_rss_sources

        industry = tenant_context.get("industry") if tenant_context else "Electronics Manufacturing"
        components = tenant_context.get("components") if tenant_context else []
        sources = get_industry_rss_sources(industry=industry, component_names=components)

        tasks = [self._fetch_rss(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles: List[Dict[str, Any]] = []
        for r in results:
            if isinstance(r, list):
                articles.extend(r)
        return articles

    async def _fetch_rss(self, source) -> List[Dict[str, Any]]:
        """Fetch and parse one RSS feed."""
        articles: List[Dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(HTTP_TIMEOUT),
                follow_redirects=True,
                headers={"User-Agent": "SupplyShieldAI/1.0 News-Collector"},
            ) as client:
                response = await client.get(source.rss_url)
                response.raise_for_status()
                raw_xml = response.text

            # feedparser is synchronous; run in thread to avoid blocking event loop
            import feedparser
            feed = await asyncio.to_thread(feedparser.parse, raw_xml)

            for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
                url   = entry.get("link", "").strip()
                title = entry.get("title", "").strip()
                if not url or not title:
                    continue

                # Extract best available content field
                content = (
                    entry.get("summary") or
                    entry.get("description") or
                    entry.get("content", [{}])[0].get("value", "") or ""
                )

                articles.append({
                    "title":             title,
                    "url":               url,
                    "content":           content,
                    "published_at":      self._parse_feedparser_date(entry),
                    "source_name":       source.name,
                    "source_url":        source.base_url,
                    "credibility_score": source.credibility_score,
                })

            logger.info(
                f"[collector] {source.name}: {len(articles)} articles"
            )

        except httpx.TimeoutException:
            logger.warning(f"[collector] Timeout fetching {source.name}")
        except httpx.HTTPStatusError as e:
            logger.warning(f"[collector] HTTP {e.response.status_code} for {source.name}")
        except Exception as e:
            logger.warning(f"[collector] {source.name} failed: {type(e).__name__}: {e}")

        return articles

    # ── Tavily Collection ─────────────────────────────────────────────────────

    async def _collect_tavily(self) -> List[Dict[str, Any]]:
        if not self.tavily_api_key:
            return []

        from app.news.sources import TAVILY_SEARCH_QUERIES

        articles: List[Dict[str, Any]] = []
        # Use first 4 queries to control API usage
        queries_to_run = TAVILY_SEARCH_QUERIES[:4]

        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.tavily_api_key)
        except ImportError:
            logger.warning("[collector] tavily-python not installed")
            return []

        for query in queries_to_run:
            try:
                response = await asyncio.to_thread(
                    client.search,
                    query=query,
                    search_depth="basic",
                    max_results=5,
                    include_raw_content=False,
                )
                for result in response.get("results", []):
                    url   = result.get("url", "").strip()
                    title = result.get("title", "").strip()
                    if not url or not title:
                        continue
                    articles.append({
                        "title":             title,
                        "url":               url,
                        "content":           result.get("content", ""),
                        "published_at":      datetime.now(timezone.utc),
                        "source_name":       "Tavily",
                        "source_url":        url,
                        "credibility_score": 7.0,
                    })
            except Exception as e:
                logger.warning(f"[collector] Tavily query '{query[:30]}' failed: {e}")
                # Continue with next query instead of failing entirely

        logger.info(f"[collector] Tavily: {len(articles)} articles from {len(queries_to_run)} queries")
        return articles

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_feedparser_date(entry) -> datetime:
        """Parse feedparser's published_parsed struct or fall back to now."""
        try:
            if getattr(entry, "published_parsed", None):
                ts = time.mktime(entry.published_parsed)
                return datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception:
            pass
        return datetime.now(timezone.utc)


# Module-level factory (configured at runtime from settings)
def make_collector(tavily_api_key: Optional[str] = None) -> NewsCollector:
    return NewsCollector(tavily_api_key=tavily_api_key)
