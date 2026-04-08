"""
Authentication routes — Google OAuth2 login, callback, user info, and logout.
"""

from __future__ import annotations

from datetime import timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.config import Settings, get_settings
from app.core.security import GOOGLE_SCOPES, SESSION_USER_KEY
from app.db.models import UserToken
from app.utils.logger import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)

FRONTEND_URL = "http://localhost:3000"


def _build_flow(settings: Settings) -> Flow:
    """Construct a Google OAuth2 ``Flow`` from application settings."""
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    return flow


@router.get("/login")
def auth_login(
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """
    Generate a Google OAuth2 authorization URL.

    The frontend should redirect the user to the returned ``auth_url``.
    """
    flow = _build_flow(settings)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
    )
    logger.info("oauth_login_url_generated")
    return {"auth_url": auth_url}


@router.get("/callback")
async def auth_callback(
    code: str | None = None,
    error: str | None = None,
    request: Request = None,
    settings: Settings = Depends(get_settings),
):
    """
    Handle the Google OAuth2 callback.

    Exchanges the authorization ``code`` for access / refresh tokens,
    fetches the user's email, upserts a ``UserToken`` document, and sets
    the session cookie.  Redirects to the frontend on success or failure.
    """
    # Handle denial / error from Google
    if error:
        logger.warning("oauth_denied_by_user", error=error)
        params = urlencode({"auth_error": f"Google authorization denied: {error}"})
        return RedirectResponse(url=f"{FRONTEND_URL}/login?{params}")

    if not code:
        params = urlencode({"auth_error": "Missing authorization code."})
        return RedirectResponse(url=f"{FRONTEND_URL}/login?{params}")

    flow = _build_flow(settings)

    try:
        flow.fetch_token(code=code)
    except Exception as exc:
        logger.error("oauth_token_exchange_failed", error=str(exc))
        params = urlencode({"auth_error": f"Token exchange failed: {exc}"})
        return RedirectResponse(url=f"{FRONTEND_URL}/login?{params}")

    credentials: Credentials = flow.credentials

    # Fetch user email from the userinfo endpoint
    try:
        oauth2_service = build(
            "oauth2", "v2", credentials=credentials, cache_discovery=False
        )
        user_info = oauth2_service.userinfo().get().execute()
        user_email: str = user_info.get("email", "")
    except Exception as exc:
        logger.error("oauth_userinfo_failed", error=str(exc))
        params = urlencode({"auth_error": "Could not retrieve user info from Google."})
        return RedirectResponse(url=f"{FRONTEND_URL}/login?{params}")

    if not user_email:
        params = urlencode({"auth_error": "Could not retrieve email from Google."})
        return RedirectResponse(url=f"{FRONTEND_URL}/login?{params}")

    token_expiry = (
        credentials.expiry.replace(tzinfo=timezone.utc) if credentials.expiry else None
    )

    # Upsert token document
    existing = await UserToken.find_one(UserToken.user_email == user_email)

    if existing:
        existing.access_token = credentials.token
        if credentials.refresh_token:
            existing.refresh_token = credentials.refresh_token
        existing.token_expiry = token_expiry
        await existing.save()
    else:
        new_token = UserToken(
            user_email=user_email,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_expiry=token_expiry,
        )
        await new_token.insert()

    # Store email in session
    request.session[SESSION_USER_KEY] = user_email

    logger.info("oauth_authenticated", user_email=user_email)
    return RedirectResponse(url=f"{FRONTEND_URL}/")


@router.get("/me")
def auth_me(request: Request) -> dict[str, str | None]:
    """Return the currently authenticated user's email, or null if not logged in."""
    user_email = request.session.get(SESSION_USER_KEY)
    return {"user_email": user_email}


@router.post("/logout")
def auth_logout(request: Request) -> dict[str, str]:
    """Clear the session, effectively logging the user out."""
    request.session.clear()
    logger.info("user_logged_out")
    return {"status": "logged_out"}
