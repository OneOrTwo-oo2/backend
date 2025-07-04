from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME

# DB 연결 엔진
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"


engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ 요게 필요했던 부분!
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()