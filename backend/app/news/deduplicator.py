"""
NewsDeduplicator — Cosine-similarity deduplication for news articles.

Algorithm: Cosine Similarity (numpy-based, no sklearn required)

  similarity = dot(a, b) / (||a|| × ||b||)

An article is a DUPLICATE when:
  1. Its URL already exists in the DB (exact URL match), OR
  2. Its embedding is within SIMILARITY_THRESHOLD of any article
     collected in the last LOOKBACK_HOURS hours.

Thresholds:
  SIMILARITY_THRESHOLD = 0.85 — articles with cosine similarity ≥ 0.85
                                 are considered near-duplicates
  LOOKBACK_HOURS       = 48   — only compare against articles from the last 48h

Fallback (when embeddings are None):
  Falls back to exact URL + normalized title hash comparison.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("news.deduplicator")

SIMILARITY_THRESHOLD = 0.85
LOOKBACK_HOURS       = 48


class NewsDeduplicator:
    """
    Filters near-duplicate articles using cosine similarity on embeddings.
    """

    # ── Cosine similarity (pure numpy) ────────────────────────────────────────

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.
        Returns float in [-1, 1]. Near-duplicates score ≥ 0.85.
        """
        va = np.array(a, dtype=np.float32)
        vb = np.array(b, dtype=np.float32)
        norm_a = np.linalg.norm(va)
        norm_b = np.linalg.norm(vb)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(va, vb) / (norm_a * norm_b))

    @staticmethod
    def _title_hash(title: str) -> str:
        normalized = " ".join(title.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()

    # ── Main deduplication interface ──────────────────────────────────────────

    def filter_new_articles(
        self,
        articles: List[Dict[str, Any]],
        existing_embeddings: List[Tuple[str, Optional[List[float]], str]],
        # existing_embeddings: [(article_id, embedding, url)]
        existing_urls: set,
        existing_title_hashes: set,
    ) -> List[Dict[str, Any]]:
        """
        Given a list of freshly collected articles, filter out:
          - Articles whose URL already exists in the DB
          - Articles whose embedding is too similar to a recent article

        Returns only genuinely new articles (not duplicates).
        Each returned article gets is_duplicate=False, duplicate_of=None.
        """
        new_articles: List[Dict[str, Any]] = []

        # Running list of vectors seen THIS batch (prevents in-batch duplicates)
        batch_embeddings: List[Tuple[str, List[float]]] = []

        for article in articles:
            url         = article.get("url", "")
            title       = article.get("title", "")
            embedding   = article.get("embedding")
            title_hash  = self._title_hash(title)

            # 1. Exact URL deduplication
            if url and url in existing_urls:
                logger.debug(f"[dedup] URL duplicate: {url[:60]}")
                continue

            # 2. Title hash deduplication (catches rephrased same headline)
            if title_hash in existing_title_hashes:
                logger.debug(f"[dedup] Title-hash duplicate: {title[:60]}")
                continue

            # 3. Embedding cosine similarity
            is_dup = False
            if embedding is not None:
                # Check against DB embeddings
                for _, existing_emb, _ in existing_embeddings:
                    if existing_emb is None:
                        continue
                    sim = self.cosine_similarity(embedding, existing_emb)
                    if sim >= SIMILARITY_THRESHOLD:
                        logger.debug(
                            f"[dedup] Semantic duplicate (sim={sim:.3f}): {title[:60]}"
                        )
                        is_dup = True
                        break

                if not is_dup:
                    # Check against articles already accepted THIS batch
                    for _, batch_emb in batch_embeddings:
                        sim = self.cosine_similarity(embedding, batch_emb)
                        if sim >= SIMILARITY_THRESHOLD:
                            is_dup = True
                            break

            if is_dup:
                continue

            # ── Accept this article ───────────────────────────────────────────
            article_out = {
                **article,
                "is_duplicate": False,
                "duplicate_of": None,
            }
            new_articles.append(article_out)

            # Track for within-batch dedup
            if embedding is not None:
                batch_embeddings.append((url, embedding))
            existing_urls.add(url)
            existing_title_hashes.add(title_hash)

        logger.info(
            f"[dedup] {len(articles)} articles → {len(new_articles)} new "
            f"({len(articles) - len(new_articles)} duplicates removed)"
        )
        return new_articles

    # ── DB helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def load_recent_from_db(db) -> Tuple[
        List[Tuple[str, Optional[List[float]], str]],
        set,
        set,
    ]:
        """
        Load from DB:
          - embeddings of articles published in last LOOKBACK_HOURS
          - set of all known URLs
          - set of all known title hashes

        Returns: (embeddings_list, urls_set, title_hashes_set)
        """
        from app.db.models.news_article import NewsArticle

        cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

        try:
            # Recent article embeddings (for semantic dedup)
            recent = (
                db.query(
                    NewsArticle.id,
                    NewsArticle.embedding,
                    NewsArticle.url,
                )
                .filter(NewsArticle.collected_at >= cutoff)
                .all()
            )
            embeddings = [
                (str(row.id), row.embedding, row.url or "")
                for row in recent
            ]

            # All known URLs (for exact URL dedup)
            all_urls = db.query(NewsArticle.url).all()
            url_set  = {row.url for row in all_urls if row.url}

            # All known title hashes (for near-title dedup)
            all_titles = db.query(NewsArticle.title).all()
            hash_set = {
                NewsDeduplicator._title_hash(row.title)
                for row in all_titles
                if row.title
            }

            logger.info(
                f"[dedup] DB loaded: {len(embeddings)} recent embeddings, "
                f"{len(url_set)} known URLs, {len(hash_set)} title hashes"
            )
            return embeddings, url_set, hash_set

        except Exception as e:
            logger.warning(f"[dedup] DB load failed (empty sets): {e}")
            return [], set(), set()


# Module-level singleton
deduplicator = NewsDeduplicator()
