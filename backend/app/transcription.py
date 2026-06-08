"""STT через локальную модель openai/whisper-small (HuggingFace transformers).

Браузер пишет аудио в webm (Opus). Whisper не читает webm напрямую, поэтому:
  webm --ffmpeg--> wav 16kHz mono --soundfile--> numpy --whisper--> текст
Модель грузится один раз при старте приложения (см. main.lifespan)."""
import os
import subprocess
import tempfile
from typing import Optional

import soundfile as sf

from .config import settings


class Transcriber:
    def __init__(self) -> None:
        self._pipe = None

    @property
    def loaded(self) -> bool:
        return self._pipe is not None

    def load(self):
        if self._pipe is None:
            # Импорт здесь, чтобы torch/transformers не тормозили импорт модуля.
            from transformers import pipeline
            self._pipe = pipeline(
                "automatic-speech-recognition",
                model=settings.whisper_model,
                device=-1,            # CPU (free tier HF Spaces)
                chunk_length_s=30,    # поддержка длинных ответов (>30с)
            )
        return self._pipe

    def transcribe(self, audio_bytes: bytes) -> str:
        self.load()
        tmp_webm: Optional[str] = None
        tmp_wav: Optional[str] = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
                f.write(audio_bytes)
                tmp_webm = f.name
            tmp_wav = tmp_webm[:-5] + ".wav"

            proc = subprocess.run(
                ["ffmpeg", "-i", tmp_webm, "-ar", "16000", "-ac", "1", "-f", "wav", "-y", tmp_wav],
                capture_output=True,
            )
            if proc.returncode != 0:
                raise RuntimeError("FFmpeg failed: " + proc.stderr.decode(errors="ignore")[:400])

            audio, sr = sf.read(tmp_wav, dtype="float32")
            if getattr(audio, "ndim", 1) > 1:
                audio = audio.mean(axis=1)  # в моно на всякий случай

            result = self._pipe({"array": audio, "sampling_rate": sr})
            return (result.get("text") or "").strip()
        finally:
            for path in (tmp_webm, tmp_wav):
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except OSError:
                        pass


transcriber = Transcriber()
