"""
Taxonomy configuration for the Film Database project.

All valid taxonomy values extracted from database/seed_taxonomy.sql (Taxonomy v2:
7 dimensions — Genre, Theme, Time Period, Place, Atmosphere, Character, Cinema Type).
Used by ClaudeEnricher to build prompts and validate outputs.

Lists are kept in seed_taxonomy.sql order (i.e. sort_order order), with a comment
per named sub-dimension so the prompt reads like the source document.
"""

# =============================================================================
# Valid taxonomy values — extracted from seed_taxonomy.sql
# =============================================================================

# --- Genre -------------------------------------------------------------------
# Main genres occupy sort_order block 100-199; everything from 200 up is a
# sub-genre. Every film must get at least one MAIN genre.

VALID_GENRES_MAIN = [
    "Drama", "Comedy", "Romance", "Historical", "Action", "Adventure",
    "Thriller", "Science-Fiction", "Fantasy", "Horror", "Musical", "Documentary",
]

VALID_GENRES_SUB = [
    # Drama / Romance (200s)
    "melodrama", "coming of age", "slice of life", "tragedy",
    # Comedy (300s)
    "parodic", "satirical", "absurdist", "black comedy",
    # Thriller / Adventure (400s)
    "psychological", "war", "crime", "investigation", "spy", "heist",
    "mafia/organized crime", "serial killer", "survival", "chase/escape",
    "odyssey/quest", "disaster", "apocalypse",
    # Historical / Justice (500s)
    "courtroom", "prison", "biopic", "fait divers/true incident",
    "western", "peplum", "swashbuckler", "costume drama", "wu xia pian",
    "revisionist/alternate history",
    # Sci-fi / Fantasy (600s)
    "supernatural", "whimsical/zany", "dystopia", "tales and legends",
    # Horror (700s)
    "jumpscare", "slasher", "gore", "body horror", "gothic horror", "folk horror",
    # Miscellaneous (800s)
    "docufiction", "martial arts",
]

VALID_CATEGORIES = VALID_GENRES_MAIN + VALID_GENRES_SUB

VALID_CINEMA_TYPES = [
    # Visual techniques (100s)
    "animation", "mixed animation", "CGI", "3D", "motion capture",
    "black and white", "aesthetics", "found footage", "dogma",
    # Industry & culture (200s)
    "blockbuster", "art house", "B", "franchise", "popular culture",
    # Narrative techniques > Sequencing (300s)
    "chapters/multi-sequence", "flashback/non linear", "real time", "timelapse",
    "slow-motion", "sequence-shot", "split screen", "musical montage",
    # Narrative techniques > Voice & Dialogue (400s)
    "dialogs/punchline", "slang dialogs", "few/no dialogs", "voiceover",
    "monologue", "fourth wall break",
    # Movements & eras (500s)
    "silent", "expressionism", "realism", "neo-realism", "noir",
    "hollywood golden age", "new hollywood", "new wave", "slow cinema",
    "neo-noir", "blaxploitation", "giallo",
]

VALID_PLACE_ENVIRONMENTS = [
    # Environments (100s)
    "urban", "small town", "rural", "forest", "mountains", "desert", "beach",
    "maritime", "island", "underground", "space", "planet",
    # Buildings & institutions (200s)
    "building", "household/house/apartment", "company/factory",
    "school/university", "hospital", "jail", "military", "castle", "hotel",
    # Narrative settings (300s)
    "road movie", "huis clos/confined setting",
    # Vehicles (400s)
    "car/bus", "train", "airplane", "ship", "submarine", "spaceship",
    # None (500)
    "no particular",
]

VALID_TIME_CONTEXTS = [
    # Chronological (future -> prehistoric)
    "future", "contemporary", "2000-2010's", "1980-90's", "1950-60-70's",
    "WW2", "1920-30's", "WW1", "1900-1910's", "19th", "modern age",
    "medieval", "antiquity", "prehistoric", "undetermined",
    # Time span (100s)
    "single day", "several years", "decades-spanning",
    # Seasons (200s)
    "spring", "summer", "autumn", "winter",
]

