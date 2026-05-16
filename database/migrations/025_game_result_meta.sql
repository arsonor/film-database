-- Step 20 follow-up: store difficulty + pool filters on each game result
-- so history can display them and the share caption can replay them.
ALTER TABLE game_result ADD COLUMN IF NOT EXISTS difficulty TEXT;
ALTER TABLE game_result ADD COLUMN IF NOT EXISTS pool_filters JSONB;
