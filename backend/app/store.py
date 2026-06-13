"""Простое in-memory хранилище сессий (для MVP).
Для production это заменяется на Redis/SQLite — структура та же."""
import uuid
from typing import Any, Dict, Optional

from .session_log import SessionLogger

sessions: Dict[str, Dict[str, Any]] = {}


def create_session() -> Dict[str, Any]:
    sid = uuid.uuid4().hex[:12]
    sessions[sid] = {
        "session_id": sid,
        "current_round": 0,      # номер раунда, чьи вопросы сейчас на руках у пользователя
        "questions": [],          # тексты вопросов текущего раунда
        "answers": [],            # [{round, question, transcript}]
        "summaries": [],          # краткие резюме после каждого раунда
        "checklist_items": [],    # итоговые пункты чеклиста
        "markdown": "",           # итоговый markdown
        "is_complete": False,
        "logger": SessionLogger(sid),
    }
    return sessions[sid]


def get(sid: str) -> Optional[Dict[str, Any]]:
    return sessions.get(sid)
