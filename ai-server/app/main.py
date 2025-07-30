import config
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from utils.langchain import load_vector_db_disease, load_bm25_retriever, load_faiss_vectorstore  #load_vector_db_recipe
from utils.watsonx import get_valid_access_token
from utils.detect_ingredients import cleanup_old_files, shutdown_cleanup_threads
from api.router import router
from image_model.classifier import get_clip_model
import os
import pathlib

app = FastAPI()
app.include_router(router)

# 정적 파일 서빙 설정 (bounding box 이미지용) - 보안 강화
results_dir = "static/results"
os.makedirs(results_dir, exist_ok=True)

# 허용된 이미지 확장자
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

@app.get("/static/results/{filename}")
async def serve_result_image(filename: str):
    """결과 이미지만 안전하게 서빙"""
    # 파일 확장자 검증
    file_ext = pathlib.Path(filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다")
    
    # 경로 순회 공격 방지
    file_path = pathlib.Path(results_dir) / filename
    if not file_path.resolve().is_relative_to(pathlib.Path(results_dir).resolve()):
        raise HTTPException(status_code=400, detail="잘못된 파일 경로입니다")
    
    # 파일 존재 확인
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    
    # 파일 접근 후 즉시 삭제 예약
    from utils.detect_ingredients import delete_file_after_delay
    delete_file_after_delay(str(file_path), delay_seconds=5)  # 5초 후 삭제
    print(f"📸 이미지 접근 감지: {filename} - 5초 후 삭제 예약")
    
    return FileResponse(file_path, media_type=f"image/{file_ext[1:]}")

@app.on_event("shutdown")
async def on_shutdown():
    """서버 종료 시 정리 스레드들 안전하게 종료"""
    print("🛑 FastAPI 서버 종료 중...")
    shutdown_cleanup_threads()

@app.on_event("startup")
def on_startup():
    # set Access token in main.py
    get_valid_access_token()
    # load vector_db before starting server
    config.vector_db_disease = load_vector_db_disease()
    config.clip_model, config.preprocess, config.tokenizer = get_clip_model()
    config.bm25_retriever = load_bm25_retriever()
    config.faiss_loaded = load_faiss_vectorstore()
    
    # 정적 파일 자동 정리 스레드 시작
    cleanup_old_files("static/results", max_age_minutes=20)


# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://recipego-frontend-service:3000",
        "https://www.recipego-oot.com",
        "https://www.recipego-oot.com:80"      
    ],
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
