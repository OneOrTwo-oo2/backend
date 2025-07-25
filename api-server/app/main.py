# fastapi imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import router

# DB초기화
from db.init_db import init_db


app = FastAPI()
app.include_router(router)

@app.on_event("startup")
def on_startup():
    init_db()

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
    uvicorn.run(app, host="0.0.0.0", port=8000)



## test