-- =============================================================================
-- verify_taxonomy_v2.sql — post-migration checks for Taxonomy v2 (step 21a)
-- =============================================================================
-- Usage:
--   psql -U postgres -d film_database -f database/verify_taxonomy_v2.sql
--
-- Read-only. Every "CHECK" block prints PASS or FAIL; the listings at the end
-- must match Part 4 of the Step 21a spec / "Taxonomy dimensions & tags.txt".
-- =============================================================================

\pset pager off

\echo '============================================================'
\echo ' 1. Tag counts per dimension'
\echo '============================================================'

SELECT dimension, tags, expected,
       CASE WHEN tags = expected THEN 'PASS' ELSE 'FAIL' END AS status
FROM (
    SELECT 'category (Genre)'          AS dimension, (SELECT count(*) FROM category)          AS tags, 55 AS expected, 1 AS ord
    UNION ALL SELECT 'theme_context (Theme)',        (SELECT count(*) FROM theme_context),      96, 2
    UNION ALL SELECT 'time_context (Time Period)',   (SELECT count(*) FROM time_context),       22, 3
    UNION ALL SELECT 'place_context (Place)',        (SELECT count(*) FROM place_context),      29, 4
    UNION ALL SELECT 'atmosphere (Atmosphere)',      (SELECT count(*) FROM atmosphere),         25, 5
    UNION ALL SELECT 'character_context (Character)',(SELECT count(*) FROM character_context),  59, 6
    UNION ALL SELECT 'cinema_type (Cinema Type)',    (SELECT count(*) FROM cinema_type),        40, 7
) x ORDER BY ord;

\echo '============================================================'
\echo ' 2. Dissolved dimensions are empty (tables still present)'
\echo '============================================================'

SELECT relation, rows,
       CASE WHEN rows = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM (
    SELECT 'motivation_relation' AS relation, (SELECT count(*) FROM motivation_relation) AS rows, 1 AS ord
    UNION ALL SELECT 'message_conveyed', (SELECT count(*) FROM message_conveyed), 2
    UNION ALL SELECT 'film_motivation',  (SELECT count(*) FROM film_motivation),  3
    UNION ALL SELECT 'film_message',     (SELECT count(*) FROM film_message),     4
) x ORDER BY ord;

\echo '============================================================'
\echo ' 3. No duplicate tag names, no orphan junction rows'
\echo '============================================================'

-- Duplicate names per lookup (category checked on the flat-genre key).
SELECT 'duplicate tag names' AS check_name, count(*) AS offenders,
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM (
    SELECT category_name FROM category WHERE historic_subcategory_name IS NULL
     GROUP BY category_name HAVING count(*) > 1
    UNION ALL SELECT theme_name    FROM theme_context     GROUP BY theme_name     HAVING count(*) > 1
    UNION ALL SELECT time_period   FROM time_context      GROUP BY time_period    HAVING count(*) > 1
    UNION ALL SELECT environment   FROM place_context     GROUP BY environment    HAVING count(*) > 1
    UNION ALL SELECT atmosphere_name FROM atmosphere      GROUP BY atmosphere_name HAVING count(*) > 1
    UNION ALL SELECT context_name  FROM character_context GROUP BY context_name   HAVING count(*) > 1
    UNION ALL SELECT technique_name FROM cinema_type      GROUP BY technique_name HAVING count(*) > 1
) d;

-- Orphan junction rows (dangling tag FK or dangling film FK).
SELECT 'orphan junction rows' AS check_name, count(*) AS offenders,
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM (
    SELECT 1 FROM film_genre j LEFT JOIN category c USING (category_id)
      LEFT JOIN film f USING (film_id) WHERE c.category_id IS NULL OR f.film_id IS NULL
    UNION ALL
    SELECT 1 FROM film_theme j LEFT JOIN theme_context t USING (theme_context_id)
      LEFT JOIN film f USING (film_id) WHERE t.theme_context_id IS NULL OR f.film_id IS NULL
    UNION ALL
    SELECT 1 FROM film_period j LEFT JOIN time_context t USING (time_context_id)
      LEFT JOIN film f USING (film_id) WHERE t.time_context_id IS NULL OR f.film_id IS NULL
    UNION ALL
    SELECT 1 FROM film_place j LEFT JOIN place_context p USING (place_context_id)
      LEFT JOIN film f USING (film_id) WHERE p.place_context_id IS NULL OR f.film_id IS NULL
    UNION ALL
    SELECT 1 FROM film_atmosphere j LEFT JOIN atmosphere a USING (atmosphere_id)
      LEFT JOIN film f USING (film_id) WHERE a.atmosphere_id IS NULL OR f.film_id IS NULL
    UNION ALL
    SELECT 1 FROM film_character_context j LEFT JOIN character_context c USING (character_context_id)
      LEFT JOIN film f USING (film_id) WHERE c.character_context_id IS NULL OR f.film_id IS NULL
    UNION ALL
    SELECT 1 FROM film_technique j LEFT JOIN cinema_type ct USING (cinema_type_id)
      LEFT JOIN film f USING (film_id) WHERE ct.cinema_type_id IS NULL OR f.film_id IS NULL
) o;

