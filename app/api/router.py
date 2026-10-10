from fastapi import APIRouter

from app.api.routes import calendar, cases, diary_entries, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(cases.router, prefix="/api/v1")
api_router.include_router(diary_entries.router, prefix="/api/v1")
api_router.include_router(calendar.router, prefix="/api/v1")
