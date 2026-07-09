"""
content_bank.py
----------------
All the *pedagogical content* lives here, separated from the app logic, so
you and your sister can add vocab, scenarios, stories, quests, and badges
without touching any engine code. See README "Customization Tips".

Content is tagged by CEFR level (A1-C1) so the tutor engine can pick
material that's roughly "i+1": one small notch above what the learner has
already mastered (Krashen's Comprehensible Input Hypothesis).

NOTE ON THRESHOLDS: a few badge/quest targets in this file (and in
gamification.py) are deliberately sized to what's actually in this bank
today (e.g. "learn all 4 Québec words", not an arbitrary round number) --
if you add more vocab/scenarios below, some thresholds in gamification.py
can be raised back up to stay meaningfully challenging.
"""

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1"]

# ---------------------------------------------------------------------------
# GAME LEVELS (separate from CEFR language level -- this is the XP ladder)
# ---------------------------------------------------------------------------
GAME_LEVELS = [
    (1, 0), (2, 80), (3, 180), (4, 320), (5, 500), (6, 750), (7, 1050),
    (8, 1450), (9, 1950), (10, 2600), (11, 3400), (12, 4400), (13, 5600),
    (14, 7000), (15, 8700),
]

LEVEL_UNLOCKS = {
    3: "Thème 'Océan' débloqué 🌊",
    5: "Thème 'Automne' débloqué 🍁",
    7: "Avatar spécial débloqué 🐸",
    10: "Thème 'Aurore' débloqué 🌅",
    12: "Avatar spécial débloqué 🦄",
}

