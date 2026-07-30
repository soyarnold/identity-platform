from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_api.db import get_db
from identity_api.deps import AuthContext, client_ip, require_admin
from identity_api.models import AuditLog, OAuthClient, User
from identity_api.redis_client import get_redis
from identity_api.schemas import (
    MessageOut,
    OAuthClientCreate,
    OAuthClientOut,
    UserOut,
)
from identity_api.schemas.admin import (
    AdminUserUpdate,
    AuditLogListOut,
    AuditLogOut,
    OAuthClientListOut,
    OAuthClientUpdate,
    UserListOut,
)
from identity_api.security import hash_password
from identity_api.services import oauth as oauth_service
from identity_api.services import sessions as session_service
from identity_api.services.audit import write_audit

router = APIRouter(prefix="/admin", tags=["admin"])

_MAX_LIMIT = 100


@router.get("/users", response_model=UserListOut)
async def list_users(
    limit: Annotated[int, Query(ge=1, le=_MAX_LIMIT)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
    _auth: AuthContext = Depends(require_admin),
) -> UserListOut:
    total = await db.scalar(select(func.count()).select_from(User)) or 0
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    )
    users = list(result.scalars().all())
    return UserListOut(items=[UserOut.model_validate(u) for u in users], total=total)


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID,
    body: AdminUserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    auth: AuthContext = Depends(require_admin),
) -> UserOut:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if body.is_active is None and body.is_admin is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide is_active and/or is_admin",
        )

    # Prevent locking yourself out of the admin panel.
    if user.id == auth.user.id and body.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin role",
        )
    if user.id == auth.user.id and body.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable your own account",
        )

    if body.is_active is not None:
        user.is_active = body.is_active
        if not body.is_active:
            await session_service.revoke_all_user_sessions(db, redis, user.id)
    if body.is_admin is not None:
        user.is_admin = body.is_admin

    await write_audit(
        db,
        action="admin.user.update",
        actor_user_id=auth.user.id,
        target_type="user",
        target_id=str(user.id),
        metadata={
            "is_active": user.is_active,
            "is_admin": user.is_admin,
        },
        ip_address=client_ip(request),
    )
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/audit-logs", response_model=AuditLogListOut)
async def list_audit_logs(
    limit: Annotated[int, Query(ge=1, le=_MAX_LIMIT)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    action: Annotated[str | None, Query()] = None,
    db: AsyncSession = Depends(get_db),
    _auth: AuthContext = Depends(require_admin),
) -> AuditLogListOut:
    # Filter by action when provided; otherwise newest-first across all events.
    filters = []
    if action:
        filters.append(AuditLog.action == action)

    count_q = select(func.count()).select_from(AuditLog)
    list_q = select(AuditLog).order_by(AuditLog.created_at.desc())
    if filters:
        count_q = count_q.where(*filters)
        list_q = list_q.where(*filters)

    total = await db.scalar(count_q) or 0
    result = await db.execute(list_q.offset(offset).limit(limit))
    rows = list(result.scalars().all())
    return AuditLogListOut(
        items=[AuditLogOut.model_validate(r) for r in rows],
        total=total,
    )


@router.get("/oauth/clients", response_model=OAuthClientListOut)
async def list_oauth_clients(
    limit: Annotated[int, Query(ge=1, le=_MAX_LIMIT)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
    _auth: AuthContext = Depends(require_admin),
) -> OAuthClientListOut:
    total = await db.scalar(select(func.count()).select_from(OAuthClient)) or 0
    result = await db.execute(
        select(OAuthClient)
        .order_by(OAuthClient.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    clients = list(result.scalars().all())
    return OAuthClientListOut(
        items=[
            OAuthClientOut(
                client_id=c.client_id,
                name=c.name,
                redirect_uris=c.redirect_uris,
                is_confidential=c.is_confidential,
            )
            for c in clients
        ],
        total=total,
    )


@router.post(
    "/oauth/clients",
    response_model=OAuthClientOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_oauth_client(
    body: OAuthClientCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(require_admin),
) -> OAuthClientOut:
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
    await write_audit(
        db,
        action="admin.oauth_client.create",
        actor_user_id=auth.user.id,
        target_type="oauth_client",
        target_id=client.client_id,
        ip_address=client_ip(request),
    )
    await db.commit()
    return OAuthClientOut(
        client_id=client.client_id,
        name=client.name,
        redirect_uris=client.redirect_uris,
        is_confidential=client.is_confidential,
    )


@router.patch("/oauth/clients/{client_id}", response_model=OAuthClientOut)
async def update_oauth_client(
    client_id: str,
    body: OAuthClientUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(require_admin),
) -> OAuthClientOut:
    client = await oauth_service.get_client(db, client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    if body.name is None and body.redirect_uris is None and body.client_secret is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide name, redirect_uris, and/or client_secret",
        )
    if body.name is not None:
        client.name = body.name
    if body.redirect_uris is not None:
        client.redirect_uris = body.redirect_uris
    if body.client_secret is not None:
        if not client.is_confidential:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot set secret on a public client",
            )
        client.client_secret_hash = hash_password(body.client_secret)

    await write_audit(
        db,
        action="admin.oauth_client.update",
        actor_user_id=auth.user.id,
        target_type="oauth_client",
        target_id=client.client_id,
        ip_address=client_ip(request),
    )
    await db.commit()
    return OAuthClientOut(
        client_id=client.client_id,
        name=client.name,
        redirect_uris=client.redirect_uris,
        is_confidential=client.is_confidential,
    )


@router.delete("/oauth/clients/{client_id}", response_model=MessageOut)
async def delete_oauth_client(
    client_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(require_admin),
) -> MessageOut:
    client = await oauth_service.get_client(db, client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    await db.delete(client)
    await write_audit(
        db,
        action="admin.oauth_client.delete",
        actor_user_id=auth.user.id,
        target_type="oauth_client",
        target_id=client_id,
        ip_address=client_ip(request),
    )
    await db.commit()
    return MessageOut(message="Client deleted")
