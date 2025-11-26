from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlmodel import select

from app.core.db import db_dep
from app.lib.auth import require_user
from uuid import uuid4
from app.models.bottle import Bottle, BottleScan, BottleHistory, BottleMainInfo, BottleLastInfo, CreateBottle, BottleDevice
from app.lib.device import generate_device_token

bottle = APIRouter()


@bottle.get("/")
def get_bottle(db: db_dep, user=Depends(require_user)):
    user_id = user.get("user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
        )
    bottles = db.exec(select(Bottle).where(Bottle.user_id == user_id)).all()

    res_ar = []

    for bottle in bottles:
        res_ar.append(BottleMainInfo(
            id=bottle.id,
            name=bottle.name,
            state=bottle.state,
            created_at=bottle.created_at,
            scanned_at=bottle.scanned_at,
        ).dict())

    return JSONResponse(
        status_code=200,
        content={"bottles": res_ar},
    )

@bottle.get("/{bottle_id}")
def get_bottle_info(bottle_id: int, db: db_dep):
    last_bottle = db.exec(
        select(BottleScan).where(BottleScan.bottle_id == bottle_id).order_by(BottleScan.scanned_at.desc())
    ).first()

    if not last_bottle:
        return JSONResponse(
            status_code=404,
            content={"message": "Bottle not found"},
        )

    res_bottle = BottleLastInfo(
        id=last_bottle.id,
        name=last_bottle.name,
        image_path=last_bottle.image.image_path if last_bottle.image else None,
        ai_image_path=last_bottle.image.ai_image_path if last_bottle.image else None,
        state=last_bottle.state,
        description=last_bottle.description,
        suggestion=last_bottle.suggestion,
        temperature=last_bottle.temperature,
        humidity=last_bottle.humidity,
        scanned_at=last_bottle.scanned_at,
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
            state=scan.state,
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

    bottle_device_id = uuid4()

    bottle = Bottle(
        user_id=user_id,
        name=form_data.name,
        device_id=bottle_device_id
    )

    bottle_device = BottleDevice(
        device_id=bottle_device_id,
        bottle_id=bottle.id,
        frequency=form_data.frequency,  # default frequency 60 minutes
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


    