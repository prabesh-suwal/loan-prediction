from fastapi import APIRouter

from app.api.v1.endpoints import loans, admin, health

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(loans.router, prefix="/loans", tags=["loans"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"]) 
api_router.include_router(health.router, prefix="/health", tags=["health"])

