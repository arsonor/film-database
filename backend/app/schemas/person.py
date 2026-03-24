"""
Pydantic schemas for person-related API responses.
"""

from datetime import date

from pydantic import BaseModel


class PersonSummary(BaseModel):
    person_id: int
    firstname: str | None = None
    lastname: str
    photo_url: str | None = None

    model_config = {"from_attributes": True}


class FilmographyEntry(BaseModel):
    film_id: int
    original_title: str
    first_release_date: date | None = None
    poster_url: str | None = None
    roles: list[str] = []
    characters: list[str] = []


class PersonDetail(PersonSummary):
    gender: str | None = None
    date_of_birth: date | None = None
    date_of_death: date | None = None
    nationality: str | None = None
    tmdb_id: int | None = None
    filmography: list[FilmographyEntry] = []
