"""
Phase 5: Knowledge Graph — Real PostgreSQL Digital Twin DiGraph Builder

Constructs and maintains the NetworkX DiGraph directly from PostgreSQL database entities:
  1. Company (COMPANY)
  2. Factories (FACTORY)
  3. Warehouses (WAREHOUSE)
  4. Products (PRODUCT)
  5. Components (COMPONENT)
  6. Production Lines (PRODUCTION_LINE)
  7. Suppliers (SUPPLIER)
  8. Shipments (SHIPMENT)
  9. Incidents (INCIDENT)
  10. Recommendations (RECOMMENDATION)
  11. Documents (DOCUMENT)
  12. Quality Issues (QUALITY_ISSUE)

Edges generated automatically:
  Company -> Factory
  Company -> Warehouse
  Factory -> Product
  Product -> Component
  Component -> Supplier
  Supplier -> Shipment
  Shipment -> Incident
  Incident -> Recommendation
  Component -> Quality Issue
  Supplier -> Document
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import networkx as nx
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.manufacturer.models import (
    ManufacturerCompany,
    ManufacturerFactory,
    ManufacturerWarehouse,
    ManufacturerProduct,
    ManufacturerComponent,
    ManufacturerProductionLine,
    ManufacturerBOM,
)
from app.supplier_management.models import SupplierInvitation
from app.db.models.enterprise_incident import EnterpriseIncident
from app.db.models.recommendation import RecommendationRow
from app.supplier_portal.models.shipment import SupplierShipment
from app.supplier_portal.models.company_profile import SupplierCompanyProfile
from app.supplier_portal.models.quality_record import SupplierQualityRecord

logger = logging.getLogger("graph.builder")


class SupplyChainGraphBuilder:
    """Builds a NetworkX DiGraph representing the digital twin supply chain."""

    def build_from_db(self, db: Session, user_id: Optional[str] = None) -> nx.DiGraph:
        """
        Construct DiGraph dynamically from PostgreSQL database.
        """
        G = nx.DiGraph()
        G.graph["name"] = "SupplyShield AI — Digital Twin Supply Chain Graph"
        G.graph["version"] = "2.0.0-db"

        # 1. Fetch Company
        co_query = db.query(ManufacturerCompany)
        if user_id:
            co_query = co_query.filter(ManufacturerCompany.user_id == user_id)
        company = co_query.first()

        if not company and not user_id:
            company = db.query(ManufacturerCompany).first()

        company_user_id = company.user_id if company else user_id

        if company:
            company_node_id = f"company_{company.user_id}"
            G.add_node(
                company_node_id,
                label=company.name,
                node_type="COMPANY",
                category="Company",
                risk_score=10.0,
                risk_level="LOW",
                status="OPERATIONAL",
                country=company.country or "US",
                industry=company.industry or "Electronics Manufacturing",
                user_id=company.user_id,
                details={
                    "Name": company.name,
                    "Industry": company.industry,
                    "Headquarters": f"{company.city or ''}, {company.country or ''}",
                    "Company Size": company.company_size or "Enterprise",
                }
            )

        # 2. Fetch Factories
        factory_query = db.query(ManufacturerFactory)
        if company_user_id:
            factory_query = factory_query.filter(ManufacturerFactory.company_user_id == company_user_id)
        factories = factory_query.all()

        for f in factories:
            f_node_id = f"factory_{f.id}"
            G.add_node(
                f_node_id,
                label=f.factory_name,
                node_type="FACTORY",
                category="Factory",
                risk_score=15.0,
                risk_level="LOW",
                status=f.operating_status or "Operational",
                code=f.factory_code,
                country=f.country or "US",
                capacity=f.manufacturing_cap or "100,000/mo",
                details={
                    "Factory Name": f.factory_name,
                    "Code": f.factory_code,
                    "Type": f.factory_type or "Main Assembly",
                    "Country": f.country,
                    "Status": f.operating_status,
                }
            )

            # Edge: Company -> Factory
            if company:
                G.add_edge(f"company_{company.user_id}", f_node_id, label="OWNS", relationship="OWNS", weight=1.0)

        # 3. Fetch Warehouses
        wh_query = db.query(ManufacturerWarehouse)
        if company_user_id:
            wh_query = wh_query.filter(ManufacturerWarehouse.company_user_id == company_user_id)
        warehouses = wh_query.all()

        for w in warehouses:
            w_node_id = f"warehouse_{w.id}"
            G.add_node(
                w_node_id,
                label=w.warehouse_name,
                node_type="WAREHOUSE",
                category="Warehouse",
                risk_score=10.0,
                risk_level="LOW",
                status=w.operating_status or "Operational",
                code=w.warehouse_code,
                country=w.country or "US",
                capacity=w.storage_capacity or "50,000 sqft",
                details={
                    "Warehouse Name": w.warehouse_name,
                    "Code": w.warehouse_code,
                    "Country": w.country,
                    "Temp Controlled": "Yes" if w.temp_controlled else "No",
                }
            )

            # Edge: Company -> Warehouse
            if company:
                G.add_edge(f"company_{company.user_id}", w_node_id, label="OPERATES", relationship="OPERATES", weight=1.0)

        # 4. Fetch Products
        prod_query = db.query(ManufacturerProduct)
        if company_user_id:
            prod_query = prod_query.filter(ManufacturerProduct.company_user_id == company_user_id)
        products = prod_query.all()

        for p in products:
            p_node_id = f"product_{p.id}"
            G.add_node(
                p_node_id,
                label=p.product_name,
                node_type="PRODUCT",
                category="Product",
                risk_score=20.0,
                risk_level="LOW",
                status=p.status or "Active",
                sku=p.sku,
                volume=p.production_volume,
                details={
                    "Product Name": p.product_name,
                    "SKU": p.sku,
                    "Category": p.category,
                    "Volume": f"{p.production_volume:,}/mo" if p.production_volume else "N/A",
                }
            )

            # Edge: Company -> Product
            if company:
                G.add_edge(f"company_{company.user_id}", p_node_id, label="PRODUCES", relationship="PRODUCES", weight=1.0)
            elif factories:
                for f in factories:
                    G.add_edge(f"factory_{f.id}", p_node_id, label="PRODUCES", relationship="PRODUCES", weight=1.0)

        # 5. Fetch Components
        comp_query = db.query(ManufacturerComponent)
        if company_user_id:
            comp_query = comp_query.filter(ManufacturerComponent.company_user_id == company_user_id)
        components = comp_query.all()

        for c in components:
            c_node_id = f"component_{c.id}"
            c_risk = 80.0 if (c.criticality or "").upper() == "CRITICAL" else 30.0
            G.add_node(
                c_node_id,
                label=c.component_name,
                node_type="COMPONENT",
                category="Component",
                risk_score=c_risk,
                risk_level="HIGH" if c_risk >= 70 else "LOW",
                status="ACTIVE",
                criticality=c.criticality,
                preferred_supplier=c.preferred_supplier,
                safety_stock=c.safety_stock,
                details={
                    "Component Name": c.component_name,
                    "Category": c.category,
                    "Criticality": c.criticality,
                    "Preferred Supplier": c.preferred_supplier,
                    "Safety Stock": f"{c.safety_stock} {c.unit or 'units'}",
                }
            )

            # Note: Edges are now created via ManufacturerBOM below (not Cartesian cross-product)
            pass

        # 5b. Fetch Manufacturer BOM Records (Product -> Component relationships)
        bom_query = db.query(ManufacturerBOM)
        if company_user_id:
            bom_query = bom_query.filter(ManufacturerBOM.company_user_id == company_user_id)
        bom_items = bom_query.all()

        for bom in bom_items:
            p_node_id = f"product_{bom.product_id}"
            c_node_id = f"component_{bom.component_id}"

            if G.has_node(p_node_id) and G.has_node(c_node_id):
                G.add_edge(
                    p_node_id,
                    c_node_id,
                    label="REQUIRES",
                    relationship="REQUIRES",
                    weight=1.0,
                    quantity_required=bom.quantity_required,
                )
            else:
                logger.warning(
                    f"[graph_builder] BOM item {bom.id} references missing node: "
                    f"product_id={bom.product_id} (exists={G.has_node(p_node_id)}), "
                    f"component_id={bom.component_id} (exists={G.has_node(c_node_id)})"
                )

        # 6. Fetch Suppliers
        supp_query = db.query(SupplierInvitation)
        if company_user_id:
            supp_query = supp_query.filter(SupplierInvitation.manufacturer_user_id == company_user_id)
        suppliers = supp_query.all()

        linked_supplier_uids = []
        uid_to_supp_node = {}

        for s in suppliers:
            s_node_id = f"supplier_{s.id}"
            G.add_node(
                s_node_id,
                label=s.supplier_company_name,
                node_type="SUPPLIER",
                category="Supplier",
                risk_score=25.0,
                risk_level="LOW",
                status=s.status or "APPROVED",
                country=s.country or "KR",
                contact=s.contact_name,
                email=s.supplier_email,
                details={
                    "Supplier Name": s.supplier_company_name,
                    "Country": s.country or "US",
                    "Contact Person": s.contact_name,
                    "Email": s.supplier_email,
                    "Status": s.status,
                }
            )

            # Edge: Component -> Supplier
            for c in components:
                if c.preferred_supplier and c.preferred_supplier.lower() == s.supplier_company_name.lower():
                    G.add_edge(f"component_{c.id}", s_node_id, label="SUPPLIED_BY", relationship="SUPPLIED_BY", weight=1.0)

            # Track linked supplier UIDs for real DB entity queries
            supp_uid = s.supplier_supabase_uid or s.supplier_account_id
            if supp_uid:
                linked_supplier_uids.append(supp_uid)
                uid_to_supp_node[supp_uid] = s_node_id

            # Real Document Nodes (from SupplierCompanyProfile.documents)
            if supp_uid:
                prof = db.query(SupplierCompanyProfile).filter(SupplierCompanyProfile.supplier_id == supp_uid).first()
                if prof and prof.documents and isinstance(prof.documents, list):
                    for d in prof.documents:
                        if isinstance(d, dict):
                            raw_doc_id = d.get("doc_id") or d.get("id")
                            if not raw_doc_id:
                                logger.warning(f"[graph_builder] Skipping document without a persisted document ID in supplier profile {s.id}")
                                continue
                            d_id = str(raw_doc_id)
                            d_name = d.get("name") or d.get("title") or "Supplier Document"
                            d_type = d.get("type") or "Document"
                            doc_node_id = f"doc_{d_id}"
                            G.add_node(
                                doc_node_id,
                                label=d_name[:30],
                                node_type="DOCUMENT",
                                category="Document",
                                risk_score=0.0,
                                risk_level="LOW",
                                status="VERIFIED",
                                details={
                                    "Document Name": d_name,
                                    "Type": d_type,
                                    "Supplier": s.supplier_company_name,
                                    "Uploaded At": d.get("uploaded_at") or "N/A"
                                }
                            )
                            G.add_edge(s_node_id, doc_node_id, label="COMPLIANCE_DOC", relationship="COMPLIANCE_DOC", weight=1.0)

        # Real Shipment Nodes (from supplier_shipments table)
        if linked_supplier_uids:
            real_shipments = db.query(SupplierShipment).filter(
                SupplierShipment.supplier_id.in_(linked_supplier_uids),
                SupplierShipment.deleted_at.is_(None)
            ).all()

            for shp in real_shipments:
                shp_node_id = f"shipment_{shp.id}"
                G.add_node(
                    shp_node_id,
                    label=f"Shipment {shp.shipment_number}",
                    node_type="SHIPMENT",
                    category="Shipment",
                    risk_score=20.0 if shp.status == "DELIVERED" else 50.0,
                    risk_level="LOW" if shp.status == "DELIVERED" else "MEDIUM",
                    status=shp.status or "IN_TRANSIT",
                    details={
                        "Shipment Number": shp.shipment_number,
                        "Tracking Number": shp.tracking_number or "N/A",
                        "Carrier": shp.carrier_name or "N/A",
                        "Origin": f"{shp.origin_city or ''}, {shp.origin_country or ''}".strip(", "),
                        "Destination": f"{shp.destination_city or ''}, {shp.destination_country or ''}".strip(", "),
                        "Status": shp.status,
                    }
                )
                supp_node_id = uid_to_supp_node.get(shp.supplier_id)
                if supp_node_id and G.has_node(supp_node_id):
                    G.add_edge(supp_node_id, shp_node_id, label="DISPATCHES", relationship="DISPATCHES", weight=1.0)

        # 7. Fetch Enterprise Incidents
        inc_query = db.query(EnterpriseIncident)
        if company_user_id:
            inc_query = inc_query.filter(EnterpriseIncident.company_user_id == company_user_id)
        incidents = inc_query.limit(10).all()

        for inc in incidents:
            inc_node_id = f"incident_{inc.id}"
            G.add_node(
                inc_node_id,
                label=inc.incident_title[:45],
                node_type="INCIDENT",
                category="Incident",
                risk_score=inc.risk_score or 85.0,
                risk_level=inc.risk_level or "HIGH",
                status=inc.status or "ACTIVE",
                details={
                    "Title": inc.incident_title,
                    "Risk Score": f"{inc.risk_score}/100 ({inc.risk_level})",
                    "Financial Exposure": inc.financial_impact,
                    "Estimated Delay": inc.estimated_delay,
                    "Source": inc.news_source or "Global Intelligence Wire",
                }
            )

            # Edge: Link Incident to matched Supplier node
            for s in suppliers:
                if inc.affected_supplier and inc.affected_supplier.lower() in s.supplier_company_name.lower():
                    s_node_id = f"supplier_{s.id}"
                    if G.has_node(s_node_id):
                        G.add_edge(s_node_id, inc_node_id, label="HAS_INCIDENT", relationship="HAS_INCIDENT", weight=1.0)

        # 8. Real Recommendation Nodes (from recommendations table)
        if linked_supplier_uids:
            recs = db.query(RecommendationRow).filter(
                RecommendationRow.at_risk_supplier_id.in_(linked_supplier_uids)
            ).limit(10).all()
        else:
            recs = []

        for rec in recs:
            rec_node_id = f"recommendation_{rec.id}"
            G.add_node(
                rec_node_id,
                label=rec.procurement_action or f"Mitigation Action",
                node_type="RECOMMENDATION",
                category="Recommendation",
                risk_score=0.0,
                risk_level="LOW",
                status="RECOMMENDED",
                details={
                    "Action": rec.procurement_action or "Strategy",
                    "Supplier": rec.at_risk_supplier_name or "N/A",
                }
            )
            supp_node_id = uid_to_supp_node.get(rec.at_risk_supplier_id)
            if supp_node_id and G.has_node(supp_node_id):
                G.add_edge(supp_node_id, rec_node_id, label="HAS_RECOMMENDATION", relationship="HAS_RECOMMENDATION", weight=1.0)

        # 9. Real Quality Issue Nodes (from supplier_quality_records table)
        if linked_supplier_uids:
            q_records = db.query(SupplierQualityRecord).filter(
                SupplierQualityRecord.supplier_id.in_(linked_supplier_uids),
                SupplierQualityRecord.deleted_at.is_(None)
            ).all()

            for q in q_records:
                qi_node_id = f"quality_issue_{q.id}"
                G.add_node(
                    qi_node_id,
                    label=f"Quality Alert: {q.title[:20]}",
                    node_type="QUALITY_ISSUE",
                    category="Quality Issue",
                    risk_score=60.0 if q.severity == "CRITICAL" else 40.0,
                    risk_level=q.severity or "MEDIUM",
                    status=q.status or "OPEN",
                    details={
                        "Record Number": q.record_number,
                        "Title": q.title,
                        "Defect Rate": f"{q.defect_rate_pct}%" if q.defect_rate_pct else "N/A",
                        "Severity": q.severity,
                    }
                )
                supp_node_id = uid_to_supp_node.get(q.supplier_id)
                if supp_node_id and G.has_node(supp_node_id):
                    G.add_edge(supp_node_id, qi_node_id, label="HAS_QUALITY_RECORD", relationship="HAS_QUALITY_RECORD", weight=1.0)

        logger.info(f"[graph_builder] Built Live Digital Twin Graph from DB: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G

    def build(
        self,
        risk_assessments: Optional[List[Dict[str, Any]]] = None,
        news_events: Optional[List[Dict[str, Any]]] = None,
    ) -> nx.DiGraph:
        """Legacy fallback signature for backward compatibility."""
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            return self.build_from_db(db)
        finally:
            db.close()
