"""001 — Baseline core schema (Phases 1–4).

Revision:    001_initial_core_schema
Revises:     (none — initial revision)
Create Date: 2026-07-20

Tables created:
  profiles, disruption_event, workflow_runs, agent_executions,
  agent_health, news_articles, risk_assessments
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# Alembic revision identifiers
revision = "001_initial_core_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── set_updated_at trigger function ──────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION public.set_updated_at()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;
    """)

    # ── profiles ─────────────────────────────────────────────────────────────
    op.create_table(
        "profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.Text, unique=True),
        sa.Column("full_name", sa.Text),
        sa.Column("avatar_url", sa.Text),
        sa.Column("role", sa.Text, nullable=False, server_default="user"),
        sa.Column("provider", sa.Text, nullable=False, server_default="email"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_profiles_email", "profiles", ["email"])
    op.create_index("idx_profiles_role", "profiles", ["role"])

    # ── disruption_event ─────────────────────────────────────────────────────
    op.create_table(
        "disruption_event",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("severity", sa.String(50), server_default="MEDIUM"),
        sa.Column("location", sa.String(255)),
        sa.Column("impact_score", sa.Float, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_disruption_event_severity", "disruption_event", ["severity"])

    # ── workflow_runs ─────────────────────────────────────────────────────────
    op.create_table(
        "workflow_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("execution_id", sa.String(36), unique=True, nullable=False),
        sa.Column("trigger_type", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("status", sa.String(50), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("agent_results", JSONB),
        sa.Column("error_summary", sa.Text),
        sa.Column("trigger_payload", JSONB),
        sa.Column("news_event_count", sa.String(10)),
        sa.Column("risk_assessment_count", sa.String(10)),
        sa.Column("recommendation_count", sa.String(10)),
    )
    op.create_index("idx_workflow_runs_execution_id", "workflow_runs", ["execution_id"])
    op.create_index("idx_workflow_runs_status", "workflow_runs", ["status"])
    op.create_index("idx_workflow_runs_started_at", "workflow_runs", ["started_at"],
                    postgresql_ops={"started_at": "DESC"})

    # ── agent_executions ──────────────────────────────────────────────────────
    op.create_table(
        "agent_executions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("execution_id", sa.String(36), sa.ForeignKey("workflow_runs.execution_id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("retry_count", sa.Integer, server_default="0"),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("output_data", JSONB),
        sa.Column("error_message", sa.Text),
    )
    op.create_index("idx_agent_executions_execution_id", "agent_executions", ["execution_id"])
    op.create_index("idx_agent_executions_agent_id", "agent_executions", ["agent_id"])

    # ── agent_health ──────────────────────────────────────────────────────────
    op.create_table(
        "agent_health",
        sa.Column("agent_id", sa.String(100), primary_key=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="idle"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("success_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("avg_duration_ms", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("last_error", sa.Text),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("description", sa.String(500)),
        sa.Column("version", sa.String(50)),
    )

    # ── news_articles ─────────────────────────────────────────────────────────
    op.create_table(
        "news_articles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("content", sa.Text),
        sa.Column("url", sa.String(2048), unique=True, nullable=False),
        sa.Column("source_name", sa.String(200)),
        sa.Column("source_url", sa.String(2048)),
        sa.Column("credibility_score", sa.Float, server_default="5.0"),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("entities", JSONB),
        sa.Column("country_codes", JSONB),
        sa.Column("industry_tags", JSONB),
        sa.Column("severity", sa.String(20), server_default="NONE"),
        sa.Column("severity_score", sa.Float, server_default="0.0"),
        sa.Column("event_type", sa.String(50)),
        sa.Column("embedding", JSONB),
        sa.Column("is_duplicate", sa.Boolean, server_default="false"),
        sa.Column("duplicate_of", UUID(as_uuid=True), sa.ForeignKey("news_articles.id", ondelete="SET NULL")),
        sa.Column("is_disruption", sa.Boolean, server_default="false"),
        sa.Column("is_processed", sa.Boolean, server_default="false"),
    )
    op.create_index("idx_news_articles_url", "news_articles", ["url"])
    op.create_index("idx_news_articles_collected_at", "news_articles", ["collected_at"],
                    postgresql_ops={"collected_at": "DESC"})
    op.create_index("idx_news_articles_severity", "news_articles", ["severity", "collected_at"],
                    postgresql_ops={"collected_at": "DESC"})

    # ── risk_assessments ──────────────────────────────────────────────────────
    op.create_table(
        "risk_assessments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("assessment_id", sa.Text, unique=True, nullable=False),
        sa.Column("news_event_id", sa.Text),
        sa.Column("title", sa.Text),
        sa.Column("url", sa.Text),
        sa.Column("source", sa.Text),
        sa.Column("event_type", sa.Text),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("countries", JSONB),
        sa.Column("industries", JSONB),
        sa.Column("risk_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("risk_level", sa.Text, nullable=False, server_default="LOW"),
        sa.Column("severity_score", sa.Float),
        sa.Column("severity_label", sa.Text),
        sa.Column("formula_components", JSONB),
        sa.Column("geo_risk", JSONB),
        sa.Column("industry_risk", JSONB),
        sa.Column("supplier_tier", sa.Text),
        sa.Column("exposure_weight", sa.Float),
        sa.Column("confidence_score", sa.Float),
        sa.Column("confidence_label", sa.Text),
        sa.Column("confidence_breakdown", JSONB),
        sa.Column("rule_engine_results", JSONB),
        sa.Column("trajectory", sa.Text),
        sa.Column("trend_slope", sa.Float),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_risk_assessments_risk_level", "risk_assessments", ["risk_level"])
    op.create_index("idx_risk_assessments_risk_score", "risk_assessments", ["risk_score"],
                    postgresql_ops={"risk_score": "DESC"})
    op.create_index("idx_risk_assessments_assessed_at", "risk_assessments", ["assessed_at"],
                    postgresql_ops={"assessed_at": "DESC"})
    op.create_index("idx_risk_assessments_countries_gin", "risk_assessments", ["countries"],
                    postgresql_using="gin")
    op.create_index("idx_risk_assessments_industries_gin", "risk_assessments", ["industries"],
                    postgresql_using="gin")


def downgrade() -> None:
    op.drop_table("risk_assessments")
    op.drop_table("news_articles")
    op.drop_table("agent_health")
    op.drop_table("agent_executions")
    op.drop_table("workflow_runs")
    op.drop_table("disruption_event")
    op.drop_table("profiles")
    op.execute("DROP FUNCTION IF EXISTS public.set_updated_at() CASCADE;")
