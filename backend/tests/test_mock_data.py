from app.mock_data import mock_transcript, ROUND_ANSWERS


def test_three_rounds_three_answers():
    assert set(ROUND_ANSWERS.keys()) == {1, 2, 3}
    for r in (1, 2, 3):
        assert len(ROUND_ANSWERS[r]) == 3


def test_mock_transcript_returns_text():
    assert isinstance(mock_transcript(1, 0), str)
    assert mock_transcript(1, 0)


def test_mock_transcript_out_of_range_safe():
    assert isinstance(mock_transcript(99, 99), str)
