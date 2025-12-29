from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
from typing import Optional

from app.core.db import dynamodb
from app.lib.auth import require_user
from app.lib.data import device_is_connected, find_all_bottle_and_env_state, find_all_detect_record_with_detect_record_state, find_bottle_state, find_detect_record, get_bottle_detect_state_history, get_device_info, get_last_detect_record, split_all_detect_state_history
from app.lib.device import generate_device_token
# table
from app.models.bottle import Bottle, BottleSingleInfo, BottleStatus, DeviceSet, DisplayState, EnvDetailInfo
# models
from app.models.bottle import BottleMainInfo, BottleHistory, CreateBottle, BottleDetailInfo
from app.core.config import Settings, get_settings

bottle = APIRouter()

bottle_table = dynamodb.Table("bottle")
deviceset_table = dynamodb.Table("deviceset")
detect_record_table = dynamodb.Table("detect_record")
detect_record_state_table = dynamodb.Table("detect_record_state")


@bottle.get("/")
def get_bottle(user=Depends(require_user), settings: Settings = Depends(get_settings)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )
    bottles = bottle_table.query(
        IndexName="UserIdIndex",
        KeyConditionExpression=Key('user_id').eq(user_id),
    ).get("Items", [])

    res_ar = []

    for bottle in bottles:
        last_detect_record = get_last_detect_record(bottle['device_id'], settings)
        detect_record_state = last_detect_record.get('detect_record_state', {}) if last_detect_record else {}
        env_record_state = last_detect_record.get('env_record_state', {}) if last_detect_record else {}

        bt_status = BottleStatus(detect_record_state['isAbnormal']) if detect_record_state else BottleStatus.UNKNOWN

        env_status = BottleStatus(env_record_state['isAbnormal']) if env_record_state else BottleStatus.UNKNOWN

        print("Last Detect Record:", last_detect_record)

        device_info = get_device_info(bottle.get("device_id"), settings)
        
        res_ar.append(
            BottleMainInfo(
                id=str(bottle['id']),
                name=bottle['name'],
                bottle_status=str(bt_status),
                bottle_status_text=detect_record_state.get("type", "未知"),
                env_status=str(env_status),
                env_status_text=env_record_state.get("type", "未知"),
                isConnected=device_info.get("isConnected", False),
                imageurl=last_detect_record.get('origPhotoUrl', None) if last_detect_record else None,
                edited_at=int(bottle.get('edited_at', 0) * 1000),
                scanned_at=int(bottle.get('scanned_at', 0) * 1000),
            ).dict()
        )
    print(res_ar)

    return JSONResponse(
        status_code=200,
        content={"bottles": res_ar},
    )

@bottle.get("/{bottle_id}")
def get_bottle_info(bottle_id: UUID, settings: Settings = Depends(get_settings), user=Depends(require_user)):

    bottle = bottle_table.get_item(
        Key={"id": str(bottle_id)}
    ).get("Item", None)

    if not bottle:
        return JSONResponse(
            status_code=404,
            content={"message": "Bottle not found"},
        )


    last_detect_record = get_last_detect_record(str(bottle['device_id']), settings)

    detect_record_state = last_detect_record.get('detect_record_state', {}) if last_detect_record else {}
    env_record_state = last_detect_record.get('env_record_state', {}) if last_detect_record else {}



    if not last_detect_record or not last_detect_record.get('detect_record_id', None):
        return JSONResponse(
            status_code=404,
            content={"message": "No scans found for this bottle"},
        )

    # if not detect_record_state:
    #     return JSONResponse(
    #         status_code=404,
    #         content={"message": "Bottle state not found"},
    #     )

    # if not env_record_state:
    #     return JSONResponse(
    #         status_code=404,
    #         content={"message": "Environment state not found"},
    #     )

    bt_status = BottleStatus(detect_record_state['isAbnormal']) if detect_record_state else BottleStatus.UNKNOWN
    env_status = BottleStatus(env_record_state['isAbnormal']) if env_record_state else BottleStatus.UNKNOWN


    print(detect_record_state)

    res_bottle = BottleSingleInfo(
        detect_state_id=last_detect_record['detect_record_id'],
        name=bottle['name'],
        bottleState=BottleDetailInfo(
            bottle_status=str(bt_status),
            bottle_status_text=detect_record_state.get('type', '未知'),
            bottle_desc=detect_record_state.get('advice', "無")
        ),
        envState=EnvDetailInfo(
            env_status=str(env_status),
            env_status_text=env_record_state.get('type', '未知'),
            env_desc=env_record_state.get('advice', "無")
        ),
        displayState=DisplayState(
            temperature=last_detect_record.get('temperature', None),
            humidity=last_detect_record.get('humidity', None),
            time=int(last_detect_record.get('detectTime', 0) * 1000)
        ),
        oriimageUri=last_detect_record.get('origPhotoUrl', None),
        AIimageUri=last_detect_record.get('aiPhotoUrl', None),
    )

    return JSONResponse(
        status_code=200,
        content=res_bottle.dict()
    )

@bottle.get("/{bottle_id}/total")
def get_bottle_total(bottle_id: UUID, user=Depends(require_user), settings: Settings = Depends(get_settings)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )

    bottle = bottle_table.query(
        IndexName='UserIdIndex',
        KeyConditionExpression=Key('user_id').eq(str(user_id)),
        FilterExpression=Attr('id').eq(str(bottle_id))
    ).get("Items", [])
    bottle = bottle[0] if bottle else None

    if not bottle:
        return JSONResponse(
            status_code=404,
            content={"message": "Bottle not found"},
        )

    last_detect_record = get_bottle_detect_state_history(device_id=str(bottle['device_id']), s=0, e=None, settings=settings)

    if len(last_detect_record) == 0:
        return JSONResponse(
            status_code=200,
            content={"total_scans": 0},
        )


    if not last_detect_record:
        return JSONResponse(
            status_code=404,
            content={"message": "No scans found for this bottle"},
        )

    res = {
        "total_scans": len(last_detect_record)
    }

    print(res)

    return JSONResponse(
        status_code=200,
        content=res,
    )

