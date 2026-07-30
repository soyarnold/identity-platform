from typing import Annotated
from urllib.parse import urlencode
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from identity_api.config import settings
from identity_api.db import get_db
from identity_api.deps import AuthContext, client_ip, get_current_auth
from identity_api.models import OAuthClient
from identity_api.redis_client import get_redis
from identity_api.schemas import (
    ConsentRequest,
    ConsentResponse,
    OAuthClientCreate,
    OAuthClientOut,
    TokenResponse,
    UserInfoResponse,
)
from identity_api.security import hash_password, verify_password
from identity_api.services import oauth as oauth_service
from identity_api.services.audit import write_audit

router = APIRouter(tags=["oauth"])


def _frontend_login_url(request: Request) -> str:
    # Build the hosted OAuth login URL, preserving authorize query params so the
    # SPA can resume the authorization request after the user signs in (phase 06).
    qs = urlencode(dict(request.query_params))
    return f"{settings.frontend_url.rstrip('/')}/oauth/login?{qs}"


def _frontend_consent_url(request: Request) -> str:
    # Build the hosted consent URL with the same authorize query string so the
    # SPA can show client/scopes and call POST /oauth/consent (phase 06).
    qs = urlencode(dict(request.query_params))
    return f"{settings.frontend_url.rstrip('/')}/oauth/consent?{qs}"


async def _require_valid_authorize_params(
    db: AsyncSession,
    *,
    client_id: str,
    redirect_uri: str,
    response_type: str,
    code_challenge: str | None,
    code_challenge_method: str | None,
) -> OAuthClient:
    # Shared validation for authorize + consent: Authorization Code + PKCE S256
    # only, known client_id, and redirect_uri must be on the client's allowlist.
    if response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="response_type must be code",
        )
    if not code_challenge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="code_challenge required (PKCE)",
        )
    if (code_challenge_method or "S256").upper() != "S256":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="code_challenge_method must be S256",
        )

    client = await oauth_service.get_client(db, client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown client_id",
        )
    if not oauth_service.validate_redirect_uri(client, redirect_uri):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri",
        )
    return client


@router.get("/.well-known/oauth-authorization-server")
async def authorization_server_metadata(request: Request) -> dict:
    # RFC 8414-style discovery document so clients can find authorize/token/userinfo
    # endpoints and supported grant / PKCE methods without hard-coding URLs.
    base = str(request.base_url).rstrip("/")
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "userinfo_endpoint": f"{base}/oauth/userinfo",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "scopes_supported": ["openid", "profile", "email", "offline_access"],
    }


@router.get("/oauth/authorize")
async def authorize(
    request: Request,
    client_id: Annotated[str, Query()],
    redirect_uri: Annotated[str, Query()],
    response_type: Annotated[str, Query()] = "code",
    code_challenge: Annotated[str | None, Query()] = None,
    code_challenge_method: Annotated[str | None, Query()] = "S256",
    state: Annotated[str | None, Query()] = None,
    scope: Annotated[str | None, Query()] = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    # OAuth authorization endpoint: validate the client/PKCE request, then 302 the
    # browser to hosted login (no sid cookie) or consent (sid present). Does not
    # issue codes here — that happens only after explicit consent.
    await _require_valid_authorize_params(
        db,
        client_id=client_id,
        redirect_uri=redirect_uri,
        response_type=response_type,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )
    # Presence of sid cookie only — full session check happens at consent.
    token = request.cookies.get(settings.cookie_name)
    if not token:
        return RedirectResponse(
            url=_frontend_login_url(request),
            status_code=status.HTTP_302_FOUND,
        )
    return RedirectResponse(
        url=_frontend_consent_url(request),
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/oauth/consent", response_model=ConsentResponse)
async def consent(
    body: ConsentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    auth: AuthContext = Depends(get_current_auth),
) -> ConsentResponse:
    # Hosted consent UI (phase 06) calls this after the user approves the client.
    # We mint a one-time auth code in Redis (PKCE challenge bound) and return the
    # third-party redirect_uri?code=&state= URL — no browser redirect from the API.
    client = await _require_valid_authorize_params(
        db,
        client_id=body.client_id,
        redirect_uri=body.redirect_uri,
        response_type=body.response_type,
        code_challenge=body.code_challenge,
        code_challenge_method=body.code_challenge_method,
    )
    if not body.approve:
        # Denial still returns redirect_to so the SPA can send the user back
        # with error=access_denied (OAuth 2.0).
        params = {"error": "access_denied"}
        if body.state:
            params["state"] = body.state
        return ConsentResponse(
            redirect_to=oauth_service.build_redirect_url(body.redirect_uri, **params)
        )

    scopes = oauth_service.normalize_scopes(body.scope)
    code = await oauth_service.issue_authorization_code(
        redis,
        client_id=client.client_id,
        user_id=auth.user.id,
        redirect_uri=body.redirect_uri,
        code_challenge=body.code_challenge,
        code_challenge_method=(body.code_challenge_method or "S256").upper(),
        scopes=scopes,
    )
    params = {"code": code}
    if body.state:
        params["state"] = body.state

    await write_audit(
        db,
        action="oauth.consent",
        actor_user_id=auth.user.id,
        target_type="oauth_client",
        target_id=client.client_id,
        ip_address=client_ip(request),
    )
    await db.commit()
    return ConsentResponse(
        redirect_to=oauth_service.build_redirect_url(body.redirect_uri, **params)
    )


@router.post("/oauth/token", response_model=TokenResponse)
async def token(
    request: Request,
    grant_type: Annotated[str, Form()],
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    code: Annotated[str | None, Form()] = None,
    redirect_uri: Annotated[str | None, Form()] = None,
    client_id: Annotated[str | None, Form()] = None,
    client_secret: Annotated[str | None, Form()] = None,
    code_verifier: Annotated[str | None, Form()] = None,
    refresh_token: Annotated[str | None, Form()] = None,
) -> TokenResponse:
    # Token endpoint (application/x-www-form-urlencoded): exchange an auth code
    # (+ PKCE verifier) or a refresh_token for access/refresh tokens. Public
    # clients skip client_secret; confidential clients must present it.
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_id required",
        )
    client = await oauth_service.get_client(db, client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client",
        )
    if client.is_confidential:
        if not client_secret or not client.client_secret_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client credentials",
            )
        if not verify_password(client.client_secret_hash, client_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client credentials",
            )

    if grant_type == "authorization_code":
        # Consume the one-time Redis code, verify PKCE S256, then issue tokens.
        if not code or not redirect_uri or not code_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="code, redirect_uri, and code_verifier required",
            )
        payload = await oauth_service.consume_authorization_code(redis, code)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired code",
            )
        if payload["client_id"] != client_id or payload["redirect_uri"] != redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="code mismatch",
            )
        if payload["code_challenge_method"] != "S256":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code_verifier",
            )
        if not oauth_service.verify_pkce_s256(
            code_verifier,
            payload["code_challenge"],
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code_verifier",
            )

        tokens = await oauth_service.issue_tokens(
            db,
            client_id=client_id,
            user_id=UUID(payload["user_id"]),
            scopes=payload["scopes"],
        )
        await write_audit(
            db,
            action="oauth.token",
            actor_user_id=UUID(payload["user_id"]),
            target_type="oauth_client",
            target_id=client_id,
            ip_address=client_ip(request),
        )
        await db.commit()
        return TokenResponse(**tokens)

    if grant_type == "refresh_token":
        # Rotate refresh token and issue a new access (+ refresh) pair.
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="refresh_token required",
            )
        tokens = await oauth_service.rotate_refresh_token(
            db,
            refresh_token=refresh_token,
            client_id=client_id,
        )
        if tokens is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid refresh_token",
            )
        await write_audit(
            db,
            action="oauth.refresh",
            target_type="oauth_client",
            target_id=client_id,
            ip_address=client_ip(request),
        )
        await db.commit()
        return TokenResponse(**tokens)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported grant_type",
    )


