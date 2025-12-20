from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi import UploadFile
from pydantic import BaseModel, Field, model_validator, ConfigDict


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
class Bottle(BaseModel):
    id: str
    user_id: str
    name: str
    # name: str = Field(index=True, nullable=False)
    # fequency: int = Field(default=0, nullable=False) # in minutes

    curr_image_path: Optional[str] = None
    curr_bottle_status: BottleStatus = BottleStatus.UNKNOWN
    curr_status: Status = Status.PENDING

    device_id: str

    scanned_at: int = int(datetime.now().timestamp())
    edited_at: int = int(datetime.now().timestamp())
    updated_at: int = int(datetime.now().timestamp())
    created_at: int = int(datetime.now().timestamp())

    model_config = ConfigDict(
        validate_assignment=True,
    )

    @model_validator(mode="after")
    @classmethod
    def update_updated_at(cls, obj: "Bottle") -> "Bottle":
        """Update updated_at field."""
        # must disable validation to avoid infinite loop
        obj.model_config["validate_assignment"] = False

        # update updated_at field
        obj.updated_at = int(datetime.now().timestamp())

        # enable validation again
        obj.model_config["validate_assignment"] = True
        return obj

class DeviceSet(BaseModel):
    device_id: str
    bottle_id: str
    user_id: str
    detectFreq: int = 30  # in minutes
    name: str
    isError: bool = False
    isConnected: bool = False
    endpoint: Optional[str] = None
    certificate: Optional[str] = None
    privateKey: Optional[str] = None

    lastEditTime: int = int(datetime.now().timestamp())
    createTime: int = int(datetime.now().timestamp())

class DetectRecord(BaseModel):
    detect_record_id: str
    bottleStateID: str
    # envStateID: int 
    device_id: str = Field(foreign_key="deviceset.device_id", nullable=False)
    bottle_id: str
    isFromDevice: bool = True
    orgPhotoUrl: Optional[str] = None
    aiPhotoUrl: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    isError: bool = False
    time: int = int(datetime.now().timestamp())

class DetectRecordState(BaseModel):
    detect_record_state_id: str
    isAbnormal: bool = False
    type: int = 0
    advice: Optional[str] = None
    bottleOrEnv: Optional[int] = None
    createTime: int = int(datetime.now().timestamp())



# interface models
class BottleMainInfo(BaseModel):
    id: str
    name: str
    status: Status
    bottle_status: BottleStatus
    image: Optional[str]
    edited_at: int
    scanned_at: int

class BottleLastInfo(BaseModel):
    id: str
    name: str
    image_path: Optional[str]
    ai_image_path: Optional[str]
    status: Status
    description: str
    suggestion: str
    temperature: float
    humidity: float
    scanned_at: int

class BottleHistory(BaseModel):
    id: int
    status: Status
    detail: str
    scanned_at: int

class CreateBottle(BaseModel):
    name: str
    frequency: int  # in minutes

class UpdateBottle(BaseModel):
    token: str
    image: UploadFile
    temperature: Optional[float]
    humidity: Optional[float]
