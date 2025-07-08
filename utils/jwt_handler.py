import jwt
from datetime import datetime, timedelta
from config import SECRET_KEY
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db.connection import SessionLocal
from db.models import User

SECRET_KEY = SECRET_KEY  # 환경변수로 관리하는 게 좋음
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/google-login")

# ✅ JWT 생성
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ✅ JWT 리프레쉬 토큰 생성 // 안하면 토큰 탈취의 위험이 있음
def create_refresh_token(data: dict, expires_delta: timedelta = timedelta(days=7)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ✅ JWT 어세스 디코딩
def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise Exception("Access token expired")
    except jwt.PyJWTError:
        raise Exception("Invalid token")
    
# ✅ JWT 디코딩 리프레쉬 토큰 보안 강화를 위해!
def decode_refresh_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise Exception("Refresh token expired")
    except jwt.PyJWTError:
        raise Exception("Invalid refresh token")


# ✅ R2R 방식: 쿠키에서 access_token 추출하여 유저 객체 반환// 기존
def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(lambda: SessionLocal())
) -> User:
    token = request.cookies.get("access_token")  # ✅ 쿠키에서 토큰 추출
    if not token:
        raise HTTPException(status_code=401, detail="Access token 누락")

    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
