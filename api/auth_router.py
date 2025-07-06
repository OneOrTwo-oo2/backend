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

from utils.jwt_handler import create_access_token

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

        finally:
            db.close()

        return {
            "token": access_token,
            "isNewUser": is_new,
            "user_email": email
        }

    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid Google token")
