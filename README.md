# 🎤 STT Checklist Agent

Голосовой AI-агент, который проводит интервью с клиентом и собирает **чеклист созвона**: задаёт вопросы по цели, слушает **голосовые** ответы, распознаёт их через **Whisper** и анализирует через LLM. 3 раунда × 3 вопроса → готовый Markdown-чеклист.

## 🌐 Демо

| | URL |
|---|---|
| **Приложение** | https://stt-checklist-agent.vercel.app |
| Backend (health) | https://bol970-stt-checklist-agent.hf.space/health |
| API docs | https://bol970-stt-checklist-agent.hf.space/docs |
| HF Space | https://huggingface.co/spaces/Bol970/stt-checklist-agent |

Подробный разбор архитектуры и принятых компромиссов — в **[PROJECT_EXPLAINED.html](PROJECT_EXPLAINED.html)** (открыть в браузере).

## 🏗️ Архитектура

```
Браузер (запись голоса)
   │  webm-аудио / JSON  (HTTPS)
   ▼
Frontend — Next.js 15 → Vercel
   │
   ▼
Backend — FastAPI → Hugging Face Space (Docker)
   ├─ Whisper-small (STT, локально, CPU)
   ├─ ruBERT sentiment (тональность каждого ответа, HF)
   └─ Agent → OpenRouter (minimax/minimax-m3): вопросы, анализ, чеклист
```

- **Frontend:** Next.js 15 · React 19 · TypeScript · Tailwind · shadcn-style UI
- **Backend:** Python 3.11 · FastAPI · transformers (whisper-small) · ffmpeg
- **LLM:** `minimax/minimax-m3` через OpenRouter (OpenAI-совместимый SDK)
- **STT:** `openai/whisper-small` локально
- **Тональность:** `seara/rubert-tiny2-russian-sentiment` — вторая HF-модель, оценивает тон каждого ответа
- **Стиль вопросов:** принципы скилла [humanizer](https://github.com/blader/humanizer) (адаптация под русский) встроены в промпт — агент говорит разговорно, без канцелярита

## 📁 Структура

```
backend/         FastAPI + Whisper + агент (деплой на HF Space)
  app/           main.py, agent.py, transcription.py, prompts.py, markdown_gen.py, ...
  Dockerfile     образ для HF Spaces (порт 7860)
  deploy_hf.py   скрипт деплоя на Hugging Face
frontend/        Next.js 15 (деплой на Vercel)
  app/ components/ hooks/ lib/
PROJECT_EXPLAINED.html   подробный разбор проекта
checklist-agent-architecture.md   исходный архитектурный документ
```

## 🚀 Локальный запуск

**Backend**
```bash
cd backend
bash setup_local.sh                 # venv + torch(CPU) + зависимости
cp .env.example .env                # вписать OPENROUTER_API_KEY
source .venv/bin/activate
uvicorn app.main:app --port 7860
```

**Frontend**
```bash
cd frontend
npm install
# .env.local: NEXT_PUBLIC_API_URL=http://localhost:7860
npm run dev                         # http://localhost:3000
```

> Микрофон в браузере доступен только на `https://` или `http://localhost`.

## 🔑 Переменные окружения

| Где | Переменная | Назначение |
|-----|-----------|-----------|
| backend (`.env` / HF Secret) | `OPENROUTER_API_KEY` | ключ OpenRouter |
| backend (опц.) | `ALLOWED_ORIGINS` | CORS, по умолчанию `*` |
| frontend (`.env.local` / Vercel) | `NEXT_PUBLIC_API_URL` | URL бэкенда |

Секреты в репозиторий не коммитятся (`.env`, `.env.local` — в `.gitignore`).
