"""
Taxonomy configuration for the Film Database project.

All valid taxonomy values extracted from database/seed_taxonomy.sql.
Used by ClaudeEnricher to build prompts and validate outputs.
"""

# =============================================================================
# Valid taxonomy values — extracted from seed_taxonomy.sql
# =============================================================================

VALID_CATEGORIES = [
    "Comedy", "Drama", "Romance", "Action", "Adventure",
    "Thriller", "Science-Fiction", "Fantasy", "Horror", "Musical",
    "Documentary", "Historical",
]

VALID_CINEMA_TYPES = [
    # Group 1: Visual techniques & aesthetics
    "animation", "mixed animation", "CGI", "3D", "motion capture",
    "black and white", "aesthetics",
    # Group 2: Movements & eras
    "silent", "expressionism", "realism", "neo-realism", "noir",
    "hollywood golden age", "new hollywood", "new wave", "neo-noir",
    # Group 3: Industry & culture
    "blockbuster", "art house", "franchise", "B",
    "generational", "popular culture",
    # Group 4: Narrative techniques
    "sequence-shot", "found footage", "multi-sequence",
    "slow cinema", "non linear narrative", "dogma",
    "dialogs", "slang dialogs", "few/no dialogs", "voiceover",
    # Group 5: Cinema sub-genres/archetypes
    "biopic", "historical event", "fait divers/true incident",
    "western", "peplum", "swashbuckler", "costume drama",
    "wu xia pian", "blaxploitation", "giallo", "slasher",
    "black comedy", "docufiction",
]

VALID_PLACE_ENVIRONMENTS = [
    # Group 1: Natural environments
    "urban", "country-style", "forest", "mountains", "desert", "beach",
    "maritime", "island", "underground", "space",
    # Group 2: Buildings & institutions
    "building", "household/house/apartment", "company/factory",
    "school/university", "hospital", "jail", "military", "naval", "ship",
    # Group 3: Narrative settings
    "road movie", "huis clos/confined setting",
    # Group 4: None
    "no particular",
]

VALID_TIME_CONTEXTS = [
    "future", "contemporary", "early 21st", "end 20th",
    "20th post-war", "WW2", "interwar", "WW1", "early 20th",
    "19th", "modern age", "medieval", "antiquity", "prehistoric",
    "undetermined",
    "spring", "summer", "autumn", "winter",
]

VALID_THEMES = [
    # Group 1: Society
    "social", "class struggle", "societal", "political",
    "religion", "business", "journalism/media", "censorship",
    "trial/judicial chronicle", "prison", "war", "immigration",
    "slavery", "colonialism", "tragedy", "apocalypse", "disaster",
    # Group 2: Personal / Psychological
    "trauma/accident", "psychological", "identity crisis", "illness",
    "amnesia", "death", "mourning", "addiction/drugs", "time passing",
    "transformation",
    # Group 3: Crime / Thriller
    "investigation", "spy", "crime", "sex crime", "organized crime",
    "heist", "kidnapping/hostage",
    "police violence", "corruption", "delinquency", "organized fraud",
    "mafia", "serial killer", "chase/escape", "terrorism",
    "sect", "survival",
    # Group 4: Sci-fi / Fantasy
    "dystopia", "tales and legends", "supernatural",
    "sorcery", "alien contact", "paranormal", "curse",
    "time travel/loop", "virtual reality", "dream", "whimsical/zany",
    # Group 5: Art, Sport & Entertainment
    "art", "art: music", "art: cinema", "art: literature", "art: fashion",
    "art: painting", "art: sculpture", "art: theatre", "art: radio",
    "art: architecture", "martial arts",
    "sport", "sport: individual", "sport: collective",
    "sport: tournament", "sport: motor",
    "party", "game", "gambling",
    # Group 6: Miscellaneous
    "nature", "AI/technology", "food/cooking",
]

VALID_CHARACTERS = [
    # Group 1: Group structure
    "solitary", "tandem", "trio", "couple", "relatives", "generations",
    "buddies", "team/group/gang", "ensemble cast",
    # Group 2: Age & identity
    "childhood", "teenager", "elderly", "adult/child", "female", "LGBT",
    "interracial",
    # Group 3: Social status & traits
    "ordinary", "poor/marginal", "wealthy", "genius", "idiot",
    "charismatic", "loser", "star/celebrity", "disturbed/madness",
    "disabled", "outcast/misfit", "prostitute", "psychopath",
    # Group 4: Narrative devices
    "double", "cross-dressing", "unreliable narrator",
    # Group 5: Archetypes — human
    "super hero", "antihero", "cop", "detective", "vigilante",
    "gangster", "soldier", "femme fatale", "samurai", "pirate", "viking",
    "scientist/researcher", "mentor",
    # Group 6: Non-human & creatures
    "animal/wildlife", "monster/terrestrial creature", "evil", "witch",
    "ghost/spirit", "vampire", "zombie", "alien", "android", "vehicle",
]

