"""
OAuth Authentication Routes
----------------------
This module defines the API routes for OAuth-based authentication using Google and Facebook.

Features:
- Retrieve OAuth login URLs.
- Redirect users to OAuth providers (Google, Facebook).
- Handle OAuth callbacks to authenticate users.
- Fetch user details from third-party OAuth providers.

Methods:
- `get_oauth_urls()`: Returns OAuth login URLs dynamically based on configuration.
- `google_login()`: Redirects the user to Google OAuth authentication.
- `google_auth_callback()`: Handles Google OAuth callback and authenticates the user.
- `facebook_login()`: Redirects the user to Facebook OAuth authentication.
- `facebook_auth_callback()`: Handles Facebook OAuth callback and authenticates the user.
- `fetch_facebook_user_info()`: Retrieves user details from Facebook's Graph API.
"""

import secrets
import httpx
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Request
from starlette.responses import JSONResponse, RedirectResponse

from swx_api.core.config.settings import settings
from swx_api.core.config.social_settings import social_settings
from swx_api.core.controllers.auth_controller import login_social_user_controller
from swx_api.core.database.db import SessionDep
from swx_api.core.repositories.user_repository import (
    get_user_by_email,
    create_social_user,
)
from swx_api.core.utils.language_helper import translate

from swx_api.core.models.token import Token

# Initialize API router with a prefix for OAuth authentication
router = APIRouter(prefix="/oauth")

# Initialize OAuth client
oauth = OAuth()

# Register Google OAuth if enabled
if social_settings.ENABLE_GOOGLE_LOGIN:
    oauth.register(
        name="google",
        client_id=social_settings.GOOGLE_CLIENT_ID,
        client_secret=social_settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

# Register Facebook OAuth if enabled
if social_settings.ENABLE_FACEBOOK_LOGIN:
    oauth.register(
        name="facebook",
        client_id=social_settings.FACEBOOK_CLIENT_ID,
        client_secret=social_settings.FACEBOOK_CLIENT_SECRET,
        access_token_url="https://graph.facebook.com/v12.0/oauth/access_token",
        authorize_url="https://www.facebook.com/v12.0/dialog/oauth",
        client_kwargs={"scope": "email,public_profile"},
    )


@router.get("/urls", status_code=200)
def get_oauth_urls():
    """
    Retrieve dynamically generated OAuth login URLs based on enabled providers.

    Returns:
        JSONResponse: A dictionary containing OAuth login URLs for Google and Facebook.
    """
    base_url = settings.BACKEND_HOST + settings.ROUTE_PREFIX
    urls = {
        "google": f"{base_url}/oauth/google"
        if social_settings.ENABLE_SOCIAL_LOGIN and social_settings.ENABLE_GOOGLE_LOGIN
        else None,
        "facebook": f"{base_url}/oauth/facebook"
        if social_settings.ENABLE_SOCIAL_LOGIN and social_settings.ENABLE_FACEBOOK_LOGIN
        else None,
    }
    return JSONResponse(urls)


@router.get("/google", status_code=307)
async def google_login(request: Request):
    """
    Redirect the user to Google's OAuth authentication page.

    Args:
        request (Request): The HTTP request object.

    Returns:
        RedirectResponse: A redirect to Google's OAuth authentication page.
    """
    try:
        if not social_settings.ENABLE_GOOGLE_LOGIN:
            raise HTTPException(status_code=400, detail=translate(request, "google_login_disabled"))

        redirect_uri = social_settings.GOOGLE_REDIRECT_URI
        if not redirect_uri:
            raise HTTPException(status_code=500, detail=translate(request, "google_redirect_uri_not_configured"))

        state = secrets.token_urlsafe(16)
        request.session["oauth_state"] = state
        return await oauth.google.authorize_redirect(request, redirect_uri, state=state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate(request, "failed_to_initiate_google_login", error=str(e)))


@router.get("/google/callback", response_model=Token, status_code=301)
async def google_auth_callback(request: Request, session: SessionDep):
    """
    Handle Google's OAuth callback, authenticate the user, and return a JWT token.

    Args:
        request (Request): The HTTP request object.
        session (SessionDep): The database session.

    Returns:
        Token: A JWT token if authentication is successful.
    """
    try:
        state = request.query_params.get("state")
        stored_state = request.session.get("oauth_state")
        if not stored_state or state != stored_state:
            return JSONResponse({"error": translate(request, "csrf_warning_state_mismatch")}, status_code=400)

        token_data = await oauth.google.authorize_access_token(request)
        if not token_data:
            return JSONResponse({"error": translate(request, "failed_to_fetch_google_token")}, status_code=400)

        user_info = token_data.get("userinfo", {})
        email = user_info.get("email")
        if not email:
            return JSONResponse({"error": translate(request, "google_account_missing_email")}, status_code=400)

        existing_user = get_user_by_email(session=session, email=email)
        if not existing_user:
            existing_user = create_social_user(session, email, user_info, "google")

        request.session.pop("oauth_state", None)

        token: Token = login_social_user_controller(session, existing_user.email)

        return redirect_with_token(token)

    except Exception as e:
        raise HTTPException(status_code=500, detail=translate(request, "google_auth_callback_failed", error=str(e)))


@router.get("/facebook", status_code=307)
async def facebook_login(request: Request):
    """
    Redirect the user to Facebook's OAuth authentication page.

    Args:
        request (Request): The HTTP request object.

    Returns:
        RedirectResponse: A redirect to Facebook's OAuth authentication page.
    """
    try:
        if not social_settings.ENABLE_FACEBOOK_LOGIN:
            raise HTTPException(status_code=400, detail=translate(request, "facebook_login_disabled"))

        redirect_uri = social_settings.FACEBOOK_REDIRECT_URI
        if not redirect_uri:
            raise HTTPException(status_code=500, detail=translate(request, "facebook_redirect_uri_not_configured"))

        return await oauth.facebook.authorize_redirect(request, redirect_uri)
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=translate(request, "failed_to_initiate_facebook_login", error=str(e)))


