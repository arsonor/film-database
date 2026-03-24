"""
Taxonomy configuration for the Film Database project.

All valid taxonomy values extracted from database/seed_taxonomy.sql.
Used by ClaudeEnricher to build prompts and validate outputs.
"""

# =============================================================================
# Valid taxonomy values — extracted from seed_taxonomy.sql
# =============================================================================

VALID_CATEGORIES = [
    "Action", "Adventure", "Comedy", "Drama", "Romance", "Thriller",
    "Horror", "Science-Fiction", "Fantasy", "Musical", "Disaster", "Historical",
]

VALID_HISTORIC_SUBCATEGORIES = [
    "biopic", "human interest story", "judicial chronicle",
    "western", "peplum", "swashbuckler",
]

VALID_CINEMA_TYPES = [
    "silent", "animation", "mixed animation", "art house", "blockbuster",
    "sequence-shot", "found footage", "motion capture", "multi-sequence",
    "black_and_white", "slow_cinema", "non_linear_narrative",
]

VALID_CULTURAL_MOVEMENTS = [
    "expressionism", "neo-realism", "realism", "noir", "hollywood golden age",
    "new hollywood", "new wave", "neo-noir", "dogma", "blaxploitation",
    "wu xia pian", "generational", "popular culture", "aesthetics",
    "CGI", "3D", "B", "Z", "Collection",
]

VALID_PLACE_ENVIRONMENTS = [
    "no particular", "urban", "country-style", "maritime", "naval", "island",
    "forest", "mountains", "desert", "beach", "space", "huis clos",
    "road movie", "school/university", "company/factory", "building",
    "household/house/apartment", "jail", "hospital",
]

VALID_TIME_CONTEXTS = [
    "undetermined", "future", "contemporary", "end 20th",
    "30-year post-war boom", "WW2", "interwar", "WW1", "early 20th",
    "19th", "modern age", "medieval", "antiquity", "prehistoric",
    "summer", "winter", "autumn", "spring",
]

VALID_THEMES = [
    # Core themes
    "social", "societal", "political", "religion", "business", "trial",
    "prison", "apocalypse", "war", "tragedy", "trauma", "psychological",
    "disease", "accident", "death", "mourning", "addiction/drugs",
    "time passing", "investigation", "spy", "crime", "organized crime",
    "delinquency", "organized fraud", "sex crime", "mafia", "gangster",
    "serial killer", "chase/escape", "terrorism", "sect", "survival",
    "slasher", "futuristic", "dystopia", "tales and legends", "supernatural",
    "sorcery", "alien contact", "paranormal", "time travel/loop",
    "virtual reality", "dream", "nonsense",
    # Art sub-types (hierarchical: "parent: sub")
    "art", "art: music", "art: cinema", "art: literature", "art: fashion",
    "art: painting", "art: sculpture", "art: theatre", "art: radio",
    # Sport sub-types (hierarchical: "parent: sub")
    "sport", "sport: motor", "sport: individual", "sport: collective",
    "sport: tournament",
    # More core themes
    "martial arts", "nature", "technology", "food/cooking",
    "party", "book",
    # Extended themes
    "identity_crisis", "police_violence", "evolution",
    "artificial_intelligence", "amnesia", "corruption", "class_struggle",
    "immigration", "censorship",
]

VALID_CHARACTERS_TYPES = [
    "solitary", "tandem", "couple", "adult/child", "trio", "buddies",
    "gang", "relatives", "generations", "ensemble cast", "animal/wildlife",
]

VALID_CHARACTER_CONTEXTS = [
    # Character Context
    "childhood", "teenager", "elderly", "female", "LGBT", "cross-dressing",
    "double", "interracial",
    # Character Archetypes
    "super hero", "vigilante", "cop", "detective", "samourai", "pirate",
    "viking", "barbarian", "psychopath", "madness", "idiot", "looser",
    "prostitute", "freak/disabled", "monster/terrestrial creature",
    "ghost/spirit", "evil", "witch", "vampire", "zombie", "android", "alien",
    # Extended archetypes
    "unreliable_narrator", "antihero", "femme_fatale",
]

VALID_ATMOSPHERES = [
    # Core atmosphere
    "family", "feel good", "crazy/nutty", "depressive/sad", "sulfurous",
    "mysterious", "violent", "trash", "gore", "awful/seedy/depraved",
    "oppressive", "disturbing", "contemplative",
    # Extended atmosphere
    "hypnotic", "psychedelic", "ethereal", "claustrophobic",
]

