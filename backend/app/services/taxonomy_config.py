"""
Taxonomy configuration for the Film Database project.

All valid taxonomy values extracted from database/seed_taxonomy.sql.
Used by ClaudeEnricher to build prompts and validate outputs.
"""

# =============================================================================
# Valid taxonomy values — extracted from seed_taxonomy.sql
# =============================================================================

VALID_CATEGORIES = [
    "Action", "Adventure", "Comedy", "Documentary", "Drama", "Romance",
    "Thriller", "Horror", "Science-Fiction", "Fantasy", "Musical",
    "Historical",
]

VALID_HISTORIC_SUBCATEGORIES = [
    "biopic", "human interest story", "judicial chronicle",
    "western", "peplum", "swashbuckler", "event",
]

VALID_CINEMA_TYPES = [
    # Group 1: Visual techniques & aesthetics
    "animation", "mixed animation", "CGI", "3D", "motion capture",
    "black and white", "aesthetics",
    # Group 2: Movements & eras
    "silent", "expressionism", "neo-realism", "noir", "hollywood golden age",
    "new hollywood", "new wave", "realism", "neo-noir", "costume",
    "dogma", "blaxploitation", "wu xia pian",
    # Group 3: Industry & culture
    "blockbuster", "art house", "B", "Z", "Collection",
    "generational", "popular culture",
    # Group 4: Narrative techniques
    "sequence-shot", "found footage", "multi-sequence",
    "slow cinema", "non linear narrative",
    # Group 5: Dialog style
    "dialogs", "slang dialogs",
]

VALID_PLACE_ENVIRONMENTS = [
    "urban", "country-style", "forest", "mountains", "desert", "beach",
    "maritime", "island", "space",
    "building", "household/house/apartment", "company/factory",
    "school/university", "hospital", "jail", "military", "naval", "ship",
    "road movie", "huis clos",
    "no particular",
]

VALID_TIME_CONTEXTS = [
    "undetermined", "future", "contemporary", "end 20th",
    "30-year post-war boom", "WW2", "interwar", "WW1", "early 20th",
    "19th", "modern age", "medieval", "antiquity", "prehistoric",
    "summer", "winter", "autumn", "spring",
]

VALID_THEMES = [
    # Group 1: Society
    "social", "class struggle", "societal", "immigration", "political",
    "religion", "business", "censorship", "trial", "prison", "war",
    "tragedy", "apocalypse", "disaster",
    # Group 2: Personal / Psychological
    "trauma/accident", "psychological", "identity crisis", "disease",
    "amnesia", "death", "mourning", "addiction/drugs", "time passing",
    "evolution",
    # Group 3: Crime / Thriller
    "investigation", "spy", "crime", "sex crime", "organized crime",
    "police violence", "corruption", "delinquency", "organized fraud",
    "mafia", "gangster", "serial killer", "chase/escape", "terrorism",
    "sect", "survival", "slasher",
    # Group 4: Sci-fi / Fantasy
    "futuristic", "dystopia", "tales and legends", "supernatural",
    "sorcery", "alien contact", "paranormal", "time travel/loop",
    "virtual reality", "dream", "nonsense", "curse",
    # Group 5: Art & Sport (hierarchical: "parent: sub")
    "art", "art: music", "art: cinema", "art: literature", "art: fashion",
    "art: painting", "art: sculpture", "art: theatre", "art: radio",
    "martial arts",
    "sport", "sport: individual", "sport: collective",
    "sport: tournament", "sport: motor",
    # Group 6: Miscellaneous
    "nature", "AI/technology", "food/cooking", "party", "book", "game",
]

