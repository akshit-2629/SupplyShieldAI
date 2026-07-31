"""
EnterpriseIncident ORM Model — Structured Supply Chain Incident Record

Maps to PostgreSQL table 'enterprise_incidents'.
Stores full enterprise risk evaluation generated from news, supplier matching,
component matching, factory matching, shipment matching, and inventory impact.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, JSON, DateTime, ForeignKey
from app.db.models.base import Base

class EnterpriseIncident(Base):
    __tablename__ = "enterprise_incidents"

    id                   = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_user_id      = Column(String, ForeignKey("manufacturer_companies.user_id", ondelete="CASCADE"), nullable=True, index=True)
    
    # News Traceability Link
    news_article_id      = Column(String, nullable=True, index=True)
    news_title           = Column(String(2000), nullable=True)
    news_url             = Column(String(2048), nullable=True)
    news_source          = Column(String(250), nullable=True)

    # Core Incident Metadata
    incident_title       = Column(String(500), nullable=False)
    incident_description = Column(Text, nullable=False)
    
    # Matched Supply Chain Entities
    affected_supplier    = Column(String(500), nullable=True)
    affected_factory     = Column(String(500), nullable=True)
    affected_components  = Column(JSON, nullable=True)   # List[str]
    affected_products    = Column(JSON, nullable=True)   # List[str]
    affected_inventory   = Column(String(500), nullable=True)
    affected_shipment    = Column(String(500), nullable=True)

    # Quantitative & Qualitative Risk Metrics
    risk_score           = Column(Float, default=0.0)
    risk_level           = Column(String(50), default="MEDIUM", index=True)
    business_impact      = Column(Text, nullable=True)
    financial_impact     = Column(String(250), nullable=True)
    estimated_delay      = Column(String(250), nullable=True)
    confidence           = Column(String(250), nullable=True)
    root_cause           = Column(Text, nullable=True)

    # Actionable Decision Support
    recommended_actions  = Column(JSON, nullable=True)   # List[Dict[str, str]] or List[str]
    alternative_suppliers = Column(JSON, nullable=True)  # List[Dict[str, str]] or List[str]
    recovery_plan        = Column(Text, nullable=True)
    timeline             = Column(JSON, nullable=True)   # List[Dict[str, str]]
    
    # Lifecycle Status
    status               = Column(String(50), default="ACTIVE", index=True)  # ACTIVE, UNDER_INVESTIGATION, MITIGATED, RESOLVED

    created_at           = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at           = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
