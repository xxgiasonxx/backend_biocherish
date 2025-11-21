from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field
from pydantic import EmailStr
from datetime import datetime


class TokenRequest(SQLModel):
    id_token: str
    
class AccessToken(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True)
    refresh_token: str = Field(nullable=False)
    access_token: str = Field(nullable=False)
    refresh_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # revoked: bool = Field(default=False)

class UserBase(SQLModel):
    id: UUID = Field(default_factory=lambda: uuid4(), unique=True, primary_key=True)
    Email: EmailStr = Field(unique=True, index=True, max_length=255)
    Username: str = Field(index=True, nullable=False)
    Password: Optional[str] = Field(default=None, nullable=True)
    Google_ID: Optional[str] = Field(default=None, index=True, nullable=True)
    
class User(UserBase, table=True):
    disabled: bool = Field(default=False, nullable=False)


class UserLogin(SQLModel):
    Email: EmailStr
    Password: str

class UserRegister(SQLModel):
    Email: EmailStr
    Username: str
    Password: str
    RePassword: str

class VerfiyData(SQLModel):
    token: str
    

