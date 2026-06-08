"""LLM-агент на чистом Python (вместо LangGraph — см. финальную HTML-объяснялку).

Шаги те же, что в архитектуре:
  generate_questions  -> вопросы раунда (адаптивные, на основе истории)
  generate_checklist  -> итоговый чеклист + резюме
Все вызовы идут в OpenRouter (модель minimax/minimax-m3) через openai SDK."""
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from .config import settings
from . import prompts

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
    return _client


def _format_history(answers: List[Dict[str, Any]]) -> str:
    if not answers:
        return ""
    lines = []
    for a in answers:
        transcript = a.get("transcript") or "(пусто)"
        lines.append(f"[Раунд {a['round']}] В: {a['question']}\n   О: {transcript}")
    return "\n".join(lines)


def _extract_json(text: str) -> Any:
    """Достаём JSON даже если модель обернула его в ```json ... ``` или текст."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def _chat(system: str, user: str, temperature: float = 0.6) -> str:
    resp = _get_client().chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        extra_headers={
            # Необязательные заголовки OpenRouter (рейтинг/атрибуция).
            "HTTP-Referer": "https://huggingface.co/spaces",
            "X-Title": "STT Checklist Agent",
        },
    )
    return resp.choices[0].message.content or ""


def generate_questions(round_number: int, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Возвращает {"summary": str, "questions": [str, ...]} — ровно N вопросов."""
    user = prompts.questions_user(
        prompts.GOAL, round_number, settings.questions_per_round, _format_history(answers)
    )
    raw = _chat(prompts.QUESTIONS_SYSTEM, user)
    try:
        data = _extract_json(raw)
        questions = [str(q).strip() for q in data.get("questions", []) if str(q).strip()]
        summary = str(data.get("summary", "")).strip()
    except Exception:
        questions, summary = [], ""

    questions = questions[: settings.questions_per_round]
    fallback = [
        "Расскажите подробнее о вашем проекте и его главной цели.",
        "Какие у вас желаемые сроки и ориентир по бюджету?",
        "Какие технические требования и интеграции для вас важны?",
    ]
    i = 0
    while len(questions) < settings.questions_per_round:
        questions.append(fallback[i % len(fallback)])
        i += 1
    return {"summary": summary, "questions": questions}


def generate_checklist(answers: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], str]:
    """Возвращает (items, summary). items — список пунктов чеклиста."""
    user = prompts.checklist_user(prompts.GOAL, _format_history(answers))
    raw = _chat(prompts.CHECKLIST_SYSTEM, user, temperature=0.3)
    try:
        data = _extract_json(raw)
        items = data.get("items", [])
        summary = str(data.get("summary", "")).strip()
    except Exception:
        items, summary = [], ""

    clean: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        notes = it.get("notes")
        if notes in (None, "null", ""):
            notes = None
        clean.append({
            "category": str(it.get("category", "Прочее")).strip() or "Прочее",
            "item": str(it.get("item", "")).strip(),
            "status": it.get("status", "needs_clarification"),
            "notes": notes,
        })
    return clean, summary
