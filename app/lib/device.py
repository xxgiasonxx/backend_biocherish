from app.core.config import get_settings
from hashlib import sha256
from datetime import datetime

settings = get_settings()


def generate_device_token() -> str:
    token = sha256(str(datetime.now().timestamp()).encode()).hexdigest()
    return token
