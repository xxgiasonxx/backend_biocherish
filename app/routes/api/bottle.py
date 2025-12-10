from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlmodel import select

from app.core.db import db_dep
from app.lib.auth import require_user
from app.lib.device import generate_device_token
from app.models.bottle import (Bottle, BottleDevice, BottleHistory,
                               BottleLastInfo, BottleMainInfo, BottleScan,
                               CreateBottle)

bottle = APIRouter()


@bottle.get("/")
def get_bottle(db: db_dep, user=Depends(require_user)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )
    bottles = db.exec(
        select(Bottle)
        .where(Bottle.user_id == user_id)
    ).all()


    res_ar = []

    for bottle in bottles:
        res_ar.append(BottleMainInfo(
            id=str(bottle.id),
            name=bottle.name,
            status=bottle.curr_status,
            bottle_status=bottle.curr_bottle_status,
            image=bottle.curr_image_path,
            edited_at=str(bottle.edited_at),
            scanned_at=str(bottle.scanned_at),
        ).dict())

    return JSONResponse(
        status_code=200,
        content={"bottles": res_ar},
    )

@bottle.get("/{bottle_id}")
def get_bottle_info(bottle_id: UUID, db: db_dep):

    bottle = db.exec(
        select(Bottle).where(Bottle.id == bottle_id)
    ).first()

    if not bottle:
        return JSONResponse(
            status_code=404,
            content={"message": "Bottle not found"},
        )

    last_bottle = db.exec(
        select(BottleScan).where(BottleScan.bottle_id == bottle_id).order_by(BottleScan.scanned_at.desc())
    ).first()

    if not last_bottle:
        return JSONResponse(
            status_code=404,
            content={"message": "No scans found for this bottle"},
        )


    res_bottle = BottleLastInfo(
        id=last_bottle.id,
        name=bottle.name,
        image_path=last_bottle.image.image_path,
        ai_image_path=last_bottle.image.ai_image_path,
        status=last_bottle.bottle_status,
        description=last_bottle.description,
        suggestion=last_bottle.suggestion,
        temperature=last_bottle.temperature,
        humidity=last_bottle.humidity,
        scanned_at=str(last_bottle.scanned_at),
    )

    return JSONResponse(
        status_code=200,
        content={
            "bottle": res_bottle.dict()
        },
    )


@bottle.get("/{bottle_id}/history")
def get_bottle_history(bottle_id: int, start: int, end: int, db: db_dep, user=Depends(require_user)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )

    bottle = db.exec(
        select(Bottle).where(Bottle.id == bottle_id, Bottle.user_id == user_id)
    ).first()

    if not bottle:
        return JSONResponse(
            status_code=404,
            content={"message": "Bottle not found"},
        )

    scans = db.exec(
        select(BottleScan).where(BottleScan.bottle_id == bottle_id).order_by(BottleScan.scanned_at.desc()).offset(start).limit(end - start)
    ).all()

    res_ar = []

    for scan in scans:
        res_ar.append(BottleHistory(
            id=scan.id,
            status=scan.bottle_status,
            scanned_at=scan.scanned_at,
            details="/bottle/{}/history/{}".format(bottle_id, scan.id)
        ).dict())

    return JSONResponse(
        status_code=200,
        content={"history": res_ar},
    )

@bottle.get("/{bottle_id}/history/{history_id}")
def get_bottle_history_detail(bottle_id: int, history_id: int, db: db_dep, user=Depends(require_user)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "UnauthorizeUploadFiled"},
        )

    bottle = db.exec(
        select(Bottle).where(Bottle.id == bottle_id, Bottle.user_id == user_id)
    ).first()

    if not bottle:
        return JSONResponse(
            status_code=404,
            content={"message": "Bottle not found"},
        )

    scan = db.exec(
        select(BottleScan).where(BottleScan.id == history_id, BottleScan.bottle_id == bottle_id)
    ).first()

    if not scan:
        return JSONResponse(
            status_code=404,
            content={"message": "History not found"},
        )

    res_bottle = BottleLastInfo(
        id=scan.id,
        name=scan.name,
        image_path=scan.image.image_path if scan.image else None,
        ai_image_path=scan.image.ai_image_path if scan.image else None,
        state=scan.state,
        description=scan.description,
        suggestion=scan.suggestion,
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
def create_new_bottle(form_data: CreateBottle, db: db_dep, user=Depends(require_user)):
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
    existing_bottle = db.exec(
        select(Bottle).where(Bottle.user_id == user_id, Bottle.name == form_data.name)
    ).first()

    if existing_bottle:
        return JSONResponse(
            status_code=400,
            content={"message": "Bottle name already exists"},
        )

    bottle_device_id = uuid4()

    bottle = Bottle(
        user_id=user_id,
        name=form_data.name,
        device_id=bottle_device_id,
    )

    bottle_device = BottleDevice(
        bottle_id=bottle.id,
        frequency=form_data.frequency,  # default frequency 60 minutes
        device_id=bottle_device_id,
    )

    db.add(bottle)
    db.add(bottle_device)
    db.commit()
    db.refresh(bottle)

    token_device_id = generate_device_token(bottle_device_id, bottle.id)

    return JSONResponse(
        status_code=201,
        content={
            "device_token": token_device_id
        },
    )


    
