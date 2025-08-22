from fastapi import APIRouter

from app.api.endpoints import weather, auth, upload, export

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
