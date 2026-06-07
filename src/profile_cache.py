import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.config import DB_PATH


CACHE_VERSION = "profile-v1"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS profile_cache (
            cache_key TEXT PRIMARY KEY,
            mode TEXT NOT NULL,
            tier TEXT NOT NULL,
            model TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            target_certification TEXT NOT NULL,
            profile_json TEXT NOT NULL,
            hit_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    return conn


def build_profile_cache_key(
    *,
    mode: str,
    model: str,
    employee_id: str,
    target_certification: str,
    text_input: str,
    work_signals: Dict[str, Any],
) -> str:
    payload = {
        "version": CACHE_VERSION,
        "mode": mode,
        "model": model,
        "employee_id": employee_id,
        "target_certification": target_certification,
        "text_input": " ".join(text_input.split()).strip().lower(),
        "work_signals": work_signals,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def get_cached_profile(cache_key: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT profile_json FROM profile_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            """
            UPDATE profile_cache
            SET hit_count = hit_count + 1, updated_at = ?
            WHERE cache_key = ?
            """,
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), cache_key),
        )
        conn.commit()
        return json.loads(row[0])
    finally:
        conn.close()


def delete_cached_profile(cache_key: str) -> None:
    conn = _connect()
    try:
        conn.execute("DELETE FROM profile_cache WHERE cache_key = ?", (cache_key,))
        conn.commit()
    finally:
        conn.close()


def set_cached_profile(
    *,
    cache_key: str,
    mode: str,
    tier: str,
    model: str,
    employee_id: str,
    target_certification: str,
    profile_data: Dict[str, Any],
) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO profile_cache (
                cache_key, mode, tier, model, employee_id, target_certification,
                profile_json, hit_count, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                tier = excluded.tier,
                profile_json = excluded.profile_json,
                updated_at = excluded.updated_at
            """,
            (
                cache_key,
                mode,
                tier,
                model,
                employee_id,
                target_certification,
                json.dumps(profile_data, sort_keys=True),
                now,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()
