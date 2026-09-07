"""
Unit tests for app.core.request_dedup.submission_guard.

These tests run without a database — they exercise the asyncio lock and content-hash
TTL cache directly.
"""

import asyncio
import pytest
from fastapi import HTTPException

from app.core.request_dedup import submission_guard, _reset


@pytest.fixture(autouse=True)
def reset_dedup_state():
    _reset()
    yield
    _reset()


# ---------------------------------------------------------------------------
# Concurrent requests (simulating rapid button clicks)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_second_request_blocked_with_429():
    """While a submission is in progress, a second concurrent request gets 429."""
    results = []

    async def submit():
        try:
            async with submission_guard(user_id=1, payload={"name": "Prop"}):
                await asyncio.sleep(0)  # yield so second coroutine can attempt the lock
            results.append("ok")
        except HTTPException as exc:
            results.append(exc.status_code)

    await asyncio.gather(submit(), submit())

    assert results.count("ok") == 1
    assert results.count(429) == 1


@pytest.mark.asyncio
async def test_five_spam_clicks_only_one_succeeds():
    """Simulates 5 rapid button clicks — exactly 1 should succeed."""
    results = []

    async def submit():
        try:
            async with submission_guard(user_id=42, payload={"name": "Spam", "price": 1_000_000}):
                await asyncio.sleep(0)
            results.append("ok")
        except HTTPException as exc:
            results.append(exc.status_code)

    await asyncio.gather(*[submit() for _ in range(5)])

    assert results.count("ok") == 1
    assert len(results) == 5


# ---------------------------------------------------------------------------
# Sequential identical resubmission (TTL cache)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_identical_resubmission_within_ttl_blocked_with_409():
    """Same payload from the same user is rejected with 409 within the TTL window."""
    payload = {"name": "Duplicate Prop"}

    async with submission_guard(user_id=1, payload=payload):
        pass  # succeeds

    with pytest.raises(HTTPException) as exc_info:
        async with submission_guard(user_id=1, payload=payload):
            pass

    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# Isolation between users
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_same_payload_different_users_both_succeed():
    """The same payload from two different users should not interfere."""
    payload = {"name": "Same Prop"}

    async with submission_guard(user_id=1, payload=payload):
        pass

    async with submission_guard(user_id=2, payload=payload):
        pass  # should not raise


@pytest.mark.asyncio
async def test_different_payload_same_user_both_succeed():
    """A user can submit different properties back-to-back without being blocked."""
    async with submission_guard(user_id=1, payload={"name": "Prop A"}):
        pass

    async with submission_guard(user_id=1, payload={"name": "Prop B"}):
        pass  # different hash → not a duplicate


# ---------------------------------------------------------------------------
# Error recovery
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_hash_evicted_on_body_exception_allowing_retry():
    """If the body raises an exception the hash is removed so the user can retry."""
    payload = {"name": "Retry Prop"}

    with pytest.raises(RuntimeError):
        async with submission_guard(user_id=1, payload=payload):
            await asyncio.sleep(0)
            raise RuntimeError("db error")

    # Hash should be gone → retry with the same payload is allowed
    async with submission_guard(user_id=1, payload=payload):
        pass  # should not raise


@pytest.mark.asyncio
async def test_lock_released_on_body_exception():
    """After a body exception the lock is released so a concurrent request can proceed."""
    payload_a = {"name": "Lock Test"}
    payload_b = {"name": "Different"}

    with pytest.raises(ValueError):
        async with submission_guard(user_id=5, payload=payload_a):
            raise ValueError("oops")

    # Lock must be free: a different payload from the same user should succeed
    async with submission_guard(user_id=5, payload=payload_b):
        pass
