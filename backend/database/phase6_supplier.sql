-- ═══════════════════════════════════════════════════════════════════════════
-- SupplyShield AI — Phase 6 Migration: Supplier Intelligence
-- Run in Supabase SQL Editor after phase5_graph.sql
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- TABLE: public.supplier_scores
-- One row per supplier per workflow run.
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.supplier_scores (
    id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id           TEXT        NOT NULL,
    execution_id          TEXT        NOT NULL,

    -- Identity
    name                  TEXT,
    country_code          VARCHAR(10),
    tier                  TEXT,                -- TIER_1 / TIER_2 / TIER_3
    revenue_exposure_pct  FLOAT,

    -- Health composite
    health_score          FLOAT       NOT NULL DEFAULT 0.0,
    health_label          TEXT,                -- EXCELLENT / GOOD / FAIR / POOR / CRITICAL

    -- KPI dimensions (all 0–100)
    reliability_score     FLOAT,
    quality_score         FLOAT,
    lead_time_score       FLOAT,
    cost_efficiency       FLOAT,
    compliance_score      FLOAT,
    responsiveness        FLOAT,
    flexibility           FLOAT,

    -- Phase 4 risk overlay
    risk_score            FLOAT,
    risk_level            TEXT,
    geo_risk              FLOAT,
    industry_risk         FLOAT,

    -- Phase 5 graph overlay
    dependency_score      FLOAT,
    centrality            FLOAT,
    blast_radius_size     INTEGER,
    products_supplied     INTEGER,

    -- Ranking & trend
    rank                  INTEGER,
    rank_change           INTEGER,
    trend                 TEXT,               -- IMPROVING / STABLE / DECLINING / NEW_ENTRY
    mom_change            FLOAT,

    -- Algorithm audit
    formula_breakdown     JSONB,

    -- Timestamp
    evaluated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.supplier_scores IS
    'Phase 6: Supplier health scores, KPI dimensions, tier classifications, '
    'and MoM trends. One row per supplier per workflow run.';

-- ── Indexes ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_supplier_scores_supplier_id
    ON public.supplier_scores (supplier_id);

CREATE INDEX IF NOT EXISTS idx_supplier_scores_execution_id
    ON public.supplier_scores (execution_id);

CREATE INDEX IF NOT EXISTS idx_supplier_scores_evaluated_at
    ON public.supplier_scores (evaluated_at DESC);

CREATE INDEX IF NOT EXISTS idx_supplier_scores_tier
    ON public.supplier_scores (tier);

CREATE INDEX IF NOT EXISTS idx_supplier_scores_health
    ON public.supplier_scores (health_score DESC);

CREATE INDEX IF NOT EXISTS idx_supplier_scores_rank
    ON public.supplier_scores (rank);

CREATE INDEX IF NOT EXISTS idx_supplier_scores_risk
    ON public.supplier_scores (risk_score DESC);

CREATE INDEX IF NOT EXISTS idx_supplier_scores_country
    ON public.supplier_scores (country_code);

CREATE INDEX IF NOT EXISTS idx_supplier_scores_trend
    ON public.supplier_scores (trend);

-- Compound: latest health per supplier
CREATE INDEX IF NOT EXISTS idx_supplier_scores_sid_eval
    ON public.supplier_scores (supplier_id, evaluated_at DESC);

-- ── Row Level Security ────────────────────────────────────────────────────────
ALTER TABLE public.supplier_scores ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "supplier_scores_select_all"         ON public.supplier_scores;
DROP POLICY IF EXISTS "supplier_scores_service_role_all"   ON public.supplier_scores;

CREATE POLICY "supplier_scores_select_all" ON public.supplier_scores
    FOR SELECT USING (true);

CREATE POLICY "supplier_scores_service_role_all" ON public.supplier_scores
    FOR ALL TO service_role USING (true);

-- ───────────────────────────────────────────────────────────────────────────
-- VIEW: v_latest_supplier_scores
-- Most recent score row per supplier (DISTINCT ON pattern)
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW public.v_latest_supplier_scores AS
SELECT DISTINCT ON (supplier_id)
    id,
    supplier_id,
    execution_id,
    name,
    country_code,
    tier,
    revenue_exposure_pct,
    health_score,
    health_label,
    reliability_score,
    quality_score,
    lead_time_score,
    cost_efficiency,
    compliance_score,
    risk_score,
    risk_level,
    dependency_score,
    centrality,
    rank,
    rank_change,
    trend,
    mom_change,
    evaluated_at
FROM public.supplier_scores
ORDER BY supplier_id, evaluated_at DESC;

-- ───────────────────────────────────────────────────────────────────────────
-- VIEW: v_supplier_tier_summary
-- Tier-level aggregation: count, avg health, total exposure
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW public.v_supplier_tier_summary AS
SELECT
    tier,
    COUNT(*)                      AS supplier_count,
    ROUND(AVG(health_score)::numeric, 2)  AS avg_health_score,
    ROUND(SUM(revenue_exposure_pct)::numeric, 2) AS total_exposure_pct,
    ROUND(AVG(risk_score)::numeric, 2)   AS avg_risk_score
FROM public.v_latest_supplier_scores
GROUP BY tier
ORDER BY tier;

-- ───────────────────────────────────────────────────────────────────────────
-- VIEW: v_critical_suppliers
-- Suppliers in CRITICAL or POOR health + Tier 1
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW public.v_critical_suppliers AS
SELECT
    supplier_id,
    name,
    tier,
    country_code,
    health_score,
    health_label,
    risk_score,
    risk_level,
    trend,
    mom_change,
    evaluated_at
FROM public.v_latest_supplier_scores
WHERE health_label IN ('CRITICAL', 'POOR')
   OR (tier = 'TIER_1' AND health_score < 50)
ORDER BY health_score ASC;
