FROM python:3.13-slim

ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu \
    CUDA_VISIBLE_DEVICES="" \
    NVIDIA_VISIBLE_DEVICES=none

RUN mkdir -p /app
COPY app/ /app/
WORKDIR /app

COPY Pipfile ./Pipfile
COPY Pipfile.lock ./Pipfile.lock

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pipenv
RUN pipenv install --system --deploy

# Streamlit 실행
EXPOSE 8502

# 실행 권한 설정
RUN chmod +x /app/run.py

HEALTHCHECK CMD curl --fail http://localhost:8502/_stcore/health


CMD ["streamlit", "run", "run.py", "--server.address", "0.0.0.0", "--server.port", "8502"]