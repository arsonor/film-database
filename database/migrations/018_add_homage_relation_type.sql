-- Migration 018: Add 'homage' relation type to film_sequel
-- For films that take a clear reference from another (e.g. Blow Out -> Blow-Up,
-- The Conversation; parodic films referencing specific source films).

BEGIN;

ALTER TABLE film_sequel
    DROP CONSTRAINT IF EXISTS film_sequel_relation_type_check;

ALTER TABLE film_sequel
    ADD CONSTRAINT film_sequel_relation_type_check
    CHECK (relation_type IN ('sequel', 'prequel', 'remake', 'spinoff', 'reboot', 'cycle', 'homage'));

COMMIT;
