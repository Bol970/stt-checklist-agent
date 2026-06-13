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
