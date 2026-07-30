from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from identity_api.db import get_db
from identity_api.deps import AuthContext, client_ip, get_current_auth
from identity_api.redis_client import get_redis
from identity_api.schemas import MessageOut, SessionOut
from identity_api.services import sessions as session_service
from identity_api.services.audit import write_audit

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
) -> list[SessionOut]:
    rows = await session_service.list_user_sessions(db, auth.user.id)
    return [
        SessionOut(
            id=row.id,
            user_agent=row.user_agent,
            ip_address=row.ip_address,
            created_at=row.created_at,
            expires_at=row.expires_at,
            is_current=row.id == auth.session.id,
        )
        for row in rows
    ]


@router.post("/sessions/{session_id}/revoke", response_model=MessageOut)
async def revoke_session(
    session_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    auth: AuthContext = Depends(get_current_auth),
) -> MessageOut:
    rows = await session_service.list_user_sessions(db, auth.user.id)
    target = next((s for s in rows if s.id == session_id), None)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    await session_service.revoke_session(db, redis, target)
    await write_audit(
        db,
        action="session.revoke",
        actor_user_id=auth.user.id,
        target_type="session",
        target_id=str(target.id),
        ip_address=client_ip(request),
    )
    await db.commit()
    return MessageOut(message="Session revoked")
