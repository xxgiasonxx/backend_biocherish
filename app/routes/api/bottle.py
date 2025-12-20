from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional

from app.core.db import dynamodb
from app.lib.auth import require_user
from app.lib.device import generate_device_token
# table
from app.models.bottle import Bottle, DeviceSet
# models
from app.models.bottle import BottleLastInfo, BottleMainInfo, BottleHistory, CreateBottle

bottle = APIRouter()

bottle_table = dynamodb.Table("bottle")
deviceset_table = dynamodb.Table("deviceset")
detect_record_table = dynamodb.Table("detect_record")
detect_record_state_table = dynamodb.Table("detect_record_state")


@bottle.get("/")
def get_bottle(user=Depends(require_user)):
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
        res_ar.append(
            BottleMainInfo(
                id=str(bottle['id']),
                name=bottle['name'],
                status=bottle['curr_status'],
                bottle_status=bottle['curr_bottle_status'],
                image=bottle['curr_image_path'],
                edited_at=bottle['edited_at'],
                scanned_at=bottle['scanned_at'],
            ).dict()
        )

    return JSONResponse(
        status_code=200,
        content={"bottles": res_ar},
    )

@bottle.get("/{bottle_id}")
def get_bottle_info(bottle_id: UUID):

    bottle = bottle_table.get_item(
        Key={"id": str(bottle_id)}
    ).get("Item", None)

    if not bottle:
        return JSONResponse(
            status_code=404,
            content={"message": "Bottle not found"},
        )

    last_bottle = detect_record_table.query(
        IndexName='BottleIdIndex',
        KeyConditionExpression=Key('bottle_id').eq(str(bottle_id)),
        ScanIndexForward=False,
        Limit=1
    ).get("Items", [])
    last_bottle = last_bottle[0] if last_bottle else None

    if not last_bottle:
        return JSONResponse(
            status_code=404,
            content={"message": "No scans found for this bottle"},
        )

    bottle_state = detect_record_state_table.get_item(
        Key={"detect_record_state_id": last_bottle.bottleStateID}
    ).get("Item", None)

    if not bottle_state:
        return JSONResponse(
            status_code=404,
            content={"message": "Bottle state not found"},
        )

    res_bottle = BottleLastInfo(
        id=last_bottle.detect_record_id,
        image_path=last_bottle.orgPhotoUrl,
        ai_image_path=last_bottle.aiPhotoUrl,
        status=bottle_state.type,
        suggestion=bottle_state.advice,
        temperature=last_bottle.temperature,
        humidity=last_bottle.humidity,
        scanned_at=str(last_bottle.time),
    )

    return JSONResponse(
        status_code=200,
        content={
            "bottle": res_bottle.dict()
        },
    )


@bottle.get("/{bottle_id}/history")
def get_bottle_history(bottle_id: UUID, limit: int, next_key: Optional[str] = None, user=Depends(require_user)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )

    if limit <= 0 or limit > 100:
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

    scans_param = {
        'IndexName': 'BottleIdIndex',
        'KeyConditionExpression': Key('bottle_id').eq(str(bottle_id)),
        'ScanIndexForward': False,
        'Limit': limit,
    }

    if next_key:
        scans_param['ExclusiveStartKey'] = {"detect_record_id": int(next_key)}

    scans = detect_record_table.query(**scans_param)

    next_key_res = scans.get("LastEvaluatedKey", None)
    scans = scans.get("Items", [])

    res_ar = []

    for scan in scans:
        res_ar.append(BottleHistory(
            id=scan.detect_record_id,
            status=scan.bottle_status,
            scanned_at=scan.scanned_at,
            details="/bottle/{}/history/{}".format(bottle_id, scan.detect_record_id)
        ).dict())

    return JSONResponse(
        status_code=200,
        content={
            "history": res_ar,
            "next_key": next_key_res
        },
    )

@bottle.get("/{bottle_id}/history/{history_id}")
def get_bottle_history_detail(bottle_id: UUID, history_id: int, user=Depends(require_user)):
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

    scan = detect_record_table.query(
        IndexName='BottleIdIndex',
        KeyConditionExpression=Key('bottle_id').eq(str(bottle_id)),
        FilterExpression=Key('detect_record_id').eq(history_id),
    ).get("Items", [])
    scan = scan[0] if scan else None
    
    if not scan:
        return JSONResponse(
            status_code=404,
            content={"message": "History not found"},
        )

    state = detect_record_state_table.get_item(
        Key={"detect_record_state_id": scan.bottleStateID}
    ).get("Item", None)

    if not scan:
        return JSONResponse(
            status_code=404,
            content={"message": "History not found"},
        )

    res_bottle = BottleLastInfo(
        id=scan.detect_record_id,
        image_path=scan.origPhotoUrl,
        ai_image_path=scan.aiPhotoUrl,
        state=state.type,
        suggestion=state.advice,
        temperature=scan.temperature,
        humidity=scan.humidity,
        scanned_at=scan.scanned_at,
    )

    return JSONResponse(
        status_code=200,
        content={
            "bottle_history": res_bottle.dict()
        },
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


    
