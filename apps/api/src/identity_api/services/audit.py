from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from identity_api.models import AuditLog


async def write_audit(
    db: AsyncSession,
    *,
    action: str,
    actor_user_id: UUID | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_json=metadata,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
    return entry
