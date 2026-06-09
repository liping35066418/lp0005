import json
import os
import threading
from datetime import datetime
from config import STATS_FILE

_lock = threading.Lock()


def _load_stats() -> dict:
    if not os.path.exists(STATS_FILE):
        return {
            "total_processed": 0,
            "style_usage": {},
            "daily_processed": {},
            "last_updated": None,
        }
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "total_processed": 0,
            "style_usage": {},
            "daily_processed": {},
            "last_updated": None,
        }


def _save_stats(stats: dict):
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def record_processing(style_id: str, count: int = 1):
    with _lock:
        stats = _load_stats()
        stats["total_processed"] += count
        stats["style_usage"][style_id] = stats["style_usage"].get(style_id, 0) + count

        today = datetime.now().strftime("%Y-%m-%d")
        stats["daily_processed"][today] = stats["daily_processed"].get(today, 0) + count
        stats["last_updated"] = datetime.now().isoformat()
        _save_stats(stats)


def get_stats() -> dict:
    with _lock:
        return _load_stats()
