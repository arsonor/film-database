-- Move Historical subcategories from category to cinema_type, rename them.
-- Also rename costume/period drama → costume drama.

-- 1. Add new cinema_type entries (biopic, historical event, fait divers/true incident)
--    Insert at the start of Group 5, shifting existing entries.
UPDATE cinema_type SET sort_order = sort_order + 3 WHERE sort_order >= 500;

INSERT INTO cinema_type (technique_name, sort_order) VALUES
    ('biopic', 500),
    ('historical event', 501),
    ('fait divers/true incident', 502)
ON CONFLICT (technique_name) DO NOTHING;

-- 2. Rename costume/period drama → costume drama
UPDATE cinema_type SET technique_name = 'costume drama' WHERE technique_name = 'costume/period drama';

-- 3. Migrate film associations: for each film linked to a Historical subcategory,
--    create the equivalent cinema_type link.

-- biopic
INSERT INTO film_technique (film_id, cinema_type_id)
SELECT fg.film_id, ct.cinema_type_id
FROM film_genre fg
JOIN category c ON fg.category_id = c.category_id
CROSS JOIN cinema_type ct
WHERE c.category_name = 'Historical' AND c.historic_subcategory_name = 'biopic'
  AND ct.technique_name = 'biopic'
ON CONFLICT DO NOTHING;

-- human interest story → fait divers/true incident
INSERT INTO film_technique (film_id, cinema_type_id)
SELECT fg.film_id, ct.cinema_type_id
FROM film_genre fg
JOIN category c ON fg.category_id = c.category_id
CROSS JOIN cinema_type ct
WHERE c.category_name = 'Historical' AND c.historic_subcategory_name = 'human interest story'
  AND ct.technique_name = 'fait divers/true incident'
ON CONFLICT DO NOTHING;

-- event → historical event
INSERT INTO film_technique (film_id, cinema_type_id)
SELECT fg.film_id, ct.cinema_type_id
FROM film_genre fg
JOIN category c ON fg.category_id = c.category_id
CROSS JOIN cinema_type ct
WHERE c.category_name = 'Historical' AND c.historic_subcategory_name = 'event'
  AND ct.technique_name = 'historical event'
ON CONFLICT DO NOTHING;

-- 4. Remove old film_genre links to Historic subcategories
DELETE FROM film_genre
WHERE category_id IN (
    SELECT category_id FROM category
    WHERE category_name = 'Historical' AND historic_subcategory_name IS NOT NULL
);

-- 5. Delete the Historical subcategory rows from category table
DELETE FROM category
WHERE category_name = 'Historical' AND historic_subcategory_name IS NOT NULL;