@bottle.get("/{bottle_id}/history")
def get_bottle_history(bottle_id: str, s: int, e: int, user=Depends(require_user), settings: Settings = Depends(get_settings)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )

    if s < 0 or e < 0 or s > e or (e - s) > 100:
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid range"},
        )

    bottle = bottle_table.query(
        IndexName='UserIdIndex',
        KeyConditionExpression=Key('user_id').eq(str(user_id)),
        FilterExpression=Attr('id').eq(str(bottle_id))
    ).get("Items", [])
    bottle = bottle[0] if bottle else None

    if not bottle:
        return JSONResponse(
            status_code=404,
            content={"message": "Bottle not found"},
        )
    scans = get_bottle_detect_state_history(device_id=bottle.get("device_id", ""), s=0, e=None, settings=settings)

    state = find_all_bottle_and_env_state(settings) 


    scans = split_all_detect_state_history(scans, s, e, settings)

    print(scans)


    res_ar = []

    for scan in scans:
        bottle_status = find_bottle_state(state, scan['bottleStateID'])
        bt_status = BottleStatus(bottle_status['isAbnormal']) if bottle_status else BottleStatus.UNKNOWN

        res_ar.append(BottleHistory(
            id=scan['detect_record_id'],
            status=str(bt_status),
            status_text=bottle_status.get('type', 'No Data') if bottle_status else 'No Data',
            scanned_at=int(scan['detectTime'] * 1000),
            detail=f"/home/{bottle_id}/history/{str(scan['detect_record_id'])}"
        ))

    return JSONResponse(
        status_code=200,
        content={
            "history": [item.dict() for item in res_ar],
        },
    )

@bottle.get("/{bottle_id}/history/{history_id}")
def get_bottle_history_detail(bottle_id: str, history_id: str, user=Depends(require_user), settings: Settings = Depends(get_settings)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "UnauthorizeUploadFiled"},
        )

    bottle = bottle_table.query(
        IndexName='UserIdIndex',
        KeyConditionExpression=Key('user_id').eq(str(user_id)),
        FilterExpression=Attr('id').eq(str(bottle_id))
    ).get("Items", [])
    bottle = bottle[0] if bottle else None

    if not bottle:
        return JSONResponse(
            status_code=404,
            content={"message": "Bottle not found"},
        )

    scan = find_detect_record(bottle['device_id'], history_id, settings)
    
    if not scan:
        return JSONResponse(
            status_code=404,
            content={"message": "History not found"},
        )

    detect_record_state = scan.get('detect_record_state', {})
    env_record_state = scan.get('env_record_state', {})


    # if not detect_record_state:
    #     return JSONResponse(
    #         status_code=404,
    #         content={"message": "History not found"},
    #     )
    # if not env_record_state:
    #     return JSONResponse(
    #         status_code=404,
    #         content={"message": "History not found"},
    #     )

    bt_status = BottleStatus(detect_record_state['isAbnormal']) if detect_record_state else BottleStatus.UNKNOWN
    env_status = BottleStatus(env_record_state['isAbnormal']) if env_record_state else BottleStatus.UNKNOWN

    print("298", scan)

    res_bottle = BottleSingleInfo(
        detect_state_id=scan['detect_record_id'],
        name=bottle['name'],
        bottleState=BottleDetailInfo(
            bottle_status=str(bt_status),
            bottle_status_text=detect_record_state.get('type', '未知'),
            bottle_desc=detect_record_state.get('advice', "無")
        ),
        envState=EnvDetailInfo(
            env_status=str(env_status),
            env_status_text=env_record_state.get('type', '未知'),
            env_desc=env_record_state.get('advice', "無")
        ),
        displayState=DisplayState(
            temperature=scan.get('temperature', None),
            humidity=scan.get('humidity', None),
            time=int(scan.get('detectTime', 0) * 1000)
        ),
        oriimageUri=scan.get('orgPhotoUrl', None),
        AIimageUri=scan.get('aiPhotoUrl', None)
    )

    return JSONResponse(
        status_code=200,
        content=res_bottle.dict(),
    )

@bottle.post("/newBottle")
def create_new_bottle(form_data: CreateBottle, user=Depends(require_user)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )

    if not form_data.name or form_data.name.strip() == "":
        return JSONResponse(
            status_code=400,
            content={"message": "Bottle name is required"},
        )
    #check if bottle name is already in database for this user
    existing_bottle = bottle_table.query(
        IndexName="UserIdIndex",
        KeyConditionExpression=Key('user_id').eq(user_id),
        FilterExpression=Attr('name').eq(form_data.name)
    ).get("Items", [])

    if existing_bottle:
        return JSONResponse(
            status_code=400,
            content={"message": "Bottle name already exists"},
        )

    bottle_device_id = str(uuid4())

    bottle = Bottle(
        id=str(uuid4()),
        user_id=str(user_id),
        name=form_data.name,
        device_id=bottle_device_id,
    )

    bottle_device = DeviceSet(
        device_id=bottle_device_id,
        bottle_id=bottle.id,
        user_id=user_id,
        detectFreq=form_data.frequency,
        name=form_data.name,
    )

    bottle_table.put_item(Item=bottle.dict())
    deviceset_table.put_item(Item=bottle_device.dict())

    token_device_id = generate_device_token(bottle_device_id, bottle.id)

    return JSONResponse(
        status_code=201,
        content={
            "device_token": token_device_id
        },
    )


    