VALID_ATMOSPHERES = [
    # Group 1: Light/Joyful
    "family-friendly", "feel good", "crazy/nutty", "delicate/intimate",
    "contemplative/meditative",
    # Group 2: Tension
    "mysterious", "oppressive", "claustrophobic",
    # Group 3: Attention
    "meticulous", "ethereal", "hypnotic/immersive", "psychedelic",
    # Group 4: Dark/Extreme
    "depressive/sad", "violent", "disturbing", "steamy", "gore", "sordid",
    # Group 5: Scale & Tone
    "gritty/realistic", "epic",
]

VALID_MOTIVATIONS = [
    # Group 1: Positive bonds
    "love", "friendship", "solidarity", "communication",
    "emancipation", "redemption", "honor/duty",
    # Group 2: Inner conflict
    "obsession", "doubt/dilemma", "lie", "manipulation", "sacrifice",
    # Group 3: Desire & transgression
    "greed/ambition", "sex", "adultery", "jealousy", "harassment",
    "perversion",
    # Group 4: Conflict & struggle
    "power", "rivalry", "fight", "rebellion/revolt", "vengeance",
    # Group 5: Epic quests
    "odyssey", "quest", "world-saving", "invasion",
]

VALID_MESSAGES = [
    # Group 1: Values & ideology
    "humanist", "feminist", "ecological", "political",
    "anti establishment", "nostalgic", "patriotic",
    "traditionalist/way of life",
    # Group 2: Comedy & satire
    "parodic", "satirical", "absurdist", "revisionist/alternate history",
    # Group 3: Reflection
    "philosophical", "metaphysical",
    # Group 4: Artistic expression
    "dreamlike", "surreal", "symbolic", "poetic",
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
    "motivations": VALID_MOTIVATIONS,
    "message": VALID_MESSAGES,
}

# =============================================================================
# Reference film examples — validated classifications from CLAUDE.md
# Used as few-shot examples in the enrichment prompt
# =============================================================================

REFERENCE_EXAMPLES = {
    "2001": {
        "title": "2001: A Space Odyssey",
        "year": 1968,
        "enrichment": {
            "categories": ["Science-Fiction", "Drama", "Adventure"],
            "cinema_type": ["blockbuster", "art house", "slow cinema", "new hollywood", "aesthetics"],
            "time_context": ["prehistoric", "20th post-war", "future"],
            "geography": [
                {"continent": "Africa", "country": "Kenya", "state_city": None, "place_type": "diegetic"},
            ],
            "place_environment": ["space", "desert"],
            "themes": [
                "alien contact", "AI/technology", "death",
                "time passing", "transformation",
            ],
            "character_context": ["solitary", "tandem", "android", "alien"],
            "atmosphere": ["contemplative/meditative", "oppressive", "mysterious", "disturbing", "psychedelic"],
            "motivations": ["quest", "odyssey", "power", "doubt/dilemma"],
            "message": ["philosophical", "metaphysical", "symbolic", "surreal"],
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
                "motivations": 0.85,
                "message": 0.9,
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
            "categories": ["Drama", "Thriller"],
            "cinema_type": ["art house", "black and white", "realism", "generational", "slang dialogs"],
            "time_context": ["end 20th"],
            "geography": [
                {"continent": "Europe", "country": "France", "state_city": "Île-de-France", "place_type": "diegetic"},
                {"continent": "Europe", "country": "France", "state_city": "Paris", "place_type": "diegetic"},
            ],
            "place_environment": ["urban", "building"],
            "themes": [
                "social", "societal", "political", "delinquency",
                "tragedy", "death", "police violence", "immigration", "trauma/accident",
            ],
            "character_context": ["trio", "buddies", "interracial", "poor/marginal", "teenager", "cop"],
            "atmosphere": ["violent", "oppressive", "depressive/sad", "gritty/realistic"],
            "motivations": [
                "friendship", "solidarity", "rebellion/revolt", "vengeance", "fight",
            ],
            "message": ["political", "humanist", "philosophical"],
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
                "motivations": 0.9,
                "message": 0.9,
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
            "categories": ["Drama", "Thriller"],
            "cinema_type": ["art house", "non linear narrative", "aesthetics", "neo-noir"],
            "time_context": ["early 21st"],
            "geography": [
                {"continent": "North America", "country": "United States", "state_city": "Los Angeles", "place_type": "diegetic"},
                {"continent": "North America", "country": "United States", "state_city": "Hollywood", "place_type": "diegetic"},
            ],
            "place_environment": ["urban"],
            "themes": [
                "psychological", "dream", "art: cinema", "crime",
                "investigation", "identity crisis", "amnesia", "trauma/accident", "mafia",
            ],
            "character_context": ["tandem", "couple", "female", "double", "LGBT", "star/celebrity"],
            "atmosphere": ["mysterious", "steamy", "disturbing", "oppressive", "hypnotic/immersive"],
            "motivations": [
                "love", "obsession", "jealousy", "manipulation",
                "lie", "sex", "adultery", "vengeance",
            ],
            "message": ["surreal", "dreamlike", "symbolic", "metaphysical"],
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
                "motivations": 0.85,
                "message": 0.95,
                "source": 0.95,
                "awards": 0.95,
            },
            "new_values_suggested": [],
        },
    },
}
