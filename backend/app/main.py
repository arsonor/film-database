"""
Film Database API — FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(films.router, prefix="/api")
app.include_router(taxonomy.router, prefix="/api")
app.include_router(persons.router, prefix="/api")
app.include_router(geography.router, prefix="/api")
app.include_router(add_film.router, prefix="/api")
