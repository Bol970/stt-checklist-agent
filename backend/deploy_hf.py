"""Деплой бэкенда на Hugging Face Space (Docker).
Запуск из папки backend/:
    HF_TOKEN=hf_xxx OPENROUTER_API_KEY=sk-or-... python deploy_hf.py [space_name]
Имя пользователя берётся из токена автоматически.
"""
import os
import sys

from huggingface_hub import HfApi

token = os.environ["HF_TOKEN"]
space_name = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("HF_SPACE_NAME", "stt-checklist-agent")
openrouter_key = os.environ["OPENROUTER_API_KEY"]
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "")

api = HfApi(token=token)
user = api.whoami()["name"]
repo_id = f"{user}/{space_name}"
host = f"{user}-{space_name}".lower().replace("_", "-") + ".hf.space"

print(f"[hf] user={user}  repo={repo_id}")
print(f"[hf] direct URL -> https://{host}")

# 1) Создаём Space (Docker SDK). exist_ok -> повторный запуск безопасен.
api.create_repo(repo_id=repo_id, repo_type="space", space_sdk="docker", exist_ok=True)

# 2) Секреты Space (НЕ попадают в код/репозиторий).
api.add_space_secret(repo_id=repo_id, key="OPENROUTER_API_KEY", value=openrouter_key)
if allowed_origins:
    api.add_space_secret(repo_id=repo_id, key="ALLOWED_ORIGINS", value=allowed_origins)
    print(f"[hf] ALLOWED_ORIGINS set -> {allowed_origins}")

# 3) Заливаем ТОЛЬКО нужные файлы (без .venv/.env/тестов/кэша).
api.upload_folder(
    repo_id=repo_id,
    repo_type="space",
    folder_path=".",
    allow_patterns=["app/**", "Dockerfile", "requirements.txt", "README.md"],
    ignore_patterns=["**/__pycache__/**", "*.pyc"],
    commit_message="Deploy STT Checklist Agent backend",
)

print("DONE_SPACE_PAGE https://huggingface.co/spaces/" + repo_id)
print("DONE_HOST https://" + host)
