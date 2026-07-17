from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import (
    routes_agents,
    routes_auth,
    routes_calls,
    routes_campaign,
    routes_customers,
    routes_debug,
    routes_knowledge,
    routes_telephony,
    routes_users,
)
from app.config import settings
from app.core.limiter import limiter
from app.database.session import ensure_database_exists, init_models
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.utils.logger import logger
from app.websocket.media_stream import handle_media_stream


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting up with APP_ENV='{settings.environment}' (loaded .env.{settings.environment})")
    ensure_database_exists()
    await init_models()
    logger.info("Startup complete.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="AI Voice Calling Agent Platform",
    description="Platform for creating AI agents that make outbound calls, "
                 "converse naturally using RAG-grounded knowledge, and extract "
                 "structured lead data from every call.",
    version="1.0.0",
    lifespan=lifespan,
    # Hide interactive docs in production; keep them for local/staging.
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)  # actually enforces default_limits globally

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

register_exception_handlers(app)

app.include_router(routes_auth.router)
app.include_router(routes_users.router)
app.include_router(routes_agents.router)
app.include_router(routes_knowledge.router)
app.include_router(routes_customers.router)
app.include_router(routes_campaign.router)
app.include_router(routes_calls.router)
app.include_router(routes_telephony.router)
app.include_router(routes_debug.router)


@app.websocket("/ws/media-stream/{call_id}")
async def media_stream_endpoint(websocket: WebSocket, call_id: str):
    await handle_media_stream(websocket, call_id)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
