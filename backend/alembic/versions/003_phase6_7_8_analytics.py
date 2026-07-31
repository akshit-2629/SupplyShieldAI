"""003 — Phases 6, 7, 8: Supplier scores, inventory projections, recommendations.

Revision:    003_phase6_7_8_analytics
Revises:     002_phase5_graph
Create Date: 2026-07-20

Tables created:
  supplier_scores, inventory_projections, recommendations
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "003_phase6_7_8_analytics"
down_revision = "002_phase5_graph"
branch_labels = None
depends_on = None


def upgrade() -> None:

    # ── supplier_scores ───────────────────────────────────────────────────────
    op.create_table(
        "supplier_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("execution_id", sa.Text, nullable=False),
        sa.Column("name", sa.Text),
        sa.Column("country_code", sa.String(10)),
        sa.Column("tier", sa.Text),
        sa.Column("revenue_exposure_pct", sa.Float),
        sa.Column("health_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("health_label", sa.Text),
        sa.Column("reliability_score", sa.Float),
        sa.Column("quality_score", sa.Float),
        sa.Column("lead_time_score", sa.Float),
        sa.Column("cost_efficiency", sa.Float),
        sa.Column("compliance_score", sa.Float),
        sa.Column("responsiveness", sa.Float),
        sa.Column("flexibility", sa.Float),
        sa.Column("risk_score", sa.Float),
        sa.Column("risk_level", sa.Text),
        sa.Column("geo_risk", sa.Float),
        sa.Column("industry_risk", sa.Float),
        sa.Column("dependency_score", sa.Float),
        sa.Column("centrality", sa.Float),
        sa.Column("blast_radius_size", sa.Integer),
        sa.Column("products_supplied", sa.Integer),
        sa.Column("rank", sa.Integer),
        sa.Column("rank_change", sa.Integer),
        sa.Column("trend", sa.Text),
        sa.Column("mom_change", sa.Float),
        sa.Column("formula_breakdown", JSONB),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_supplier_scores_supplier_id", "supplier_scores", ["supplier_id"])
    op.create_index("idx_supplier_scores_execution_id", "supplier_scores", ["execution_id"])
    op.create_index("idx_supplier_scores_evaluated_at", "supplier_scores", ["evaluated_at"],
                    postgresql_ops={"evaluated_at": "DESC"})
    op.create_index("idx_supplier_scores_health", "supplier_scores", ["health_score"],
                    postgresql_ops={"health_score": "DESC"})
    op.create_index("idx_supplier_scores_sid_eval", "supplier_scores",
                    ["supplier_id", "evaluated_at"], postgresql_ops={"evaluated_at": "DESC"})

    # ── inventory_projections ─────────────────────────────────────────────────
    op.create_table(
        "inventory_projections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("component_id", sa.Text, nullable=False),
        sa.Column("component_name", sa.Text),
        sa.Column("supplier_id", sa.Text),
        sa.Column("execution_id", sa.Text, nullable=False),
        sa.Column("current_stock", sa.Float),
        sa.Column("daily_consumption", sa.Float),
        sa.Column("safety_stock", sa.Float),
        sa.Column("reorder_point", sa.Float),
        sa.Column("lead_time_days", sa.Integer),
        sa.Column("days_remaining", sa.Float),
        sa.Column("safety_stock_days", sa.Float),
        sa.Column("stockout_risk", sa.Text),
        sa.Column("stockout_probability", sa.Float),
        sa.Column("stockout_date", sa.Text),
        sa.Column("inventory_health_score", sa.Float),
        sa.Column("inventory_health_label", sa.Text),
        sa.Column("coverage_ratio", sa.Float),
        sa.Column("days_short", sa.Float),
        sa.Column("units_short", sa.Float),
        sa.Column("revenue_lost_usd", sa.Float),
        sa.Column("cogs_at_risk_usd", sa.Float),
        sa.Column("delay_days", sa.Float),
        sa.Column("recovery_days", sa.Float),
        sa.Column("delay_severity", sa.Text),
        sa.Column("affected_products", JSONB),
        sa.Column("formula_breakdown", JSONB),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_inventory_component_id", "inventory_projections", ["component_id"])
    op.create_index("idx_inventory_supplier_id", "inventory_projections", ["supplier_id"])
    op.create_index("idx_inventory_evaluated_at", "inventory_projections", ["evaluated_at"],
                    postgresql_ops={"evaluated_at": "DESC"})
    op.create_index("idx_inventory_stockout_risk", "inventory_projections", ["stockout_risk"])
    op.create_index("idx_inventory_cid_eval", "inventory_projections",
                    ["component_id", "evaluated_at"], postgresql_ops={"evaluated_at": "DESC"})

    # ── recommendations ───────────────────────────────────────────────────────
    op.create_table(
        "recommendations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("at_risk_supplier_id", sa.Text, nullable=False),
        sa.Column("at_risk_supplier_name", sa.Text),
        sa.Column("execution_id", sa.Text, nullable=False),
        sa.Column("stockout_risk", sa.Text),
        sa.Column("revenue_at_risk_usd", sa.Float),
        sa.Column("delay_days", sa.Float),
        sa.Column("top_supplier_id", sa.Text),
        sa.Column("top_supplier_name", sa.Text),
        sa.Column("top_recommendation_score", sa.Float),
        sa.Column("top_topsis_score", sa.Float),
        sa.Column("top_cosine_sim", sa.Float),
        sa.Column("top_country_code", sa.String(10)),
        sa.Column("top_tier", sa.Text),
        sa.Column("procurement_action", sa.Text),
        sa.Column("procurement_priority", sa.Text),
        sa.Column("explanation", sa.Text),
        sa.Column("mcdm_ranking", JSONB),
        sa.Column("topsis_ranking", JSONB),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_recs_at_risk_supplier", "recommendations", ["at_risk_supplier_id"])
    op.create_index("idx_recs_execution_id", "recommendations", ["execution_id"])
    op.create_index("idx_recs_evaluated_at", "recommendations", ["evaluated_at"],
                    postgresql_ops={"evaluated_at": "DESC"})
    op.create_index("idx_recs_mcdm_gin", "recommendations", ["mcdm_ranking"],
                    postgresql_using="gin")


def downgrade() -> None:
    op.drop_table("recommendations")
    op.drop_table("inventory_projections")
    op.drop_table("supplier_scores")
