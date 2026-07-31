"""
Auth schemas — registration, login, account status responses.
"""
from __future__ import annotations
import re
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict


# ── Password rules ────────────────────────────────────────────────────────────

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&^#_\-])[A-Za-z\d@$!%*?&^#_\-]{8,}$"
)
PHONE_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")


def validate_password(v: str) -> str:
    if not PASSWORD_REGEX.match(v):
        raise ValueError(
            "Password must be at least 8 characters and contain uppercase, "
            "lowercase, digit, and special character (@$!%*?&^#_-)"
        )
    return v


def validate_phone(v: Optional[str]) -> Optional[str]:
    if v and not PHONE_REGEX.match(v):
        raise ValueError("Invalid phone number. Use E.164 format: +[country][number]")
    return v


# ── Request schemas ───────────────────────────────────────────────────────────

class SupplierRegisterRequest(BaseModel):
    """Payload for POST /supplier-portal/auth/register"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    company_name: str = Field(..., min_length=2, max_length=200)
    contact_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None
    # Module B — invitation token (optional for backward compatibility)
    invitation_token: Optional[str] = Field(None, min_length=64, max_length=64)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_password(v)

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v: Optional[str]) -> Optional[str]:
        return validate_phone(v)


class SupplierLoginRequest(BaseModel):
    """Payload for POST /supplier-portal/auth/login"""
    email: EmailStr
    password: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8)
    token: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_password(v)


class ChangePasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8)
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_password(v)

    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


# ── Response schemas ──────────────────────────────────────────────────────────

class SupplierAccountStatusResponse(BaseModel):
    """Account approval status for pre-login or profile pages."""
    supplier_id: str
    email: str
    company_name: str
    status: str           # PENDING | APPROVED | REJECTED | SUSPENDED
    is_email_verified: bool
    rejection_reason: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupplierAuthResponse(BaseModel):
    """Returned after successful login."""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    supplier_id: str
    email: str
    company_name: str
    status: str
