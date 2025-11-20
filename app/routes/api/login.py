import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from google.auth.transport import requests
from google.oauth2 import id_token

login_app = APIRouter()

GOOGLE_CLIENT_ID = "your-google-client-id.apps.googleusercontent.com"
JWT_SECRET_KEY = "your-jwt-secret-key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60o

@login_app.get("/google/login")
def google_login():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
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

@login_app.get("/google/callback")
def google_callback(code: str):
    # 用 code 換 token
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    token_res = requests.post(TOKEN_URL, data=data)
    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to obtain token from Google")

    tokens = token_res.json()
    access_token = tokens["access_token"]

    # 取得使用者資訊
    userinfo_res = requests.get(USERINFO_URL, headers={
        "Authorization": f"Bearer {access_token}"
    })
    userinfo = userinfo_res.json()

    # userinfo 內容包含：
    # email, name, picture, sub (user id)

    # TODO: 查詢或建立 user
    # user_id = ...

    # 產生 JWT（你自己的登入 token）
    payload = {
        "email": userinfo["email"],
        "name": userinfo.get("name"),
        "google_id": userinfo["sub"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
    }
    jwt_token = jwt.encode(payload, JWT_SECRET_KEY , algorithm=JWT_ALGORITHM)

    # 前端 RN 無法處理 redirect cookies，所以直接 redirect 回你的自定義 URL
    # 把 token 夾在 query 或 hash 避免被攔截
    frontend_url = f"myapp://auth?token={jwt_token}"
    return RedirectResponse(frontend_url)

@login_app.get("/verify-token")
def verify_token(token: str):

@login_app.get("/login")
def login(req: Request):
    try:
        email = req.query_params.get("email")
        password = req.query_params.get("password")
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")


        
        password = jwt.encode({"password": password}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        return 0
    except Exception as e:
        raise HTTPException(status_code=403, detail="")
    




@login_app.post("/auth/logout")
