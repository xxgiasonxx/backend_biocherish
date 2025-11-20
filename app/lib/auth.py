import datetime

import jwt
from fastapi import APIRouter, HTTPException, Request

from app.core.config import Settings, get_settings
from app.exceptions.UserException import credentialsException

login_app = APIRouter()

JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_EXPIRATION_MINUTES = settings.JWT_EXPIRATION_MINUTES

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise UnAuthorizedException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise UnAuthorizedException(status_code=401, detail="Invalid token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = verify_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentialsException()
    except JWTError:
        raise credentialsException()

    # need to add database call to get user
    if user is None:
        raise credentialsException()
    return user
