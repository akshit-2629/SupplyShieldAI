from fastapi import APIRouter, Depends
from app.core.security import get_current_user, validate_api_key, RoleChecker, UserPrincipal

router = APIRouter(prefix="/security-demo", tags=["Security Demo"])

@router.get("/jwt-protected")
def jwt_protected_route(current_user: UserPrincipal = Depends(get_current_user)):
    """
    Endpoint validating JWT access credentials.
    """
    return {
        "message": "Authorized JWT access successful.",
        "user_id": current_user.user_id,
        "roles": current_user.roles
    }

@router.get("/admin-only")
def admin_only_route(current_user: UserPrincipal = Depends(RoleChecker(["admin"]))):
    """
    Endpoint validating admin-level permissions using RBAC helper dependencies.
    """
    return {
        "message": "Authorized Admin access successful.",
        "user_id": current_user.user_id
    }

@router.get("/api-key-protected")
def api_key_protected_route(api_key: str = Depends(validate_api_key)):
    """
    Endpoint validating API credentials (e.g. system agent communication keys).
    """
    return {
        "message": "Authorized API Key access successful.",
        "api_key_preview": f"{api_key[:4]}..."
    }
