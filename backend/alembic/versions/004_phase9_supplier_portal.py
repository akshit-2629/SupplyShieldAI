"""004 — Phase 9: Supplier Portal (11 core tables).

Revision:    004_phase9_supplier_portal
Revises:     003_phase6_7_8_analytics
Create Date: 2026-07-20

Tables created (11):
  supplier_accounts, supplier_company_profiles, supplier_production_capacity,
  supplier_inventory_items, supplier_lead_times, supplier_shipments,
  supplier_incidents, supplier_capacity_forecasts, supplier_notifications,
  supplier_support_tickets, supplier_audit_logs
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "004_phase9_supplier_portal"
down_revision = "003_phase6_7_8_analytics"
branch_labels = None
depends_on = None

PORTAL_TABLES = [
    "supplier_audit_logs",
    "supplier_support_tickets",
    "supplier_notifications",
    "supplier_capacity_forecasts",
    "supplier_incidents",
    "supplier_shipments",
    "supplier_lead_times",
    "supplier_inventory_items",
    "supplier_production_capacity",
    "supplier_company_profiles",
    "supplier_accounts",
]


def upgrade() -> None:
    # ── supplier_accounts ─────────────────────────────────────────────────────
    op.create_table(
        "supplier_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supabase_uid", sa.Text, unique=True, nullable=False),
        sa.Column("email", sa.Text, unique=True, nullable=False),
        sa.Column("company_name", sa.Text, nullable=False),
        sa.Column("contact_name", sa.Text, nullable=False),
        sa.Column("phone", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("rejection_reason", sa.Text),
        sa.Column("reviewed_by", sa.Text),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_supplier_accounts_supabase_uid", "supplier_accounts", ["supabase_uid"], unique=True)
    op.create_index("idx_supplier_accounts_email", "supplier_accounts", ["email"], unique=True)
    op.create_index("idx_supplier_accounts_status", "supplier_accounts", ["status"])

    # ── supplier_company_profiles ─────────────────────────────────────────────
    op.create_table(
        "supplier_company_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, unique=True, nullable=False),
        sa.Column("company_name", sa.Text, nullable=False),
        sa.Column("legal_name", sa.Text),
        sa.Column("registration_number", sa.Text),
        sa.Column("tax_id", sa.Text),
        sa.Column("year_established", sa.Integer),
        sa.Column("employee_count", sa.Integer),
        sa.Column("annual_revenue_usd", sa.Text),
        sa.Column("description", sa.Text),
        sa.Column("website", sa.Text),
        sa.Column("email", sa.Text),
        sa.Column("phone", sa.Text),
        sa.Column("headquarters_address", sa.Text),
        sa.Column("headquarters_country", sa.Text),
        sa.Column("headquarters_city", sa.Text),
        sa.Column("logo_url", sa.Text),
        sa.Column("locations", JSONB),
        sa.Column("contacts", JSONB),
        sa.Column("manufacturing_categories", JSONB),
        sa.Column("products", JSONB),
        sa.Column("certifications", JSONB),
        sa.Column("documents", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_company_profiles_supplier_id", "supplier_company_profiles", ["supplier_id"])

    # ── supplier_production_capacity ──────────────────────────────────────────
    op.create_table(
        "supplier_production_capacity",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("maximum_capacity_units", sa.Integer),
        sa.Column("current_output_units", sa.Integer),
        sa.Column("utilization_pct", sa.Numeric(5, 2)),
        sa.Column("production_rate_per_day", sa.Numeric(10, 2)),
        sa.Column("workforce_count", sa.Integer),
        sa.Column("shifts_per_day", sa.SmallInteger),
        sa.Column("factory_status", sa.String(20), server_default="OPERATIONAL"),
        sa.Column("planned_downtime_days", sa.Integer, server_default="0"),
        sa.Column("next_maintenance_date", sa.DateTime(timezone=True)),
        sa.Column("maintenance_notes", sa.Text),
        sa.Column("machine_utilization", JSONB),
        sa.Column("notes", sa.Text),
        sa.Column("submitted_by", sa.Text),
        sa.Column("ip_address", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_prod_capacity_supplier_id", "supplier_production_capacity", ["supplier_id"])
    op.create_index("idx_prod_capacity_created_at", "supplier_production_capacity", ["created_at"],
                    postgresql_ops={"created_at": "DESC"})

    # ── supplier_inventory_items ──────────────────────────────────────────────
    op.create_table(
        "supplier_inventory_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("sku", sa.Text, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.Text),
        sa.Column("unit", sa.String(50), server_default="units"),
        sa.Column("quantity_on_hand", sa.Integer, nullable=False, server_default="0"),
        sa.Column("safety_stock_level", sa.Integer, server_default="0"),
        sa.Column("reorder_point", sa.Integer, server_default="0"),
        sa.Column("maximum_stock", sa.Integer),
        sa.Column("warehouse_id", sa.Text),
        sa.Column("warehouse_location", sa.Text),
        sa.Column("unit_cost_usd", sa.Numeric(14, 4)),
        sa.Column("is_low_stock", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_critical_component", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("supplier_id", "sku", name="uq_inventory_supplier_sku"),
    )
    op.create_index("idx_inventory_items_supplier_id", "supplier_inventory_items", ["supplier_id"])
    op.create_index("idx_inventory_items_sku", "supplier_inventory_items", ["sku"])
    op.create_index("idx_inventory_items_is_low_stock", "supplier_inventory_items", ["is_low_stock"])

    # ── supplier_lead_times ───────────────────────────────────────────────────
    op.create_table(
        "supplier_lead_times",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("product_sku", sa.Text),
        sa.Column("product_name", sa.Text),
        sa.Column("category", sa.Text),
        sa.Column("manufacturing_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("packaging_days", sa.Integer, server_default="0"),
        sa.Column("quality_check_days", sa.Integer, server_default="0"),
        sa.Column("shipping_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("customs_days", sa.Integer, server_default="0"),
        sa.Column("total_lead_time_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("average_delay_days", sa.Numeric(6, 2), server_default="0"),
        sa.Column("expected_delivery_days", sa.Integer),
        sa.Column("destination_country", sa.Text),
        sa.Column("shipping_method", sa.Text),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_lead_times_supplier_id", "supplier_lead_times", ["supplier_id"])

    # ── supplier_shipments ────────────────────────────────────────────────────
    op.create_table(
        "supplier_shipments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("shipment_number", sa.Text, nullable=False),
        sa.Column("tracking_number", sa.Text),
        sa.Column("purchase_order_number", sa.Text),
        sa.Column("status", sa.String(30), nullable=False, server_default="PREPARING"),
        sa.Column("carrier_name", sa.Text),
        sa.Column("carrier_code", sa.Text),
        sa.Column("shipping_method", sa.Text),
        sa.Column("origin_country", sa.Text),
        sa.Column("origin_city", sa.Text),
        sa.Column("destination_country", sa.Text),
        sa.Column("destination_city", sa.Text),
        sa.Column("destination_address", sa.Text),
        sa.Column("shipped_at", sa.DateTime(timezone=True)),
        sa.Column("estimated_arrival", sa.DateTime(timezone=True)),
        sa.Column("actual_arrival", sa.DateTime(timezone=True)),
        sa.Column("quantity", sa.Integer),
        sa.Column("unit", sa.Text),
        sa.Column("weight_kg", sa.Float),
        sa.Column("volume_m3", sa.Float),
        sa.Column("items", JSONB),
        sa.Column("timeline", JSONB),
        sa.Column("notes", sa.Text),
        sa.Column("customs_status", sa.Text),
        sa.Column("incoterms", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_shipments_supplier_id", "supplier_shipments", ["supplier_id"])
    op.create_index("idx_shipments_tracking_number", "supplier_shipments", ["tracking_number"])
    op.create_index("idx_shipments_status", "supplier_shipments", ["status"])
    op.create_index("idx_shipments_estimated_arrival", "supplier_shipments", ["estimated_arrival"])

    # ── supplier_incidents ────────────────────────────────────────────────────
    op.create_table(
        "supplier_incidents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("incident_type", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("affected_products", JSONB),
        sa.Column("affected_countries", JSONB),
        sa.Column("estimated_recovery_days", sa.Integer),
        sa.Column("capacity_impact_pct", sa.SmallInteger),
        sa.Column("attachments", JSONB),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolution_notes", sa.Text),
        sa.Column("ip_address", sa.Text),
        sa.Column("is_deleted", sa.SmallInteger, server_default="0"),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_incidents_supplier_id", "supplier_incidents", ["supplier_id"])
    op.create_index("idx_incidents_severity", "supplier_incidents", ["severity"])
    op.create_index("idx_incidents_status", "supplier_incidents", ["status"])

    # ── supplier_capacity_forecasts ───────────────────────────────────────────
    op.create_table(
        "supplier_capacity_forecasts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("forecast_year", sa.Integer, nullable=False),
        sa.Column("forecast_month", sa.SmallInteger),
        sa.Column("period_type", sa.String(20), server_default="monthly"),
        sa.Column("quarter", sa.SmallInteger),
        sa.Column("forecasted_output", sa.Integer),
        sa.Column("maximum_capacity", sa.Integer),
        sa.Column("planned_downtime_days", sa.SmallInteger, server_default="0"),
        sa.Column("status", sa.String(20), server_default="DRAFT"),
        sa.Column("submitted_by", sa.Text),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_forecasts_supplier_id", "supplier_capacity_forecasts", ["supplier_id"])
    op.create_index("idx_forecasts_year_month", "supplier_capacity_forecasts",
                    ["forecast_year", "forecast_month"])

    # ── supplier_notifications ────────────────────────────────────────────────
    op.create_table(
        "supplier_notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("category", sa.String(30), nullable=False, server_default="GENERAL"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="NORMAL"),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("body", sa.Text),
        sa.Column("action_url", sa.Text),
        sa.Column("extra_metadata", JSONB),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_notifications_supplier_id", "supplier_notifications", ["supplier_id"])
    op.create_index("idx_notifications_is_read", "supplier_notifications", ["is_read"])
    op.create_index("idx_notifications_created_at", "supplier_notifications", ["created_at"],
                    postgresql_ops={"created_at": "DESC"})

    # ── supplier_support_tickets ──────────────────────────────────────────────
    op.create_table(
        "supplier_support_tickets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("ticket_number", sa.Text, unique=True, nullable=False),
        sa.Column("subject", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category", sa.String(40), nullable=False, server_default="GENERAL"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(30), nullable=False, server_default="OPEN"),
        sa.Column("assigned_to", sa.Text),
        sa.Column("replies", JSONB),
        sa.Column("attachments", JSONB),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_tickets_supplier_id", "supplier_support_tickets", ["supplier_id"])
    op.create_index("idx_tickets_status", "supplier_support_tickets", ["status"])
    op.create_index("idx_tickets_ticket_number", "supplier_support_tickets", ["ticket_number"])

    # ── supplier_audit_logs ───────────────────────────────────────────────────
    op.create_table(
        "supplier_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("user_id", sa.Text),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("entity", sa.Text, nullable=False),
        sa.Column("entity_id", sa.Text),
        sa.Column("old_value", JSONB),
        sa.Column("new_value", JSONB),
        sa.Column("ip_address", sa.Text),
        sa.Column("user_agent", sa.Text),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_audit_logs_supplier_id", "supplier_audit_logs", ["supplier_id"])
    op.create_index("idx_audit_logs_entity", "supplier_audit_logs", ["entity", "action"])
    op.create_index("idx_audit_logs_created_at", "supplier_audit_logs", ["created_at"],
                    postgresql_ops={"created_at": "DESC"})


def downgrade() -> None:
    for tbl in PORTAL_TABLES:
        op.drop_table(tbl)
