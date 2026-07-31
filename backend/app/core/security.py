import logging
from typing import Optional, List
import jwt
from jwt import PyJWTError
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

logger = logging.getLogger("app")

# Bearer token security scheme — auto_error=False so we can return custom errors
security_scheme = HTTPBearer(auto_error=False)


class UserPrincipal:
    """
    Represents the authenticated user extracted from a verified Supabase JWT.
    """
    def __init__(self, user_id: str, email: str, roles: List[str], user_metadata: dict = None):
        self.user_id = user_id
        self.email = email
        self.roles = roles
        self.user_metadata = user_metadata or {}

    @property
    def role(self) -> str:
        """Primary role extracted from JWT claim or user_metadata."""
        meta_role = self.user_metadata.get("role")
        if meta_role:
            return meta_role
        return self.roles[0] if self.roles else "authenticated"

    @property
    def is_approved(self) -> bool:
        """Whether this supplier account has been approved by an admin."""
        if "is_approved" in self.user_metadata:
            return bool(self.user_metadata.get("is_approved"))
        return True

    @property
    def is_admin(self) -> bool:
        return self.role in ("admin", "service_role")

    @property
    def is_supplier(self) -> bool:
        return self.role == "supplier" or self.user_metadata.get("role") == "supplier"



import time
import datetime
import requests
from jwt import PyJWKSet

class SupabaseJWTVerifier:
    def __init__(self):
        self.jwk_set: Optional[PyJWKSet] = None
        self.last_fetch: float = 0.0

    def get_public_key(self, kid: str):
        now = time.time()
        if not self.jwk_set or (now - self.last_fetch) > 3600:
            self._fetch_jwks()
            
        key = self._find_key(kid)
        if not key:
            self._fetch_jwks()
            key = self._find_key(kid)
        return key

    def _find_key(self, kid: str):
        if not self.jwk_set or not kid:
            return None
        for jwk in self.jwk_set.keys:
            if jwk.key_id == kid:
                return jwk.key
        return None

    def _fetch_jwks(self):
        if not settings.SUPABASE_URL:
            return
        try:
            url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                self.jwk_set = PyJWKSet.from_dict(resp.json())
                self.last_fetch = time.time()
        except Exception as e:
            logger.error(f"Failed to fetch Supabase JWKS from {url}: {e}")

_jwt_verifier = SupabaseJWTVerifier()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> UserPrincipal:
    """
    Validates a Supabase JWT Bearer token and returns the authenticated user.

    Supports both:
    1. ES256 / RS256 asymmetric keys (verified via Supabase JWKS)
    2. HS256 symmetric keys (verified via SUPABASE_JWT_SECRET)
    """
    if not credentials:
        logger.warning("Request received without Authorization header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")
        kid = header.get("kid")
    except Exception as e:
        logger.warning(f"Could not parse JWT header: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed JWT token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    key = None
    if alg in ["ES256", "RS256", "EdDSA"]:
        key = _jwt_verifier.get_public_key(kid)
        if not key:
            logger.error(f"Public key not found for kid: {kid}")
    
    if key is None:
        if not settings.SUPABASE_JWT_SECRET:
            logger.error("SUPABASE_JWT_SECRET is not configured. Cannot validate tokens.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service is not configured",
            )
        key = settings.SUPABASE_JWT_SECRET

    decode_options_list = [
        {"audience": "authenticated"},      # Supabase v1 / projects with aud claim
        {"options": {"verify_aud": False}}, # Supabase v2 / projects without aud claim
    ]

    payload = None
    last_error = None

    for decode_kwargs in decode_options_list:
        try:
            payload = jwt.decode(
                token,
                key,
                algorithms=[alg],
                leeway=datetime.timedelta(seconds=60),  # Tolerate up to 60s clock skew (ImmatureSignatureError)
                **decode_kwargs,
            )
            break
        except jwt.ExpiredSignatureError:
            logger.warning("Rejected expired JWT token.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please sign in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except (jwt.InvalidAudienceError, jwt.MissingRequiredClaimError) as e:
            last_error = type(e).__name__
            continue
        except PyJWTError as e:
            logger.error(f"JWT validation failed exception ({alg}): {type(e).__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    if payload is None:
        logger.warning(f"JWT audience validation failed after all attempts: {last_error}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    email: str   = payload.get("email", "")
    role: str    = payload.get("role", "authenticated")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject claim",
        )

    logger.info(f"Authenticated user: {user_id} ({email}) role={role}")
    return UserPrincipal(
        user_id=user_id,
        email=email,
        roles=[role],
        user_metadata=payload.get("user_metadata", {}),
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Optional[UserPrincipal]:
    """
    Optional authentication dependency.
    Returns UserPrincipal if valid Bearer token provided, else returns None without raising 401.
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except Exception:
        return None






class RoleChecker:
    """
    FastAPI dependency for Role-Based Access Control (RBAC).
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: UserPrincipal = Depends(get_current_user)) -> UserPrincipal:
        logger.info(f"RBAC check — required: {self.allowed_roles}, user: {current_user.user_id}")
        has_role = any(role in self.allowed_roles for role in current_user.roles)
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return current_user


from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def validate_api_key(
    api_key: Optional[str] = Depends(api_key_header)
) -> str:
    """
    Validates API key for internal agent/system endpoints.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key header (X-API-Key) is missing",
        )
    return api_key


# ── Phase 9: Supplier Portal role dependencies ──────────────────────────────────

async def require_supplier(
    current_user: UserPrincipal = Depends(get_current_user),
) -> UserPrincipal:
    """
    FastAPI dependency that validates the caller is an *approved* supplier.
    """
    if not current_user.is_supplier and not current_user.user_metadata.get("role") == "supplier":
        from app.db.session import SessionLocal
        from app.supplier_portal.models.supplier_account import SupplierAccount
        db = SessionLocal()
        try:
            acct = db.query(SupplierAccount).filter_by(supabase_uid=current_user.user_id).first()
            if not acct and current_user.email:
                acct = db.query(SupplierAccount).filter_by(email=current_user.email).first()
            if not acct:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Supplier account required to access this resource",
                )
        finally:
            db.close()

    if not current_user.is_approved:
        from app.db.session import SessionLocal
        from app.supplier_portal.models.supplier_account import SupplierAccount
        db = SessionLocal()
        try:
            acct = db.query(SupplierAccount).filter_by(supabase_uid=current_user.user_id).first()
            if not acct and current_user.email:
                acct = db.query(SupplierAccount).filter_by(email=current_user.email).first()
            if not acct or acct.status.upper() != "APPROVED":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your supplier account is pending admin approval",
                )
        finally:
            db.close()

    return current_user



async def require_admin(
    current_user: UserPrincipal = Depends(get_current_user),
) -> UserPrincipal:
    """
    FastAPI dependency that validates the caller is an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return current_user


async def require_supplier_or_admin(
    current_user: UserPrincipal = Depends(get_current_user),
) -> UserPrincipal:
    """
    FastAPI dependency: allows either an approved supplier or an admin.
    Useful for read endpoints that admin should also be able to query.
    """
    if current_user.is_admin:
        return current_user
    if current_user.is_supplier and current_user.is_approved:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Approved supplier or admin access required",
    )
