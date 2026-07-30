from pydantic import BaseModel, Field


class ConsentRequest(BaseModel):
    client_id: str
    redirect_uri: str
    response_type: str = "code"
    code_challenge: str
    code_challenge_method: str = "S256"
    state: str | None = None
    scope: str | None = None
    approve: bool = True


class ConsentResponse(BaseModel):
    redirect_to: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: str | None = None
    scope: str | None = None


class UserInfoResponse(BaseModel):
    sub: str
    email: str
    email_verified: bool = True


class OAuthClientCreate(BaseModel):
    """Dev/test helper until admin CRUD lands in phase 07."""

    name: str = Field(min_length=1, max_length=255)
    client_id: str = Field(min_length=3, max_length=64)
    redirect_uris: list[str] = Field(min_length=1)
    is_confidential: bool = False
    client_secret: str | None = None


class OAuthClientOut(BaseModel):
    client_id: str
    name: str
    redirect_uris: list[str]
    is_confidential: bool
