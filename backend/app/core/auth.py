"""
Clerk JWT verification for FastAPI.

Usage (protected route):
    from app.core.auth import get_current_user
    from app.models.user import User

    @app.get("/api/me")
    def me(user: User = Depends(get_current_user)):
        return {"id": user.id, "email": user.email}

Health / public routes do NOT need this dependency.
"""

import os
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CLERK_PUBLISHABLE_KEY: str = os.getenv("VITE_CLERK_PUBLISHABLE_KEY", "")
# Derive Frontend API from the publishable key:
#   pk_test_dGVuZGVyLWtvaS01Njk0LmNsZXJrLmFjY291bnRzLmRldiQ
#   → base64 decode the middle part → "tender-koi-5694.clerk.accounts.dev"
# We just hard-code the JWKS URL via env; fall back to auto-detect.
CLERK_JWKS_URL: str = os.getenv(
    "CLERK_JWKS_URL",
    "https://tender-koi-5694.clerk.accounts.dev/.well-known/jwks.json",
)

_bearer = HTTPBearer(auto_error=False)

# Simple in-memory JWKS cache (keys rotate rarely).
_jwks_cache: Optional[dict] = None


def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        resp = httpx.get(CLERK_JWKS_URL, timeout=10)
        resp.raise_for_status()
        _jwks_cache = resp.json()
    return _jwks_cache


def _verify_clerk_token(token: str) -> dict:
    """Decode and verify a Clerk-issued JWT. Returns the payload dict."""
    try:
        jwks = _get_jwks()
        # jose.jwt can consume a JWKS dict directly.
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Clerk doesn't set aud on session tokens
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def sync_user_data(
    clerk_user_id: str,
    email: Optional[str],
    name: Optional[str],
    db: Session,
) -> User:
    """
    Upsert a local User row keyed by clerk_user_id.
    Creates the row on first sign-in or updates existing details (email, name).
    If email already exists under a legacy account without clerk_user_id, links it.
    """
    clean_email = email.strip() if email else ""
    clean_name = name.strip() if name else ""

    # 1. Search by clerk_user_id
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()

    # 2. If not found by clerk_user_id, check by clean_email (if non-empty) to link existing local user
    if user is None and clean_email:
        user = db.query(User).filter(User.email == clean_email).first()
        if user:
            user.clerk_user_id = clerk_user_id

    # 3. If still not found, create new user
    if user is None:
        # Fallback email if clean_email is empty to avoid UNIQUE constraint collision on empty strings
        effective_email = clean_email if clean_email else f"{clerk_user_id}@clerk.user"
        effective_name = clean_name if clean_name else (clean_email.split("@")[0] if clean_email else "User")
        
        user = User(
            clerk_user_id=clerk_user_id,
            email=effective_email,
            name=effective_name,
            password_hash=None,  # Clerk owns auth
        )
        db.add(user)
    else:
        # Update existing user details if new valid details are provided or if placeholder exists
        if clean_email and (user.email != clean_email or user.email.endswith("@clerk.user")):
            user.email = clean_email
        if clean_name and (user.name != clean_name or user.name == "User" or not user.name):
            user.name = clean_name

    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that verifies a Clerk Bearer token and returns the
    corresponding local User row (creating it on first call).

    Raises 401 if the token is missing or invalid.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _verify_clerk_token(credentials.credentials)

    # Clerk session token claims
    clerk_user_id: str = payload.get("sub", "")
    email: Optional[str] = payload.get("email")
    name: Optional[str] = payload.get("name")

    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
        )

    return sync_user_data(clerk_user_id, email, name, db)

