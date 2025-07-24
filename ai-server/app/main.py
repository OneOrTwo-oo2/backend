import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.langchain import load_vector_db_disease, load_bm25_retriever   # load_faiss_vectorstore  #load_vector_db_recipe
from utils.watsonx import get_valid_access_token
from api.router import router
from image_model.classifier import get_clip_model

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
def on_startup():
    # set Access token in main.py
    get_valid_access_token()
    # load vector_db before starting server
    config.vector_db_disease = load_vector_db_disease()
    config.clip_model, config.preprocess, config.tokenizer = get_clip_model()
    config.bm25_retriever = load_bm25_retriever()
    #config.faiss_loaded = load_faiss_vectorstore()


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
