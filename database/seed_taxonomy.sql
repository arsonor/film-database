-- Film Database Seed Data
-- Pre-populate all taxonomy/lookup tables with reference values
-- Uses ON CONFLICT DO NOTHING for idempotent execution

-- =============================================================================
-- PERSON_JOB - Crew roles
-- =============================================================================

INSERT INTO person_job (role_name) VALUES
    ('Director'),
    ('Writer'),
    ('Cinematographer'),
    ('Composer'),
    ('Producer'),
    ('Editor'),
    ('Art Director'),
    ('Costume Designer'),
    ('Sound Designer'),
    ('Executive Producer'),
    ('Co-Producer'),
    ('Associate Producer'),
    ('Line Producer'),
    ('Production Designer'),
    ('Set Decorator'),
    ('Makeup Artist'),
    ('Hair Stylist'),
    ('Visual Effects Supervisor'),
    ('Stunt Coordinator'),
    ('Casting Director')
ON CONFLICT (role_name) DO NOTHING;

-- =============================================================================
-- CATEGORY (Genre) - 55 tags
-- Main genres occupy the 100s block; everything from 200 up is a sub-genre.
-- "Is a main genre" == sort_order < 200. All rows are flat
-- (historic_subcategory_name IS NULL); the composite mechanism is inert.
-- =============================================================================

INSERT INTO category (category_name, historic_subcategory_name, sort_order) VALUES
    -- Main (100s)
    ('Drama', NULL, 100),
    ('Comedy', NULL, 101),
    ('Romance', NULL, 102),
    ('Historical', NULL, 103),
    ('Action', NULL, 104),
    ('Adventure', NULL, 105),
    ('Thriller', NULL, 106),
    ('Science-Fiction', NULL, 107),
    ('Fantasy', NULL, 108),
    ('Horror', NULL, 109),
    ('Musical', NULL, 110),
    ('Documentary', NULL, 111),
    -- Sub-genres: Drama / Romance (200s)
    ('melodrama', NULL, 200),
    ('coming of age', NULL, 201),
    ('slice of life', NULL, 202),
    ('tragedy', NULL, 203),
    -- Sub-genres: Comedy (300s)
    ('parodic', NULL, 300),
    ('satirical', NULL, 301),
    ('absurdist', NULL, 302),
    ('black comedy', NULL, 303),
    -- Sub-genres: Thriller / Adventure (400s)
    ('psychological', NULL, 400),
    ('war', NULL, 401),
    ('crime', NULL, 402),
    ('investigation', NULL, 403),
    ('spy', NULL, 404),
    ('heist', NULL, 405),
    ('mafia/organized crime', NULL, 406),
    ('serial killer', NULL, 407),
    ('survival', NULL, 408),
    ('chase/escape', NULL, 409),
    ('odyssey/quest', NULL, 410),
    ('disaster', NULL, 411),
    ('apocalypse', NULL, 412),
    -- Sub-genres: Historical / Justice (500s)
    ('trial/judicial chronicle', NULL, 500),
    ('prison', NULL, 501),
    ('biopic', NULL, 502),
    ('fait divers/true incident', NULL, 503),
    ('western', NULL, 504),
    ('peplum', NULL, 505),
    ('swashbuckler', NULL, 506),
    ('costume drama', NULL, 507),
    ('wu xia pian', NULL, 508),
    ('revisionist/alternate history', NULL, 509),
    -- Sub-genres: Sci-fi / Fantasy (600s)
    ('supernatural', NULL, 600),
    ('whimsical/zany', NULL, 601),
    ('dystopia', NULL, 602),
    ('tales and legends', NULL, 603),
    -- Sub-genres: Horror (700s)
    ('jumpscare', NULL, 700),
    ('slasher', NULL, 701),
    ('gore', NULL, 702),
    ('body horror', NULL, 703),
    ('gothic horror', NULL, 704),
    ('folk horror', NULL, 705),
    -- Sub-genres: Miscellaneous (800s)
    ('docufiction', NULL, 800),
    ('martial arts', NULL, 801)
ON CONFLICT (category_name) WHERE historic_subcategory_name IS NULL DO NOTHING;

-- =============================================================================
-- CINEMA_TYPE (Cinema Type) - 40 tags
-- =============================================================================

