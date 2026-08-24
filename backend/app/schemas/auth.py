import re
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models.user import UserRole


class SignupRequest(BaseModel):
    org_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")

    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter (A-Z)")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter (a-z)")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number (0-9)")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*)")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OrgOut(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: UUID
    org_id: UUID
    email: EmailStr
    role: UserRole
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    user: UserOut
    organization: OrgOut
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserMeResponse(BaseModel):
    user: UserOut
    organization: OrgOut
