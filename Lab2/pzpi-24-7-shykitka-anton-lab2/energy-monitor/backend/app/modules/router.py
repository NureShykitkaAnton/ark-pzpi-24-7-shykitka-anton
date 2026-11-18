"""Головний агрегатор маршрутизаторів прикладного програмного інтерфейсу (/api/v1)."""

from fastapi import APIRouter

from app.modules.admin.router import router as admin_router
from app.modules.anomalies.router import router as anomalies_router
from app.modules.auth.router import router as auth_router
from app.modules.budgets.router import router as budgets_router
from app.modules.health.router import router as health_router
from app.modules.lines.router import router as lines_router
from app.modules.notifications.router import router as notifications_router
from app.modules.tariffs.router import router as tariffs_router
from app.modules.telemetry.router import router as telemetry_router
from app.modules.users.router import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(tariffs_router)
api_router.include_router(lines_router)
api_router.include_router(budgets_router)
api_router.include_router(telemetry_router)
api_router.include_router(anomalies_router)
api_router.include_router(notifications_router)
api_router.include_router(admin_router)
