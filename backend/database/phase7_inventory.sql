-- ═══════════════════════════════════════════════════════════════════════════
-- SupplyShield AI — Phase 7 Migration: Inventory Impact
-- Run in Supabase SQL Editor after phase6_supplier.sql
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- TABLE: public.inventory_projections
-- One row per component per workflow run.
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.inventory_projections (
    id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    component_id          TEXT        NOT NULL,
    component_name        TEXT,
    supplier_id           TEXT,
    execution_id          TEXT        NOT NULL,

    -- Stock levels
    current_stock         FLOAT,
    daily_consumption     FLOAT,
    safety_stock          FLOAT,
    reorder_point         FLOAT,
    lead_time_days        INTEGER,

    -- Stockout Prediction (Algorithms 1–5)
    days_remaining        FLOAT,
    safety_stock_days     FLOAT,
    stockout_risk         TEXT,                -- CRITICAL/HIGH/MEDIUM/LOW/SAFE
    stockout_probability  FLOAT,
    stockout_date         TEXT,

    -- Inventory Health (Algorithm 6)
    inventory_health_score FLOAT,
    inventory_health_label TEXT,
    coverage_ratio         FLOAT,

    -- Revenue Impact (Algorithm 7)
    days_short            FLOAT,
    units_short           FLOAT,
    revenue_lost_usd      FLOAT,
    cogs_at_risk_usd      FLOAT,

    -- Manufacturing Delay (Algorithm 8)
    delay_days            FLOAT,
    recovery_days         FLOAT,
    delay_severity        TEXT,
    affected_products     JSONB,

    -- Algorithm audit trail
    formula_breakdown     JSONB,

    -- Timestamp
    evaluated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.inventory_projections IS
    'Phase 7: Inventory stockout predictions, revenue impact, and '
    'manufacturing delay analysis. One row per component per workflow run.';

-- ── Indexes ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_inventory_component_id
    ON public.inventory_projections (component_id);

CREATE INDEX IF NOT EXISTS idx_inventory_supplier_id
    ON public.inventory_projections (supplier_id);

CREATE INDEX IF NOT EXISTS idx_inventory_execution_id
    ON public.inventory_projections (execution_id);

CREATE INDEX IF NOT EXISTS idx_inventory_evaluated_at
    ON public.inventory_projections (evaluated_at DESC);

CREATE INDEX IF NOT EXISTS idx_inventory_days_remaining
    ON public.inventory_projections (days_remaining ASC);

CREATE INDEX IF NOT EXISTS idx_inventory_stockout_risk
    ON public.inventory_projections (stockout_risk);

CREATE INDEX IF NOT EXISTS idx_inventory_health_score
    ON public.inventory_projections (inventory_health_score DESC);

CREATE INDEX IF NOT EXISTS idx_inventory_revenue_lost
    ON public.inventory_projections (revenue_lost_usd DESC);

-- Compound: latest per component
CREATE INDEX IF NOT EXISTS idx_inventory_cid_eval
    ON public.inventory_projections (component_id, evaluated_at DESC);

-- GIN for product lookups
CREATE INDEX IF NOT EXISTS idx_inventory_products_gin
    ON public.inventory_projections USING GIN (affected_products);

-- ── Row Level Security ────────────────────────────────────────────────────────
ALTER TABLE public.inventory_projections ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "inventory_select_all"       ON public.inventory_projections;
DROP POLICY IF EXISTS "inventory_service_role_all" ON public.inventory_projections;

CREATE POLICY "inventory_select_all" ON public.inventory_projections
    FOR SELECT USING (true);

CREATE POLICY "inventory_service_role_all" ON public.inventory_projections
    FOR ALL TO service_role USING (true);

-- ───────────────────────────────────────────────────────────────────────────
-- VIEW: v_latest_inventory
-- Most recent projection per component (DISTINCT ON)
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW public.v_latest_inventory AS
SELECT DISTINCT ON (component_id)
    id,
    component_id,
    component_name,
    supplier_id,
    execution_id,
    current_stock,
    daily_consumption,
    safety_stock,
    lead_time_days,
    days_remaining,
    stockout_risk,
    stockout_probability,
    stockout_date,
    inventory_health_score,
    inventory_health_label,
    coverage_ratio,
    days_short,
    units_short,
    revenue_lost_usd,
    delay_days,
    delay_severity,
    affected_products,
    evaluated_at
FROM public.inventory_projections
ORDER BY component_id, evaluated_at DESC;

-- ───────────────────────────────────────────────────────────────────────────
-- VIEW: v_critical_inventory
-- Components with CRITICAL or HIGH stockout risk
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW public.v_critical_inventory AS
SELECT
    component_id,
    component_name,
    supplier_id,
    days_remaining,
    lead_time_days,
    stockout_risk,
    stockout_probability,
    stockout_date,
    revenue_lost_usd,
    delay_days,
    affected_products,
    evaluated_at
FROM public.v_latest_inventory
WHERE stockout_risk IN ('CRITICAL', 'HIGH')
ORDER BY days_remaining ASC;

-- ───────────────────────────────────────────────────────────────────────────
-- VIEW: v_inventory_revenue_impact
-- Revenue impact summary sorted by highest impact
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW public.v_inventory_revenue_impact AS
SELECT
    component_id,
    component_name,
    supplier_id,
    stockout_risk,
    days_remaining,
    units_short,
    revenue_lost_usd,
    cogs_at_risk_usd,
    ROUND((revenue_lost_usd + cogs_at_risk_usd)::numeric, 2) AS total_impact_usd,
    delay_days,
    affected_products,
    evaluated_at
FROM public.v_latest_inventory
WHERE revenue_lost_usd > 0
ORDER BY total_impact_usd DESC;
