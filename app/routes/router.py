from fastapi import APIRouter

from app.routes.api.login import login_app

router = APIRouter()

router.include_router(
    prefix="/users",
    tags=["users"],
    router=login_app,
)


