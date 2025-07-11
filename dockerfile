FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# 1. 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential libgl1-mesa-glx libglib2.0-0 curl git \
    && rm -rf /var/lib/apt/lists/*

# 최신 pip 설치
RUN pip install --upgrade pip

# 2. typing-extensions 문제 우회 (PyTorch 2.7.1 요구 충족)
RUN pip install typing-extensions==4.12.0

# 3. PyTorch 설치 (CUDA 11.8)
RUN pip install torch==2.7.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 4. 나머지 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 앱 복사
COPY app /app

# 6. 캐시 제거
RUN rm -rf /root/.cache /tmp/*

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
