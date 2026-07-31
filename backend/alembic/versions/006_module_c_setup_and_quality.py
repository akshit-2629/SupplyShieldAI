"""006 — Phase 11: Module C Setup Status & Quality Management.

Revision:    006_module_c_setup_and_quality
Revises:     005_phase10_normalized
Create Date: 2026-07-27

Tables created (3):
  supplier_setup_status, supplier_quality_records, supplier_quality_history
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "006_module_c_setup_and_quality"
down_revision = "005_phase10_normalized"
branch_labels = None
depends_on = None

NEW_TABLES = [
    "supplier_quality_history",
    "supplier_quality_records",
    "supplier_setup_status",
]


def upgrade() -> None:
    # ── supplier_setup_status ──────────────────────────────────────────────────
    op.create_table(
        "supplier_setup_status",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, unique=True, nullable=False),
        sa.Column("step_company_profile", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("step_contacts", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("step_locations", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("step_products", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("step_production", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("step_lead_times", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("step_certifications", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("step_media", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_complete", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("completion_pct", sa.Integer, nullable=False, server_default="0"),
        sa.Column("wizard_started_at", sa.DateTime(timezone=True)),
        sa.Column("wizard_completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_setup_status_supplier_id", "supplier_setup_status", ["supplier_id"], unique=True)
    op.create_index("idx_setup_status_is_complete", "supplier_setup_status", ["is_complete"])

    # ── supplier_quality_records ──────────────────────────────────────────────
    op.create_table(
        "supplier_quality_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("record_number", sa.Text, nullable=False),
        sa.Column("record_type", sa.Text, nullable=False, server_default="INSPECTION_REPORT"),
        sa.Column("severity", sa.Text, nullable=False, server_default="MINOR"),
        sa.Column("status", sa.Text, nullable=False, server_default="OPEN"),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("inspection_date", sa.Date),
        sa.Column("product_sku", sa.Text),
        sa.Column("product_name", sa.Text),
        sa.Column("batch_number", sa.Text),
        sa.Column("quantity_inspected", sa.Integer),
        sa.Column("quantity_passed", sa.Integer),
        sa.Column("quantity_failed", sa.Integer),
        sa.Column("defect_rate_pct", sa.Numeric(6, 2)),
        sa.Column("root_cause", sa.Text),
        sa.Column("corrective_action", sa.Text),
        sa.Column("corrective_action_date", sa.Date),
        sa.Column("responsible_person", sa.Text),
        sa.Column("standard_reference", sa.Text),
        sa.Column("customer_notified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("regulatory_reportable", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("attachments", JSONB, nullable=False, server_default="[]"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("closed_by", sa.Text),
        sa.Column("created_by", sa.Text),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_quality_records_supplier_id", "supplier_quality_records", ["supplier_id"])
    op.create_index("idx_quality_records_status", "supplier_quality_records", ["status"])

    # ── supplier_quality_history ──────────────────────────────────────────────
    op.create_table(
        "supplier_quality_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("quality_id", UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("changed_by", sa.Text),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("change_summary", sa.Text),
        sa.Column("snapshot", JSONB, nullable=False, server_default="{}"),
    )
    op.create_index("idx_quality_history_quality_id", "supplier_quality_history", ["quality_id"])


def downgrade() -> None:
    for tbl in NEW_TABLES:
        op.drop_table(tbl)
