from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional
from uuid import uuid4
import os
import datetime

from app.core.config import Settings, get_settings
from app.core.db import dynamodb
from app.lib.build_firmware import build_zip, put_data, run_build
from app.lib.data import create_new_device, device_connect_check, find_bottle_and_env_state, get_device_info, get_os_file_content, manual_device_shot, manual_scan_bottle, update_device_all_info, update_device_info
from app.lib.device import generate_device_token
from app.lib.auth import require_user
from app.lib.file import download_file_requests, upload_file, upload_file_check
# table
from app.models.bottle import Bottle, BottleDetailInfo, BottleSingleInfo, BottleStatus, DetectRecord, DetectRecordState, DisplayState, EnvDetailInfo, GetDeviceInfo, ManualDeviceShot, NewDeviceInfo, Status
from app.models.bottle import UpdateBottle

device = APIRouter()

bottle_table = dynamodb.Table("bottle")

@device.post("/getDevice")
def get_device(data: GetDeviceInfo, user=Depends(require_user), settings: Settings = Depends(get_settings)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )
    if data.bottle_id is None:
        return JSONResponse(
            status_code=400,
            content={"message": "device_id are required"},
        )
    bottle = bottle_table.get_item(
        Key={"id": data.bottle_id}
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

@device.post("/manualUpdate")
def manual_update(file: UploadFile, temperature: Optional[float] = None, humidity: Optional[float] = None, user=Depends(require_user), settings: Settings = Depends(get_settings)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )
    try:
        upload_file_check(file, settings)
    except JSONResponse as e:
        return e

    res = manual_scan_bottle(file, temperature, humidity, settings)

    if not res:
        return JSONResponse(
            status_code=500,
            content={"message": "Failed to record manual update"},
        )
    if res.get("status_code", 500) != 200:
        return JSONResponse(
            status_code=res.get("status_code", 500),
            content={"message": res.get("message", "Failed to record manual update")},
        )

    try:
        ori_image_path = upload_file(user_id, file, "original", settings)
    except JSONResponse as e:
        return e

    ai_image_path = ori_image_path.replace("original", "ai")
    
    try:
        download_file_requests(res['orgPhotoUrl'], ai_image_path)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Failed to download original image: {str(e)}"},
        )
    detect_record_state, env_record_state = find_bottle_and_env_state(res['bottleStateID'], res.get('envStateID', ''), settings)

    bt_status = BottleStatus(detect_record_state['isAbnormal']) if detect_record_state else BottleStatus.UNKNOWN
    env_status = BottleStatus(env_record_state['isAbnormal']) if env_record_state else BottleStatus.UNKNOWN


    res_bottle = BottleSingleInfo(
        bottleState=BottleDetailInfo(
            bottle_status=str(bt_status),
            bottle_status_text=detect_record_state.get('type', "未知"),
            bottle_desc=detect_record_state.get('advice', "無")
        ),
        envState=EnvDetailInfo(
            env_status=str(env_status),
            env_status_text=env_record_state.get('type', "未知"),
            env_desc=env_record_state.get('advice', "無")
        ),
        displayState=DisplayState(
            temperature=temperature,
            humidity=humidity,
            time=datetime.datetime.utcnow().timestamp(),
        ),
        oriimageUri=ori_image_path,
        AIimageUri=ai_image_path,
    )

    return JSONResponse(
        status_code=200,
        constent=res_bottle.dict()
    )

@device.post("/newDevice")
def new_device(data: NewDeviceInfo,user=Depends(require_user), settings: Settings = Depends(get_settings)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )

    device_id = generate_device_token()

    res = create_new_device(device_id, data.name, data.detectFreq, settings)

    res2 = bottle_table.put_item(
        Item=Bottle(
            id=str(uuid4()),
            user_id=user_id,
            device_id=device_id,
            name=data.name,
            curr_image_path=None,
            curr_bottle_status=BottleStatus.UNKNOWN,
            curr_status=Status.PENDING
        ).dict()
    )

    if not res or not res2:
        return JSONResponse(
            status_code=500,
            content={"message": "Failed to create new device"},
        )

    CA = get_os_file_content(settings.IOT_CERT_CA).decode('utf-8')
    CRT = get_os_file_content(settings.IOT_CERT_CRT).decode('utf-8')
    PRIVATE = get_os_file_content(settings.IOT_PRIVATE_KEY).decode('utf-8')

    secrets_h =  put_data(
        WIFI_SSID=data.wifiSSID,
        WIFI_PASSWORD=data.wifiPassword,
        AWS_IOT_ENDPOINT=settings.IOT_ENDPOINT,
        DEVICE_ID=device_id,
        CERT_CA=CA,
        CERT_CRT=CRT,
        CERT_PRIVATE=PRIVATE,
    )

    res = update_device_all_info(device_id, data.name, data.detectFreq, settings.IOT_ENDPOINT, CRT, PRIVATE, settings)
    if not res:
        return JSONResponse(
            status_code=500,
            content={"message": "Failed to update device info"},
        )

    try:
        res_bin_path = run_build(device_id, secrets_h, settings)
        if not res_bin_path:
            raise Exception("請先建立專案目錄並放入程式碼。")
        res_zip_path = build_zip(device_id, secrets_h, settings)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Failed to build firmware: {str(e)}"},
        )

    return JSONResponse(
        status_code=200,
        content={
            "device_id": device_id,
        },
    )

@device.get("/{device_id}/bin")
async def download_device_firmware(device_id: str, settings: Settings = Depends(get_settings), user=Depends(require_user)):
    file_path = f"{settings.FILE_FOLDER}/{device_id}/{device_id}.bin"
    
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=f"firmware_{device_id}.bin",
            media_type="application/octet-stream"
        )
    return JSONResponse(
        status_code=404,
        content={"message": "Firmware not found"},
    )

@device.get("/{device_id}/zip")
async def download_device_firmware_zip(device_id: str, settings: Settings = Depends(get_settings), user=Depends(require_user)):
    file_path = f"{settings.FILE_FOLDER}/{device_id}/{device_id}.zip"
    
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=f"firmware_{device_id}.zip",
            media_type="application/zip"
        )
    return JSONResponse(
        status_code=404,
        content={"message": "Firmware zip not found"},
    )

@device.post("/manualScan")
def manual_scan(data: ManualDeviceShot, user=Depends(require_user), settings: Settings = Depends(get_settings)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )
    try:
        res = manual_device_shot(data.device_id, settings)
    except JSONResponse as e:
        return e

    if not res:
        return JSONResponse(
            status_code=500,
            content={"message": "Failed to trigger manual scan"},
        )
    return JSONResponse(
        status_code=200,
        content={"message": "Manual scan triggered successfully"},
    )

@device.get("/{device_id}/connect")
def check_device_connect(device_id: str, settings: Settings = Depends(get_settings), user=Depends(require_user)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )
    isConnected = device_connect_check(device_id, settings)
    if isConnected is None:
        return JSONResponse(
            status_code=500,
            content={"message": "Failed to check device connection"},
        )

    return JSONResponse(
        status_code=200,
        content={"isConnected": isConnected},
    )