from datetime import datetime
from typing import List, Optional, Literal
from uuid import UUID, uuid4
from fastapi import UploadFile

from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import TIMESTAMP, text

# database models
State = Literal[0, 1, 2, 3]  # 0: unknown, 1: good, 2: warning, 3: critical

class Bottle(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False, index=True)
    name: str = Field(index=True, nullable=False)
    # fequency: int = Field(default=0, nullable=False) # in minutes

    curr_image_id: Optional[int] = Field(default=None, foreign_key="bottleimage.id", nullable=True)
    curr_state: int = Field(default=0, nullable=False)

    device_id: UUID = Field(foreign_key="bottledevice.device_id", nullable=False)
    history: List["BottleScan"] = Relationship(back_populates="bottle")

    scanned_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ))
    edited_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ))
    created_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ))



class BottleScan(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    bottle_id: UUID = Field(foreign_key="bottle.id", nullable=False, index=True)
    state: int = Field(default=0, nullable=False)
    description: str = Field(default="", nullable=True)
    suggestion: str = Field(default="", nullable=True)
    temperature: float = Field(default=0.0, nullable=True)
    humidity: float = Field(default=0.0, nullable=True)
    image_id: int = Field(default=None, foreign_key="bottleimage.id", nullable=True)
    bottle: Bottle = Relationship(back_populates="history")
    image: "BottleImage" = Relationship(back_populates="bottle_scans")
    # image_path: Optional[str] = Field(default=None, nullable=True)
    # ai_image_path: Optional[str] = Field(default=None, nullable=True)

    scanned_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ))
    created_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ))

class BottleImage(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    image_path: str = Field(nullable=False)
    ai_image_path: str = Field(nullable=True)
    bottle_scans: BottleScan = Relationship(back_populates="image")
    ai_gen_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ))
    created_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ))


class BottleDevice(SQLModel, table=True):
    device_id: UUID = Field(primary_key=True, default_factory=uuid4)
    bottle_id: UUID = Field(foreign_key="bottle.id", nullable=False)
    frequency: int = Field(default=60, nullable=False)  # in minutes
    is_connected: bool = Field(default=False, nullable=False)
    is_error: bool = Field(default=False, nullable=False)
    error_message: Optional[str] = Field(default=None, nullable=True)
    edited_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ))
    created_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ))

# interface models
class BottleMainInfo(SQLModel):
    id: UUID
    name: str
    state: State
    edited_at: datetime
    scanned_at: datetime

class BottleLastInfo(SQLModel):
    id: UUID
    name: str
    image_path: Optional[str]
    ai_image_path: Optional[str]
    state: State
    description: str
    suggestion: str
    temperature: float
    humidity: float
    scanned_at: datetime

class BottleHistory(SQLModel):
    id: int
    state: State
    scanned_at: datetime
    detail: str

class CreateBottle(SQLModel):
    name: str
    frequency: int  # in minutes
    
class UpdateBottle(SQLModel):
    token: str
    image: UploadFile
    temperature: Optional[float]
    humidity: Optional[float]