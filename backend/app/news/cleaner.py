"""
NewsArticleCleaner — HTML stripping and text normalization.

Steps:
  1. Parse HTML with BeautifulSoup + lxml (falls back to html.parser)
  2. Remove script, style, navigation, and ad elements
  3. Extract visible text
  4. Normalize whitespace and Unicode
  5. Limit content to MAX_CONTENT_CHARS to cap memory/DB usage
"""

from __future__ import annotations

import re
import unicodedata
import logging
from typing import Optional

logger = logging.getLogger("news.cleaner")

MAX_CONTENT_CHARS = 5_000   # Store at most 5 k chars of body text
MAX_TITLE_CHARS   = 500


class NewsArticleCleaner:
    """Cleans raw HTML articles into plain text."""

    # Tags whose entire subtree we discard
    _DISCARD_TAGS = {
        "script", "style", "nav", "header", "footer",
        "aside", "noscript", "iframe", "form", "button",
        "svg", "img", "figure", "figcaption", "ad",
    }

    def clean_article(self, article: dict) -> dict:
        """
        Return a copy of article with title and content cleaned.
        The original dict is NOT mutated.
        """
        cleaned = dict(article)
        cleaned["title"]   = self._clean_text(article.get("title",   "") or "", MAX_TITLE_CHARS)
        cleaned["content"] = self._clean_html(article.get("content", "") or "", MAX_CONTENT_CHARS)
        return cleaned

    # ── HTML cleaning ─────────────────────────────────────────────────────────

    def _clean_html(self, raw: str, max_chars: int) -> str:
        if not raw or not raw.strip():
            return ""

        # Try BeautifulSoup with lxml, fall back to html.parser
        try:
            from bs4 import BeautifulSoup as _BS
            _bs_available = True
        except ImportError:
            _bs_available = False

        if _bs_available:
            try:
                soup = _BS(raw, "lxml")
            except Exception:
                try:
                    soup = _BS(raw, "html.parser")
                except Exception:
                    return self._strip_tags_regex(raw)[:max_chars]

            # Remove unwanted subtrees
            for tag in soup.find_all(self._DISCARD_TAGS):
                tag.decompose()

            text = soup.get_text(separator=" ", strip=True)
        else:
            text = self._strip_tags_regex(raw)

        return self._clean_text(text, max_chars)

    def _strip_tags_regex(self, html: str) -> str:
        """Fast fallback: remove HTML tags with regex."""
        return re.sub(r"<[^>]+>", " ", html)

    # ── Text normalization ────────────────────────────────────────────────────

    def _clean_text(self, text: str, max_chars: int) -> str:
        if not text:
            return ""

        # Normalize Unicode to NFC (e.g., combining characters → composed)
        text = unicodedata.normalize("NFC", text)

        # Collapse multiple whitespace (spaces, tabs, newlines) to single space
        text = re.sub(r"[\r\n\t]+",    " ", text)
        text = re.sub(r" {2,}",        " ", text)

        # Remove null bytes and other control characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        text = text.strip()
        return text[:max_chars]


# Module-level singleton
cleaner = NewsArticleCleaner()
