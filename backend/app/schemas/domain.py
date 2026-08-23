from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.user import UserRole


# Generic Paginated Response Schema
class PaginatedResponse(BaseModel):
    total: int
    skip: int
    limit: int


# --- Team Member Schemas ---
class TeamMemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Full name of team member")
    email: EmailStr = Field(..., description="Email address")
    role: str = Field("Member", max_length=100, description="Role or job title")
    status: str = Field("active", description="Status (active/inactive)")


class TeamMemberUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[str] = None


class TeamMemberRead(BaseModel):
    id: UUID
    org_id: UUID
    user_id: Optional[UUID] = None
    name: str
    email: EmailStr
    role: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamMemberListResponse(PaginatedResponse):
    items: List[TeamMemberRead]


# --- Note / Brainstorm Board Schemas ---
class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of note")
    content: str = Field(..., min_length=1, description="Content or note body")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags like ['idea', 'blocker', 'decision', 'question']")


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None


class NoteRead(BaseModel):
    id: UUID
    org_id: UUID
    title: str
    content: str
    author_id: Optional[UUID] = None
    tags: Optional[List[str]] = Field(default=None, alias="tags_json")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class NoteListResponse(PaginatedResponse):
    items: List[NoteRead]


# --- Project Progress Schemas ---
class ProjectProgressCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Project title")
    status: str = Field("in_progress", description="Status (in_progress, completed, blocked, deferred)")
    progress_pct: int = Field(0, ge=0, le=100, description="Percentage completed (0-100)")
    owner_id: Optional[UUID] = Field(None, description="Optional user ID of project owner")
    target_date: Optional[datetime] = None


class ProjectProgressUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = None
    progress_pct: Optional[int] = Field(None, ge=0, le=100)
    owner_id: Optional[UUID] = None
    target_date: Optional[datetime] = None


class ProjectProgressRead(BaseModel):
    id: UUID
    org_id: UUID
    title: str
    status: str
    progress_pct: int
    owner_id: Optional[UUID] = None
    target_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectProgressListResponse(PaginatedResponse):
    items: List[ProjectProgressRead]


# --- Change Schemas ---
class ChangeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Change title")
    description: str = Field(..., min_length=1, description="Detailed deployment / change description")
    status: str = Field("pending", description="Status (pending, approved, deployed, rolled_back)")
    deployment_date: Optional[datetime] = None
    risk_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="Optional numerical risk score")
    metadata: Optional[dict] = Field(default_factory=dict, description="Custom metadata dictionary")


class ChangeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = None
    deployment_date: Optional[datetime] = None
    risk_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    metadata: Optional[dict] = None


class ChangeRead(BaseModel):
    id: UUID
    org_id: UUID
    title: str
    description: str
    status: str
    author_id: Optional[UUID] = None
    deployment_date: Optional[datetime] = None
    risk_score: Optional[float] = None
    metadata: Optional[dict] = Field(default=None, alias="metadata_json")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ChangeListResponse(PaginatedResponse):
    items: List[ChangeRead]


# --- Risk Analysis Schemas ---
class RiskAnalysisRead(BaseModel):
    id: UUID
    org_id: UUID
    change_id: UUID
    technical_summary: str
    business_summary: str
    risk_level: str
    risk_score: Optional[float] = None
    recommendations: List[str] = Field(default_factory=list)
    is_degraded: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Org Invite & Member Management Schemas ---
class InviteCreate(BaseModel):
    email: EmailStr = Field(..., description="Recipient email address")
    role: UserRole = Field(UserRole.ENGINEER, description="Assigned user role")


class InviteRead(BaseModel):
    id: UUID
    org_id: UUID
    email: EmailStr
    role: UserRole
    token: str
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InviteAcceptRequest(BaseModel):
    token: str = Field(..., description="Invite token received via link")
    password: str = Field(..., min_length=8, description="Set account password")
    name: Optional[str] = Field(None, description="Optional user name")


class RoleUpdatePayload(BaseModel):
    role: UserRole = Field(..., description="New UserRole")


# --- Audit Log Schemas ---
class AuditLogRead(BaseModel):
    id: UUID
    org_id: UUID
    actor_user_id: Optional[UUID] = None
    action: str
    target_type: str
    target_id: Optional[str] = None
    metadata: Optional[dict] = Field(default=None, alias="metadata_json")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AuditLogListResponse(PaginatedResponse):
    items: List[AuditLogRead]
