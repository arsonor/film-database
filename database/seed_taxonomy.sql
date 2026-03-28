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
-- CATEGORY - Film genres with historical subcategories
-- =============================================================================

-- Main categories
INSERT INTO category (category_name, historic_subcategory_name) VALUES
    ('Action', NULL),
    ('Adventure', NULL),
    ('Comedy', NULL),
    ('Documentary', NULL),
    ('Drama', NULL),
    ('Romance', NULL),
    ('Thriller', NULL),
    ('Horror', NULL),
    ('Science-Fiction', NULL),
    ('Fantasy', NULL),
    ('Musical', NULL),
    ('Disaster', NULL),
    ('Historical', NULL),
    -- Historical subcategories
    ('Historical', 'biopic'),
    ('Historical', 'human interest story'),
    ('Historical', 'judicial chronicle'),
    ('Historical', 'western'),
    ('Historical', 'peplum'),
    ('Historical', 'swashbuckler'),
    ('Historical', 'event')
ON CONFLICT (category_name, historic_subcategory_name) DO NOTHING;

-- =============================================================================
-- CINEMA_TYPE - Cinematographic techniques
-- =============================================================================

INSERT INTO cinema_type (technique_name) VALUES
    ('silent'),
    ('animation'),
    ('mixed animation'),
    ('art house'),
    ('blockbuster'),
    ('sequence-shot'),
    ('found footage'),
    ('motion capture'),
    ('multi-sequence'),
    ('black and white'),
    ('slow cinema'),
    ('non linear narrative'),
    ('costume')
ON CONFLICT (technique_name) DO NOTHING;

-- =============================================================================
-- CULTURAL_MOVEMENT - Cinematic movements
-- =============================================================================

INSERT INTO cultural_movement (movement_name) VALUES
    ('expressionism'),
    ('neo-realism'),
    ('realism'),
    ('noir'),
    ('hollywood golden age'),
    ('new hollywood'),
    ('new wave'),
    ('neo-noir'),
    ('dogma'),
    ('blaxploitation'),
    ('wu xia pian'),
    ('generational'),
    ('popular culture'),
    ('aesthetics'),
    ('CGI'),
    ('3D'),
    ('B'),
    ('Z'),
    ('Collection')
ON CONFLICT (movement_name) DO NOTHING;

-- =============================================================================
-- PLACE_CONTEXT - Environmental settings
-- =============================================================================

INSERT INTO place_context (environment) VALUES
    ('no particular'),
    ('urban'),
    ('country-style'),
    ('maritime'),
    ('naval'),
    ('island'),
    ('forest'),
    ('mountains'),
    ('desert'),
    ('beach'),
    ('space'),
    ('huis clos'),
    ('road movie'),
    ('school/university'),
    ('company/factory'),
    ('building'),
    ('household/house/apartment'),
    ('jail'),
    ('hospital'),
    ('military'),
    ('ship')
ON CONFLICT (environment) DO NOTHING;

-- =============================================================================
-- TIME_CONTEXT - Historical periods and seasons
-- =============================================================================

INSERT INTO time_context (time_period, sort_order) VALUES
    -- Chronological (future → prehistoric)
    ('future', 1),
    ('contemporary', 2),
    ('end 20th', 3),
    ('30-year post-war boom', 4),
    ('WW2', 5),
    ('interwar', 6),
    ('WW1', 7),
    ('early 20th', 8),
    ('19th', 9),
    ('modern age', 10),
    ('medieval', 11),
    ('antiquity', 12),
    ('prehistoric', 13),
    ('undetermined', 14),
    -- Seasons
    ('spring', 100),
    ('summer', 101),
    ('autumn', 102),
    ('winter', 103)
ON CONFLICT (time_period) DO NOTHING;

-- =============================================================================
-- THEME_CONTEXT - Thematic elements (core + extended)
-- Hierarchical themes use "parent: sub" convention (e.g. "art: cinema")
-- =============================================================================

INSERT INTO theme_context (theme_name, sort_order) VALUES
    -- Group 1: Society (100-199)
    ('social', 100),
    ('class struggle', 101),
    ('societal', 102),
    ('immigration', 103),
    ('political', 104),
    ('religion', 105),
    ('business', 106),
    ('censorship', 107),
    ('trial', 108),
    ('prison', 109),
    ('war', 110),
    ('tragedy', 111),
    ('apocalypse', 112),
    -- Group 2: Personal / Psychological (200-299)
    ('trauma/accident', 200),
    ('psychological', 201),
    ('identity crisis', 202),
    ('disease', 203),
    ('amnesia', 204),
    ('death', 205),
    ('mourning', 206),
    ('addiction/drugs', 207),
    ('time passing', 208),
    ('evolution', 209),
    -- Group 3: Crime / Thriller (300-399)
    ('investigation', 300),
    ('spy', 301),
    ('crime', 302),
    ('sex crime', 303),
    ('organized crime', 304),
    ('police violence', 305),
    ('corruption', 306),
    ('delinquency', 307),
    ('organized fraud', 308),
    ('mafia', 309),
    ('gangster', 310),
    ('serial killer', 311),
    ('chase/escape', 312),
    ('terrorism', 313),
    ('sect', 314),
    ('survival', 315),
    ('slasher', 316),
    -- Group 4: Sci-fi / Fantasy (400-499)
    ('futuristic', 400),
    ('dystopia', 401),
    ('tales and legends', 402),
    ('supernatural', 403),
    ('sorcery', 404),
    ('alien contact', 405),
    ('paranormal', 406),
    ('time travel/loop', 407),
    ('virtual reality', 408),
    ('dream', 409),
    ('nonsense', 410),
    -- Group 5: Art & Sport (500-599)
    ('art', 500),
    ('art: music', 501),
    ('art: cinema', 502),
    ('art: literature', 503),
    ('art: fashion', 504),
    ('art: painting', 505),
    ('art: sculpture', 506),
    ('art: theatre', 507),
    ('art: radio', 508),
    ('martial arts', 509),
    ('sport', 520),
    ('sport: individual', 521),
    ('sport: collective', 522),
    ('sport: tournament', 523),
    ('sport: motor', 524),
    -- Group 6: Miscellaneous (600-699)
    ('nature', 600),
    ('AI/technology', 601),
    ('food/cooking', 602),
    ('party', 603),
    ('book', 604)
