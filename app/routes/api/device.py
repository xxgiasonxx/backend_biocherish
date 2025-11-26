from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import select
from app.core.db import db_dep
from app.models.bottle import UpdateBottle
from app.lib.device import verify_device_token


device = APIRouter()


@device.post("/update")
def update_bottle_info(form_data: UpdateBottle, bottle_id: int, db: db_dep):
    if not form_data.token:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized: Missing token"},
        )

    token = verify_device_token(form_data.token)

    if not token:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized: Invalid token"},
        )

    device_id = token.get("device_id")
    bottle_id_token = token.get("bottle_id")

    

    
    
