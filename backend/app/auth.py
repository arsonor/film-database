"""
Supabase JWT authentication for FastAPI.
Verifies tokens issued by Supabase Auth using JWKS (ES256).
"""

import os
import logging
from dataclasses import dataclass

import jwt
from jwt import PyJWKClient
from fastapi import Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# JWKS client for ES256 verification (caches keys automatically)
_jwks_client: PyJWKClient | None = None
if SUPABASE_URL:
    _jwks_client = PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json")


@dataclass
class UserInfo:
    id: str          # UUID as string
    email: str
    tier: str        # 'free' | 'pro' | 'admin'


def _decode_token(token: str) -> dict:
    """Decode and verify a Supabase JWT. Tries JWKS (ES256) first, falls back to HS256."""
    # Try JWKS (ES256) first
    if _jwks_client:
        try:
            signing_key = _jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                options={"verify_aud": False},
            )
            return payload
        except Exception as e:
            logger.debug("JWKS decode failed, trying HS256: %s", e)

    # Fallback to HS256 with shared secret (legacy Supabase projects)
    if SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            return payload
        except jwt.InvalidTokenError as e:
            logger.warning("HS256 JWT decode failed: %s", e)
            raise HTTPException(status_code=401, detail="Invalid token")

    raise HTTPException(status_code=500, detail="Auth not configured")


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> UserInfo | None:
    """
    Optional auth dependency. Returns UserInfo if a valid token is present, None otherwise.
    Auto-creates user_profile on first login.
    """
    if not authorization:
        return None

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0] != "Bearer":
        return None

    token = parts[1]

    # Dev fallback: if no JWKS and no JWT secret, but ADMIN_SECRET_KEY matches
    admin_key = os.getenv("ADMIN_SECRET_KEY")
    if not SUPABASE_URL and not SUPABASE_JWT_SECRET and admin_key and token == admin_key:
        return UserInfo(id="dev-admin", email="admin@localhost", tier="admin")

    payload = _decode_token(token)
    user_id = payload.get("sub")
    email = payload.get("email", "")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: no sub claim")

    # Look up or auto-create user_profile
    result = await db.execute(
        text("SELECT id, email, tier FROM user_profile WHERE id = :uid"),
        {"uid": user_id},
    )
    row = result.fetchone()

    if row:
        # Update email if changed
        if row[1] != email and email:
            await db.execute(
                text("UPDATE user_profile SET email = :email WHERE id = :uid"),
                {"uid": user_id, "email": email},
            )
            await db.commit()
        return UserInfo(id=str(row[0]), email=row[1], tier=row[2])
    else:
        # Auto-create profile on first login (default tier: free)
        await db.execute(
            text("""
                INSERT INTO user_profile (id, email, display_name, tier)
                VALUES (:uid, :email, :display_name, 'free')
            """),
            {"uid": user_id, "email": email, "display_name": email.split("@")[0]},
        )
        await db.commit()
        logger.info("Auto-created user profile for %s (%s)", user_id, email)
        return UserInfo(id=user_id, email=email, tier="free")


async def require_authenticated(
    user: UserInfo | None = Depends(get_current_user),
) -> UserInfo:
    """Dependency: requires a logged-in user, any tier."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def require_admin(
    user: UserInfo = Depends(require_authenticated),
) -> UserInfo:
    """Dependency: requires an admin user."""
    if user.tier != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
