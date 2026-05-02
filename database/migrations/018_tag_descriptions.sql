-- Add a centralized tag description table for tooltip hints
CREATE TABLE IF NOT EXISTS tag_description (
    dimension   TEXT NOT NULL,
    tag_name    TEXT NOT NULL,
    description TEXT NOT NULL,
    PRIMARY KEY (dimension, tag_name)
);

-- THEMES
INSERT INTO tag_description (dimension, tag_name, description) VALUES
('themes', 'social', 'Interpersonal relations within a community, class dynamics, or living conditions'),
('themes', 'societal', 'How society functions as a system - institutions, norms, cultural shifts, systemic issues'),
('themes', 'tragedy', 'A narrative driven by fate, inevitability, or a fatal flaw leading to downfall'),
('themes', 'psychological', 'Inner mental life of a character: psyche, mental processes, perceptions, or psychological deterioration'),
('themes', 'death', 'Where mortality, grief, the meaning of death, or the process of dying is what the film is wrestling with'),
('themes', 'transformation', 'Significant and radical change in a character''s physical or mental state between beginning and end'),
('themes', 'whimsical/zany', 'A playful, fanciful, logic-defying spirit - bends or ignores rules of reality in a lighthearted or imaginative way')
ON CONFLICT (dimension, tag_name) DO UPDATE SET description = EXCLUDED.description;

-- ATMOSPHERES
INSERT INTO tag_description (dimension, tag_name, description) VALUES
('atmospheres', 'family-friendly', 'Watchable with children, parents, or any group without discomfort - about audience accessibility, not families on screen'),
('atmospheres', 'feel good', 'Can have adult themes; not necessarily family-friendly, but uplifting'),
('atmospheres', 'crazy/nutty', 'Chaotic, exuberant, over-the-top energy - embraces excess and wild unpredictability'),
('atmospheres', 'delicate/intimate', 'Quiet, tender, emotionally close - handles its subject with softness and subtlety'),
('atmospheres', 'contemplative/meditative', 'Calm, stillness, peaceful observation - static camera, silence, emotional distance or serenity'),
('atmospheres', 'oppressive', 'Sustained, suffocating weight the viewer physically feels throughout'),
('atmospheres', 'meticulous', 'Everything feels deliberate, ordered, controlled - exceptional precision in storytelling or visual composition'),
('atmospheres', 'ethereal', 'Light, floating, airy quality - feels weightless or suspended above reality'),
('atmospheres', 'hypnotic/immersive', 'Trance-like effect through rhythmic editing, repetition, droning sound, visual intensity'),
('atmospheres', 'psychedelic', 'Vivid, hallucinatory, sensory-overload visual or audio experience'),
('atmospheres', 'steamy', 'Strong erotic charge or sexual tension pervading the atmosphere'),
('atmospheres', 'sordid', 'Moral degradation, sleaze, depravity, or a world of seedy, ugly reality'),
('atmospheres', 'cityscape', 'The urban environment as a defining visual and narrative presence'),
('atmospheres', 'pastoral', 'The countryside, rural life, or natural landscape as a defining atmospheric presence'),
('atmospheres', 'gritty/realistic', 'Raw and real life, grounded in harsh or unglamorous reality without cinematic polish'),
('atmospheres', 'epic', 'Grand in scale, scope, or ambition - sweeping narratives, historical or emotional magnitude')
ON CONFLICT (dimension, tag_name) DO UPDATE SET description = EXCLUDED.description;

-- CHARACTERS
INSERT INTO tag_description (dimension, tag_name, description) VALUES
('characters', 'ensemble cast', 'Multiple distinct characters in separate storylines that intersect or parallel each other'),
('characters', 'adult/child', 'Central relationship or dynamic between an adult and a child'),
('characters', 'female', 'Places female experience, perspective, or identity at its core'),
('characters', 'ordinary', 'Ordinariness as a deliberate artistic choice - draws meaning from the mundane'),
('characters', 'simpleton/fool', 'Naivety or simplicity as a defining trait, often for comic effect or as an unexpected lens'),
('characters', 'disabled', 'Significant physical or cognitive disability explicitly depicted and relevant to the narrative'),
('characters', 'outcast/misfit', 'Social rejection or a profound inability to belong'),
('characters', 'double', 'Duplicated, mirrored, or has a doppelganger - literal (twins, clones) or metaphorical (split personality)'),
('characters', 'cross-dressing', 'Disguises as another character/gender, for comic, dramatic, or identity-related purposes'),
('characters', 'unreliable narrator', 'Story told through a perspective the audience discovers is distorted, biased, or deceptive'),
('characters', 'antihero', 'Lacks conventional heroic qualities but the audience follows and roots for them despite flaws'),
('characters', 'vigilante', 'Takes justice into their own hands outside the law'),
('characters', 'vehicle', 'A vehicle as a character or as a central narrative element')
ON CONFLICT (dimension, tag_name) DO UPDATE SET description = EXCLUDED.description;

