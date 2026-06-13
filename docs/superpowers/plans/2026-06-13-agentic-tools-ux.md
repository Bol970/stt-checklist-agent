# Agentic Tools + UX восприятия времени — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Превратить агента в tool-using (function calling, агент сам решает когда звать calc/kb_search/web_search), добавить UX по трём законам восприятия времени, mock-режим и логирование сессии.

**Architecture:** Бэкенд — FastAPI: `_chat` заменяется на `run_agent` (tool-calling loop) + `tools.py` (реестр инструментов) + `SessionLogger` (память+файл). Единый поток step-событий питает и `/progress` (UX закон №3), и лог-файл. Mock-режим — bool-переменная окружения, по умолчанию выкл. Фронт — Next.js: ProgressPanel с таймером/шагами, «✓ принято», демо-тоггл, просмотр лога.

**Tech Stack:** Python 3.12, FastAPI, openai SDK (OpenRouter, `minimax/minimax-m3`), pytest (новая dev-зависимость), tavily-python (опц.); Next.js 15, React, TypeScript.

**Спека:** [docs/superpowers/specs/2026-06-13-agentic-tools-ux-design.md](../specs/2026-06-13-agentic-tools-ux-design.md)

---

## File Structure

| Файл | Ответственность |
|---|---|
| `backend/app/tools.py` | **новый** — calc / kb_search / web_search, JSON-схемы, dispatch |
| `backend/app/knowledge_base.md` | **новый** — КБ компании |
| `backend/app/session_log.py` | **новый** — SessionLogger (step-события: память + файл) |
| `backend/app/mock_data.py` | **новый** — заготовленные ответы для mock-режима |
| `backend/app/agent.py` | рефактор `_chat`→`run_agent` (tool loop), проброс логгера |
| `backend/app/config.py` | новые настройки (секреты + переменные) |
| `backend/app/store.py` | привязать SessionLogger к сессии |
| `backend/app/main.py` | эндпоинты `/progress`, `/log`; mock-режим; проброс логгера |
| `backend/requirements.txt` | + `pytest`, `tavily-python` |
| `backend/.env.example` | новые секреты/переменные + комментарий о разделении |
| `backend/tests/` | **новый** — юнит-тесты pytest |
| `frontend/lib/types.ts` | типы ProgressResponse |
| `frontend/lib/api.ts` | `getProgress`, `getLog`, демо-сабмит |
| `frontend/components/ProgressPanel.tsx` | **новый** — шаги + таймер + оценка |
| `frontend/components/LogViewer.tsx` | **новый** — просмотр лога сессии |
| `frontend/components/screens/Interview.tsx` | «✓ принято», polling прогресса, демо-тоггл |

---

## Task 1: Настройки конфигурации (секреты + переменные)

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/.env.example`

- [ ] **Step 1: Добавить настройки в `Settings`**

В [backend/app/config.py](../../../backend/app/config.py) после блока sentiment-модели добавить:

```python
    # --- Секрет: веб-поиск (опционально) ---
    tavily_api_key: str = ""

    # --- Переменные режима (не секреты) ---
    mock_mode: bool = False           # MOCK_MODE=true → заготовленные ответы вместо STT
    kb_path: str = "app/knowledge_base.md"
    agent_max_tool_iters: int = 5     # макс. итераций tool-calling в run_agent
```

pydantic-settings сам приводит `MOCK_MODE=true/false/1/0` к `bool` — ручной парсинг не нужен.

- [ ] **Step 2: Обновить `.env.example`**

Заменить содержимое [backend/.env.example](../../../backend/.env.example):

```bash
# === СЕКРЕТЫ (HF Space → Secrets, локально — этот файл, в git НЕ коммитим) ===
OPENROUTER_API_KEY=sk-or-v1-...
# Веб-поиск через Tavily (опционально; без ключа инструмент web_search просто отключён):
TAVILY_API_KEY=

# === ПЕРЕМЕННЫЕ РЕЖИМА (HF Space → Variables, дефолты можно коммитить) ===
# Mock-режим: true — подставлять заготовленные ответы вместо распознавания голоса.
# ВАЖНО: включать только после того, как убедились, что реальный путь (голос) работает.
MOCK_MODE=false
# Прочее (по умолчанию такие):
# LLM_MODEL=minimax/minimax-m3
# AGENT_MAX_TOOL_ITERS=5
# KB_PATH=app/knowledge_base.md
# ALLOWED_ORIGINS=*
```

- [ ] **Step 3: Проверить, что конфиг грузится**

Run: `cd backend && .venv/bin/python -c "from app.config import settings; print(settings.mock_mode, settings.agent_max_tool_iters, settings.kb_path)"`
Expected: `False 5 app/knowledge_base.md`

- [ ] **Step 4: Commit**

```bash
git add backend/app/config.py backend/.env.example
git commit -m "config: секреты vs переменные (tavily, mock_mode, kb_path, tool-iters)"
```

---

## Task 2: pytest + структура тестов

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/tests/__init__.py`
- Create: `backend/pytest.ini`

- [ ] **Step 1: Добавить pytest в requirements**

В [backend/requirements.txt](../../../backend/requirements.txt) добавить в конец:

```
pytest==8.3.4
```

- [ ] **Step 2: Установить**

Run: `cd backend && .venv/bin/pip install pytest==8.3.4`
Expected: `Successfully installed pytest-8.3.4` (или already satisfied)

- [ ] **Step 3: Создать `backend/pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 4: Создать `backend/tests/__init__.py`** (пустой файл)

- [ ] **Step 5: Проверить, что pytest стартует**

Run: `cd backend && .venv/bin/python -m pytest -q`
Expected: `no tests ran` (без ошибок коллекции)

- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/pytest.ini backend/tests/__init__.py
git commit -m "test: добавить pytest и каталог tests/"
```

---

## Task 3: Инструмент `calc` (детерминированная арифметика)

**Files:**
- Create: `backend/app/tools.py`
- Test: `backend/tests/test_tools_calc.py`

- [ ] **Step 1: Написать падающий тест**

`backend/tests/test_tools_calc.py`:

