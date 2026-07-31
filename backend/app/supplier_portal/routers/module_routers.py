"""
All supplier portal module routers in one efficient file.
Each router section is clearly marked. All use require_supplier dependency.
"""
from __future__ import annotations

import logging
import math
import uuid
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import require_supplier, require_admin, UserPrincipal
from app.supplier_portal.schemas import (
    APIResponse, PaginatedResponse,
    CompanyProfileCreateRequest, CompanyProfileUpdateRequest, CompanyProfileResponse,
    ProductionCapacityRequest, ProductionCapacityResponse,
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse, BulkInventoryUpdate,
    LeadTimeCreate, LeadTimeUpdate, LeadTimeResponse,
    ShipmentCreate, ShipmentUpdate, ShipmentStatusUpdate, ShipmentResponse,
    IncidentCreate, IncidentUpdate, IncidentResponse,
    ForecastSubmitRequest, ForecastResponse,
    PerformanceScoreResponse,
    NotificationResponse, UnreadCountResponse,
    SupportTicketCreate, SupportTicketReply, SupportTicketResponse,
    NotificationPreferences, DisplayPreferences, ProfileUpdateRequest, SettingsResponse,
    paginate,
)
from app.supplier_portal.services.services import (
    CompanyProfileService, ProductionCapacityService, InventoryService,
    LeadTimeService, ShipmentService, IncidentService, ForecastService,
    PerformanceService, NotificationService, SupportService, SettingsService,
)
from app.supplier_portal.repositories.repos import SupplierAccountRepo, AuditLogRepo

logger = logging.getLogger("supplier_portal.routers")


def _ip(request: Request) -> str:
    return request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")


# ══════════════════════════════════════════════════════════════════════════════
# COMPANY PROFILE
# ══════════════════════════════════════════════════════════════════════════════

profile_router = APIRouter(prefix="/profile", tags=["Supplier Portal — Company Profile"])


