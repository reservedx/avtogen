from fastapi import APIRouter

from app.api.routes import router as platform_router

api_router = APIRouter()
api_router.include_router(platform_router)
