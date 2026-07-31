"""005 — Phase 10: Normalized extension tables (15 new tables).

Revision:    005_phase10_normalized
Revises:     004_phase9_supplier_portal
Create Date: 2026-07-20

Tables created (15):
  supplier_categories, supplier_factory_locations, supplier_warehouse_locations,
  supplier_contacts, supplier_certifications, supplier_documents, supplier_products,
  supplier_inventory_transactions, supplier_shipment_events,
  supplier_incident_attachments, supplier_forecast_accuracy,
  supplier_score_explanations, api_logs, orchestrator_events, dashboard_kpi_cache
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "005_phase10_normalized"
down_revision = "004_phase9_supplier_portal"
branch_labels = None
depends_on = None

NEW_TABLES = [
    "dashboard_kpi_cache",
    "orchestrator_events",
    "api_logs",
    "supplier_score_explanations",
    "supplier_forecast_accuracy",
    "supplier_incident_attachments",
    "supplier_shipment_events",
    "supplier_inventory_transactions",
    "supplier_products",
    "supplier_documents",
    "supplier_certifications",
    "supplier_contacts",
    "supplier_warehouse_locations",
    "supplier_factory_locations",
    "supplier_categories",
]


def upgrade() -> None:
    # Enable trigram extension for LIKE/ILIKE search indexes
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("CREATE EXTENSION IF NOT EXISTS uuid-ossp;")

    # ── supplier_categories ───────────────────────────────────────────────────
    op.create_table(
        "supplier_categories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("parent_id", UUID(as_uuid=True),
                  sa.ForeignKey("supplier_categories.id", ondelete="SET NULL")),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_supplier_categories_parent_id", "supplier_categories", ["parent_id"])
    op.create_index("idx_supplier_categories_is_active", "supplier_categories", ["is_active"])

    # ── supplier_factory_locations ────────────────────────────────────────────
    op.create_table(
        "supplier_factory_locations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("location_name", sa.Text, nullable=False),
        sa.Column("address", sa.Text),
        sa.Column("city", sa.Text),
        sa.Column("state_province", sa.Text),
        sa.Column("country", sa.Text, nullable=False),
        sa.Column("postal_code", sa.Text),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("latitude", sa.Numeric(10, 7)),
        sa.Column("longitude", sa.Numeric(10, 7)),
        sa.Column("capacity_sqft", sa.Integer),
        sa.Column("employee_count", sa.Integer),
        sa.Column("phone", sa.Text),
        sa.Column("email", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_factory_locations_supplier_id", "supplier_factory_locations", ["supplier_id"])
    op.create_index("idx_factory_locations_country", "supplier_factory_locations", ["country"])

    # ── supplier_warehouse_locations ──────────────────────────────────────────
    op.create_table(
        "supplier_warehouse_locations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("address", sa.Text),
        sa.Column("city", sa.Text),
        sa.Column("state_province", sa.Text),
        sa.Column("country", sa.Text, nullable=False),
        sa.Column("postal_code", sa.Text),
        sa.Column("storage_type", sa.String(30)),
        sa.Column("capacity_units", sa.Integer),
        sa.Column("capacity_sqft", sa.Integer),
        sa.Column("phone", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_warehouse_locations_supplier_id", "supplier_warehouse_locations", ["supplier_id"])
    op.create_index("idx_warehouse_locations_country", "supplier_warehouse_locations", ["country"])

    # ── supplier_contacts ─────────────────────────────────────────────────────
    op.create_table(
        "supplier_contacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("contact_type", sa.String(30), nullable=False, server_default="GENERAL"),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("email", sa.Text),
        sa.Column("phone", sa.Text),
        sa.Column("title", sa.Text),
        sa.Column("department", sa.Text),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_supplier_contacts_supplier_id", "supplier_contacts", ["supplier_id"])
    op.create_index("idx_supplier_contacts_email", "supplier_contacts", ["email"])

    # ── supplier_certifications ───────────────────────────────────────────────
    op.create_table(
        "supplier_certifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("cert_type", sa.String(50), nullable=False),
        sa.Column("cert_name", sa.Text),
        sa.Column("cert_number", sa.Text),
        sa.Column("issuing_body", sa.Text),
        sa.Column("issued_date", sa.Date),
        sa.Column("expiry_date", sa.Date),
        sa.Column("document_url", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_supplier_certifications_supplier_id", "supplier_certifications", ["supplier_id"])
    op.create_index("idx_supplier_certifications_expiry_date", "supplier_certifications", ["expiry_date"])

    # ── supplier_documents ────────────────────────────────────────────────────
    op.create_table(
        "supplier_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("doc_type", sa.String(30), nullable=False, server_default="OTHER"),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("size_bytes", sa.BigInteger),
        sa.Column("mime_type", sa.Text),
        sa.Column("version", sa.Text),
        sa.Column("uploaded_by", sa.Text),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
    )
    op.create_index("idx_supplier_documents_supplier_id", "supplier_documents", ["supplier_id"])
    op.create_index("idx_supplier_documents_doc_type", "supplier_documents", ["doc_type"])

    # ── supplier_products ─────────────────────────────────────────────────────
    op.create_table(
        "supplier_products",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("category_id", UUID(as_uuid=True),
                  sa.ForeignKey("supplier_categories.id", ondelete="SET NULL")),
        sa.Column("sku", sa.Text, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("unit", sa.Text, nullable=False, server_default="units"),
        sa.Column("lead_time_days", sa.Integer),
        sa.Column("moq", sa.Integer),
        sa.Column("unit_price_usd", sa.Numeric(14, 4)),
        sa.Column("weight_kg", sa.Numeric(10, 4)),
        sa.Column("dimensions_cm", sa.Text),
        sa.Column("hs_code", sa.Text),
        sa.Column("country_of_origin", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("supplier_id", "sku", name="uq_supplier_products_supplier_sku"),
    )
    op.create_index("idx_supplier_products_supplier_id", "supplier_products", ["supplier_id"])
    op.create_index("idx_supplier_products_category_id", "supplier_products", ["category_id"])

    # ── supplier_inventory_transactions ───────────────────────────────────────
    op.create_table(
        "supplier_inventory_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("item_id", UUID(as_uuid=True),
                  sa.ForeignKey("supplier_inventory_items.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("transaction_type", sa.String(30), nullable=False),
        sa.Column("quantity_delta", sa.Integer, nullable=False),
        sa.Column("quantity_after", sa.Integer, nullable=False),
        sa.Column("reference_id", sa.Text),
        sa.Column("reference_type", sa.Text),
        sa.Column("unit_cost_usd", sa.Numeric(14, 4)),
        sa.Column("notes", sa.Text),
        sa.Column("created_by", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_inv_txn_item_id", "supplier_inventory_transactions", ["item_id"])
    op.create_index("idx_inv_txn_supplier_id", "supplier_inventory_transactions", ["supplier_id"])
    op.create_index("idx_inv_txn_created_at", "supplier_inventory_transactions", ["created_at"],
                    postgresql_ops={"created_at": "DESC"})
    op.create_index("idx_inv_txn_item_created", "supplier_inventory_transactions",
                    ["item_id", "created_at"], postgresql_ops={"created_at": "DESC"})

    # ── supplier_shipment_events ──────────────────────────────────────────────
    op.create_table(
        "supplier_shipment_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("shipment_id", UUID(as_uuid=True),
                  sa.ForeignKey("supplier_shipments.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False, server_default="UPDATE"),
        sa.Column("location", sa.Text),
        sa.Column("city", sa.Text),
        sa.Column("country", sa.Text),
        sa.Column("latitude", sa.Numeric(10, 7)),
        sa.Column("longitude", sa.Numeric(10, 7)),
        sa.Column("notes", sa.Text),
        sa.Column("carrier_message", sa.Text),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_shipment_events_shipment_id", "supplier_shipment_events", ["shipment_id"])
    op.create_index("idx_shipment_events_supplier_id", "supplier_shipment_events", ["supplier_id"])
    op.create_index("idx_shipment_events_recorded_at", "supplier_shipment_events", ["recorded_at"],
                    postgresql_ops={"recorded_at": "DESC"})

    # ── supplier_incident_attachments ─────────────────────────────────────────
    op.create_table(
        "supplier_incident_attachments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("incident_id", UUID(as_uuid=True),
                  sa.ForeignKey("supplier_incidents.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("file_name", sa.Text, nullable=False),
        sa.Column("file_url", sa.Text, nullable=False),
        sa.Column("mime_type", sa.Text),
        sa.Column("size_bytes", sa.BigInteger),
        sa.Column("description", sa.Text),
        sa.Column("uploaded_by", sa.Text),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_incident_attachments_incident_id", "supplier_incident_attachments", ["incident_id"])
    op.create_index("idx_incident_attachments_supplier_id", "supplier_incident_attachments", ["supplier_id"])

    # ── supplier_forecast_accuracy ────────────────────────────────────────────
    op.create_table(
        "supplier_forecast_accuracy",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("forecast_id", UUID(as_uuid=True),
                  sa.ForeignKey("supplier_capacity_forecasts.id", ondelete="SET NULL")),
        sa.Column("forecast_year", sa.Integer, nullable=False),
        sa.Column("forecast_month", sa.SmallInteger),
        sa.Column("period_type", sa.String(20), server_default="monthly"),
        sa.Column("forecasted_output", sa.Integer),
        sa.Column("actual_output", sa.Integer),
        sa.Column("mape_pct", sa.Numeric(8, 4)),
        sa.Column("accuracy_pct", sa.Numeric(8, 4)),
        sa.Column("computed_by", sa.Text),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_forecast_accuracy_supplier_id", "supplier_forecast_accuracy", ["supplier_id"])
    op.create_index("idx_forecast_accuracy_year", "supplier_forecast_accuracy", ["forecast_year"])

    # ── supplier_score_explanations ───────────────────────────────────────────
    op.create_table(
        "supplier_score_explanations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("execution_id", sa.Text, nullable=False),
        sa.Column("score_id", UUID(as_uuid=True),
                  sa.ForeignKey("supplier_scores.id", ondelete="CASCADE")),
        sa.Column("dimension", sa.String(50), nullable=False),
        sa.Column("explanation_text", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float),
        sa.Column("generated_by", sa.Text, nullable=False, server_default="gemini-1.5-pro"),
        sa.Column("model_version", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_score_explanations_supplier_id", "supplier_score_explanations", ["supplier_id"])
    op.create_index("idx_score_explanations_score_id", "supplier_score_explanations", ["score_id"])

    # ── api_logs ──────────────────────────────────────────────────────────────
    op.create_table(
        "api_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Text),
        sa.Column("supplier_id", sa.Text),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column("query_params", sa.Text),
        sa.Column("status_code", sa.Integer, nullable=False),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("ip_address", sa.Text),
        sa.Column("user_agent", sa.Text),
        sa.Column("request_body_hash", sa.Text),
        sa.Column("response_size_bytes", sa.Integer),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_api_logs_user_id", "api_logs", ["user_id"])
    op.create_index("idx_api_logs_supplier_id", "api_logs", ["supplier_id"])
    op.create_index("idx_api_logs_status_code", "api_logs", ["status_code"])
    op.create_index("idx_api_logs_created_at", "api_logs", ["created_at"],
                    postgresql_ops={"created_at": "DESC"})

    # ── orchestrator_events ───────────────────────────────────────────────────
    op.create_table(
        "orchestrator_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("source", sa.Text, nullable=False, server_default="supplier_portal"),
        sa.Column("entity_type", sa.Text),
        sa.Column("entity_id", sa.Text),
        sa.Column("supplier_id", sa.Text),
        sa.Column("execution_id", sa.Text),
        sa.Column("payload", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="3"),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Integer),
    )
    op.create_index("idx_orch_events_event_type", "orchestrator_events", ["event_type"])
    op.create_index("idx_orch_events_status", "orchestrator_events", ["status"])
    op.create_index("idx_orch_events_supplier_id", "orchestrator_events", ["supplier_id"])
    op.create_index("idx_orch_events_created_at", "orchestrator_events", ["created_at"],
                    postgresql_ops={"created_at": "DESC"})
    op.create_index("idx_orch_events_payload_gin", "orchestrator_events", ["payload"],
                    postgresql_using="gin")

    # ── dashboard_kpi_cache ───────────────────────────────────────────────────
    op.create_table(
        "dashboard_kpi_cache",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("cache_key", sa.Text, nullable=False, unique=True),
        sa.Column("scope", sa.Text, nullable=False, server_default="global"),
        sa.Column("execution_id", sa.Text),
        sa.Column("data", JSONB, nullable=False),
        sa.Column("ttl_seconds", sa.Integer, nullable=False, server_default="300"),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_kpi_cache_cache_key", "dashboard_kpi_cache", ["cache_key"])
    op.create_index("idx_kpi_cache_scope", "dashboard_kpi_cache", ["scope"])
    op.create_index("idx_kpi_cache_refreshed_at", "dashboard_kpi_cache", ["refreshed_at"],
                    postgresql_ops={"refreshed_at": "DESC"})


def downgrade() -> None:
    for tbl in NEW_TABLES:
        op.drop_table(tbl)