@profile_router.get("", response_model=APIResponse, summary="Get company profile")
async def get_profile(
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = CompanyProfileService(db)
    profile = svc.get_profile(current_user.user_id)
    data = CompanyProfileResponse.model_validate(profile).model_dump() if profile else None
    return APIResponse(data=data, message="Profile retrieved" if profile else "No profile found")


@profile_router.post("", status_code=201, summary="Create company profile")
async def create_profile(
    body: CompanyProfileCreateRequest,
    request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = CompanyProfileService(db)
    profile = svc.create_profile(current_user.user_id, current_user.user_id, body.model_dump(exclude_none=True), _ip(request))
    return APIResponse(data=CompanyProfileResponse.model_validate(profile).model_dump(), message="Profile created")


@profile_router.put("", summary="Update company profile")
async def update_profile(
    body: CompanyProfileUpdateRequest,
    request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = CompanyProfileService(db)
    profile = svc.update_profile(current_user.user_id, current_user.user_id, body.model_dump(exclude_none=True), _ip(request))
    return APIResponse(data=CompanyProfileResponse.model_validate(profile).model_dump(), message="Profile updated")


@profile_router.post("/logo", summary="Upload company logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Upload logo to Supabase Storage and update logo_url on profile."""
    from app.db.supabase_client import get_supabase
    supabase = get_supabase()
    allowed = {"image/jpeg", "image/png", "image/webp", "image/svg+xml"}
    if file.content_type not in allowed:
        from app.core.exceptions import FileUploadException
        raise FileUploadException("Only JPEG, PNG, WebP, and SVG images are accepted")
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        from app.core.exceptions import FileUploadException
        raise FileUploadException("File size exceeds 10MB limit")
    storage_path = f"supplier-logos/{current_user.user_id}/{file.filename}"
    logo_url = storage_path   # placeholder — replace with supabase.storage upload in production
    if supabase:
        try:
            supabase.storage.from_("supplier-assets").upload(storage_path, contents)
            logo_url = supabase.storage.from_("supplier-assets").get_public_url(storage_path)
        except Exception as exc:
            logger.warning(f"[profile_router] Storage upload failed: {exc}")
    svc = CompanyProfileService(db)
    svc.update_logo(current_user.user_id, logo_url)
    return APIResponse(data={"logo_url": logo_url}, message="Logo uploaded")


@profile_router.get("/documents", summary="List uploaded documents")
async def list_documents(
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = CompanyProfileService(db)
    profile = svc.get_profile(current_user.user_id)
    docs = profile.documents if profile else []
    return APIResponse(data=docs or [], message=f"{len(docs or [])} document(s) found")


@profile_router.post("/documents", summary="Upload a document")
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    from app.db.supabase_client import get_supabase
    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        from app.core.exceptions import FileUploadException
        raise FileUploadException("File size exceeds 20MB limit")
    storage_path = f"supplier-docs/{current_user.user_id}/{file.filename}"
    doc_url = storage_path
    supabase = get_supabase()
    if supabase:
        try:
            supabase.storage.from_("supplier-assets").upload(storage_path, contents)
            doc_url = supabase.storage.from_("supplier-assets").get_public_url(storage_path)
        except Exception as exc:
            logger.warning(f"[profile_router] Doc upload failed: {exc}")
    doc_meta = {"name": file.filename, "type": file.content_type, "url": doc_url}
    svc = CompanyProfileService(db)
    svc.add_document(current_user.user_id, doc_meta)
    return APIResponse(data=doc_meta, message="Document uploaded")


@profile_router.delete("/documents/{doc_id}", summary="Delete a document")
async def delete_document(
    doc_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = CompanyProfileService(db)
    svc.delete_document(current_user.user_id, doc_id)
    return APIResponse(message="Document deleted")


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTION CAPACITY
# ══════════════════════════════════════════════════════════════════════════════

production_router = APIRouter(prefix="/production", tags=["Supplier Portal — Production Capacity"])


@production_router.get("", summary="Get latest capacity snapshot")
async def get_production(
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ProductionCapacityService(db)
    snapshot = svc.get_latest(current_user.user_id)
    data = ProductionCapacityResponse.model_validate(snapshot).model_dump() if snapshot else None
    return APIResponse(data=data, message="Latest snapshot retrieved" if snapshot else "No capacity data yet")


@production_router.post("", status_code=201, summary="Submit capacity update — triggers orchestrator")
async def submit_production(
    body: ProductionCapacityRequest,
    request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ProductionCapacityService(db)
    snapshot = await svc.submit_update(
        current_user.user_id, current_user.user_id,
        body.model_dump(exclude_none=True), _ip(request)
    )
    return APIResponse(data=ProductionCapacityResponse.model_validate(snapshot).model_dump(),
                       message="Capacity update submitted. AI agents notified.")


@production_router.get("/history", summary="Get capacity history (paginated)")
async def production_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ProductionCapacityService(db)
    rows, total = svc.get_history(current_user.user_id, page=page, page_size=page_size)
    return PaginatedResponse(
        data=[ProductionCapacityResponse.model_validate(r).model_dump() for r in rows],
        **paginate(total, page, page_size),
    )


# ══════════════════════════════════════════════════════════════════════════════
# INVENTORY
# ══════════════════════════════════════════════════════════════════════════════

inventory_router = APIRouter(prefix="/inventory", tags=["Supplier Portal — Inventory"])


@inventory_router.get("", summary="List inventory items")
async def list_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    search: Optional[str] = None,
    low_stock_only: bool = False,
    critical_only: bool = False,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = InventoryService(db)
    rows, total = svc.list_items(
        current_user.user_id, category=category, warehouse_id=warehouse_id,
        search=search, low_stock_only=low_stock_only, critical_only=critical_only,
        page=page, page_size=page_size,
    )
    return PaginatedResponse(
        data=[InventoryItemResponse.model_validate(r).model_dump() for r in rows],
        **paginate(total, page, page_size),
    )


@inventory_router.post("", status_code=201, summary="Create inventory item")
async def create_inventory_item(
    body: InventoryItemCreate,
    request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = InventoryService(db)
    item = await svc.create_item(current_user.user_id, current_user.user_id, body.model_dump(), _ip(request))
    return APIResponse(data=InventoryItemResponse.model_validate(item).model_dump(), message="Inventory item created")


@inventory_router.get("/low-stock", summary="Get low-stock items")
async def low_stock(current_user: UserPrincipal = Depends(require_supplier), db: Session = Depends(get_db)):
    svc = InventoryService(db)
    rows, total = svc.list_items(current_user.user_id, low_stock_only=True, page_size=100)
    return APIResponse(data=[InventoryItemResponse.model_validate(r).model_dump() for r in rows],
                       message=f"{total} low-stock item(s)")


@inventory_router.get("/critical", summary="Get critical component items")
async def critical_items(current_user: UserPrincipal = Depends(require_supplier), db: Session = Depends(get_db)):
    svc = InventoryService(db)
    rows, total = svc.list_items(current_user.user_id, critical_only=True, page_size=100)
    return APIResponse(data=[InventoryItemResponse.model_validate(r).model_dump() for r in rows],
                       message=f"{total} critical component(s)")


@inventory_router.get("/warehouse-summary", summary="Summary by warehouse")
async def warehouse_summary(current_user: UserPrincipal = Depends(require_supplier), db: Session = Depends(get_db)):
    svc = InventoryService(db)
    return APIResponse(data=svc.warehouse_summary(current_user.user_id))


@inventory_router.post("/bulk-update", summary="Bulk update inventory items")
async def bulk_update(
    body: BulkInventoryUpdate,
    request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = InventoryService(db)
    result = await svc.bulk_update(current_user.user_id, current_user.user_id, body.items, _ip(request))
    return APIResponse(data=result, message=f"Bulk update: {result['updated']} updated, {len(result['errors'])} errors")


@inventory_router.get("/{item_id}", summary="Get single inventory item")
async def get_inventory_item(
    item_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = InventoryService(db)
    item = svc.get_item(current_user.user_id, item_id)
    return APIResponse(data=InventoryItemResponse.model_validate(item).model_dump())


@inventory_router.put("/{item_id}", summary="Update inventory item — triggers orchestrator")
async def update_inventory_item(
    item_id: str,
    body: InventoryItemUpdate,
    request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = InventoryService(db)
    item = await svc.update_item(current_user.user_id, current_user.user_id, item_id, body.model_dump(exclude_none=True), _ip(request))
    return APIResponse(data=InventoryItemResponse.model_validate(item).model_dump(), message="Inventory updated")


@inventory_router.delete("/{item_id}", summary="Soft delete inventory item")
async def delete_inventory_item(
    item_id: str,
    request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = InventoryService(db)
    await svc.delete_item(current_user.user_id, current_user.user_id, item_id, _ip(request))
    return APIResponse(message="Inventory item deleted")


# ══════════════════════════════════════════════════════════════════════════════
# LEAD TIMES
# ══════════════════════════════════════════════════════════════════════════════

lead_time_router = APIRouter(prefix="/lead-times", tags=["Supplier Portal — Lead Times"])


@lead_time_router.get("", summary="List lead time records")
async def list_lead_times(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = LeadTimeService(db)
    rows, total = svc.list_records(current_user.user_id, page=page, page_size=page_size)
    return PaginatedResponse(data=[LeadTimeResponse.model_validate(r).model_dump() for r in rows], **paginate(total, page, page_size))


@lead_time_router.post("", status_code=201, summary="Create lead time record")
async def create_lead_time(
    body: LeadTimeCreate, request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = LeadTimeService(db)
    record = await svc.create_record(current_user.user_id, current_user.user_id, body.model_dump(exclude_none=True), _ip(request))
    return APIResponse(data=LeadTimeResponse.model_validate(record).model_dump(), message="Lead time record created")


@lead_time_router.get("/trends", summary="Get historical lead time trends")
async def lead_time_trends(
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = LeadTimeService(db)
    rows = svc.get_trends(current_user.user_id)
    return APIResponse(data=[LeadTimeResponse.model_validate(r).model_dump() for r in rows])


@lead_time_router.get("/{record_id}", summary="Get lead time record")
async def get_lead_time(
    record_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = LeadTimeService(db)
    record = svc.get_record(current_user.user_id, record_id)
    return APIResponse(data=LeadTimeResponse.model_validate(record).model_dump())


@lead_time_router.put("/{record_id}", summary="Update lead time record — triggers orchestrator")
async def update_lead_time(
    record_id: str, body: LeadTimeUpdate, request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = LeadTimeService(db)
    record = await svc.update_record(current_user.user_id, current_user.user_id, record_id, body.model_dump(exclude_none=True), _ip(request))
    return APIResponse(data=LeadTimeResponse.model_validate(record).model_dump(), message="Lead time updated")


@lead_time_router.delete("/{record_id}", summary="Delete lead time record")
async def delete_lead_time(
    record_id: str, request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = LeadTimeService(db)
    await svc.delete_record(current_user.user_id, current_user.user_id, record_id, _ip(request))
    return APIResponse(message="Lead time record deleted")


# ══════════════════════════════════════════════════════════════════════════════
# SHIPMENTS
# ══════════════════════════════════════════════════════════════════════════════

shipment_router = APIRouter(prefix="/shipments", tags=["Supplier Portal — Shipments"])


@shipment_router.get("", summary="List shipments (paginated, filtered)")
async def list_shipments(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None, search: Optional[str] = None,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ShipmentService(db)
    rows, total = svc.list_shipments(current_user.user_id, status=status, search=search, page=page, page_size=page_size)
    return PaginatedResponse(data=[ShipmentResponse.model_validate(r).model_dump() for r in rows], **paginate(total, page, page_size))


@shipment_router.post("", status_code=201, summary="Create shipment")
async def create_shipment(
    body: ShipmentCreate, request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ShipmentService(db)
    shipment = await svc.create_shipment(current_user.user_id, current_user.user_id, body.model_dump(exclude_none=True), _ip(request))
    return APIResponse(data=ShipmentResponse.model_validate(shipment).model_dump(), message="Shipment created")


@shipment_router.get("/{shipment_id}", summary="Get shipment detail")
async def get_shipment(
    shipment_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ShipmentService(db)
    s = svc.get_shipment(current_user.user_id, shipment_id)
    return APIResponse(data=ShipmentResponse.model_validate(s).model_dump())


@shipment_router.put("/{shipment_id}", summary="Update shipment — triggers orchestrator")
async def update_shipment(
    shipment_id: str, body: ShipmentUpdate, request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ShipmentService(db)
    s = await svc.update_shipment(current_user.user_id, current_user.user_id, shipment_id, body.model_dump(exclude_none=True), _ip(request))
    return APIResponse(data=ShipmentResponse.model_validate(s).model_dump(), message="Shipment updated")


@shipment_router.put("/{shipment_id}/status", summary="Update delivery status")
async def update_status(
    shipment_id: str, body: ShipmentStatusUpdate, request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ShipmentService(db)
    s = await svc.update_status(current_user.user_id, current_user.user_id, shipment_id, body.status.value, body.notes, _ip(request))
    return APIResponse(data=ShipmentResponse.model_validate(s).model_dump(), message=f"Status updated to {body.status.value}")


@shipment_router.get("/{shipment_id}/tracking", summary="Get tracking timeline")
async def get_tracking(
    shipment_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ShipmentService(db)
    s = svc.get_shipment(current_user.user_id, shipment_id)
    return APIResponse(data={"timeline": s.timeline or [], "status": s.status})


@shipment_router.delete("/{shipment_id}", summary="Delete shipment")
async def delete_shipment(
    shipment_id: str, request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ShipmentService(db)
    await svc.delete_shipment(current_user.user_id, current_user.user_id, shipment_id, _ip(request))
    return APIResponse(message="Shipment deleted")


# ══════════════════════════════════════════════════════════════════════════════
# INCIDENTS
# ══════════════════════════════════════════════════════════════════════════════

incident_router = APIRouter(prefix="/incidents", tags=["Supplier Portal — Incidents"])


@incident_router.get("", summary="List incidents")
async def list_incidents(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    incident_type: Optional[str] = None, severity: Optional[str] = None,
    status: Optional[str] = None,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = IncidentService(db)
    rows, total = svc.list_incidents(current_user.user_id, incident_type=incident_type,
                                     severity=severity, status=status, page=page, page_size=page_size)
    return PaginatedResponse(data=[IncidentResponse.model_validate(r).model_dump() for r in rows], **paginate(total, page, page_size))


@incident_router.post("", status_code=201, summary="Report incident — triggers AI agents")
async def report_incident(
    body: IncidentCreate, request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = IncidentService(db)
    incident = await svc.report_incident(current_user.user_id, current_user.user_id, body.model_dump(), _ip(request))
    return APIResponse(data=IncidentResponse.model_validate(incident).model_dump(),
                       message="Incident reported. Risk and News agents have been notified.")


@incident_router.get("/{incident_id}", summary="Get incident detail")
async def get_incident(
    incident_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = IncidentService(db)
    incident = svc.get_incident(current_user.user_id, incident_id)
    return APIResponse(data=IncidentResponse.model_validate(incident).model_dump())


@incident_router.put("/{incident_id}", summary="Update incident status")
async def update_incident(
    incident_id: str, body: IncidentUpdate, request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = IncidentService(db)
    incident = await svc.update_incident(current_user.user_id, current_user.user_id, incident_id, body.model_dump(exclude_none=True), _ip(request))
    return APIResponse(data=IncidentResponse.model_validate(incident).model_dump(), message="Incident updated")


@incident_router.delete("/{incident_id}", summary="Retract incident (soft delete)")
async def retract_incident(
    incident_id: str, request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = IncidentService(db)
    await svc.retract_incident(current_user.user_id, current_user.user_id, incident_id, _ip(request))
    return APIResponse(message="Incident retracted")


# ══════════════════════════════════════════════════════════════════════════════
# CAPACITY FORECAST
# ══════════════════════════════════════════════════════════════════════════════

forecast_router = APIRouter(prefix="/forecasts", tags=["Supplier Portal — Capacity Forecast"])


@forecast_router.post("", status_code=201, summary="Submit forecast — triggers orchestrator")
async def submit_forecast(
    body: ForecastSubmitRequest, request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ForecastService(db)
    entries = [e.model_dump(exclude_none=True) for e in body.entries]
    created = await svc.submit_forecast(current_user.user_id, current_user.user_id, body.forecast_year, body.period_type, entries, _ip(request))
    return APIResponse(
        data=[ForecastResponse.model_validate(c).model_dump() for c in created],
        message=f"Forecast submitted: {len(created)} entries for {body.forecast_year}",
    )


@forecast_router.get("/monthly/{year}", summary="Get monthly forecast entries for a year")
async def get_monthly_forecast(
    year: int,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ForecastService(db)
    rows = svc.get_monthly(current_user.user_id, year)
    return APIResponse(data=[ForecastResponse.model_validate(r).model_dump() for r in rows])


@forecast_router.get("/quarterly/{year}", summary="Get quarterly forecast entries")
async def get_quarterly_forecast(
    year: int,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ForecastService(db)
    rows = svc.get_quarterly(current_user.user_id, year)
    return APIResponse(data=[ForecastResponse.model_validate(r).model_dump() for r in rows])


@forecast_router.get("/history", summary="All historical forecast submissions")
async def forecast_history(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ForecastService(db)
    rows, total = svc.get_history(current_user.user_id, page=page, page_size=page_size)
    return PaginatedResponse(data=[ForecastResponse.model_validate(r).model_dump() for r in rows], **paginate(total, page, page_size))


@forecast_router.put("/{forecast_id}", summary="Update forecast entry")
async def update_forecast(
    forecast_id: str, body: dict, request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ForecastService(db)
    entry = await svc.update_entry(current_user.user_id, current_user.user_id, forecast_id, body, _ip(request))
    return APIResponse(data=ForecastResponse.model_validate(entry).model_dump(), message="Forecast entry updated")


@forecast_router.delete("/{forecast_id}", summary="Delete forecast entry")
async def delete_forecast(
    forecast_id: str, request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = ForecastService(db)
    await svc.delete_entry(current_user.user_id, current_user.user_id, forecast_id, _ip(request))
    return APIResponse(message="Forecast entry deleted")


# ══════════════════════════════════════════════════════════════════════════════
# AI PERFORMANCE (read-only)
# ══════════════════════════════════════════════════════════════════════════════

performance_router = APIRouter(prefix="/performance", tags=["Supplier Portal — AI Performance Scores"])


@performance_router.get("/scores", summary="Get AI-generated performance scores (read-only)")
async def get_scores(
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = PerformanceService(db)
    scores = svc.get_scores(current_user.user_id)
    if not scores:
        return APIResponse(
            data={"supplier_id": current_user.user_id, "note": "No scores available yet. Trigger a workflow run first."},
            message="No AI scores computed yet"
        )
    data = PerformanceScoreResponse.model_validate(scores).model_dump()
    data["reliability"] = data.get("reliability_score") or 0.0
    data["performance"] = data.get("quality_score") or data.get("performance_score") or 0.0
    data["risk"]        = data.get("risk_score") or 0.0
    data["health"]      = data.get("health_score") or 0.0
    data["confidence"]  = data.get("compliance_score") or 95.0
    return APIResponse(data=data, message="AI performance scores (read-only)")


@performance_router.get("/history", summary="6-month score history (chart-ready)")
async def get_score_history(
    limit: int = Query(12, ge=1, le=24),
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = PerformanceService(db)
    rows = svc.get_history(current_user.user_id, limit=limit)

    MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def _to_chart_row(r):
        row = PerformanceScoreResponse.model_validate(r).model_dump()
        # Add month label for the LineChart X-axis
        evaluated_at = getattr(r, 'evaluated_at', None)
        if evaluated_at:
            row['month'] = MONTH_NAMES[evaluated_at.month - 1]
        else:
            row['month'] = '—'
        # Normalise field names to match frontend METRICS keys
        row['reliability'] = row.get('reliability_score') or 0
        row['performance'] = row.get('performance_score') or 0
        row['risk']        = row.get('risk_score')        or 0
        row['health']      = row.get('health_score')      or 0
        row['confidence']  = row.get('confidence_score')  or 0
        return row

    # Reverse so oldest data is first (left side of chart)
    history = [_to_chart_row(r) for r in reversed(rows)]
    return APIResponse(data=history, message=f"{len(history)} score history records")


# ══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════════════

notification_router = APIRouter(prefix="/notifications", tags=["Supplier Portal — Notifications"])


@notification_router.get("", summary="List notifications")
async def list_notifications(
    page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100),
    category: Optional[str] = None,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = NotificationService(db)
    rows, total = svc.list_notifications(current_user.user_id, category=category, page=page, page_size=page_size)
    return PaginatedResponse(data=[NotificationResponse.model_validate(r).model_dump() for r in rows], **paginate(total, page, page_size))


@notification_router.get("/unread", summary="Get unread count by category")
async def unread_count(
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = NotificationService(db)
    return APIResponse(data=svc.get_unread_count(current_user.user_id))


@notification_router.put("/read-all", summary="Mark all notifications as read")
async def mark_all_read(
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = NotificationService(db)
    count = svc.mark_all_read(current_user.user_id)
    return APIResponse(message=f"{count} notification(s) marked as read")


@notification_router.put("/{notification_id}/read", summary="Mark single notification as read")
async def mark_read(
    notification_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = NotificationService(db)
    n = svc.mark_read(current_user.user_id, notification_id)
    return APIResponse(data=NotificationResponse.model_validate(n).model_dump(), message="Marked as read")


@notification_router.delete("/{notification_id}", summary="Delete notification")
async def delete_notification(
    notification_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = NotificationService(db)
    svc.delete_notification(current_user.user_id, notification_id)
    return APIResponse(message="Notification deleted")


# ══════════════════════════════════════════════════════════════════════════════
# SUPPORT
# ══════════════════════════════════════════════════════════════════════════════

support_router = APIRouter(prefix="/support", tags=["Supplier Portal — Support"])


@support_router.get("/tickets", summary="List support tickets")
async def list_tickets(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = SupportService(db)
    rows, total = svc.list_tickets(current_user.user_id, status=status, page=page, page_size=page_size)
    return PaginatedResponse(data=[SupportTicketResponse.model_validate(r).model_dump() for r in rows], **paginate(total, page, page_size))


@support_router.post("/tickets", status_code=201, summary="Create support ticket")
async def create_ticket(
    body: SupportTicketCreate,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = SupportService(db)
    ticket = svc.create_ticket(current_user.user_id, current_user.user_id, body.model_dump())
    return APIResponse(data=SupportTicketResponse.model_validate(ticket).model_dump(), message="Ticket submitted")


@support_router.get("/tickets/{ticket_id}", summary="Get ticket detail with replies")
async def get_ticket(
    ticket_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = SupportService(db)
    ticket = svc.get_ticket(current_user.user_id, ticket_id)
    return APIResponse(data=SupportTicketResponse.model_validate(ticket).model_dump())


@support_router.post("/tickets/{ticket_id}/reply", summary="Reply to a ticket")
async def reply_ticket(
    ticket_id: str, body: SupportTicketReply,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = SupportService(db)
    ticket = svc.add_reply(current_user.user_id, current_user.user_id, ticket_id, body.message)
    return APIResponse(data=SupportTicketResponse.model_validate(ticket).model_dump(), message="Reply added")


@support_router.put("/tickets/{ticket_id}/close", summary="Close a ticket")
async def close_ticket(
    ticket_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = SupportService(db)
    ticket = svc.close_ticket(current_user.user_id, ticket_id)
    return APIResponse(data=SupportTicketResponse.model_validate(ticket).model_dump(), message="Ticket closed")


# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

settings_router = APIRouter(prefix="/settings", tags=["Supplier Portal — Settings"])


@settings_router.get("/profile", summary="Get display settings")
async def get_settings(
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = SettingsService(db)
    data = svc.get_settings(current_user.user_id)
    return APIResponse(data=data)


@settings_router.put("/profile", summary="Update contact name / phone")
async def update_profile_settings(
    body: ProfileUpdateRequest,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = SettingsService(db)
    data = svc.update_profile(current_user.user_id, body.model_dump(exclude_none=True))
    return APIResponse(data=data, message="Profile settings updated")


@settings_router.get("/sessions", summary="Active sessions (placeholder)")
async def get_sessions(current_user: UserPrincipal = Depends(require_supplier)):
    return APIResponse(data={"sessions": [], "note": "Full session management available after Redis integration"})
