"""
Idempotent local seed: admin user + demo OAuth client.

  cd apps/api
  alembic upgrade head
  python -m identity_api.seed

Reads SEED_* / DEMO_* from repo-root .env (see .env.example).
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from identity_api import db as db_mod
from identity_api.config import get_settings
from identity_api.models import OAuthClient, User
from identity_api.security import hash_password


async def seed() -> None:
    settings = get_settings()
    email = settings.seed_admin_email.lower().strip()
    password = settings.seed_admin_password

    async with db_mod.SessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password(password),
                is_active=True,
                is_admin=True,
            )
            db.add(user)
            print(f"Created admin user: {email}")
        else:
            # Ensure local bootstrap stays admin/active; refresh password hash.
            user.is_admin = True
            user.is_active = True
            user.password_hash = hash_password(password)
            print(f"Updated admin user: {email}")

        client_id = settings.demo_client_id.strip()
        redirect = settings.demo_redirect_uri.strip()
        existing = await db.execute(
            select(OAuthClient).where(OAuthClient.client_id == client_id)
        )
        client = existing.scalar_one_or_none()
        if client is None:
            db.add(
                OAuthClient(
                    client_id=client_id,
                    name=settings.demo_client_name,
                    redirect_uris=[redirect],
                    is_confidential=False,
                    client_secret_hash=None,
                )
            )
            print(f"Created OAuth client: {client_id} → {redirect}")
        else:
            # Keep redirect allowlist in sync with .env for local demo.
            if redirect not in (client.redirect_uris or []):
                client.redirect_uris = list(
                    dict.fromkeys([*(client.redirect_uris or []), redirect])
                )
            client.name = settings.demo_client_name
            print(f"Updated OAuth client: {client_id}")

        await db.commit()

    await db_mod.engine.dispose()
    print("Seed complete.")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
