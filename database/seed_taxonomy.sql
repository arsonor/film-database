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
-- CATEGORY - Film genres
-- =============================================================================

INSERT INTO category (category_name, historic_subcategory_name, sort_order) VALUES
    ('Comedy', NULL, 100),
    ('Drama', NULL, 101),
    ('Romance', NULL, 102),
    ('Action', NULL, 103),
    ('Adventure', NULL, 104),
    ('Thriller', NULL, 105),
    ('Science-Fiction', NULL, 106),
    ('Fantasy', NULL, 107),
    ('Horror', NULL, 108),
    ('Musical', NULL, 109),
    ('Documentary', NULL, 110),
    ('Historical', NULL, 111)
ON CONFLICT (category_name, historic_subcategory_name) DO NOTHING;

-- =============================================================================
-- CINEMA_TYPE - Cinema types, techniques & cultural movements
-- =============================================================================

INSERT INTO cinema_type (technique_name, sort_order) VALUES
    -- Group 1: Visual techniques & aesthetics (100s)
    ('animation', 100),
    ('mixed animation', 101),
    ('CGI', 102),
    ('3D', 103),
    ('motion capture', 104),
    ('black and white', 105),
    ('aesthetics', 106),
    -- Group 2: Movements & eras (200s)
    ('silent', 200),
    ('expressionism', 201),
    ('realism', 202),
    ('neo-realism', 203),
    ('noir', 204),
    ('hollywood golden age', 205),
    ('new hollywood', 206),
    ('new wave', 207),
    ('neo-noir', 208),
    -- Group 3: Industry & culture (300s)
    ('blockbuster', 300),
    ('art house', 301),
    ('franchise', 302),
    ('B', 303),
    ('generational', 304),
    ('popular culture', 305),
    -- Group 4: Narrative techniques (400s)
    ('sequence-shot', 400),
    ('found footage', 401),
    ('multi-sequence', 402),
    ('slow cinema', 403),
    ('non linear narrative', 404),
    ('dogma', 405),
    ('dialogs', 406),
    ('slang dialogs', 407),
    ('few/no dialogs', 408),
    ('voiceover', 409),
    -- Group 5: Cinema sub-genres/archetypes (500s)
    ('biopic', 500),
    ('historical event', 501),
    ('fait divers/true incident', 502),
    ('western', 503),
    ('peplum', 504),
    ('swashbuckler', 505),
    ('costume drama', 506),
    ('wu xia pian', 507),
    ('blaxploitation', 508),
    ('giallo', 509),
    ('slasher', 510),
    ('black comedy', 511),
    ('docufiction', 512)
ON CONFLICT (technique_name) DO NOTHING;

-- =============================================================================
-- PLACE_CONTEXT - Environmental settings
-- =============================================================================

INSERT INTO place_context (environment, sort_order) VALUES
    -- Group 1: Natural environments (100s)
    ('urban', 100),
    ('country-style', 101),
    ('forest', 102),
    ('mountains', 103),
    ('desert', 104),
    ('beach', 105),
    ('maritime', 106),
    ('island', 107),
    ('underground', 108),
    ('space', 109),
    -- Group 2: Buildings & institutions (200s)
    ('building', 200),
    ('household/house/apartment', 201),
    ('company/factory', 202),
    ('school/university', 203),
    ('hospital', 204),
    ('jail', 205),
    ('military', 206),
    ('naval', 207),
    ('ship', 208),
    -- Group 3: Narrative settings (300s)
    ('road movie', 300),
    ('huis clos/confined setting', 301),
    -- Group 4: None
    ('no particular', 400)
ON CONFLICT (environment) DO NOTHING;

-- =============================================================================
-- TIME_CONTEXT - Historical periods and seasons
-- =============================================================================

INSERT INTO time_context (time_period, sort_order) VALUES
    -- Chronological (future -> prehistoric)
    ('future', 1),
    ('contemporary', 2),
    ('early 21st', 3),
    ('end 20th', 4),
    ('20th post-war', 5),
    ('WW2', 6),
    ('interwar', 7),
    ('WW1', 8),
    ('early 20th', 9),
    ('19th', 10),
    ('modern age', 11),
    ('medieval', 12),
    ('antiquity', 13),
    ('prehistoric', 14),
    ('undetermined', 15),
    -- Seasons
    ('spring', 100),
    ('summer', 101),
    ('autumn', 102),
    ('winter', 103)
