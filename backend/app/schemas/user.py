from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr
from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.ENGINEER


class UserRead(UserBase):
    id: UUID
    org_id: UUID
    role: UserRole
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
