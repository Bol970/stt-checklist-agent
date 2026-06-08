---
title: STT Checklist Agent
emoji: 🎤
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# STT Checklist Agent — Backend

Голосовой агент для заполнения чеклиста созвона с клиентом.

- **STT:** `openai/whisper-small` (локально, transformers)
- **LLM-агент:** `minimax/minimax-m3` через OpenRouter
- **API:** FastAPI

## Endpoints

| Метод | Путь | Описание |
|------|------|----------|
| GET  | `/health` | Состояние сервиса + загрузка Whisper |
| POST | `/api/session/start` | Старт сессии, первые 3 вопроса |
| POST | `/api/session/transcribe` | Транскрипция одного аудио (превью) |
| POST | `/api/session/{id}/submit` | Отправка ответов раунда → следующие вопросы или чеклист |
| GET  | `/api/session/{id}/results` | Итоговый чеклист (JSON + markdown) |
| GET  | `/api/session/{id}/download` | Скачать чеклист `.md` |

## Секреты (Space → Settings → Secrets)

- `OPENROUTER_API_KEY` — ключ OpenRouter.
- (опц.) `ALLOWED_ORIGINS` — URL фронтенда на Vercel (CORS). По умолчанию `*`.