-- Every Genre row must be flat (the composite mechanism is inert in v2).
SELECT 'genre rows with a historic subcategory' AS check_name, count(*) AS offenders,
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM category WHERE historic_subcategory_name IS NOT NULL;

-- No tag left on the default sort_order.
SELECT 'tags without an explicit sort_order' AS check_name, count(*) AS offenders,
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM (
    SELECT 1 FROM category          WHERE sort_order IS NULL OR sort_order = 999
    UNION ALL SELECT 1 FROM theme_context     WHERE sort_order IS NULL OR sort_order = 999
    UNION ALL SELECT 1 FROM time_context      WHERE sort_order IS NULL OR sort_order = 999
    UNION ALL SELECT 1 FROM place_context     WHERE sort_order IS NULL OR sort_order = 999
    UNION ALL SELECT 1 FROM atmosphere        WHERE sort_order IS NULL OR sort_order = 999
    UNION ALL SELECT 1 FROM character_context WHERE sort_order IS NULL OR sort_order = 999
    UNION ALL SELECT 1 FROM cinema_type       WHERE sort_order IS NULL OR sort_order = 999
) s;

-- tag_description must no longer reference the dissolved dimensions.
SELECT 'tag_description rows on motivations/messages' AS check_name, count(*) AS offenders,
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM tag_description WHERE dimension IN ('motivations', 'messages');

-- tag_description rows pointing at a tag that no longer exists.
SELECT 'tag_description rows with no matching tag' AS check_name, count(*) AS offenders,
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM tag_description td
WHERE NOT EXISTS (
    SELECT 1 FROM category          WHERE td.dimension = 'categories'     AND category_name   = td.tag_name
    UNION ALL SELECT 1 FROM theme_context     WHERE td.dimension = 'themes'         AND theme_name      = td.tag_name
    UNION ALL SELECT 1 FROM time_context      WHERE td.dimension = 'time_periods'   AND time_period     = td.tag_name
    UNION ALL SELECT 1 FROM place_context     WHERE td.dimension = 'place_contexts' AND environment     = td.tag_name
    UNION ALL SELECT 1 FROM atmosphere        WHERE td.dimension = 'atmospheres'    AND atmosphere_name = td.tag_name
    UNION ALL SELECT 1 FROM character_context WHERE td.dimension = 'characters'     AND context_name    = td.tag_name
    UNION ALL SELECT 1 FROM cinema_type       WHERE td.dimension = 'cinema_types'   AND technique_name  = td.tag_name
);

\echo '============================================================'
\echo ' 4. Association preservation — reference films'
\echo '============================================================'

-- 2001: A Space Odyssey — the merged genre odyssey/quest (from motivations)
-- and the themes philosophical / metaphysical (from messages).
SELECT '2001 - moved/merged tags' AS check_name, count(*) AS found, 3 AS expected,
       CASE WHEN count(*) = 3 THEN 'PASS' ELSE 'FAIL' END AS status
FROM (
    SELECT 1 FROM film f JOIN film_genre fg USING (film_id) JOIN category c USING (category_id)
     WHERE f.original_title ILIKE '2001%Space Odyssey%' AND c.category_name = 'odyssey/quest'
    UNION ALL
    SELECT 1 FROM film f JOIN film_theme ft USING (film_id) JOIN theme_context t USING (theme_context_id)
     WHERE f.original_title ILIKE '2001%Space Odyssey%' AND t.theme_name IN ('philosophical', 'metaphysical')
) x;

-- Mulholland Drive — atmosphere dreamlike/surreal (merge), genre
-- mafia/organized crime (merge), and the 8 motivations now living in Theme.
SELECT 'Mulholland Drive - merges' AS check_name, count(*) AS found, 2 AS expected,
       CASE WHEN count(*) = 2 THEN 'PASS' ELSE 'FAIL' END AS status
FROM (
    SELECT 1 FROM film f JOIN film_atmosphere fa USING (film_id) JOIN atmosphere a USING (atmosphere_id)
     WHERE f.original_title ILIKE 'Mulholland Dr%' AND a.atmosphere_name = 'dreamlike/surreal'
    UNION ALL
    SELECT 1 FROM film f JOIN film_genre fg USING (film_id) JOIN category c USING (category_id)
     WHERE f.original_title ILIKE 'Mulholland Dr%' AND c.category_name = 'mafia/organized crime'
) x;

-- NB: the 8 motivations the film actually carried in the DB. CLAUDE.md's ground
-- truth lists 'obsession', but the stored record has 'greed/ambition' instead —
-- verified against the pre-migration dump, so this is the real "before" set.
SELECT 'Mulholland Drive - motivations now themes' AS check_name, count(*) AS found, 8 AS expected,
       CASE WHEN count(*) = 8 THEN 'PASS' ELSE 'FAIL' END AS status
FROM film f JOIN film_theme ft USING (film_id) JOIN theme_context t USING (theme_context_id)
WHERE f.original_title ILIKE 'Mulholland Dr%'
  AND t.theme_name IN ('love','greed/ambition','jealousy','manipulation','lie','sex','adultery','vengeance');

