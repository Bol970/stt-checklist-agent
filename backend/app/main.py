"""FastAPI-приложение: API сессий + локальный Whisper + агент на OpenRouter.
Деплоится как Docker-образ на Hugging Face Space (порт 7860)."""
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from . import agent, store
from .config import settings
from .markdown_gen import build_markdown
from .transcription import transcriber


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Грузим Whisper один раз при старте (а не на каждый запрос).
    try:
        transcriber.load()
        print("[startup] Whisper model loaded:", settings.whisper_model)
    except Exception as e:  # не валим старт — health покажет whisper_loaded=false
        print("[startup] Whisper load failed:", e)
    yield


app = FastAPI(title="STT Checklist Agent", version="1.0.0", lifespan=lifespan)

_origins = (
    ["*"]
    if settings.allowed_origins.strip() == "*"
    else [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _q_objs(round_no: int, questions: List[str]):
    return [{"id": f"q{round_no}_{i}", "text": q} for i, q in enumerate(questions)]


@app.get("/")
def root():
    return {"name": "STT Checklist Agent", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "whisper_loaded": transcriber.loaded,
        "whisper_model": settings.whisper_model,
        "llm_model": settings.llm_model,
        "llm_key_set": bool(settings.openrouter_api_key),
    }


@app.post("/api/session/start")
def start_session():
    s = store.create_session()
    s["current_round"] = 1
    result = agent.generate_questions(1, [])
    s["questions"] = result["questions"]
    return {
        "session_id": s["session_id"],
        "round": 1,
        "max_rounds": settings.max_rounds,
        "questions": _q_objs(1, s["questions"]),
        "is_complete": False,
    }


@app.post("/api/session/transcribe")
async def transcribe_one(audio_file: UploadFile = File(...)):
    """Транскрипция одного аудио — для превью перед подтверждением ответа."""
    data = await audio_file.read()
    return {"transcript": transcriber.transcribe(data)}


@app.post("/api/session/{session_id}/submit")
async def submit_answers(
    session_id: str,
    audio_files: List[UploadFile] = File(...),
    question_ids: str = Form(""),
):
    s = store.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    if s["is_complete"]:
        return {"round": s["current_round"], "is_complete": True, "checklist_preview": s["markdown"]}

    questions = s["questions"]
    transcripts = []
    for f in audio_files:
        transcripts.append(transcriber.transcribe(await f.read()))
    for q, t in zip(questions, transcripts):
        s["answers"].append({"round": s["current_round"], "question": q, "transcript": t})

    # Ещё есть раунды -> генерируем следующие вопросы (адаптивно).
    if s["current_round"] < settings.max_rounds:
        s["current_round"] += 1
        result = agent.generate_questions(s["current_round"], s["answers"])
        s["questions"] = result["questions"]
        s["summaries"].append(result.get("summary", ""))
        return {
            "round": s["current_round"],
            "max_rounds": settings.max_rounds,
            "questions": _q_objs(s["current_round"], s["questions"]),
            "round_summary": result.get("summary", ""),
            "is_complete": False,
        }

    # Последний раунд -> собираем чеклист.
    items, summary = agent.generate_checklist(s["answers"])
    md = build_markdown(s, items)
    s["checklist_items"], s["markdown"], s["is_complete"] = items, md, True
    return {
        "round": s["current_round"],
        "is_complete": True,
        "round_summary": summary,
        "checklist_preview": md,
    }


@app.get("/api/session/{session_id}/results")
def get_results(session_id: str):
    s = store.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    return {
        "session_id": session_id,
        "checklist": s["checklist_items"],
        "markdown": s["markdown"],
        "is_complete": s["is_complete"],
    }


@app.get("/api/session/{session_id}/download")
def download(session_id: str):
    s = store.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    return Response(
        content=s["markdown"] or "# (пусто)",
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=checklist-{session_id}.md"},
    )
