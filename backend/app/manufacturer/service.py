"""
app/manufacturer/service.py — Business logic for the manufacturer onboarding wizard.

All methods receive the authenticated user_id (Supabase auth.uid()) to enforce
data isolation without relying solely on database-level RLS.
"""
from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.manufacturer.models import (
    ManufacturerCompany,
    ManufacturerFactory,
    ManufacturerWarehouse,
    ManufacturerProduct,
    ManufacturerComponent,
)
from app.manufacturer.schemas import (
    CompanyCreate,
    CompanyUpdate,
    FactoryCreate,
    FactoryUpdate,
    WarehouseCreate,
    WarehouseUpdate,
    ProductCreate,
    ProductUpdate,
    ComponentCreate,
    ComponentUpdate,
)

logger = logging.getLogger("manufacturer.service")


class ManufacturerService:
    """Stateless service — receives a db Session per request."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ──────────────────────────────────────────────────────────────────────────
    # Setup status
    # ──────────────────────────────────────────────────────────────────────────

    def get_setup_status(self, user_id: str) -> dict:
        company = self.db.get(ManufacturerCompany, user_id)
        if company is None:
            return {"complete": False, "current_step": 1, "company_exists": False}
        return {
            "complete":       company.onboarding_complete,
            "current_step":   company.onboarding_step,
            "company_exists": True,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Company CRUD
    # ──────────────────────────────────────────────────────────────────────────

    def get_company(self, user_id: str) -> Optional[ManufacturerCompany]:
        return self.db.get(ManufacturerCompany, user_id)

    def create_or_update_company(self, user_id: str, data: CompanyCreate) -> ManufacturerCompany:
        """Upsert — creates if missing, updates if exists."""
        company = self.db.get(ManufacturerCompany, user_id)
        payload = data.model_dump(exclude_none=False)
        if company is None:
            company = ManufacturerCompany(user_id=user_id, **payload)
            self.db.add(company)
            logger.info("Created manufacturer company for user_id=%s", user_id)
        else:
            for k, v in payload.items():
                setattr(company, k, v)
            logger.info("Updated manufacturer company for user_id=%s", user_id)
        self.db.commit()
        self.db.refresh(company)
        return company

    def advance_step(self, user_id: str, step: int) -> None:
        """Move onboarding_step forward (never backward)."""
        company = self.db.get(ManufacturerCompany, user_id)
        if company and company.onboarding_step < step:
            company.onboarding_step = step
            self.db.commit()

    # ──────────────────────────────────────────────────────────────────────────
    # Factory CRUD
    # ──────────────────────────────────────────────────────────────────────────

    def list_factories(self, user_id: str) -> List[ManufacturerFactory]:
        return (
            self.db.query(ManufacturerFactory)
            .filter(ManufacturerFactory.company_user_id == user_id)
            .order_by(ManufacturerFactory.created_at)
            .all()
        )

    def create_factory(self, user_id: str, data: FactoryCreate) -> ManufacturerFactory:
        self._require_company(user_id)
        factory = ManufacturerFactory(
            company_user_id=user_id,
            **data.model_dump(exclude_none=True),
        )
        self.db.add(factory)
        self.db.commit()
        self.db.refresh(factory)
        return factory

    def update_factory(self, user_id: str, factory_id: UUID,
                       data: FactoryUpdate) -> ManufacturerFactory:
        factory = self._get_factory(user_id, factory_id)
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(factory, k, v)
        self.db.commit()
        self.db.refresh(factory)
        return factory

    def delete_factory(self, user_id: str, factory_id: UUID) -> None:
        factory = self._get_factory(user_id, factory_id)
        self.db.delete(factory)
        self.db.commit()

    def _get_factory(self, user_id: str, factory_id: UUID) -> ManufacturerFactory:
        factory = (
            self.db.query(ManufacturerFactory)
            .filter_by(id=factory_id, company_user_id=user_id)
            .first()
        )
        if factory is None:
            from fastapi import HTTPException, status
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Factory not found")
        return factory

    # ──────────────────────────────────────────────────────────────────────────
    # Warehouse CRUD
    # ──────────────────────────────────────────────────────────────────────────

    def list_warehouses(self, user_id: str) -> List[ManufacturerWarehouse]:
        return (
            self.db.query(ManufacturerWarehouse)
            .filter(ManufacturerWarehouse.company_user_id == user_id)
            .order_by(ManufacturerWarehouse.created_at)
            .all()
        )

    def create_warehouse(self, user_id: str, data: WarehouseCreate) -> ManufacturerWarehouse:
        self._require_company(user_id)
        wh = ManufacturerWarehouse(
            company_user_id=user_id,
            **data.model_dump(exclude_none=True),
        )
        self.db.add(wh)
        self.db.commit()
        self.db.refresh(wh)
        return wh

    def update_warehouse(self, user_id: str, warehouse_id: UUID,
                         data: WarehouseUpdate) -> ManufacturerWarehouse:
        wh = self._get_warehouse(user_id, warehouse_id)
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(wh, k, v)
        self.db.commit()
        self.db.refresh(wh)
        return wh

    def delete_warehouse(self, user_id: str, warehouse_id: UUID) -> None:
        wh = self._get_warehouse(user_id, warehouse_id)
        self.db.delete(wh)
        self.db.commit()

    def _get_warehouse(self, user_id: str, warehouse_id: UUID) -> ManufacturerWarehouse:
        wh = (
            self.db.query(ManufacturerWarehouse)
            .filter_by(id=warehouse_id, company_user_id=user_id)
            .first()
        )
        if wh is None:
            from fastapi import HTTPException, status
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Warehouse not found")
        return wh

    # ──────────────────────────────────────────────────────────────────────────
    # Product CRUD
    # ──────────────────────────────────────────────────────────────────────────

    def list_products(self, user_id: str) -> List[ManufacturerProduct]:
        return (
            self.db.query(ManufacturerProduct)
            .filter(ManufacturerProduct.company_user_id == user_id)
            .order_by(ManufacturerProduct.created_at)
            .all()
        )

    def create_product(self, user_id: str, data: ProductCreate) -> ManufacturerProduct:
        self._require_company(user_id)
        product = ManufacturerProduct(
            company_user_id=user_id,
            **data.model_dump(exclude_none=True),
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_product(self, user_id: str, product_id: UUID,
                       data: ProductUpdate) -> ManufacturerProduct:
        product = self._get_product(user_id, product_id)
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(product, k, v)
        self.db.commit()
        self.db.refresh(product)
        return product

    def delete_product(self, user_id: str, product_id: UUID) -> None:
        product = self._get_product(user_id, product_id)
        self.db.delete(product)
        self.db.commit()

    def _get_product(self, user_id: str, product_id: UUID) -> ManufacturerProduct:
        product = (
            self.db.query(ManufacturerProduct)
            .filter_by(id=product_id, company_user_id=user_id)
            .first()
        )
        if product is None:
            from fastapi import HTTPException, status
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
        return product

    # ──────────────────────────────────────────────────────────────────────────
    # Component CRUD
    # ──────────────────────────────────────────────────────────────────────────

    def list_components(self, user_id: str,
                        product_id: Optional[UUID] = None) -> List[ManufacturerComponent]:
        q = self.db.query(ManufacturerComponent).filter(
            ManufacturerComponent.company_user_id == user_id
        )
        if product_id is not None:
            q = q.filter(ManufacturerComponent.product_id == product_id)
        return q.order_by(ManufacturerComponent.created_at).all()

    def create_component(self, user_id: str, data: ComponentCreate) -> ManufacturerComponent:
        self._require_company(user_id)
        component = ManufacturerComponent(
            company_user_id=user_id,
            **data.model_dump(exclude_none=True),
        )
        self.db.add(component)
        self.db.commit()
        self.db.refresh(component)
        return component

    def update_component(self, user_id: str, component_id: UUID,
                         data: ComponentUpdate) -> ManufacturerComponent:
        component = self._get_component(user_id, component_id)
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(component, k, v)
        self.db.commit()
        self.db.refresh(component)
        return component

    def delete_component(self, user_id: str, component_id: UUID) -> None:
        component = self._get_component(user_id, component_id)
        self.db.delete(component)
        self.db.commit()

    def _get_component(self, user_id: str, component_id: UUID) -> ManufacturerComponent:
        component = (
            self.db.query(ManufacturerComponent)
            .filter_by(id=component_id, company_user_id=user_id)
            .first()
        )
        if component is None:
            from fastapi import HTTPException, status
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Component not found")
        return component

    # ──────────────────────────────────────────────────────────────────────────
    # Complete setup
    # ──────────────────────────────────────────────────────────────────────────

    def complete_setup(self, user_id: str) -> dict:
        """
        Mark onboarding as complete.
        Returns a summary dict the frontend uses to confirm everything was saved.
        """
        company = self._require_company(user_id)
        company.onboarding_complete = True
        company.onboarding_step = 7
        self.db.commit()
        self.db.refresh(company)
        logger.info("Manufacturer onboarding COMPLETE for user_id=%s company=%s",
                    user_id, company.name)
        return {
            "success":  True,
            "message":  "Onboarding complete. AI monitoring activated.",
            "redirect": "/dashboard",
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Production Line CRUD
    # ──────────────────────────────────────────────────────────────────────────

    def list_production_lines(self, user_id: str, factory_id: Optional[UUID] = None) -> List[dict]:
        from app.manufacturer.models import ManufacturerProductionLine
        q = self.db.query(ManufacturerProductionLine).filter(
            ManufacturerProductionLine.company_user_id == user_id
        )
        if factory_id is not None:
            q = q.filter(ManufacturerProductionLine.factory_id == factory_id)
        lines = q.order_by(ManufacturerProductionLine.created_at).all()
        res = []
        for line in lines:
            d = {
                "id": line.id,
                "company_user_id": line.company_user_id,
                "factory_id": line.factory_id,
                "factory_name": line.factory.factory_name if line.factory else None,
                "line_name": line.line_name,
                "line_code": line.line_code,
                "capacity_per_hour": line.capacity_per_hour,
                "operating_status": line.operating_status,
                "created_at": line.created_at,
                "updated_at": line.updated_at,
            }
            res.append(d)
        return res

    def create_production_line(self, user_id: str, data: ProductionLineCreate):
        from app.manufacturer.models import ManufacturerProductionLine
        self._require_company(user_id)
        line = ManufacturerProductionLine(
            company_user_id=user_id,
            **data.model_dump(exclude_none=True),
        )
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return {
            "id": line.id,
            "company_user_id": line.company_user_id,
            "factory_id": line.factory_id,
            "factory_name": line.factory.factory_name if line.factory else None,
            "line_name": line.line_name,
            "line_code": line.line_code,
            "capacity_per_hour": line.capacity_per_hour,
            "operating_status": line.operating_status,
            "created_at": line.created_at,
            "updated_at": line.updated_at,
        }

    def update_production_line(self, user_id: str, line_id: UUID, data: ProductionLineUpdate):
        from app.manufacturer.models import ManufacturerProductionLine
        from fastapi import HTTPException, status
        line = self.db.query(ManufacturerProductionLine).filter_by(id=line_id, company_user_id=user_id).first()
        if not line:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Production line not found")
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(line, k, v)
        self.db.commit()
        self.db.refresh(line)
        return {
            "id": line.id,
            "company_user_id": line.company_user_id,
            "factory_id": line.factory_id,
            "factory_name": line.factory.factory_name if line.factory else None,
            "line_name": line.line_name,
            "line_code": line.line_code,
            "capacity_per_hour": line.capacity_per_hour,
            "operating_status": line.operating_status,
            "created_at": line.created_at,
            "updated_at": line.updated_at,
        }

    def delete_production_line(self, user_id: str, line_id: UUID) -> None:
        from app.manufacturer.models import ManufacturerProductionLine
        from fastapi import HTTPException, status
        line = self.db.query(ManufacturerProductionLine).filter_by(id=line_id, company_user_id=user_id).first()
        if not line:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Production line not found")
        self.db.delete(line)
        self.db.commit()

    # ──────────────────────────────────────────────────────────────────────────
    # BOM CRUD
    # ──────────────────────────────────────────────────────────────────────────

    def list_bom_items(self, user_id: str, product_id: Optional[UUID] = None) -> List[dict]:
        from app.manufacturer.models import ManufacturerBOM
        q = self.db.query(ManufacturerBOM).filter(
            ManufacturerBOM.company_user_id == user_id
        )
        if product_id is not None:
            q = q.filter(ManufacturerBOM.product_id == product_id)
        items = q.order_by(ManufacturerBOM.created_at).all()
        res = []
        for item in items:
            d = {
                "id": item.id,
                "company_user_id": item.company_user_id,
                "product_id": item.product_id,
                "component_id": item.component_id,
                "product_name": item.product.product_name if item.product else None,
                "component_name": item.component.component_name if item.component else None,
                "quantity_required": item.quantity_required,
                "notes": item.notes,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            res.append(d)
        return res

    def create_bom_item(self, user_id: str, data: BOMItemCreate):
        from app.manufacturer.models import ManufacturerBOM
        self._require_company(user_id)
        bom = ManufacturerBOM(
            company_user_id=user_id,
            **data.model_dump(exclude_none=True),
        )
        self.db.add(bom)
        self.db.commit()
        self.db.refresh(bom)
        return {
            "id": bom.id,
            "company_user_id": bom.company_user_id,
            "product_id": bom.product_id,
            "component_id": bom.component_id,
            "product_name": bom.product.product_name if bom.product else None,
            "component_name": bom.component.component_name if bom.component else None,
            "quantity_required": bom.quantity_required,
            "notes": bom.notes,
            "created_at": bom.created_at,
            "updated_at": bom.updated_at,
        }

    def delete_bom_item(self, user_id: str, bom_id: UUID) -> None:
        from app.manufacturer.models import ManufacturerBOM
        from fastapi import HTTPException, status
        bom = self.db.query(ManufacturerBOM).filter_by(id=bom_id, company_user_id=user_id).first()
        if not bom:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "BOM item not found")
        self.db.delete(bom)
        self.db.commit()

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _require_company(self, user_id: str) -> ManufacturerCompany:
        """Raise 404 if company row doesn't exist yet."""
        company = self.db.get(ManufacturerCompany, user_id)
        if company is None:
            from fastapi import HTTPException, status
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Company not found. Complete Step 1 (Company Information) first.",
            )
        return company
