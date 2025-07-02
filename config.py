import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 🔐 환경 변수 로딩
WATSON_API_KEY = os.getenv("WATSON_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
SPACE_ID = os.getenv("SPACE_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL")  # 구글 이메일
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD")  # 구글 비밀번호
CHROME_PROFILE_PATH = os.getenv("CHROME_PROFILE_PATH")


# ✅ access token 전역 저장
ACCESS_TOKEN = None

# vector_db 사전 저장
vector_db = None
