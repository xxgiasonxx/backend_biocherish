from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import JSONResponse
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional
from uuid import uuid4
import os
import datetime

from app.core.config import Settings, get_settings
from app.core.db import dynamodb
from app.lib.device import verify_device_token, generate_device_token
from app.lib.auth import require_user
# table
from app.models.bottle import DetectRecord, DetectRecordState
from app.models.bottle import UpdateBottle

device = APIRouter()

detect_record_table = dynamodb.Table("detect_record")
detect_record_state_table = dynamodb.Table("detect_record_state")
device_set_table = dynamodb.Table("deviceset")

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

@device.post("/update")
def update_bottle_info(token: str, file: UploadFile, temperature: Optional[float] = None, humidity: Optional[float] = None, settings: Settings = Depends(get_settings)):
    if not token:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized: Missing token"},
        )
    token = verify_device_token(token)

    if not token:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized: Invalid token"},
        )

    device_id = token.get("device_id")
    bottle_id = token.get("bottle_id")

    if device_id is None or bottle_id is None:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized: Invalid token data"},
        )

    if not os.path.exists(settings.UPLOAD_DIRECTORY):
        os.makedirs(settings.UPLOAD_DIRECTORY)

    bottle_folder = os.path.join(settings.UPLOAD_DIRECTORY, str(bottle_id))
    if not os.path.exists(bottle_folder):
        os.makedirs(bottle_folder)

    folder_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    scan_folder = os.path.join(bottle_folder, folder_name)
    os.makedirs(scan_folder)
 
    if not file:
        return JSONResponse(
            status_code=400,
            content={"message": "Bad Request: Missing image file"},
        )
    if file.content_type not in ["image/jpeg", "image/png"]:
        return JSONResponse(
            status_code=400,
            content={"message": "Bad Request: Invalid image file type"},
        )
    if file.size > 5 * 1024 * 1024:
        return JSONResponse(
            status_code=400,
            content={"message": "Bad Request: Image file size exceeds limit"},
        )

    try:
        file_path = os.path.join(scan_folder, f"original_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(file.file.read())
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Internal Server Error: Failed to save image file. {str(e)}"},
        )

    detect_record_state_id = str(uuid4())
    bottlestate = DetectRecordState(
        detect_record_state_id=detect_record_state_id,
    )
    detect_record_state_table.put_item(
        Item=bottlestate.dict(),
    )

    bottlescan = DetectRecord(
        detect_record_id=str(uuid4()),
        bottleStateID=detect_record_state_id,
        device_id=device_id,
        bottle_id=bottle_id,
        temperature=temperature,
        humidity=humidity,
        orgPhotoUrl=file_path,
    )

    detect_record_table.put_item(
        Item=bottlescan.dict(),
    )

    return JSONResponse(
        status_code=200,
        content={"message": "Bottle scan data updated successfully"},
    )

