# auth/jwt_handler.py
import jwt
from datetime import datetime, timedelta
from config import SECRET_KEY
SECRET_KEY = SECRET_KEY  # 환경변수로 관리하는 게 좋음
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise Exception("Access token expired")
    except jwt.PyJWTError:
        raise Exception("Invalid token")
