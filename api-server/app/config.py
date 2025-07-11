import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL")  # 구글 이메일
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD")  # 구글 비밀번호
CHROME_PROFILE_PATH = os.getenv("CHROME_PROFILE_PATH")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
SECRET_KEY = os.getenv("SECRET_KEY") # JWT 토큰 인증키 우리가 지정하는 것!

