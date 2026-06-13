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
