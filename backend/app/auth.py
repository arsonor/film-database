"""
Admin authentication dependency for FastAPI.
"""

import os
from fastapi import Header, HTTPException


async def require_admin(authorization: str | None = Header(default=None)) -> None:
    admin_key = os.getenv("ADMIN_SECRET_KEY")

    # Dev fallback: if no key configured, allow all requests
    if not admin_key:
        return

    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0] != "Bearer" or parts[1] != admin_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
