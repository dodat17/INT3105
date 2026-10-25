from fastapi import APIRouter

from app.api.auth.router import router as auth_router
from app.api.booking.router import admin_router as admin_booking_router
from app.api.booking.router import router as booking_router
from app.api.catalog.router import admin_router as admin_catalog_router
from app.api.catalog.router import router as catalog_router
from app.api.cinema.router import router as cinema_router
from app.api.health.router import router as health_router
from app.api.scheduling.router import admin_router as admin_scheduling_router
from app.api.scheduling.router import router as scheduling_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(catalog_router)
api_router.include_router(scheduling_router)
api_router.include_router(booking_router)
api_router.include_router(admin_catalog_router)
api_router.include_router(cinema_router)
api_router.include_router(admin_scheduling_router)
api_router.include_router(admin_booking_router)

root_router = APIRouter()
root_router.include_router(health_router)
root_router.include_router(api_router)