```python
from app.tools import calc


def test_calc_basic():
    assert calc("5 * 200000 * 3") == {"result": 3000000}


def test_calc_float():
    assert calc("2000000 / 3")["result"] > 666666


def test_calc_unary_and_parens():
    assert calc("-(2 + 3) * 4") == {"result": -20}


def test_calc_rejects_names():
    out = calc("__import__('os').system('echo hi')")
    assert "error" in out


def test_calc_rejects_garbage():
    out = calc("not a number")
    assert "error" in out
```

- [ ] **Step 2: Запустить — убедиться, что падает**

Run: `cd backend && .venv/bin/python -m pytest tests/test_tools_calc.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.tools'`

- [ ] **Step 3: Реализовать calc в `backend/app/tools.py`**

```python
"""Инструменты агента: calc / kb_search / web_search.
Каждый инструмент возвращает dict; ошибки — это {"error": "..."} (агент не падает).
Решение о вызове принимает модель (function calling, tool_choice="auto")."""
import ast
import operator
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

from .config import settings

# --- calc: безопасная арифметика на ast (без eval) -------------------------
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("unsupported expression")


def calc(expr: str) -> Dict[str, Any]:
    """Считает арифметическое выражение. Разрешены только числа и + - * / // % ** ( )."""
    try:
        return {"result": _eval_node(ast.parse(expr, mode="eval"))}
    except Exception as e:
        return {"error": f"cannot evaluate '{expr}': {e}"}
```

- [ ] **Step 4: Запустить — убедиться, что проходит**

Run: `cd backend && .venv/bin/python -m pytest tests/test_tools_calc.py -q`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/tools.py backend/tests/test_tools_calc.py
git commit -m "tools: calc — безопасная арифметика на ast"
```

---

## Task 4: База знаний + инструмент `kb_search`

**Files:**
- Create: `backend/app/knowledge_base.md`
- Modify: `backend/app/tools.py`
- Test: `backend/tests/test_tools_kb.py`

- [ ] **Step 1: Создать `backend/app/knowledge_base.md`**

```markdown
# База знаний компании

## О компании
Студия заказной разработки. Делаем веб- и мобильные приложения под ключ:
аналитика требований, дизайн, разработка, поддержка. Средняя команда на проект —
3–6 человек (PM, дизайнер, 1–3 разработчика, QA).

## Типовые проекты и сроки
- Лендинг / промо-сайт: 2–4 недели.
- Корпоративный сайт / каталог: 1–2 месяца.
- MVP мобильного или веб-приложения: 2–4 месяца.
- Сложная платформа с интеграциями: от 4 месяцев.

## Вилки бюджета (ориентир)
- Лендинг: 150–400 тыс. руб.
- MVP приложения: 1.5–4 млн руб.
- Платформа с интеграциями: от 4 млн руб.
Ставка ориентировочно 150–250 тыс. руб. за разработчика в месяц.

## Частые интеграции
- 1С: обмен заказами/товарами; уточнять версию (8.3), формат обмена, есть ли готовый API.
- Платежи: ЮKassa, CloudPayments; нужен расчётный счёт и договор эквайринга.
- CRM: amoCRM, Bitrix24; уточнять, какие сущности синхронизируются.
- Карты/геолокация: Яндекс.Карты (нужен API-ключ и тариф).

## Типовые риски
- Нет чёткого ТЗ → расползание объёма; фиксируем MVP-границу.
- Интеграции с внешними системами без документации/доступов → срыв сроков.
- Нет ответственного на стороне клиента для приёмки.
- Контент (тексты, фото) не готов к старту разработки.
- Жёсткий дедлайн под событие при нечётком объёме.

## О чём всегда уточнять на созвоне
Целевая платформа (web/iOS/Android), целевая аудитория, ключевая метрика успеха,
кто принимает работу, наличие готового дизайна/бренда, требования к интеграциям и доступам.
```

- [ ] **Step 2: Написать падающий тест**

`backend/tests/test_tools_kb.py`:

```python
from app.tools import kb_search


def test_kb_finds_integration_section():
    out = kb_search("интеграция с 1С")
    assert "snippets" in out
    joined = " ".join(s["text"] for s in out["snippets"])
    assert "1С" in joined


def test_kb_finds_budget():
    out = kb_search("бюджет сколько стоит лендинг")
    joined = " ".join(s["title"] + s["text"] for s in out["snippets"])
    assert "удж" in joined.lower() or "150" in joined


def test_kb_empty_on_nonsense():
    out = kb_search("zzz qqq xxx")
    assert out["snippets"] == []
```

- [ ] **Step 3: Запустить — убедиться, что падает**

Run: `cd backend && .venv/bin/python -m pytest tests/test_tools_kb.py -q`
Expected: FAIL — `ImportError: cannot import name 'kb_search'`

- [ ] **Step 4: Добавить kb_search в `backend/app/tools.py`**

Дописать в конец файла:

```python
# --- kb_search: keyword-поиск по секциям knowledge_base.md ------------------
_kb_cache: List[Tuple[str, str]] = None  # type: ignore


def _load_kb() -> List[Tuple[str, str]]:
    global _kb_cache
    if _kb_cache is None:
        path = Path(settings.kb_path)
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        sections: List[Tuple[str, str]] = []
        title, lines = "Документ", []
        for line in text.splitlines():
            if line.startswith("#"):
                if lines:
                    sections.append((title, "\n".join(lines).strip()))
                title, lines = line.lstrip("#").strip(), []
            else:
                lines.append(line)
        if lines:
            sections.append((title, "\n".join(lines).strip()))
        _kb_cache = [(t, b) for t, b in sections if b]
    return _kb_cache


def kb_search(query: str, top_k: int = 3) -> Dict[str, Any]:
    """Ищет релевантные секции в базе знаний компании по ключевым словам."""
    words = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
    scored = []
    for title, body in _load_kb():
        hay = (title + " " + body).lower()
        score = sum(hay.count(w) for w in words)
        if score:
            scored.append((score, title, body))
    scored.sort(key=lambda x: x[0], reverse=True)
    return {"snippets": [{"title": t, "text": b} for _, t, b in scored[:top_k]]}
```

- [ ] **Step 5: Запустить — убедиться, что проходит**

Run: `cd backend && .venv/bin/python -m pytest tests/test_tools_kb.py -q`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/app/knowledge_base.md backend/app/tools.py backend/tests/test_tools_kb.py
git commit -m "tools: knowledge_base.md + kb_search (keyword-поиск по секциям)"
```

