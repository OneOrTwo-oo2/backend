# fastapi imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import router
import config
from utils.watsonx import get_ibm_access_token
from utils.langchain import load_vector_db

# set Access token in main.py
config.ACCESS_TOKEN = get_ibm_access_token(config.WATSON_API_KEY)

# load vector_db before starting server
config.vector_db = load_vector_db()

app = FastAPI()
app.include_router(router)

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프론트 도메인
    # allow_origins=["http://localhost:3000"],  # 프론트 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


