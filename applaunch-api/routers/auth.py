# applaunch-api/routers/auth.py
"""
Supabase JWT authentication middleware and FastAPI dependency.

AL-8: Set up Supabase Auth with Google OAuth
AL-9: Create FastAPI JWT auth middleware and Depends
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from typing import Optional
from config import get_settings
from db.supabase_client import get_supabase

bearer_scheme = HTTPBearer()


class AuthenticatedUser(BaseModel):
    """Decoded user identity from a valid Supabase JWT."""
    id: str
    email: str
    role: str = "authenticated"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> AuthenticatedUser:
    """
    FastAPI dependency — validates the Supabase JWT from the Authorization header.

    Usage:
        @router.get("/protected")
        async def endpoint(user: AuthenticatedUser = Depends(get_current_user)):
            ...

    Returns:
        AuthenticatedUser with id, email, role.

    Raises:
        HTTP 401 if token is missing, expired, or invalid.
    """
    settings = get_settings()
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Token has expired", "code": "TOKEN_EXPIRED"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": f"Invalid token: {str(exc)}", "code": "INVALID_TOKEN"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")
    email: Optional[str] = payload.get("email")

    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Malformed token payload", "code": "MALFORMED_TOKEN"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ensure user row exists in our `users` table (upsert on first login)
    await _ensure_user_record(user_id, email)

    return AuthenticatedUser(id=user_id, email=email)


async def _ensure_user_record(user_id: str, email: str) -> None:
    """
    Upsert a user record into the `users` table on first login.
    Safe to call on every request — uses ON CONFLICT DO NOTHING semantics.
    """
    try:
        supabase = get_supabase()
        supabase.table("users").upsert(
            {"id": user_id, "email": email},
            on_conflict="id",
            ignore_duplicates=True,
        ).execute()
    except Exception as exc:
        # Non-fatal — log but don't block the request
        import logging
        logging.getLogger(__name__).warning(f"Failed to upsert user record: {exc}")
