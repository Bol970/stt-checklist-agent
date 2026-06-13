from app import store
from app.session_log import SessionLogger


def test_create_session_attaches_logger():
    s = store.create_session()
    assert isinstance(s["logger"], SessionLogger)
    assert s["logger"].session_id == s["session_id"]