VALID_MOTIVATIONS = [
    "feelings", "friendship", "emancipation", "solidarity", "adultery",
    "jealousy", "sex", "harassment", "lie", "doubt/dilemma", "rivalry",
    "power", "perversion", "manipulation", "redemption", "obsession",
    "vengeance", "rebellion/revolt", "fight", "odyssey", "quest",
    "world saver", "survival",
]

VALID_MESSAGES = [
    # Core messages
    "parodic", "satirical", "political", "humanist", "nostalgic",
    "dreamlike", "surreal", "symbolic", "philosophical", "metaphysical",
    "dialogs", "slang dialogs", "black comedy",
    # Extended messages
    "anti_establishment", "feminist", "absurdist", "ecological",
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
    "historic_subcategories": VALID_HISTORIC_SUBCATEGORIES,
    "cinema_type": VALID_CINEMA_TYPES,
    "cultural_movement": VALID_CULTURAL_MOVEMENTS,
    "time_context": VALID_TIME_CONTEXTS,
    "place_environment": VALID_PLACE_ENVIRONMENTS,
    "themes": VALID_THEMES,
    "characters_type": VALID_CHARACTERS_TYPES,
    "character_context": VALID_CHARACTER_CONTEXTS,
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
            "historic_subcategories": [],
            "cinema_type": ["blockbuster", "art house"],
            "cultural_movement": ["new hollywood", "aesthetics"],
            "time_context": ["prehistoric", "30-year post-war boom", "future"],
            "geography": [
                {"continent": "Africa", "country": "Kenya", "state_city": None, "place_type": "diegetic"},
            ],
            "place_environment": ["space", "desert"],
            "themes": [
                "futuristic", "alien contact", "technology", "death",
                "time passing", "evolution",
            ],
            "characters_type": ["solitary", "tandem"],
            "character_context": ["android", "alien"],
            "atmosphere": ["contemplative", "oppressive", "mysterious", "disturbing"],
            "motivations": ["quest", "odyssey", "power", "doubt/dilemma", "survival"],
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
                "cultural_movement": 0.8,
                "time_context": 0.95,
                "geography": 0.7,
                "place_environment": 0.9,
                "themes": 0.9,
                "characters_type": 0.85,
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
            "historic_subcategories": [],
            "cinema_type": ["art house", "black_and_white"],
            "cultural_movement": ["realism", "generational"],
            "time_context": ["contemporary", "end 20th"],
            "geography": [
                {"continent": "Europe", "country": "France", "state_city": "Île-de-France", "place_type": "diegetic"},
                {"continent": "Europe", "country": "France", "state_city": "Paris", "place_type": "diegetic"},
            ],
            "place_environment": ["urban"],
            "themes": [
                "social", "societal", "political", "delinquency",
                "tragedy", "death", "police_violence",
            ],
            "characters_type": ["trio", "buddies"],
            "character_context": ["interracial", "teenager"],
            "atmosphere": ["violent", "oppressive", "depressive/sad"],
            "motivations": [
                "friendship", "solidarity", "rebellion/revolt", "vengeance",
            ],
            "message": ["political", "humanist", "slang dialogs", "black comedy"],
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
                "cultural_movement": 0.85,
                "time_context": 0.95,
                "geography": 0.9,
                "place_environment": 0.95,
                "themes": 0.9,
                "characters_type": 0.95,
                "character_context": 0.9,
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
            "historic_subcategories": [],
            "cinema_type": ["art house"],
            "cultural_movement": ["aesthetics", "neo-noir"],
            "time_context": ["contemporary", "end 20th"],
            "geography": [
                {"continent": "North America", "country": "United States", "state_city": "Los Angeles", "place_type": "diegetic"},
                {"continent": "North America", "country": "United States", "state_city": "Hollywood", "place_type": "diegetic"},
            ],
            "place_environment": ["urban"],
            "themes": [
                "psychological", "dream", "art: cinema", "crime",
                "investigation", "identity_crisis", "accident", "mafia",
            ],
            "characters_type": ["tandem", "couple"],
            "character_context": ["female", "double", "LGBT"],
            "atmosphere": ["mysterious", "sulfurous", "disturbing", "oppressive", "hypnotic"],
            "motivations": [
                "feelings", "obsession", "jealousy", "manipulation",
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
                "cultural_movement": 0.9,
                "time_context": 0.9,
                "geography": 0.9,
                "place_environment": 0.95,
                "themes": 0.9,
                "characters_type": 0.9,
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
