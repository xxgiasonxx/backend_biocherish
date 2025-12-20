import boto3
from fastapi import Depends
from app.core.config import get_settings
from typing import Annotated
from app.core.createTable import init_tables
import logging

logger = logging.getLogger(__name__)

# get settings
settings = get_settings()

dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url=settings.DATABASE_URL,
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)


async def on_startup():
    if not dynamodb:
        logger.error("Could not connect to DynamoDB")
        raise Exception("Could not connect to DynamoDB")
    init_tables(dynamodb)