INSERT INTO cinema_type (technique_name, sort_order) VALUES
    -- Visual techniques (100s)
    ('animation', 100),
    ('mixed animation', 101),
    ('CGI', 102),
    ('3D', 103),
    ('motion capture', 104),
    ('black and white', 105),
    ('aesthetics', 106),
    ('found footage', 107),
    ('dogma', 108),
    -- Industry & culture (200s)
    ('blockbuster', 200),
    ('art house', 201),
    ('B', 202),
    ('franchise', 203),
    ('popular culture', 204),
    -- Narrative techniques > Sequencing (300s)
    ('chapters/multi-sequence', 300),
    ('flashback/non linear', 301),
    ('real time', 302),
    ('timelapse', 303),
    ('slow-motion', 304),
    ('sequence-shot', 305),
    ('split screen', 306),
    ('musical montage', 307),
    -- Narrative techniques > Voice & Dialogue (400s)
    ('dialogs/punchline', 400),
    ('slang dialogs', 401),
    ('few/no dialogs', 402),
    ('voiceover', 403),
    ('monologue', 404),
    ('fourth wall break', 405),
    -- Movements & eras (500s)
    ('silent', 500),
    ('expressionism', 501),
    ('realism', 502),
    ('neo-realism', 503),
    ('noir', 504),
    ('hollywood golden age', 505),
    ('new hollywood', 506),
    ('new wave', 507),
    ('slow cinema', 508),
    ('neo-noir', 509),
    ('blaxploitation', 510),
    ('giallo', 511)
ON CONFLICT (technique_name) DO NOTHING;

-- =============================================================================
-- PLACE_CONTEXT (Place) - 29 tags
-- =============================================================================

INSERT INTO place_context (environment, sort_order) VALUES
    -- Environments (100s)
    ('urban', 100),
    ('small town', 101),
    ('rural', 102),
    ('forest', 103),
    ('mountains', 104),
    ('desert', 105),
    ('beach', 106),
    ('maritime', 107),
    ('island', 108),
    ('underground', 109),
    ('space', 110),
    ('planet', 111),
    -- Buildings & institutions (200s)
    ('building', 200),
    ('household/house/apartment', 201),
    ('company/factory', 202),
    ('school/university', 203),
    ('hospital', 204),
    ('jail', 205),
    ('military', 206),
    ('naval', 207),
    ('castle', 208),
    ('hotel', 209),
    -- Narrative settings (300s)
    ('road movie', 300),
    ('huis clos/confined setting', 301),
    -- Vehicles (400s)
    ('car/bus', 400),
    ('train', 401),
    ('airplane', 402),
    ('ship', 403),
    -- None (500)
    ('no particular', 500)
ON CONFLICT (environment) DO NOTHING;

-- =============================================================================
-- TIME_CONTEXT (Time Period) - 22 tags
-- Year ranges: future 2030+ | contemporary 2020-2029 | 2000-2010's 2000-2019 |
-- 1980-90's 1980-1999 | 1950-60-70's 1946-1979 | WW2 1939-1945 |
-- 1920-30's 1919-1938 | WW1 1914-1918 | 1900-1910's 1900-1913 | 19th 1800-1899 |
-- modern age 1500-1799 | medieval 500-1500 | antiquity 3000 BC-500 AD |
-- prehistoric before recorded civilization | undetermined no identifiable period
-- =============================================================================

INSERT INTO time_context (time_period, sort_order) VALUES
    -- Chronological (future -> prehistoric)
    ('future', 1),
    ('contemporary', 2),
    ('2000-2010''s', 3),
    ('1980-90''s', 4),
    ('1950-60-70''s', 5),
    ('WW2', 6),
    ('1920-30''s', 7),
    ('WW1', 8),
    ('1900-1910''s', 9),
    ('19th', 10),
    ('modern age', 11),
    ('medieval', 12),
    ('antiquity', 13),
    ('prehistoric', 14),
    ('undetermined', 15),
    -- Time span (100s)
    ('single day', 100),
    ('several years', 101),
    ('decades-spanning', 102),
    -- Seasons (200s)
    ('spring', 200),
    ('summer', 201),
    ('autumn', 202),
    ('winter', 203)
ON CONFLICT (time_period) DO NOTHING;

-- =============================================================================
-- THEME_CONTEXT (Theme) - 96 tags
-- Hierarchical themes use the "parent: sub" convention (e.g. "art: cinema")
-- =============================================================================

