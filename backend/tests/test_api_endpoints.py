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


@patch("app.sentiment.sentiment.analyze",
       return_value={"label": "neutral", "score": 0.0, "emoji": "😐", "ru": "нейтральный"})
@patch("app.agent.generate_questions",
       return_value={"summary": "s", "questions": ["q1", "q2", "q3"]})
def test_submit_mock_mode_uses_canned_answers(mock_q, mock_sent, monkeypatch):
    from app.mock_data import ROUND_ANSWERS

    monkeypatch.setattr(config.settings, "mock_mode", True)
    sid = client.post("/api/session/start").json()["session_id"]
    files = [("audio_files", (f"a{i}.webm", b"", "audio/webm")) for i in range(3)]
    r = client.post(f"/api/session/{sid}/submit", files=files,
                    data={"question_ids": "q1_0,q1_1,q1_2"})
    assert r.status_code == 200
    # В mock-режиме транскрипты берутся из заготовок, а не из Whisper.
    answers = client.get(f"/api/session/{sid}/results").json()["answers"]
    assert [a["transcript"] for a in answers] == ROUND_ANSWERS[1]
    # И это видно в логе сессии.
    assert "заготовленный ответ" in client.get(f"/api/session/{sid}/log").text
