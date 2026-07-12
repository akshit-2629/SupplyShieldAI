"""
Google OAuth 2.0 Authentication Endpoints
==========================================

Provides three ways for the backend to authenticate users via Google:

  GET  /auth/google/login     → Returns the Google OAuth authorization URL.
                                The frontend (or any client) should redirect
                                the user to this URL to start the OAuth flow.

  GET  /auth/google/callback  → Handles the redirect from Google after the
                                user grants consent. Exchanges the auth code
                                for tokens, fetches the Google profile, creates
                                or finds the Supabase user, mints a session
                                JWT, and redirects the browser to the frontend.

  POST /auth/google/verify    → Accepts a Google ID token directly
                                (e.g., from Google One Tap or a mobile app).
                                Verifies it with Google's public certs, then
                                returns a Supabase-compatible session.

Authentication Flow
-------------------
                   Browser
                     │
   GET /auth/google/login   → returns google_auth_url
                     │
   browser redirects to → accounts.google.com/o/oauth2/v2/auth
                     │
   user consents → Google redirects to → /auth/google/callback?code=...
                     │
   backend exchanges code → Google token endpoint
                     │
   backend fetches user info → Google userinfo endpoint
                     │
   backend upserts user → Supabase admin API
                     │
   backend mints Supabase-compatible JWT
                     │
   backend redirects browser → {FRONTEND_URL}/auth/callback#access_token=...
                     │
   frontend AuthCallback.jsx picks up token and stores session
"""

import logging
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from supabase import create_client

# Google library for verifying ID tokens (e.g., from Google One Tap)
try:
    from google.oauth2 import id_token as google_id_token
    from google.auth.transport import requests as google_requests
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger("app")

router = APIRouter(prefix="/auth/google", tags=["Google Authentication"])

# ── Google OAuth 2.0 endpoints ────────────────────────────────────────────────
GOOGLE_AUTH_BASE_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL      = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL   = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_OAUTH_SCOPES   = "openid email profile"


