# Дизайн: агентность (инструменты) + UX восприятия времени

Дата: 2026-06-13
Проект: STT Checklist Agent (backend FastAPI + Whisper + OpenRouter `minimax/minimax-m3`, frontend Next.js)

## Цель

1. Сделать агента **настоящим tool-using** — он сам решает, когда вызвать инструмент (function calling), а не идёт по фиксированному конвейеру.
2. Улучшить **UX** по трём законам восприятия времени.
3. Добавить **mockup-режим** для тестирования без перезаписи голоса.
4. Добавить **логирование** сессии + простой просмотрщик.
5. Навести порядок в **ENV**: секреты vs переменные.

## Сквозная идея

Один поток «шагов» (step-events) обслуживает и **прозрачность UX (закон №3)**, и **логирование**. Агент-цикл на каждом действии пишет событие → оно идёт в лог-файл сессии и в эндпоинт прогресса, который опрашивает фронт. Один механизм, не два.

## Подтверждённые проверки

- `minimax/minimax-m3` через OpenRouter **поддерживает function calling** (проверено: на запрос про бюджет модель сама вернула `calc {"expr": "5 * 200000 * 3"}` при `tool_choice="auto"`).

## Подтверждённые решения

1. **Tavily — напрямую через Python SDK/REST как function-tool**, НЕ через MCP. Требование «агент сам решает» выполняется function-calling'ом; деплой на HF остаётся простым. Без ключа инструмент деградирует мягко (агент работает без веб-поиска).
2. **Прогресс — polling `GET /api/session/{id}/progress` + лог**, НЕ SSE. Надёжнее на HF, переиспользует логирование.
3. **КБ** — черновой `knowledge_base.md` для агентства-разработки, пользователь правит позже.

---

## 1. Агентность: tool-calling loop

