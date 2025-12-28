import logging

from fastapi import FastAPI

from app.exceptions import exceptions
from app.middlewares.response import middlewares
from app.routes.router import router
from starlette.middleware.cors import CORSMiddleware
from app.core.db import on_startup

# initlize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# initlize app
bio_app = FastAPI(title="Bioinformatics API", version="1.0.0")


# middleware
for mware in middlewares:
    bio_app.middleware("http")(mware)

for cls, fn in exceptions:
    bio_app.exception_handler(cls)(fn)

bio_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*", 
        "http://localhost:8081"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# include routers
prefix = "/api/v1"
bio_app.include_router(router, prefix=prefix)


bio_app.add_event_handler("startup", on_startup)


# Health check endpoint
# @bio_app.get("/health", tags=["Health"])
# async def health_check():
#     return {"status": "ok"}
