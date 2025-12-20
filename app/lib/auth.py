import datetime
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import get_settings

oauth2_scheme = HTTPBearer()
settings = get_settings()


def generate_access_token(userId: str):
    return jwt.encode(
        {
            "user_id": userId,
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    
def generate_refresh_token(userId: str):
    return jwt.encode(
        {
            "user_id": userId,
            "jti": str(uuid4()),
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

def verify_jwt_token(token: str):
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return None

def verify_password(hashed_password: str, plain_password: str) -> bool:
    from argon2 import PasswordHasher
    ph = PasswordHasher()
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except:
        return False

def hash_password(plain_password: str) -> str:
    from argon2 import PasswordHasher
    ph = PasswordHasher()
    return ph.hash(plain_password)


def require_user(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    try:
        payload = verify_jwt_token(token.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("jti", None) is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload
