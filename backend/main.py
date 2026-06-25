"""
main.py — FastAPI application entry point for Mykare Voice AI backend.

Start with:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.database import init_db
from app.utils.logger import get_logger
from app.api.routes import router
from app.api.websocket import websocket_endpoint

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("startup", env=os.getenv("ENV", "development"))
    await init_db()
    logger.info("database_initialized")
    yield
    logger.info("shutdown")


app = FastAPI(
    title="Mykare Voice AI",
    description="Healthcare front-desk voice agent API",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── REST routes ──────────────────────────────────────────────────────────────
app.include_router(router, prefix="/api/v1")


# ── WebSocket ────────────────────────────────────────────────────────────────
from fastapi import WebSocket  # noqa: E402

@app.websocket("/ws/{room_name}")
async def ws_room(websocket: WebSocket, room_name: str):
    await websocket_endpoint(websocket, room_name)


# ── Global exception handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error("unhandled_exception", path=str(request.url), error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
