# backend/routers/router.py
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from db.connection import SessionLocal
from db.models import User
from config import GOOGLE_CLIENT_ID
import bcrypt
import re

router = APIRouter()

class GoogleLoginRequest(BaseModel):
    credential: str

class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str

class EmailSignupRequest(BaseModel):
    email: EmailStr
    password: str

class EmailCheckRequest(BaseModel):
    email: EmailStr

from utils.jwt_handler import create_access_token, create_refresh_token, decode_refresh_token, get_current_user_from_cookie

def hash_password(password: str) -> str:
    """비밀번호를 해싱합니다."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """비밀번호를 검증합니다."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def validate_password(password: str) -> bool:
    """비밀번호 유효성을 검사합니다."""
    # 최소 6자 이상
    if len(password) < 6:
        return False
    return True

def validate_email(email: str) -> bool:
    """이메일 형식을 검증합니다."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@router.post("/auth/check-email")
def check_email_duplicate(payload: EmailCheckRequest):
    """이메일 중복확인"""
    email = payload.email
    
    # 이메일 형식 검증
    if not validate_email(email):
        raise HTTPException(status_code=400, detail="올바른 이메일 형식을 입력해주세요.")
    
    db = SessionLocal()
    try:
        # 이메일 중복 확인
        existing_user = db.query(User).filter(User.user_email == email).first()
        
        if existing_user:
            return {"available": False, "message": "이미 가입된 이메일입니다."}
        else:
            return {"available": True, "message": "사용 가능한 이메일입니다."}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail="중복확인 중 오류가 발생했습니다.")
    finally:
        db.close()

@router.post("/auth/signup")
def email_signup(payload: EmailSignupRequest):
    """이메일 회원가입"""
    email = payload.email
    password = payload.password
    
    # 이메일 형식 검증
    if not validate_email(email):
        raise HTTPException(status_code=400, detail="올바른 이메일 형식을 입력해주세요.")
    
    # 비밀번호 유효성 검사
    if not validate_password(password):
        raise HTTPException(status_code=400, detail="비밀번호는 6자 이상이어야 합니다.")
    
    db = SessionLocal()
    try:
        # 이메일 중복 확인
        existing_user = db.query(User).filter(User.user_email == email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")
        
        # 비밀번호 해싱
        hashed_password = hash_password(password)
        
        # 새 사용자 생성
        new_user = User(
            user_email=email,
            password=hashed_password,
            login_type="email"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # JWT 토큰 발급
        access_token = create_access_token({"user_id": new_user.user_id, "email": new_user.user_email})
        refresh_token = create_refresh_token({"user_id": new_user.user_id, "email": new_user.user_email})
        
        # 쿠키 설정
        res = JSONResponse(content={"message": "회원가입이 완료되었습니다.", "isNewUser": True})
        res.set_cookie(key="access_token", value=access_token,
                       httponly=True, secure=True, samesite="None", max_age=3600)
        res.set_cookie(key="refresh_token", value=refresh_token,
                       httponly=True, secure=True, samesite="None", max_age=7*24*60*60)
        return res
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="회원가입 중 오류가 발생했습니다.")
    finally:
        db.close()

@router.post("/auth/login")
def email_login(payload: EmailLoginRequest):
    """이메일 로그인"""
    email = payload.email
    password = payload.password
    
    db = SessionLocal()
    try:
        # 사용자 찾기
        user = db.query(User).filter(User.user_email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
        
        # 비밀번호 검증
        if not user.password or not verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
        
        # JWT 토큰 발급
        access_token = create_access_token({"user_id": user.user_id, "email": user.user_email})
        refresh_token = create_refresh_token({"user_id": user.user_id, "email": user.user_email})
        
        # 쿠키 설정
        res = JSONResponse(content={"message": "로그인이 완료되었습니다.", "isNewUser": False})
        res.set_cookie(key="access_token", value=access_token,
                       httponly=True, secure=True, samesite="None", max_age=3600)
        res.set_cookie(key="refresh_token", value=refresh_token,
                       httponly=True, secure=True, samesite="None", max_age=7*24*60*60)
        return res
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="로그인 중 오류가 발생했습니다.")
    finally:
        db.close()

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
                user = User(user_email=email, login_type="google")
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
                       httponly=True, secure=True, samesite="None", max_age=3600)
        res.set_cookie(key="refresh_token", value=refresh_token,
                       httponly=True, secure=True, samesite="None", max_age=7*24*60*60)
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
                       httponly=True, secure=True, samesite="None", max_age=3600)
        return res

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# front protectedroute 받는 주소 때문에 설정!
@router.get("/auth/user")
def get_authenticated_user(user = Depends(get_current_user_from_cookie)):
    return {"user_id": user.user_id, "email": user.user_email}


# 로그인 페이지 진입시 쿠키 리셋
@router.post("/auth/clear-cookie")
def clear_cookie():
    res = JSONResponse(content={"message": "쿠키 초기화 완료"})
    res.delete_cookie("access_token", path="/")
    res.delete_cookie("refresh_token", path="/")
    return res

# 기존 로그아웃 방식(로컬스토리지)에서 쿠키방식으로 전환해서 만든 함수
@router.post("/auth/logout")
def logout():
    res = JSONResponse(content={"message": "로그아웃 완료"})
    res.delete_cookie("access_token", path="/")
    res.delete_cookie("refresh_token", path="/")
    return res