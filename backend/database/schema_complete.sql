-- ═══════════════════════════════════════════════════════════════════════════
-- SupplyShield AI — Unified Database Schema (Phases 1 - 4)
-- ═══════════════════════════════════════════════════════════════════════════
-- Run this entire script in the Supabase SQL Editor:
--   Supabase Dashboard → SQL Editor → New Query → Paste → Run
--
-- This script safely drops existing policies first to prevent 
-- "Policy already exists" errors when rerun on an active database.
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- 0. SHARED HELPER FUNCTIONS
-- ───────────────────────────────────────────────────────────────────────────

-- Automatically refreshes updated_at timestamp on UPDATE
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


-- ───────────────────────────────────────────────────────────────────────────
-- 1. TABLE: public.profiles
-- Extends auth.users with application-specific user data.
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT        UNIQUE,
    full_name   TEXT,
    avatar_url  TEXT,
    role        TEXT        NOT NULL DEFAULT 'user'
                            CHECK (role IN ('user', 'admin', 'analyst', 'viewer')),
    provider    TEXT        NOT NULL DEFAULT 'email'
                            CHECK (provider IN ('email', 'google', 'github')),
    is_active   BOOLEAN     NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  public.profiles           IS 'Extended user profiles with app-specific fields, linked 1-to-1 with auth.users.';
COMMENT ON COLUMN public.profiles.id        IS 'References auth.users.id — same UUID as the Supabase auth user.';
COMMENT ON COLUMN public.profiles.role      IS 'App-level role: user | admin | analyst | viewer.';
COMMENT ON COLUMN public.profiles.provider  IS 'Auth provider used at sign-up: email | google | github.';

-- Indexes for profiles
CREATE INDEX IF NOT EXISTS idx_profiles_email      ON public.profiles (email);
CREATE INDEX IF NOT EXISTS idx_profiles_role       ON public.profiles (role);
CREATE INDEX IF NOT EXISTS idx_profiles_provider   ON public.profiles (provider);
CREATE INDEX IF NOT EXISTS idx_profiles_is_active  ON public.profiles (is_active);

-- Enable RLS for profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any to prevent "Policy already exists" errors
DROP POLICY IF EXISTS "profiles_select_own" ON public.profiles;
DROP POLICY IF EXISTS "profiles_update_own" ON public.profiles;
DROP POLICY IF EXISTS "profiles_service_role_all" ON public.profiles;

CREATE POLICY "profiles_select_own" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "profiles_update_own" ON public.profiles
    FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

CREATE POLICY "profiles_service_role_all" ON public.profiles
    USING (auth.jwt() ->> 'role' = 'service_role')
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

-- Trigger to automatically map new signup to public.profiles
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_provider  TEXT;
    v_full_name TEXT;
BEGIN
    v_provider  := COALESCE(
        NEW.raw_app_meta_data  ->> 'provider',
        NEW.raw_user_meta_data ->> 'provider',
        'email'
    );

    v_full_name := COALESCE(
        NEW.raw_user_meta_data ->> 'full_name',
        NEW.raw_user_meta_data ->> 'name',
        split_part(NEW.email, '@', 1)
    );

    INSERT INTO public.profiles (id, email, full_name, avatar_url, provider)
    VALUES (
        NEW.id,
        NEW.email,
        v_full_name,
        NEW.raw_user_meta_data ->> 'avatar_url',
        v_provider
    )
    ON CONFLICT (id) DO NOTHING;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

DROP TRIGGER IF EXISTS profiles_set_updated_at ON public.profiles;
CREATE TRIGGER profiles_set_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();


