"""
FastAPI dependencies shared across routes.
"""

from fastapi import HTTPException, Request

from app.core.security import SESSION_USER_KEY
from app.db.models import UserToken


async def get_current_user(request: Request) -> UserToken:
    """
    Read the authenticated user's email from the session, look up the
    corresponding ``UserToken`` in MongoDB, and return it.

    Raises HTTP 401 if the session has no user or the token record is missing.
    """
    user_email: str | None = request.session.get(SESSION_USER_KEY)
    if not user_email:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please log in via /api/v1/auth/login.",
        )

    token = await UserToken.find_one(UserToken.user_email == user_email)
    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication token not found. Please re-authenticate via /api/v1/auth/login.",
        )

    return token
