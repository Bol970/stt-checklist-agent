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
from . import tools
from .session_log import SessionLogger

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


_STEP_LABELS = {
    "calc": ("🧮", "Считаю числа"),
    "kb_search": ("🗂", "Сверяюсь с базой знаний"),
    "web_search": ("🔎", "Ищу в вебе"),
}


def run_agent(system: str, user: str, *, temperature: float = 0.6,
              logger: Optional[SessionLogger] = None) -> str:
    """Tool-calling loop: модель сама решает, звать ли инструменты. Возвращает финальный текст."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    last_content = ""
    for _ in range(settings.agent_max_tool_iters):
        resp = _get_client().chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            tools=tools.TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=temperature,
            extra_headers={
                "HTTP-Referer": "https://huggingface.co/spaces",
                "X-Title": "STT Checklist Agent",
            },
        )
        msg = resp.choices[0].message
        last_content = msg.content or last_content
        if not msg.tool_calls:
            return msg.content or ""
        messages.append({
            # content может быть None у assistant-сообщения с tool_calls — так и оставляем
            "role": "assistant", "content": msg.content,
            "tool_calls": [{"id": tc.id, "type": "function",
                            "function": {"name": tc.function.name,
                                         "arguments": tc.function.arguments}}
                           for tc in msg.tool_calls],
        })
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except Exception:
                args = {}
            result = tools.dispatch(name, args)
            if logger is not None:
                icon, label = _STEP_LABELS.get(name, ("🛠", f"Инструмент {name}"))
                logger.step(label, icon=icon, tool=name, args=args,
                            result=str(result)[:200])
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(result, ensure_ascii=False)})
    # Исчерпали лимит итераций, а финального ответа модель так и не дала.
    if logger is not None:
        logger.step("Достигнут лимит вызовов инструментов", icon="⚠")
    return last_content


def generate_questions(round_number: int, answers: List[Dict[str, Any]],
                       logger: Optional[SessionLogger] = None) -> Dict[str, Any]:
    """Возвращает {"summary": str, "questions": [str, ...]} — ровно N вопросов."""
    user = prompts.questions_user(
        prompts.GOAL, round_number, settings.questions_per_round, _format_history(answers)
    )
    raw = run_agent(prompts.QUESTIONS_SYSTEM, user, logger=logger)
    try:
        data = _extract_json(raw)
        questions = [str(q).strip() for q in data.get("questions", []) if str(q).strip()]
        summary = str(data.get("summary", "")).strip()
    except Exception:
        questions, summary = [], ""

    questions = questions[: settings.questions_per_round]
    fallback = [
        "Что за проект и какая у него главная цель?",
        "Какие сроки и какой примерно бюджет?",
        "Какие технические требования или интеграции важны?",
    ]
    i = 0
    while len(questions) < settings.questions_per_round:
        questions.append(fallback[i % len(fallback)])
        i += 1
    return {"summary": summary, "questions": questions}


def generate_checklist(answers: List[Dict[str, Any]],
                       logger: Optional[SessionLogger] = None) -> Tuple[List[Dict[str, Any]], str]:
    """Возвращает (items, summary). items — список пунктов чеклиста."""
    user = prompts.checklist_user(prompts.GOAL, _format_history(answers))
    raw = run_agent(prompts.CHECKLIST_SYSTEM, user, temperature=0.3, logger=logger)
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