# ---------------------------------------------------------------------------
# VOCABULARY BANK
# ---------------------------------------------------------------------------
VOCAB = [
    # --- A1: Salutations ---
    {"id": "salut1", "cefr": "A1", "theme": "Salutations", "fr": "Bonjour", "en": "Hello / Good day",
     "ex_fr": "Bonjour ! Comment ça va ?", "ex_en": "Hello! How are you?"},
    {"id": "salut2", "cefr": "A1", "theme": "Salutations", "fr": "Salut", "en": "Hi / Bye (informal)",
     "ex_fr": "Salut, ça va ?", "ex_en": "Hi, how's it going?"},
    {"id": "salut3", "cefr": "A1", "theme": "Salutations", "fr": "Merci", "en": "Thank you",
     "ex_fr": "Merci beaucoup !", "ex_en": "Thank you very much!"},
    {"id": "salut4", "cefr": "A1", "theme": "Salutations", "fr": "S'il vous plaît", "en": "Please (formal)",
     "ex_fr": "Un café, s'il vous plaît.", "ex_en": "A coffee, please."},
    {"id": "salut5", "cefr": "A1", "theme": "Salutations", "fr": "À bientôt", "en": "See you soon",
     "ex_fr": "Au revoir, à bientôt !", "ex_en": "Goodbye, see you soon!"},
    # --- A1: La famille ---
    {"id": "fam1", "cefr": "A1", "theme": "La famille", "fr": "la sœur", "en": "sister",
     "ex_fr": "Ma sœur apprend le français avec moi.", "ex_en": "My sister is learning French with me."},
    {"id": "fam2", "cefr": "A1", "theme": "La famille", "fr": "le frère", "en": "brother",
     "ex_fr": "Mon frère habite à Toronto.", "ex_en": "My brother lives in Toronto."},
    {"id": "fam3", "cefr": "A1", "theme": "La famille", "fr": "les parents", "en": "parents",
     "ex_fr": "Nos parents parlent un peu français.", "ex_en": "Our parents speak a little French."},
    {"id": "fam4", "cefr": "A1", "theme": "La famille", "fr": "la famille", "en": "family",
     "ex_fr": "J'aime ma famille.", "ex_en": "I love my family."},
    # --- A1: Au café ---
    {"id": "cafe1", "cefr": "A1", "theme": "Au café", "fr": "un café", "en": "a coffee",
     "ex_fr": "Je voudrais un café, s'il vous plaît.", "ex_en": "I'd like a coffee, please."},
    {"id": "cafe2", "cefr": "A1", "theme": "Au café", "fr": "un croissant", "en": "a croissant",
     "ex_fr": "Un croissant et un café, merci.", "ex_en": "A croissant and a coffee, thanks."},
    {"id": "cafe3", "cefr": "A1", "theme": "Au café", "fr": "l'addition", "en": "the bill/check",
     "ex_fr": "L'addition, s'il vous plaît.", "ex_en": "The check, please."},
    {"id": "cafe4", "cefr": "A1", "theme": "Au café", "fr": "combien ça coûte", "en": "how much does it cost",
     "ex_fr": "Combien ça coûte, le café ?", "ex_en": "How much does the coffee cost?"},
    # --- A1: La météo ---
    {"id": "meteo1", "cefr": "A1", "theme": "La météo", "fr": "il fait beau", "en": "the weather is nice",
     "ex_fr": "Aujourd'hui, il fait beau.", "ex_en": "Today the weather is nice."},
    {"id": "meteo2", "cefr": "A1", "theme": "La météo", "fr": "il neige", "en": "it's snowing",
     "ex_fr": "En janvier, il neige beaucoup au Québec.", "ex_en": "In January, it snows a lot in Quebec."},
    {"id": "meteo3", "cefr": "A1", "theme": "La météo", "fr": "il fait froid", "en": "it's cold",
     "ex_fr": "Il fait froid à Niagara en hiver.", "ex_en": "It's cold in Niagara in winter."},
    # --- A2: La vie quotidienne ---
    {"id": "vie1", "cefr": "A2", "theme": "La vie quotidienne", "fr": "se réveiller", "en": "to wake up",
     "ex_fr": "Je me réveille à sept heures.", "ex_en": "I wake up at seven o'clock."},
    {"id": "vie2", "cefr": "A2", "theme": "La vie quotidienne", "fr": "le travail", "en": "work",
     "ex_fr": "Après le travail, je fais du sport.", "ex_en": "After work, I exercise."},
    {"id": "vie3", "cefr": "A2", "theme": "La vie quotidienne", "fr": "faire les courses", "en": "to go grocery shopping",
     "ex_fr": "Le samedi, je fais les courses.", "ex_en": "On Saturdays, I go grocery shopping."},
    {"id": "vie4", "cefr": "A2", "theme": "La vie quotidienne", "fr": "se coucher", "en": "to go to bed",
     "ex_fr": "Je me couche vers minuit.", "ex_en": "I go to bed around midnight."},
    # --- A2: Les voyages ---
    {"id": "voy1", "cefr": "A2", "theme": "Les voyages", "fr": "l'aéroport", "en": "the airport",
     "ex_fr": "On se retrouve à l'aéroport.", "ex_en": "We'll meet at the airport."},
    {"id": "voy2", "cefr": "A2", "theme": "Les voyages", "fr": "une valise", "en": "a suitcase",
     "ex_fr": "Ma valise est très lourde.", "ex_en": "My suitcase is very heavy."},
    {"id": "voy3", "cefr": "A2", "theme": "Les voyages", "fr": "réserver", "en": "to book/reserve",
     "ex_fr": "J'ai réservé une chambre d'hôtel.", "ex_en": "I booked a hotel room."},
    {"id": "voy4", "cefr": "A2", "theme": "Les voyages", "fr": "le chemin", "en": "the way/path",
     "ex_fr": "Excusez-moi, quel est le chemin pour la gare ?", "ex_en": "Excuse me, which way is the train station?"},
    # --- A2/B1: Le Québec & le Canada français (cultural immersion) ---
    {"id": "qc1", "cefr": "A2", "theme": "Le Québec", "fr": "la cabane à sucre", "en": "sugar shack (maple syrup house)",
     "ex_fr": "Au printemps, on va à la cabane à sucre.", "ex_en": "In spring, we go to the sugar shack."},
    {"id": "qc2", "cefr": "A2", "theme": "Le Québec", "fr": "le Vieux-Québec", "en": "Old Quebec (historic district)",
     "ex_fr": "Le Vieux-Québec est magnifique en hiver.", "ex_en": "Old Quebec is beautiful in winter."},
    {"id": "qc3", "cefr": "B1", "theme": "Le Québec", "fr": "magasiner", "en": "to shop (Québécois French)",
     "ex_fr": "On va magasiner au centre-ville.", "ex_en": "We're going shopping downtown."},
    {"id": "qc4", "cefr": "B1", "theme": "Le Québec", "fr": "un dépanneur", "en": "a convenience store (Québécois)",
     "ex_fr": "Je vais acheter du lait au dépanneur.", "ex_en": "I'm going to buy milk at the convenience store."},
    # --- B1: Les émotions ---
    {"id": "emo1", "cefr": "B1", "theme": "Les émotions", "fr": "être fier / fière", "en": "to be proud",
     "ex_fr": "Je suis fière de nos progrès en français !", "ex_en": "I'm proud of our progress in French!"},
    {"id": "emo2", "cefr": "B1", "theme": "Les émotions", "fr": "avoir hâte de", "en": "to look forward to",
     "ex_fr": "J'ai hâte de te voir ce week-end.", "ex_en": "I'm looking forward to seeing you this weekend."},
    {"id": "emo3", "cefr": "B1", "theme": "Les émotions", "fr": "être soulagé(e)", "en": "to be relieved",
     "ex_fr": "Je suis soulagée d'avoir fini l'examen.", "ex_en": "I'm relieved to have finished the exam."},
    # --- B1/B2: Opinions & discussion ---
    {"id": "op1", "cefr": "B1", "theme": "Les opinions", "fr": "à mon avis", "en": "in my opinion",
     "ex_fr": "À mon avis, ce film est excellent.", "ex_en": "In my opinion, this film is excellent."},
    {"id": "op2", "cefr": "B2", "theme": "Les opinions", "fr": "il me semble que", "en": "it seems to me that",
     "ex_fr": "Il me semble que la situation s'améliore.", "ex_en": "It seems to me that the situation is improving."},
    {"id": "op3", "cefr": "B2", "theme": "Les opinions", "fr": "d'une part... d'autre part", "en": "on one hand... on the other hand",
     "ex_fr": "D'une part c'est cher, d'autre part c'est de qualité.", "ex_en": "On one hand it's expensive, on the other it's quality."},
]


