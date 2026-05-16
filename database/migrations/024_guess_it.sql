-- Step 20: Guess It game — add decoy storage for daily challenges
ALTER TABLE daily_challenge ADD COLUMN IF NOT EXISTS decoy_film_ids INTEGER[];
