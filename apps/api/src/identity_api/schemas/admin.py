from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from identity_api.schemas.auth import UserOut
from identity_api.schemas.oauth import OAuthClientOut


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None


class UserListOut(BaseModel):
    items: list[UserOut]
    total: int


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_user_id: UUID | None
    action: str
    target_type: str | None
    target_id: str | None
    metadata_json: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime


class AuditLogListOut(BaseModel):
    items: list[AuditLogOut]
    total: int


class OAuthClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    redirect_uris: list[str] | None = Field(default=None, min_length=1)
    # Rotate secret only when provided; omit to leave unchanged.
    client_secret: str | None = Field(default=None, min_length=8, max_length=128)


class OAuthClientListOut(BaseModel):
    items: list[OAuthClientOut]
    total: int