def vocab_for_level(cefr: str):
    idx = CEFR_ORDER.index(cefr) if cefr in CEFR_ORDER else 0
    allowed = set(CEFR_ORDER[: idx + 1])
    return [v for v in VOCAB if v["cefr"] in allowed]


def vocab_by_id(word_id: str):
    for v in VOCAB:
        if v["id"] == word_id:
            return v
    return None


# ---------------------------------------------------------------------------
# GRAMMAR TIPS (short "tip of the day" style notes)
# ---------------------------------------------------------------------------
GRAMMAR_TIPS = {
    "A1": [
        ("Avoir vs. être", "Beaucoup d'expressions utilisent AVOIR en français là où l'anglais utilise 'to be' : "
                            "j'ai faim (I am hungry), j'ai froid (I am cold), j'ai 25 ans (I am 25)."),
        ("Le genre des noms", "Chaque nom a un genre : masculin (le/un) ou féminin (la/une). "
                               "Ex : le café (m), la famille (f). Ça s'apprend petit à petit, pas de panique !"),
    ],
    "A2": [
        ("Le passé composé", "On forme le passé composé avec avoir/être + participe passé : "
                              "j'ai mangé, je suis allé(e). La plupart des verbes utilisent AVOIR."),
        ("Les verbes pronominaux", "Se réveiller, se coucher, s'habiller... on ajoute un pronom réfléchi : "
                                    "je me réveille, tu te réveilles, il/elle se réveille."),
    ],
    "B1": [
        ("Le subjonctif (intro)", "Après 'il faut que' ou 'je veux que', le verbe change de forme : "
                                   "il faut que tu FASSES tes devoirs (pas 'fais')."),
        ("Le français québécois", "Au Québec, on dit souvent 'magasiner' (faire du shopping) ou "
                                   "'un dépanneur' (convenience store) -- même langue, saveur différente !"),
    ],
    "B2": [
        ("Les nuances d'opinion", "Varier 'je pense que' avec 'il me semble que', 'à mon sens', "
                                   "'d'un point de vue personnel' rend le discours plus riche et nuancé."),
    ],
    "C1": [
        ("Registres de langue", "Le français a des registres très marqués : familier ('bouffer'), "
                                 "courant ('manger'), soutenu ('se restaurer'). Choisir le bon registre "
                                 "selon le contexte est une compétence avancée."),
    ],
}

