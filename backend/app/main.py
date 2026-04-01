"""
Film Database API — FastAPI application entry point.
"""

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.auth import require_admin
from backend.app.database import engine
from backend.app.routers import add_film, films, geography, persons, taxonomy


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Film Database API",
    description="Personal film database with rich taxonomy classification",
    version="0.1.0",
    lifespan=lifespan,
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
origins = [o.strip() for o in origins if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(films.router, prefix="/api")
app.include_router(taxonomy.router, prefix="/api")
app.include_router(persons.router, prefix="/api")
app.include_router(geography.router, prefix="/api")
app.include_router(add_film.router, prefix="/api")


# =============================================================================
# Auth endpoints
# =============================================================================


class LoginRequest(BaseModel):
    password: str


@app.post("/api/auth/login")
async def auth_login(body: LoginRequest):
    admin_key = os.getenv("ADMIN_SECRET_KEY")
    if not admin_key:
        raise HTTPException(status_code=401, detail="Admin auth not configured")
    if body.password != admin_key:
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"token": body.password}


@app.get("/api/auth/check")
async def auth_check(admin: None = Depends(require_admin)):
    return {"admin": True}