---

## Task 5: Инструмент `web_search` (Tavily, мягкая деградация)

**Files:**
- Modify: `backend/app/tools.py`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/test_tools_web.py`

- [ ] **Step 1: Добавить tavily в requirements**

В [backend/requirements.txt](../../../backend/requirements.txt) добавить:

```
tavily-python==0.5.0
```

Run: `cd backend && .venv/bin/pip install tavily-python==0.5.0`
Expected: `Successfully installed ...`

- [ ] **Step 2: Написать падающий тест** (проверяем деградацию без ключа — без сети)

`backend/tests/test_tools_web.py`:

```python
from app import tools


def test_web_search_disabled_without_key(monkeypatch):
    monkeypatch.setattr(tools.settings, "tavily_api_key", "")
    out = tools.web_search("что такое 1С")
    assert "error" in out
    assert "disabled" in out["error"]
```

- [ ] **Step 3: Запустить — убедиться, что падает**

Run: `cd backend && .venv/bin/python -m pytest tests/test_tools_web.py -q`
Expected: FAIL — `AttributeError: module 'app.tools' has no attribute 'web_search'`

- [ ] **Step 4: Добавить web_search в `backend/app/tools.py`**

Дописать в конец:

```python
# --- web_search: Tavily (опционально) --------------------------------------
def web_search(query: str, max_results: int = 3) -> Dict[str, Any]:
    """Ищет в вебе через Tavily. Без TAVILY_API_KEY инструмент отключён."""
    if not settings.tavily_api_key:
        return {"error": "web search disabled (no TAVILY_API_KEY)"}
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.tavily_api_key)
        resp = client.search(query=query, max_results=max_results)
        return {"results": [
            {"title": r.get("title"), "url": r.get("url"),
             "snippet": (r.get("content") or "")[:300]}
            for r in resp.get("results", [])
        ]}
    except Exception as e:
        return {"error": f"web search failed: {e}"}
```

- [ ] **Step 5: Запустить — убедиться, что проходит**

Run: `cd backend && .venv/bin/python -m pytest tests/test_tools_web.py -q`
Expected: PASS (1 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/app/tools.py backend/requirements.txt backend/tests/test_tools_web.py
git commit -m "tools: web_search через Tavily (мягкая деградация без ключа)"
```

---

## Task 6: Реестр инструментов + JSON-схемы + dispatch

**Files:**
- Modify: `backend/app/tools.py`
- Test: `backend/tests/test_tools_registry.py`

- [ ] **Step 1: Написать падающий тест**

`backend/tests/test_tools_registry.py`:

```python
from app.tools import TOOL_SCHEMAS, dispatch


def test_schemas_have_three_tools():
    names = {s["function"]["name"] for s in TOOL_SCHEMAS}
    assert names == {"calc", "kb_search", "web_search"}


def test_dispatch_calc():
    assert dispatch("calc", {"expr": "2+2"}) == {"result": 4}


def test_dispatch_unknown_tool():
    assert "error" in dispatch("nope", {})


def test_dispatch_bad_args_does_not_crash():
    out = dispatch("calc", {"wrong": "x"})
    assert "error" in out
```

- [ ] **Step 2: Запустить — убедиться, что падает**

Run: `cd backend && .venv/bin/python -m pytest tests/test_tools_registry.py -q`
Expected: FAIL — `ImportError: cannot import name 'TOOL_SCHEMAS'`

- [ ] **Step 3: Добавить схемы и dispatch в `backend/app/tools.py`**

Дописать в конец:

```python
# --- Реестр и схемы для OpenRouter function calling ------------------------
TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {"type": "function", "function": {
        "name": "calc",
        "description": "Точно посчитать арифметику (бюджет, сроки, размер команды). "
                       "Используй, когда в ответах есть числа, которые нужно перемножить/сложить.",
        "parameters": {"type": "object",
                       "properties": {"expr": {"type": "string",
                                               "description": "Выражение, напр. '5 * 200000 * 3'"}},
                       "required": ["expr"]}}},
    {"type": "function", "function": {
        "name": "kb_search",
        "description": "Поиск по внутренней базе знаний компании (типовые проекты, сроки, "
                       "вилки бюджета, интеграции, риски). Свернись с ней, чтобы задавать "
                       "умные вопросы и не переспрашивать известное.",
        "parameters": {"type": "object",
                       "properties": {"query": {"type": "string"}},
                       "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "web_search",
        "description": "Поиск в интернете по упомянутой клиентом технологии/сервису/интеграции, "
                       "если её нет в базе знаний и нужно уточнить детали.",
        "parameters": {"type": "object",
                       "properties": {"query": {"type": "string"}},
                       "required": ["query"]}}},
]

_REGISTRY: Dict[str, Callable[..., Dict[str, Any]]] = {
    "calc": calc, "kb_search": kb_search, "web_search": web_search,
}


def dispatch(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Вызывает инструмент по имени; любые ошибки превращает в {"error": ...}."""
    fn = _REGISTRY.get(name)
    if fn is None:
        return {"error": f"unknown tool: {name}"}
    try:
        return fn(**args)
    except Exception as e:
        return {"error": f"tool {name} failed: {e}"}
```

- [ ] **Step 4: Запустить — убедиться, что проходит**

Run: `cd backend && .venv/bin/python -m pytest tests/test_tools_registry.py -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/tools.py backend/tests/test_tools_registry.py
git commit -m "tools: реестр TOOL_SCHEMAS + dispatch (function calling)"
```

---

## Task 7: SessionLogger (step-события: память + файл)

**Files:**
- Create: `backend/app/session_log.py`
- Test: `backend/tests/test_session_log.py`

- [ ] **Step 1: Написать падающий тест**

`backend/tests/test_session_log.py`:

