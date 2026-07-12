-- ═══════════════════════════════════════════════════════════════════════════
-- SupplyShield AI — Missing Tables Migration (Phases 6, 7, 8)
-- Run this in Supabase SQL Editor:
--   https://supabase.com/dashboard/project/qcmypkzxtbbkyyjbjisw/sql/new
-- ═══════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────────
-- Fix agent_health (id column is agent_id VARCHAR, not UUID)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.agent_health (
    agent_id        VARCHAR(100) PRIMARY KEY,
    status          VARCHAR(50)  NOT NULL DEFAULT 'idle',
    enabled         BOOLEAN      NOT NULL DEFAULT true,
    success_count   INTEGER      NOT NULL DEFAULT 0,
    failure_count   INTEGER      NOT NULL DEFAULT 0,
    avg_duration_ms FLOAT        NOT NULL DEFAULT 0.0,
    last_error      TEXT,
    last_heartbeat  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    description     VARCHAR(500),
    version         VARCHAR(50)
);

ALTER TABLE public.agent_health ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "agent_health_select_all" ON public.agent_health;
DROP POLICY IF EXISTS "agent_health_service_role_all" ON public.agent_health;
CREATE POLICY "agent_health_select_all" ON public.agent_health FOR SELECT USING (true);
CREATE POLICY "agent_health_service_role_all" ON public.agent_health FOR ALL TO service_role USING (true);


