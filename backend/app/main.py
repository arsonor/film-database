"""
Film Database API — FastAPI application entry point.
"""

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.auth import UserInfo, require_authenticated
from backend.app.database import engine
from backend.app.routers import add_film, films, geography, persons, taxonomy, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Film Database API",
    description="Personal film database with rich taxonomy classification",
    version="0.2.0",
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
app.include_router(users.router, prefix="/api")


# =============================================================================
# Auth endpoints
# =============================================================================


@app.get("/api/auth/me")
async def auth_me(user: UserInfo = Depends(require_authenticated)):
    return {"id": user.id, "email": user.email, "tier": user.tier}
