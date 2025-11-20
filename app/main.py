from logging import logging

from fastapi import FastAPI

from app.exceptions.main import exceptions
from app.middleware.response import add_process_time_header

# initlize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# initlize app
bio_app = FastAPI(title="Bioinformatics API", version="1.0.0")

# middleware
bio_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
bio_app.middleware("http")(add_process_time_header)

for cls, fn in exceptions:
    bio_app.exception_handler(cls), fn)

# include routers
prefix = "/api/v1"
bio_app.include_router(router, prefix=prefix)

# Health check endpoint
@bio_app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
