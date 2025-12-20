from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class TokenRequest(BaseModel):
    id_token: str
    
class AccessToken(BaseModel):
    id: str
    user_id: str
    refresh_token: str
    token_version: int = 0
    created_at: int = int(datetime.now().timestamp())

class UserBase(BaseModel):
    id: str
    Email: EmailStr = Field(max_length=255)
    Username: str
    Password: Optional[str] = None
    Google_ID: str = "None"

class User(UserBase):
    disabled: bool = False
    token_version: int = 0
    created_at: int = int(datetime.now().timestamp())

class UserLogin(BaseModel):
    Email: EmailStr
    Password: str

class UserRegister(BaseModel):
    Email: EmailStr
    Username: str
    Password: str
    RePassword: str

class VerfiyData(BaseModel):
    token: str
    

