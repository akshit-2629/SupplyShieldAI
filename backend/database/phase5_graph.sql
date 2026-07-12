-- ═══════════════════════════════════════════════════════════════════════════
-- SupplyShield AI — Phase 5 Migration: Knowledge Graph Snapshots
-- Run in Supabase SQL Editor after schema_complete.sql
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- TABLE: public.graph_snapshots
-- Stores one row per workflow run with the full graph analysis result.
-- Large JSON blobs (react_flow, centrality, blast_radius) are stored as JSONB
-- for fast querying and GIN indexing.
-- ───────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.graph_snapshots (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id        TEXT        NOT NULL,                  -- links to workflow_runs.id

    -- Summary counts (denormalized for fast dashboards)
    node_count          INTEGER     NOT NULL DEFAULT 0,
    edge_count          INTEGER     NOT NULL DEFAULT 0,
    spof_count          INTEGER     NOT NULL DEFAULT 0,        -- single points of failure
    blast_impacted      INTEGER     NOT NULL DEFAULT 0,        -- nodes in blast radius
    critical_paths      INTEGER     NOT NULL DEFAULT 0,        -- computed Dijkstra paths

    -- Full analysis blobs
    react_flow_json     JSONB,      -- { nodes: [...], edges: [...] } for React Flow UI
    centrality_json     JSONB,      -- degree centrality + SPOF list
    blast_radius_json   JSONB,      -- blast radius report for all disrupted nodes
    graph_stats_json    JSONB,      -- density, DAG check, risk distribution, etc.

    -- Timestamp
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.graph_snapshots IS
    'Phase 5: Stores one supply chain DiGraph snapshot per workflow run. '
    'Includes React Flow JSON for UI rendering and algorithm results.';

-- ── Indexes ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_graph_snapshots_execution_id
    ON public.graph_snapshots (execution_id);

CREATE INDEX IF NOT EXISTS idx_graph_snapshots_created_at
    ON public.graph_snapshots (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_graph_snapshots_spof_count
    ON public.graph_snapshots (spof_count DESC);

-- GIN indexes for JSON querying
CREATE INDEX IF NOT EXISTS idx_graph_snapshots_react_flow_gin
    ON public.graph_snapshots USING GIN (react_flow_json);

CREATE INDEX IF NOT EXISTS idx_graph_snapshots_centrality_gin
    ON public.graph_snapshots USING GIN (centrality_json);

-- ── Row Level Security ────────────────────────────────────────────────────────
ALTER TABLE public.graph_snapshots ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "graph_snapshots_select_all"         ON public.graph_snapshots;
DROP POLICY IF EXISTS "graph_snapshots_service_role_all"   ON public.graph_snapshots;

-- Anyone authenticated can read graph snapshots
CREATE POLICY "graph_snapshots_select_all" ON public.graph_snapshots
    FOR SELECT USING (true);

-- Only the service role (backend) can write
CREATE POLICY "graph_snapshots_service_role_all" ON public.graph_snapshots
    FOR ALL TO service_role USING (true);

-- ───────────────────────────────────────────────────────────────────────────
-- VIEW: v_latest_graph_snapshot
-- Always returns the most recent snapshot for the dashboard.
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW public.v_latest_graph_snapshot AS
SELECT
    id,
    execution_id,
    node_count,
    edge_count,
    spof_count,
    blast_impacted,
    critical_paths,
    created_at
FROM public.graph_snapshots
ORDER BY created_at DESC
LIMIT 1;

-- ───────────────────────────────────────────────────────────────────────────
-- VIEW: v_graph_history
-- Last 10 snapshots for trend display.
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW public.v_graph_history AS
SELECT
    id,
    execution_id,
    node_count,
    edge_count,
    spof_count,
    blast_impacted,
    critical_paths,
    created_at
FROM public.graph_snapshots
ORDER BY created_at DESC
LIMIT 10;
