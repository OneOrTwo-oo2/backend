import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 🔐 환경 변수 로딩
WATSON_API_KEY = os.getenv("WATSON_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
SPACE_ID = os.getenv("SPACE_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

WATSONX_URL = os.getenv("WATSONX_URL")

# ✅ access token 전역 저장
ACCESS_TOKEN = None

# vector_db 사전 저장
vector_db_disease = None
vector_db_recipe = None
embedding_model = None