### Ядро
Заменить фиксированный `_chat()` ([backend/app/agent.py:51](../../../backend/app/agent.py#L51)) на цикл:

```
run_agent(system, user, logger, temperature, max_iters):
    messages = [system, user]
    for i in range(max_iters):
        resp = client.chat.completions.create(model, messages, tools=TOOLS, tool_choice="auto", temperature)
        msg = resp.choices[0].message
        if msg.tool_calls:
            messages.append(assistant tool-call msg)
            for tc in msg.tool_calls:
                result = dispatch(tc.function.name, json.loads(tc.function.arguments))
                logger.step(tool=tc.name, args=..., result_preview=...)
                messages.append({"role":"tool","tool_call_id":tc.id,"content":json.dumps(result)})
            continue
        return msg.content   # финальный JSON
    # лимит итераций → вернуть последний content / fallback
```

`generate_questions` и `generate_checklist` вызывают `run_agent` вместо `_chat`. Существующий `_extract_json` и fallback-логика сохраняются.

### Инструменты — `backend/app/tools.py`
Реестр: `{name: (json_schema, python_callable)}`. Диспетчер ловит исключения инструмента и возвращает `{"error": "..."}` (агент не падает).

- **`calc(expr: str)`** — детерминированная арифметика. БЕЗ `eval`: парсер на `ast` с белым списком узлов (числа, `+ - * / // % **`, скобки, унарный минус). Возвращает `{"result": <number>}` или `{"error": ...}`.
- **`kb_search(query: str)`** — поиск по `knowledge_base.md`. Реализация: разбить КБ на секции по заголовкам, вернуть топ-секции по совпадению ключевых слов (простой scoring, без внешних либ). Возвращает `{"snippets": [...]}`.
- **`web_search(query: str)`** — Tavily SDK/REST. Если `TAVILY_API_KEY` пуст → `{"error": "web search disabled"}`. Иначе топ-N результатов `{"results": [{title, url, snippet}]}`.

Системные промпты ([prompts.py](../../../backend/app/prompts.py)) дополняются строкой о доступных инструментах и когда их уместно звать (бюджет/сроки → calc; упомянута технология/интеграция → web_search; перед вопросами свериться с КБ → kb_search). Решение о вызове остаётся за моделью.

### КБ — `backend/app/knowledge_base.md`
Небольшой осмысленный файл: чем занимается компания, типовые типы проектов, стандартные риски, вилки бюджета/сроков, заметки по частым интеграциям (1С, оплаты, CRM). Агент читает через `kb_search`, чтобы задавать умнее вопросы и не переспрашивать известное.

---

## 2. UX: три закона восприятия времени

### Бэкенд
Шаги генерируются агент-циклом и STT-этапом (см. SessionLogger). Эндпоинт `GET /api/session/{id}/progress` → `{steps: [{ts, icon, text}], elapsed_ms, estimate_ms}`.

### Фронт
- **Закон №1 (занятое/принятое):** сразу после записи ответа — «✓ Ответ принят», оптимистичный переход, без пустого спиннера.
- **Закон №2 (известное):** оценка ожидания (`estimate_ms`, напр. «≈45 сек») + живой счётчик прошедшего времени.
- **Закон №3 (объяснённое):** во время ожидания опрос `/progress` (~500 мс) и рендер реальных шагов: «🎙 Распознаю речь…», «🗂 Смотрю базу знаний…», «🧮 Считаю бюджет…», «🔎 Ищу в вебе…», «📝 Собираю чеклист…». Пока реальных шагов нет — дефолтные «воображаемые» шаги.

Затрагиваются [Interview.tsx](../../../frontend/components/screens/Interview.tsx), [lib/api.ts](../../../frontend/lib/api.ts), при необходимости новый компонент `ProgressPanel`.

---

## 3. Mockup data

- **Выключен по умолчанию** (ограничение: не включать, пока не убедились, что реальный путь работает).
- Переключатель — переменная `MOCK_MODE: bool` (env/HF Variable). `true` → STT не гоняется, ответы берутся из `backend/app/mock_data.py` (набор заготовленных транскриптов по раундам). `false` → обычный путь.
- На фронте — кнопка «Демо-режим» (через `NEXT_PUBLIC_DEMO_MODE`): подставляет заготовленные ответы, минуя запись.
- Цель: тестировать операции над данными без 10 перезаписей, экономия времени/денег.

---

## 4. Логирование — `backend/app/session_log.py`

`SessionLogger`:
- На сессию: список step-событий в памяти + дозапись в `logs/session-{id}.log` (текст, с таймстемпами).
- Пишет: STT-результаты, каждый tool-call (имя + аргументы + превью результата), сырые ответы LLM, тайминги этапов.
- `GET /api/session/{id}/log` → текст лога. Фронт — простая панель-просмотрщик (раскрывается на экране результатов/интервью).

Тот же поток событий питает `/progress` (раздел 2). Каталог `logs/` — в `.gitignore`.

---

## 5. ENV: секреты vs переменные

- **Секреты** (HF *Secrets*, локально gitignored `backend/.env`, не в git): `OPENROUTER_API_KEY`, `TAVILY_API_KEY`.
- **Переменные** (HF *Variables*, дефолты коммитятся): `MOCK_MODE`, `LLM_MODEL`, `AGENT_MAX_TOOL_ITERS`, `KB_PATH`, `ALLOWED_ORIGINS`.
- `MOCK_MODE` парсится в `bool` явно в [config.py](../../../backend/app/config.py).
- Фронт: несекретный конфиг через `NEXT_PUBLIC_*`. Опционально — число «свободных слотов» на лендинге как env-переменная (менять без правок кода).

---

## Карта модулей

| Файл | Изменение |
|---|---|
| `backend/app/tools.py` | **новый** — calc / kb_search / web_search + схемы + диспетчер |
| `backend/app/agent.py` | рефактор `_chat`→`run_agent` (tool loop) + проброс логгера |
| `backend/app/session_log.py` | **новый** — SessionLogger (память + файл, step-события) |
| `backend/app/knowledge_base.md` | **новый** — КБ компании (черновик) |
| `backend/app/mock_data.py` | **новый** — заготовленные ответы + mock STT |
| `backend/app/main.py` | эндпоинты `/progress`, `/log`; mock-режим; проброс логгера |
| `backend/app/config.py` | `tavily_api_key`, `mock_mode`, `kb_path`, `agent_max_tool_iters` |
| `backend/app/store.py` | привязать SessionLogger к сессии |
| `backend/requirements.txt` | `tavily-python` (опционально) |
| `backend/.env.example` | новые секреты/переменные + комментарий о разделении |
| `frontend/components/screens/Interview.tsx` | ProgressPanel, «✓ принято», таймер |
| `frontend/lib/api.ts` | вызовы `/progress`, `/log` |
| `frontend/components/...` | ProgressPanel, LogViewer, демо-тоггл |

## Тестирование

- `calc`: юнит-тесты парсера (корректные выражения + отказ на небезопасных).
- `kb_search`: возвращает релевантные секции на ключевые запросы.
- `run_agent`: мок OpenRouter-ответа с tool_call → проверка, что инструмент вызван и результат скормлен обратно.
- e2e ([test_e2e.py](../../../backend/test_e2e.py)) расширить: mock-режим прогоняет полную сессию без аудио; `/progress` и `/log` отдают данные.
- Принцип: сперва убедиться, что реальный путь (голос) работает, потом полагаться на mock.

## Деплой

- HF Space: добавить Secret `TAVILY_API_KEY` (опц.), Variable `MOCK_MODE=false`.
- `logs/` эфемерен на HF — ок для жизни сессии.
- Vercel: `NEXT_PUBLIC_*` для несекретного конфига.

## Вне скоупа (YAGNI)

- Полноценный MCP-клиент в бэкенде.
- SSE/websockets.
- Персистентная БД сессий (остаётся in-memory + лог-файлы).
- Векторный поиск по КБ (достаточно keyword-scoring).
