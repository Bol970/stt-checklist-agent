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
