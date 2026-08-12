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
    "trial/judicial chronicle", "prison", "biopic", "fait divers/true incident",
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
    "school/university", "hospital", "jail", "military", "naval", "castle",
    "hotel",
    # Narrative settings (300s)
    "road movie", "huis clos/confined setting",
    # Vehicles (400s)
    "car/bus", "train", "airplane", "ship",
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
    # Social status & traits (300s)
    "ordinary", "poor/marginal", "wealthy", "genius", "simpleton/fool",
    "loser", "star/celebrity", "disturbed/madness", "disabled",
    "outcast/misfit", "sex worker", "psychopath",
    # Narrative devices (400s)
    "double", "cross-dressing", "unreliable narrator",
    # Archetypes — human (500s)
    "super hero", "chosen one", "antihero", "scientist/researcher", "mentor",
    "cop", "detective", "secret agent", "vigilante", "gangster", "soldier",
    "warrior", "knight", "samurai", "pirate", "viking", "witch/wizard",
    "femme fatale",
    # Non-human & creatures (600s)
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
            "categories": ["Science-Fiction", "Drama", "Adventure", "odyssey/quest"],
            "cinema_type": ["blockbuster", "art house", "slow cinema", "new hollywood", "aesthetics"],
            "time_context": ["prehistoric", "1950-60-70's", "future", "decades-spanning"],
            "geography": [
                {"continent": "Africa", "country": "Kenya", "state_city": None, "place_type": "diegetic"},
            ],
            "place_environment": ["space", "desert"],
            "themes": [
                "alien contact", "AI/technology", "death", "time passing",
                "transformation", "philosophical", "metaphysical", "power",
                "doubt/dilemma", "exploration",
            ],
            "character_context": ["solitary", "tandem", "android/robot", "alien", "scientist/researcher"],
            "atmosphere": [
                "contemplative/meditative", "oppressive", "mysterious", "disturbing",
                "psychedelic", "symbolic", "dreamlike/surreal", "epic",
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
            "categories": ["Drama", "Thriller", "tragedy"],
            "cinema_type": ["art house", "black and white", "realism", "slang dialogs"],
            "time_context": ["1980-90's", "single day"],
            "geography": [
                {"continent": "Europe", "country": "France", "state_city": "Île-de-France", "place_type": "diegetic"},
                {"continent": "Europe", "country": "France", "state_city": "Paris", "place_type": "diegetic"},
            ],
            "place_environment": ["urban", "building"],
            "themes": [
                "social", "societal", "generational", "political", "delinquency",
                "death", "police violence", "immigration", "trauma/accident",
                "friendship", "solidarity", "rebellion/revolt", "vengeance",
                "fight", "humanist", "philosophical",
            ],
            "character_context": ["trio", "buddies", "interracial", "poor/marginal", "teenager", "cop"],
            "atmosphere": ["violent", "oppressive", "depressive/sad", "gritty/realistic", "cityscape"],
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
            "categories": [
                "Drama", "Thriller", "psychological", "crime", "investigation",
                "mafia/organized crime",
            ],
            "cinema_type": ["art house", "flashback/non linear", "aesthetics", "neo-noir"],
            "time_context": ["2000-2010's"],
            "geography": [
                {"continent": "North America", "country": "United States", "state_city": "Los Angeles", "place_type": "diegetic"},
                {"continent": "North America", "country": "United States", "state_city": "Hollywood", "place_type": "diegetic"},
            ],
            "place_environment": ["urban"],
            "themes": [
                "dream", "art: cinema", "identity crisis", "amnesia",
                "trauma/accident", "love", "obsession", "jealousy",
                "manipulation", "lie", "sex", "adultery", "vengeance",
                "metaphysical",
            ],
            "character_context": ["tandem", "couple", "female lead", "double", "LGBT", "star/celebrity"],
            "atmosphere": [
                "mysterious", "steamy", "disturbing", "oppressive",
                "hypnotic/immersive", "symbolic", "dreamlike/surreal",
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
