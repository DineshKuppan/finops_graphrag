from fastapi import APIRouter

from app.api.routes import abac_demo, auth, pbac_demo, rbac_demo

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(rbac_demo.router)
api_router.include_router(abac_demo.router)
api_router.include_router(pbac_demo.router)