@router.get("/oauth/userinfo", response_model=UserInfoResponse)
async def userinfo(
    db: AsyncSession = Depends(get_db),
    authorization: Annotated[str | None, Header()] = None,
) -> UserInfoResponse:
    # OpenID-style userinfo: resolve Bearer access token to the resource owner
    # and return subject + email (expand claims later as needed).
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
        )
    access_token = authorization.split(" ", 1)[1].strip()
    result = await oauth_service.get_user_for_access_token(db, access_token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )
    user, _row = result
    return UserInfoResponse(sub=str(user.id), email=user.email)


@router.post(
    "/oauth/dev/clients",
    response_model=OAuthClientOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_dev_client(
    body: OAuthClientCreate,
    db: AsyncSession = Depends(get_db),
) -> OAuthClientOut:
    # Temporary helper for local/manual testing until admin client CRUD (phase 07).
    # Registers a public or confidential OAuth client with allowed redirect_uris.
    existing = await oauth_service.get_client(db, body.client_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="client_id already exists",
        )
    if body.is_confidential and not body.client_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_secret required for confidential clients",
        )
    client = OAuthClient(
        client_id=body.client_id,
        name=body.name,
        redirect_uris=body.redirect_uris,
        is_confidential=body.is_confidential,
        client_secret_hash=(
            hash_password(body.client_secret)
            if body.is_confidential and body.client_secret
            else None
        ),
    )
    db.add(client)
    await db.commit()
    return OAuthClientOut(
        client_id=client.client_id,
        name=client.name,
        redirect_uris=client.redirect_uris,
        is_confidential=client.is_confidential,
    )


# ---------------------------------------------------------------------------
# URL flow — third-party client sign-in via this authorization server (PKCE)
#
# Example client: demo app at http://localhost:5174 (client_id=demo-app)
# Identity web UI: http://localhost:5173  |  API: http://localhost:8000
#
# 1) User clicks "Sign in" on the client app.
#    Client generates code_verifier / code_challenge (S256) and redirects browser:
#      GET http://localhost:8000/oauth/authorize
#          ?client_id=demo-app
#          &redirect_uri=http://localhost:5174/callback
#          &response_type=code
#          &code_challenge=<S256>
#          &code_challenge_method=S256
#          &state=<csrf>
#          &scope=openid%20profile%20email
#
# 2) /oauth/authorize validates client + PKCE, then 302s:
#    - No sid cookie → hosted login (preserve query string):
#        http://localhost:5173/oauth/login?<same authorize params>
#    - Has sid cookie → hosted consent:
#        http://localhost:5173/oauth/consent?<same authorize params>
#
# 3) If login was required, user signs in/registers on the hosted UI (session
#    cookie set via /auth/*). SPA then navigates to /oauth/consent with params.
#
# 4) User approves on consent UI → SPA POST /oauth/consent (cookie auth) →
#    API returns JSON { redirect_to: "http://localhost:5174/callback?code=...&state=..." }
#    SPA performs location redirect to that URL.
#
# 5) Client app callback exchanges the code (server-side or public PKCE):
#      POST http://localhost:8000/oauth/token
#          grant_type=authorization_code
#          code=...&redirect_uri=...&client_id=demo-app&code_verifier=...
#    → access_token (+ refresh_token)
#
# 6) Client calls:
#      GET http://localhost:8000/oauth/userinfo
#          Authorization: Bearer <access_token>
#    → { sub, email, ... }
#
# Deny path: consent with approve=false → redirect_to callback?error=access_denied&state=...
# ---------------------------------------------------------------------------
