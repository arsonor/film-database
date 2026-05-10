-- Migration 021: Group studios by parent family
--
-- TMDB returns dozens of regional / sub-label variants for the same studio
-- family (e.g. Warner Bros. Pictures, Warner Bros. Animation, Warner Bros.-
-- Seven Arts, Warner Bros Pictures Italia...). For dashboard stats and the
-- filter sidebar we want a single canonical group name per family.
--
-- Strategy: keep `studio_name` exactly as TMDB provides it (so per-film
-- detail still shows the precise sub-label) and add a nullable
-- `studio_group` column that names the umbrella family. Filtering and
-- stats queries should match on COALESCE(studio_group, studio_name) so
-- ungrouped studios fall back to their own name.
--
-- The actual mapping of studios → group names is applied by
-- `scripts/group_studios.py`, which can be re-run safely whenever new
-- studios appear in the DB.

ALTER TABLE studio
    ADD COLUMN IF NOT EXISTS studio_group TEXT;

COMMENT ON COLUMN studio.studio_group IS
    'Canonical parent-studio name (e.g. "Warner Bros."). Populated by '
    'scripts/group_studios.py from a curated regex mapping. NULL for '
    'studios that do not belong to a known family — queries should '
    'COALESCE(studio_group, studio_name).';

CREATE INDEX IF NOT EXISTS idx_studio_studio_group ON studio(studio_group);
