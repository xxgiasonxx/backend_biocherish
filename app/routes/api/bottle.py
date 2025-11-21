from fastapi import APIRouter, Header, Depends
from fastapi.responses import JSONResponse


bottle = APIRouter()


@bottle.get("/")
def get_bottle():
    return JSONResponse(
        status_code=200,
        content={"message": "This is a protected bottle endpoint."},
    )