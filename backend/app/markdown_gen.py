"""Сборка итогового Markdown-чеклиста из структурированных пунктов.
Рендерим в Python (а не просим LLM) — так формат предсказуемый и стабильный."""
from collections import OrderedDict
from typing import Any, Dict, List

_STATUS_BOX = {
    "confirmed": "[x]",
    "needs_clarification": "[ ]",
    "not_discussed": "[ ]",
}
_STATUS_LABEL = {
    "needs_clarification": "требует уточнения",
    "not_discussed": "не обсуждалось",
}


def build_markdown(session: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
    lines: List[str] = ["# Чеклист созвона с клиентом", ""]
    lines.append(f"**Сессия:** `{session['session_id']}`  ")
    lines.append(f"**Задано вопросов:** {len(session['answers'])}")
    lines.append("")
    lines.append("---")
    lines.append("")

    categories: "OrderedDict[str, List[Dict[str, Any]]]" = OrderedDict()
    for it in items:
        categories.setdefault(it.get("category", "Прочее"), []).append(it)

    for category, cat_items in categories.items():
        lines.append(f"## {category}")
        for it in cat_items:
            status = it.get("status", "needs_clarification")
            box = _STATUS_BOX.get(status, "[ ]")
            text = it.get("item", "")
            note = it.get("notes")
            suffix = ""
            if status != "confirmed":
                label = _STATUS_LABEL.get(status, "")
                bits = [b for b in (label, note) if b]
                if bits:
                    suffix = " — " + "; ".join(bits)
            lines.append(f"- {box} {text}{suffix}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 📝 Ответы клиента (транскрипт)")
    for a in session["answers"]:
        lines.append(f"- **{a['question']}**")
        lines.append(f"  > {a.get('transcript') or '(пусто)'}")
    lines.append("")
    lines.append("---")
    lines.append("*Сгенерировано автоматически: STT Checklist Agent — Whisper (HF) + minimax-m3 (OpenRouter).*")
    return "\n".join(lines)