-- MOTIVATIONS
INSERT INTO tag_description (dimension, tag_name, description) VALUES
('motivations', 'love', 'Deep emotional attachment: romantic, parental, fraternal, platonic'),
('motivations', 'emancipation', 'Freeing from control, constraint, or dependence - also covers coming-of-age growth toward autonomy'),
('motivations', 'communication', 'The act of communicating or failing to - misunderstandings, language barriers, the struggle to connect'),
('motivations', 'honor/duty', 'Acts out of obligation, moral code, or loyalty to a principle larger than self-interest'),
('motivations', 'obsession', 'A pathological, consuming fixation that distorts behavior and judgment'),
('motivations', 'manipulation', 'Deliberately controls, deceives, or psychologically exploits others'),
('motivations', 'sacrifice', 'Deliberately gives up something vital for another person or cause'),
('motivations', 'greed/ambition', 'Pursuit of wealth, status, or power as a personal drive'),
('motivations', 'perversion', 'Desire that transgresses social norms, taken to a dark or disturbing extreme'),
('motivations', 'fight', 'Significant action/combat scenes, not just metaphorical struggles'),
('motivations', 'world-saving', 'Stakes are global or existential - trying to prevent large-scale destruction')
ON CONFLICT (dimension, tag_name) DO UPDATE SET description = EXCLUDED.description;

-- MESSAGES
INSERT INTO tag_description (dimension, tag_name, description) VALUES
('messages', 'humanist', 'Human compassion, dignity, or the value of every individual life'),
('messages', 'anti establishment', 'Challenges or criticizes institutional power, authority, or the status quo'),
('messages', 'traditionalist/way of life', 'A particular cultural tradition, lifestyle, or set of values, often rural or community-based'),
('messages', 'revisionist/alternate history', 'Deliberately reinterprets, subverts, or reimagines historical events or genre conventions'),
('messages', 'surreal', 'Deliberate, often jarring juxtapositions of impossible or irrational elements'),
('messages', 'dreamlike', 'Floating, oneiric quality - dream-like in texture, regardless of whether actual dreams appear'),
('messages', 'symbolic', 'Images, objects, or situations as symbols carrying meaning beyond their literal function'),
('messages', 'poetic', 'Lyrical quality - beauty, rhythm, and emotional resonance over narrative efficiency')
ON CONFLICT (dimension, tag_name) DO UPDATE SET description = EXCLUDED.description;

-- CINEMA TYPES
INSERT INTO tag_description (dimension, tag_name, description) VALUES
('cinema_types', 'aesthetics', 'Strong, distinctive visual and auditory identity - the "look" is inseparable from the film''s meaning'),
('cinema_types', 'expressionism', 'Early 20th-century German movement using extreme visual distortion to externalize psychological states'),
('cinema_types', 'realism', 'Depicts everyday social life without artifice - working classes, fatalism, unembellished truth'),
('cinema_types', 'neo-realism', 'Italian post-war movement: real locations, non-professional actors, stories about ordinary people in ruins of war'),
('cinema_types', 'noir', 'Cynical narratives, moral ambiguity, femmes fatales, high-contrast lighting, deep shadows, urban nights'),
('cinema_types', 'neo-noir', 'Revival and reinterpretation of noir themes and aesthetics in contemporary settings'),
('cinema_types', 'hollywood golden age', 'Major studio system era: star-driven glamour, strict genre conventions, Production Code, lavish values'),
('cinema_types', 'new wave', 'Nouvelle Vague and similar movements: location shooting, jump cuts, breaking the fourth wall, auteur-driven'),
('cinema_types', 'new hollywood', 'Film-school directors breaking from studio conventions - darker, politically engaged, auteur-driven'),
('cinema_types', 'blockbuster', 'Large-scale mainstream commercial entertainment with high budgets and broad audience appeal'),
('cinema_types', 'art house', 'Artistic expression over mass commercial appeal - festival circulation, independent distribution'),
('cinema_types', 'B', 'Originially low-budget commercial genre entertainment with modest production values - not "bad film" or "indie"'),
('cinema_types', 'generational', 'Deeply representative of a specific generation''s identity, struggles, or cultural moment'),
('cinema_types', 'popular culture', 'Explicitly references or is steeped in shared pop culture - speaks through pop culture'),
('cinema_types', 'multi-sequence', 'Narrative structured in distinct segments: multiple storylines, chapters, or anthology-like episodes'),
('cinema_types', 'sequence-shot', 'Notable use of long, unbroken takes as a defining stylistic choice'),
('cinema_types', 'slow cinema', 'Extremely long takes, minimal dialogue, static camera, deliberate pacing as artistic statement'),
('cinema_types', 'dogma', 'Following or inspired by Dogme 95: natural lighting, handheld camera, no effects, diegetic sound'),
('cinema_types', 'dialogs', 'Writing quality, wit, or density of dialogue is a defining characteristic'),
('cinema_types', 'slang dialogs', 'Language rooted in street speech, regional vernacular, or subcultural jargon'),
('cinema_types', 'fait divers/true incident', 'Based on a specific real-life incident, case, or news story'),
('cinema_types', 'costume drama', 'Historical setting, costumes, and production design are central to the experience'),
('cinema_types', 'swashbuckler', 'Sword-fighting heroes in historical settings - dashing protagonists, daring rescues'),
('cinema_types', 'wu xia pian', 'Chinese martial arts genre rooted in the wuxia literary tradition'),
('cinema_types', 'blaxploitation', '1970s movement featuring Black casts in genre films for Black urban audiences'),
('cinema_types', 'giallo', 'Italian thriller/horror: elaborate murders, stylized visuals, mystery-driven plots'),
('cinema_types', 'slasher', 'Horror subgenre: a killer systematically murdering victims in graphic sequences'),
('cinema_types', 'docufiction', 'Dramatizing real events with documentary feel, or documentary format for fictional subjects')
ON CONFLICT (dimension, tag_name) DO UPDATE SET description = EXCLUDED.description;
