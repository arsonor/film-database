"""
Pydantic schemas for film-related API request/response models.
"""

from datetime import date

from pydantic import BaseModel, Field


# =============================================================================
# Sub-schemas used in FilmDetail
# =============================================================================


class FilmTitle(BaseModel):
    language_code: str
    language_name: str
    title: str
    is_original: bool


class CrewMember(BaseModel):
    person_id: int
    firstname: str | None
    lastname: str
    role: str
    photo_url: str | None = None


class CastMember(BaseModel):
    person_id: int
    firstname: str | None
    lastname: str
    character_name: str | None
    cast_order: int | None
    photo_url: str | None = None


class FilmSetPlaceOut(BaseModel):
    continent: str | None
    country: str | None
    state_city: str | None
    place_type: str


class SourceOut(BaseModel):
    source_type: str
    source_title: str | None
    author: str | None


class AwardOut(BaseModel):
    festival_name: str
    category: str | None
    year: int | None
    result: str | None


class FilmRelation(BaseModel):
    related_film_id: int
    related_film_title: str
    relation_type: str
    poster_url: str | None = None


# =============================================================================
# User film status
# =============================================================================


class UserFilmStatus(BaseModel):
    seen: bool = False
    favorite: bool = False
    watchlist: bool = False
    rating: int | None = None


# =============================================================================
# FilmListItem — compact, for grid display
# =============================================================================


class FilmListItem(BaseModel):
    film_id: int
    original_title: str
    first_release_date: date | None = None
    duration: int | None = None
    poster_url: str | None = None
    user_status: UserFilmStatus | None = None
    categories: list[str] = []
    director: str | None = None

    model_config = {"from_attributes": True}


# =============================================================================
# FilmDetail — full, for detail page
# =============================================================================


class FilmDetail(BaseModel):
    film_id: int
    original_title: str
    duration: int | None = None
    color: bool = True
    first_release_date: date | None = None
    summary: str | None = None
    user_status: UserFilmStatus | None = None
    poster_url: str | None = None
    backdrop_url: str | None = None
    imdb_id: str | None = None
    tmdb_id: int | None = None
    budget: int | None = None
    revenue: int | None = None
    titles: list[FilmTitle] = []
    categories: list[str] = []
    cinema_types: list[str] = []
    themes: list[str] = []
    characters: list[str] = []
    motivations: list[str] = []
    atmospheres: list[str] = []
    messages: list[str] = []
    time_periods: list[str] = []
    place_contexts: list[str] = []
    set_places: list[FilmSetPlaceOut] = []
    crew: list[CrewMember] = []
    cast: list[CastMember] = []
    studios: list[str] = []
    sources: list[SourceOut] = []
    awards: list[AwardOut] = []
    streaming_platforms: list[str] = []
    sequels: list[FilmRelation] = []

    model_config = {"from_attributes": True}


# =============================================================================
# Paginated response
# =============================================================================


class PaginatedFilms(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    items: list[FilmListItem]


# =============================================================================
# Create / Update schemas
# =============================================================================


class FilmCreate(BaseModel):
    """Schema for creating a film. Matches the structure from db_inserter."""
    film: dict
    titles: list[dict] = []
    categories: list[str] = []
    historic_subcategories: list[str] = []
    crew: list[dict] = []
    cast: list[dict] = []
    studios: list[dict] = []
    languages: list[dict] = []
    keywords: list[str] = []
    production_countries: list[str] = []
    streaming_platforms: list[str] = []
    enrichment: dict = {}


class FilmUpdate(BaseModel):
    """Schema for updating a film. All fields optional."""
    original_title: str | None = None
    duration: int | None = None
    color: bool | None = None
    first_release_date: date | None = None
    summary: str | None = None
    poster_url: str | None = None
    backdrop_url: str | None = None
    budget: int | None = None
    revenue: int | None = None
    categories: list[str] | None = None
    cinema_types: list[str] | None = None
    themes: list[str] | None = None
    characters: list[str] | None = None
    motivations: list[str] | None = None
    atmospheres: list[str] | None = None
    messages: list[str] | None = None
    time_periods: list[str] | None = None
    place_contexts: list[str] | None = None
    studios: list[str] | None = None
    streaming_platforms: list[str] | None = None
    sources: list[dict] | None = None
    set_places: list[dict] | None = None
    awards: list[dict] | None = None