-- ─────────────────────────────────────────────────────────────────────────────
-- Phase 6: supplier_scores
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.supplier_scores (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    supplier_id          TEXT        NOT NULL,
    execution_id         TEXT        NOT NULL,
    name                 TEXT,
    country_code         VARCHAR(10),
    tier                 TEXT,
    revenue_exposure_pct FLOAT,

    -- Health
    health_score         FLOAT       NOT NULL DEFAULT 0.0,
    health_label         TEXT,

    -- KPI dimensions
    reliability_score    FLOAT,
    quality_score        FLOAT,
    lead_time_score      FLOAT,
    cost_efficiency      FLOAT,
    compliance_score     FLOAT,
    responsiveness       FLOAT,
    flexibility          FLOAT,

    -- Risk (from Phase 4)
    risk_score           FLOAT,
    risk_level           TEXT,
    geo_risk             FLOAT,
    industry_risk        FLOAT,

    -- Graph (from Phase 5)
    dependency_score     FLOAT,
    centrality           FLOAT,
    blast_radius_size    INTEGER,
    products_supplied    INTEGER,

    -- Ranking & trend
    rank                 INTEGER,
    rank_change          INTEGER,
    trend                TEXT,
    mom_change           FLOAT,

    -- Algorithm audit
    formula_breakdown    JSONB,

    -- Timestamp
    evaluated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_supplier_scores_supplier_id   ON public.supplier_scores (supplier_id);
CREATE INDEX IF NOT EXISTS idx_supplier_scores_execution_id  ON public.supplier_scores (execution_id);
CREATE INDEX IF NOT EXISTS idx_supplier_scores_health_score  ON public.supplier_scores (health_score);
CREATE INDEX IF NOT EXISTS idx_supplier_scores_country_code  ON public.supplier_scores (country_code);
CREATE INDEX IF NOT EXISTS idx_supplier_scores_tier          ON public.supplier_scores (tier);
CREATE INDEX IF NOT EXISTS idx_supplier_scores_evaluated_at  ON public.supplier_scores (evaluated_at DESC);

ALTER TABLE public.supplier_scores ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "supplier_scores_select_all" ON public.supplier_scores;
DROP POLICY IF EXISTS "supplier_scores_service_role_all" ON public.supplier_scores;
CREATE POLICY "supplier_scores_select_all" ON public.supplier_scores FOR SELECT USING (true);
CREATE POLICY "supplier_scores_service_role_all" ON public.supplier_scores FOR ALL TO service_role USING (true);


-- ─────────────────────────────────────────────────────────────────────────────
-- Phase 7: inventory_projections
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.inventory_projections (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    component_id           TEXT        NOT NULL,
    component_name         TEXT,
    supplier_id            TEXT,
    execution_id           TEXT        NOT NULL,

    -- Stock levels
    current_stock          FLOAT,
    daily_consumption      FLOAT,
    safety_stock           FLOAT,
    reorder_point          FLOAT,
    lead_time_days         INTEGER,

    -- Stockout prediction
    days_remaining         FLOAT,
    safety_stock_days      FLOAT,
    stockout_risk          TEXT,          -- CRITICAL/HIGH/MEDIUM/LOW/SAFE
    stockout_probability   FLOAT,
    stockout_date          TEXT,

    -- Inventory health
    inventory_health_score FLOAT,
    inventory_health_label TEXT,
    coverage_ratio         FLOAT,

    -- Revenue impact
    days_short             FLOAT,
    units_short            FLOAT,
    revenue_lost_usd       FLOAT,
    cogs_at_risk_usd       FLOAT,

    -- Manufacturing delay
    delay_days             FLOAT,
    recovery_days          FLOAT,
    delay_severity         TEXT,
    affected_products      JSONB,

    -- Algorithm audit trail
    formula_breakdown      JSONB,

    -- Timestamp
    evaluated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inventory_component_id    ON public.inventory_projections (component_id);
CREATE INDEX IF NOT EXISTS idx_inventory_supplier_id     ON public.inventory_projections (supplier_id);
CREATE INDEX IF NOT EXISTS idx_inventory_execution_id    ON public.inventory_projections (execution_id);
CREATE INDEX IF NOT EXISTS idx_inventory_stockout_risk   ON public.inventory_projections (stockout_risk);
CREATE INDEX IF NOT EXISTS idx_inventory_health_score    ON public.inventory_projections (inventory_health_score);
CREATE INDEX IF NOT EXISTS idx_inventory_evaluated_at    ON public.inventory_projections (evaluated_at DESC);

ALTER TABLE public.inventory_projections ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "inventory_projections_select_all" ON public.inventory_projections;
DROP POLICY IF EXISTS "inventory_projections_service_role_all" ON public.inventory_projections;
CREATE POLICY "inventory_projections_select_all" ON public.inventory_projections FOR SELECT USING (true);
CREATE POLICY "inventory_projections_service_role_all" ON public.inventory_projections FOR ALL TO service_role USING (true);


-- ─────────────────────────────────────────────────────────────────────────────
-- Phase 8: recommendations
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.recommendations (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- At-risk supplier
    at_risk_supplier_id      TEXT        NOT NULL,
    at_risk_supplier_name    TEXT,
    execution_id             TEXT        NOT NULL,
    stockout_risk            TEXT,
    revenue_at_risk_usd      FLOAT,
    delay_days               FLOAT,

    -- Top recommendation
    top_supplier_id          TEXT,
    top_supplier_name        TEXT,
    top_recommendation_score FLOAT,
    top_topsis_score         FLOAT,
    top_cosine_sim           FLOAT,
    top_country_code         TEXT,
    top_tier                 TEXT,

    -- Procurement action
    procurement_action       TEXT,
    procurement_priority     TEXT,

    -- Full algorithm outputs
    explanation              TEXT,
    mcdm_ranking             JSONB,
    topsis_ranking           JSONB,

    -- Timestamp
    evaluated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recommendations_at_risk_id   ON public.recommendations (at_risk_supplier_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_execution_id ON public.recommendations (execution_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_stockout     ON public.recommendations (stockout_risk);
CREATE INDEX IF NOT EXISTS idx_recommendations_action       ON public.recommendations (procurement_action);
CREATE INDEX IF NOT EXISTS idx_recommendations_evaluated_at ON public.recommendations (evaluated_at DESC);

ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "recommendations_select_all" ON public.recommendations;
DROP POLICY IF EXISTS "recommendations_service_role_all" ON public.recommendations;
CREATE POLICY "recommendations_select_all" ON public.recommendations FOR SELECT USING (true);
CREATE POLICY "recommendations_service_role_all" ON public.recommendations FOR ALL TO service_role USING (true);


-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ═══════════════════════════════════════════════════════════════════════════
SELECT 'supplier_scores' AS table_name, COUNT(*) AS rows FROM public.supplier_scores
UNION ALL
SELECT 'inventory_projections', COUNT(*) FROM public.inventory_projections
UNION ALL
SELECT 'recommendations', COUNT(*) FROM public.recommendations;