INSERT INTO theme_context (theme_name, sort_order) VALUES
    -- Society & World (100s)
    ('social', 100),
    ('societal', 101),
    ('generational', 102),
    ('political', 103),
    ('religion', 104),
    ('business', 105),
    ('journalism/media', 106),
    ('censorship', 107),
    ('conspiracy', 108),
    ('sect', 109),
    ('immigration', 110),
    ('colonialism', 111),
    ('slavery', 112),
    ('nature/wildlife', 113),
    ('AI/technology', 114),
    -- Values & Reflection (200s)
    ('humanist', 200),
    ('feminist', 201),
    ('nostalgic', 202),
    ('ecological', 203),
    ('patriotic', 204),
    ('anti establishment', 205),
    ('traditionalist/way of life', 206),
    ('philosophical', 207),
    ('metaphysical', 208),
    -- Human Relations > Bonds & attachments (300s)
    ('love', 300),
    ('friendship', 301),
    ('solidarity', 302),
    ('communication', 303),
    ('family/parenthood', 304),
    -- Human Relations > Desire & transgression (400s)
    ('power', 400),
    ('manipulation', 401),
    ('sex', 402),
    ('adultery', 403),
    ('jealousy', 404),
    ('perversion', 405),
    -- Human Relations > Interpersonal conflict (500s)
    ('class/culture clash', 500),
    ('rivalry', 501),
    ('fight', 502),
    ('rebellion/revolt', 503),
    ('vengeance', 504),
    ('harassment', 505),
    -- Human Relations > Crime & abuse of power (600s)
    ('delinquency', 600),
    ('police violence', 601),
    ('sex crime', 602),
    ('kidnapping/hostage', 603),
    ('trafficking/fraud', 604),
    ('corruption', 605),
    ('terrorism', 606),
    -- Personal / Inner conflict > Wounds & burdens (700s)
    ('trauma/accident', 700),
    ('identity crisis', 701),
    ('illness', 702),
    ('amnesia', 703),
    ('death', 704),
    ('grief/mourning', 705),
    ('addiction/drugs', 706),
    ('loneliness', 707),
    ('guilt', 708),
    -- Personal / Inner conflict > Drives & arcs (800s)
    ('obsession', 800),
    ('greed/ambition', 801),
    ('doubt/dilemma', 802),
    ('lie', 803),
    ('sacrifice', 804),
    ('honor/duty', 805),
    ('emancipation', 806),
    ('redemption', 807),
    ('transformation', 808),
    ('time passing', 809),
    ('dream', 810),
    -- Art, Sport & Entertainment > Art (900s)
    ('art', 900),
    ('art: music/dance', 901),
    ('art: cinema', 902),
    ('art: literature', 903),
    ('art: fashion', 904),
    ('art: painting', 905),
    ('art: sculpture', 906),
    ('art: theatre', 907),
    ('art: radio', 908),
    ('art: architecture', 909),
    -- Art, Sport & Entertainment > Sport (1000s)
    ('sport', 1000),
    ('sport: individual', 1001),
    ('sport: collective', 1002),
    ('sport: tournament', 1003),
    ('sport: motor', 1004),
    -- Art, Sport & Entertainment > Entertainment (1100s)
    ('food/cooking', 1100),
    ('party', 1101),
    ('game', 1102),
    ('gambling', 1103),
    ('contest', 1104),
    -- Face to the unknown (1200s)
    ('sorcery', 1200),
    ('alien contact', 1201),
    ('paranormal', 1202),
    ('curse', 1203),
    ('time travel/loop', 1204),
    ('virtual/parallel universe', 1205),
    ('invasion', 1206),
    ('exploration', 1207)
ON CONFLICT (theme_name) DO NOTHING;

-- =============================================================================
-- CHARACTER_CONTEXT (Character) - 59 tags
-- =============================================================================

INSERT INTO character_context (context_name, sort_order) VALUES
    -- Group structure (100s)
    ('solitary', 100),
    ('tandem', 101),
    ('trio', 102),
    ('couple', 103),
    ('relatives', 104),
    ('generations', 105),
    ('buddies', 106),
    ('team/group/gang', 107),
    ('ensemble cast', 108),
    -- Age & identity (200s)
    ('childhood', 200),
    ('teenager', 201),
    ('elderly', 202),
    ('adult/child', 203),
    ('female lead', 204),
    ('male ensemble', 205),
    ('LGBT', 206),
    ('interracial', 207),
    -- Social status & traits (300s)
    ('ordinary', 300),
    ('poor/marginal', 301),
    ('wealthy', 302),
    ('genius', 303),
    ('simpleton/fool', 304),
    ('loser', 305),
    ('star/celebrity', 306),
    ('disturbed/madness', 307),
    ('disabled', 308),
    ('outcast/misfit', 309),
    ('sex worker', 310),
    ('psychopath', 311),
    -- Narrative devices (400s)
    ('double', 400),
    ('cross-dressing', 401),
    ('unreliable narrator', 402),
    -- Archetypes - human (500s)
    ('super hero', 500),
    ('chosen one', 501),
    ('antihero', 502),
    ('scientist/researcher', 503),
    ('mentor', 504),
    ('cop', 505),
    ('detective', 506),
    ('secret agent', 507),
    ('vigilante', 508),
    ('gangster', 509),
    ('soldier', 510),
    ('warrior', 511),
    ('knight', 512),
    ('samurai', 513),
    ('pirate', 514),
    ('viking', 515),
    ('witch/wizard', 516),
    ('femme fatale', 517),
    -- Non-human & creatures (600s)
    ('animal', 600),
    ('monster/terrestrial creature', 601),
    ('devil', 602),
    ('ghost/spirit', 603),
    ('vampire', 604),
    ('zombie', 605),
    ('alien', 606),
    ('android/robot', 607),
    ('vehicle', 608)
