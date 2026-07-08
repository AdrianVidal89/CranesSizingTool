"""FastAPI application entrypoint (Phase 1 — no persistence, no auth)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ALLOWED_ORIGINS
from app.interfaces.api.calc import router as calc_router
from app.interfaces.api.health import router as health_router

app = FastAPI(title="Cranes Sizing Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(calc_router)
