from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class WebAuthnCredentialResponse(BaseModel):
    """Browser credential JSON from SimpleWebAuthn / navigator.credentials."""

    model_config = ConfigDict(extra="allow")

    id: str
    rawId: str
    type: str = "public-key"
    response: dict[str, Any]
    clientExtensionResults: dict[str, Any] = Field(default_factory=dict)
    authenticatorAttachment: str | None = None


class RegisterOptionsOut(BaseModel):
    options: dict[str, Any]


class RegisterVerifyRequest(BaseModel):
    credential: WebAuthnCredentialResponse
    device_name: str | None = Field(default=None, max_length=255)


class LoginOptionsRequest(BaseModel):
    email: EmailStr


class LoginOptionsOut(BaseModel):
    options: dict[str, Any]


class LoginVerifyRequest(BaseModel):
    email: EmailStr
    credential: WebAuthnCredentialResponse


class PasskeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_name: str | None
    transports: list[str] | None
    created_at: datetime
    last_used_at: datetime | None
    sign_count: int


class PasskeyRenameRequest(BaseModel):
    device_name: str = Field(min_length=1, max_length=255)
