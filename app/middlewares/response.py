from fastapi import Request
from fastapi.responses import JSONResponse
import datetime
import json
import logging

logger = logging.getLogger(__name__)

async def add_process_time_header(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.exception("An error occurred while processing the request.")
        logger.error(f"Internal Server Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

async def add_timestamp_to_json_response(request: Request, call_next):
    response = await call_next(request)
    
    # 只處理 JSONResponse
    if "application/json" in response.headers.get("content-type", ""):
        # 先取得原本資料
        body = [section async for section in response.body_iterator]
        raw_data = b"".join(body).decode()
        try:
            data = json.loads(raw_data)
        except Exception:
            data = raw_data  # 如果解析失敗就不改
        # 加 timestamp
        if isinstance(data, dict):
            data["timestamp"] = int(datetime.datetime.utcnow().timestamp())
        # 回傳新 response
        response = JSONResponse(content=data, status_code=response.status_code)
    
    return response

middlewares = [
    add_process_time_header,
    add_timestamp_to_json_response,
]
