from fastapi import APIRouter, Depends
from app.core.security import get_current_user, UserPrincipal

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me")
async def get_me(current_user: UserPrincipal = Depends(get_current_user)):
    """
    Returns the authenticated user's profile extracted from the Supabase JWT.
    This endpoint is protected — a valid Bearer token is required.
    """
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "roles": current_user.roles,
    }


@router.get("/verify")
async def verify_token(current_user: UserPrincipal = Depends(get_current_user)):
    """
    Lightweight token verification endpoint.
    Returns 200 if the token is valid, 401 otherwise.
    Useful for frontend pre-flight auth checks.
    """
    return {
        "valid": True,
        "user_id": current_user.user_id,
    }
