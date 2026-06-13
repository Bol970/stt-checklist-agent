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
