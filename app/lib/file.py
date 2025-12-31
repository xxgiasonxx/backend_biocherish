import os
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from app.core.config import Settings
from datetime import datetime
import requests

def upload_file_check(file: UploadFile, settings: Settings) -> JSONResponse | None:
    if not os.path.exists(settings.UPLOAD_DIRECTORY):
        os.makedirs(settings.UPLOAD_DIRECTORY)

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
    return None

def download_file_with_url(uri: str) -> bytes | JSONResponse:
    try:
        import requests
        response = requests.get(uri)
        if response.status_code != 200:
            return JSONResponse(
                status_code=500,
                content={"message": "Failed to download file from URL"},
            )
        return response.content
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Internal Server Error: {str(e)}"},
        )

def download_file_requests(url, save_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Check if the download was successful

    with open(save_path, 'wb') as f:
        f.write(response.content)
    print(f"File successfully downloaded and saved to {save_path}")


    

def upload_file(user_id: str, file: UploadFile, prefix: str, settings: Settings) -> str | JSONResponse:
    if not os.path.exists(settings.UPLOAD_DIRECTORY):
        os.makedirs(settings.UPLOAD_DIRECTORY)

    user_folder = os.path.join(settings.UPLOAD_DIRECTORY, str(user_id))
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    folder_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    scan_folder = os.path.join(user_folder, folder_name)
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
        file_path = os.path.join(scan_folder, f"{prefix}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(file.file.read())
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Internal Server Error: Failed to save image file. {str(e)}"},
        )
    return file_path
        
