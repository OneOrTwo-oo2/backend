# Python 3.9 슬림 이미지 기반
FROM python:3.9-slim

# 환경 변수 설정 (시스템 상 비대화형 설치 허용)
ENV DEBIAN_FRONTEND=noninteractive

# 작업 디렉토리 설정
WORKDIR /app

# 필수 시스템 패키지 설치
# - build-essential: C/C++ 컴파일 도구
# - libgl1: OpenCV 및 ultralytics 실행을 위한 GL 라이브러리
# - curl, git: huggingface 및 기타 의존 패키지용
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 전체 프로젝트 복사
COPY . .

# 포트 열기 (FastAPI 기본)
EXPOSE 8000

# FastAPI 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
