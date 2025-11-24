from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from app.core.db import db_dep
from app.lib.auth import require_user
from app.models.bottle import BottleHistory, BottleMainInfo

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

