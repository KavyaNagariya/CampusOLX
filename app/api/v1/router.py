from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.items import router as items_router
from app.api.v1.categories import router as categories_router
from app.api.v1.reservations import router as reservations_router
from app.api.v1.reports import router as reports_router
from app.api.v1.ratings import router as ratings_router
from app.api.v1.admin import router as admin_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(items_router)
api_router.include_router(categories_router)
api_router.include_router(reservations_router)
api_router.include_router(reports_router)
api_router.include_router(ratings_router)
api_router.include_router(admin_router)

