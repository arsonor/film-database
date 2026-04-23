-- Migration 017: Add 'cycle' relation type to film_sequel
-- For thematically linked films by the same director (diptychs, trilogies, etc.)

BEGIN;

ALTER TABLE film_sequel
    DROP CONSTRAINT IF EXISTS film_sequel_relation_type_check;

ALTER TABLE film_sequel
    ADD CONSTRAINT film_sequel_relation_type_check
    CHECK (relation_type IN ('sequel', 'prequel', 'remake', 'spinoff', 'reboot', 'cycle'));

COMMIT;
