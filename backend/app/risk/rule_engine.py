"""
Risk Rule Engine — Phase 4: 12 deterministic business-logic rules.

Rules fire in priority order. Later rules can override earlier ones.
Full audit trail is stored in rule_engine_results.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("risk.rule_engine")


class RuleEngine:
    """
    Applies 12 priority-ordered rules to a risk assessment.

    Usage:
        engine = RuleEngine()
        assessment = engine.apply(assessment, event)
    """

    RULES: List[Tuple[str, Any]] = []  # populated in __init__

    def __init__(self) -> None:
        self.RULES = [
            ("P01_taiwan_semiconductor",     self._p01_taiwan_semiconductor),
            ("P02_russia_ukraine_war",        self._p02_russia_ukraine),
            ("P03_china_rare_earth",          self._p03_china_rare_earth),
            ("P04_india_china_pharma",        self._p04_india_china_pharma),
            ("P05_china_chip_controls",       self._p05_china_chip_controls),
            ("P06_major_port_closure",        self._p06_major_port_closure),
            ("P07_natural_disaster_hub",      self._p07_natural_disaster_hub),
            ("P08_multi_industry_spread",     self._p08_multi_industry_spread),
            ("P09_multi_country_spread",      self._p09_multi_country_spread),
            ("P10_force_majeure",             self._p10_force_majeure),
            ("P11_low_credibility_cap",       self._p11_low_credibility_cap),
            ("P12_low_severity_floor",        self._p12_low_severity_floor),
        ]

    def apply(self, assessment: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all rules against an assessment.

        Args:
            assessment: dict from RiskScorer.score() merged with event metadata
            event: raw news event dict

        Returns:
            Updated assessment with rule_engine_results added
        """
        title      = (event.get("title") or "").lower()
        content    = (event.get("content") or event.get("summary") or "").lower()
        text       = title + " " + content
        countries  = [c.upper() for c in (event.get("countries") or [])]
        industries = [i.lower() for i in (event.get("industry_tags") or event.get("industries") or [])]
        event_type = (event.get("event_type") or "").upper()

        fired_rules: List[Dict[str, Any]] = []
        original_score = assessment["risk_score"]
        original_level = assessment["risk_level"]

        for rule_id, rule_fn in self.RULES:
            try:
                override = rule_fn(assessment, text, countries, industries, event_type)
                if override:
                    fired_rules.append({
                        "rule_id":     rule_id,
                        "action":      override.get("action"),
                        "before_score": assessment["risk_score"],
                        "before_level": assessment["risk_level"],
                    })
                    if "risk_score" in override:
                        assessment["risk_score"] = override["risk_score"]
                    if "risk_level" in override:
                        assessment["risk_level"] = override["risk_level"]
                    fired_rules[-1]["after_score"] = assessment["risk_score"]
                    fired_rules[-1]["after_level"] = assessment["risk_level"]
            except Exception as exc:
                logger.debug(f"[rule_engine] Rule {rule_id} error: {exc}")

        assessment["rule_engine_results"] = {
            "rules_fired":     len(fired_rules),
            "original_score":  original_score,
            "original_level":  original_level,
            "final_score":     assessment["risk_score"],
            "final_level":     assessment["risk_level"],
            "fired_rules":     fired_rules,
        }
        return assessment

    # ── Individual Rules ──────────────────────────────────────────────────────

    def _p01_taiwan_semiconductor(self, a, text, countries, industries, event_type):
        if "TW" in countries and any(k in text for k in ["tsmc", "semiconductor", "chip", "strait"]):
            return {"action": "force_critical", "risk_score": max(a["risk_score"], 90.0), "risk_level": "CRITICAL"}

    def _p02_russia_ukraine(self, a, text, countries, industries, event_type):
        if any(c in countries for c in ["RU", "UA"]) and any(k in text for k in ["war", "invasion", "missile", "attack", "conflict", "sanction"]):
            return {"action": "force_critical", "risk_score": max(a["risk_score"], 88.0), "risk_level": "CRITICAL"}

    def _p03_china_rare_earth(self, a, text, countries, industries, event_type):
        if "CN" in countries and any(k in text for k in ["rare earth", "lithium", "cobalt", "embargo", "export ban", "restriction"]):
            return {"action": "force_critical", "risk_score": max(a["risk_score"], 85.0), "risk_level": "CRITICAL"}

    def _p04_india_china_pharma(self, a, text, countries, industries, event_type):
        if any(c in countries for c in ["IN", "CN"]) and any(k in industries for k in ["pharmaceutical", "drug", "api", "medicine"]):
            score = max(a["risk_score"], 70.0)
            level = "HIGH" if score < 85 else "CRITICAL"
            return {"action": "escalate_pharma", "risk_score": score, "risk_level": level}

    def _p05_china_chip_controls(self, a, text, countries, industries, event_type):
        if "CN" in countries and any(k in text for k in ["export control", "chip ban", "technology restriction", "semiconductor sanction"]):
            return {"action": "escalate_high", "risk_score": max(a["risk_score"], 75.0), "risk_level": "HIGH" if a["risk_score"] < 85 else "CRITICAL"}

    def _p06_major_port_closure(self, a, text, countries, industries, event_type):
        port_keywords = ["port closure", "port strike", "shipping halt", "logistics disruption", "suez", "rotterdam", "shanghai port", "los angeles port"]
        if event_type in ("LOGISTICS", "LABOR") and any(k in text for k in port_keywords):
            return {"action": "escalate_high", "risk_score": max(a["risk_score"], 72.0), "risk_level": "HIGH" if a["risk_score"] < 85 else "CRITICAL"}

    def _p07_natural_disaster_hub(self, a, text, countries, industries, event_type):
        hubs = ["TW", "JP", "VN", "BD", "KR", "CN"]
        if event_type == "NATURAL_DISASTER" and any(c in countries for c in hubs):
            new_score = min(a["risk_score"] * 1.25, 100.0)
            from app.risk.scorer import RiskScorer
            return {"action": "escalate_disaster_hub", "risk_score": round(new_score, 2), "risk_level": RiskScorer.level_from_score(new_score)}

    def _p08_multi_industry_spread(self, a, text, countries, industries, event_type):
        if len(industries) >= 3:
            new_score = min(a["risk_score"] + 10.0, 100.0)
            from app.risk.scorer import RiskScorer
            return {"action": "multi_industry_bonus", "risk_score": round(new_score, 2), "risk_level": RiskScorer.level_from_score(new_score)}

    def _p09_multi_country_spread(self, a, text, countries, industries, event_type):
        if len(countries) >= 4:
            new_score = min(a["risk_score"] + 8.0, 100.0)
            from app.risk.scorer import RiskScorer
            return {"action": "multi_country_bonus", "risk_score": round(new_score, 2), "risk_level": RiskScorer.level_from_score(new_score)}

    def _p10_force_majeure(self, a, text, countries, industries, event_type):
        fm_keywords = ["force majeure", "act of god", "catastrophic", "unprecedented disaster"]
        if any(k in text for k in fm_keywords):
            return {"action": "force_majeure_critical", "risk_score": max(a["risk_score"], 90.0), "risk_level": "CRITICAL"}

    def _p11_low_credibility_cap(self, a, text, countries, industries, event_type):
        conf_score = a.get("confidence", {}).get("score", 1.0)
        if conf_score < 0.3 and a["risk_level"] in ("LOW", "MEDIUM"):
            capped = min(a["risk_score"], 50.0)
            return {"action": "cap_low_confidence", "risk_score": capped, "risk_level": "LOW" if capped < 33 else "MEDIUM"}

    def _p12_low_severity_floor(self, a, text, countries, industries, event_type):
        if a.get("formula_components", {}).get("severity_score", 1.0) < 1.0:
            return {"action": "force_low", "risk_score": min(a["risk_score"], 25.0), "risk_level": "LOW"}