# Year ranges for the Chronological block — mirrored in the enrichment prompt.
TIME_PERIOD_YEAR_RANGES = [
    ("future", "2030 onward"),
    ("contemporary", "2020-2029"),
    ("2000-2010's", "2000-2019"),
    ("1980-90's", "1980-1999"),
    ("1950-60-70's", "1946-1979"),
    ("WW2", "1939-1945"),
    ("1920-30's", "1919-1938"),
    ("WW1", "1914-1918"),
    ("1900-1910's", "1900-1913"),
    ("19th", "1800-1899"),
    ("modern age", "1500-1799"),
    ("medieval", "500-1500"),
    ("antiquity", "3000 BC-500 AD"),
    ("prehistoric", "before recorded civilization"),
    ("undetermined", "no identifiable period"),
]

VALID_THEMES = [
    # Society & World (100s)
    "social", "societal", "generational", "political", "religion", "business",
    "journalism/media", "censorship", "conspiracy", "sect", "immigration",
    "colonialism", "slavery", "nature/wildlife", "AI/technology",
    # Values & Reflection (200s)
    "humanist", "feminist", "nostalgic", "ecological", "patriotic",
    "anti establishment", "traditionalist/way of life", "philosophical",
    "metaphysical",
    # Human Relations > Bonds & attachments (300s)
    "love", "friendship", "solidarity", "communication", "family/parenthood",
    # Human Relations > Desire & transgression (400s)
    "power", "manipulation", "sex", "adultery", "jealousy", "perversion",
    # Human Relations > Interpersonal conflict (500s)
    "class/culture clash", "rivalry", "fight", "rebellion/revolt", "vengeance",
    "harassment",
    # Human Relations > Crime & abuse of power (600s)
    "delinquency", "police violence", "sex crime", "kidnapping/hostage",
    "trafficking/fraud", "corruption", "terrorism",
    # Personal / Inner conflict > Wounds & burdens (700s)
    "trauma/accident", "identity crisis", "illness", "amnesia", "death",
    "grief/mourning", "addiction/drugs", "loneliness", "guilt",
    # Personal / Inner conflict > Drives & arcs (800s)
    "obsession", "greed/ambition", "doubt/dilemma", "lie", "sacrifice",
    "honor/duty", "emancipation", "redemption", "transformation",
    "time passing", "dream",
    # Art, Sport & Entertainment > Art (900s)
    "art", "art: music/dance", "art: cinema", "art: literature", "art: fashion",
    "art: painting", "art: sculpture", "art: theatre", "art: radio",
    "art: architecture",
    # Art, Sport & Entertainment > Sport (1000s)
    "sport", "sport: individual", "sport: collective", "sport: tournament",
    "sport: motor",
    # Art, Sport & Entertainment > Entertainment (1100s)
    "food/cooking", "party", "game", "gambling", "contest",
    # Face to the unknown (1200s)
    "sorcery", "alien contact", "paranormal", "curse", "time travel/loop",
    "virtual/parallel universe", "invasion", "exploration",
]

VALID_CHARACTERS = [
    # Group structure (100s)
    "solitary", "tandem", "trio", "couple", "relatives", "generations",
    "buddies", "team/group/gang", "ensemble cast",
    # Age & identity (200s)
    "childhood", "teenager", "elderly", "adult/child", "female lead",
    "male ensemble", "LGBT", "interracial",
    # Social status (300s)
    "ordinary", "poor/marginal", "wealthy", "star/celebrity", "sex worker",
    "outcast/misfit",
    # Traits & conditions (400s)
    "genius", "simpleton/fool", "loser", "disabled", "disturbed/madness",
    "psychopath",
    # Narrative devices (500s)
    "double", "cross-dressing", "unreliable narrator",
    # Archetypes — human > Figures & roles (600s)
    "super hero", "chosen one", "antihero", "mentor", "scientist/researcher",
    "witch/wizard", "femme fatale",
    # Archetypes — human > Law & crime (700s)
    "cop", "detective", "secret agent", "vigilante", "gangster",
    # Archetypes — human > Fighters (800s)
    "soldier", "warrior", "knight", "samurai", "pirate", "viking",
    # Non-human & creatures (900s)
    "animal", "monster/terrestrial creature", "devil", "ghost/spirit",
    "vampire", "zombie", "alien", "android/robot", "vehicle",
]