-- La Haine — motivations + messages now themes, and 'tragedy' now a genre.
SELECT 'La Haine - motivations/messages now themes' AS check_name, count(*) AS found, 7 AS expected,
       CASE WHEN count(*) = 7 THEN 'PASS' ELSE 'FAIL' END AS status
FROM film f JOIN film_theme ft USING (film_id) JOIN theme_context t USING (theme_context_id)
WHERE f.original_title ILIKE 'La Haine%'
  AND t.theme_name IN ('friendship','solidarity','rebellion/revolt','vengeance','fight','political','humanist');

SELECT 'La Haine - tragedy moved to Genre' AS check_name, count(*) AS found, 1 AS expected,
       CASE WHEN count(*) = 1 THEN 'PASS' ELSE 'FAIL' END AS status
FROM film f JOIN film_genre fg USING (film_id) JOIN category c USING (category_id)
WHERE f.original_title ILIKE 'La Haine%' AND c.category_name = 'tragedy';

\echo '============================================================'
\echo ' 5. Global association totals (post-migration)'
\echo '============================================================'

SELECT 'film_genre' AS junction, count(*) FROM film_genre
UNION ALL SELECT 'film_theme',      count(*) FROM film_theme
UNION ALL SELECT 'film_period',     count(*) FROM film_period
UNION ALL SELECT 'film_place',      count(*) FROM film_place
UNION ALL SELECT 'film_atmosphere', count(*) FROM film_atmosphere
UNION ALL SELECT 'film_character_context', count(*) FROM film_character_context
UNION ALL SELECT 'film_technique',  count(*) FROM film_technique
UNION ALL SELECT 'TOTAL (7 dims)',
       (SELECT count(*) FROM film_genre) + (SELECT count(*) FROM film_theme)
     + (SELECT count(*) FROM film_period) + (SELECT count(*) FROM film_place)
     + (SELECT count(*) FROM film_atmosphere) + (SELECT count(*) FROM film_character_context)
     + (SELECT count(*) FROM film_technique);

-- Every tag with its usage count; a moved tag with 0 films where it used to
-- have some would show up here.
\echo '------------------------------------------------------------'
\echo ' Tags that ended up with zero films (expected: only new tags)'
\echo '------------------------------------------------------------'

SELECT 'categories' AS dimension, c.category_name AS tag, c.sort_order
  FROM category c LEFT JOIN film_genre fg USING (category_id)
 GROUP BY 1,2,3 HAVING count(fg.film_id) = 0
UNION ALL
SELECT 'themes', t.theme_name, t.sort_order
  FROM theme_context t LEFT JOIN film_theme ft USING (theme_context_id)
 GROUP BY 1,2,3 HAVING count(ft.film_id) = 0
UNION ALL
SELECT 'time_periods', tc.time_period, tc.sort_order
  FROM time_context tc LEFT JOIN film_period fp USING (time_context_id)
 GROUP BY 1,2,3 HAVING count(fp.film_id) = 0
UNION ALL
SELECT 'place_contexts', p.environment, p.sort_order
  FROM place_context p LEFT JOIN film_place fpl USING (place_context_id)
 GROUP BY 1,2,3 HAVING count(fpl.film_id) = 0
UNION ALL
SELECT 'atmospheres', a.atmosphere_name, a.sort_order
  FROM atmosphere a LEFT JOIN film_atmosphere fa USING (atmosphere_id)
 GROUP BY 1,2,3 HAVING count(fa.film_id) = 0
UNION ALL
SELECT 'characters', cc.context_name, cc.sort_order
  FROM character_context cc LEFT JOIN film_character_context fcc USING (character_context_id)
 GROUP BY 1,2,3 HAVING count(fcc.film_id) = 0
UNION ALL
SELECT 'cinema_types', ct.technique_name, ct.sort_order
  FROM cinema_type ct LEFT JOIN film_technique fte USING (cinema_type_id)
 GROUP BY 1,2,3 HAVING count(fte.film_id) = 0
ORDER BY 1, 3;

\echo '============================================================'
\echo ' 6. Full per-dimension listing (must match the v2 document)'
\echo '============================================================'

\echo '--- GENRE ---------------------------------------------------'
SELECT sort_order, category_name AS tag FROM category ORDER BY sort_order;

\echo '--- THEME ---------------------------------------------------'
SELECT sort_order, theme_name AS tag FROM theme_context ORDER BY sort_order;

\echo '--- TIME PERIOD ---------------------------------------------'
SELECT sort_order, time_period AS tag FROM time_context ORDER BY sort_order;

\echo '--- PLACE ---------------------------------------------------'
SELECT sort_order, environment AS tag FROM place_context ORDER BY sort_order;

\echo '--- ATMOSPHERE ----------------------------------------------'
SELECT sort_order, atmosphere_name AS tag FROM atmosphere ORDER BY sort_order;

\echo '--- CHARACTER -----------------------------------------------'
SELECT sort_order, context_name AS tag FROM character_context ORDER BY sort_order;

\echo '--- CINEMA TYPE ---------------------------------------------'
SELECT sort_order, technique_name AS tag FROM cinema_type ORDER BY sort_order;
