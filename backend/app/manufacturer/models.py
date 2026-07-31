"""
app/manufacturer/models.py — SQLAlchemy ORM models for the manufacturer onboarding module.

5 tables:
  ManufacturerCompany      → manufacturer_companies
  ManufacturerFactory      → manufacturer_factories
  ManufacturerWarehouse    → manufacturer_warehouses
  ManufacturerProduct      → manufacturer_products
  ManufacturerComponent    → manufacturer_components
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, ForeignKey,
    Integer, Numeric, SmallInteger, String, Text, func,
    UniqueConstraint, TypeDecorator,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped

from app.db.models.base import Base


class JSONList(TypeDecorator):
    """
    Stores a Python list as a JSON string in any dialect (SQLite, PostgreSQL).
    Avoids using PostgreSQL-only ARRAY so that tests running on SQLite do not fail.
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return []


class ManufacturerCompany(Base):
    """
    Root entity for a manufacturer.  Primary key is the Supabase auth.uid()
    string so we never need a separate lookup table.
    """
    __tablename__ = "manufacturer_companies"

    user_id              = Column(String,   primary_key=True)
    name                 = Column(String,   nullable=False)
    industry             = Column(String,   nullable=False, default="Electronics Manufacturing")
    description          = Column(Text)

    # Location
    country              = Column(String,   nullable=False)
    state                = Column(String)
    city                 = Column(String)
    address              = Column(Text)

    # Contact
    website              = Column(String)
    business_email       = Column(String)
    business_phone       = Column(String)
    logo_url             = Column(String)

    # Size
    company_size         = Column(String)
    annual_production_cap = Column(String)

    # Legal
    registration_number  = Column(String)
    tax_number           = Column(String)

    # Operational
    timezone             = Column(String,   nullable=False, default="Asia/Kolkata")
    working_days         = Column(ARRAY(Text).with_variant(JSONList, "sqlite"))  # PostgreSQL TEXT[] with SQLite fallback
    working_hours_start  = Column(String,   nullable=False, default="09:00")
    working_hours_end    = Column(String,   nullable=False, default="18:00")

    # Onboarding
    onboarding_complete  = Column(Boolean,  nullable=False, default=False)
    onboarding_step      = Column(SmallInteger, nullable=False, default=1)

    # Timestamps
    created_at           = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at           = Column(DateTime(timezone=True), server_default=func.now(),
                                  onupdate=func.now(), nullable=False)

    # Relationships
    factories   = relationship("ManufacturerFactory",   back_populates="company",
                               cascade="all, delete-orphan", lazy="dynamic")
    warehouses  = relationship("ManufacturerWarehouse", back_populates="company",
                               cascade="all, delete-orphan", lazy="dynamic")
    products    = relationship("ManufacturerProduct",   back_populates="company",
                               cascade="all, delete-orphan", lazy="dynamic")
    components  = relationship("ManufacturerComponent", back_populates="company",
                               cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<ManufacturerCompany user_id={self.user_id!r} name={self.name!r}>"


class ManufacturerFactory(Base):
    __tablename__ = "manufacturer_factories"
    __table_args__ = (
        UniqueConstraint("company_user_id", "factory_code", name="uq_mfr_factory_code"),
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_user_id = Column(String, ForeignKey("manufacturer_companies.user_id",
                                                ondelete="CASCADE"), nullable=False)
    factory_name    = Column(String, nullable=False)
    factory_code    = Column(String, nullable=False)
    factory_type    = Column(String, nullable=False, default="Assembly")
    country         = Column(String, nullable=False)
    state           = Column(String)
    city            = Column(String)
    address         = Column(Text)
    latitude        = Column(Numeric(10, 6))
    longitude       = Column(Numeric(10, 6))
    manufacturing_cap = Column(String)
    operating_status  = Column(String, nullable=False, default="Operational")
    factory_manager   = Column(String)
    contact_number    = Column(String)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(),
                             onupdate=func.now(), nullable=False)

    company = relationship("ManufacturerCompany", back_populates="factories")

    def __repr__(self) -> str:
        return f"<ManufacturerFactory {self.factory_name!r} ({self.factory_code})>"


class ManufacturerWarehouse(Base):
    __tablename__ = "manufacturer_warehouses"
    __table_args__ = (
        UniqueConstraint("company_user_id", "warehouse_code", name="uq_mfr_warehouse_code"),
    )

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_user_id  = Column(String, ForeignKey("manufacturer_companies.user_id",
                                                 ondelete="CASCADE"), nullable=False)
    warehouse_name   = Column(String, nullable=False)
    warehouse_code   = Column(String, nullable=False)
    country          = Column(String, nullable=False)
    state            = Column(String)
    city             = Column(String)
    address          = Column(Text)
    latitude         = Column(Numeric(10, 6))
    longitude        = Column(Numeric(10, 6))
    storage_capacity = Column(String)
    operating_status = Column(String, nullable=False, default="Operational")
    temp_controlled  = Column(Boolean, nullable=False, default=False)
    warehouse_manager = Column(String)
    contact_number   = Column(String)
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(),
                              onupdate=func.now(), nullable=False)

    company = relationship("ManufacturerCompany", back_populates="warehouses")

    def __repr__(self) -> str:
        return f"<ManufacturerWarehouse {self.warehouse_name!r}>"


