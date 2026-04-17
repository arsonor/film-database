"""
SQLAlchemy ORM models for the Film Database.

Mirrors database/schema.sql exactly.
"""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# =============================================================================
# CORE TABLE: FILM
# =============================================================================


class Film(Base):
    __tablename__ = "film"

    film_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_title: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[int | None] = mapped_column(Integer)
    color: Mapped[bool] = mapped_column(Boolean, default=True)
    first_release_date: Mapped[date | None] = mapped_column(Date)
    summary: Mapped[str | None] = mapped_column(Text)
    vu: Mapped[bool] = mapped_column(Boolean, default=False)
    poster_url: Mapped[str | None] = mapped_column(Text)
    backdrop_url: Mapped[str | None] = mapped_column(Text)
    imdb_id: Mapped[str | None] = mapped_column(String(20), unique=True)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    budget: Mapped[int | None] = mapped_column(BigInteger)
    revenue: Mapped[int | None] = mapped_column(BigInteger)
    tmdb_score: Mapped[float | None] = mapped_column(Numeric(3, 1))
    tmdb_vote_count: Mapped[int | None] = mapped_column(Integer)
    weighted_score: Mapped[float | None] = mapped_column(Numeric(4, 2))
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now)

    # Relationships for detail loading
    genres: Mapped[list["FilmGenre"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    techniques: Mapped[list["FilmTechnique"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    set_places: Mapped[list["FilmSetPlace"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    places: Mapped[list["FilmPlace"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    periods: Mapped[list["FilmPeriod"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    themes: Mapped[list["FilmTheme"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    characters: Mapped[list["FilmCharacterContext"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    atmospheres: Mapped[list["FilmAtmosphere"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    motivations: Mapped[list["FilmMotivation"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    messages: Mapped[list["FilmMessage"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    origins: Mapped[list["FilmOrigin"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    titles: Mapped[list["FilmLanguage"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    crew_entries: Mapped[list["Crew"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    cast_entries: Mapped[list["Casting"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    productions: Mapped[list["Production"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    exploitations: Mapped[list["FilmExploitation"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    awards: Mapped[list["Award"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    sequels_from: Mapped[list["FilmSequel"]] = relationship(
        back_populates="film", foreign_keys="FilmSequel.film_id", cascade="all, delete-orphan"
    )
    sequels_to: Mapped[list["FilmSequel"]] = relationship(
        back_populates="related_film", foreign_keys="FilmSequel.related_film_id", cascade="all, delete-orphan"
    )


# =============================================================================
# PEOPLE & ROLES
# =============================================================================


class Person(Base):
    __tablename__ = "person"

    person_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    firstname: Mapped[str | None] = mapped_column(Text)
    lastname: Mapped[str] = mapped_column(Text, nullable=False)
    gender: Mapped[str | None] = mapped_column(String(1))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    date_of_death: Mapped[date | None] = mapped_column(Date)
    nationality: Mapped[str | None] = mapped_column(Text)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    photo_url: Mapped[str | None] = mapped_column(Text)

    crew_entries: Mapped[list["Crew"]] = relationship(back_populates="person")
    cast_entries: Mapped[list["Casting"]] = relationship(back_populates="person")


class PersonJob(Base):
    __tablename__ = "person_job"

    job_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    crew_entries: Mapped[list["Crew"]] = relationship(back_populates="job")


class Crew(Base):
    __tablename__ = "crew"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("person.person_id", ondelete="CASCADE"), primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("person_job.job_id", ondelete="CASCADE"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="crew_entries")
    person: Mapped["Person"] = relationship(back_populates="crew_entries")
    job: Mapped["PersonJob"] = relationship(back_populates="crew_entries")


class Casting(Base):
    __tablename__ = "casting"

    cast_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), nullable=False)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("person.person_id", ondelete="CASCADE"), nullable=False)
    character_name: Mapped[str | None] = mapped_column(Text)
    cast_order: Mapped[int | None] = mapped_column(Integer)

    film: Mapped["Film"] = relationship(back_populates="cast_entries")
    person: Mapped["Person"] = relationship(back_populates="cast_entries")


# =============================================================================
# PRODUCTION
# =============================================================================


class Studio(Base):
    __tablename__ = "studio"

    studio_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    studio_name: Mapped[str] = mapped_column(Text, nullable=False)
    country_name: Mapped[str | None] = mapped_column(Text)

    productions: Mapped[list["Production"]] = relationship(back_populates="studio")


class Production(Base):
    __tablename__ = "production"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    studio_id: Mapped[int] = mapped_column(Integer, ForeignKey("studio.studio_id", ondelete="CASCADE"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="productions")
    studio: Mapped["Studio"] = relationship(back_populates="productions")


# =============================================================================
# LANGUAGE & TITLES
# =============================================================================


class Language(Base):
    __tablename__ = "language"

    language_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    language_name: Mapped[str] = mapped_column(Text, nullable=False)


class FilmLanguage(Base):
    __tablename__ = "film_language"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    language_id: Mapped[int] = mapped_column(Integer, ForeignKey("language.language_id", ondelete="CASCADE"), primary_key=True)
    film_title: Mapped[str] = mapped_column(Text, nullable=False, primary_key=True)
    is_original: Mapped[bool] = mapped_column(Boolean, default=False)
    has_dubbing: Mapped[bool] = mapped_column(Boolean, default=False)

    film: Mapped["Film"] = relationship(back_populates="titles")
    language: Mapped["Language"] = relationship()


# =============================================================================
# CLASSIFICATION: CATEGORY / GENRE
# =============================================================================


class Category(Base):
    __tablename__ = "category"
    __table_args__ = (UniqueConstraint("category_name", "historic_subcategory_name"),)

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_name: Mapped[str] = mapped_column(Text, nullable=False)
    historic_subcategory_name: Mapped[str | None] = mapped_column(Text)


class FilmGenre(Base):
    __tablename__ = "film_genre"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("category.category_id", ondelete="CASCADE"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="genres")
    category: Mapped["Category"] = relationship()


# =============================================================================
# CLASSIFICATION: CINEMA TYPE
# =============================================================================


class CinemaType(Base):
    __tablename__ = "cinema_type"

    cinema_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    technique_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=999)


class FilmTechnique(Base):
    __tablename__ = "film_technique"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    cinema_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("cinema_type.cinema_type_id", ondelete="CASCADE"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="techniques")
    cinema_type: Mapped["CinemaType"] = relationship()


# =============================================================================
# CLASSIFICATION: GEOGRAPHY & PLACE
# =============================================================================


class Geography(Base):
    __tablename__ = "geography"
    __table_args__ = (UniqueConstraint("continent", "country", "state_city"),)

    geography_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    continent: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(Text)
    state_city: Mapped[str | None] = mapped_column(Text)


class FilmSetPlace(Base):
    __tablename__ = "film_set_place"
    __table_args__ = (
        CheckConstraint("place_type IN ('diegetic', 'shooting', 'fictional')"),
    )

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    geography_id: Mapped[int] = mapped_column(Integer, ForeignKey("geography.geography_id", ondelete="CASCADE"), primary_key=True)
    place_type: Mapped[str] = mapped_column(String(20), nullable=False, primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="set_places")
    geography: Mapped["Geography"] = relationship()


class PlaceContext(Base):
    __tablename__ = "place_context"

    place_context_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    environment: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class FilmPlace(Base):
    __tablename__ = "film_place"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    place_context_id: Mapped[int] = mapped_column(Integer, ForeignKey("place_context.place_context_id", ondelete="CASCADE"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="places")
    place_context: Mapped["PlaceContext"] = relationship()


# =============================================================================
# CLASSIFICATION: TIME CONTEXT
# =============================================================================


class TimeContext(Base):
    __tablename__ = "time_context"

    time_context_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    time_period: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class FilmPeriod(Base):
    __tablename__ = "film_period"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    time_context_id: Mapped[int] = mapped_column(Integer, ForeignKey("time_context.time_context_id", ondelete="CASCADE"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="periods")
    time_context: Mapped["TimeContext"] = relationship()


# =============================================================================
# CLASSIFICATION: THEMES
# =============================================================================


class ThemeContext(Base):
    __tablename__ = "theme_context"

    theme_context_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    theme_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class FilmTheme(Base):
    __tablename__ = "film_theme"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    theme_context_id: Mapped[int] = mapped_column(Integer, ForeignKey("theme_context.theme_context_id", ondelete="CASCADE"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="themes")
    theme: Mapped["ThemeContext"] = relationship()


# =============================================================================
# CLASSIFICATION: CHARACTERS (merged types + contexts + archetypes)
# =============================================================================


class CharacterContext(Base):
    __tablename__ = "character_context"

    character_context_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    context_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=999)


class FilmCharacterContext(Base):
    __tablename__ = "film_character_context"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    character_context_id: Mapped[int] = mapped_column(Integer, ForeignKey("character_context.character_context_id", ondelete="CASCADE"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="characters")
    context: Mapped["CharacterContext"] = relationship()


# =============================================================================
# CLASSIFICATION: ATMOSPHERE
# =============================================================================


class Atmosphere(Base):
    __tablename__ = "atmosphere"

    atmosphere_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    atmosphere_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class FilmAtmosphere(Base):
    __tablename__ = "film_atmosphere"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    atmosphere_id: Mapped[int] = mapped_column(Integer, ForeignKey("atmosphere.atmosphere_id", ondelete="CASCADE"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="atmospheres")
    atmosphere: Mapped["Atmosphere"] = relationship()


# =============================================================================
# CLASSIFICATION: MOTIVATIONS & RELATIONS
# =============================================================================


class MotivationRelation(Base):
    __tablename__ = "motivation_relation"

    motivation_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    motivation_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class FilmMotivation(Base):
    __tablename__ = "film_motivation"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    motivation_id: Mapped[int] = mapped_column(Integer, ForeignKey("motivation_relation.motivation_id", ondelete="CASCADE"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="motivations")
    motivation: Mapped["MotivationRelation"] = relationship()


# =============================================================================
# CLASSIFICATION: MESSAGE CONVEYED
# =============================================================================


class MessageConveyed(Base):
    __tablename__ = "message_conveyed"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class FilmMessage(Base):
    __tablename__ = "film_message"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("message_conveyed.message_id", ondelete="CASCADE"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="messages")
    message: Mapped["MessageConveyed"] = relationship()


# =============================================================================
# FILM RELATIONSHIPS
# =============================================================================


class FilmSequel(Base):
    __tablename__ = "film_sequel"
    __table_args__ = (
        CheckConstraint("relation_type IN ('sequel', 'prequel', 'remake', 'spinoff', 'reboot')"),
    )

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    related_film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    relation_type: Mapped[str] = mapped_column(String(20), nullable=False)

    film: Mapped["Film"] = relationship(back_populates="sequels_from", foreign_keys=[film_id])
    related_film: Mapped["Film"] = relationship(back_populates="sequels_to", foreign_keys=[related_film_id])


# =============================================================================
# SOURCE / ORIGIN
# =============================================================================


class Source(Base):
    __tablename__ = "source"

    source_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_title: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(Text)


class FilmOrigin(Base):
    __tablename__ = "film_origin"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("source.source_id", ondelete="CASCADE"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="origins")
    source: Mapped["Source"] = relationship()


# =============================================================================
# EXPLOITATION / STREAMING
# =============================================================================


class StreamPlatform(Base):
    __tablename__ = "stream_platform"

    platform_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class FilmExploitation(Base):
    __tablename__ = "film_exploitation"

    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), primary_key=True)
    platform_id: Mapped[int] = mapped_column(Integer, ForeignKey("stream_platform.platform_id", ondelete="CASCADE"), primary_key=True)

    film: Mapped["Film"] = relationship(back_populates="exploitations")
    platform: Mapped["StreamPlatform"] = relationship()


# =============================================================================
# AWARDS
# =============================================================================


class Award(Base):
    __tablename__ = "award"
    __table_args__ = (
        CheckConstraint("result IN ('won', 'nominated')"),
    )

    award_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    film_id: Mapped[int] = mapped_column(Integer, ForeignKey("film.film_id", ondelete="CASCADE"), nullable=False)
    festival_name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(Text)
    award_year: Mapped[int | None] = mapped_column(Integer)
    result: Mapped[str | None] = mapped_column(String(20))

    film: Mapped["Film"] = relationship(back_populates="awards")
