import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.langchain import load_vector_db_disease, load_vector_db_recipe
from utils.watsonx import get_valid_access_token
from api.router import router

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
def on_startup():
    # set Access token in main.py
    get_valid_access_token()
    # load vector_db before starting server
    config.vector_db_disease = load_vector_db_disease()
    config.embedding_model, config.vector_db_recipe = load_vector_db_recipe()

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프론트 도메인
    # allow_origins=["http://localhost:3000"],  # 프론트 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Hello from FastAPI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