class ManufacturerProduct(Base):
    __tablename__ = "manufacturer_products"
    __table_args__ = (
        UniqueConstraint("company_user_id", "sku", name="uq_mfr_product_sku"),
    )

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_user_id   = Column(String, ForeignKey("manufacturer_companies.user_id",
                                                  ondelete="CASCADE"), nullable=False)
    product_name      = Column(String, nullable=False)
    sku               = Column(String, nullable=False)
    category          = Column(String, nullable=False, default="Electronics")
    model_number      = Column(String)
    description       = Column(Text)
    production_volume = Column(Integer)
    status            = Column(String, nullable=False, default="Active")
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at        = Column(DateTime(timezone=True), server_default=func.now(),
                               onupdate=func.now(), nullable=False)

    company    = relationship("ManufacturerCompany",   back_populates="products")
    components = relationship("ManufacturerComponent", back_populates="product",
                              cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<ManufacturerProduct {self.product_name!r} sku={self.sku!r}>"


class ManufacturerComponent(Base):
    __tablename__ = "manufacturer_components"
    __table_args__ = (
        CheckConstraint("criticality IN ('Low','Medium','High','Critical')",
                        name="ck_mfr_component_criticality"),
    )

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_user_id   = Column(String, ForeignKey("manufacturer_companies.user_id",
                                                  ondelete="CASCADE"), nullable=False)
    product_id        = Column(UUID(as_uuid=True), ForeignKey("manufacturer_products.id",
                                                              ondelete="SET NULL"), nullable=True)
    component_name    = Column(String, nullable=False)
    category          = Column(String, nullable=False, default="Electronic")
    criticality       = Column(String, nullable=False, default="Medium")
    preferred_supplier = Column(String)
    safety_stock      = Column(Integer, nullable=False, default=0)
    unit              = Column(String, nullable=False, default="units")
    avg_monthly_usage = Column(Integer)
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at        = Column(DateTime(timezone=True), server_default=func.now(),
                               onupdate=func.now(), nullable=False)

    company = relationship("ManufacturerCompany", back_populates="components")
    product = relationship("ManufacturerProduct", back_populates="components")

    def __repr__(self) -> str:
        return f"<ManufacturerComponent {self.component_name!r} criticality={self.criticality!r}>"


class ManufacturerProductionLine(Base):
    __tablename__ = "manufacturer_production_lines"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_user_id   = Column(String, ForeignKey("manufacturer_companies.user_id",
                                                  ondelete="CASCADE"), nullable=False)
    factory_id        = Column(UUID(as_uuid=True), ForeignKey("manufacturer_factories.id",
                                                              ondelete="CASCADE"), nullable=True)
    line_name         = Column(String, nullable=False)
    line_code         = Column(String, nullable=False)
    capacity_per_hour = Column(Integer, nullable=False, default=100)
    operating_status  = Column(String, nullable=False, default="Operational")
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at        = Column(DateTime(timezone=True), server_default=func.now(),
                               onupdate=func.now(), nullable=False)

    factory = relationship("ManufacturerFactory")


class ManufacturerBOM(Base):
    __tablename__ = "manufacturer_bom_items"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_user_id   = Column(String, ForeignKey("manufacturer_companies.user_id",
                                                  ondelete="CASCADE"), nullable=False)
    product_id        = Column(UUID(as_uuid=True), ForeignKey("manufacturer_products.id",
                                                              ondelete="CASCADE"), nullable=False)
    component_id      = Column(UUID(as_uuid=True), ForeignKey("manufacturer_components.id",
                                                              ondelete="CASCADE"), nullable=False)
    quantity_required = Column(Integer, nullable=False, default=1)
    notes             = Column(Text)
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at        = Column(DateTime(timezone=True), server_default=func.now(),
                               onupdate=func.now(), nullable=False)

    product   = relationship("ManufacturerProduct")
    component = relationship("ManufacturerComponent")
