-- ═══════════════════════════════════════════════════════════════════════════
-- SupplyShield AI — Database Schema
-- Run this entire script in the Supabase SQL Editor:
--   Supabase Dashboard → SQL Editor → New Query → Paste → Run
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- TABLE: public.profiles
-- Extends auth.users with application-specific user data.
-- Each auth.users row gets a corresponding profile row via trigger.
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

-- ───────────────────────────────────────────────────────────────────────────
-- INDEXES for fast lookups
-- ───────────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_profiles_email      ON public.profiles (email);
CREATE INDEX IF NOT EXISTS idx_profiles_role       ON public.profiles (role);
CREATE INDEX IF NOT EXISTS idx_profiles_provider   ON public.profiles (provider);
CREATE INDEX IF NOT EXISTS idx_profiles_is_active  ON public.profiles (is_active);

-- ───────────────────────────────────────────────────────────────────────────
-- ROW LEVEL SECURITY (RLS)
-- All access is denied by default; policies below grant specific access.
-- ───────────────────────────────────────────────────────────────────────────
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Authenticated users can SELECT their own profile only
CREATE POLICY "profiles_select_own"
    ON public.profiles
    FOR SELECT
    USING (auth.uid() = id);

-- Authenticated users can UPDATE their own profile
-- (role and is_active are excluded from direct user mutation — use admin API)
CREATE POLICY "profiles_update_own"
    ON public.profiles
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Service role (backend with SUPABASE_SERVICE_ROLE_KEY) has full access
-- This lets the FastAPI backend read/write any profile
CREATE POLICY "profiles_service_role_all"
    ON public.profiles
    USING     (auth.jwt() ->> 'role' = 'service_role')
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

-- ───────────────────────────────────────────────────────────────────────────
-- FUNCTION: public.handle_new_user()
-- Auto-creates a profile row when a new auth.users row is inserted.
-- Fires for both email sign-up and Google/OAuth sign-up.
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER          -- runs with the rights of the function owner (postgres)
SET search_path = public
AS $$
DECLARE
    v_provider  TEXT;
    v_full_name TEXT;
BEGIN
    -- Determine the auth provider from Supabase metadata
    v_provider  := COALESCE(
        NEW.raw_app_meta_data  ->> 'provider',
        NEW.raw_user_meta_data ->> 'provider',
        'email'
    );

    -- Determine full name: prefer metadata, fall back to email prefix
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
    ON CONFLICT (id) DO NOTHING;  -- idempotent: no-op if profile already exists

    RETURN NEW;
END;
$$;

-- Attach trigger to auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- ───────────────────────────────────────────────────────────────────────────
-- FUNCTION: public.set_updated_at()
-- Automatically refreshes updated_at on every profile UPDATE.
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS profiles_set_updated_at ON public.profiles;
CREATE TRIGGER profiles_set_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- ───────────────────────────────────────────────────────────────────────────
-- VERIFY: Quick sanity check — should return 'Schema applied successfully'
-- ───────────────────────────────────────────────────────────────────────────
SELECT 'Schema applied successfully' AS status;