async def fetch_facebook_user_info(access_token: str):
    """
    Fetch user details from Facebook's Graph API using `httpx`.

    Args:
        access_token (str): The Facebook OAuth access token.

    Returns:
        dict: A dictionary containing user information.
    """
    user_info_url = "https://graph.facebook.com/me?fields=id,name,email"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(user_info_url, headers=headers)
            response.raise_for_status()
            user_data = response.json()

            if "error" in user_data:
                raise HTTPException(status_code=400, detail=f"Facebook API Error: {user_data['error']['message']}")

            return user_data

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Facebook API request failed: {str(e)}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to Facebook API: {str(e)}")


@router.get("/facebook/callback", response_model=Token, status_code=301)
async def facebook_auth_callback(request: Request, session: SessionDep):
    """
    Handle Facebook's OAuth callback, authenticate the user, and return a JWT token.

    Args:
        request (Request): The HTTP request object.
        session (SessionDep): The database session.

    Returns:
        Token: A JWT token if authentication is successful.
    """
    try:
        state = request.query_params.get("state")
        code = request.query_params.get("code")
        if not state or not code:
            raise HTTPException(status_code=400, detail=translate(request, "invalid_oauth_response"))

        token_data = await oauth.facebook.authorize_access_token(request)
        if not token_data:
            raise HTTPException(status_code=400, detail=translate(request, "failed_to_retrieve_facebook_token"))

        access_token = token_data.get("access_token")
        user_info = await fetch_facebook_user_info(access_token)
        email = user_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail=translate(request, "facebook_account_missing_email"))

        existing_user = get_user_by_email(session=session, email=email)
        if not existing_user:
            existing_user = create_social_user(session, email, user_info, "facebook")

        token: Token = login_social_user_controller(session, existing_user.email)

        return redirect_with_token(token)

    except Exception as e:
        raise HTTPException(status_code=500, detail=translate(request, "facebook_auth_callback_failed", error=str(e)))


def redirect_with_token(token: Token) -> RedirectResponse:
    """
    Redirect to frontend with access and refresh tokens in query string.
    """
    redirect_url = (
        f"{settings.FRONTEND_HOST}/oauth-success"
        f"?access_token={token.access_token}"
        f"&refresh_token={token.refresh_token or ''}"
    )
    return RedirectResponse(url=redirect_url, status_code=302)