VALID_ATMOSPHERES = [
    # Light / Joyful (100s)
    "family-friendly", "feel good", "crazy/nutty", "delicate/intimate",
    # Dark / Extreme (200s)
    "depressive/sad", "violent", "disturbing", "steamy", "sordid",
    # Pace, Tension & Scale (300s)
    "epic", "edge of your seat", "mysterious", "oppressive", "claustrophobic",
    "contemplative/meditative",
    # Artistic Directing (400s)
    "cityscape", "pastoral", "gritty/realistic", "meticulous",
    "hypnotic/immersive", "psychedelic", "ethereal", "symbolic",
    "dreamlike/surreal", "poetic",
]

VALID_SOURCE_TYPES = [
    "original screenplay", "novel", "comic", "TV series", "true story",
    "play", "video game", "poem", "short story", "remake",
]

# =============================================================================
# All valid values grouped by dimension — for prompt building and validation
# =============================================================================

TAXONOMY_DIMENSIONS = {
    "categories": VALID_CATEGORIES,
    "cinema_type": VALID_CINEMA_TYPES,
    "time_context": VALID_TIME_CONTEXTS,
    "place_environment": VALID_PLACE_ENVIRONMENTS,
    "themes": VALID_THEMES,
    "character_context": VALID_CHARACTERS,
    "atmosphere": VALID_ATMOSPHERES,
}

# =============================================================================
# Reference film examples — validated classifications from CLAUDE.md,
# re-tagged under Taxonomy v2. Used as few-shot examples in the prompt.
# =============================================================================

