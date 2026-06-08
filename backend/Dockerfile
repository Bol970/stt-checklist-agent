FROM python:3.11-slim

# HF-кэш внутри /app, чтобы предзагруженная модель попала в образ и была доступна в рантайме.
ENV HF_HOME=/app/.cache \
    HF_HUB_CACHE=/app/.cache/hub \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ffmpeg обязателен для конвертации webm->wav; libsndfile1 — для soundfile.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# CPU-сборка torch (без CUDA — меньше образ, быстрее).
RUN pip install --no-cache-dir torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Предзагрузка Whisper во время сборки -> быстрый холодный старт Space.
RUN mkdir -p /app/.cache && chmod -R 777 /app/.cache
RUN python -c "from transformers import pipeline; pipeline('automatic-speech-recognition', model='openai/whisper-small')"
# Вторая HF-модель: тональность (ruBERT) — тоже кэшируем в образ.
RUN python -c "from transformers import pipeline; pipeline('text-classification', model='seara/rubert-tiny2-russian-sentiment')"

COPY ./app /app/app

# Hugging Face Spaces слушает порт 7860.
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
