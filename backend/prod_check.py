"""Быстрая проверка ПРОДА: LLM (/start), STT (/transcribe), CORS."""
import os
import subprocess
import tempfile

import requests
from gtts import gTTS

BASE = os.environ.get("BASE", "https://bol970-stt-checklist-agent.hf.space")
ORIGIN = "https://stt-checklist-agent.vercel.app"


def webm(text: str) -> bytes:
    mp3 = tempfile.mktemp(suffix=".mp3")
    w = tempfile.mktemp(suffix=".webm")
    gTTS(text, lang="ru").save(mp3)
    subprocess.run(["ffmpeg", "-i", mp3, "-y", w], capture_output=True, check=True)
    with open(w, "rb") as f:
        return f.read()


print("BASE:", BASE)

# 1) LLM путь
s = requests.post(f"{BASE}/api/session/start", timeout=60).json()
print("\n[1] /start OK — session:", s["session_id"])
for q in s["questions"]:
    print("    Q:", q["text"])

# 2) STT путь (одно аудио)
audio = webm("Проект называется ФудФаст, приложение доставки еды, бюджет два миллиона.")
r = requests.post(
    f"{BASE}/api/session/transcribe",
    files=[("audio_file", ("a.webm", audio, "audio/webm"))],
    timeout=120,
).json()
print("\n[2] /transcribe OK — распознано:")
print("    ", r["transcript"])

# 3) CORS
resp = requests.post(f"{BASE}/api/session/start", headers={"Origin": ORIGIN}, timeout=60)
acao = resp.headers.get("access-control-allow-origin")
print("\n[3] CORS access-control-allow-origin:", acao)
print("\n✅ PROD OK" if acao else "\n⚠️ CORS header missing")
