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
    ('Historical', NULL, 111),
    -- Historical subcategories
    ('Historical', 'biopic', 112),
    ('Historical', 'human interest story', 113),
    ('Historical', 'judicial chronicle', 114),
    ('Historical', 'western', 115),
    ('Historical', 'peplum', 116),
    ('Historical', 'swashbuckler', 117),
    ('Historical', 'event', 118)
ON CONFLICT (category_name, historic_subcategory_name) DO NOTHING;

-- =============================================================================
-- CINEMA_TYPE - Cinema types, techniques & cultural movements (merged)
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
    ('neo-realism', 202),
    ('noir', 203),
    ('hollywood golden age', 204),
    ('new hollywood', 205),
    ('new wave', 206),
    ('realism', 207),
    ('neo-noir', 208),
    ('costume', 209),
    ('dogma', 210),
    ('blaxploitation', 211),
    ('wu xia pian', 212),
    -- Group 3: Industry & culture (300s)
    ('blockbuster', 300),
    ('art house', 301),
    ('B', 302),
    ('Z', 303),
    ('Collection', 304),
    ('generational', 305),
    ('popular culture', 306),
    -- Group 4: Narrative techniques (400s)
    ('sequence-shot', 400),
    ('found footage', 401),
    ('multi-sequence', 402),
    ('slow cinema', 403),
    ('non linear narrative', 404),
    -- Group 5: Dialog style (500s)
    ('dialogs', 500),
    ('slang dialogs', 501)
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
    ('space', 108),
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
    ('huis clos', 301),
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
    ('disaster', 113),
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
    ('curse', 411),
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
    ('book', 604),
    ('game', 605)
ON CONFLICT (theme_name) DO NOTHING;

-- =============================================================================
-- CHARACTER_CONTEXT - Characters (merged types + contexts + archetypes)
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
    ('interracial', 108),
    ('ensemble cast', 109),
    -- Group 2: Age & identity (200s)
    ('childhood', 200),
    ('teenager', 201),
    ('elderly', 202),
    ('adult/child', 203),
    ('female', 204),
    ('LGBT', 205),
    -- Group 3: Social status & traits (300s)
    ('ordinary', 300),
    ('poor/marginal', 301),
    ('wealthy', 302),
    ('genius', 303),
    ('idiot', 304),
    ('looser', 305),
    ('star/celebrity', 306),
    ('madness', 307),
    ('freak/disabled', 308),
    ('prostitute', 309),
    ('psychopath', 310),
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
    ('soldier', 505),
    ('femme fatale', 506),
    ('samourai', 507),
    ('pirate', 508),
    ('viking', 509),
    ('barbarian', 510),
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
-- ATMOSPHERE - Film atmosphere/tone (core + extended)
-- =============================================================================

INSERT INTO atmosphere (atmosphere_name, sort_order) VALUES
    -- Group 1: Light (100s)
    ('family', 100),
    ('feel good', 101),
    ('crazy/nutty', 102),
    ('depressive/sad', 103),
    -- Group 2: Tension (200s)
    ('mysterious', 200),
    ('oppressive', 201),
    ('claustrophobic', 202),
    -- Group 3: Contemplative (300s)
    ('contemplative', 300),
    ('ethereal', 301),
    ('hypnotic', 302),
    ('psychedelic', 303),
    -- Group 4: Dark (400s)
    ('violent', 400),
    ('disturbing', 401),
    ('sulfurous', 402),
    ('trash', 403),
    ('gore', 404),
    ('awful/seedy/depraved', 405)
ON CONFLICT (atmosphere_name) DO NOTHING;

-- =============================================================================
-- MOTIVATION_RELATION - Character motivations
-- =============================================================================

INSERT INTO motivation_relation (motivation_name, sort_order) VALUES
    -- Group 1: Positive bonds (100s)
    ('feelings', 100),
    ('friendship', 101),
    ('solidarity', 102),
    ('communication', 103),
    ('emancipation', 104),
    ('redemption', 105),
    -- Group 2: Inner conflict (200s)
    ('obsession', 200),
    ('doubt/dilemma', 201),
    ('lie', 202),
    ('manipulation', 203),
    -- Group 3: Desire & transgression (300s)
    ('sex', 300),
    ('adultery', 301),
    ('jealousy', 302),
    ('harassment', 303),
    ('perversion', 304),
    -- Group 4: Conflict & struggle (400s)
    ('power', 400),
    ('rivalry', 401),
    ('fight', 402),
    ('rebellion/revolt', 403),
    ('vengeance', 404),
    -- Group 5: Epic quests (500s)
    ('odyssey', 500),
    ('quest', 501),
    ('world saver', 502),
    ('invasion', 503)
ON CONFLICT (motivation_name) DO NOTHING;

-- =============================================================================
-- MESSAGE_CONVEYED - Film messages (core + extended)
-- =============================================================================

INSERT INTO message_conveyed (message_name, sort_order) VALUES
    -- Group 1: Values & ideology (100s)
    ('humanist', 100),
    ('philosophical', 101),
    ('feminist', 102),
    ('ecological', 103),
    ('political', 104),
    -- Group 2: Comedy & satire (200s)
    ('parodic', 200),
    ('satirical', 201),
    ('black comedy', 202),
    ('absurdist', 203),
    -- Group 3: Cultural perspective (300s)
    ('anti establishment', 300),
    ('nostalgic', 301),
    ('patriotic', 302),
    ('traditionalist/way of life', 303),
    ('history revisited', 304),
    -- Group 4: Artistic expression (400s)
    ('dreamlike', 400),
    ('surreal', 401),
    ('symbolic', 402),
    ('metaphysical', 403)
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
