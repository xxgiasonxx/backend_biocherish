from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import DateTime, func
from sqlmodel import Column, Field, Relationship, SQLModel


# Enum
class BottleStatus(int, Enum):
    UNKNOWN = 0
    GOOD = 1
    CAREFUL = 2
    WARNING = 3

class Status(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# database models
class Bottle(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False, index=True)
    name: str = Field(index=True, nullable=False)
    # fequency: int = Field(default=0, nullable=False) # in minutes

    curr_image_path: Optional[str] = Field(default=None, nullable=True)
    curr_bottle_status: BottleStatus = Field(default=BottleStatus.UNKNOWN, nullable=False)
    curr_status: Status = Field(default=Status.PENDING, nullable=False)

    device_id: UUID = Field(foreign_key="bottledevice.device_id", nullable=False)
    device: "BottleDevice" = Relationship(
        back_populates="bottle",
        sa_relationship_kwargs={"uselist": False}
    )

    history: List["BottleScan"] = Relationship(back_populates="bottle")

    scanned_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )
    edited_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )



class BottleScan(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    bottle_id: UUID = Field(foreign_key="bottle.id", nullable=False, index=True)
    status: Status = Field(default=Status.PENDING, nullable=False)
    bottle_status: BottleStatus = Field(default=BottleStatus.UNKNOWN, nullable=False)
    description: str = Field(default="", nullable=True)
    suggestion: str = Field(default="", nullable=True)
    temperature: float = Field(default=0.0, nullable=True)
    humidity: float = Field(default=0.0, nullable=True)
    image_id: int = Field(foreign_key="bottleimage.id", nullable=False)
    bottle: Bottle = Relationship(back_populates="history")
    image: "BottleImage" = Relationship(back_populates="bottle_scans") # image_path: Optional[str] = Field(default=None, nullable=True) ai_image_path: Optional[str] = Field(default=None, nullable=True)

    scanned_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )

class BottleImage(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    image_path: str = Field(nullable=True)
    ai_image_path: str = Field(nullable=True)
    bottle_scans: BottleScan = Relationship(back_populates="image")
    ai_gen_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )


class BottleDevice(SQLModel, table=True):
    device_id: UUID = Field(primary_key=True, default_factory=uuid4)
    bottle: "Bottle" = Relationship(
        back_populates="device",
        sa_relationship_kwargs={"uselist": False}
    )
    frequency: int = Field(default=60, nullable=False)  # in minutes
    is_connected: bool = Field(default=False, nullable=False)
    is_error: bool = Field(default=False, nullable=False)
    error_message: Optional[str] = Field(default=None, nullable=True)
    edited_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )


# interface models
class BottleMainInfo(SQLModel):
    id: str
    name: str
    status: Status
    bottle_status: BottleStatus
    image: Optional[str]
    edited_at: str
    scanned_at: str

class BottleLastInfo(SQLModel):
    id: str
    name: str
    image_path: Optional[str]
    ai_image_path: Optional[str]
    status: Status
    description: str
    suggestion: str
    temperature: float
    humidity: float
    scanned_at: str

class BottleHistory(SQLModel):
    id: int
    status: Status
    detail: str
    scanned_at: str

class CreateBottle(SQLModel):
    name: str
    frequency: int  # in minutes

class UpdateBottle(SQLModel):
    token: str
    image: UploadFile
    temperature: Optional[float]
    humidity: Optional[float]
