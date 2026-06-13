"""Инструменты агента: calc / kb_search / web_search.
Каждый инструмент возвращает dict; ошибки — это {"error": "..."} (агент не падает).
Решение о вызове принимает модель (function calling, tool_choice="auto")."""
import ast
import operator
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .config import settings

# --- calc: безопасная арифметика на ast (без eval) -------------------------
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


_MAX_EXPONENT = 100  # защита от DoS: 2**1000000 заморозил бы ответ


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > _MAX_EXPONENT:
            raise ValueError(f"exponent too large (> {_MAX_EXPONENT})")
        return _OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("unsupported expression")


def calc(expr: str) -> Dict[str, Any]:
    """Считает арифметическое выражение. Разрешены только числа и + - * / // % ** ( )."""
    if len(expr) > 200:
        return {"error": "expression too long"}
    try:
        return {"result": _eval_node(ast.parse(expr, mode="eval"))}
    except Exception as e:
        return {"error": f"cannot evaluate '{expr}': {e}"}


# --- kb_search: keyword-поиск по секциям knowledge_base.md ------------------
_kb_cache: Optional[List[Tuple[str, str]]] = None  # в тестах сбрасывать в None при смене kb_path


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
    words = [w.lower() for w in re.findall(r"\w+", query) if len(w) >= 2]
    scored = []
    for title, body in _load_kb():
        hay = (title + " " + body).lower()
        score = sum(hay.count(w) for w in words)
        if score:
            scored.append((score, title, body))
    scored.sort(key=lambda x: x[0], reverse=True)
    return {"snippets": [{"title": t, "text": b} for _, t, b in scored[:top_k]]}


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
            {"title": r.get("title", ""), "url": r.get("url", ""),
             "snippet": (r.get("content") or "")[:300]}
            for r in resp.get("results", [])
        ]}
    except Exception as e:
        return {"error": f"web search failed: {e}"}


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
