# from google.auth.transport import requests
# from google.oauth2 import id_token
import datetime
import logging

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from uuid import uuid4
from boto3.dynamodb.conditions import Key, Attr

from app.core.config import Settings, get_settings
from app.core.db import dynamodb
from app.exceptions import CredentialsException
from app.lib.auth import (generate_access_token, generate_refresh_token,
                          hash_password, verify_jwt_token, verify_password)
from app.models.user import (AccessToken, User, UserLogin, UserRegister,
                             VerfiyData)

logger = logging.getLogger(__name__)


TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

auth = APIRouter()

# db
user_table = dynamodb.Table("user")
access_table = dynamodb.Table("access_token")


@auth.get("/google/login")
def google_login(settings: Settings = Depends(get_settings)):
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    params_encoded = "&".join([f"{key}={value}" for key, value in params.items()])
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + params_encoded
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "url": url,
        }
    )
    # return RedirectResponse(url)

@auth.get("/google/callback")
def google_callback(code: str, settings: Settings = Depends(get_settings)):
    # 用 code 換 token
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    token_res = requests.post(TOKEN_URL, data=data)
    if token_res.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to obtain token from Google")

    tokens = token_res.json()
    access_token = tokens.get("access_token", "")

    # 取得使用者資訊
    userinfo_res = requests.get(USERINFO_URL, headers={
        "Authorization": f"Bearer {access_token}"
    })
    userinfo = userinfo_res.json()
    username = userinfo.get("name", userinfo["email"].split("@")[0])

    user = user_table.query(
        IndexName='GoogleIDIndex',
        KeyConditionExpression=Key('Google_ID').eq(userinfo["sub"]),
        FilterExpression=Attr('disabled').eq(False)
    ).get("Items", [])
    user = user[0] if user else None
    if not user:
        # 自動註冊
        user = User(
            id=str(uuid4()),
            Email=userinfo["email"],
            Username=username,
            Google_ID=userinfo["sub"],
            Password=None
        )
        user_table.put_item(Item=user.dict())
    id = user.get("id") if isinstance(user, dict) else user.id

    access_token = generate_access_token(userId=str(id))
    refresh_token = generate_refresh_token(userId=str(id))

    new_token_version = user_table.update_item(
        Key={"id": id},
        UpdateExpression="SET token_version = token_version + :inc",
        ExpressionAttributeValues={":inc": 1},
        ReturnValues="UPDATED_NEW"
    )["Attributes"]["token_version"]

    access_table.put_item(
        Item=AccessToken(
            id=str(uuid4()),
            user_id=id,
            refresh_token=refresh_token,
            token_version=new_token_version,
        ).dict()
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
    )

@auth.post("/refresh")
def verify_token(form_data: VerfiyData, settings: Settings = Depends(get_settings)):
    token = form_data.token
    if not token:
        raise CredentialsException(msg="Invalid refresh token")

    find_r = access_table.query(
        IndexName='refreshTokenIndex',
        KeyConditionExpression=Key('refresh_token').eq(token),
    ).get("Items", [])

    find_r = find_r[0] if find_r else None
    if not find_r:
        raise CredentialsException(msg="Refresh token not found")

    payload = verify_jwt_token(token)
    if payload.get("exp") < datetime.datetime.utcnow().timestamp():
        raise CredentialsException(msg="Token has expired")

    user_id = payload.get("user_id")

    user = user_table.get_item(Key={"id": user_id}).get("Item")

    if user['token_version'] != find_r['token_version']:
        raise CredentialsException(msg="Refresh token has been revoked")

    # generate new tokens
    refresh_token = generate_refresh_token(userId=user_id)
    access_token = generate_access_token(userId=user_id)

    new_token_version = user_table.update_item(
        Key={"id": user_id},
        UpdateExpression="SET token_version = token_version + :inc",
        ExpressionAttributeValues={":inc": 1},
        ReturnValues="UPDATED_NEW"
    )["Attributes"]["token_version"]

    access_table.put_item(
        Item=AccessToken(
            id=str(uuid4()),
            user_id=user_id,
            refresh_token=refresh_token,
            token_version=new_token_version,
        ).dict()
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "refresh_token": refresh_token,
            "access_token": access_token,
            "token_type": "bearer",
        },
    )


@auth.post("/login")
def login(form_data: UserLogin, settings: Settings = Depends(get_settings)):
    email = form_data.Email
    password = form_data.Password

    if not email or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password are required")

    user = user_table.query(
        IndexName='EmailIndex',
        KeyConditionExpression=Key('Email').eq(email),
        FilterExpression=Key('disabled').eq(False)
    ).get("Items", [])

    user = user[0] if user else None
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    if not verify_password(user['Password'], password):
        raise CredentialsException(msg="Invalid email or password")

    id = user['id']

    # generate Token
    access_token = generate_access_token(userId=str(id))
    refresh_token = generate_refresh_token(userId=str(id))
    new_token_version = user_table.update_item(
        Key={"id": id},
        UpdateExpression="SET token_version = token_version + :inc",
        ExpressionAttributeValues={":inc": 1},
        ReturnValues="UPDATED_NEW"
    )["Attributes"]["token_version"]

    access_table.put_item(
        Item=AccessToken(
            id=str(uuid4()),
            user_id=id,
            refresh_token=refresh_token,
            token_version=new_token_version,
        ).dict()
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
    )

@auth.post("/register")
def register(form_data: UserRegister, settings: Settings = Depends(get_settings)):
    email = form_data.Email
    username = form_data.Username
    password = form_data.Password
    repassword = form_data.RePassword
    if not email or not password or not username or not repassword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email, Username and Password are required",
        )

    if password != repassword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    # check if user exists
    existing_user = user_table.query(
        IndexName='EmailIndex',
        KeyConditionExpression=Key('Email').eq(email)
    ).get("Items", [])

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )

    # password hash
    hashed_password = hash_password(password)

    new_user = User(
        id=str(uuid4()),
        Email=email,
        Username=username,
        Password=hashed_password,
        disabled=False,
    )
    user_table.put_item(Item=new_user.dict())

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "email": new_user.Email,
            "username": new_user.Username,
        },
    )

@auth.post("/logout")
def logout(form_data: VerfiyData):
    payload = verify_jwt_token(form_data.token)
    if not payload:
        raise CredentialsException(msg="Invalid token")

    user_id = payload.get("user_id")

    user_table.update_item(
        Key={"id": user_id},
        UpdateExpression="SET token_version = token_version + :inc",
        ExpressionAttributeValues={":inc": 1},
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Logged out successfully"},
    )
