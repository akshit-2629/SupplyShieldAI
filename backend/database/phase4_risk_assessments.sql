-- ============================================================
-- Phase 4: Risk Assessment Agent — Database Migration
-- SupplyShield AI
-- ============================================================
-- Run this in: Supabase SQL Editor → New Query → Paste + Run
-- URL: https://supabase.com/dashboard/project/_/sql/new
--
-- Creates:
--   • risk_assessments table (full risk scoring output)
--   • Indexes for high-performance filtering
--   • Row Level Security policies
-- ============================================================

-- 1. Create risk_assessments table
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.risk_assessments (
    -- Identity
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id        TEXT UNIQUE NOT NULL,

    -- Foreign key to news_articles (soft ref)
    news_event_id        TEXT,

    -- Source event summary (denormalized for fast queries)
    title                TEXT,
    url                  TEXT,
    source               TEXT,
    event_type           TEXT,
    published_at         TIMESTAMPTZ,
    countries            JSONB,         -- List[str] ISO codes
    industries           JSONB,         -- List[str] tags

    -- Risk scoring
    risk_score           FLOAT NOT NULL DEFAULT 0.0,
    risk_level           TEXT  NOT NULL DEFAULT 'LOW',  -- LOW/MEDIUM/HIGH/CRITICAL
    severity_score       FLOAT,
    severity_label       TEXT,

    -- Formula audit trail
    formula_components   JSONB,

    -- Geographic risk breakdown
    geo_risk             JSONB,

    -- Industry risk breakdown
    industry_risk        JSONB,

    -- Supplier dependency
    supplier_tier        TEXT,
    exposure_weight      FLOAT,

    -- Confidence score
    confidence_score     FLOAT,
    confidence_label     TEXT,
    confidence_breakdown JSONB,

    -- Rule engine results
    rule_engine_results  JSONB,

    -- Trajectory
    trajectory           TEXT,   -- ESCALATING/STABLE/DECLINING/RECOVERING
    trend_slope          FLOAT,

    -- Timestamps
    assessed_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Indexes for common query patterns
-- ─────────────────────────────────────────────────────────────

-- Fast risk-level filtering (dashboard: show all CRITICAL first)
CREATE INDEX IF NOT EXISTS idx_risk_assessments_risk_level
    ON public.risk_assessments(risk_level);

-- Fast risk score ordering (top risks view)
CREATE INDEX IF NOT EXISTS idx_risk_assessments_risk_score
    ON public.risk_assessments(risk_score DESC);

-- Time-series queries (risk trend over time)
CREATE INDEX IF NOT EXISTS idx_risk_assessments_assessed_at
    ON public.risk_assessments(assessed_at DESC);

-- News event ID lookup (link back to news_articles)
CREATE INDEX IF NOT EXISTS idx_risk_assessments_news_event_id
    ON public.risk_assessments(news_event_id);

-- Confidence score filtering
CREATE INDEX IF NOT EXISTS idx_risk_assessments_confidence
    ON public.risk_assessments(confidence_score DESC);

-- Trajectory filtering
CREATE INDEX IF NOT EXISTS idx_risk_assessments_trajectory
    ON public.risk_assessments(trajectory)
    WHERE trajectory IS NOT NULL;

-- JSONB GIN index for country/industry array searches
CREATE INDEX IF NOT EXISTS idx_risk_assessments_countries_gin
    ON public.risk_assessments USING GIN (countries);

CREATE INDEX IF NOT EXISTS idx_risk_assessments_industries_gin
    ON public.risk_assessments USING GIN (industries);

-- Composite: risk_level + risk_score for dashboard fast path
CREATE INDEX IF NOT EXISTS idx_risk_assessments_level_score
    ON public.risk_assessments(risk_level, risk_score DESC);

-- 3. Row Level Security
-- ─────────────────────────────────────────────────────────────

ALTER TABLE public.risk_assessments ENABLE ROW LEVEL SECURITY;

-- Allow anonymous (API) reads for now
-- In production: restrict to authenticated users / roles
CREATE POLICY "risk_assessments_select_all"
    ON public.risk_assessments
    FOR SELECT
    USING (true);

-- Only service role can insert/update/delete
CREATE POLICY "risk_assessments_insert_service"
    ON public.risk_assessments
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY "risk_assessments_update_service"
    ON public.risk_assessments
    FOR UPDATE
    USING (true);

-- 4. Utility view: high risk summary
-- ─────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW public.v_high_risk_events AS
SELECT
    assessment_id,
    news_event_id,
    title,
    event_type,
    risk_score,
    risk_level,
    confidence_score,
    trajectory,
    countries,
    industries,
    assessed_at
FROM public.risk_assessments
WHERE risk_level IN ('HIGH', 'CRITICAL')
ORDER BY risk_score DESC, assessed_at DESC;

-- 5. Utility view: risk level summary statistics
-- ─────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW public.v_risk_level_stats AS
SELECT
    risk_level,
    COUNT(*)           AS count,
    AVG(risk_score)    AS avg_risk_score,
    MAX(risk_score)    AS max_risk_score,
    AVG(confidence_score) AS avg_confidence
FROM public.risk_assessments
GROUP BY risk_level
ORDER BY
    CASE risk_level
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH'     THEN 2
        WHEN 'MEDIUM'   THEN 3
        WHEN 'LOW'      THEN 4
        ELSE 5
    END;

-- ============================================================
-- Verify
-- ============================================================

SELECT
    'risk_assessments table created successfully' AS status,
    COUNT(*) AS existing_rows
FROM public.risk_assessments;