# ══════════════════════════════════════════════════════════════════════════════
#  Private Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _require_google_config() -> None:
    """Raise 503 if Google OAuth credentials are not configured."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Google OAuth is not configured on this server. "
                "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env"
            ),
        )


def _require_supabase_admin_config() -> None:
    """Raise 503 if Supabase service role key is not configured."""
    if not settings.SUPABASE_SERVICE_ROLE_KEY or not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Supabase admin credentials are not configured. "
                "Set SUPABASE_SERVICE_ROLE_KEY and SUPABASE_JWT_SECRET in backend/.env"
            ),
        )


def _get_admin_client():
    """
    Returns a Supabase client authenticated with the service_role key.
    This client bypasses Row Level Security and can perform admin operations
    (create users, read all profiles) on behalf of the backend.
    """
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
    )


def _mint_supabase_jwt(user_id: str, email: str) -> dict:
    """
    Creates a short-lived Supabase-compatible JWT for the given user.

    Supabase validates JWTs that are:
      - Signed with the project JWT secret (HS256)
      - Carrying aud='authenticated'
      - Not expired

    The frontend can store this token and use it as a Bearer token for
    both Supabase client calls and our FastAPI protected endpoints.
    """
    _require_supabase_admin_config()

    now = datetime.now(timezone.utc)
    expires_in_seconds = 3600  # 1 hour

    payload = {
        "sub": user_id,
        "email": email,
        "role": "authenticated",
        "aud": "authenticated",
        "iss": f"{settings.SUPABASE_URL}/auth/v1",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in_seconds)).timestamp()),
    }

    access_token = jwt.encode(
        payload,
        settings.SUPABASE_JWT_SECRET,
        algorithm="HS256",
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in_seconds,
        "user": {
            "id": user_id,
            "email": email,
        },
    }


async def _get_or_create_supabase_user(
    email: str,
    full_name: str,
    avatar_url: str,
) -> str:
    """
    Finds or creates a Supabase auth user for the given Google account.

    Strategy:
      1. Try to create the user via Supabase admin API.
      2. If creation fails (user already exists), look up the UUID from
         the public.profiles table using the email.
      3. Return the Supabase user UUID.
    """
    admin = _get_admin_client()

    try:
        response = admin.auth.admin.create_user({
            "email": email,
            "email_confirm": True,   # Google accounts are already verified
            "user_metadata": {
                "full_name": full_name,
                "avatar_url": avatar_url,
                "provider": "google",
            },
        })
        user_id = str(response.user.id)
        logger.info(f"Created new Supabase user for Google account: {email} ({user_id})")
        return user_id

    except Exception as create_error:
        # User already exists — look up by email from profiles table
        logger.info(f"User {email} already exists, looking up by email")
        try:
            result = admin.table("profiles").select("id").eq("email", email).execute()
            if result.data:
                return result.data[0]["id"]
        except Exception as lookup_error:
            logger.error(f"Profile lookup failed: {lookup_error}")

        logger.error(f"Could not resolve Supabase user for: {email}. Create error: {create_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not resolve a Supabase user for this Google account.",
        )


# ══════════════════════════════════════════════════════════════════════════════
#  Endpoint 1 — Initiate Google OAuth
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/login",
    summary="Initiate Google OAuth flow",
    description=(
        "Returns the Google OAuth authorization URL. "
        "The client should redirect the user's browser to this URL. "
        "After Google consent, the user is sent to /auth/google/callback."
    ),
)
def google_login():
    """
    Returns the Google OAuth 2.0 authorization URL.

    The client (frontend or mobile app) should open or redirect to this URL
    so the user can sign in with their Google account.
    """
    _require_google_config()

    params = {
        "client_id":     settings.GOOGLE_CLIENT_ID,
        "redirect_uri":  settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         GOOGLE_OAUTH_SCOPES,
        "access_type":   "offline",
        "prompt":        "select_account",
    }
    auth_url = f"{GOOGLE_AUTH_BASE_URL}?{urlencode(params)}"
    logger.info("Returning Google OAuth authorization URL")
    return {"auth_url": auth_url}


# ══════════════════════════════════════════════════════════════════════════════
#  Endpoint 2 — Handle Google OAuth Callback
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/callback",
    summary="Handle Google OAuth callback",
    description=(
        "Google redirects the user here after they grant consent. "
        "The backend exchanges the authorization code for tokens, "
        "fetches the user's Google profile, creates or finds the Supabase user, "
        "mints a session JWT, and redirects the browser to the frontend."
    ),
)
async def google_callback(
    code:  str = Query(..., description="Authorization code from Google"),
    state: str = Query("", description="Optional state parameter"),
    error: str = Query("", description="Error from Google (if consent denied)"),
):
    """
    Full Google OAuth 2.0 Authorization Code Flow.

    Steps:
    1. Check for errors (user denied access, etc.)
    2. Exchange the authorization code for an access token
    3. Fetch the Google user profile (email, name, picture)
    4. Get or create the Supabase auth user
    5. Mint a Supabase-compatible JWT
    6. Redirect to the frontend with the token in the URL fragment
    """
    _require_google_config()

    # Step 0: Handle errors from Google (e.g., user denied access)
    if error:
        logger.warning(f"Google OAuth error: {error}")
        frontend_error_url = f"{settings.FRONTEND_URL}/login?error={error}"
        return RedirectResponse(url=frontend_error_url)

    # Step 1: Exchange authorization code for Google access token
    logger.info("Exchanging Google authorization code for tokens")
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id":     settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code":          code,
                "grant_type":    "authorization_code",
                "redirect_uri":  settings.GOOGLE_REDIRECT_URI,
            },
        )

    if token_resp.status_code != 200:
        logger.error(f"Google token exchange failed ({token_resp.status_code}): {token_resp.text}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange Google authorization code: {token_resp.text}",
        )

    tokens = token_resp.json()
    google_access_token = tokens.get("access_token")

    if not google_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No access_token received from Google",
        )

    # Step 2: Fetch Google user profile
    logger.info("Fetching Google user profile")
    async with httpx.AsyncClient(timeout=10.0) as client:
        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_access_token}"},
        )

    if userinfo_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch user profile from Google",
        )

    google_user = userinfo_resp.json()
    email      = google_user.get("email")
    full_name  = google_user.get("name", "")
    avatar_url = google_user.get("picture", "")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account does not expose an email address. Ensure the 'email' scope is granted.",
        )

    logger.info(f"Google OAuth callback: email={email}, name={full_name}")

    # Step 3: Get or create Supabase user
    user_id = await _get_or_create_supabase_user(email, full_name, avatar_url)

    # Step 4: Mint a Supabase-compatible JWT
    session = _mint_supabase_jwt(user_id, email)

    # Step 5: Redirect to frontend with the token in the URL fragment
    # The frontend AuthCallback.jsx will pick this up and store the session.
    access_token = session["access_token"]
    redirect_url = (
        f"{settings.FRONTEND_URL}/auth/callback"
        f"#access_token={access_token}"
        f"&token_type=bearer"
        f"&expires_in={session['expires_in']}"
    )
    logger.info(f"Google OAuth complete for {email} — redirecting to frontend")
    return RedirectResponse(url=redirect_url, status_code=302)


# ══════════════════════════════════════════════════════════════════════════════
#  Endpoint 3 — Verify a Google ID Token (One Tap / Mobile)
# ══════════════════════════════════════════════════════════════════════════════

class GoogleTokenRequest(BaseModel):
    id_token: str


@router.post(
    "/verify",
    summary="Verify a Google ID token",
    description=(
        "Accepts a Google ID token (e.g., from Google One Tap or a native mobile app), "
        "verifies it against Google's public certificates, "
        "creates or finds the Supabase user, and returns a Supabase-compatible session."
    ),
)
async def google_verify_token(body: GoogleTokenRequest):
    """
    Verify a Google ID token directly — no redirect required.

    Use this endpoint when the frontend (or mobile app) has obtained a
    Google ID token via the Google Sign-In JavaScript library or Google One Tap,
    and wants to exchange it for a SupplyShield session without a full page redirect.

    Request body:
        { "id_token": "<google_id_token>" }

    Returns:
        { "access_token": "...", "token_type": "bearer", "expires_in": 3600, "user": {...} }
    """
    _require_google_config()

    if not GOOGLE_AUTH_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="google-auth library is not installed. Run: pip install google-auth",
        )

    # Verify the Google ID token against Google's public certificates
    try:
        idinfo = google_id_token.verify_oauth2_token(
            body.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        logger.warning(f"Google ID token verification failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired Google ID token: {str(exc)}",
        )

    email      = idinfo.get("email")
    full_name  = idinfo.get("name", "")
    avatar_url = idinfo.get("picture", "")

    if not idinfo.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This Google account's email address is not verified by Google.",
        )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google ID token does not contain an email address.",
        )

    logger.info(f"Google ID token verified for: {email}")

    # Get or create Supabase user
    user_id = await _get_or_create_supabase_user(email, full_name, avatar_url)

    # Mint session
    return _mint_supabase_jwt(user_id, email)
