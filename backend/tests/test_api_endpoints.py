from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app import config

client = TestClient(app)


def test_health_reports_mock_and_tools(monkeypatch):
    monkeypatch.setattr(config.settings, "mock_mode", True)
    body = client.get("/health").json()
    assert body["mock_mode"] is True
    assert set(body["tools"]) >= {"calc", "kb_search", "web_search"}


@patch("app.agent.generate_questions",
       return_value={"summary": "", "questions": ["q1", "q2", "q3"]})
def test_progress_and_log_endpoints(mock_q):
    sid = client.post("/api/session/start").json()["session_id"]
    prog = client.get(f"/api/session/{sid}/progress").json()
    assert "steps" in prog and "elapsed_ms" in prog and "estimate_ms" in prog
    assert client.get(f"/api/session/{sid}/log").status_code == 200


def test_progress_404_for_unknown():
    assert client.get("/api/session/nope/progress").status_code == 404
