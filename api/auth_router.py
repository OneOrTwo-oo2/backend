# backend/routers/router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from db.connection import SessionLocal
from db.models import User
import os
from dotenv import load_dotenv
from config import GOOGLE_CLIENT_ID

router = APIRouter()

class GoogleLoginRequest(BaseModel):
    credential: str

@router.post("/auth/google-login")
def google_login(payload: GoogleLoginRequest):
    token = payload.credential
    if not token:
        raise HTTPException(status_code=400, detail="No token provided")

    try:
        # ✅ .env에서 가져온 CLIENT_ID로 검증
        idinfo = id_token.verify_oauth2_token(
            token,
            grequests.Request(),
            audience = GOOGLE_CLIENT_ID
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
        finally:
            db.close()  # ✅ 연결 해제는 finally로 안전하게

        return {
            "token": "임의의_토큰",  # 나중에 JWT로 변경 가능
            "isNewUser": is_new,
            "user_email": email
        }

    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid Google token")
