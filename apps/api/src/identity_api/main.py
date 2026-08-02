from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from identity_api.config import settings
from identity_api.redis_client import close_redis
from identity_api.routers import admin, auth, health, me, oauth, passkeys, webauthn

API_PREFIX = "/api"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup hooks go before yield; shutdown after.
    # Close the shared Redis client so connections do not leak on reload/exit.
    yield
    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Identity Platform API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    # Credentials (cookies) require an explicit origin allowlist — not "*".
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # All JSON/API routes live under /api so same-origin nginx can proxy
    # /api/* without colliding with SPA routes (/oauth/login, /admin/users, …).
    api = APIRouter(prefix=API_PREFIX)
    api.include_router(health.router)
    api.include_router(auth.router)
    api.include_router(me.router)
    api.include_router(passkeys.router)
    api.include_router(webauthn.router)
    api.include_router(oauth.router)
    api.include_router(admin.router)
    app.include_router(api)
    return app


app = create_app()
