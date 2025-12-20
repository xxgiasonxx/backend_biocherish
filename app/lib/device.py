from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import Optional, List, Literal
from jose import jwt
from app.core.config import get_settings

settings = get_settings()


def generate_device_token(device_id: UUID, bottle_id: UUID) -> str:
    # expire = datetime.utcnow() + timedelta(days=365)
    to_encode = {
        "device_id": str(device_id),
        "bottle_id": str(bottle_id),  # for simplicity, bottle_id is same as device_id here
    }
    encoded_jwt = jwt.encode(to_encode, settings.DEVICE_JWT_SECRET_KEY, algorithm=settings.DEVICE_JWT_ALGORITHM)
    return encoded_jwt

def verify_device_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.DEVICE_JWT_SECRET_KEY,
            algorithms=[settings.DEVICE_JWT_ALGORITHM],
        )
        return payload
    except jwt.JWTError:
        return None