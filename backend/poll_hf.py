"""Опрос статуса сборки HF Space до RUNNING (или ошибки)."""
import os
import time

from huggingface_hub import HfApi

api = HfApi(token=os.environ["HF_TOKEN"])
repo = os.environ.get("HF_REPO", "Bol970/stt-checklist-agent")

for i in range(150):  # до ~50 минут
    try:
        rt = api.get_space_runtime(repo)
        stage = rt.stage
        print(f"[{i}] stage={stage}", flush=True)
        if stage == "RUNNING":
            print("READY")
            break
        if stage in ("BUILD_ERROR", "RUNTIME_ERROR", "CONFIG_ERROR", "NO_APP_FILE"):
            print("ERROR_STAGE", stage)
            break
    except Exception as e:
        print("poll error:", e, flush=True)
    time.sleep(20)
