"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.interfaces.api.auth import router as auth_router
from app.interfaces.api.calc import router as calc_router
from app.interfaces.api.calculation_runs import router as calculation_runs_router
from app.interfaces.api.health import router as health_router
from app.interfaces.api.projects import router as projects_router
from app.interfaces.api.reports import router as reports_router

app = FastAPI(title="Cranes Sizing Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(calc_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(calculation_runs_router)
app.include_router(reports_router)
