from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import select

from app.core.config import Settings, get_settings
from app.core.db import db_dep
from app.lib.device import verify_device_token
from app.models.bottle import BottleImage, BottleScan, UpdateBottle

device = APIRouter()




@device.post("/update")
def update_bottle_info(form_data: UpdateBottle, bottle_id: int, db: db_dep, settings: Settings = Depends(get_settings)):
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
 
    file = form_data.image
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

    bottleimage = BottleImage(
        image_path=file_path
    )

    bottlescan = BottleScan(
        bottle_id=bottle_id,
        temperature=form_data.temperature,
        humidity=form_data.humidity,
        image=bottleimage,
    )

    db.add(bottlescan)
    db.commit()
    db.refresh(bottlescan)
    db.refresh(bottleimage)

    return JSONResponse(
        status_code=200,
        content={"message": "Bottle scan data updated successfully"},
    )