# ---------------------------------------------------------------------------
# ROLE-PLAY SCENARIOS (branching dialogue trees)
# `setting` / `bot_role` / `min_turns` are used only in AI-driven mode
# (see tutor_engine.respond_roleplay_ai) -- the `nodes` tree below is the
# offline fallback used automatically when no API key is configured.
# ---------------------------------------------------------------------------
SCENARIOS = {
    "cafe": {
        "title": "Au café ☕",
        "cefr": "A1",
        "description": "Commandez un café (et un croissant !) dans un café parisien.",
        "setting": "Un petit café parisien animé, en fin de matinée.",
        "bot_role": "le serveur ou la serveuse du café -- amical(e) et patient(e)",
        "min_turns": 3,
        "start": "greet",
        "nodes": {
            "greet": {
                "bot_fr": "Bonjour ! Bienvenue au café. Qu'est-ce que je vous sers aujourd'hui ?",
                "bot_en": "Hello! Welcome to the café. What can I get you today?",
                "keywords": ["café", "the", "thé", "eau", "chocolat", "croissant", "jus"],
                "examples": ["Je voudrais un café, s'il vous plaît.", "Un thé, merci."],
                "next": "anything_else",
                "xp": 8,
            },
            "anything_else": {
                "bot_fr": "Très bien ! Et avec ça, un croissant ou une pâtisserie ?",
                "bot_en": "Great! And with that, a croissant or a pastry?",
                "keywords": ["croissant", "oui", "non", "pâtisserie", "merci", "pain"],
                "examples": ["Oui, un croissant, s'il vous plaît.", "Non merci, juste le café."],
                "next": "pay",
                "xp": 8,
            },
            "pay": {
                "bot_fr": "Parfait. Ça fait 4 euros 50. Vous payez comment -- carte ou espèces ?",
                "bot_en": "Perfect. That's 4.50 euros. How are you paying -- card or cash?",
                "keywords": ["carte", "espèces", "cash", "argent"],
                "examples": ["Par carte, s'il vous plaît.", "En espèces."],
                "next": "end",
                "xp": 8,
            },
            "end": {
                "bot_fr": "Merci beaucoup, et bonne journée ! ☕",
                "bot_en": "Thank you very much, and have a good day!",
                "keywords": [],
                "examples": [],
                "next": None,
                "xp": 12,
            },
        },
    },
    "directions": {
        "title": "Demander son chemin 🗺️",
        "cefr": "A2",
        "description": "Vous êtes perdu(e) dans le Vieux-Québec et demandez votre chemin.",
        "setting": "Une rue pavée du Vieux-Québec, un après-midi d'été.",
        "bot_role": "un(e) passant(e) sympathique du Vieux-Québec",
        "min_turns": 3,
        "start": "ask",
        "nodes": {
            "ask": {
                "bot_fr": "Excusez-moi, je peux vous aider ? Vous cherchez quelque chose ?",
                "bot_en": "Excuse me, can I help you? Are you looking for something?",
                "keywords": ["cherche", "gare", "musée", "hôtel", "château", "restaurant", "où"],
                "examples": ["Je cherche le Château Frontenac.", "Où est la gare, s'il vous plaît ?"],
                "next": "directions_given",
                "xp": 10,
            },
            "directions_given": {
                "bot_fr": "Ah, c'est facile ! Continuez tout droit, puis tournez à gauche après l'église.",
                "bot_en": "Ah, that's easy! Keep going straight, then turn left after the church.",
                "keywords": ["merci", "gauche", "droite", "compris", "tout droit"],
                "examples": ["Merci beaucoup, c'est très gentil.", "D'accord, tout droit puis à gauche."],
                "next": "end",
                "xp": 10,
            },
            "end": {
                "bot_fr": "De rien ! Bonne visite du Vieux-Québec ! 🏰",
                "bot_en": "You're welcome! Enjoy your visit to Old Quebec!",
                "keywords": [],
                "examples": [],
                "next": None,
                "xp": 12,
            },
        },
    },
    "market": {
        "title": "Au marché 🧺",
        "cefr": "A2",
        "description": "Achetez des fruits et légumes à un marché local.",
        "setting": "Un marché en plein air, un samedi matin.",
        "bot_role": "un marchand ou une marchande de fruits et légumes, chaleureux(se)",
        "min_turns": 3,
        "start": "browse",
        "nodes": {
            "browse": {
                "bot_fr": "Bonjour ! Nos pommes sont fraîches aujourd'hui. Vous en voulez ?",
                "bot_en": "Hello! Our apples are fresh today. Would you like some?",
                "keywords": ["pomme", "oui", "non", "combien", "kilo", "fraise", "légume"],
                "examples": ["Oui, un kilo de pommes, s'il vous plaît.", "Combien coûtent les fraises ?"],
                "next": "upsell",
                "xp": 8,
            },
            "upsell": {
                "bot_fr": "Bon choix ! Et pour accompagner, j'ai de belles carottes du Québec.",
                "bot_en": "Good choice! And to go with that, I have nice carrots from Quebec.",
                "keywords": ["carotte", "oui", "non", "merci", "légume"],
                "examples": ["Oui, ajoutez des carottes aussi.", "Non merci, ce sera tout."],
                "next": "end",
                "xp": 10,
            },
            "end": {
                "bot_fr": "Voilà, ça fait 6 dollars. Merci et bonne journée !",
                "bot_en": "Here you go, that's 6 dollars. Thanks and have a good day!",
                "keywords": [],
                "examples": [],
                "next": None,
                "xp": 12,
            },
        },
    },
    "meeting_friend": {
        "title": "Rencontrer un ami 👋",
        "cefr": "B1",
        "description": "Vous retrouvez un ami que vous n'avez pas vu depuis longtemps.",
        "setting": "Une terrasse de café, un an après vous être vus pour la dernière fois.",
        "bot_role": "un(e) vieil(le) ami(e), chaleureux(se) et curieux(se) de vos nouvelles",
        "min_turns": 3,
        "start": "greet",
        "nodes": {
            "greet": {
                "bot_fr": "Ça alors, ça fait longtemps ! Comment vas-tu ? Quoi de neuf ?",
                "bot_en": "Wow, it's been a while! How are you? What's new?",
                "keywords": ["bien", "ça va", "content", "nouvelle", "travail"],
                "examples": ["Ça va bien, merci ! Et toi ?", "Je suis content de te voir !"],
                "next": "catch_up",
                "xp": 12,
            },
            "catch_up": {
                "bot_fr": "Raconte-moi, qu'est-ce que tu as fait ces derniers mois ?",
                "bot_en": "Tell me, what have you been up to these last few months?",
                "keywords": ["voyagé", "travaillé", "étudié", "déménagé", "appris"],
                "examples": ["J'ai voyagé au Québec avec ma sœur.", "J'ai appris le français !"],
                "next": "end",
                "xp": 14,
            },
            "end": {
                "bot_fr": "C'est génial ! On devrait se revoir bientôt. À la prochaine !",
                "bot_en": "That's great! We should meet up again soon. Until next time!",
                "keywords": [],
                "examples": [],
                "next": None,
                "xp": 14,
            },
        },
    },
}

