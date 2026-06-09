import json
import os
import hashlib
import threading
import uuid
from datetime import datetime
from config import STATS_FILE, RECORDS_FILE

_lock = threading.Lock()


def _load_stats() -> dict:
    if not os.path.exists(STATS_FILE):
        return {
            "total_processed": 0,
            "total_unique_images": 0,
            "total_conversions": 0,
            "style_usage": {},
            "daily_processed": {},
            "last_updated": None,
        }
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            stats = json.load(f)
        if "total_unique_images" not in stats:
            stats["total_unique_images"] = 0
        if "total_conversions" not in stats:
            stats["total_conversions"] = stats.get("total_processed", 0)
        return stats
    except (json.JSONDecodeError, IOError):
        return {
            "total_processed": 0,
            "total_unique_images": 0,
            "total_conversions": 0,
            "style_usage": {},
            "daily_processed": {},
            "last_updated": None,
        }


def _save_stats(stats: dict):
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def _load_records() -> dict:
    if not os.path.exists(RECORDS_FILE):
        return {
            "groups": {},
            "order": [],
        }
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "groups": {},
            "order": [],
        }


def _save_records(records: dict):
    os.makedirs(os.path.dirname(RECORDS_FILE), exist_ok=True)
    with open(RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def compute_md5(file_bytes: bytes) -> str:
    return hashlib.md5(file_bytes).hexdigest()


def record_processing(
    style_id: str,
    count: int = 1,
    md5: str = None,
    original_filename: str = None,
    upload_path: str = None,
    output_filename: str = None,
    output_url: str = None,
    intensity: float = 0.8,
):
    with _lock:
        stats = _load_stats()
        records = _load_records()

        stats["total_processed"] += count
        stats["total_conversions"] += count
        stats["style_usage"][style_id] = stats["style_usage"].get(style_id, 0) + count

        today = datetime.now().strftime("%Y-%m-%d")
        stats["daily_processed"][today] = stats["daily_processed"].get(today, 0) + count
        stats["last_updated"] = datetime.now().isoformat()

        if md5 and output_filename:
            is_new_image = md5 not in records["groups"]
            if is_new_image:
                stats["total_unique_images"] += 1
                records["groups"][md5] = {
                    "md5": md5,
                    "original_filename": original_filename or "image.png",
                    "upload_path": upload_path or "",
                    "upload_url": "/uploads/" + os.path.basename(upload_path) if upload_path else "",
                    "conversions": [],
                    "created_at": datetime.now().isoformat(),
                }
                records["order"].insert(0, md5)

            conversion_id = uuid.uuid4().hex[:12]
            conversion_record = {
                "id": conversion_id,
                "style": style_id,
                "intensity": intensity,
                "output_filename": output_filename,
                "output_url": output_url or f"/outputs/{output_filename}",
                "created_at": datetime.now().isoformat(),
            }
            records["groups"][md5]["conversions"].append(conversion_record)
            records["groups"][md5]["last_updated"] = datetime.now().isoformat()

        _save_stats(stats)
        _save_records(records)


def get_stats() -> dict:
    with _lock:
        return _load_stats()


def get_grouped_records() -> list:
    with _lock:
        records = _load_records()
        result = []
        for md5 in records["order"]:
            if md5 in records["groups"]:
                group = records["groups"][md5]
                result.append({
                    "md5": group["md5"],
                    "original_filename": group["original_filename"],
                    "upload_url": group.get("upload_url", ""),
                    "conversions_count": len(group["conversions"]),
                    "created_at": group.get("created_at", ""),
                    "last_updated": group.get("last_updated", ""),
                    "conversions": list(reversed(group["conversions"])),
                })
        return result
