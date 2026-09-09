"""Every route requires a signed-in caller unless it is on the list below.

26 of 91 routes were reachable without any credentials, 10 of them accepting
writes — anyone who could reach the server could edit a property, move it
through the workflow, or delete a negotiation table. The cause was easy to
miss: the dependency is per-handler, so leaving it off one signature silently
opens that route, and nothing complains.

This test inverts that. The exceptions are written down, and anything else that
becomes reachable without a login fails here rather than in production.
"""
import pytest
from fastapi.routing import APIRoute

from app.main import app

# Dependencies that establish who the caller is.
AUTH_DEPENDENCIES = {
    "get_current_user",
    "current_admin_user",
    "current_superuser_admin",
    "get_current_active_user",
    "current_active_user",
}

# Routes that are meant to be reachable without a login, and why.
PUBLIC_BY_DESIGN = {
    # You cannot present a token before you have one.
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    # Philippine address reference data — public, and holds nothing of ours.
    "/api/v1/address/health",
    "/api/v1/address/regions",
    "/api/v1/address/provinces/{region_code}",
    "/api/v1/address/cities/{province_code}",
    "/api/v1/address/barangays/{city_code}",
    "/api/v1/address/generate-address",
    # Serve images and files. A browser cannot put a bearer token on an <img>
    # tag, so these need signed URLs rather than a dependency; until then they
    # stay open deliberately.
    "/api/v1/files/{object_key:path}",
    "/api/v1/uploads/attachment/{attachment_id}/thumbnail",
}


def _dependency_names(route: APIRoute) -> set:
    """Every dependency in the route's flattened tree, router-level included."""
    names = set()

    def walk(dependant, depth=0):
        if depth > 8:
            return
        call = getattr(dependant, "call", None)
        if call is not None:
            names.add(getattr(call, "__name__", str(call)))
        for sub in getattr(dependant, "dependencies", []):
            walk(sub, depth + 1)

    walk(route.dependant)
    return names


def _unauthenticated_routes():
    found = set()
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/api/v1"):
            continue
        if not (_dependency_names(route) & AUTH_DEPENDENCIES):
            found.add(route.path)
    return found


def test_no_route_is_reachable_without_a_login_unless_listed():
    unexpected = _unauthenticated_routes() - PUBLIC_BY_DESIGN
    assert not unexpected, (
        "These routes are reachable without any credentials. Add the auth "
        "dependency, or add them to PUBLIC_BY_DESIGN with a reason:\n  "
        + "\n  ".join(sorted(unexpected))
    )


def test_the_public_list_has_not_gone_stale():
    """A path listed as public but no longer open means the list needs pruning."""
    stale = PUBLIC_BY_DESIGN - _unauthenticated_routes()
    assert not stale, (
        "Listed as public by design, but now requires auth — remove from the "
        "list:\n  " + "\n  ".join(sorted(stale))
    )


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/properties/",
        "/api/v1/properties/{property_id}",
        "/api/v1/properties-submit/{property_id}",
        "/api/v1/properties-submit/{property_id}/status",
        "/api/v1/properties-submit/statistics",
        "/api/v1/properties-submit/recent-activity",
        "/api/v1/nego-tables/",
        "/api/v1/nego-tables/{nego_table_id}",
    ],
)
def test_the_routes_that_were_open_are_now_closed(path):
    """Named individually so a regression says which door reopened."""
    assert path not in _unauthenticated_routes()
