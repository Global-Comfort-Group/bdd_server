from fastapi import APIRouter
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.auth import get_user_manager

# Bearer transport
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# JWT strategy function
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.SECRET_KEY,
        lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

# Authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPIUsers instance
fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

# Current user dependencies
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

# Auth router
auth_router = APIRouter()
auth_router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/jwt", tags=["auth"]
)
auth_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="",
    tags=["auth"],
)
auth_router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="",
    tags=["auth"],
)
auth_router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="",
    tags=["auth"],
)

# Users router
users_router = APIRouter()
users_router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)