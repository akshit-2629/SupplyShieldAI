"""
NewsEmbedder — Generates dense vector representations for articles.

Model: sentence-transformers all-MiniLM-L6-v2
  • Output dimensions: 384
  • Size on disk: ~90 MB (downloaded once from HuggingFace and cached)
  • Speed: ~1000 sentences/second on CPU

The model is lazy-loaded on first call so it does NOT block FastAPI startup.

Fallback: if sentence-transformers is unavailable, returns None embeddings.
The deduplicator handles None embeddings by falling back to URL-hash comparison.
"""

from __future__ import annotations

import logging
from typing import List, Optional

logger = logging.getLogger("news.embedder")

# Lazy-loaded model — None until first call, False if unavailable
_model = None

MODEL_NAME = "all-MiniLM-L6-v2"


def _get_model():
    """Load sentence-transformers model on first call (thread-safe via GIL)."""
    global _model
    if _model is not None:
        return _model

    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"[embedder] Loading {MODEL_NAME} ...")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info(f"[embedder] {MODEL_NAME} loaded ✓  (dim={_model.get_sentence_embedding_dimension()})")
    except ImportError:
        logger.warning("[embedder] sentence-transformers not installed — deduplication disabled")
        _model = False
    except Exception as e:
        logger.warning(f"[embedder] Failed to load model: {e} — deduplication disabled")
        _model = False

    return _model


# ─────────────────────────────────────────────────────────────────────────────

class NewsEmbedder:
    """
    Generates 384-dimensional sentence embeddings for news articles.

    The embedding input is: "<title>. <first 500 chars of content>"
    Using title + lead text gives better semantic coverage than title alone.
    """

    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text string.
        Returns list[float] of length 384, or None if model unavailable.
        """
        model = _get_model()
        if not model:
            return None
        try:
            vec = model.encode(text, normalize_embeddings=True)
            return vec.tolist()
        except Exception as e:
            logger.warning(f"[embedder] embed_text error: {e}")
            return None

    def embed_article(self, article: dict) -> Optional[List[float]]:
        """
        Generate embedding for an article dict.
        Concatenates title and the first 500 characters of content.
        """
        title   = (article.get("title",   "") or "").strip()
        content = (article.get("content", "") or "").strip()[:500]
        text    = f"{title}. {content}" if content else title

        if not text.strip():
            return None
        return self.embed_text(text)

    def embed_batch(self, articles: List[dict]) -> List[dict]:
        """
        Generate embeddings for a batch of article dicts in one forward pass.
        Adds 'embedding' key to each article (in-place on a shallow copy).
        Uses batch encoding for efficiency.
        """
        model = _get_model()
        if not model:
            return [{**a, "embedding": None} for a in articles]

        texts = []
        for a in articles:
            title   = (a.get("title",   "") or "").strip()
            content = (a.get("content", "") or "").strip()[:500]
            texts.append(f"{title}. {content}" if content else title)

        try:
            vecs = model.encode(
                texts,
                batch_size=32,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return [
                {**a, "embedding": v.tolist()}
                for a, v in zip(articles, vecs)
            ]
        except Exception as e:
            logger.warning(f"[embedder] embed_batch error: {e}")
            return [{**a, "embedding": None} for a in articles]


# Module-level singleton
embedder = NewsEmbedder()
