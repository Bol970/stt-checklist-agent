"""Локальный тест STT: gTTS синтезирует речь -> webm (как из браузера) -> Whisper."""
import subprocess
import tempfile

from gtts import gTTS

from app.transcription import transcriber

PHRASES = [
    "Мы делаем мобильное приложение для доставки еды с интеграцией црм.",
    "Бюджет пока не определён, запустить хотим за три месяца.",
]


def make_webm(text: str) -> bytes:
    mp3 = tempfile.mktemp(suffix=".mp3")
    webm = tempfile.mktemp(suffix=".webm")
    gTTS(text, lang="ru").save(mp3)
    # mp3 -> webm/opus, имитируем запись браузера
    subprocess.run(["ffmpeg", "-i", mp3, "-y", webm], capture_output=True, check=True)
    with open(webm, "rb") as f:
        return f.read()


if __name__ == "__main__":
    for p in PHRASES:
        data = make_webm(p)
        result = transcriber.transcribe(data)
        print("ОРИГИНАЛ :", p)
        print("РАСПОЗНАНО:", result)
        print("-" * 60)