```python
from pathlib import Path

from app.session_log import SessionLogger


def test_logger_records_steps_and_progress(tmp_path):
    lg = SessionLogger("abc123", log_dir=tmp_path)
    lg.start_phase(estimate_ms=45000)
    lg.step("Распознаю речь", icon="🎙")
    lg.step("Считаю бюджет", icon="🧮", tool="calc")
    prog = lg.progress()
    assert prog["estimate_ms"] == 45000
    assert [s["text"] for s in prog["steps"]] == ["Распознаю речь", "Считаю бюджет"]
    assert prog["elapsed_ms"] >= 0


def test_logger_writes_file(tmp_path):
    lg = SessionLogger("abc123", log_dir=tmp_path)
    lg.step("привет", icon="•")
    log_text = (tmp_path / "session-abc123.log").read_text(encoding="utf-8")
    assert "привет" in log_text


def test_start_phase_resets_live_steps_but_keeps_file(tmp_path):
    lg = SessionLogger("s", log_dir=tmp_path)
    lg.step("раунд 1")
    lg.start_phase(estimate_ms=1000)
    lg.step("раунд 2")
    assert [s["text"] for s in lg.progress()["steps"]] == ["раунд 2"]
    assert "раунд 1" in (tmp_path / "session-s.log").read_text(encoding="utf-8")
```

- [ ] **Step 2: Запустить — убедиться, что падает**

Run: `cd backend && .venv/bin/python -m pytest tests/test_session_log.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.session_log'`

- [ ] **Step 3: Реализовать `backend/app/session_log.py`**

```python
"""Лог сессии: один поток step-событий питает и /progress (UX), и текстовый лог-файл.
Шаги в памяти (self.steps) — для живого прогресса текущего ожидания;
файл logs/session-<id>.log аккумулирует всё за сессию."""
import json
import time
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_LOG_DIR = Path("logs")


class SessionLogger:
    def __init__(self, session_id: str, log_dir: Path = DEFAULT_LOG_DIR):
        self.session_id = session_id
        self.steps: List[Dict[str, Any]] = []
        self.estimate_ms = 0
        self._started = time.time()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.log_dir / f"session-{session_id}.log"

    def _elapsed_ms(self) -> int:
        return int((time.time() - self._started) * 1000)

    def start_phase(self, estimate_ms: int = 0) -> None:
        """Начать новое ожидание: сбросить таймер и живые шаги (файл не трогаем)."""
        self._started = time.time()
        self.steps = []
        self.estimate_ms = estimate_ms

    def step(self, text: str, icon: str = "•", **details: Any) -> None:
        evt = {"ts": self._elapsed_ms(), "icon": icon, "text": text}
        self.steps.append(evt)
        line = f"[{evt['ts']:>7} ms] {icon} {text}"
        if details:
            line += " | " + json.dumps(details, ensure_ascii=False, default=str)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def progress(self) -> Dict[str, Any]:
        return {"steps": self.steps, "elapsed_ms": self._elapsed_ms(),
                "estimate_ms": self.estimate_ms}

    def read_log(self) -> str:
        return self.path.read_text(encoding="utf-8") if self.path.exists() else ""
```

- [ ] **Step 4: Запустить — убедиться, что проходит**

Run: `cd backend && .venv/bin/python -m pytest tests/test_session_log.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/session_log.py backend/tests/test_session_log.py
git commit -m "session_log: SessionLogger (step-события: память + файл)"
```

---

## Task 8: Рефактор agent.py — `run_agent` (tool-calling loop)

**Files:**
- Modify: `backend/app/agent.py`
- Modify: `backend/app/prompts.py`
- Test: `backend/tests/test_agent_loop.py`

- [ ] **Step 1: Написать падающий тест** (мок OpenRouter-клиента, без сети)

`backend/tests/test_agent_loop.py`:

```python
from types import SimpleNamespace

from app import agent
from app.session_log import SessionLogger


class _FakeToolCall:
    def __init__(self, name, args):
        self.id = "call_1"
        self.type = "function"
        self.function = SimpleNamespace(name=name, arguments=args)


class _FakeClient:
    """Первый ответ — tool_call calc; второй — финальный текст."""
    def __init__(self):
        self.calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            msg = SimpleNamespace(content="", tool_calls=[_FakeToolCall("calc", '{"expr": "2*3"}')])
        else:
            msg = SimpleNamespace(content='{"ok": true}', tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def test_run_agent_executes_tool_then_returns(monkeypatch, tmp_path):
    fake = _FakeClient()
    monkeypatch.setattr(agent, "_get_client", lambda: fake)
    lg = SessionLogger("t", log_dir=tmp_path)
    lg.start_phase()
    out = agent.run_agent("sys", "user", logger=lg)
    assert out == '{"ok": true}'
    assert fake.calls == 2                     # был второй вызов после инструмента
    assert any(s.get("icon") == "🧮" for s in lg.steps)   # шаг calc залогирован
```

- [ ] **Step 2: Запустить — убедиться, что падает**

Run: `cd backend && .venv/bin/python -m pytest tests/test_agent_loop.py -q`
Expected: FAIL — `AttributeError: module 'app.agent' has no attribute 'run_agent'`

- [ ] **Step 3: Заменить `_chat` на `run_agent` в `backend/app/agent.py`**

