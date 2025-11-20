from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from logger import logger

logger = logging.getLogger(__name__)

async def add_process_time_header(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except:
        logger.exception("An error occurred while processing the request.")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )


