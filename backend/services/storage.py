import json
import os
from datetime import datetime
from typing import Dict, Any, List

# Resolve project-level data directory robustly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "data"))
PROGRESS_PATH = os.path.join(DATA_DIR, "progress.json")

def _ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    # If file missing or empty/invalid JSON, (re)initialize it
    if not os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
            json.dump({"events": []}, f)
    else:
        try:
            # check valid JSON
            with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
                data = f.read()
                if not data.strip():
                    raise ValueError("empty")
                json.loads(data)
        except Exception:
            # overwrite with a valid initial structure
            with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
                json.dump({"events": []}, f)

def read_progress() -> Dict[str, Any]:
    _ensure_file()
    with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_progress(data: Dict[str, Any]) -> None:
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def save_study_event(event: Dict[str, Any]) -> None:
    _ensure_file()
    progress = read_progress()
    event.setdefault("timestamp", datetime.utcnow().isoformat())
    progress.get("events", []).append(event)
    _write_progress(progress)

def save_quiz_result(result: Dict[str, Any]) -> None:
    _ensure_file()
    progress = read_progress()
    result.setdefault("timestamp", datetime.utcnow().isoformat())
    progress.get("events", []).append(result)
    _write_progress(progress)
