# from google.auth.transport import requests
# from google.oauth2 import id_token
import datetime
import logging

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from jose import jwt
from sqlmodel import select, update

from app.core.config import Settings, get_settings
from app.core.db import db_dep
from app.exceptions import CredentialsException
from app.lib.auth import (generate_access_token, generate_refresh_token,
                          hash_password, verify_jwt_token, verify_password)
from app.models.user import (AccessToken, User, UserLogin, UserRegister,
                             VerfiyData)

logger = logging.getLogger(__name__)


auth = APIRouter()


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
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    )
    # return RedirectResponse(url)

@auth.get("/google/callback")
def google_callback(code: str, db: db_dep, settings: Settings = Depends(get_settings)):
    # 用 code 換 token
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    token_res = requests.post(TOKEN_URL, data=data)
    if token_res.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to obtain token from Google")

    tokens = token_res.json()
    access_token = tokens["access_token"]

    # 取得使用者資訊
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    userinfo_res = requests.get(USERINFO_URL, headers={
        "Authorization": f"Bearer {access_token}"
    })
    userinfo = userinfo_res.json()
    username = userinfo.get("name", userinfo["email"].split("@")[0])

    user = db.exec(select(User).where(User.Google_ID == userinfo["sub"])).first()
    if not user:
        # 自動註冊
        user = User(
            Email=userinfo["email"],
            Username=username,
            Google_ID=userinfo["sub"],
            Password=None
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = generate_access_token(userId=str(user.id))
    refresh_token = generate_refresh_token(userId=str(user.id))

    db.add(AccessToken(
        user_id=user.id,
        refresh_token=refresh_token,
        access_token=access_token,
    )) 
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
    )

@auth.post("/refresh")
def verify_token(form_data: VerfiyData, db: db_dep, settings: Settings = Depends(get_settings)):
    token = form_data.token
    if not token:
        raise CredentialsException(msg="Invalid refresh token")

    find_r = db.exec(
        select(AccessToken).where(AccessToken.refresh_token == token)
    ).first()

    if not find_r:
        raise CredentialsException(msg="Refresh token not found")

    payload = verify_jwt_token(token)
    if payload.get("exp") < datetime.datetime.utcnow().timestamp():
        raise CredentialsException(msg="Token has expired")

    user_id = payload.get("user_id")
    refresh_token = generate_refresh_token(userId=user_id)
    access_token = generate_access_token(userId=user_id)

    db.exec(
        update(AccessToken)
        .where(AccessToken.user_id == user_id)
        .values(
            refresh_token=refresh_token,
            access_token=access_token,
            refresh_at=datetime.datetime.now(datetime.timezone.utc),
        )
    )
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "refresh_token": refresh_token,
            "access_token": access_token,
            "token_type": "bearer",
        },
    )


@auth.post("/login")
def login(form_data: UserLogin, db: db_dep, settings: Settings = Depends(get_settings)):
    email = form_data.Email
    password = form_data.Password

    if not email or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password are required")

    user = db.exec(select(User).where(User.Email == email)).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    if not verify_password(user.Password, password):
        raise CredentialsException(msg="Invalid email or password")

    # generate Token
    access_token = generate_access_token(userId=str(user.id))
    refresh_token = generate_refresh_token(userId=str(user.id))

    db.add(AccessToken(
        user_id=user.id,
        refresh_token=refresh_token,
        access_token=access_token,
    ))
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
    )

@auth.post("/register")
def register(form_data: UserRegister, db: db_dep, settings: Settings = Depends(get_settings)):
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
    existing_user = db.exec(select(User).where(User.Email == email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )

    # password hash
    hashed_password = hash_password(password)

    new_user = User(Email=email, Username=username, Password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "email": new_user.Email,
            "username": new_user.Username,
        },
    )

@auth.post("/logout")
def logout(form_data: VerfiyData, db: db_dep):
    payload = verify_jwt_token(form_data.token)
    if not payload:
        raise CredentialsException(msg="Invalid token")

    user_id = payload.get("user_id")

    db.exec(
        select(AccessToken).where(AccessToken.user_id == user_id).delete()
    )
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Logged out successfully"},
    )
