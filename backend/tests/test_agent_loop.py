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


def test_run_agent_works_without_logger(monkeypatch):
    fake = _FakeClient()
    monkeypatch.setattr(agent, "_get_client", lambda: fake)
    assert agent.run_agent("sys", "user") == '{"ok": true}'


class _AlwaysToolClient:
    """Модель бесконечно зовёт инструмент и никогда не даёт финальный ответ."""
    def __init__(self):
        self.calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls += 1
        msg = SimpleNamespace(content="думаю...",
                              tool_calls=[_FakeToolCall("calc", '{"expr": "1+1"}')])
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def test_run_agent_exhaustion_returns_last_content_and_warns(monkeypatch, tmp_path):
    fake = _AlwaysToolClient()
    monkeypatch.setattr(agent, "_get_client", lambda: fake)
    lg = SessionLogger("t", log_dir=tmp_path)
    lg.start_phase()
    out = agent.run_agent("sys", "user", logger=lg)
    assert fake.calls == agent.settings.agent_max_tool_iters   # не зациклились
    assert out == "думаю..."                                   # вернулся последний контент
    assert any(s.get("icon") == "⚠" for s in lg.steps)         # предупреждение о лимите


class _BadArgsClient:
    """Первый ответ — tool_call с битым JSON в аргументах; второй — финал."""
    def __init__(self):
        self.calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            msg = SimpleNamespace(content="", tool_calls=[_FakeToolCall("calc", "{не json")])
        else:
            msg = SimpleNamespace(content="готово", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def test_run_agent_handles_malformed_tool_args(monkeypatch, tmp_path):
    fake = _BadArgsClient()
    monkeypatch.setattr(agent, "_get_client", lambda: fake)
    lg = SessionLogger("t", log_dir=tmp_path)
    lg.start_phase()
    out = agent.run_agent("sys", "user", logger=lg)   # не должно падать
    assert out == "готово"
    assert fake.calls == 2
