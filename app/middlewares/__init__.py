import logging
from typing import Any, Dict, Union

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.main import app

logger = logging.getLogger(__name__)

class NewHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: Any = None, headers: Union[Dict[str, Any], None] = None, msg: str = None) -> None:
        super().__init__(status_code, detail, headers)
        if msg:
            self.msg = msg
        else:
            self.msg = detail

@app.middleware("http")
async def get_request(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:     # 非預期的錯誤
        logger.error(f"Unhandled error: {e}", exc_info=True) # 紀錄非預期的錯誤的 log
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

@app.exception_handler(NewHTTPException)
async def unicorn_exception_handler(request: Request, exc: NewHTTPException):
    logger.error(f"Unhandled error: {exc.msg}", exc_info=True) # 紀錄非預期的錯誤的 log
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
