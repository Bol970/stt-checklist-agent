import sys
import types

from app import tools


def test_web_search_disabled_without_key(monkeypatch):
    monkeypatch.setattr(tools.settings, "tavily_api_key", "")
    out = tools.web_search("что такое 1С")
    assert "error" in out
    assert "disabled" in out["error"]


def _fake_tavily_module(search_impl):
    """Подсовывает фейковый пакет `tavily` с TavilyClient.search = search_impl."""
    mod = types.ModuleType("tavily")

    class FakeClient:
        def __init__(self, api_key=None):
            pass

        def search(self, **kwargs):
            return search_impl(**kwargs)

    mod.TavilyClient = FakeClient
    return mod


def test_web_search_happy_path(monkeypatch):
    monkeypatch.setattr(tools.settings, "tavily_api_key", "test-key")
    fake = _fake_tavily_module(lambda **kw: {
        "results": [{"title": "1С", "url": "https://1c.ru", "content": "x" * 500}]
    })
    monkeypatch.setitem(sys.modules, "tavily", fake)
    out = tools.web_search("1С")
    assert out["results"][0]["title"] == "1С"
    assert out["results"][0]["url"] == "https://1c.ru"
    assert len(out["results"][0]["snippet"]) == 300  # обрезано до 300


def test_web_search_handles_failure(monkeypatch):
    monkeypatch.setattr(tools.settings, "tavily_api_key", "test-key")

    def boom(**kw):
        raise RuntimeError("network down")

    monkeypatch.setitem(sys.modules, "tavily", _fake_tavily_module(boom))
    out = tools.web_search("1С")
    assert "error" in out
    assert "failed" in out["error"]