-- ───────────────────────────────────────────────────────────────────────────
-- 2. TABLE: public.disruption_event
-- Represents active supply chain disruptions.
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.disruption_event (
    id           SERIAL      PRIMARY KEY,
    title        VARCHAR(255) NOT NULL,
    description  TEXT,
    severity     VARCHAR(50)  DEFAULT 'MEDIUM',
    location     VARCHAR(255),
    impact_score FLOAT        DEFAULT 0.0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.disruption_event IS 'Database model representing active supply chain disruptions.';

-- Indexes for disruption_event
CREATE INDEX IF NOT EXISTS idx_disruption_event_severity ON public.disruption_event (severity);

DROP TRIGGER IF EXISTS disruption_event_set_updated_at ON public.disruption_event;
CREATE TRIGGER disruption_event_set_updated_at
    BEFORE UPDATE ON public.disruption_event
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- Enable RLS for disruption_event
ALTER TABLE public.disruption_event ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "disruption_event_select_all" ON public.disruption_event;
DROP POLICY IF EXISTS "disruption_event_service_role_all" ON public.disruption_event;

CREATE POLICY "disruption_event_select_all" ON public.disruption_event
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "disruption_event_service_role_all" ON public.disruption_event
    FOR ALL TO service_role USING (true);


-- ───────────────────────────────────────────────────────────────────────────
-- 3. TABLE: public.workflow_runs
-- Persists each full orchestrator workflow execution run.
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.workflow_runs (
    id                     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id           VARCHAR(36) UNIQUE NOT NULL,
    trigger_type           VARCHAR(50) NOT NULL DEFAULT 'manual',
    status                 VARCHAR(50) NOT NULL DEFAULT 'running',
    started_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at           TIMESTAMPTZ,
    agent_results          JSONB,
    error_summary          TEXT,
    trigger_payload        JSONB,
    news_event_count       VARCHAR(10),
    risk_assessment_count  VARCHAR(10),
    recommendation_count   VARCHAR(10)
);

COMMENT ON TABLE public.workflow_runs IS 'Tracks each master orchestrator workflow run lifecycle and summaries.';

-- Indexes for workflow_runs
CREATE INDEX IF NOT EXISTS idx_workflow_runs_execution_id ON public.workflow_runs (execution_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON public.workflow_runs (status);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_started_at ON public.workflow_runs (started_at DESC);

-- Enable RLS for workflow_runs
ALTER TABLE public.workflow_runs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "workflow_runs_select_all" ON public.workflow_runs;
DROP POLICY IF EXISTS "workflow_runs_service_role_all" ON public.workflow_runs;

CREATE POLICY "workflow_runs_select_all" ON public.workflow_runs
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "workflow_runs_service_role_all" ON public.workflow_runs
    FOR ALL TO service_role USING (true);


-- ───────────────────────────────────────────────────────────────────────────
-- 4. TABLE: public.agent_executions
-- Audit trail logging each individual agent node execution step inside a run.
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.agent_executions (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id  VARCHAR(36) NOT NULL REFERENCES public.workflow_runs(execution_id) ON DELETE CASCADE,
    agent_id      VARCHAR(100) NOT NULL,
    status        VARCHAR(50) NOT NULL,
    retry_count   INTEGER     DEFAULT 0,
    duration_ms   INTEGER,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at  TIMESTAMPTZ,
    output_data   JSONB,
    error_message TEXT
);

COMMENT ON TABLE public.agent_executions IS 'Audit trail of every agent run inside any workflow execution.';

-- Indexes for agent_executions
CREATE INDEX IF NOT EXISTS idx_agent_executions_execution_id ON public.agent_executions (execution_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_id ON public.agent_executions (agent_id);

-- Enable RLS for agent_executions
ALTER TABLE public.agent_executions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "agent_executions_select_all" ON public.agent_executions;
DROP POLICY IF EXISTS "agent_executions_service_role_all" ON public.agent_executions;

CREATE POLICY "agent_executions_select_all" ON public.agent_executions
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "agent_executions_service_role_all" ON public.agent_executions
    FOR ALL TO service_role USING (true);


-- ───────────────────────────────────────────────────────────────────────────
-- 5. TABLE: public.agent_health
-- Live operational status metrics & health snapshot for each registered agent.
-- ───────────────────────────────────────────────────────────────────────────
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

COMMENT ON TABLE public.agent_health IS 'Real-time heartbeat, performance metrics, and settings for each agent.';

-- Enable RLS for agent_health
ALTER TABLE public.agent_health ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "agent_health_select_all" ON public.agent_health;
DROP POLICY IF EXISTS "agent_health_service_role_all" ON public.agent_health;

CREATE POLICY "agent_health_select_all" ON public.agent_health
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "agent_health_service_role_all" ON public.agent_health
    FOR ALL TO service_role USING (true);


-- ───────────────────────────────────────────────────────────────────────────
-- 6. TABLE: public.news_articles
-- Phase 3: Raw articles enriched with extracted entities, countries, and NLP.
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.news_articles (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    title             TEXT        NOT NULL,
    content           TEXT,
    url               VARCHAR(2048) UNIQUE NOT NULL,
    source_name       VARCHAR(200),
    source_url        VARCHAR(2048),
    credibility_score FLOAT       DEFAULT 5.0,
    published_at      TIMESTAMPTZ,
    collected_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    entities          JSONB,       -- {"organizations": [...], "people": [...], "locations": [...]}
    country_codes     JSONB,       -- ["CN", "US", "TW"]
    industry_tags     JSONB,       -- ["semiconductor", "logistics"]
    severity          VARCHAR(20) DEFAULT 'NONE', -- CRITICAL/HIGH/MEDIUM/LOW/NONE
    severity_score    FLOAT       DEFAULT 0.0,
    event_type        VARCHAR(50), -- GEOPOLITICAL/NATURAL_DISASTER/LABOR/etc.
    embedding         JSONB,       -- all-MiniLM-L6-v2 vector array
    is_duplicate      BOOLEAN     DEFAULT false,
    duplicate_of      UUID        REFERENCES public.news_articles(id) ON DELETE SET NULL,
    is_disruption     BOOLEAN     DEFAULT false,
    is_processed      BOOLEAN     DEFAULT false
);

COMMENT ON TABLE public.news_articles IS 'Raw collected news articles enriched with NLP metadata and classification.';

-- Indexes for news_articles
CREATE INDEX IF NOT EXISTS idx_news_articles_url ON public.news_articles (url);
CREATE INDEX IF NOT EXISTS idx_news_articles_collected_at ON public.news_articles (collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_articles_is_disruption ON public.news_articles (is_disruption) WHERE is_processed = false;
CREATE INDEX IF NOT EXISTS idx_news_articles_severity ON public.news_articles (severity, collected_at DESC);

-- Enable RLS for news_articles
ALTER TABLE public.news_articles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "news_articles_select_all" ON public.news_articles;
DROP POLICY IF EXISTS "news_articles_service_role_all" ON public.news_articles;

CREATE POLICY "news_articles_select_all" ON public.news_articles
    FOR SELECT USING (true);

CREATE POLICY "news_articles_service_role_all" ON public.news_articles
    FOR ALL TO service_role USING (true);


-- ───────────────────────────────────────────────────────────────────────────
-- 7. TABLE: public.risk_assessments
-- Phase 4: Risk scores, formulas, rules engine results, and trends.
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.risk_assessments (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id        TEXT        UNIQUE NOT NULL,
    news_event_id        TEXT,       -- Linked soft ref to news_articles.id
    title                TEXT,
    url                  TEXT,
    source               TEXT,
    event_type           TEXT,
    published_at         TIMESTAMPTZ,
    countries            JSONB,      -- List[str] ISO codes
    industries           JSONB,      -- List[str] tags
    risk_score           FLOAT       NOT NULL DEFAULT 0.0,
    risk_level           TEXT        NOT NULL DEFAULT 'LOW',
    severity_score       FLOAT,
    severity_label       TEXT,
    formula_components   JSONB,      -- scoring audit trail
    geo_risk             JSONB,      -- geo-risk breakdown
    industry_risk        JSONB,      -- industry-risk breakdown
    supplier_tier        TEXT,
    exposure_weight      FLOAT,
    confidence_score     FLOAT,
    confidence_label     TEXT,
    confidence_breakdown JSONB,
    rule_engine_results  JSONB,      -- matched rules log
    trajectory           TEXT,       -- ESCALATING/STABLE/DECLINING/RECOVERING
    trend_slope          FLOAT,
    assessed_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.risk_assessments IS 'Persists quantified business risk scores, rules applied, and trajectory trends.';

-- Indexes for risk_assessments
CREATE INDEX IF NOT EXISTS idx_risk_assessments_risk_level ON public.risk_assessments (risk_level);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_risk_score ON public.risk_assessments (risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_assessed_at ON public.risk_assessments (assessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_news_event_id ON public.risk_assessments (news_event_id);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_confidence ON public.risk_assessments (confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_trajectory ON public.risk_assessments (trajectory) WHERE trajectory IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_risk_assessments_countries_gin ON public.risk_assessments USING GIN (countries);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_industries_gin ON public.risk_assessments USING GIN (industries);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_level_score ON public.risk_assessments (risk_level, risk_score DESC);

-- Enable RLS for risk_assessments
ALTER TABLE public.risk_assessments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "risk_assessments_select_all" ON public.risk_assessments;
DROP POLICY IF EXISTS "risk_assessments_service_role_all" ON public.risk_assessments;

CREATE POLICY "risk_assessments_select_all" ON public.risk_assessments
    FOR SELECT USING (true);

CREATE POLICY "risk_assessments_service_role_all" ON public.risk_assessments
    FOR ALL TO service_role USING (true);


-- ───────────────────────────────────────────────────────────────────────────
-- 8. UTILITY VIEWS FOR REPORTING & DASHBOARDS
-- ───────────────────────────────────────────────────────────────────────────

-- Summarizes all active High & Critical risk incidents
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

-- Summarizes metrics grouped by risk levels
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


-- ───────────────────────────────────────────────────────────────────────────
-- VERIFY: Quick sanity check — should return 'Schema applied successfully'
-- ───────────────────────────────────────────────────────────────────────────
SELECT 'Unified database schema applied successfully' AS status;
