"""FastAPI application entry point."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title="ModelArena API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Anonymous session middleware
@app.middleware("http")
async def anon_session_middleware(request: Request, call_next):
    session_id = request.cookies.get("arena_session")
    if not session_id:
        session_id = str(uuid.uuid4())
        request.state.new_session = True
    else:
        request.state.new_session = False
    request.state.session_id = session_id
    response: Response = await call_next(request)
    if request.state.new_session:
        response.set_cookie(
            key="arena_session",
            value=session_id,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 365,
            path="/",
        )
    return response


# Import and include routers
from app.api.health import router as health_router  # noqa: E402
from app.api.auth import router as auth_router  # noqa: E402
from app.api.battles import router as battles_router  # noqa: E402
from app.api.leaderboard import router as leaderboard_router  # noqa: E402
from app.api.stats import router as stats_router  # noqa: E402
from app.api.admin import router as admin_router  # noqa: E402

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(battles_router, prefix="/api/battles")
app.include_router(leaderboard_router, prefix="/api")
app.include_router(stats_router, prefix="/api/stats")
app.include_router(admin_router, prefix="/api/admin")

