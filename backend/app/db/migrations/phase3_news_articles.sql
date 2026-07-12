-- Phase 3: News Intelligence Agent — Database Schema
-- Run this SQL in your Supabase SQL Editor to create the news_articles table
-- (or apply via Alembic migration if connected to local PostgreSQL)

-- ─────────────────────────────────────────────────────────────────────────────
-- news_articles table
-- Stores every collected article with full NLP metadata and embeddings
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS news_articles (
    -- Identity
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core article fields
    title             TEXT NOT NULL,
    content           TEXT,
    url               VARCHAR(2048) NOT NULL UNIQUE,

    -- Source
    source_name       VARCHAR(200),
    source_url        VARCHAR(2048),
    credibility_score FLOAT DEFAULT 5.0,

    -- Timestamps
    published_at      TIMESTAMPTZ,
    collected_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- NLP Metadata (stored as JSONB for flexibility)
    entities          JSONB,           -- {"organizations": [...], "people": [...], "locations": [...]}
    country_codes     JSONB,           -- ["CN", "US", "TW"]
    industry_tags     JSONB,           -- ["semiconductor", "logistics"]

    -- Severity Assessment
    severity          VARCHAR(20) DEFAULT 'NONE',    -- CRITICAL/HIGH/MEDIUM/LOW/NONE
    severity_score    FLOAT DEFAULT 0.0,              -- Continuous 0-10

    -- Event Classification
    event_type        VARCHAR(50),                    -- GEOPOLITICAL/NATURAL_DISASTER/LABOR/etc.

    -- Semantic Embedding (384-dim all-MiniLM-L6-v2, stored as JSONB float array)
    -- Phase 20: Migrate to pgvector extension for efficient similarity search
    embedding         JSONB,

    -- Deduplication
    is_duplicate      BOOLEAN DEFAULT FALSE,
    duplicate_of      UUID REFERENCES news_articles(id) ON DELETE SET NULL,

    -- Classification Flags
    is_disruption     BOOLEAN DEFAULT FALSE,
    is_processed      BOOLEAN DEFAULT FALSE
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Indexes for common query patterns
-- ─────────────────────────────────────────────────────────────────────────────

-- Primary lookup by URL (deduplication check)
CREATE INDEX IF NOT EXISTS idx_news_articles_url
    ON news_articles (url);

-- Disruption events feed (is_disruption=TRUE ordered by severity_score)
CREATE INDEX IF NOT EXISTS idx_news_articles_disruption
    ON news_articles (is_disruption, severity_score DESC, collected_at DESC)
    WHERE is_disruption = TRUE;

-- Time-based queries (most recent first)
CREATE INDEX IF NOT EXISTS idx_news_articles_collected_at
    ON news_articles (collected_at DESC);

-- Severity filter
CREATE INDEX IF NOT EXISTS idx_news_articles_severity
    ON news_articles (severity, collected_at DESC);

-- Source filter
CREATE INDEX IF NOT EXISTS idx_news_articles_source
    ON news_articles (source_name, collected_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- Row Level Security (RLS)
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE news_articles ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read news articles
CREATE POLICY "Authenticated users can read news_articles"
    ON news_articles
    FOR SELECT
    TO authenticated
    USING (true);

-- Only service_role can insert/update/delete (backend only)
CREATE POLICY "Service role manages news_articles"
    ON news_articles
    FOR ALL
    TO service_role
    USING (true);