Заменить функцию `_chat` ([backend/app/agent.py:51-65](../../../backend/app/agent.py#L51-L65)) на:

```python
from typing import Optional
from . import tools
from .session_log import SessionLogger

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
            "role": "assistant", "content": msg.content or "",
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
    return last_content
```

- [ ] **Step 4: Переключить `generate_questions` / `generate_checklist` на `run_agent`**

В [backend/app/agent.py](../../../backend/app/agent.py) изменить сигнатуры и вызовы:

В `generate_questions` заменить строку `raw = _chat(prompts.QUESTIONS_SYSTEM, user)` на:

```python
    raw = run_agent(prompts.QUESTIONS_SYSTEM, user, logger=logger)
```

и сигнатуру на:

```python
def generate_questions(round_number: int, answers: List[Dict[str, Any]],
                       logger: Optional[SessionLogger] = None) -> Dict[str, Any]:
```

В `generate_checklist` заменить `raw = _chat(prompts.CHECKLIST_SYSTEM, user, temperature=0.3)` на:

```python
    raw = run_agent(prompts.CHECKLIST_SYSTEM, user, temperature=0.3, logger=logger)
```

и сигнатуру на:

```python
def generate_checklist(answers: List[Dict[str, Any]],
                       logger: Optional[SessionLogger] = None) -> Tuple[List[Dict[str, Any]], str]:
```

- [ ] **Step 5: Дополнить промпты подсказкой про инструменты**

В [backend/app/prompts.py](../../../backend/app/prompts.py) в конец строки `QUESTIONS_SYSTEM` (перед закрывающей `)`), добавить абзац:

```python
    "\n\nУ тебя есть инструменты: calc (точная арифметика по числам клиента), "
    "kb_search (внутренняя база знаний — типовые проекты, сроки, бюджеты, интеграции, риски), "
    "web_search (интернет про упомянутую технологию). Сам решай, когда они нужны: "
    "сверься с kb_search перед уточняющими вопросами, чтобы не спрашивать очевидное."
```

В конец `CHECKLIST_SYSTEM` аналогично добавить:

```python
    " У тебя есть инструменты calc (пересчитать бюджет/сроки/команду из ответов), "
    "kb_search (типовые риски и нормы из базы знаний) и web_search. Вызывай их, когда это "
    "повышает точность чеклиста."
```

- [ ] **Step 6: Запустить — убедиться, что проходит**

Run: `cd backend && .venv/bin/python -m pytest tests/test_agent_loop.py -q`
Expected: PASS (1 passed)

- [ ] **Step 7: Прогнать все юнит-тесты**

Run: `cd backend && .venv/bin/python -m pytest -q`
Expected: PASS (все)

- [ ] **Step 8: Commit**

```bash
git add backend/app/agent.py backend/app/prompts.py backend/tests/test_agent_loop.py
git commit -m "agent: run_agent — tool-calling loop, инструменты в промптах, проброс логгера"
```

---

## Task 9: Привязать SessionLogger к сессии в store

**Files:**
- Modify: `backend/app/store.py`
- Test: `backend/tests/test_store_logger.py`

- [ ] **Step 1: Написать падающий тест**

`backend/tests/test_store_logger.py`:

```python
from app import store
from app.session_log import SessionLogger


def test_create_session_attaches_logger():
    s = store.create_session()
    assert isinstance(s["logger"], SessionLogger)
    assert s["logger"].session_id == s["session_id"]
```

- [ ] **Step 2: Запустить — убедиться, что падает**

Run: `cd backend && .venv/bin/python -m pytest tests/test_store_logger.py -q`
Expected: FAIL — `KeyError: 'logger'`

- [ ] **Step 3: Добавить logger в `create_session`**

В [backend/app/store.py](../../../backend/app/store.py) добавить импорт вверху:

```python
from .session_log import SessionLogger
```

В словарь сессии в `create_session` добавить ключ (после `"is_complete": False,`):

```python
        "logger": SessionLogger(sid),
```

- [ ] **Step 4: Запустить — убедиться, что проходит**

Run: `cd backend && .venv/bin/python -m pytest tests/test_store_logger.py -q`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/store.py backend/tests/test_store_logger.py
git commit -m "store: привязать SessionLogger к каждой сессии"
```

---

## Task 10: Mock-данные + mock STT

**Files:**
- Create: `backend/app/mock_data.py`
- Test: `backend/tests/test_mock_data.py`

- [ ] **Step 1: Написать падающий тест**

`backend/tests/test_mock_data.py`:

```python
from app.mock_data import mock_transcript, ROUND_ANSWERS


def test_three_rounds_three_answers():
    assert set(ROUND_ANSWERS.keys()) == {1, 2, 3}
    for r in (1, 2, 3):
        assert len(ROUND_ANSWERS[r]) == 3


def test_mock_transcript_returns_text():
    assert isinstance(mock_transcript(1, 0), str)
    assert mock_transcript(1, 0)


def test_mock_transcript_out_of_range_safe():
    assert isinstance(mock_transcript(99, 99), str)
```

- [ ] **Step 2: Запустить — убедиться, что падает**

Run: `cd backend && .venv/bin/python -m pytest tests/test_mock_data.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.mock_data'`

- [ ] **Step 3: Реализовать `backend/app/mock_data.py`**

```python
"""Заготовленные ответы для mock-режима (MOCK_MODE=true).
Позволяют прогонять полную сессию без записи голоса — экономия времени на тестах.
ВАЖНО: использовать только после проверки, что реальный путь (голос) работает."""
from typing import Dict, List

ROUND_ANSWERS: Dict[int, List[str]] = {
    1: [
        "Проект называется ФудФаст, это мобильное приложение доставки еды.",
        "Главная цель — доставка за тридцать минут и рост числа заказов.",
        "Сроки около трёх месяцев, бюджет примерно два миллиона рублей.",
    ],
    2: [
        "Аудитория — жители крупных городов от двадцати до сорока лет.",
        "Нужна интеграция с 1С и оплата через ЮKassa.",
        "Метрика успеха — сто заказов в день при среднем чеке семьсот рублей.",
    ],
    3: [
        "Команда с нашей стороны — продакт и тестировщик для приёмки.",
        "Дизайна пока нет, нужен с нуля.",
        "Главный риск — жёсткий дедлайн под запуск к Новому году.",
    ],
}


def mock_transcript(round_no: int, idx: int) -> str:
    answers = ROUND_ANSWERS.get(round_no, ROUND_ANSWERS[1])
    return answers[idx] if 0 <= idx < len(answers) else "Ответ не записан (mock)."
```

- [ ] **Step 4: Запустить — убедиться, что проходит**

Run: `cd backend && .venv/bin/python -m pytest tests/test_mock_data.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/mock_data.py backend/tests/test_mock_data.py
git commit -m "mock_data: заготовленные ответы + mock_transcript для mock-режима"
```

---

## Task 11: main.py — проброс логгера, mock-режим, эндпоинты /progress и /log

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/.gitignore` (корневой — добавить logs/)
- Test: `backend/tests/test_api_endpoints.py`

- [ ] **Step 1: Написать падающий тест** (через FastAPI TestClient, mock-режим — без сети для STT)

`backend/tests/test_api_endpoints.py`:

```python
import os
os.environ["MOCK_MODE"] = "true"   # до импорта settings

from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app

client = TestClient(app)


def test_health_reports_mock_and_tools():
    r = client.get("/health")
    body = r.json()
    assert body["mock_mode"] is True
    assert "tools" in body


@patch("app.agent.generate_questions", return_value={"summary": "", "questions": ["q1", "q2", "q3"]})
def test_progress_and_log_endpoints(mock_q):
    sid = client.post("/api/session/start").json()["session_id"]
    prog = client.get(f"/api/session/{sid}/progress").json()
    assert "steps" in prog and "elapsed_ms" in prog and "estimate_ms" in prog
    log = client.get(f"/api/session/{sid}/log")
    assert log.status_code == 200


def test_progress_404_for_unknown():
    assert client.get("/api/session/nope/progress").status_code == 404
```

`fastapi` тянет `starlette.testclient`, которому нужен `httpx`. Установить:
Run: `cd backend && .venv/bin/pip install "httpx>=0.27"`

- [ ] **Step 2: Запустить — убедиться, что падает**

Run: `cd backend && .venv/bin/python -m pytest tests/test_api_endpoints.py -q`
Expected: FAIL — нет ключей `mock_mode`/`tools` в /health и нет эндпоинта /progress

- [ ] **Step 3: Обновить /health**

В [backend/app/main.py](../../../backend/app/main.py) в `health()` добавить в возвращаемый словарь:

```python
        "mock_mode": settings.mock_mode,
        "tools": [s["function"]["name"] for s in __import__("app.tools", fromlist=["TOOL_SCHEMAS"]).TOOL_SCHEMAS],
```

(или добавить `from . import tools` вверху и `"tools": [s["function"]["name"] for s in tools.TOOL_SCHEMAS]`)

- [ ] **Step 4: Прокинуть logger в агента и добавить mock-режим в submit/start/transcribe**

В `start_session` заменить вызов на:

```python
    s["logger"].start_phase(estimate_ms=20000)
    s["logger"].step("Готовлю вопросы интервью", icon="📝")
    result = agent.generate_questions(1, [], logger=s["logger"])
```

В `transcribe_one` — если mock, не гонять Whisper:

```python
    if settings.mock_mode:
        return {"transcript": "Демо-ответ (mock-режим)."}
    data = await audio_file.read()
    return {"transcript": transcriber.transcribe(data)}
```

В `submit_answers` заменить блок транскрипции и вызовы агента:

```python
    s["logger"].start_phase(estimate_ms=45000)
    questions = s["questions"]
    transcripts = []
    for i, f in enumerate(audio_files):
        if settings.mock_mode:
            from .mock_data import mock_transcript
            transcripts.append(mock_transcript(s["current_round"], i))
        else:
            s["logger"].step("Распознаю речь", icon="🎙")
            transcripts.append(transcriber.transcribe(await f.read()))
    for q, t in zip(questions, transcripts):
        s["answers"].append({
            "round": s["current_round"], "question": q, "transcript": t,
            "sentiment": sentiment.analyze(t),
        })

    if s["current_round"] < settings.max_rounds:
        s["current_round"] += 1
        s["logger"].step("Готовлю уточняющие вопросы", icon="📝")
        result = agent.generate_questions(s["current_round"], s["answers"], logger=s["logger"])
        ...
```

(в ветке последнего раунда):

```python
    s["logger"].step("Собираю итоговый чеклист", icon="📝")
    items, summary = agent.generate_checklist(s["answers"], logger=s["logger"])
```

- [ ] **Step 5: Добавить эндпоинты /progress и /log**

В конец [backend/app/main.py](../../../backend/app/main.py):

```python
@app.get("/api/session/{session_id}/progress")
def get_progress(session_id: str):
    s = store.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    return s["logger"].progress()


@app.get("/api/session/{session_id}/log")
def get_log(session_id: str):
    s = store.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    return Response(content=s["logger"].read_log() or "(лог пуст)",
                    media_type="text/plain; charset=utf-8")
```

- [ ] **Step 6: Игнорировать logs/ в git**

В корневой `.gitignore` добавить строку:

```
logs/
backend/logs/
```

- [ ] **Step 7: Запустить — убедиться, что проходит**

Run: `cd backend && .venv/bin/python -m pytest tests/test_api_endpoints.py -q`
Expected: PASS (3 passed)

- [ ] **Step 8: Прогнать все юнит-тесты**

Run: `cd backend && .venv/bin/python -m pytest -q`
Expected: PASS (все)

- [ ] **Step 9: Commit**

```bash
git add backend/app/main.py .gitignore backend/tests/test_api_endpoints.py
git commit -m "api: проброс логгера, mock-режим, эндпоинты /progress и /log"
```

---

## Task 12: Ручная проверка бэкенда целиком (реальный путь + mock)

**Files:** (без изменений кода — верификация)

- [ ] **Step 1: Реальный путь (голос) — убедиться, что всё работает ДО включения mock**

Run: `cd backend && MOCK_MODE=false .venv/bin/uvicorn app.main:app --port 7860 &` затем `sleep 5 && curl -s localhost:7860/health | python -m json.tool`
Expected: `whisper_loaded: true`, `mock_mode: false`, `tools: ["calc","kb_search","web_search"]`

- [ ] **Step 2: Mock-путь — полная сессия без аудио**

Run (mock-режим, реальный LLM с инструментами):
```bash
cd backend && pkill -f uvicorn; MOCK_MODE=true .venv/bin/uvicorn app.main:app --port 7860 & sleep 8
SID=$(curl -s -XPOST localhost:7860/api/session/start | python -c "import sys,json;print(json.load(sys.stdin)['session_id'])")
# отправляем три пустых "аудио" — в mock они игнорируются
curl -s -XPOST localhost:7860/api/session/$SID/submit -F "audio_files=@/dev/null" -F "audio_files=@/dev/null" -F "audio_files=@/dev/null" -F "question_ids=q1_0,q1_1,q1_2" >/dev/null
curl -s localhost:7860/api/session/$SID/progress | python -m json.tool
curl -s localhost:7860/api/session/$SID/log
```
Expected: в `/progress` есть шаги; в `/log` видны строки с tool-вызовами (например `🧮`/`🗂`), если модель ими воспользовалась.

- [ ] **Step 3: Остановить сервер**

Run: `pkill -f uvicorn`

- [ ] **Step 4: Зафиксировать наблюдения** (если нашлись баги — чинить до фронта). Коммит не требуется, если кода не меняли.

---

## Task 13: Frontend — типы и API-клиент для прогресса/лога

**Files:**
- Modify: `frontend/lib/types.ts`
- Modify: `frontend/lib/api.ts`

- [ ] **Step 1: Добавить типы прогресса**

В конец [frontend/lib/types.ts](../../../frontend/lib/types.ts):

```typescript
export interface ProgressStep {
  ts: number;
  icon: string;
  text: string;
}

export interface ProgressResponse {
  steps: ProgressStep[];
  elapsed_ms: number;
  estimate_ms: number;
}
```

- [ ] **Step 2: Добавить вызовы API**

В конец [frontend/lib/api.ts](../../../frontend/lib/api.ts):

```typescript
import type { ProgressResponse } from "./types";

export async function getProgress(sessionId: string): Promise<ProgressResponse> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/progress`);
  if (!res.ok) throw new Error(`progress failed: ${res.status}`);
  return res.json();
}

export async function getLog(sessionId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/log`);
  if (!res.ok) throw new Error(`log failed: ${res.status}`);
  return res.text();
}
```

(перенести `import type { ProgressResponse }` к существующему импорту типов в начале файла, чтобы не дублировать import-блоки.)

- [ ] **Step 3: Проверить сборку типов**

Run: `cd frontend && npx tsc --noEmit`
Expected: без ошибок

- [ ] **Step 4: Commit**

```bash
git add frontend/lib/types.ts frontend/lib/api.ts
git commit -m "frontend(api): типы ProgressResponse + getProgress/getLog"
```

---

## Task 14: Frontend — ProgressPanel (шаги + таймер + оценка)

**Files:**
- Create: `frontend/components/ProgressPanel.tsx`

- [ ] **Step 1: Создать компонент**

`frontend/components/ProgressPanel.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { getProgress } from "@/lib/api";
import type { ProgressStep } from "@/lib/types";