# ---------------------------------------------------------------------------
# COLLABORATIVE STORY MODE
# Only the first chapter is ever shown verbatim. In AI mode, Claude
# improvises everything after that based on your contributions; in offline
# mode, the fixed chapter sequence below is used throughout.
# ---------------------------------------------------------------------------
STORIES = {
    "mystere_quebec": {
        "title": "Le Mystère à Québec 🕵️",
        "cefr": "A2",
        "chapters": [
            {"fr": "Il est huit heures du soir dans le Vieux-Québec. Toi et ta sœur marchez près du "
                   "Château Frontenac quand vous remarquez une vieille clé dorée sur le trottoir.",
             "prompt": "Qu'est-ce que vous faites ? (Ramassez-vous la clé ? Cherchez-vous le propriétaire ?)"},
            {"fr": "Bonne idée ! Vous décidez d'explorer. Une petite porte en bois, cachée derrière un "
                   "café, semble correspondre à la clé. Une plaque indique : « Chocolaterie -- fermée depuis 1998 ».",
             "prompt": "Ouvrez-vous la porte avec la clé, ou frappez-vous d'abord ?"},
            {"fr": "La porte s'ouvre en grinçant. À l'intérieur, il y a une vieille recette de chocolat "
                   "chaud écrite à la main, et une carte du Québec avec un endroit marqué d'une croix rouge.",
             "prompt": "Décidez-vous de suivre la carte, ou de garder la recette et de partir ?"},
            {"fr": "Vous suivez la carte jusqu'à la cabane à sucre familiale à l'extérieur de la ville. "
                   "Le propriétaire, surpris, vous explique que la clé appartenait à sa grand-mère !",
             "prompt": "Que dites-vous au propriétaire ? Lui rendez-vous la clé ?"},
            {"fr": "Le propriétaire, ému, vous invite à goûter sa tire d'érable en remerciement. "
                   "Vous et votre sœur repartez avec une nouvelle histoire... et de nouveaux mots de "
                   "vocabulaire québécois ! Fin. 🍁",
             "prompt": None},
        ],
    },
    "voyage_provence": {
        "title": "Un Voyage en Provence 🌻",
        "cefr": "A1",
        "chapters": [
            {"fr": "Vous arrivez en Provence en été. Le soleil brille et il y a des champs de "
                   "lavande partout.",
             "prompt": "Qu'est-ce que vous voulez faire en premier : visiter un marché, ou se reposer à l'hôtel ?"},
            {"fr": "Au marché, il y a des fromages, des olives, et des fruits frais. Un vendeur "
                   "vous sourit et dit « Bonjour ! Vous voulez goûter ? »",
             "prompt": "Que répondez-vous au vendeur ?"},
            {"fr": "Vous goûtez un fromage délicieux et achetez un petit pot de miel de lavande.",
             "prompt": "Où allez-vous ensuite : à la plage, ou dans un petit village dans les collines ?"},
            {"fr": "Le village est magnifique, avec des rues pavées et des fleurs partout. "
                   "Vous prenez beaucoup de photos avec votre sœur.",
             "prompt": None},
        ],
    },
}


