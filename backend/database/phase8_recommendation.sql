-- ═══════════════════════════════════════════════════════════════════════════
-- SupplyShield AI — Phase 8 Migration: Recommendation Agent
-- Run in Supabase SQL Editor after phase7_inventory.sql
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- TABLE: public.recommendations
-- One row per at-risk supplier per workflow run.
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.recommendations (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),

    -- At-risk supplier
    at_risk_supplier_id     TEXT        NOT NULL,
    at_risk_supplier_name   TEXT,
    execution_id            TEXT        NOT NULL,
    stockout_risk           TEXT,                -- CRITICAL/HIGH/MEDIUM/LOW
    revenue_at_risk_usd     FLOAT,
    delay_days              FLOAT,

    -- Top recommendation result
    top_supplier_id         TEXT,
    top_supplier_name       TEXT,
    top_recommendation_score FLOAT,
    top_topsis_score        FLOAT,
    top_cosine_sim          FLOAT,
    top_country_code        VARCHAR(10),
    top_tier                TEXT,

    -- Procurement action
    procurement_action      TEXT,       -- IMMEDIATE_SWITCH/DUAL_SOURCE/QUALIFY/MONITOR
    procurement_priority    TEXT,       -- CRITICAL/HIGH/MEDIUM/LOW

    -- Full algorithm outputs
    explanation             TEXT,
    mcdm_ranking            JSONB,
    topsis_ranking          JSONB,

    -- Timestamp
    evaluated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.recommendations IS
    'Phase 8: MCDM-based supplier recommendations. One row per at-risk '
    'supplier per workflow run. Stores TOPSIS, cosine similarity, '
    'and composite recommendation scores.';

-- ── Indexes ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_recs_at_risk_supplier
    ON public.recommendations (at_risk_supplier_id);

CREATE INDEX IF NOT EXISTS idx_recs_execution_id
    ON public.recommendations (execution_id);

CREATE INDEX IF NOT EXISTS idx_recs_evaluated_at
    ON public.recommendations (evaluated_at DESC);

CREATE INDEX IF NOT EXISTS idx_recs_stockout_risk
    ON public.recommendations (stockout_risk);

CREATE INDEX IF NOT EXISTS idx_recs_procurement_action
    ON public.recommendations (procurement_action);

CREATE INDEX IF NOT EXISTS idx_recs_top_score
    ON public.recommendations (top_recommendation_score DESC);

CREATE INDEX IF NOT EXISTS idx_recs_revenue_at_risk
    ON public.recommendations (revenue_at_risk_usd DESC);

-- GIN for MCDM ranking search
CREATE INDEX IF NOT EXISTS idx_recs_mcdm_gin
    ON public.recommendations USING GIN (mcdm_ranking);

-- Compound: latest per at-risk supplier
CREATE INDEX IF NOT EXISTS idx_recs_supplier_eval
    ON public.recommendations (at_risk_supplier_id, evaluated_at DESC);

-- ── Row Level Security ────────────────────────────────────────────────────────
ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "recs_select_all"       ON public.recommendations;
DROP POLICY IF EXISTS "recs_service_role_all" ON public.recommendations;

CREATE POLICY "recs_select_all" ON public.recommendations
    FOR SELECT USING (true);

CREATE POLICY "recs_service_role_all" ON public.recommendations
    FOR ALL TO service_role USING (true);

-- ───────────────────────────────────────────────────────────────────────────
-- VIEW: v_latest_recommendations
-- Most recent recommendation per at-risk supplier
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW public.v_latest_recommendations AS
SELECT DISTINCT ON (at_risk_supplier_id)
    id,
    at_risk_supplier_id,
    at_risk_supplier_name,
    execution_id,
    stockout_risk,
    revenue_at_risk_usd,
    delay_days,
    top_supplier_id,
    top_supplier_name,
    top_recommendation_score,
    top_topsis_score,
    top_cosine_sim,
    top_country_code,
    top_tier,
    procurement_action,
    procurement_priority,
    evaluated_at
FROM public.recommendations
ORDER BY at_risk_supplier_id, evaluated_at DESC;

-- ───────────────────────────────────────────────────────────────────────────
-- VIEW: v_urgent_recommendations
-- IMMEDIATE_SWITCH and DUAL_SOURCE actions sorted by revenue at risk
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW public.v_urgent_recommendations AS
SELECT
    at_risk_supplier_id,
    at_risk_supplier_name,
    stockout_risk,
    revenue_at_risk_usd,
    delay_days,
    top_supplier_id,
    top_supplier_name,
    top_recommendation_score,
    top_country_code,
    procurement_action,
    procurement_priority,
    evaluated_at
FROM public.v_latest_recommendations
WHERE procurement_action IN ('IMMEDIATE_SWITCH', 'DUAL_SOURCE')
ORDER BY revenue_at_risk_usd DESC NULLS LAST;

-- ───────────────────────────────────────────────────────────────────────────
-- VIEW: v_recommendation_summary
-- One-row summary of fleet recommendation status
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW public.v_recommendation_summary AS
SELECT
    COUNT(*)                                    AS total_recommendations,
    COUNT(*) FILTER (WHERE procurement_action = 'IMMEDIATE_SWITCH') AS immediate_switches,
    COUNT(*) FILTER (WHERE procurement_action = 'DUAL_SOURCE')      AS dual_sources,
    COUNT(*) FILTER (WHERE procurement_action = 'QUALIFY')          AS qualifications,
    COUNT(*) FILTER (WHERE stockout_risk = 'CRITICAL')              AS critical_count,
    ROUND(SUM(revenue_at_risk_usd)::numeric, 2)                     AS total_revenue_at_risk,
    ROUND(AVG(top_recommendation_score)::numeric, 4)                AS avg_recommendation_score,
    MAX(evaluated_at)                                               AS last_evaluated_at
FROM public.v_latest_recommendations;
