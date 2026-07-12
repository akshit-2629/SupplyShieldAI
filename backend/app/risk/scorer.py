"""
Risk Scorer — Phase 4: Quantitative Risk Assessment

Master formula:
  risk_score = severity_score × likelihood × exposure_weight
               × geo_multiplier × industry_multiplier
               × credibility_score × 5

Clamped to [0, 100].
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("risk.scorer")

# ── Risk level thresholds ─────────────────────────────────────────────────────
RISK_LEVELS = [
    (85.0, "CRITICAL"),
    (67.0, "HIGH"),
    (33.0, "MEDIUM"),
    (0.0,  "LOW"),
]

# ── Default geo-risk multipliers by ISO country code ─────────────────────────
GEO_RISK_MAP: Dict[str, float] = {
    # East Asia — extreme semiconductor dependency
    "TW": 1.8, "CN": 1.6, "KR": 1.4, "JP": 1.3,
    # South / Southeast Asia
    "VN": 1.35, "BD": 1.3, "IN": 1.2, "PH": 1.2, "ID": 1.15, "MY": 1.15,
    # Eastern Europe / conflict zones
    "UA": 1.7, "RU": 1.6, "BY": 1.4,
    # Middle East
    "IR": 1.5, "IQ": 1.4, "YE": 1.4, "SY": 1.4, "SA": 1.2, "AE": 1.1,
    # Africa
    "CD": 1.4, "SS": 1.4, "SO": 1.4, "ET": 1.3, "NG": 1.2, "ZA": 1.1,
    # Americas
    "US": 1.0, "CA": 0.95, "MX": 1.1, "BR": 1.15,
    # Europe (stable)
    "DE": 0.9, "FR": 0.9, "GB": 0.9, "NL": 0.9, "CH": 0.85,
}

# ── Industry risk multipliers ──────────────────────────────────────────────────
INDUSTRY_RISK_MAP: Dict[str, float] = {
    "semiconductor":    1.8,
    "chip":             1.8,
    "electronics":      1.5,
    "automotive":       1.4,
    "pharmaceutical":   1.4,
    "chemicals":        1.3,
    "energy":           1.3,
    "logistics":        1.25,
    "shipping":         1.25,
    "aerospace":        1.2,
    "defense":          1.2,
    "food":             1.15,
    "agriculture":      1.1,
    "textile":          1.0,
    "retail":           0.9,
    "financial":        0.85,
}

# ── Event-type likelihood multipliers ─────────────────────────────────────────
EVENT_LIKELIHOOD_MAP: Dict[str, float] = {
    "GEOPOLITICAL":    0.75,
    "NATURAL_DISASTER": 0.85,
    "LOGISTICS":       0.80,
    "LABOR":           0.70,
    "ECONOMIC":        0.65,
    "REGULATORY":      0.55,
    "PANDEMIC":        0.90,
    "CYBER":           0.80,
}

# ── Supplier tier exposure weights ────────────────────────────────────────────
TIER_EXPOSURE: Dict[str, float] = {
    "TIER_1": 0.85,
    "TIER_2": 0.60,
    "TIER_3": 0.35,
    "UNKNOWN": 0.50,
}


class RiskScorer:
    """
    Computes a 0–100 risk score for a single news event.

    Usage:
        scorer = RiskScorer()
        result = scorer.score(news_event)
    """

    def score(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score one news event.

        Args:
            event: dict with keys from NewsAgent pipeline output

        Returns:
            dict with risk_score, risk_level, formula_components, geo_risk,
            industry_risk, supplier_dependency, confidence
        """
        # ── Inputs ────────────────────────────────────────────────────────────
        severity_score  = float(event.get("severity_score") or 0.0)
        countries       = event.get("countries") or []
        industries      = event.get("industry_tags") or event.get("industries") or []
        event_type      = (event.get("event_type") or "UNKNOWN").upper()
        credibility     = float(event.get("credibility_score") or 5.0) / 10.0  # normalise to [0,1]
        severity_label  = (event.get("severity") or "NONE").upper()

        # ── Geo multiplier (worst-case country) ───────────────────────────────
        geo_mults   = [GEO_RISK_MAP.get(c, 1.0) for c in countries] or [1.0]
        geo_mult    = max(geo_mults)
        geo_country = countries[geo_mults.index(geo_mult)] if countries else "UNKNOWN"

        # ── Industry multiplier ───────────────────────────────────────────────
        ind_mults  = [INDUSTRY_RISK_MAP.get(i.lower(), 1.0) for i in industries] or [1.0]
        ind_mult   = max(ind_mults)
        ind_name   = industries[ind_mults.index(ind_mult)] if industries else "UNKNOWN"

        # ── Likelihood (event type) ───────────────────────────────────────────
        likelihood = EVENT_LIKELIHOOD_MAP.get(event_type, 0.60)

        # ── Supplier exposure (default tier based on severity) ────────────────
        if severity_label in ("CRITICAL",):
            tier = "TIER_1"
        elif severity_label in ("HIGH",):
            tier = "TIER_2"
        else:
            tier = "TIER_3"
        exposure = TIER_EXPOSURE[tier]

        # ── Master formula ────────────────────────────────────────────────────
        raw = severity_score * likelihood * exposure * geo_mult * ind_mult * credibility * 5.0
        risk_score = round(min(max(raw, 0.0), 100.0), 2)

        # ── Confidence score ──────────────────────────────────────────────────
        has_countries  = 1.0 if countries  else 0.0
        has_industries = 1.0 if industries else 0.0
        has_event_type = 0.0 if event_type == "UNKNOWN" else 1.0
        has_entities   = 1.0 if event.get("entities") else 0.0
        conf_score = round(
            0.25 * has_countries + 0.25 * has_industries
            + 0.25 * has_event_type + 0.25 * has_entities, 3
        )
        conf_score = max(conf_score, 0.2)  # floor

        if conf_score >= 0.75:
            conf_label = "HIGH"
        elif conf_score >= 0.5:
            conf_label = "MEDIUM"
        else:
            conf_label = "LOW"

        # ── Risk level ────────────────────────────────────────────────────────
        risk_level = "LOW"
        for threshold, label in RISK_LEVELS:
            if risk_score >= threshold:
                risk_level = label
                break

        return {
            "risk_score":   risk_score,
            "risk_level":   risk_level,
            "formula_components": {
                "severity_score":  severity_score,
                "likelihood":      likelihood,
                "exposure_weight": exposure,
                "geo_multiplier":  geo_mult,
                "industry_multiplier": ind_mult,
                "credibility":     round(credibility, 3),
                "multiplier_5":    5.0,
                "raw_score":       round(raw, 4),
            },
            "geo_risk": {
                "worst_country": geo_country,
                "multiplier":    geo_mult,
                "all_countries": countries,
            },
            "industry_risk": {
                "worst_industry": ind_name,
                "multiplier":     ind_mult,
                "all_industries": industries,
            },
            "supplier_dependency": {
                "tier":           tier,
                "exposure_weight": exposure,
            },
            "confidence": {
                "score":   conf_score,
                "label":   conf_label,
                "breakdown": {
                    "has_countries":  has_countries,
                    "has_industries": has_industries,
                    "has_event_type": has_event_type,
                    "has_entities":   has_entities,
                },
            },
        }

    @staticmethod
    def level_from_score(score: float) -> str:
        for threshold, label in RISK_LEVELS:
            if score >= threshold:
                return label
        return "LOW"
