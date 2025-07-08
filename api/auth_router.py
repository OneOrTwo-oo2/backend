# backend/routers/router.py
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from db.connection import SessionLocal
from db.models import User
from config import GOOGLE_CLIENT_ID

router = APIRouter()

class GoogleLoginRequest(BaseModel):
    credential: str

from utils.jwt_handler import create_access_token, create_refresh_token, decode_refresh_token, get_current_user_from_cookie

@router.post("/auth/google-login")
def google_login(payload: GoogleLoginRequest):
    token = payload.credential
    if not token:
        raise HTTPException(status_code=400, detail="No token provided")

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            grequests.Request(),
            audience=GOOGLE_CLIENT_ID
        )
        email = idinfo["email"]

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.user_email == email).first()
            is_new = False

            if not user:
                user = User(user_email=email)
                db.add(user)
                db.commit()
                db.refresh(user)
                is_new = True

            # ✅ JWT 토큰 발급
            access_token = create_access_token({"user_id": user.user_id, "email": user.user_email})
            refresh_token = create_refresh_token({"user_id": user.user_id, "email": user.user_email})


        finally:
            db.close()

        # ✅ 쿠키 설정
        res = JSONResponse(content={"isNewUser": is_new})
        res.set_cookie(key="access_token", value=access_token,
                       httponly=True, secure=True, samesite="Strict", max_age=3600)
        res.set_cookie(key="refresh_token", value=refresh_token,
                       httponly=True, secure=True, samesite="Strict", max_age=7*24*60*60)
        return res

    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid Google token")


# 액세스 토큰 만료시 리프레쉬 토큰을 불러서 로그인 유지
@router.post("/auth/refresh-token")
def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = decode_refresh_token(refresh_token)
        user_id = payload.get("user_id")
        email = payload.get("email")

        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # 새로운 액세스 토큰 발급
        new_access_token = create_access_token({"user_id": user_id, "email": email})
        res = JSONResponse(content={"message": "Access token refreshed"})
        res.set_cookie(key="access_token", value=new_access_token,
                       httponly=True, secure=True, samesite="Strict", max_age=3600)
        return res

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# front protectedroute 받는 주소 때문에 설정!
@router.get("/auth/user")
def get_authenticated_user(user = Depends(get_current_user_from_cookie)):
    return {"user_id": user.user_id, "email": user.user_email}