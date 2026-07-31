"""002 — Phase 5: Knowledge Graph snapshots.

Revision:    002_phase5_graph
Revises:     001_initial_core_schema
Create Date: 2026-07-20

Tables created:
  graph_snapshots
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "002_phase5_graph"
down_revision = "001_initial_core_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "graph_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("execution_id", sa.Text, nullable=False, index=True),
        sa.Column("supplier_count", sa.Integer, server_default="0"),
        sa.Column("component_count", sa.Integer, server_default="0"),
        sa.Column("edge_count", sa.Integer, server_default="0"),
        sa.Column("nodes", JSONB),
        sa.Column("edges", JSONB),
        sa.Column("risk_summary", JSONB),
        sa.Column("critical_paths", JSONB),
        sa.Column("algorithm_metadata", JSONB),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_graph_snapshots_execution_id", "graph_snapshots", ["execution_id"])
    op.create_index("idx_graph_snapshots_snapshot_at", "graph_snapshots", ["snapshot_at"],
                    postgresql_ops={"snapshot_at": "DESC"})


def downgrade() -> None:
    op.drop_table("graph_snapshots")
