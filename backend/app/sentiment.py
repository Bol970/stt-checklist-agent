"""Вторая HF-модель: анализ тональности ответов клиента (ruBERT).
Модель: cointegrated/rubert-tiny-sentiment-balanced (3 класса, быстрая на CPU).
Это «эксперимент с другой моделью на Hugging Face» — отдельно от Whisper и LLM."""
from typing import Dict

from .config import settings

_RU = {
    "positive": ("🙂", "позитивный"),
    "neutral": ("😐", "нейтральный"),
    "negative": ("🙁", "негативный"),
}


class SentimentAnalyzer:
    def __init__(self) -> None:
        self._pipe = None

    @property
    def loaded(self) -> bool:
        return self._pipe is not None

    def load(self):
        if self._pipe is None:
            from transformers import pipeline
            self._pipe = pipeline(
                "text-classification",
                model=settings.sentiment_model,
                device=-1,
                truncation=True,
                max_length=256,
            )
        return self._pipe

    @staticmethod
    def _norm(label: str) -> str:
        m = {
            "positive": "positive", "neutral": "neutral", "negative": "negative",
            "POSITIVE": "positive", "NEUTRAL": "neutral", "NEGATIVE": "negative",
            "LABEL_0": "negative", "LABEL_1": "neutral", "LABEL_2": "positive",
        }
        return m.get(label, label.lower())

    def analyze(self, text: str) -> Dict:
        text = (text or "").strip()
        if not text:
            return {"label": "neutral", "score": 0.0, "emoji": "😐", "ru": "нейтральный"}
        try:
            self.load()
            r = self._pipe(text)[0]
            label = self._norm(r["label"])
        except Exception:
            label = "neutral"
            r = {"score": 0.0}
        emoji, ru = _RU.get(label, ("😐", label))
        return {"label": label, "score": round(float(r.get("score", 0.0)), 3), "emoji": emoji, "ru": ru}


sentiment = SentimentAnalyzer()
