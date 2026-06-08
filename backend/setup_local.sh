#!/usr/bin/env bash
# Локальная установка бэкенда (CPU). Запускать из папки backend/.
set -e
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
# CPU-сборка torch (без CUDA)
pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
echo "✅ Готово. Запуск:  source .venv/bin/activate && uvicorn app.main:app --port 7860"
