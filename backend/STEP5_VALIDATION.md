# Step 5 — Backend API: Test & Validation Procedure

## Prerequisites

- PostgreSQL running with `film_database` populated (Steps 1–4.5 completed: 3 reference films seeded)
- Python virtual environment activated
- All dependencies installed: `pip install -r backend/requirements.txt`

---

## 1. Start the API Server

```bash
cd G:\Users\Martin\GITHUB\film-database
uvicorn backend.app.main:app --reload
```

**Expected:** Server starts on `http://127.0.0.1:8000` with no errors.

Open browser: **http://localhost:8000/docs** → Swagger UI loads with all endpoints listed.

---

## 2. Test Film Endpoints

### 2.1 — GET /api/films (list, no filters)

```
GET http://localhost:8000/api/films
```

**Check:**
- `total` = 3
- `page` = 1, `per_page` = 20, `total_pages` = 1
- `items` array has 3 films
- Each item has: `film_id`, `original_title`, `first_release_date`, `duration`, `poster_url`, `vu`, `categories` (list), `director` (string)
- Default sort = year DESC → Mulholland Drive (2001), La Haine (1995), 2001: A Space Odyssey (1968)

### 2.2 — GET /api/films with pagination

```
GET http://localhost:8000/api/films?per_page=2&page=1
```

**Check:** `total` = 3, `total_pages` = 2, `items` has 2 films

```
GET http://localhost:8000/api/films?per_page=2&page=2
```

**Check:** `items` has 1 film

### 2.3 — GET /api/films with sorting

```
GET http://localhost:8000/api/films?sort_by=title&sort_order=asc
```

**Check:** Items ordered alphabetically: "2001: A Space Odyssey", "La Haine", "Mulholland Drive"

```
GET http://localhost:8000/api/films?sort_by=year&sort_order=asc
```

**Check:** Oldest first: 2001: A Space Odyssey (1968), La Haine (1995), Mulholland Drive (2001)

### 2.4 — GET /api/films with taxonomy filter

```
GET http://localhost:8000/api/films?categories=Drama
```

**Check:** Returns films classified as "Drama" (should include La Haine and others depending on enrichment)

```
GET http://localhost:8000/api/films?categories=Science-fiction
```

**Check:** Should return 2001: A Space Odyssey

```
GET http://localhost:8000/api/films?themes=Alienation
```

**Check:** Returns films matching that theme (verify against DB content)

### 2.5 — GET /api/films with year filter

```
GET http://localhost:8000/api/films?year_min=1990&year_max=2005
```

**Check:** Returns La Haine (1995) and Mulholland Drive (2001) only

```
GET http://localhost:8000/api/films?year_max=1970
```

**Check:** Returns 2001: A Space Odyssey only

### 2.6 — GET /api/films with director filter

```
GET http://localhost:8000/api/films?director=Kubrick
```

**Check:** Returns 2001: A Space Odyssey only

```
GET http://localhost:8000/api/films?director=Lynch
```

**Check:** Returns Mulholland Drive only

### 2.7 — GET /api/films with vu filter

```
GET http://localhost:8000/api/films?vu=true
```

**Check:** Returns only films marked as seen

```
GET http://localhost:8000/api/films?vu=false
```

**Check:** Returns only films marked as unseen

### 2.8 — GET /api/films with full-text search

```
GET http://localhost:8000/api/films?q=Kubrick
```

**Check:** Returns 2001: A Space Odyssey (match on crew name)

```
GET http://localhost:8000/api/films?q=Mulholland
```

**Check:** Returns Mulholland Drive (match on title)

### 2.9 — GET /api/films with combined filters

```
GET http://localhost:8000/api/films?year_min=1990&categories=Drama
```

**Check:** Returns only films that are both post-1990 AND classified as Drama

---

## 3. Test Film Detail Endpoint

### 3.1 — GET /api/films/{film_id} (valid ID)

First, note a `film_id` from the list response (e.g. film_id of "2001: A Space Odyssey").

```
GET http://localhost:8000/api/films/{film_id}
```

