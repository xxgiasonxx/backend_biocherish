from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import JSONResponse
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional
from uuid import uuid4
import os
import datetime

from app.core.config import Settings, get_settings
from app.core.db import dynamodb
from app.lib.data import get_device_info, update_device_info
from app.lib.device import verify_device_token, generate_device_token
from app.lib.auth import require_user
# table
from app.models.bottle import DetectRecord, DetectRecordState
from app.models.bottle import UpdateBottle

device = APIRouter()

bottle_table = dynamodb.Table("bottle")

@device.post("/getAllDeviceToken")
def get_all_device_token(user=Depends(require_user)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )

    devices = device_set_table.scan(
        FilterExpression=Attr('user_id').eq(user_id)
    ).get("Items", [])

    tokens = []
    for device in devices:
        token = generate_device_token(device['device_id'], device['bottle_id'])
        tokens.append({
            "bottle_id": device['bottle_id'],
            "token": token
        })

    return JSONResponse(
        status_code=200,
        content={"devices": tokens},
    )

@device.post("/getDevice")
def get_device(bottle_id: str, name: str, user=Depends(require_user), settings: Settings = Depends(get_settings)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )
    if bottle_id is None or name is None:
        return JSONResponse(
            status_code=400,
            content={"message": "device_id and name are required"},
        )
    bottle = bottle_table.get_item(
        Key={"id": bottle_id}
    ).get("Item", None)
    if not bottle or bottle.get("user_id", None) != user_id:
        return JSONResponse(
            status_code=404,
            content={"message": "Bottle not found"},
        )

    device_info = get_device_info(bottle.get("device_id", ""), settings)

    return JSONResponse(
        status_code=200,
        content={
            "device_id": device_info.get("device_id", ""),
            "name": device_info.get("name", ""),
            "detectFreq": device_info.get("detectFreq", 30),
        },
    )

@device.put("/updateDevice")
def update_device(freq: int, name: str, device_id: str, user=Depends(require_user), settings: Settings = Depends(get_settings)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )

    data = {
        "device_id": device_id,
        "name": name,
        "detectFreq": freq,
    }

    success = update_device_info(data, settings)

    if not success:
        return JSONResponse(
            status_code=500,
            content={"message": "Failed to update device"},
        )

    return JSONResponse(
        status_code=200,
        content={"message": "Device updated successfully"},
    )
