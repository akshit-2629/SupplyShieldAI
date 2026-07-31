"""
Supplier Portal Test Suite
Tests for auth, profile, inventory, incidents, and shipments.
Uses FastAPI TestClient with SQLite in-memory DB for isolation.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_supplier_user():
    """Mock UserPrincipal for an approved supplier."""
    user = MagicMock()
    user.user_id = "test-supplier-uid-12345"
    user.email = "supplier@testcompany.com"
    user.role = "supplier"
    user.is_supplier = True
    user.is_approved = True
    user.is_admin = False
    user.user_metadata = {"role": "supplier", "is_approved": True}
    return user


@pytest.fixture
def mock_admin_user():
    """Mock UserPrincipal for an admin."""
    user = MagicMock()
    user.user_id = "admin-uid-12345"
    user.email = "admin@supplyshield.ai"
    user.role = "admin"
    user.is_supplier = False
    user.is_approved = False
    user.is_admin = True
    user.user_metadata = {"role": "admin"}
    return user


# ── Schema Validation Tests ───────────────────────────────────────────────────

class TestAuthSchemas:
    def test_register_request_valid(self):
        from app.supplier_portal.schemas.auth import SupplierRegisterRequest
        req = SupplierRegisterRequest(
            email="supplier@company.com",
            password="SecurePass1!",
            company_name="Acme Corp",
            contact_name="John Doe",
        )
        assert req.email == "supplier@company.com"
        assert req.company_name == "Acme Corp"

    def test_register_request_weak_password(self):
        from app.supplier_portal.schemas.auth import SupplierRegisterRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            SupplierRegisterRequest(
                email="test@test.com",
                password="weak",
                company_name="Co",
                contact_name="Jane",
            )
        assert "Password" in str(exc_info.value) or "8 characters" in str(exc_info.value)

    def test_register_request_invalid_email(self):
        from app.supplier_portal.schemas.auth import SupplierRegisterRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SupplierRegisterRequest(
                email="not-an-email",
                password="SecurePass1!",
                company_name="Co",
                contact_name="Jane",
            )

    def test_change_password_mismatch(self):
        from app.supplier_portal.schemas.auth import ChangePasswordRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ChangePasswordRequest(
                new_password="SecurePass1!",
                confirm_password="DifferentPass1!",
            )

    def test_change_password_match(self):
        from app.supplier_portal.schemas.auth import ChangePasswordRequest
        req = ChangePasswordRequest(
            new_password="SecurePass1!",
            confirm_password="SecurePass1!",
        )
        assert req.new_password == "SecurePass1!"


class TestInventorySchemas:
    def test_inventory_item_create_valid(self):
        from app.supplier_portal.schemas.modules import InventoryItemCreate
        item = InventoryItemCreate(
            sku="SKU-001",
            name="Aluminium Sheets",
            quantity_on_hand=500,
            safety_stock_level=100,
        )
        assert item.sku == "SKU-001"
        assert item.is_critical_component is False

    def test_inventory_item_negative_quantity_fails(self):
        from app.supplier_portal.schemas.modules import InventoryItemCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            InventoryItemCreate(sku="X", name="X", quantity_on_hand=-1)

    def test_inventory_item_update_optional_fields(self):
        from app.supplier_portal.schemas.modules import InventoryItemUpdate
        update = InventoryItemUpdate(quantity_on_hand=200)
        assert update.quantity_on_hand == 200
        assert update.name is None


class TestIncidentSchemas:
    def test_incident_create_valid(self):
        from app.supplier_portal.schemas.modules import IncidentCreate, IncidentType, IncidentSeverity
        incident = IncidentCreate(
            incident_type=IncidentType.FLOOD,
            severity=IncidentSeverity.HIGH,
            title="Factory flooding in Building A",
            description="Heavy monsoon caused partial flooding of the manufacturing floor.",
        )
        assert incident.incident_type == IncidentType.FLOOD
        assert incident.severity == IncidentSeverity.HIGH

    def test_incident_short_description_fails(self):
        from app.supplier_portal.schemas.modules import IncidentCreate, IncidentType
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            IncidentCreate(
                incident_type=IncidentType.OTHER,
                title="Test",
                description="Too short",  # < 10 chars
            )

    def test_incident_capacity_impact_range(self):
        from app.supplier_portal.schemas.modules import IncidentCreate, IncidentType
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            IncidentCreate(
                incident_type=IncidentType.OTHER,
                title="Valid Title Here",
                description="This is a valid description with enough characters.",
                capacity_impact_pct=150,  # > 100
            )


class TestShipmentSchemas:
    def test_shipment_create_valid(self):
        from app.supplier_portal.schemas.modules import ShipmentCreate, ShipmentStatus
        shipment = ShipmentCreate(
            shipment_number="SHP-2024-001",
            status=ShipmentStatus.PREPARING,
            carrier_name="FedEx Freight",
            origin_country="CN",
            destination_country="US",
        )
        assert shipment.shipment_number == "SHP-2024-001"

    def test_shipment_status_enum(self):
        from app.supplier_portal.schemas.modules import ShipmentStatus
        assert "IN_TRANSIT" in [s.value for s in ShipmentStatus]
        assert "DELIVERED" in [s.value for s in ShipmentStatus]


class TestForecastSchemas:
    def test_forecast_valid(self):
        from app.supplier_portal.schemas.modules import ForecastSubmitRequest, ForecastEntry
        req = ForecastSubmitRequest(
            forecast_year=2025,
            period_type="monthly",
            entries=[
                ForecastEntry(forecast_month=1, forecasted_output=10000, maximum_capacity=12000),
                ForecastEntry(forecast_month=2, forecasted_output=11000, maximum_capacity=12000),
            ]
        )
        assert len(req.entries) == 2

    def test_forecast_invalid_year(self):
        from app.supplier_portal.schemas.modules import ForecastSubmitRequest, ForecastEntry
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ForecastSubmitRequest(
                forecast_year=1990,  # < 2020
                period_type="monthly",
                entries=[ForecastEntry(forecast_month=1)]
            )

    def test_forecast_invalid_month(self):
        from app.supplier_portal.schemas.modules import ForecastEntry
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ForecastEntry(forecast_month=13)  # > 12


# ── Repository Unit Tests ─────────────────────────────────────────────────────

class TestBaseRepository:
    def test_total_pages(self):
        from app.supplier_portal.repositories.base_repo import BaseRepository
        repo = BaseRepository.__new__(BaseRepository)
        assert repo.total_pages(total=100, page_size=20) == 5
        assert repo.total_pages(total=21, page_size=20) == 2
        assert repo.total_pages(total=0, page_size=20) == 0

    def test_paginate_helper(self):
        from app.supplier_portal.schemas.common import paginate
        result = paginate(total=47, page=2, page_size=10)
        assert result["total"] == 47
        assert result["total_pages"] == 5
        assert result["page"] == 2


# ── Service Unit Tests ────────────────────────────────────────────────────────

class TestLeadTimeService:
    def test_compute_total_days(self):
        """_compute_total correctly sums lead time components."""
        from app.supplier_portal.services.services import LeadTimeService
        svc = LeadTimeService.__new__(LeadTimeService)
        data = {
            "manufacturing_days": 10,
            "packaging_days": 2,
            "quality_check_days": 3,
            "shipping_days": 7,
            "customs_days": 2,
        }
        result = svc._compute_total(data)
        assert result["total_lead_time_days"] == 24

    def test_compute_total_respects_existing(self):
        """_compute_total does not overwrite if total already set."""
        from app.supplier_portal.services.services import LeadTimeService
        svc = LeadTimeService.__new__(LeadTimeService)
        data = {
            "manufacturing_days": 5,
            "total_lead_time_days": 99,  # already present
        }
        result = svc._compute_total(data)
        assert result["total_lead_time_days"] == 99


class TestInventoryService:
    def test_compute_low_stock_flag(self):
        """is_low_stock computed correctly when below safety stock."""
        from app.supplier_portal.services.services import InventoryService
        from app.supplier_portal.models.inventory_item import SupplierInventoryItem
        svc = InventoryService.__new__(InventoryService)

        item = SupplierInventoryItem()
        item.quantity_on_hand = 50
        item.safety_stock_level = 100
        svc._compute_flags(item)
        assert item.is_low_stock is True

        item.quantity_on_hand = 200
        svc._compute_flags(item)
        assert item.is_low_stock is False

        item.safety_stock_level = 0
        svc._compute_flags(item)
        assert item.is_low_stock is False


# ── Orchestrator Bridge Tests ─────────────────────────────────────────────────

class TestOrchestratorBridge:
    @pytest.mark.asyncio
    async def test_notify_handles_orchestrator_not_initialized(self):
        """Bridge should NOT raise when orchestrator is not ready."""
        from app.supplier_portal.services.orchestrator_bridge import OrchestratorBridge
        bridge = OrchestratorBridge()
        with patch("app.supplier_portal.services.orchestrator_bridge.asyncio.create_task") as mock_task:
            with patch("app.orchestrator.orchestrator.MasterOrchestrator.get_instance") as mock_get:
                mock_get.side_effect = RuntimeError("Not initialized")
                # Should not raise
                await bridge.notify("supplier_portal.incident_reported", "supplier-uid-123", {})

    @pytest.mark.asyncio
    async def test_notify_dispatches_to_orchestrator(self):
        """Bridge dispatches event when orchestrator is ready."""
        from app.supplier_portal.services.orchestrator_bridge import OrchestratorBridge
        bridge = OrchestratorBridge()

        mock_orchestrator = MagicMock()
        mock_orchestrator.trigger = AsyncMock(return_value={"status": "completed"})

        with patch("app.supplier_portal.services.orchestrator_bridge.asyncio.create_task") as mock_task:
            with patch("app.orchestrator.orchestrator.MasterOrchestrator.get_instance",
                       return_value=mock_orchestrator):
                await bridge.notify(
                    "supplier_portal.inventory_updated",
                    "supplier-uid-456",
                    {"item_id": "uuid-123"}
                )
                mock_task.assert_called_once()


# ── Security / Role Tests ─────────────────────────────────────────────────────

class TestSecurityDependencies:
    def test_user_principal_is_supplier(self):
        from app.core.security import UserPrincipal
        user = UserPrincipal(
            user_id="uid", email="x@x.com", roles=["supplier"],
            user_metadata={"role": "supplier", "is_approved": True}
        )
        assert user.is_supplier is True
        assert user.is_admin is False
        assert user.is_approved is True

    def test_user_principal_pending_supplier(self):
        from app.core.security import UserPrincipal
        user = UserPrincipal(
            user_id="uid", email="x@x.com", roles=["supplier"],
            user_metadata={"role": "supplier", "is_approved": False}
        )
        assert user.is_supplier is True
        assert user.is_approved is False

    def test_user_principal_admin(self):
        from app.core.security import UserPrincipal
        user = UserPrincipal(
            user_id="uid", email="admin@x.com", roles=["admin"],
            user_metadata={"role": "admin"}
        )
        assert user.is_admin is True
        assert user.is_supplier is False

    @pytest.mark.asyncio
    async def test_require_supplier_blocks_non_supplier(self):
        from app.core.security import require_supplier, UserPrincipal
        from fastapi import HTTPException
        user = UserPrincipal(
            user_id="uid", email="x@x.com", roles=["authenticated"],
            user_metadata={}
        )
        with pytest.raises(HTTPException) as exc_info:
            await require_supplier(current_user=user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_supplier_blocks_unapproved(self):
        from app.core.security import require_supplier, UserPrincipal
        from fastapi import HTTPException
        user = UserPrincipal(
            user_id="uid", email="x@x.com", roles=["supplier"],
            user_metadata={"role": "supplier", "is_approved": False}
        )
        with pytest.raises(HTTPException) as exc_info:
            await require_supplier(current_user=user)
        assert exc_info.value.status_code == 403
        assert "pending" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_require_supplier_allows_approved(self):
        from app.core.security import require_supplier, UserPrincipal
        user = UserPrincipal(
            user_id="uid", email="x@x.com", roles=["supplier"],
            user_metadata={"role": "supplier", "is_approved": True}
        )
        result = await require_supplier(current_user=user)
        assert result.user_id == "uid"
