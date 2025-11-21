from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pydantic import (
    Field
)
from . import config

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', 
        extra='ignore'
    )
    GOOGLE_CLIENT_ID: str = Field(validation_alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(validation_alias="GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = Field(validation_alias="GOOGLE_REDIRECT_URI")
    JWT_SECRET_KEY: str = Field(validation_alias="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(validation_alias="JWT_ALGORITHM", default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")  # 1 week
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, validation_alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")  # 7 days
    DATABASE_URL: str = Field(validation_alias="DATABASE_URL")


@lru_cache
def get_settings():
    return config.Settings()