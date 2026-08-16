-- =============================================================================
-- Migration 029 — Character sub-dimension restructuring
-- =============================================================================
--
-- Pure `sort_order` renumbering inside `character_context`. No tag is added,
-- renamed or deleted, and no `film_character_context` row is touched — only the
-- sub-dimension blocks (block = sort_order / 100) change.
--
-- 1. 'Social status & traits' (block 3, 12 tags) splits into two blocks:
--      block 3 'Social status'       — ordinary, poor/marginal, wealthy,
--                                      star/celebrity, sex worker, outcast/misfit
--      block 4 'Traits & conditions' — genius, simpleton/fool, loser, disabled,
--                                      disturbed/madness, psychopath
--
-- 2. 'Narrative devices' shifts from block 4 to block 5.
--
-- 3. 'Archetypes — human' (block 5, 18 tags) splits into three blocks that keep
--    'Archetypes — human' as their shared parent heading (same mechanism as
--    Theme's "Human Relations" and Cinema Type's "Narrative techniques"):
--      block 6 'Figures & roles' — super hero, chosen one, antihero, mentor,
--                                  scientist/researcher, witch/wizard, femme fatale
--      block 7 'Law & crime'     — cop, detective, secret agent, vigilante, gangster
--      block 8 'Fighters'        — soldier, warrior, knight, samurai, pirate, viking
--
-- 4. 'Non-human & creatures' shifts from block 6 to block 9.
--
-- Blocks 1 (Group structure) and 2 (Age & identity) are unchanged.
-- Tag count stays at 59.
--
-- Idempotent: the migration assigns absolute sort_order values by tag name, so
-- re-running is a no-op.
-- =============================================================================

BEGIN;

-- ── Pre-flight snapshot ─────────────────────────────────────────────────────
DO $$
DECLARE
    n_tags  INTEGER;
    n_assoc INTEGER;
BEGIN
    SELECT count(*) INTO n_tags  FROM character_context;
    SELECT count(*) INTO n_assoc FROM film_character_context;
    RAISE NOTICE 'BEFORE: character_context tags=%, film associations=%',
                 n_tags, n_assoc;
END $$;


-- ── Renumber ────────────────────────────────────────────────────────────────
UPDATE character_context AS c
   SET sort_order = v.sort_order
  FROM (VALUES
    -- Group structure (100s) — unchanged
    ('solitary',                     100),
    ('tandem',                       101),
    ('trio',                         102),
    ('couple',                       103),
    ('relatives',                    104),
    ('generations',                  105),
    ('buddies',                      106),
    ('team/group/gang',              107),
    ('ensemble cast',                108),
    -- Age & identity (200s) — unchanged
    ('childhood',                    200),
    ('teenager',                     201),
    ('elderly',                      202),
    ('adult/child',                  203),
    ('female lead',                  204),
    ('male ensemble',                205),
    ('LGBT',                         206),
    ('interracial',                  207),
    -- Social status (300s) — was 'Social status & traits'
    ('ordinary',                     300),
    ('poor/marginal',                301),
    ('wealthy',                      302),
    ('star/celebrity',               303),
    ('sex worker',                   304),
    ('outcast/misfit',               305),
    -- Traits & conditions (400s) — new block, split off the 300s
    ('genius',                       400),
    ('simpleton/fool',               401),
    ('loser',                        402),
    ('disabled',                     403),
    ('disturbed/madness',            404),
    ('psychopath',                   405),
    -- Narrative devices (500s) — was 400s
    ('double',                       500),
    ('cross-dressing',               501),
    ('unreliable narrator',          502),
    -- Archetypes — human > Figures & roles (600s)
    ('super hero',                   600),
    ('chosen one',                   601),
    ('antihero',                     602),
    ('mentor',                       603),
    ('scientist/researcher',         604),
    ('witch/wizard',                 605),
    ('femme fatale',                 606),
    -- Archetypes — human > Law & crime (700s)
    ('cop',                          700),
    ('detective',                    701),
    ('secret agent',                 702),
    ('vigilante',                    703),
    ('gangster',                     704),
    -- Archetypes — human > Fighters (800s)
    ('soldier',                      800),
    ('warrior',                      801),
    ('knight',                       802),
    ('samurai',                      803),
    ('pirate',                       804),
    ('viking',                       805),
    -- Non-human & creatures (900s) — was 600s
    ('animal',                       900),
    ('monster/terrestrial creature', 901),
    ('devil',                        902),
    ('ghost/spirit',                 903),
    ('vampire',                      904),
    ('zombie',                       905),
    ('alien',                        906),
    ('android/robot',                907),
    ('vehicle',                      908)
  ) AS v(context_name, sort_order)
 WHERE c.context_name = v.context_name;


-- ── Post-flight assertions ──────────────────────────────────────────────────
DO $$
DECLARE
    n_tags   INTEGER;
    n_assoc  INTEGER;
    n_orphan INTEGER;
    bad      INTEGER;
BEGIN
    SELECT count(*) INTO n_tags  FROM character_context;
    SELECT count(*) INTO n_assoc FROM film_character_context;

    IF n_tags <> 59 THEN
        RAISE EXCEPTION 'character_context should hold 59 tags, found %', n_tags;
    END IF;

    -- Every tag must have landed in one of the nine blocks (nothing left at 999).
    SELECT count(*) INTO n_orphan
      FROM character_context
     WHERE sort_order / 100 NOT BETWEEN 1 AND 9;
    IF n_orphan > 0 THEN
        RAISE EXCEPTION '% character tag(s) fell outside blocks 1-9', n_orphan;
    END IF;

    -- No duplicate sort_order.
    IF EXISTS (SELECT 1 FROM character_context GROUP BY sort_order HAVING count(*) > 1) THEN
        RAISE EXCEPTION 'duplicate sort_order in character_context';
    END IF;

    -- Block sizes must match the new layout.
    SELECT count(*) INTO bad FROM (
        SELECT sort_order / 100 AS block, count(*) AS n
          FROM character_context GROUP BY 1
    ) b
    WHERE (b.block, b.n) NOT IN (
        (1,9),(2,8),(3,6),(4,6),(5,3),(6,7),(7,5),(8,6),(9,9)
    );
    IF bad > 0 THEN
        RAISE EXCEPTION 'character_context block sizes do not match the new layout';
    END IF;

    -- Spot-check the boundaries of the three new archetype blocks.
    IF (SELECT sort_order FROM character_context WHERE context_name = 'cop') <> 700
       OR (SELECT sort_order FROM character_context WHERE context_name = 'soldier') <> 800
       OR (SELECT sort_order FROM character_context WHERE context_name = 'genius') <> 400 THEN
        RAISE EXCEPTION 'archetype/trait block boundaries are wrong';
    END IF;

    RAISE NOTICE 'AFTER: character_context tags=%, film associations=% (unchanged)',
                 n_tags, n_assoc;
END $$;

COMMIT;
