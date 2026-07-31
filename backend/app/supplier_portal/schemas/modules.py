"""
Production capacity, inventory, lead time, shipment, incident, forecast, 
performance, notification, support, and settings schemas — all in one pass.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTION CAPACITY
# ══════════════════════════════════════════════════════════════════════════════

class FactoryStatus(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    PARTIAL     = "PARTIAL"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE     = "OFFLINE"


class MachineUtilization(BaseModel):
    machine_id: Optional[str] = None
    name: str
    utilization_pct: float = Field(..., ge=0, le=100)
    status: Optional[str] = None


class ProductionCapacityRequest(BaseModel):
    maximum_capacity_units: Optional[int] = Field(None, ge=0)
    current_output_units: Optional[int] = Field(None, ge=0)
    utilization_pct: Optional[float] = Field(None, ge=0, le=100)
    production_rate_per_day: Optional[float] = Field(None, ge=0)
    workforce_count: Optional[int] = Field(None, ge=0)
    shifts_per_day: Optional[int] = Field(None, ge=1, le=3)
    factory_status: FactoryStatus = FactoryStatus.OPERATIONAL
    planned_downtime_days: Optional[int] = Field(None, ge=0, le=31)
    next_maintenance_date: Optional[datetime] = None
    maintenance_notes: Optional[str] = Field(None, max_length=1000)
    machine_utilization: Optional[List[MachineUtilization]] = None
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator(
        "maximum_capacity_units", "current_output_units", "utilization_pct",
        "production_rate_per_day", "workforce_count", "shifts_per_day",
        "planned_downtime_days", "next_maintenance_date", "maintenance_notes", "notes",
        mode="before"
    )
    @classmethod
    def sanitize_empty_values(cls, v: Any) -> Any:
        if v == "" or v is None:
            return None
        return v


class ProductionCapacityResponse(BaseModel):
    id: Any
    supplier_id: Any
    maximum_capacity_units: Optional[int]
    current_output_units: Optional[int]
    utilization_pct: Optional[float]
    production_rate_per_day: Optional[float]
    workforce_count: Optional[int]
    shifts_per_day: Optional[int]
    factory_status: str
    planned_downtime_days: Optional[int]
    next_maintenance_date: Optional[datetime]
    maintenance_notes: Optional[str]
    machine_utilization: Optional[list]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


# ══════════════════════════════════════════════════════════════════════════════
# INVENTORY
# ══════════════════════════════════════════════════════════════════════════════

class InventoryItemCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    unit: str = Field("units", max_length=50)
    quantity_on_hand: int = Field(..., ge=0)
    safety_stock_level: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    maximum_stock: Optional[int] = Field(None, ge=0)
    warehouse_id: Optional[str] = None
    warehouse_location: Optional[str] = Field(None, max_length=200)
    unit_cost_usd: Optional[float] = Field(None, ge=0)
    is_critical_component: bool = False


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    quantity_on_hand: Optional[int] = Field(None, ge=0)
    safety_stock_level: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    maximum_stock: Optional[int] = Field(None, ge=0)
    warehouse_id: Optional[str] = None
    warehouse_location: Optional[str] = None
    unit_cost_usd: Optional[float] = Field(None, ge=0)
    is_critical_component: Optional[bool] = None
    is_active: Optional[bool] = None


class InventoryItemResponse(BaseModel):
    id: Any
    supplier_id: Any
    sku: str
    name: str
    description: Optional[str]
    category: Optional[str]
    unit: str
    quantity_on_hand: int
    safety_stock_level: Optional[int]
    reorder_point: Optional[int]
    maximum_stock: Optional[int]
    warehouse_id: Optional[str]
    warehouse_location: Optional[str]
    unit_cost_usd: Optional[float]
    is_low_stock: bool
    is_critical_component: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class BulkInventoryUpdate(BaseModel):
    items: List[Dict[str, Any]] = Field(..., min_length=1, max_length=500)


# ══════════════════════════════════════════════════════════════════════════════
# LEAD TIME
# ══════════════════════════════════════════════════════════════════════════════

class LeadTimeCreate(BaseModel):
    product_sku: Optional[str] = None
    product_name: Optional[str] = Field(None, max_length=300)
    category: Optional[str] = Field(None, max_length=100)
    manufacturing_days: Optional[int] = Field(None, ge=0)
    packaging_days: Optional[int] = Field(None, ge=0)
    quality_check_days: Optional[int] = Field(None, ge=0)
    shipping_days: Optional[int] = Field(None, ge=0)
    customs_days: Optional[int] = Field(None, ge=0)
    total_lead_time_days: Optional[int] = Field(None, ge=0)
    average_delay_days: Optional[float] = Field(None, ge=0)
    expected_delivery_days: Optional[int] = Field(None, ge=0)
    destination_country: Optional[str] = None
    shipping_method: Optional[str] = Field(None, pattern="^(air|sea|land|courier|mixed)?$")
    notes: Optional[str] = Field(None, max_length=1000)


class LeadTimeUpdate(LeadTimeCreate):
    pass


class LeadTimeResponse(BaseModel):
    id: Any
    supplier_id: Any
    product_sku: Optional[str]
    product_name: Optional[str]
    category: Optional[str]
    manufacturing_days: Optional[int]
    packaging_days: Optional[int]
    quality_check_days: Optional[int]
    shipping_days: Optional[int]
    customs_days: Optional[int]
    total_lead_time_days: Optional[int]
    average_delay_days: Optional[float]
    expected_delivery_days: Optional[int]
    destination_country: Optional[str]
    shipping_method: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


# ══════════════════════════════════════════════════════════════════════════════
# SHIPMENT
# ══════════════════════════════════════════════════════════════════════════════

class ShipmentStatus(str, Enum):
    PREPARING   = "PREPARING"
    IN_TRANSIT  = "IN_TRANSIT"
    CUSTOMS     = "CUSTOMS"
    DELIVERED   = "DELIVERED"
    DELAYED     = "DELAYED"
    CANCELLED   = "CANCELLED"


class ShipmentItem(BaseModel):
    sku: Optional[str] = None
    name: str
    quantity: int = Field(..., ge=1)


class TimelineEvent(BaseModel):
    event: str
    location: Optional[str] = None
    timestamp: Optional[str] = None
    notes: Optional[str] = None


class ShipmentCreate(BaseModel):
    shipment_number: str = Field(..., min_length=1, max_length=100)
    tracking_number: Optional[str] = Field(None, max_length=200)
    purchase_order_number: Optional[str] = Field(None, max_length=100)
    status: ShipmentStatus = ShipmentStatus.PREPARING
    carrier_name: Optional[str] = Field(None, max_length=200)
    carrier_code: Optional[str] = Field(None, max_length=50)
    shipping_method: Optional[str] = None
    origin_country: Optional[str] = None
    origin_city: Optional[str] = None
    destination_country: Optional[str] = None
    destination_city: Optional[str] = None
    destination_address: Optional[str] = None
    shipped_at: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    quantity: Optional[int] = Field(None, ge=0)
    unit: Optional[str] = None
    weight_kg: Optional[float] = Field(None, ge=0)
    volume_m3: Optional[float] = Field(None, ge=0)
    items: Optional[List[ShipmentItem]] = None
    notes: Optional[str] = Field(None, max_length=2000)
    customs_status: Optional[str] = None
    incoterms: Optional[str] = None


class ShipmentUpdate(BaseModel):
    tracking_number: Optional[str] = None
    status: Optional[ShipmentStatus] = None
    carrier_name: Optional[str] = None
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    notes: Optional[str] = None
    customs_status: Optional[str] = None


class ShipmentStatusUpdate(BaseModel):
    status: ShipmentStatus
    notes: Optional[str] = None


class ShipmentResponse(BaseModel):
    id: Any
    supplier_id: Any
    shipment_number: str
    tracking_number: Optional[str]
    purchase_order_number: Optional[str]
    status: str
    carrier_name: Optional[str]
    carrier_code: Optional[str]
    shipping_method: Optional[str]
    origin_country: Optional[str]
    origin_city: Optional[str]
    destination_country: Optional[str]
    destination_city: Optional[str]
    destination_address: Optional[str]
    shipped_at: Optional[datetime]
    estimated_arrival: Optional[datetime]
    actual_arrival: Optional[datetime]
    quantity: Optional[int]
    unit: Optional[str]
    weight_kg: Optional[float]
    volume_m3: Optional[float]
    items: Optional[list]
    timeline: Optional[list]
    notes: Optional[str]
    customs_status: Optional[str]
    incoterms: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


# ══════════════════════════════════════════════════════════════════════════════
# INCIDENT
# ══════════════════════════════════════════════════════════════════════════════

class IncidentType(str, Enum):
    MACHINE_FAILURE      = "MACHINE_FAILURE"
    FLOOD                = "FLOOD"
    EARTHQUAKE           = "EARTHQUAKE"
    STRIKE               = "STRIKE"
    POWER_FAILURE        = "POWER_FAILURE"
    CYBER_ATTACK         = "CYBER_ATTACK"
    MATERIAL_SHORTAGE    = "MATERIAL_SHORTAGE"
    QUALITY_ISSUE        = "QUALITY_ISSUE"
    TRANSPORTATION_DELAY = "TRANSPORTATION_DELAY"
    OTHER                = "OTHER"


class IncidentSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"


class IncidentCreate(BaseModel):
    incident_type: IncidentType
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    title: str = Field(..., min_length=5, max_length=300)
    description: str = Field(..., min_length=10, max_length=5000)
    affected_products: Optional[List[Dict[str, Any]]] = None
    affected_countries: Optional[List[str]] = None
    estimated_recovery_days: Optional[int] = Field(None, ge=0, le=365)
    capacity_impact_pct: Optional[int] = Field(None, ge=0, le=100)


class IncidentUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(ACTIVE|RECOVERING|RESOLVED|CLOSED)$")
    severity: Optional[IncidentSeverity] = None
    estimated_recovery_days: Optional[int] = Field(None, ge=0, le=365)
    capacity_impact_pct: Optional[int] = Field(None, ge=0, le=100)
    resolution_notes: Optional[str] = Field(None, max_length=2000)


class IncidentResponse(BaseModel):
    id: Any
    supplier_id: Any
    incident_type: str
    severity: str
    status: str
    title: str
    description: str
    affected_products: Optional[list]
    affected_countries: Optional[list]
    estimated_recovery_days: Optional[int]
    capacity_impact_pct: Optional[int]
    attachments: Optional[list]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    reported_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


# ══════════════════════════════════════════════════════════════════════════════
# CAPACITY FORECAST
# ══════════════════════════════════════════════════════════════════════════════

class ForecastEntry(BaseModel):
    forecast_month: Optional[int] = Field(None, ge=1, le=12)
    quarter: Optional[int] = Field(None, ge=1, le=4)
    forecasted_output: Optional[int] = Field(None, ge=0)
    maximum_capacity: Optional[int] = Field(None, ge=0)
    planned_downtime_days: Optional[int] = Field(None, ge=0, le=31)
    notes: Optional[str] = None


class ForecastSubmitRequest(BaseModel):
    forecast_year: int = Field(..., ge=2020, le=2050)
    period_type: str = Field("monthly", pattern="^(monthly|quarterly|annual)$")
    entries: List[ForecastEntry] = Field(..., min_length=1, max_length=12)


class ForecastResponse(BaseModel):
    id: Any
    supplier_id: Any
    forecast_year: int
    forecast_month: Optional[int]
    period_type: str
    quarter: Optional[int]
    forecasted_output: Optional[int]
    maximum_capacity: Optional[int]
    planned_downtime_days: Optional[int]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


# ══════════════════════════════════════════════════════════════════════════════
# AI PERFORMANCE SCORES (read-only)
# ══════════════════════════════════════════════════════════════════════════════

class PerformanceScoreResponse(BaseModel):
    supplier_id: Any
    health_score: Optional[float]
    health_label: Optional[str]
    reliability_score: Optional[float]
    quality_score: Optional[float]
    lead_time_score: Optional[float]
    cost_efficiency: Optional[float]
    compliance_score: Optional[float]
    responsiveness: Optional[float]
    flexibility: Optional[float]
    risk_score: Optional[float]
    risk_level: Optional[str]
    rank: Optional[int]
    rank_change: Optional[int]
    trend: Optional[str]
    mom_change: Optional[float]
    formula_breakdown: Optional[dict]
    evaluated_at: Optional[datetime]
    note: str = "Scores are AI-generated and read-only. Update your data to improve scores."

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


# ══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════════════

class NotificationResponse(BaseModel):
    id: Any
    supplier_id: Any
    category: str
    priority: str
    title: str
    body: Optional[str]
    action_url: Optional[str]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class UnreadCountResponse(BaseModel):
    total_unread: int
    by_category: Dict[str, int]


# ══════════════════════════════════════════════════════════════════════════════
# SUPPORT TICKETS
# ══════════════════════════════════════════════════════════════════════════════

class SupportTicketCreate(BaseModel):
    subject: str = Field(..., min_length=5, max_length=300)
    description: str = Field(..., min_length=10, max_length=5000)
    category: Optional[str] = Field(None, max_length=50)
    priority: str = Field("MEDIUM", pattern="^(LOW|MEDIUM|HIGH|URGENT)$")


class SupportTicketReply(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)


class SupportTicketResponse(BaseModel):
    id: Any
    supplier_id: Any
    ticket_number: str
    subject: str
    description: str
    category: Optional[str]
    priority: str
    status: str
    assigned_to: Optional[str]
    replies: Optional[list]
    attachments: Optional[list]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

class NotificationPreferences(BaseModel):
    email_alerts: bool = True
    email_shipments: bool = True
    email_inventory: bool = True
    email_recommendations: bool = False
    sms_alerts: bool = False
    sms_shipments: bool = False


class DisplayPreferences(BaseModel):
    language: str = "English"
    timezone: str = "UTC"
    date_format: str = "MM/DD/YYYY"


class ProfileUpdateRequest(BaseModel):
    contact_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None


class SettingsResponse(BaseModel):
    supplier_id: Any
    contact_name: str
    email: str
    phone: Optional[str]
    notification_preferences: Optional[dict]
    display_preferences: Optional[dict]

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