**Check all fields populated:**
- Core: `film_id`, `original_title`, `duration`, `color`, `first_release_date`, `summary`, `tmdb_id`, `imdb_id`
- Media: `poster_url`, `backdrop_url`
- Titles: array with at least original title (language_code, language_name, title, is_original)
- Taxonomy arrays: `categories`, `themes`, `atmospheres`, `messages`, `characters`, `motivations`, `cinema_types`, `cultural_movements`, `time_periods`, `character_contexts`, `place_contexts`
- Geography: `set_places` array with `continent`, `country`, `state_city`, `place_type`
- People: `crew` array (each: person_id, firstname, lastname, role, photo_url), `cast` array (each: person_id, firstname, lastname, character_name, cast_order, photo_url)
- Crew should include Director role for Kubrick
- Cast should list actors with character names
- `studios` array (strings)
- `sources` array (source_type, source_title, author)
- `awards` array (festival_name, category, year, result)
- `streaming_platforms` array (strings)
- `sequels` array (should be empty for these films)
- Financial: `budget`, `revenue`

### 3.2 — GET /api/films/{film_id} (invalid ID)

```
GET http://localhost:8000/api/films/99999
```

**Check:** HTTP 404 with `{"detail": "Film not found"}`

---

## 4. Test Taxonomy Endpoint

### 4.1 — GET /api/taxonomy/{dimension} (all 13 dimensions)

Test each dimension and verify response structure `{ dimension, items: [{ id, name, film_count }] }`:

```
GET http://localhost:8000/api/taxonomy/categories
GET http://localhost:8000/api/taxonomy/themes
GET http://localhost:8000/api/taxonomy/atmospheres
GET http://localhost:8000/api/taxonomy/messages
GET http://localhost:8000/api/taxonomy/characters
GET http://localhost:8000/api/taxonomy/character_contexts
GET http://localhost:8000/api/taxonomy/motivations
GET http://localhost:8000/api/taxonomy/cinema_types
GET http://localhost:8000/api/taxonomy/cultural_movements
GET http://localhost:8000/api/taxonomy/time_periods
GET http://localhost:8000/api/taxonomy/place_contexts
GET http://localhost:8000/api/taxonomy/streaming_platforms
GET http://localhost:8000/api/taxonomy/person_jobs
```

**Check for each:**
- Response has `dimension` matching the requested dimension
- `items` is a non-empty array (seed_taxonomy.sql populated all lookup tables)
- Each item has `id` (int), `name` (string), `film_count` (int ≥ 0)
- `film_count` > 0 for items linked to the 3 reference films
- Items sorted alphabetically by name
- `categories`: subcategory rows filtered out (no `historic_subcategory_name` entries)
- `person_jobs`: `film_count` always 0 (no junction table used)

### 4.2 — GET /api/taxonomy/{dimension} (invalid dimension)

```
GET http://localhost:8000/api/taxonomy/invalid_dimension
```

**Check:** HTTP 400 with error listing valid dimensions

---

## 5. Test Person Endpoints

### 5.1 — GET /api/persons/search?q=

```
GET http://localhost:8000/api/persons/search?q=Kubrick
```

**Check:**
- Returns array with at least one result
- Each result: `person_id`, `firstname`, `lastname`, `photo_url`
- Stanley Kubrick found

```
GET http://localhost:8000/api/persons/search?q=Naomi
```

**Check:** Naomi Watts found (from Mulholland Drive cast)

```
GET http://localhost:8000/api/persons/search?q=xyznonexistent
```

**Check:** Returns empty array `[]`

### 5.2 — GET /api/persons/{person_id}

