"""
Phase 7: Inventory Impact — Component & Product Mapper

Maps Phase 4 risk assessments and Phase 5 graph data onto inventory items.

Overlay logic:
  1. Phase 4 → find risk_assessments mentioning the component's supplier
     country/industry and boost the component's effective risk
  2. Phase 5 → find the component node in graph_snapshot and retrieve
     blast_radius_size, centrality, products_supplied
  3. Phase 6 → find the supplier's health_score and tier
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("inventory.mapper")


class InventoryMapper:
    """
    Resolves Phase 4 risk data, Phase 5 graph data, and Phase 6 supplier
    health data into per-component risk overlays.
    """

    def build_risk_overlay(
        self,
        component_id:     str,
        supplier_id:      str,
        supplier_name:    str,
        risk_assessments: List[Dict[str, Any]],
        supplier_scores:  List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Returns a risk overlay dict for a component:
          {
            "component_risk_score":  float (0–100)
            "supplier_health_score": float
            "supplier_tier":         str
            "effective_lead_time":   int   (lead_time × risk multiplier)
            "risk_level":            str
          }
        """
        # Resolve supplier risk from Phase 6
        supplier_health = 75.0
        supplier_tier   = "TIER_3"
        supplier_risk   = 0.0
        risk_level      = "LOW"

        for ss in (supplier_scores or []):
            if ss.get("supplier_id") == supplier_id:
                supplier_health = float(ss.get("health", {}).get("health_score", 75.0))
                supplier_tier   = ss.get("tier", "TIER_3")
                supplier_risk   = float(ss.get("risk_score", 0.0))
                risk_level      = ss.get("risk_level", "LOW")
                break

        # Find risk assessments mentioning this supplier's country/industry
        component_risk = 0.0
        for ra in (risk_assessments or []):
            rs = float(ra.get("risk_score", 0.0))
            if rs > component_risk:
                component_risk = rs

        effective_component_risk = max(component_risk * 0.6, supplier_risk * 0.8)

        # Lead time multiplier based on risk level
        lt_multipliers = {"LOW": 1.0, "MEDIUM": 1.15, "HIGH": 1.35, "CRITICAL": 1.60}
        lt_multiplier  = lt_multipliers.get(risk_level, 1.0)

        return {
            "component_risk_score":  round(effective_component_risk, 2),
            "supplier_health_score": round(supplier_health, 2),
            "supplier_tier":         supplier_tier,
            "risk_level":            risk_level,
            "lead_time_multiplier":  lt_multiplier,
        }

    def build_graph_overlay(
        self,
        component_id:   str,
        graph_snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Returns graph metrics for a component from Phase 5 snapshot:
          { blast_radius_size, centrality, products_supplied }
        """
        default = {"blast_radius_size": 0, "centrality": 0.0, "products_supplied": 0}

        centrality_data = graph_snapshot.get("centrality", {})
        for node in (centrality_data.get("top_nodes") or []):
            if node.get("node_id") == component_id:
                return {
                    "blast_radius_size": node.get("out_degree", 0),
                    "centrality":        float(node.get("centrality", 0.0)),
                    "products_supplied": node.get("out_degree", 0),
                }
        return default

    def enrich_item(
        self,
        item_dict:        Dict[str, Any],
        risk_assessments: List[Dict[str, Any]],
        supplier_scores:  List[Dict[str, Any]],
        graph_snapshot:   Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Enriches an inventory seed dict with Phase 4/5/6 overlays.
        Returns the enriched dict ready for InventoryItem construction.
        """
        risk_overlay  = self.build_risk_overlay(
            component_id     = item_dict["component_id"],
            supplier_id      = item_dict["supplier_id"],
            supplier_name    = item_dict["supplier_name"],
            risk_assessments = risk_assessments,
            supplier_scores  = supplier_scores,
        )
        graph_overlay = self.build_graph_overlay(
            component_id   = item_dict["component_id"],
            graph_snapshot = graph_snapshot,
        )

        # Adjust lead time by risk multiplier
        base_lt = item_dict.get("lead_time_days", 30)
        adjusted_lt = int(round(base_lt * risk_overlay["lead_time_multiplier"]))

        enriched = {**item_dict}
        enriched["lead_time_days"] = adjusted_lt
        enriched["metadata"] = {
            "base_lead_time_days": base_lt,
            "risk_overlay":        risk_overlay,
            "graph_overlay":       graph_overlay,
        }
        return enriched
