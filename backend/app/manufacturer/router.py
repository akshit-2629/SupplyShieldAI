"""
app/manufacturer/router.py — FastAPI router for the manufacturer onboarding wizard.

All endpoints require a valid authenticated user (JWT).
Base prefix: /api/v1/manufacturer
"""
from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, UserPrincipal
from app.manufacturer.service import ManufacturerService
from app.manufacturer.schemas import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    FactoryCreate,
    FactoryUpdate,
    FactoryResponse,
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseResponse,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ComponentCreate,
    ComponentUpdate,
    ComponentResponse,
    ProductionLineCreate,
    ProductionLineUpdate,
    ProductionLineResponse,
    BOMItemCreate,
    BOMItemResponse,
    SetupStatusResponse,
    CompleteSetupResponse,
    OKResponse,
)

logger = logging.getLogger("manufacturer.router")
router = APIRouter(prefix="/manufacturer", tags=["Manufacturer Onboarding"])


def _svc(db: Session = Depends(get_db)) -> ManufacturerService:
    return ManufacturerService(db)


# ══════════════════════════════════════════════════════════════════════════════
# Setup status — called by ProtectedRoute on every dashboard load
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/setup-status",
    response_model=SetupStatusResponse,
    summary="Check if manufacturer onboarding is complete",
    description=(
        "Returns onboarding state for the authenticated user. "
        "The frontend calls this immediately after login to decide whether to "
        "redirect to /setup or /dashboard."
    ),
)
async def get_setup_status(
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    return svc.get_setup_status(current_user.user_id)


# ══════════════════════════════════════════════════════════════════════════════
# Company (Step 1)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/company", response_model=CompanyResponse, summary="Get company profile")
async def get_company(
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    company = svc.get_company(current_user.user_id)
    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not configured yet")
    return company


from app.orchestrator.event_bus import event_bus
from app.orchestrator.events import Event, EventType

@router.post(
    "/company",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update company (upsert)",
    description="Safe to call multiple times — updates existing record if one already exists.",
)
async def upsert_company(
    data: CompanyCreate,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    result = svc.create_or_update_company(current_user.user_id, data)
    try:
        await event_bus.publish(Event(
            type=EventType.COMPANY_CREATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "name": result.name}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish COMPANY_CREATED event: {exc}")
    return result


@router.put("/company", response_model=CompanyResponse, summary="Update company fields")
async def update_company(
    data: CompanyUpdate,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    result = svc.create_or_update_company(current_user.user_id, data)
    try:
        await event_bus.publish(Event(
            type=EventType.COMPANY_UPDATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "name": result.name}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish COMPANY_UPDATED event: {exc}")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# Factories (Step 2)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/factories", response_model=List[FactoryResponse], summary="List factories")
async def list_factories(
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    return svc.list_factories(current_user.user_id)


@router.post(
    "/factories",
    response_model=FactoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a factory",
)
async def create_factory(
    data: FactoryCreate,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    res = svc.create_factory(current_user.user_id, data)
    try:
        await event_bus.publish(Event(
            type=EventType.FACTORY_CREATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "factory_id": str(res.id), "name": res.factory_name}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish FACTORY_CREATED event: {exc}")
    return res


@router.put("/factories/{factory_id}", response_model=FactoryResponse, summary="Update factory")
async def update_factory(
    factory_id: UUID,
    data: FactoryUpdate,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    res = svc.update_factory(current_user.user_id, factory_id, data)
    try:
        await event_bus.publish(Event(
            type=EventType.FACTORY_UPDATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "factory_id": str(res.id)}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish FACTORY_UPDATED event: {exc}")
    return res


@router.delete(
    "/factories/{factory_id}",
    response_model=OKResponse,
    summary="Delete factory",
)
async def delete_factory(
    factory_id: UUID,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    svc.delete_factory(current_user.user_id, factory_id)
    try:
        await event_bus.publish(Event(
            type=EventType.FACTORY_DELETED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "factory_id": str(factory_id)}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish FACTORY_DELETED event: {exc}")
    return OKResponse(message="Factory deleted")


# ══════════════════════════════════════════════════════════════════════════════
# Warehouses (Step 3)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/warehouses", response_model=List[WarehouseResponse], summary="List warehouses")
async def list_warehouses(
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    return svc.list_warehouses(current_user.user_id)


@router.post(
    "/warehouses",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a warehouse",
)
async def create_warehouse(
    data: WarehouseCreate,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    res = svc.create_warehouse(current_user.user_id, data)
    try:
        await event_bus.publish(Event(
            type=EventType.WAREHOUSE_CREATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "warehouse_id": str(res.id)}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish WAREHOUSE_CREATED event: {exc}")
    return res


@router.put("/warehouses/{warehouse_id}", response_model=WarehouseResponse, summary="Update warehouse")
async def update_warehouse(
    warehouse_id: UUID,
    data: WarehouseUpdate,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    res = svc.update_warehouse(current_user.user_id, warehouse_id, data)
    try:
        await event_bus.publish(Event(
            type=EventType.WAREHOUSE_UPDATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "warehouse_id": str(res.id)}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish WAREHOUSE_UPDATED event: {exc}")
    return res


@router.delete("/warehouses/{warehouse_id}", response_model=OKResponse, summary="Delete warehouse")
async def delete_warehouse(
    warehouse_id: UUID,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    svc.delete_warehouse(current_user.user_id, warehouse_id)
    try:
        await event_bus.publish(Event(
            type=EventType.WAREHOUSE_DELETED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "warehouse_id": str(warehouse_id)}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish WAREHOUSE_DELETED event: {exc}")
    return OKResponse(message="Warehouse deleted")


# ══════════════════════════════════════════════════════════════════════════════
# Products (Step 4)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/products", response_model=List[ProductResponse], summary="List products")
async def list_products(
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    return svc.list_products(current_user.user_id)


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a product",
)
async def create_product(
    data: ProductCreate,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    res = svc.create_product(current_user.user_id, data)
    try:
        await event_bus.publish(Event(
            type=EventType.PRODUCT_CREATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "product_id": str(res.id), "name": res.product_name}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish PRODUCT_CREATED event: {exc}")
    return res


@router.put("/products/{product_id}", response_model=ProductResponse, summary="Update product")
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    res = svc.update_product(current_user.user_id, product_id, data)
    try:
        await event_bus.publish(Event(
            type=EventType.PRODUCT_UPDATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "product_id": str(res.id)}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish PRODUCT_UPDATED event: {exc}")
    return res


@router.delete("/products/{product_id}", response_model=OKResponse, summary="Delete product")
async def delete_product(
    product_id: UUID,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    svc.delete_product(current_user.user_id, product_id)
    try:
        await event_bus.publish(Event(
            type=EventType.PRODUCT_DELETED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "product_id": str(product_id)}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish PRODUCT_DELETED event: {exc}")
    return OKResponse(message="Product deleted")


# ══════════════════════════════════════════════════════════════════════════════
# Components (Step 5)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/components", response_model=List[ComponentResponse], summary="List components")
async def list_components(
    product_id: Optional[UUID] = None,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    return svc.list_components(current_user.user_id, product_id=product_id)


@router.post(
    "/components",
    response_model=ComponentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a component",
)
async def create_component(
    data: ComponentCreate,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    res = svc.create_component(current_user.user_id, data)
    try:
        await event_bus.publish(Event(
            type=EventType.COMPONENT_CREATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "component_id": str(res.id), "name": res.component_name}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish COMPONENT_CREATED event: {exc}")
    return res


@router.put("/components/{component_id}", response_model=ComponentResponse, summary="Update component")
async def update_component(
    component_id: UUID,
    data: ComponentUpdate,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    res = svc.update_component(current_user.user_id, component_id, data)
    try:
        await event_bus.publish(Event(
            type=EventType.COMPONENT_UPDATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "component_id": str(res.id)}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish COMPONENT_UPDATED event: {exc}")
    return res


@router.delete("/components/{component_id}", response_model=OKResponse, summary="Delete component")
async def delete_component(
    component_id: UUID,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    svc.delete_component(current_user.user_id, component_id)
    try:
        await event_bus.publish(Event(
            type=EventType.COMPONENT_DELETED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "component_id": str(component_id)}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish COMPONENT_DELETED event: {exc}")
    return OKResponse(message="Component deleted")


# ══════════════════════════════════════════════════════════════════════════════
# Production Lines (MDM Module)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/production-lines", response_model=List[ProductionLineResponse], summary="List production lines")
async def list_production_lines(
    factory_id: Optional[UUID] = None,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    return svc.list_production_lines(current_user.user_id, factory_id=factory_id)


@router.post("/production-lines", response_model=ProductionLineResponse, status_code=status.HTTP_201_CREATED, summary="Create production line")
async def create_production_line(
    data: ProductionLineCreate,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    res = svc.create_production_line(current_user.user_id, data)
    try:
        await event_bus.publish(Event(
            type=EventType.PRODUCTION_LINE_CREATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "line_id": str(res["id"])}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish PRODUCTION_LINE_CREATED event: {exc}")
    return res


@router.put("/production-lines/{line_id}", response_model=ProductionLineResponse, summary="Update production line")
async def update_production_line(
    line_id: UUID,
    data: ProductionLineUpdate,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    res = svc.update_production_line(current_user.user_id, line_id, data)
    try:
        await event_bus.publish(Event(
            type=EventType.PRODUCTION_LINE_UPDATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "line_id": str(line_id)}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish PRODUCTION_LINE_UPDATED event: {exc}")
    return res


@router.delete("/production-lines/{line_id}", response_model=OKResponse, summary="Delete production line")
async def delete_production_line(
    line_id: UUID,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    svc.delete_production_line(current_user.user_id, line_id)
    try:
        await event_bus.publish(Event(
            type=EventType.PRODUCTION_LINE_DELETED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "line_id": str(line_id)}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish PRODUCTION_LINE_DELETED event: {exc}")
    return OKResponse(message="Production line deleted")


# ══════════════════════════════════════════════════════════════════════════════
# Bills of Materials (BOM) (MDM Module)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/bom", response_model=List[BOMItemResponse], summary="List BOM items")
async def list_bom_items(
    product_id: Optional[UUID] = None,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    return svc.list_bom_items(current_user.user_id, product_id=product_id)


@router.post("/bom", response_model=BOMItemResponse, status_code=status.HTTP_201_CREATED, summary="Create BOM item")
async def create_bom_item(
    data: BOMItemCreate,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    res = svc.create_bom_item(current_user.user_id, data)
    try:
        await event_bus.publish(Event(
            type=EventType.BOM_UPDATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "bom_id": str(res["id"])}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish BOM_UPDATED event: {exc}")
    return res


@router.delete("/bom/{bom_id}", response_model=OKResponse, summary="Delete BOM item")
async def delete_bom_item(
    bom_id: UUID,
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    svc.delete_bom_item(current_user.user_id, bom_id)
    try:
        await event_bus.publish(Event(
            type=EventType.BOM_UPDATED,
            source="manufacturer.router",
            payload={"user_id": current_user.user_id, "bom_id": str(bom_id)}
        ))
    except Exception as exc:
        logger.warning(f"Failed to publish BOM_UPDATED event: {exc}")
    return OKResponse(message="BOM item deleted")


# ══════════════════════════════════════════════════════════════════════════════
# Complete setup (Step 7 → Finish)
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/complete-setup",
    response_model=CompleteSetupResponse,
    summary="Finalise onboarding — activates AI monitoring",
    description=(
        "Marks onboarding_complete=true. "
        "After this call, GET /manufacturer/setup-status returns { complete: true } "
        "and the frontend redirects to /dashboard."
    ),
)
async def complete_setup(
    current_user: UserPrincipal = Depends(get_current_user),
    svc: ManufacturerService = Depends(_svc),
):
    result = svc.complete_setup(current_user.user_id)
    return result
