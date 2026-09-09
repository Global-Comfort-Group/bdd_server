"""A slashless request for a slashed route must be served, not redirected.

Nine routes are registered with a trailing slash. Starlette answers the
slashless form with a 307 whose Location is absolute, built from the request's
Host header — behind a reverse proxy, this service's own hostname rather than
the one the browser is talking to.

That makes the redirect cross-origin, and `fetch` drops the Authorization
header when it follows one: the retry arrives unauthenticated, the API answers
401, and the frontend reads that as an expired session and signs the user out.
Clicking anything in the admin panel logged the user out for exactly this
reason.

The browser cannot avoid it by asking for the slashed path, because Next.js
normalises the slash away before proxying. So the fix belongs here: match the
route directly and never issue the redirect.

These tests exercise the app over ASGI, which is the seam the proxy hits. They
need no database — the paths chosen answer before touching one.
"""
import httpx
import pytest

from app.main import app

# Answers 401 without a database: the auth dependency rejects the request before
# any handler runs, which is all these tests need.
SLASHED_ROUTE = "/api/v1/admin/users/"
SLASHLESS = "/api/v1/admin/users"


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        follow_redirects=False,
    )


@pytest.mark.asyncio
async def test_slashless_path_is_served_not_redirected():
    """The whole point: no 3xx, so no cross-origin hop for fetch to strip."""
    async with _client() as client:
        response = await client.get(SLASHLESS)

    assert response.status_code != 307, (
        "A redirect here becomes cross-origin behind a proxy, and the browser "
        "drops the Authorization header when it follows one."
    )
    assert "location" not in response.headers


@pytest.mark.asyncio
async def test_both_forms_give_the_same_answer():
    """Whether the proxy keeps the slash or strips it must not matter."""
    async with _client() as client:
        with_slash = await client.get(SLASHED_ROUTE)
        without_slash = await client.get(SLASHLESS)

    assert with_slash.status_code == without_slash.status_code


@pytest.mark.asyncio
async def test_an_unknown_path_is_still_a_404():
    """Only real routes are matched — a missing path does not become one."""
    async with _client() as client:
        response = await client.get("/api/v1/no-such-endpoint")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_a_route_registered_without_a_slash_is_untouched():
    """The rewrite applies to slashed routes only; everything else is normal."""
    async with _client() as client:
        response = await client.get("/api/v1/admin/dashboard/system-stats")

    assert response.status_code == 401
    assert "location" not in response.headers
