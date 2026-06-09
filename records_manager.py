import json
import os
import threading
from datetime import datetime
from config import DATA_DIR

RECORDS_FILE = os.path.join(DATA_DIR, "records.json")

_lock = threading.Lock()


def _load_records() -> dict:
    if not os.path.exists(RECORDS_FILE):
        return {"groups": {}, "order": []}
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "groups" not in data:
                data["groups"] = {}
            if "order" not in data:
                data["order"] = []
            return data
    except (json.JSONDecodeError, IOError):
        return {"groups": {}, "order": []}


def _save_records(records: dict):
    os.makedirs(os.path.dirname(RECORDS_FILE), exist_ok=True)
    with open(RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def _short_id() -> str:
    import uuid
    return uuid.uuid4().hex[:12]


def add_conversion(
    md5: str,
    original_filename: str,
    upload_path: str,
    upload_url: str,
    style: str,
    intensity: float,
    output_filename: str,
    output_url: str,
) -> dict:
    with _lock:
        records = _load_records()
        now = datetime.now().isoformat()

        if md5 not in records["groups"]:
            records["groups"][md5] = {
                "md5": md5,
                "original_filename": original_filename,
                "upload_path": upload_path,
                "upload_url": upload_url,
                "conversions": [],
                "created_at": now,
                "last_updated": now,
            }
            records["order"].insert(0, md5)

        group = records["groups"][md5]
        group["last_updated"] = now
        if original_filename:
            group["original_filename"] = original_filename
        if upload_path:
            group["upload_path"] = upload_path
        if upload_url:
            group["upload_url"] = upload_url

        conversion = {
            "id": _short_id(),
            "style": style,
            "intensity": intensity,
            "output_filename": output_filename,
            "output_url": output_url,
            "created_at": now,
        }
        group["conversions"].append(conversion)

        _save_records(records)
        return group


def get_all_records() -> dict:
    with _lock:
        records = _load_records()
        return records


def get_unique_image_count() -> int:
    with _lock:
        records = _load_records()
        return len(records["groups"])


def get_total_conversion_count() -> int:
    with _lock:
        records = _load_records()
        total = 0
        for g in records["groups"].values():
            total += len(g.get("conversions", []))
        return total