ON CONFLICT (time_period) DO NOTHING;

-- =============================================================================
-- THEME_CONTEXT - Thematic elements
-- Hierarchical themes use "parent: sub" convention (e.g. "art: cinema")
-- =============================================================================

INSERT INTO theme_context (theme_name, sort_order) VALUES
    -- Group 1: Society (100-199)
    ('social', 100),
    ('class struggle', 101),
    ('societal', 102),
    ('political', 103),
    ('religion', 104),
    ('business', 105),
    ('journalism/media', 106),
    ('censorship', 107),
    ('trial/judicial chronicle', 108),
    ('prison', 109),
    ('war', 110),
    ('immigration', 111),
    ('slavery', 112),
    ('colonialism', 113),
    ('tragedy', 114),
    ('apocalypse', 115),
    ('disaster', 116),
    -- Group 2: Personal / Psychological (200-299)
    ('trauma/accident', 200),
    ('psychological', 201),
    ('identity crisis', 202),
    ('illness', 203),
    ('amnesia', 204),
    ('death', 205),
    ('mourning', 206),
    ('addiction/drugs', 207),
    ('time passing', 208),
    ('transformation', 209),
    -- Group 3: Crime / Thriller (300-399)
    ('investigation', 300),
    ('spy', 301),
    ('crime', 302),
    ('sex crime', 303),
    ('organized crime', 304),
    ('heist', 305),
    ('kidnapping/hostage', 306),
    ('police violence', 307),
    ('corruption', 308),
    ('delinquency', 309),
    ('organized fraud', 310),
    ('mafia', 311),
    ('serial killer', 312),
    ('chase/escape', 313),
    ('terrorism', 314),
    ('sect', 315),
    ('survival', 316),
    -- Group 4: Sci-fi / Fantasy (400-499)
    ('dystopia', 400),
    ('tales and legends', 401),
    ('supernatural', 402),
    ('sorcery', 403),
    ('alien contact', 404),
    ('paranormal', 405),
    ('curse', 406),
    ('time travel/loop', 407),
    ('virtual reality', 408),
    ('dream', 409),
    ('whimsical/zany', 410),
    -- Group 5: Art, Sport & Entertainment (500-599)
    ('art', 500),
    ('art: music', 501),
    ('art: cinema', 502),
    ('art: literature', 503),
    ('art: fashion', 504),
    ('art: painting', 505),
    ('art: sculpture', 506),
    ('art: theatre', 507),
    ('art: radio', 508),
    ('art: architecture', 509),
    ('martial arts', 510),
    ('party', 513),
    ('game', 514),
    ('gambling', 515),
    ('sport', 520),
    ('sport: individual', 521),
    ('sport: collective', 522),
    ('sport: tournament', 523),
    ('sport: motor', 524),
    -- Group 6: Miscellaneous (600-699)
    ('nature', 600),
    ('AI/technology', 601),
    ('food/cooking', 602)
ON CONFLICT (theme_name) DO NOTHING;

-- =============================================================================
-- CHARACTER_CONTEXT - Characters
-- =============================================================================

INSERT INTO character_context (context_name, sort_order) VALUES
    -- Group 1: Group structure (100s)
    ('solitary', 100),
    ('tandem', 101),
    ('trio', 102),
    ('couple', 103),
    ('relatives', 104),
    ('generations', 105),
    ('buddies', 106),
    ('team/group/gang', 107),
    ('ensemble cast', 108),
    -- Group 2: Age & identity (200s)
    ('childhood', 200),
    ('teenager', 201),
    ('elderly', 202),
    ('adult/child', 203),
    ('female', 204),
    ('LGBT', 205),
    ('interracial', 206),
    -- Group 3: Social status & traits (300s)
    ('ordinary', 300),
    ('poor/marginal', 301),
    ('wealthy', 302),
    ('genius', 303),
    ('idiot', 304),
    ('charismatic', 305),
    ('loser', 306),
    ('star/celebrity', 307),
    ('disturbed/madness', 308),
    ('disabled', 309),
    ('outcast/misfit', 310),
    ('prostitute', 311),
    ('psychopath', 312),
    -- Group 4: Narrative devices (400s)
    ('double', 400),
    ('cross-dressing', 401),
    ('unreliable narrator', 402),
    -- Group 5: Archetypes - human (500s)
    ('super hero', 500),
    ('antihero', 501),
    ('cop', 502),
    ('detective', 503),
    ('vigilante', 504),
    ('gangster', 505),
    ('soldier', 506),
    ('femme fatale', 507),
    ('samurai', 508),
    ('pirate', 509),
    ('viking', 510),
    ('scientist/researcher', 511),
    ('mentor', 512),
    -- Group 6: Non-human & creatures (600s)
    ('animal/wildlife', 600),
    ('monster/terrestrial creature', 601),
    ('evil', 602),
    ('witch', 603),
    ('ghost/spirit', 604),
    ('vampire', 605),
    ('zombie', 606),
    ('alien', 607),
    ('android', 608),
    ('vehicle', 609)
