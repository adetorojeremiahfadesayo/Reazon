import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.config import DB_PATH


AI_CACHE_VERSION = "ai-call-v1"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_call_cache (
            cache_key TEXT PRIMARY KEY,
            call_type TEXT NOT NULL,
            model TEXT NOT NULL,
            request_json TEXT NOT NULL,
            response_json TEXT NOT NULL,
            hit_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    return conn


def build_ai_call_cache_key(
    *,
    call_type: str,
    model: str,
    request_payload: Dict[str, Any],
) -> str:
    payload = {
        "version": AI_CACHE_VERSION,
        "call_type": call_type,
        "model": model,
        "request_payload": request_payload,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def get_cached_ai_call(cache_key: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT response_json FROM ai_call_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            """
            UPDATE ai_call_cache
            SET hit_count = hit_count + 1, updated_at = ?
            WHERE cache_key = ?
            """,
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), cache_key),
        )
        conn.commit()
        return json.loads(row[0])
    finally:
        conn.close()


def set_cached_ai_call(
    *,
    cache_key: str,
    call_type: str,
    model: str,
    request_payload: Dict[str, Any],
    response_payload: Dict[str, Any],
) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO ai_call_cache (
                cache_key, call_type, model, request_json, response_json,
                hit_count, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                response_json = excluded.response_json,
                updated_at = excluded.updated_at
            """,
            (
                cache_key,
                call_type,
                model,
                json.dumps(request_payload, sort_keys=True, default=str),
                json.dumps(response_payload, sort_keys=True, default=str),
                now,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def delete_cached_ai_call(cache_key: str) -> None:
    conn = _connect()
    try:
        conn.execute("DELETE FROM ai_call_cache WHERE cache_key = ?", (cache_key,))
        conn.commit()
    finally:
        conn.close()