ON CONFLICT (context_name) DO NOTHING;

-- =============================================================================
-- ATMOSPHERE (Atmosphere) - 25 tags
-- =============================================================================

INSERT INTO atmosphere (atmosphere_name, sort_order) VALUES
    -- Light / Joyful (100s)
    ('family-friendly', 100),
    ('feel good', 101),
    ('crazy/nutty', 102),
    ('delicate/intimate', 103),
    -- Dark / Extreme (200s)
    ('depressive/sad', 200),
    ('violent', 201),
    ('disturbing', 202),
    ('steamy', 203),
    ('sordid', 204),
    -- Pace, Tension & Scale (300s)
    ('epic', 300),
    ('edge of your seat', 301),
    ('mysterious', 302),
    ('oppressive', 303),
    ('claustrophobic', 304),
    ('contemplative/meditative', 305),
    -- Artistic Directing (400s)
    ('cityscape', 400),
    ('pastoral', 401),
    ('gritty/realistic', 402),
    ('meticulous', 403),
    ('hypnotic/immersive', 404),
    ('psychedelic', 405),
    ('ethereal', 406),
    ('symbolic', 407),
    ('dreamlike/surreal', 408),
    ('poetic', 409)
ON CONFLICT (atmosphere_name) DO NOTHING;

-- =============================================================================
-- MOTIVATION_RELATION / MESSAGE_CONVEYED - DEPRECATED
-- Dissolved into Genre / Theme / Atmosphere by migration 026 (Taxonomy v2).
-- The tables still exist (empty) so the recommender, dashboard and games keep
-- running until Step 22; they are deliberately no longer seeded.
-- =============================================================================

-- =============================================================================
-- STREAM_PLATFORM - Streaming platforms
-- =============================================================================

INSERT INTO stream_platform (platform_name) VALUES
    ('Netflix'),
    ('Amazon Prime Video'),
    ('Disney+'),
    ('Canal+'),
    ('Apple TV+'),
    ('Hulu'),
    ('HBO Max'),
    ('Paramount+'),
    ('Mubi'),
    ('Criterion Channel'),
    ('Arte')
ON CONFLICT (platform_name) DO NOTHING;

-- =============================================================================
-- LANGUAGE - Common languages (basic seed)
-- =============================================================================

INSERT INTO language (language_code, language_name) VALUES
    ('en', 'English'),
    ('fr', 'French'),
    ('es', 'Spanish'),
    ('de', 'German'),
    ('it', 'Italian'),
    ('pt', 'Portuguese'),
    ('ja', 'Japanese'),
    ('ko', 'Korean'),
    ('zh', 'Chinese'),
    ('hi', 'Hindi'),
    ('ru', 'Russian'),
    ('ar', 'Arabic'),
    ('sv', 'Swedish'),
    ('da', 'Danish'),
    ('no', 'Norwegian'),
    ('fi', 'Finnish'),
    ('pl', 'Polish'),
    ('nl', 'Dutch'),
    ('tr', 'Turkish'),
    ('th', 'Thai'),
    ('vi', 'Vietnamese'),
    ('id', 'Indonesian'),
    ('he', 'Hebrew'),
    ('el', 'Greek'),
    ('cs', 'Czech'),
    ('hu', 'Hungarian'),
    ('ro', 'Romanian'),
    ('uk', 'Ukrainian'),
    ('fa', 'Persian'),
    ('bn', 'Bengali'),
    ('ta', 'Tamil'),
    ('te', 'Telugu'),
    ('ml', 'Malayalam'),
    ('kn', 'Kannada'),
    ('mr', 'Marathi'),
    ('pa', 'Punjabi'),
    ('la', 'Latin'),
    ('silent', 'Silent')
ON CONFLICT (language_code) DO NOTHING;

-- =============================================================================
-- END OF SEED DATA
-- =============================================================================