VALID_CHARACTERS = [
    # Group 1: Group structure
    "solitary", "tandem", "trio", "couple", "relatives", "generations",
    "buddies", "team/group/gang", "interracial", "ensemble cast",
    # Group 2: Age & identity
    "childhood", "teenager", "elderly", "adult/child", "female", "LGBT",
    # Group 3: Social status & traits
    "ordinary", "poor/marginal", "wealthy", "genius", "idiot", "looser",
    "star/celebrity", "madness", "freak/disabled", "prostitute", "psychopath",
    # Group 4: Narrative devices
    "double", "cross-dressing", "unreliable narrator",
    # Group 5: Archetypes — human
    "super hero", "antihero", "cop", "detective", "vigilante", "soldier",
    "femme fatale", "samourai", "pirate", "viking", "barbarian",
    # Group 6: Non-human & creatures
    "animal/wildlife", "monster/terrestrial creature", "evil", "witch",
    "ghost/spirit", "vampire", "zombie", "alien", "android", "vehicle",
]

VALID_ATMOSPHERES = [
    # Group 1: Light
    "family", "feel good", "crazy/nutty", "depressive/sad",
    # Group 2: Tension
    "mysterious", "oppressive", "claustrophobic",
    # Group 3: Contemplative
    "contemplative", "ethereal", "hypnotic", "psychedelic",
    # Group 4: Dark
    "violent", "disturbing", "sulfurous", "trash", "gore",
    "awful/seedy/depraved",
]

VALID_MOTIVATIONS = [
    # Group 1: Positive bonds
    "feelings", "friendship", "solidarity", "communication",
    "emancipation", "redemption",
    # Group 2: Inner conflict
    "obsession", "doubt/dilemma", "lie", "manipulation",
    # Group 3: Desire & transgression
    "sex", "adultery", "jealousy", "harassment", "perversion",
    # Group 4: Conflict & struggle
    "power", "rivalry", "fight", "rebellion/revolt", "vengeance",
    # Group 5: Epic quests
    "odyssey", "quest", "world saver", "invasion",
]

VALID_MESSAGES = [
    # Group 1: Values & ideology
    "humanist", "philosophical", "feminist", "ecological", "political",
    # Group 2: Comedy & satire
    "parodic", "satirical", "black comedy", "absurdist",
    # Group 3: Cultural perspective
    "anti establishment", "nostalgic", "patriotic",
    "traditionalist/way of life", "history revisited",
    # Group 4: Artistic expression
    "dreamlike", "surreal", "symbolic", "metaphysical",
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
            "historic_subcategories": [],
            "cinema_type": ["blockbuster", "art house", "slow cinema", "new hollywood", "aesthetics"],
            "time_context": ["prehistoric", "30-year post-war boom", "future"],
            "geography": [
                {"continent": "Africa", "country": "Kenya", "state_city": None, "place_type": "diegetic"},
            ],
            "place_environment": ["space", "desert"],
            "themes": [
                "futuristic", "alien contact", "AI/technology", "death",
                "time passing", "evolution",
            ],
            "character_context": ["solitary", "tandem", "android", "alien"],
            "atmosphere": ["contemplative", "oppressive", "mysterious", "disturbing", "psychedelic"],
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
            "historic_subcategories": [],
            "cinema_type": ["art house", "black and white", "realism", "generational"],
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
            "atmosphere": ["violent", "oppressive", "depressive/sad"],
            "motivations": [
                "friendship", "solidarity", "rebellion/revolt", "vengeance", "fight",
            ],
            "message": ["political", "humanist", "black comedy"],
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
            "historic_subcategories": [],
            "cinema_type": ["art house", "non linear narrative", "aesthetics", "neo-noir"],
            "time_context": ["contemporary"],
            "geography": [
                {"continent": "North America", "country": "United States", "state_city": "Los Angeles", "place_type": "diegetic"},
                {"continent": "North America", "country": "United States", "state_city": "Hollywood", "place_type": "diegetic"},
            ],
            "place_environment": ["urban"],
            "themes": [
                "psychological", "dream", "art: cinema", "crime",
                "investigation", "identity crisis", "amnesia", "trauma/accident", "mafia",
            ],
            "character_context": ["tandem", "couple", "female", "double", "LGBT"],
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
