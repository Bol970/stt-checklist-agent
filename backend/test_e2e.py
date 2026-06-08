"""End-to-end тест бэкенда по HTTP: полная сессия 3 раунда через реальный API."""
import subprocess
import tempfile

import requests
from gtts import gTTS

BASE = "http://localhost:7860"

ANSWERS = [
    [
        "Проект называется ФудФаст, это мобильное приложение доставки еды.",
        "Главная цель — доставка за тридцать минут и рост числа заказов.",
        "Сроки около трёх месяцев, бюджет примерно два миллиона рублей.",
    ],
    [
        "Целевая аудитория — жители крупных городов от двадцати до сорока лет.",
        "Метрика успеха — сто заказов в день и средний чек семьсот рублей.",
        "Нужна интеграция с системой учёта и оплата картой через эквайринг.",
    ],
    [
        "Платформы — айфон и андроид.",
        "Главные риски — сжатые сроки и нехватка курьеров.",
        "Есть база ресторанов в таблицах, её нужно перенести в систему.",
    ],
]


def webm(text: str) -> bytes:
    mp3 = tempfile.mktemp(suffix=".mp3")
    w = tempfile.mktemp(suffix=".webm")
    gTTS(text, lang="ru").save(mp3)
    subprocess.run(["ffmpeg", "-i", mp3, "-y", w], capture_output=True, check=True)
    with open(w, "rb") as f:
        return f.read()


def main():
    s = requests.post(BASE + "/api/session/start").json()
    sid = s["session_id"]
    print(f"[start] session={sid} round={s['round']}/{s['max_rounds']}")
    for q in s["questions"]:
        print("   Q:", q["text"])
    cur = s

    for rnd in range(3):
        files = [
            ("audio_files", (f"a{i}.webm", webm(a), "audio/webm"))
            for i, a in enumerate(ANSWERS[rnd])
        ]
        data = {"question_ids": ",".join(q["id"] for q in cur["questions"])}
        r = requests.post(f"{BASE}/api/session/{sid}/submit", files=files, data=data).json()
        if r.get("is_complete"):
            print("\n=== ✅ COMPLETE ===")
            print("round_summary:", r.get("round_summary"))
            print("\n--- checklist markdown ---\n")
            print(r["checklist_preview"])
        else:
            print(f"\n[round {r['round']}] summary: {r.get('round_summary')}")
            for q in r["questions"]:
                print("   Q:", q["text"])
            cur = r

    res = requests.get(f"{BASE}/api/session/{sid}/results").json()
    print("\n[results] items:", len(res["checklist"]), "| is_complete:", res["is_complete"])


if __name__ == "__main__":
    main()