REFERENCE_EXAMPLES = {
    "2001": {
        "title": "2001: A Space Odyssey",
        "year": 1968,
        "enrichment": {
            "categories": ["Science-Fiction", "Drama", "psychological", "survival"],
            "cinema_type": [
                "aesthetics", "blockbuster", "art house", "chapters/multi-sequence",
                "timelapse", "few/no dialogs", "voiceover", "slow cinema",
                "new hollywood",
            ],
            "time_context": ["prehistoric", "1950-60-70's", "future"],
            "geography": [
                {"continent": "Africa", "country": "Kenya", "state_city": None, "place_type": "diegetic"},
            ],
            "place_environment": ["desert", "space", "planet", "spaceship"],
            "themes": [
                "nature/wildlife", "AI/technology", "philosophical", "metaphysical",
                "power", "rebellion/revolt", "death", "loneliness", "obsession",
                "doubt/dilemma", "lie", "transformation", "time passing",
                "alien contact", "exploration",
            ],
            "character_context": ["solitary", "tandem", "android/robot", "alien", "scientist/researcher"],
            "atmosphere": [
                "disturbing", "epic", "mysterious", "oppressive",
                "contemplative/meditative", "meticulous", "hypnotic/immersive",
                "psychedelic", "ethereal", "symbolic", "dreamlike/surreal",
            ],
            "source": {
                "type": "novel",
                "title": "The Sentinel",
                "author": "Arthur C. Clarke",
            },
            "awards": [
                {"festival_name": "Academy Awards", "category": "Best Visual Effects", "year": 1969, "result": "won"},
                {"festival_name": "Academy Awards", "category": "Best Director", "year": 1969, "result": "nominated"},
                {"festival_name": "Academy Awards", "category": "Best Picture", "year": 1969, "result": "nominated"},
                {"festival_name": "Academy Awards", "category": "Best Original Screenplay", "year": 1969, "result": "nominated"},
                {"festival_name": "Academy Awards", "category": "Best Art Direction", "year": 1969, "result": "nominated"},
            ],
            "confidence": {
                "categories": 0.95,
                "cinema_type": 0.9,
                "time_context": 0.95,
                "geography": 0.7,
                "place_environment": 0.9,
                "themes": 0.9,
                "character_context": 0.85,
                "atmosphere": 0.9,
                "source": 0.8,
                "awards": 0.95,
            },
            "new_values_suggested": [],
        },
    },
    "la_haine": {
        "title": "La Haine",
        "year": 1995,
        "enrichment": {
            "categories": ["Drama", "Thriller", "slice of life", "black comedy"],
            "cinema_type": [
                "black and white", "art house", "realism", "popular culture",
                "dialogs/punchline", "slang dialogs", "monologue",
            ],
            "time_context": ["1980-90's", "single day"],
            "geography": [
                {"continent": "Europe", "country": "France", "state_city": "Île-de-France", "place_type": "diegetic"},
                {"continent": "Europe", "country": "France", "state_city": "Paris", "place_type": "diegetic"},
            ],
            "place_environment": ["urban", "building"],
            "themes": [
                "social", "societal", "generational", "political", "immigration",
                "class/culture clash", "humanist", "friendship", "solidarity",
                "fight", "rebellion/revolt", "delinquency", "police violence",
                "trauma/accident", "death", "doubt/dilemma", "art: music/dance",
            ],
            "character_context": [
                "trio", "buddies", "teenager", "male ensemble", "interracial",
                "ordinary", "poor/marginal", "cop",
            ],
            "atmosphere": [
                "depressive/sad", "violent", "disturbing", "oppressive",
                "cityscape", "gritty/realistic",
            ],
            "source": {
                "type": "original screenplay",
                "title": None,
                "author": None,
            },
            "awards": [
                {"festival_name": "Cannes Film Festival", "category": "Best Director", "year": 1995, "result": "won"},
                {"festival_name": "César Awards", "category": "Best Film", "year": 1996, "result": "won"},
                {"festival_name": "César Awards", "category": "Best Editing", "year": 1996, "result": "won"},
                {"festival_name": "César Awards", "category": "Best Producer", "year": 1996, "result": "won"},
            ],
            "confidence": {
                "categories": 0.95,
                "cinema_type": 0.95,
                "time_context": 0.95,
                "geography": 0.9,
                "place_environment": 0.95,
                "themes": 0.9,
                "character_context": 0.95,
                "atmosphere": 0.9,
                "source": 0.95,
                "awards": 0.95,
            },
            "new_values_suggested": [],
        },
    },
    "mulholland_drive": {
        "title": "Mulholland Drive",
        "year": 2001,
        "enrichment": {
            "categories": ["Drama", "Thriller", "psychological", "mafia/organized crime"],
            "cinema_type": [
                "aesthetics", "art house", "popular culture",
                "flashback/non linear", "neo-noir",
            ],
            "time_context": ["2000-2010's"],
            "geography": [
                {"continent": "North America", "country": "United States", "state_city": "Los Angeles", "place_type": "diegetic"},
                {"continent": "North America", "country": "United States", "state_city": "Hollywood", "place_type": "diegetic"},
            ],
            "place_environment": ["urban"],
            "themes": [
                "love", "manipulation", "sex", "jealousy", "obsession",
                "trauma/accident", "identity crisis", "amnesia", "guilt",
                "greed/ambition", "lie", "loneliness", "death", "dream",
                "art: cinema",
            ],
            "character_context": [
                "tandem", "couple", "female lead", "LGBT", "loser",
                "star/celebrity", "disturbed/madness", "double",
                "unreliable narrator",
            ],
            "atmosphere": [
                "depressive/sad", "disturbing", "steamy", "mysterious",
                "oppressive", "cityscape", "meticulous", "hypnotic/immersive",
                "symbolic", "dreamlike/surreal",
            ],
            "source": {
                "type": "original screenplay",
                "title": None,
                "author": None,
            },
            "awards": [
                {"festival_name": "Cannes Film Festival", "category": "Best Director", "year": 2001, "result": "won"},
                {"festival_name": "César Awards", "category": "Best Foreign Film", "year": 2002, "result": "nominated"},
            ],
            "confidence": {
                "categories": 0.95,
                "cinema_type": 0.95,
                "time_context": 0.9,
                "geography": 0.9,
                "place_environment": 0.95,
                "themes": 0.9,
                "character_context": 0.9,
                "atmosphere": 0.9,
                "source": 0.95,
                "awards": 0.95,
            },
            "new_values_suggested": [],
        },
    },
}
