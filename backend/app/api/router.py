from fastapi import APIRouter, Depends

from app.api.routes import router as platform_router
from app.services.auth import get_current_role

api_router = APIRouter()
api_router.include_router(platform_router, dependencies=[Depends(get_current_role)])
