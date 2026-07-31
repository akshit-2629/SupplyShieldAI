"""
app/manufacturer/schemas.py — Pydantic request/response schemas for the
manufacturer onboarding wizard.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# ══════════════════════════════════════════════════════════════════════════════
# Shared base
# ══════════════════════════════════════════════════════════════════════════════

class OKResponse(BaseModel):
    success: bool = True
    message: str


class SetupStatusResponse(BaseModel):
    complete:      bool
    current_step:  int
    company_exists: bool


# ══════════════════════════════════════════════════════════════════════════════
# Company
# ══════════════════════════════════════════════════════════════════════════════

class CompanyCreate(BaseModel):
    name:                  str                  = Field(..., min_length=2, max_length=200)
    industry:              str                  = Field(default="Electronics Manufacturing")
    description:           Optional[str]        = None
    country:               str                  = Field(..., min_length=2)
    state:                 Optional[str]        = None
    city:                  Optional[str]        = None
    address:               Optional[str]        = None
    website:               Optional[str]        = None
    business_email:        Optional[str]        = None
    business_phone:        Optional[str]        = None
    logo_url:              Optional[str]        = None
    company_size:          Optional[str]        = None
    annual_production_cap: Optional[str]        = None
    registration_number:   Optional[str]        = None
    tax_number:            Optional[str]        = None
    timezone:              str                  = Field(default="Asia/Kolkata")
    working_days:          Optional[List[str]]  = None
    working_hours_start:   str                  = Field(default="09:00")
    working_hours_end:     str                  = Field(default="18:00")
    onboarding_step:       int                  = Field(default=1, ge=1, le=7)


class CompanyUpdate(CompanyCreate):
    # All fields optional on update
    name:    Optional[str] = None  # type: ignore[assignment]
    country: Optional[str] = None  # type: ignore[assignment]


class CompanyResponse(BaseModel):
    user_id:               str
    name:                  str
    industry:              str
    description:           Optional[str]
    country:               str
    state:                 Optional[str]
    city:                  Optional[str]
    address:               Optional[str]
    website:               Optional[str]
    business_email:        Optional[str]
    business_phone:        Optional[str]
    logo_url:              Optional[str]
    company_size:          Optional[str]
    annual_production_cap: Optional[str]
    registration_number:   Optional[str]
    tax_number:            Optional[str]
    timezone:              str
    working_days:          Optional[List[str]]
    working_hours_start:   str
    working_hours_end:     str
    onboarding_complete:   bool
    onboarding_step:       int
    created_at:            datetime
    updated_at:            datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Factory
# ══════════════════════════════════════════════════════════════════════════════

class FactoryCreate(BaseModel):
    factory_name:      str           = Field(..., min_length=1, max_length=200)
    factory_code:      str           = Field(..., min_length=1, max_length=50)
    factory_type:      str           = Field(default="Assembly")
    country:           str           = Field(..., min_length=2)
    state:             Optional[str] = None
    city:              Optional[str] = None
    address:           Optional[str] = None
    latitude:          Optional[float] = Field(None, ge=-90, le=90)
    longitude:         Optional[float] = Field(None, ge=-180, le=180)
    manufacturing_cap: Optional[str] = None
    operating_status:  str           = Field(default="Operational")
    factory_manager:   Optional[str] = None
    contact_number:    Optional[str] = None


class FactoryUpdate(FactoryCreate):
    factory_name: Optional[str] = None  # type: ignore[assignment]
    factory_code: Optional[str] = None  # type: ignore[assignment]
    country:      Optional[str] = None  # type: ignore[assignment]


class FactoryResponse(FactoryCreate):
    id:              UUID
    company_user_id: str
    created_at:      datetime
    updated_at:      datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Warehouse
# ══════════════════════════════════════════════════════════════════════════════

class WarehouseCreate(BaseModel):
    warehouse_name:    str            = Field(..., min_length=1, max_length=200)
    warehouse_code:    str            = Field(..., min_length=1, max_length=50)
    country:           str            = Field(..., min_length=2)
    state:             Optional[str]  = None
    city:              Optional[str]  = None
    address:           Optional[str]  = None
    latitude:          Optional[float] = Field(None, ge=-90, le=90)
    longitude:         Optional[float] = Field(None, ge=-180, le=180)
    storage_capacity:  Optional[str]  = None
    operating_status:  str            = Field(default="Operational")
    temp_controlled:   bool           = False
    warehouse_manager: Optional[str]  = None
    contact_number:    Optional[str]  = None


class WarehouseUpdate(WarehouseCreate):
    warehouse_name: Optional[str] = None  # type: ignore[assignment]
    warehouse_code: Optional[str] = None  # type: ignore[assignment]
    country:        Optional[str] = None  # type: ignore[assignment]


class WarehouseResponse(WarehouseCreate):
    id:              UUID
    company_user_id: str
    created_at:      datetime
    updated_at:      datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Product
# ══════════════════════════════════════════════════════════════════════════════

class ProductCreate(BaseModel):
    product_name:      str            = Field(..., min_length=1, max_length=200)
    sku:               str            = Field(..., min_length=1, max_length=100)
    category:          str            = Field(default="Electronics")
    model_number:      Optional[str]  = None
    description:       Optional[str]  = None
    production_volume: Optional[int]  = Field(None, ge=0)
    status:            str            = Field(default="Active")


class ProductUpdate(ProductCreate):
    product_name: Optional[str] = None  # type: ignore[assignment]
    sku:          Optional[str] = None  # type: ignore[assignment]


class ProductResponse(ProductCreate):
    id:              UUID
    company_user_id: str
    created_at:      datetime
    updated_at:      datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Component
# ══════════════════════════════════════════════════════════════════════════════

VALID_CRITICALITY = {"Low", "Medium", "High", "Critical"}

class ComponentCreate(BaseModel):
    product_id:         Optional[UUID] = None
    component_name:     str            = Field(..., min_length=1, max_length=200)
    category:           str            = Field(default="Electronic")
    criticality:        str            = Field(default="Medium")
    preferred_supplier: Optional[str]  = None
    safety_stock:       int            = Field(default=0, ge=0)
    unit:               str            = Field(default="units")
    avg_monthly_usage:  Optional[int]  = Field(None, ge=0)

    @field_validator("criticality")
    @classmethod
    def validate_criticality(cls, v: str) -> str:
        if v not in VALID_CRITICALITY:
            raise ValueError(f"criticality must be one of {VALID_CRITICALITY}")
        return v


class ComponentUpdate(ComponentCreate):
    component_name: Optional[str] = None  # type: ignore[assignment]


class ComponentResponse(ComponentCreate):
    id:              UUID
    company_user_id: str
    created_at:      datetime
    updated_at:      datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Production Line
# ══════════════════════════════════════════════════════════════════════════════

class ProductionLineCreate(BaseModel):
    factory_id:        Optional[UUID] = None
    line_name:         str            = Field(..., min_length=1, max_length=200)
    line_code:         str            = Field(..., min_length=1, max_length=50)
    capacity_per_hour: int            = Field(default=100, ge=1)
    operating_status:  str            = Field(default="Operational")


class ProductionLineUpdate(ProductionLineCreate):
    line_name: Optional[str] = None  # type: ignore[assignment]
    line_code: Optional[str] = None  # type: ignore[assignment]


class ProductionLineResponse(ProductionLineCreate):
    id:              UUID
    company_user_id: str
    factory_name:    Optional[str] = None
    created_at:      datetime
    updated_at:      datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Bill of Materials (BOM)
# ══════════════════════════════════════════════════════════════════════════════

class BOMItemCreate(BaseModel):
    product_id:        UUID
    component_id:      UUID
    quantity_required: int            = Field(default=1, ge=1)
    notes:             Optional[str]  = None


class BOMItemResponse(BOMItemCreate):
    id:              UUID
    company_user_id: str
    product_name:    Optional[str] = None
    component_name:  Optional[str] = None
    created_at:      datetime
    updated_at:      datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Complete-setup response
# ══════════════════════════════════════════════════════════════════════════════

class CompleteSetupResponse(BaseModel):
    success:   bool = True
    message:   str  = "Onboarding complete. AI monitoring activated."
    redirect:  str  = "/dashboard"