const FALLBACK: ProgressStep[] = [
  { ts: 0, icon: "🎙", text: "Распознаю речь" },
  { ts: 0, icon: "🧠", text: "Анализирую ответы" },
  { ts: 0, icon: "📝", text: "Готовлю результат" },
];

export function ProgressPanel({
  sessionId,
  title,
}: {
  sessionId: string;
  title: string;
}) {
  const [steps, setSteps] = useState<ProgressStep[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [estimate, setEstimate] = useState(45000);

  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try {
        const p = await getProgress(sessionId);
        if (!alive) return;
        setSteps(p.steps);
        setElapsed(p.elapsed_ms);
        if (p.estimate_ms) setEstimate(p.estimate_ms);
      } catch {
        /* во время ожидания сеть может моргать — игнорируем */
      }
    };
    poll();
    const id = setInterval(poll, 600);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [sessionId]);

  const shown = steps.length ? steps : FALLBACK;
  const sec = Math.floor(elapsed / 1000);
  const estSec = Math.round(estimate / 1000);

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-4 text-center">
      <Loader2 className="h-12 w-12 animate-spin text-indigo-600" />
      <h2 className="mt-6 text-xl font-semibold text-slate-800">{title}</h2>

      {/* Закон №2: известное время — оценка + счётчик */}
      <p className="mt-2 text-sm text-slate-500">
        Прошло {sec} с · обычно занимает ≈{estSec} с
      </p>

      {/* Закон №3: объяснённое время — реальные шаги агента */}
      <ul className="mt-4 w-full space-y-1 text-left text-sm text-slate-600">
        {shown.map((s, i) => (
          <li key={i} className="flex items-center gap-2">
            <span>{s.icon}</span>
            <span>{s.text}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 2: Проверить сборку**

Run: `cd frontend && npx tsc --noEmit`
Expected: без ошибок

- [ ] **Step 3: Commit**

```bash
git add frontend/components/ProgressPanel.tsx
git commit -m "frontend: ProgressPanel — шаги агента + таймер + оценка (законы №2,3)"
```

---

## Task 15: Frontend — Interview: «✓ принято» + использование ProgressPanel

**Files:**
- Modify: `frontend/components/screens/Interview.tsx`

- [ ] **Step 1: Заменить заглушку `Processing` на ProgressPanel**

В [frontend/components/screens/Interview.tsx](../../../frontend/components/screens/Interview.tsx):

Импорт вверху добавить:
```tsx
import { ProgressPanel } from "@/components/ProgressPanel";
```

Заменить блок `if (submitting) { return <Processing .../>; }` (строки ~55-57) на:
```tsx
  if (submitting) {
    const last = round === maxRounds;
    return (
      <ProgressPanel
        sessionId={sessionId}
        title={last ? "Собираю чеклист…" : "Анализирую ваши ответы…"}
      />
    );
  }
```

Удалить старую функцию `Processing` (строки ~119-137) и неиспользуемый импорт `Loader2` из этого файла.

- [ ] **Step 2: Закон №1 — мгновенный «✓ Ответ принят»**

В `QuestionCard` ответ уже отмечается (`answered={!!blobs[q.id]}`). Усилить визуально: под счётчиком «Отвечено N/M» добавить строку подтверждения последнего действия. После блока с `Progress` (после строки ~72) вставить:

```tsx
      {answeredCount > 0 && (
        <p className="mb-4 text-center text-sm font-medium text-emerald-600">
          ✓ Ответ принят — можно переходить к следующему вопросу
        </p>
      )}
```

- [ ] **Step 3: Проверить сборку**

Run: `cd frontend && npx tsc --noEmit`
Expected: без ошибок

- [ ] **Step 4: Ручная проверка в браузере**

Run: запустить фронт (`cd frontend && npm run dev`) и бэк (mock-режим), пройти раунд.
Expected: после записи — зелёное «✓ Ответ принят»; при отправке — панель с таймером и шагами агента (🗂/🧮/📝).

- [ ] **Step 5: Commit**

```bash
git add frontend/components/screens/Interview.tsx
git commit -m "frontend(interview): ProgressPanel + мгновенное '✓ принято' (закон №1)"
```

---

## Task 16: Frontend — LogViewer (просмотр лога сессии)

**Files:**
- Create: `frontend/components/LogViewer.tsx`
- Modify: `frontend/components/screens/Results.tsx`

- [ ] **Step 1: Создать компонент**

`frontend/components/LogViewer.tsx`:

```tsx
"use client";

import { useState } from "react";
import { getLog } from "@/lib/api";

export function LogViewer({ sessionId }: { sessionId: string }) {
  const [open, setOpen] = useState(false);
  const [log, setLog] = useState("");

  async function toggle() {
    if (!open && !log) {
      try {
        setLog(await getLog(sessionId));
      } catch {
        setLog("(не удалось загрузить лог)");
      }
    }
    setOpen((v) => !v);
  }

  return (
    <div className="mt-6">
      <button
        onClick={toggle}
        className="text-sm font-medium text-slate-500 underline hover:text-slate-700"
      >
        {open ? "Скрыть лог сессии" : "Показать лог сессии (что делал агент)"}
      </button>
      {open && (
        <pre className="mt-2 max-h-80 overflow-auto rounded-lg bg-slate-900 p-4 text-xs text-slate-100">
          {log || "(лог пуст)"}
        </pre>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Встроить в экран результатов**

Открыть [frontend/components/screens/Results.tsx](../../../frontend/components/screens/Results.tsx), импортировать `LogViewer` и отрендерить `<LogViewer sessionId={sessionId} />` в подвале результатов (Results должен иметь доступ к `sessionId`; если его там нет — прокинуть проп из родителя `page.tsx`).

- [ ] **Step 3: Проверить сборку**

Run: `cd frontend && npx tsc --noEmit`
Expected: без ошибок

- [ ] **Step 4: Commit**

```bash
git add frontend/components/LogViewer.tsx frontend/components/screens/Results.tsx
git commit -m "frontend: LogViewer — раскрывающийся лог сессии на экране результатов"
```

---

## Task 17: Frontend — демо-режим (mockup без записи)

**Files:**
- Modify: `frontend/components/screens/Interview.tsx`

- [ ] **Step 1: Добавить демо-тоггл**

В [frontend/components/screens/Interview.tsx](../../../frontend/components/screens/Interview.tsx) включить демо-кнопку, видимую только когда `process.env.NEXT_PUBLIC_DEMO_MODE === "true"`. Она автозаполняет все ответы пустыми blob'ами (в mock-режиме бэк всё равно их игнорирует) и сразу сабмитит:

После блока с кнопкой Send (перед закрывающим `</div>` sticky-блока) добавить:

```tsx
        {process.env.NEXT_PUBLIC_DEMO_MODE === "true" && (
          <Button
            variant="outline"
            className="mt-2 w-full"
            disabled={submitting}
            onClick={() => {
              const filled: Record<string, Blob> = {};
              questions.forEach((q) => {
                filled[q.id] = new Blob([], { type: "audio/webm" });
              });
              setBlobs(filled);
              setTimeout(handleSubmit, 0);
            }}
          >
            ⚡ Демо: заполнить ответы автоматически
          </Button>
        )}
```

(`Button` уже импортирован; `variant="outline"` поддержан в [frontend/components/ui/button.tsx](../../../frontend/components/ui/button.tsx) — проверить и при отсутствии использовать существующий вариант.)

- [ ] **Step 2: Проверить сборку**

Run: `cd frontend && npx tsc --noEmit`
Expected: без ошибок

- [ ] **Step 3: Ручная проверка**

Run: `cd frontend && NEXT_PUBLIC_DEMO_MODE=true npm run dev` (бэк в `MOCK_MODE=true`).
Expected: появляется кнопка «⚡ Демо…», по клику сессия проходит без записи голоса, виден прогресс и лог.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/screens/Interview.tsx
git commit -m "frontend(interview): демо-режим — автозаполнение ответов (mockup data)"
```

---

## Task 18: Документация деплоя (HF Secrets/Variables) + финальный прогон

**Files:**
- Modify: `README.md` (или `backend/README.md`)

- [ ] **Step 1: Дописать в README блок про новые ENV**

Добавить раздел:

```markdown
## Инструменты агента и режимы

Агент сам решает, когда звать инструменты (function calling, minimax-m3):
- `calc` — арифметика по бюджету/срокам/команде;
- `kb_search` — внутренняя база знаний `backend/app/knowledge_base.md`;
- `web_search` — Tavily (нужен секрет `TAVILY_API_KEY`, иначе отключён).

### ENV: секреты vs переменные
- Секреты (HF Space → Secrets): `OPENROUTER_API_KEY`, `TAVILY_API_KEY`.
- Переменные (HF Space → Variables): `MOCK_MODE` (true/false), `LLM_MODEL`,
  `AGENT_MAX_TOOL_ITERS`, `KB_PATH`, `ALLOWED_ORIGINS`.

`MOCK_MODE=true` подставляет заготовленные ответы вместо распознавания голоса
(для быстрого тестирования). Включать только после проверки реального пути.

UX: на ожидании показываются реальные шаги агента + таймер; на экране результатов —
раскрывающийся лог сессии.
```

- [ ] **Step 2: Финальный прогон всех бэкенд-тестов**

Run: `cd backend && .venv/bin/python -m pytest -q`
Expected: PASS (все)

- [ ] **Step 3: Финальная проверка типов фронта**

Run: `cd frontend && npx tsc --noEmit`
Expected: без ошибок

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: инструменты агента, ENV (секреты/переменные), mock-режим, лог"
```

---

## Self-Review (выполнено при написании плана)

- **Покрытие спеки:** агентность (T3–T8), UX законы №1/2/3 (T14,T15), mock (T1,T10,T17), логирование (T7,T11,T16), ENV секреты/переменные (T1,T18). ✔
- **Плейсхолдеры:** код приведён в каждом шаге; «прокинуть sessionId в Results» (T16) — единственная точка, зависящая от текущей структуры `page.tsx`, помечена явно.
- **Согласованность имён:** `run_agent`, `SessionLogger.step/start_phase/progress/read_log`, `dispatch`, `TOOL_SCHEMAS`, `getProgress/getLog`, `ProgressResponse/ProgressStep` — едины во всех задачах.
- **Порядок:** инфраструктура → инструменты → логгер → агент → store → mock → api → ручная проверка бэка (T12, перед фронтом) → фронт. Реальный путь проверяется до опоры на mock (ограничение пользователя соблюдено).
