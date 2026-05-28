import asyncio
import hashlib
import json
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import HTTPException

_user_locks: Dict[int, asyncio.Lock] = {}
_dedup_cache: Dict[str, float] = {}
_DEDUP_WINDOW = 10.0  # seconds — window after first submit where identical payloads are rejected


def _get_user_lock(user_id: int) -> asyncio.Lock:
    if user_id not in _user_locks:
        _user_locks[user_id] = asyncio.Lock()
    return _user_locks[user_id]


def _make_content_key(user_id: int, data: Any) -> str:
    payload = json.dumps({"uid": user_id, **data}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _is_recent_duplicate(key: str) -> bool:
    now = time.monotonic()
    expired = [k for k, ts in _dedup_cache.items() if now - ts > _DEDUP_WINDOW]
    for k in expired:
        del _dedup_cache[k]
    if key in _dedup_cache:
        return True
    _dedup_cache[key] = now
    return False


@asynccontextmanager
async def submission_guard(user_id: int, payload: Any):
    """
    Prevents duplicate property submissions from rapid button clicks.

    Two layers:
    - Per-user asyncio lock: rejects a second concurrent request while the first is still processing.
    - Content-hash TTL cache: rejects identical payloads submitted within _DEDUP_WINDOW seconds.

    On body exception the hash is evicted so the user can retry. On success the hash stays
    in cache for _DEDUP_WINDOW seconds.

    Safe for single-worker uvicorn (asyncio, no cross-process state needed).
    """
    lock = _get_user_lock(user_id)

    if lock.locked():
        raise HTTPException(
            status_code=429,
            detail="A submission is already in progress. Please wait before submitting again.",
        )

    content_key = _make_content_key(user_id, payload)
    if _is_recent_duplicate(content_key):
        raise HTTPException(
            status_code=409,
            detail="Duplicate submission detected. Please wait a moment before resubmitting.",
        )

    # Acquire immediately (lock is free — no yield, no context switch possible here)
    await lock.acquire()
    try:
        yield
    except Exception:
        # Body failed — remove from cache so the user can retry
        _dedup_cache.pop(content_key, None)
        raise
    finally:
        lock.release()


def _reset() -> None:
    """Clear all in-memory state. For use in tests only."""
    _user_locks.clear()
    _dedup_cache.clear()