def get_story_chapter(story_id: str, index: int):
    story = STORIES[story_id]
    if index < len(story["chapters"]):
        return story["chapters"][index]
    return None


# ---------------------------------------------------------------------------
# QUESTS
# ---------------------------------------------------------------------------
QUESTS_DAILY = [
    {"id": "d1", "title": "Dis bonjour !", "desc": "Envoie 5 messages au tuteur en français aujourd'hui.",
     "type": "chat_count", "target": 5, "xp": 20, "coins": 5},
    {"id": "d2", "title": "Décris ta journée", "desc": "Écris 10 phrases sur ta journée dans le chat.",
     "type": "chat_count", "target": 10, "xp": 30, "coins": 8},
    {"id": "d3", "title": "Café du matin", "desc": "Termine le jeu de rôle « Au café ».",
     "type": "scenario", "target": "cafe", "xp": 25, "coins": 6},
    {"id": "d4", "title": "Révision éclair", "desc": "Révise 10 cartes de vocabulaire.",
     "type": "vocab_review", "target": 10, "xp": 20, "coins": 5},
    {"id": "d5", "title": "Suite de l'histoire", "desc": "Continue un chapitre du mode Histoire.",
     "type": "story", "target": 1, "xp": 25, "coins": 6},
]

QUESTS_WEEKLY = [
    {"id": "w1", "title": "Semaine d'immersion", "desc": "Pratique 5 jours cette semaine (streak).",
     "type": "active_days", "target": 5, "xp": 100, "coins": 25},
    {"id": "w2", "title": "Explorateur du Québec", "desc": "Apprends les 4 mots de vocabulaire du thème Québec.",
     "type": "vocab_theme", "target": 4, "xp": 90, "coins": 20},
    {"id": "w3", "title": "Maître des dialogues", "desc": "Termine 3 jeux de rôle différents.",
     "type": "scenario_count", "target": 3, "xp": 110, "coins": 25},
]

