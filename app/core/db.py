from sqlmodel import Session, create_engine, select, SQLModel
from fastapi import Depends
from app.core.config import get_settings
from typing import Annotated

# get settings
settings = get_settings()

# create engine
engine = create_engine(settings.DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session

db_dep = Annotated[Session, Depends(get_session)]

async def on_startup():
    SQLModel.metadata.create_all(engine)