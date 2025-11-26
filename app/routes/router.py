from fastapi import APIRouter, Depends, HTTPException, status

from app.lib.auth import require_user
from app.routes.api.auth import auth
from app.routes.api.bottle import bottle
from app.routes.api.device import device



router = APIRouter()

router.include_router(
    prefix="/auth",
    tags=["auth"],
    router=auth,
)

router.include_router(
    prefix="/bottle",
    tags=["bottle"],
    router=bottle,
    dependencies=[Depends(require_user)],
)

router.include_router(
    prefix="/device",
    tags=["device"],
    router=device,
)