JOINT_QUESTS = [
    {"id": "j1", "title": "Défi fraternel : Jeu de rôle", "desc": "Vous devez chacun terminer un jeu de rôle cette semaine.",
     "type": "both_scenario", "xp": 60, "coins": 15},
    {"id": "j2", "title": "Défi fraternel : Histoire commune", "desc": "Vous devez chacun avancer dans le mode Histoire cette semaine.",
     "type": "both_story", "xp": 60, "coins": 15},
    {"id": "j3", "title": "Défi fraternel : 7 jours ensemble", "desc": "Obtenez chacun une série (streak) d'au moins 7 jours.",
     "type": "both_streak7", "xp": 150, "coins": 40},
]


# ---------------------------------------------------------------------------
# BADGES (id, name, emoji, description) -- logic lives in gamification.py
# ---------------------------------------------------------------------------
BADGES = [
    {"id": "first_message", "name": "Premier Pas", "emoji": "👣", "desc": "Envoie ton premier message en français."},
    {"id": "streak_3", "name": "Élan", "emoji": "🔥", "desc": "Atteins une série de 3 jours."},
    {"id": "streak_7", "name": "Streak Master", "emoji": "🔥🔥", "desc": "Atteins une série de 7 jours."},
    {"id": "streak_30", "name": "Immersion Totale", "emoji": "🔥🔥🔥", "desc": "Atteins une série de 30 jours."},
    {"id": "first_hour", "name": "First Immersion Hour", "emoji": "⏳", "desc": "Envoie 60 messages au total."},
    {"id": "quebec_explorer", "name": "Quebec Explorer", "emoji": "🍁", "desc": "Apprends tous les mots du thème Québec."},
    {"id": "cafe_master", "name": "Habitué du Café", "emoji": "☕", "desc": "Termine le jeu de rôle 'Au café'."},
    {"id": "scenario_5", "name": "Acteur", "emoji": "🎭", "desc": "Termine toutes les scènes de jeu de rôle disponibles."},
    {"id": "storyteller", "name": "Conteur", "emoji": "📖", "desc": "Termine une histoire complète."},
    {"id": "vocab_50", "name": "Collectionneur de Mots", "emoji": "🧠", "desc": "Apprends 20 mots de vocabulaire."},
    {"id": "vocab_100", "name": "Polyglotte en Herbe", "emoji": "📚", "desc": "Apprends 30 mots de vocabulaire."},
    {"id": "team_player", "name": "Esprit d'Équipe", "emoji": "🤝", "desc": "Termine un défi fraternel avec ta sœur/ton frère."},
    {"id": "level_5", "name": "Niveau 5", "emoji": "⭐", "desc": "Atteins le niveau de jeu 5."},
    {"id": "level_10", "name": "Niveau 10", "emoji": "🌟", "desc": "Atteins le niveau de jeu 10."},
    {"id": "corrector", "name": "Apprenti Grammairien", "emoji": "✏️", "desc": "Reçois 20 corrections amicales -- l'erreur fait partie de l'apprentissage !"},
]
