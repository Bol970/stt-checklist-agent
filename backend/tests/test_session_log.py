from pathlib import Path

from app.session_log import SessionLogger


def test_logger_records_steps_and_progress(tmp_path):
    lg = SessionLogger("abc123", log_dir=tmp_path)
    lg.start_phase(estimate_ms=45000)
    lg.step("Распознаю речь", icon="🎙")
    lg.step("Считаю бюджет", icon="🧮", tool="calc")
    prog = lg.progress()
    assert prog["estimate_ms"] == 45000
    assert [s["text"] for s in prog["steps"]] == ["Распознаю речь", "Считаю бюджет"]
    assert prog["elapsed_ms"] >= 0


def test_logger_writes_file(tmp_path):
    lg = SessionLogger("abc123", log_dir=tmp_path)
    lg.step("привет", icon="•")
    log_text = (tmp_path / "session-abc123.log").read_text(encoding="utf-8")
    assert "привет" in log_text


def test_start_phase_resets_live_steps_but_keeps_file(tmp_path):
    lg = SessionLogger("s", log_dir=tmp_path)
    lg.step("раунд 1")
    lg.start_phase(estimate_ms=1000)
    lg.step("раунд 2")
    assert [s["text"] for s in lg.progress()["steps"]] == ["раунд 2"]
    assert "раунд 1" in (tmp_path / "session-s.log").read_text(encoding="utf-8")