Use `person_id` from the search result above (e.g. Kubrick's ID).

```
GET http://localhost:8000/api/persons/{person_id}
```

**Check:**
- Core fields: `person_id`, `firstname`, `lastname`, `gender`, `date_of_birth`, `date_of_death`, `nationality`, `tmdb_id`, `photo_url`
- `filmography` array with at least 1 entry
- Each filmography entry: `film_id`, `original_title`, `first_release_date`, `poster_url`, `roles` (list), `characters` (list)
- For Kubrick: roles should include "Director", characters should be empty
- Filmography sorted by date DESC

### 5.3 — GET /api/persons/{person_id} (invalid ID)

```
GET http://localhost:8000/api/persons/99999
```

**Check:** HTTP 404 with `{"detail": "Person not found"}`

---

## 6. Test Stats Endpoint

```
GET http://localhost:8000/api/stats
```

**Check:**
- `total_films` = 3
- `seen` + `unseen` = `total_films`
- `by_decade` array: objects with `decade` (int) and `count` (int), decades present: 1960, 1990, 2000
- `top_categories` array: objects with `name` and `count`, sorted by count DESC
- `top_countries` array: objects with `name` and `count`, sorted by count DESC

---

## 7. Test Update Endpoint

### 7.1 — PUT /api/films/{film_id} (mark as seen)

Pick a film_id, then:

```
PUT http://localhost:8000/api/films/{film_id}
Content-Type: application/json

{
    "vu": true
}
```

**Check:**
- Response: `{"film_id": ..., "message": "Film updated successfully"}`
- Verify: `GET /api/films/{film_id}` → `vu` is now `true`

### 7.2 — PUT /api/films/{film_id} (update taxonomy)

```
PUT http://localhost:8000/api/films/{film_id}
Content-Type: application/json

{
    "categories": ["Drama", "Thriller"]
}
```

**Check:**
- Response: success message
- Verify: `GET /api/films/{film_id}` → `categories` now contains exactly `["Drama", "Thriller"]`
- Old categories were cleared and replaced (clear-and-reinsert pattern)

### 7.3 — PUT /api/films/99999 (invalid ID)

```
PUT http://localhost:8000/api/films/99999
Content-Type: application/json

{"vu": true}
```

**Check:** HTTP 404

---

## 8. Test Error Handling & Edge Cases

### 8.1 — Invalid pagination

```
GET http://localhost:8000/api/films?page=0
```

**Check:** HTTP 422 (Validation Error — page must be ≥ 1)

```
GET http://localhost:8000/api/films?per_page=200
```

**Check:** HTTP 422 (Validation Error — per_page max 100)

### 8.2 — Invalid sort_by

```
GET http://localhost:8000/api/films?sort_by=invalid
```

**Check:** HTTP 422 (Validation Error — must match pattern)

### 8.3 — Empty search

```
GET http://localhost:8000/api/persons/search?q=
```

**Check:** HTTP 422 (Validation Error — min_length=1)

---

## 9. CORS Verification

From browser console (on any page), run:

```javascript
fetch('http://localhost:8000/api/films', {
    headers: { 'Origin': 'http://localhost:3000' }
}).then(r => {
    console.log('CORS headers:', r.headers.get('access-control-allow-origin'));
    return r.json();
}).then(console.log);
```

**Check:** `access-control-allow-origin: http://localhost:3000` header present, data returned.

---

## 10. Validation Summary Checklist

| # | Test | Status |
|---|------|--------|
| 1 | Server starts without errors | ⬜ |
| 2 | Swagger UI loads at /docs | ⬜ |
| 3 | GET /api/films returns 3 films | ⬜ |
| 4 | Pagination works (per_page, page) | ⬜ |
| 5 | Sorting works (title asc, year asc/desc) | ⬜ |
| 6 | Taxonomy filter works (categories, themes) | ⬜ |
| 7 | Year range filter works | ⬜ |
| 8 | Director filter works | ⬜ |
| 9 | Vu filter works | ⬜ |
| 10 | Full-text search works (title, person) | ⬜ |
| 11 | Combined filters work | ⬜ |
| 12 | Film detail returns all 20+ fields | ⬜ |
| 13 | Film detail 404 on invalid ID | ⬜ |
| 14 | All 13 taxonomy dimensions return data | ⬜ |
| 15 | Taxonomy 400 on invalid dimension | ⬜ |
| 16 | Person search returns results | ⬜ |
| 17 | Person detail with filmography works | ⬜ |
| 18 | Person 404 on invalid ID | ⬜ |
| 19 | Stats endpoint returns correct totals | ⬜ |
| 20 | PUT update core field works | ⬜ |
| 21 | PUT update taxonomy (clear+reinsert) works | ⬜ |
| 22 | PUT 404 on invalid ID | ⬜ |
| 23 | Validation errors (422) on bad input | ⬜ |
| 24 | CORS headers present for localhost:3000 | ⬜ |

---

## 11. Git Commit

Once all checks pass:

```bash
git add backend/app/
git commit -m "Step 5: FastAPI backend API — films, taxonomy, persons, stats endpoints"
git push
```
