"""
NewsArticleExtractor — NLP-powered metadata extraction.

Extracts the following from article title + content:
  • entities:       organizations, people, locations (via spaCy with keyword fallback)
  • country_codes:  ISO 3166-1 alpha-2 codes (via country keyword map + spaCy GPE)
  • industry_tags:  up to 5 matched industry categories
  • severity:       CRITICAL / HIGH / MEDIUM / LOW / NONE (weighted keyword scoring)
  • severity_score: continuous float 0–10
  • event_type:     GEOPOLITICAL / NATURAL_DISASTER / LABOR / REGULATORY /
                    LOGISTICS / ECONOMIC / PANDEMIC (keyword category matching)
  • is_disruption:  True when severity is MEDIUM, HIGH, or CRITICAL

Algorithms:
  - Weighted Keyword Scoring: count(keywords_in_tier) × tier_weight → severity_score
  - Top-score wins: highest-scoring tier sets the severity label
  - Event type: category with most keyword matches wins (ties → first match)
  - NLP entities: spaCy NER with graceful fallback to keyword matching
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from app.news.sources import (
    COUNTRY_KEYWORDS,
    EVENT_TYPE_KEYWORDS,
    INDUSTRY_KEYWORDS,
    SEVERITY_KEYWORDS,
)

logger = logging.getLogger("news.extractor")

# ── spaCy lazy loader ─────────────────────────────────────────────────────────

_nlp = None


def _get_nlp():
    """Lazy-load spaCy model. Returns None if unavailable (fallback mode)."""
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy
        try:
            _nlp = spacy.load("en_core_web_sm")
            logger.info("[extractor] spaCy en_core_web_sm loaded ✓")
        except OSError:
            _nlp = spacy.blank("en")
            logger.warning("[extractor] en_core_web_sm not found — using blank spaCy (reduced NER)")
    except ModuleNotFoundError:
        logger.warning("[extractor] spaCy not installed — using keyword-only entity extraction")
        _nlp = False  # Sentinel: spaCy unavailable
    return _nlp


class NewsArticleExtractor:
    """Enriches a cleaned article dict with NLP metadata."""

    def enrich(self, article: dict) -> dict:
        """
        Return a copy of article with all metadata fields added.
        The original dict is NOT mutated.
        """
        enriched = dict(article)

        title   = article.get("title",   "") or ""
        content = article.get("content", "") or ""
        text    = f"{title}. {content}"

        enriched["entities"]      = self._extract_entities(text)
        enriched["country_codes"] = self._extract_countries(text)
        enriched["industry_tags"] = self._extract_industries(text)

        severity, score           = self._score_severity(text)
        enriched["severity"]      = severity
        enriched["severity_score"] = score
        enriched["event_type"]    = self._classify_event_type(text)
        enriched["is_disruption"] = severity in {"CRITICAL", "HIGH", "MEDIUM"}

        return enriched

    # ── Severity scoring (Weighted Keyword Algorithm) ──────────────────────────

    def _score_severity(self, text: str) -> Tuple[str, float]:
        """
        Compute severity score: Σ(keyword_match × tier_weight) per tier.
        Returns (severity_label, continuous_score 0-10).
        """
        lower = text.lower()
        best_label = "NONE"
        best_score = 0.0

        for tier, cfg in SEVERITY_KEYWORDS.items():
            tier_weight = cfg["score"]
            matches = sum(1 for kw in cfg["keywords"] if kw in lower)
            if matches == 0:
                continue
            # Diminishing returns: log(1+matches) keeps score bounded
            import math
            raw = tier_weight * math.log1p(matches)
            score = min(10.0, round(raw, 2))

            if score > best_score:
                best_score = score
                best_label = tier

        return best_label, best_score

    # ── Event type classification ─────────────────────────────────────────────

    def _classify_event_type(self, text: str) -> Optional[str]:
        """Returns the event type with the most keyword hits, or None."""
        lower = text.lower()
        counts: Dict[str, int] = {}

        for event_type, keywords in EVENT_TYPE_KEYWORDS.items():
            counts[event_type] = sum(1 for kw in keywords if kw in lower)

        if not counts:
            return None

        best = max(counts, key=lambda k: counts[k])
        return best if counts[best] > 0 else None

    # ── Industry detection ────────────────────────────────────────────────────

    def _extract_industries(self, text: str) -> List[str]:
        """Returns matched industry categories (up to 5)."""
        lower = text.lower()
        matched = [
            industry
            for industry, keywords in INDUSTRY_KEYWORDS.items()
            if any(kw.lower() in lower for kw in keywords)
        ]
        return matched[:5]

    # ── Country detection ─────────────────────────────────────────────────────

    def _extract_countries(self, text: str) -> List[str]:
        """
        Returns unique ISO country codes from:
        1. COUNTRY_KEYWORDS map (keyword matching)
        2. spaCy GPE entities (geographic-political entities)
        """
        codes: set = set()

        # Keyword map matching
        for name, code in COUNTRY_KEYWORDS.items():
            if name.lower() in text.lower():
                codes.add(code)

        # spaCy GPE extraction
        nlp = _get_nlp()
        if nlp and nlp is not False:
            try:
                doc = nlp(text[:3000])
                for ent in doc.ents:
                    if ent.label_ in {"GPE", "LOC"}:
                        # Match entity text back through keyword map
                        ent_text = ent.text.strip()
                        for name, code in COUNTRY_KEYWORDS.items():
                            if name.lower() == ent_text.lower():
                                codes.add(code)
            except Exception as e:
                logger.debug(f"[extractor] spaCy GPE extraction error: {e}")

        return list(codes)[:10]

    # ── NLP Entity extraction ─────────────────────────────────────────────────

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Returns {organizations, people, locations} lists.
        Primary: spaCy NER. Fallback: keyword scan from INDUSTRY_KEYWORDS.
        """
        entities: Dict[str, List[str]] = {
            "organizations": [],
            "people":        [],
            "locations":     [],
        }

        nlp = _get_nlp()

        if nlp and nlp is not False:
            try:
                doc = nlp(text[:5000])
                for ent in doc.ents:
                    label = ent.label_
                    ent_text = ent.text.strip()
                    if not ent_text or len(ent_text) < 2:
                        continue
                    if label == "ORG":
                        entities["organizations"].append(ent_text)
                    elif label == "PERSON":
                        entities["people"].append(ent_text)
                    elif label in {"GPE", "LOC", "FAC"}:
                        entities["locations"].append(ent_text)
            except Exception as e:
                logger.debug(f"[extractor] spaCy NER error: {e}")

        # Fallback: extract known org names from industry keywords
        if not entities["organizations"]:
            known_orgs = [
                "TSMC", "Intel", "Samsung", "Nvidia", "AMD", "Ford", "Toyota",
                "Tesla", "Maersk", "DHL", "FedEx", "UPS", "Amazon", "Walmart",
                "OPEC", "FDA", "WHO", "WTO",
            ]
            lower = text.lower()
            entities["organizations"] = [
                org for org in known_orgs if org.lower() in lower
            ]

        # Deduplicate and limit
        return {
            key: list(dict.fromkeys(vals))[:20]
            for key, vals in entities.items()
        }


# Module-level singleton
extractor = NewsArticleExtractor()
