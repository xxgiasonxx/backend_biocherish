from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Password


class TokenRequest(BaseModel):
    id_token: str

class UserBase(BaseModel):
    id: Optional[UUID] = None
    Email: EmailStr
    Username: str
    Password: str

