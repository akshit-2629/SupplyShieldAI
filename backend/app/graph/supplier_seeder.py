"""
supplier_seeder.py — Automatically populates the Knowledge Graph from live supplier data.

Called by the /graph/snapshot endpoint when the graph has fewer than 5 nodes.
Converts supplier portal DB records into NetworkX nodes and edges so the
Knowledge Graph is always populated — even before the first AI workflow run.

Node types created:
  manufacturer | supplier | factory | warehouse | product | component
  country | shipment | incident

Edge types created:
  SUPPLIES | MANUFACTURES | SHIPS | STORES | LOCATED_IN | DEPENDS_ON | AFFECTED_BY
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

logger = logging.getLogger("graph.supplier_seeder")

if TYPE_CHECKING:
    import networkx as nx


def seed_from_supplier_data(G: "nx.DiGraph", db: Session) -> int:
    """
    Read live supplier portal data and upsert nodes/edges into G.
    Returns the number of nodes added.
    Safe to call repeatedly (idempotent — upsert semantics).
    """
    try:
        return _do_seed(G, db)
    except Exception as exc:
        logger.warning(f"[supplier_seeder] seed failed (non-fatal): {exc}", exc_info=True)
        return 0


def _do_seed(G, db: Session) -> int:
    from app.supplier_portal.models.company_profile import SupplierCompanyProfile
    from app.supplier_portal.models.incident import SupplierIncident
    from app.supplier_portal.models.shipment import SupplierShipment
    from app.supplier_portal.models.inventory_item import SupplierInventoryItem
    from app.supplier_portal.models.production_capacity import SupplierProductionCapacity

    added = 0

    # ── Supplier profiles ─────────────────────────────────────────────────────
    profiles = db.query(SupplierCompanyProfile).filter(
        SupplierCompanyProfile.company_name.isnot(None)
    ).limit(200).all()

    for p in profiles:
        sid = f"supplier_{p.supplier_id}"
        if not G.has_node(sid):
            G.add_node(sid,
                label=p.company_name,
                type="supplier",
                supplier_id=p.supplier_id,
                country=p.headquarters_country or "Unknown",
                city=p.headquarters_city or "",
                risk_score=0,
                status="active",
            )
            added += 1

        # ── Country node ──────────────────────────────────────────────────────
        country = (p.headquarters_country or "").strip()
        if country:
            cid = f"country_{country.replace(' ', '_').lower()}"
            if not G.has_node(cid):
                G.add_node(cid, label=country, type="country", risk_score=0)
                added += 1
            _add_edge(G, sid, cid, "LOCATED_IN")

        # ── Locations (factories + warehouses) ────────────────────────────────
        for loc in (p.locations or []):
            loc_country = loc.get("country", "")
            loc_city    = loc.get("city", "")
            loc_type    = loc.get("type", "factory")
            loc_name    = loc.get("name") or f"{loc_type.title()} ({loc_city})"
            node_type   = "factory" if "factory" in loc_type.lower() else "warehouse"
            lid         = f"{node_type}_{p.supplier_id}_{loc_city.replace(' ','_').lower()}"
            if not G.has_node(lid):
                G.add_node(lid,
                    label=loc_name, type=node_type,
                    supplier_id=p.supplier_id,
                    country=loc_country, city=loc_city,
                    risk_score=0,
                )
                added += 1
            _add_edge(G, sid, lid, "OPERATES" if node_type == "factory" else "STORES_AT")

            # Country edge for each location
            if loc_country:
                lc_id = f"country_{loc_country.replace(' ', '_').lower()}"
                if not G.has_node(lc_id):
                    G.add_node(lc_id, label=loc_country, type="country", risk_score=0)
                    added += 1
                _add_edge(G, lid, lc_id, "LOCATED_IN")

        # ── Products / Components ─────────────────────────────────────────────
        for prod in (p.products or []):
            pname = prod.get("name", "")
            psku  = prod.get("sku", "")
            if not pname:
                continue
            pid = f"product_{p.supplier_id}_{(psku or pname).replace(' ','_').lower()}"
            if not G.has_node(pid):
                G.add_node(pid,
                    label=pname, type="component",
                    sku=psku, supplier_id=p.supplier_id, risk_score=0,
                )
                added += 1
            _add_edge(G, sid, pid, "SUPPLIES")

        # ── Manufacturing categories → product type nodes ─────────────────────
        for cat in (p.manufacturing_categories or []):
            if not cat: continue
            cat_id = f"category_{cat.replace(' ','_').lower()}"
            if not G.has_node(cat_id):
                G.add_node(cat_id, label=cat, type="product", risk_score=0)
                added += 1
            _add_edge(G, sid, cat_id, "MANUFACTURES")

    # ── Active incidents ──────────────────────────────────────────────────────
    incidents = db.query(SupplierIncident).filter(
        SupplierIncident.status.in_(["open", "investigating", "OPEN", "INVESTIGATING"]),
        SupplierIncident.deleted_at.is_(None) if hasattr(SupplierIncident, "deleted_at") else True,
    ).limit(100).all()

    for inc in incidents:
        iid = f"incident_{inc.id}"
        title = getattr(inc, "title", None) or getattr(inc, "incident_type", "Incident")
        if not G.has_node(iid):
            G.add_node(iid,
                label=title, type="risk",
                incident_type=getattr(inc, "incident_type", "UNKNOWN"),
                severity=getattr(inc, "severity", "MEDIUM"),
                risk_score=_severity_to_score(getattr(inc, "severity", "MEDIUM")),
            )
            added += 1
        # Connect incident → supplier
        sid = f"supplier_{inc.supplier_id}"
        if G.has_node(sid):
            _add_edge(G, iid, sid, "AFFECTS")

    # ── Active shipments ──────────────────────────────────────────────────────
    shipments = db.query(SupplierShipment).filter(
        SupplierShipment.status.notin_(["DELIVERED", "CANCELLED"]) if hasattr(SupplierShipment, "status") else True
    ).limit(100).all()

    for sh in shipments:
        shid      = f"shipment_{sh.id}"
        ship_num  = getattr(sh, "shipment_number", str(sh.id)[:8])
        dest      = getattr(sh, "destination_country", "") or getattr(sh, "destination", "")
        if not G.has_node(shid):
            G.add_node(shid,
                label=f"Shipment {ship_num}",
                type="shipment",
                status=getattr(sh, "status", "IN_TRANSIT"),
                destination=dest,
                risk_score=20,
            )
            added += 1
        sid = f"supplier_{sh.supplier_id}"
        if G.has_node(sid):
            _add_edge(G, sid, shid, "SHIPS")
        if dest:
            dc_id = f"country_{dest.replace(' ','_').lower()}"
            if not G.has_node(dc_id):
                G.add_node(dc_id, label=dest, type="country", risk_score=0)
                added += 1
            _add_edge(G, shid, dc_id, "SHIPS_TO")

    logger.info(f"[supplier_seeder] Seeded {added} new nodes from supplier data")
    return added


def _add_edge(G, source: str, target: str, rel: str) -> None:
    """Upsert an edge — no-op if it already exists."""
    if not G.has_edge(source, target):
        G.add_edge(source, target, relationship=rel, risk_level="LOW", risk_weight=1)


def _severity_to_score(severity: str) -> float:
    return {"LOW": 25, "MEDIUM": 55, "HIGH": 80, "CRITICAL": 95}.get(
        (severity or "MEDIUM").upper(), 50
    )