ON CONFLICT (context_name) DO NOTHING;

-- =============================================================================
-- ATMOSPHERE - Film atmosphere/tone
-- =============================================================================

INSERT INTO atmosphere (atmosphere_name, sort_order) VALUES
    -- Group 1: Light/Joyful (100s)
    ('family-friendly', 100),
    ('feel good', 101),
    ('crazy/nutty', 102),
    ('delicate/intimate', 103),
    ('contemplative/meditative', 104),
    -- Group 2: Tension (200s)
    ('mysterious', 200),
    ('oppressive', 201),
    ('claustrophobic', 202),
    -- Group 3: Attention (300s)
    ('meticulous', 300),
    ('ethereal', 301),
    ('hypnotic/immersive', 302),
    ('psychedelic', 303),
    -- Group 4: Dark/Extreme (400s)
    ('depressive/sad', 400),
    ('violent', 401),
    ('disturbing', 402),
    ('steamy', 403),
    ('gore', 404),
    ('sordid', 405),
    -- Group 5: Scale & Tone (500s)
    ('gritty/realistic', 500),
    ('epic', 501)
ON CONFLICT (atmosphere_name) DO NOTHING;

-- =============================================================================
-- MOTIVATION_RELATION - Character motivations
-- =============================================================================

INSERT INTO motivation_relation (motivation_name, sort_order) VALUES
    -- Group 1: Positive bonds (100s)
    ('love', 100),
    ('friendship', 101),
    ('solidarity', 102),
    ('communication', 103),
    ('emancipation', 104),
    ('redemption', 105),
    ('honor/duty', 106),
    -- Group 2: Inner conflict (200s)
    ('obsession', 200),
    ('doubt/dilemma', 201),
    ('lie', 202),
    ('manipulation', 203),
    ('sacrifice', 204),
    -- Group 3: Desire & transgression (300s)
    ('greed/ambition', 300),
    ('sex', 301),
    ('adultery', 302),
    ('jealousy', 303),
    ('harassment', 304),
    ('perversion', 305),
    -- Group 4: Conflict & struggle (400s)
    ('power', 400),
    ('rivalry', 401),
    ('fight', 402),
    ('rebellion/revolt', 403),
    ('vengeance', 404),
    -- Group 5: Epic quests (500s)
    ('odyssey', 500),
    ('quest', 501),
    ('world-saving', 502),
    ('invasion', 503)
ON CONFLICT (motivation_name) DO NOTHING;

-- =============================================================================
-- MESSAGE_CONVEYED - Film messages
-- =============================================================================

INSERT INTO message_conveyed (message_name, sort_order) VALUES
    -- Group 1: Values & ideology (100s)
    ('humanist', 100),
    ('feminist', 101),
    ('ecological', 102),
    ('political', 103),
    ('anti establishment', 104),
    ('nostalgic', 105),
    ('patriotic', 106),
    ('traditionalist/way of life', 107),
    -- Group 2: Comedy & satire (200s)
    ('parodic', 200),
    ('satirical', 201),
    ('absurdist', 202),
    ('revisionist/alternate history', 203),
    -- Group 3: Reflection (300s)
    ('philosophical', 300),
    ('metaphysical', 301),
    -- Group 4: Artistic expression (400s)
    ('dreamlike', 400),
    ('surreal', 401),
    ('symbolic', 402),
    ('poetic', 403)
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
