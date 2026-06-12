import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.db_utils import execute_query, execute_update, get_db_transaction, init_db_tables

logger = logging.getLogger(__name__)

AI_CACHE_VERSION = "ai-call-v1"

# Initialize database tables on module import
try:
    init_db_tables()
except Exception as e:
    logger.warning(f"Database initialization check: {e}")


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
    """
    Retrieve cached AI call response and increment hit counter.
    Safe: Handles connection management automatically.
    
    Args:
        cache_key: The cache key to look up
        
    Returns:
        Parsed response payload or None if not found
    """
    try:
        row = execute_query(
            "SELECT response_json FROM ai_call_cache WHERE cache_key = ?",
            (cache_key,),
            fetch_one=True
        )
        
        if row is None:
            return None
        
        # Update hit count
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        execute_update(
            """
            UPDATE ai_call_cache
            SET hit_count = hit_count + 1, updated_at = ?
            WHERE cache_key = ?
            """,
            (now, cache_key),
        )
        
        return json.loads(row[0])
    except Exception as e:
        logger.error(f"Error retrieving cached AI call for key {cache_key}: {e}")
        raise


def set_cached_ai_call(
    *,
    cache_key: str,
    call_type: str,
    model: str,
    request_payload: Dict[str, Any],
    response_payload: Dict[str, Any],
) -> None:
    """
    Cache an AI call response.
    Safe: Handles connection management and transactions automatically.
    
    Args:
        cache_key: The cache key
        call_type: Type of AI call
        model: Model used
        request_payload: Request data
        response_payload: Response data
    """
    try:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        execute_update(
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
    except Exception as e:
        logger.error(f"Error caching AI call with key {cache_key}: {e}")
        raise


def delete_cached_ai_call(cache_key: str) -> None:
    """
    Delete a cached AI call.
    Safe: Handles connection management and transactions automatically.
    
    Args:
        cache_key: The cache key to delete
    """
    try:
        execute_update(
            "DELETE FROM ai_call_cache WHERE cache_key = ?",
            (cache_key,)
        )
    except Exception as e:
        logger.error(f"Error deleting cached AI call for key {cache_key}: {e}")
        raise
