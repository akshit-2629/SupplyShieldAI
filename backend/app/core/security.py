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
    def __init__(self, user_id: str, email: str, roles: List[str]):
        self.user_id = user_id
        self.email = email
        self.roles = roles


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> UserPrincipal:
    """
    Validates a Supabase JWT Bearer token and returns the authenticated user.

    Supabase issues HS256 JWTs signed with the project JWT secret.
    The token audience is "authenticated" for logged-in users.
    """
    if not credentials:
        logger.warning("Request received without Authorization header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Guard against missing configuration
    if not settings.SUPABASE_JWT_SECRET:
        logger.error("SUPABASE_JWT_SECRET is not configured. Cannot validate tokens.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service is not configured",
        )

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )

        user_id: str = payload.get("sub")
        email: str = payload.get("email", "")
        role: str = payload.get("role", "authenticated")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing subject claim",
            )

        logger.info(f"Authenticated user: {user_id} ({email})")
        return UserPrincipal(user_id=user_id, email=email, roles=[role])

    except jwt.ExpiredSignatureError:
        logger.warning("Rejected expired JWT token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidAudienceError:
        logger.warning("Rejected JWT with invalid audience claim.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except PyJWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


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
