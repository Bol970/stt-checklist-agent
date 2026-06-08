"""Конфигурация приложения. Значения читаются из переменных окружения
(на Hugging Face Space — из Secrets, локально — из backend/.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- OpenRouter (LLM) ---
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "minimax/minimax-m3"

    # --- Whisper (STT) ---
    whisper_model: str = "openai/whisper-small"

    # --- Логика интервью ---
    max_rounds: int = 3
    questions_per_round: int = 3
    max_audio_seconds: int = 120

    # --- CORS: "*" или список origin через запятую ---
    allowed_origins: str = "*"


settings = Settings()