ON CONFLICT (theme_name) DO NOTHING;

-- =============================================================================
-- CHARACTERS_TYPE - Character configurations
-- =============================================================================

INSERT INTO characters_type (type_name) VALUES
    ('solitary'),
    ('tandem'),
    ('couple'),
    ('adult/child'),
    ('trio'),
    ('buddies'),
    ('gang'),
    ('relatives'),
    ('generations'),
    ('ensemble cast'),
    ('animal/wildlife')
ON CONFLICT (type_name) DO NOTHING;

-- =============================================================================
-- CHARACTER_CONTEXT - Character contexts, archetypes, and extended
-- =============================================================================

INSERT INTO character_context (context_name) VALUES
    -- Character Context
    ('childhood'),
    ('teenager'),
    ('elderly'),
    ('female'),
    ('LGBT'),
    ('cross-dressing'),
    ('double'),
    ('interracial'),
    ('ordinary'),
    ('poor/marginal'),
    ('wealthy')
    -- Character Archetypes
    ('super hero'),
    ('vigilante'),
    ('cop'),
    ('detective'),
    ('samourai'),
    ('pirate'),
    ('viking'),
    ('barbarian'),
    ('soldier'),
    ('psychopath'),
    ('madness'),
    ('idiot'),
    ('genius')
    ('looser'),
    ('prostitute'),
    ('freak/disabled'),
    ('monster/terrestrial creature'),
    ('ghost/spirit'),
    ('evil'),
    ('witch'),
    ('vampire'),
    ('zombie'),
    ('android'),
    ('alien'),
    -- Extended archetypes
    ('unreliable narrator'),
    ('antihero'),
    ('femme fatale'),
    ('star/celebrity'),
    ('vehicle')
ON CONFLICT (context_name) DO NOTHING;

-- =============================================================================
-- ATMOSPHERE - Film atmosphere/tone (core + extended)
-- =============================================================================

INSERT INTO atmosphere (atmosphere_name) VALUES
    -- Core atmosphere
    ('family'),
    ('feel good'),
    ('crazy/nutty'),
    ('depressive/sad'),
    ('sulfurous'),
    ('mysterious'),
    ('violent'),
    ('trash'),
    ('gore'),
    ('awful/seedy/depraved'),
    ('oppressive'),
    ('disturbing'),
    ('contemplative'),
    -- Extended atmosphere
    ('hypnotic'),
    ('psychedelic'),
    ('ethereal'),
    ('claustrophobic')
ON CONFLICT (atmosphere_name) DO NOTHING;

-- =============================================================================
-- MOTIVATION_RELATION - Character motivations
-- =============================================================================

INSERT INTO motivation_relation (motivation_name) VALUES
    ('feelings'),
    ('friendship'),
    ('emancipation'),
    ('solidarity'),
    ('adultery'),
    ('jealousy'),
    ('sex'),
    ('harassment'),
    ('lie'),
    ('doubt/dilemma'),
    ('rivalry'),
    ('power'),
    ('perversion'),
    ('manipulation'),
    ('redemption'),
    ('obsession'),
    ('vengeance'),
    ('rebellion/revolt'),
    ('fight'),
    ('odyssey'),
    ('quest'),
    ('world saver'),
    ('communication'),
    ('invasion')
ON CONFLICT (motivation_name) DO NOTHING;

-- =============================================================================
-- MESSAGE_CONVEYED - Film messages (core + extended)
-- =============================================================================

INSERT INTO message_conveyed (message_name) VALUES
    -- Core messages
    ('parodic'),
    ('satirical'),
    ('political'),
    ('humanist'),
    ('nostalgic'),
    ('dreamlike'),
    ('surreal'),
    ('symbolic'),
    ('philosophical'),
    ('metaphysical'),
    ('dialogs'),
    ('slang dialogs'),
    ('black comedy'),
    -- Extended messages
    ('anti establishment'),
    ('feminist'),
    ('absurdist'),
    ('ecological'),
    ('patriotic'),
    ('history revisited'),
    ('traditionalist/way of life')
ON CONFLICT (message_name) DO NOTHING;

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
