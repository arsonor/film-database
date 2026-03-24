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
    ('Historical', 'swashbuckler')
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
    ('black_and_white'),
    ('slow_cinema'),
    ('non_linear_narrative')
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
    ('hospital')
ON CONFLICT (environment) DO NOTHING;

-- =============================================================================
-- TIME_CONTEXT - Historical periods and seasons
-- =============================================================================

INSERT INTO time_context (time_period) VALUES
    -- Historical periods
    ('undetermined'),
    ('future'),
    ('contemporary'),
    ('end 20th'),
    ('30-year post-war boom'),
    ('WW2'),
    ('interwar'),
    ('WW1'),
    ('early 20th'),
    ('19th'),
    ('modern age'),
    ('medieval'),
    ('antiquity'),
    ('prehistoric'),
    -- Seasons
    ('summer'),
    ('winter'),
    ('autumn'),
    ('spring')
ON CONFLICT (time_period) DO NOTHING;

-- =============================================================================
-- THEME_CONTEXT - Thematic elements (core + extended)
-- Hierarchical themes use "parent: sub" convention (e.g. "art: cinema")
-- =============================================================================

INSERT INTO theme_context (theme_name) VALUES
    -- Core themes
    ('social'),
    ('societal'),
    ('political'),
    ('religion'),
    ('business'),
    ('trial'),
    ('prison'),
    ('apocalypse'),
    ('war'),
    ('tragedy'),
    ('trauma'),
    ('psychological'),
    ('disease'),
    ('accident'),
    ('death'),
    ('mourning'),
    ('addiction/drugs'),
    ('time passing'),
    ('investigation'),
    ('spy'),
    ('crime'),
    ('organized crime'),
    ('delinquency'),
    ('organized fraud'),
    ('sex crime'),
    ('mafia'),
    ('gangster'),
    ('serial killer'),
    ('chase/escape'),
    ('terrorism'),
    ('sect'),
    ('survival'),
    ('slasher'),
    ('futuristic'),
    ('dystopia'),
    ('tales and legends'),
    ('supernatural'),
    ('sorcery'),
    ('alien contact'),
    ('paranormal'),
    ('time travel/loop'),
    ('virtual reality'),
    ('dream'),
    ('nonsense'),
    -- Art sub-types
    ('art'),
    ('art: music'),
    ('art: cinema'),
    ('art: literature'),
    ('art: fashion'),
    ('art: painting'),
    ('art: sculpture'),
    ('art: theatre'),
    ('art: radio'),
    -- Sport sub-types
    ('sport'),
    ('sport: motor'),
    ('sport: individual'),
    ('sport: collective'),
    ('sport: tournament'),
    -- More core themes
    ('martial arts'),
    ('nature'),
    ('technology'),
    ('food/cooking'),
    ('party'),
    ('book'),
    -- Extended themes
    ('identity_crisis'),
    ('police_violence'),
    ('evolution'),
    ('artificial_intelligence'),
    ('amnesia'),
    ('corruption'),
    ('class_struggle'),
    ('immigration'),
    ('censorship')
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
    -- Character Archetypes
    ('super hero'),
    ('vigilante'),
    ('cop'),
    ('detective'),
    ('samourai'),
    ('pirate'),
    ('viking'),
    ('barbarian'),
    ('psychopath'),
    ('madness'),
    ('idiot'),
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
    ('unreliable_narrator'),
    ('antihero'),
    ('femme_fatale')
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
    ('survival')
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
    ('anti_establishment'),
    ('feminist'),
    ('absurdist'),
    ('ecological')
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
