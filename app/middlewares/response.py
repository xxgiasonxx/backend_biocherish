from fastapi import Request
from fastapi.responses import JSONResponse
import datetime
import json
import logging

logger = logging.getLogger(__name__)

async def add_process_time_header(request: Request, call_next):
    print(f">>> Request: {request.method} {request.url.path}") # 加這行
    try:
        response = await call_next(request)
        # print(f"DEBUG: Request headers: {request.headers}")
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
    
    if "application/json" in response.headers.get("content-type", ""):
        body = [section async for section in response.body_iterator]
        raw_data = b"".join(body).decode()
        
        try:
            data = json.loads(raw_data)
        except Exception:
            data = raw_data 

        if isinstance(data, dict):
            # 轉換為 timestamp
            data["timestamp"] = int(datetime.datetime.utcnow().timestamp())
            
            # 1. 備份舊的 Headers (包含 CORS 資料)
            old_headers = dict(response.headers)
            
            # 2. 建立新 Response
            response = JSONResponse(content=data, status_code=response.status_code)
            
            # 3. 重新把 Headers 塞回去 (排除 content-length，因為長度變了)
            old_headers.pop("content-length", None)
            response.init_headers(old_headers)
    
    return response

middlewares = [
    add_process_time_header,
    add_timestamp_to_json_response,
]
