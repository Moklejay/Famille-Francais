"""
tutor_engine.py
----------------
Conversation logic for the tutor, the role-play scenarios, and story mode.

When a Claude API key is configured (see core/ai_client.py), every
function here talks to the real model for genuinely adaptive French
conversation, in-character improv, and collaborative storytelling. When no
key is configured (or a call fails), it falls back to a rule-based /
scripted offline engine so the app still works instantly, for free.

Either way, the pedagogical framing is the same:
  * i+1 targeting (Krashen): stay one small notch above the learner's
    CEFR level -- understandable with a little effort, never overwhelming.
  * Contextual embedding: emoji "gestures" and short English hints give
    context clues instead of translating everything outright.
  * Low-anxiety interaction: mistakes are corrected gently and separately
    from the conversational flow, never mid-reply.
"""

from __future__ import annotations
import random
import re
from core import corrections, ai_client

CEFR_FALLBACK_ORDER = ["A1", "A2", "B1", "B2", "C1"]

CEFR_DESCRIPTIONS = {
    "A1": "grand débutant -- phrases très courtes et simples, vocabulaire de base uniquement",
    "A2": "débutant -- phrases simples, temps présent et passé composé, vocabulaire courant",
    "B1": "intermédiaire -- phrases plus riches, plusieurs temps, sujets variés du quotidien",
    "B2": "intermédiaire avancé -- nuances, opinions, sujets abstraits, registre plus naturel",
    "C1": "avancé -- langue proche du natif, nuances fines, registres de langue variés",
}


def _cefr_desc(cefr: str) -> str:
    return CEFR_DESCRIPTIONS.get(cefr, CEFR_DESCRIPTIONS["A1"])


# ===========================================================================
# AI-DRIVEN MODE (used automatically when ai_client.is_configured())
# ===========================================================================

CHAT_SYSTEM_PROMPT = """Tu es un tuteur de français chaleureux, patient et encourageant pour {name}, \
qui pratique le français au quotidien avec son frère/sa sœur dans le cadre d'un rituel d'immersion. \
{name} est actuellement au niveau {cefr} du CECR ({cefr_desc}).

RÈGLES STRICTES :
1. Réponds TOUJOURS uniquement en français, calibré précisément au niveau {cefr} (théorie de \
l'input compréhensible de Krashen : reste à "i+1", un tout petit peu au-dessus du niveau maîtrisé, \
jamais un saut trop grand).
2. Sois chaleureux et positif -- jamais intimidant. Célèbre les tentatives, même imparfaites.
3. Si {name} écrit en anglais ou est bloqué(e), encourage-le/la gentiment à essayer en français, \
avec un exemple concret de début de phrase, plutôt que de traduire tout.
4. Fais vivre une vraie conversation : pose des questions ouvertes, rebondis sur ce que {name} dit, \
propose parfois des mini-scénarios de la vie quotidienne ou de la culture francophone (France, \
Québec, Canada français).
5. Si {name} fait une erreur de grammaire, de genre, de conjugaison ou de vocabulaire, ne la corrige \
JAMAIS dans le texte de ta réponse -- note-la séparément dans le champ "corrections" du JSON, avec \
bienveillance, une suggestion, et une explication brève et claire.
6. N'aborde jamais de sujets sensibles ou difficiles à moins que {name} ne les amène en premier.
7. Ne répète pas la même question ou structure de phrase que dans tes 2-3 derniers messages.

Réponds STRICTEMENT avec un objet JSON valide, sans aucun texte avant ou après, exactement dans ce format :
{{"reply_fr": "ta réponse en français", "hint_en": "résumé anglais très court, UNIQUEMENT si niveau A1 \
et phrase potentiellement difficile, sinon null", "corrections": [{{"original": "...", "suggestion": "...", \
"explanation": "..."}}], "new_vocab": [{{"fr": "...", "en": "..."}}]}}"""


def respond_ai(user_text: str, cefr: str, name: str, history: list) -> dict:
    """
    Real, adaptive conversation via the Claude API. `history` is a list of
    {"role": "user"/"assistant", "content": str} for the last few turns
    (plain text only -- no metadata) so the model has conversational context.
    Raises RuntimeError if the API isn't configured or the call fails --
    callers should catch this and fall back to respond_rulebased().
    """
    system_prompt = CHAT_SYSTEM_PROMPT.format(name=name, cefr=cefr, cefr_desc=_cefr_desc(cefr))
    messages = history[-12:] + [{"role": "user", "content": user_text}]
    result = ai_client.chat_json(system_prompt, messages)

    corrections_list = [
        {"matched": c.get("original", ""), "suggestion": c.get("suggestion", ""), "explanation": c.get("explanation", "")}
        for c in (result.get("corrections") or [])
    ]
    return {
        "reply": result.get("reply_fr", "Désolé, je n'ai pas de réponse -- réessaie !"),
        "hint_en": result.get("hint_en"),
        "corrections": corrections_list,
        "new_vocab": result.get("new_vocab") or [],
        "matched_intent": "ai",
        "source": "ai",
    }


ROLEPLAY_SYSTEM_PROMPT = """Tu incarnes un personnage dans un jeu de rôle immersif en français pour {name} \
(niveau {cefr} du CECR -- {cefr_desc}). Tu joues : {bot_role}. Contexte de la scène : {setting}.

RÈGLES :
1. Reste TOUJOURS dans le personnage. Réponds uniquement en français, calibré au niveau {cefr}.
2. Fais avancer la scène de façon naturelle et réaliste, en réagissant vraiment à ce que {name} dit.
3. Sois chaleureux et patient. Si {name} est bloqué(e) ou répond en anglais, reste dans le personnage \
mais simplifie ta phrase et propose un exemple de réponse possible.
4. Note les erreurs de grammaire/vocabulaire séparément dans "corrections" (jamais dans ta réplique), \
avec bienveillance.
5. Après au moins {min_turns} échanges, quand la scène arrive à une conclusion naturelle (ex : la \
commande est passée, le chemin est expliqué, les adieux sont dits), termine la scène avec une réplique \
de conclusion et mets "scene_ended": true. Sinon "scene_ended": false.

Réponds STRICTEMENT en JSON valide, sans texte avant/après :
{{"reply_fr": "...", "hint_en": "résumé anglais très court si niveau A1, sinon null", \
"corrections": [{{"original": "...", "suggestion": "...", "explanation": "..."}}], "scene_ended": false}}"""


def respond_roleplay_ai(scenario: dict, user_text: str, cefr: str, name: str, history: list) -> dict:
    """
    AI-driven improv for a single role-play scenario. `scenario` is one of
    the dicts in content_bank.SCENARIOS (needs setting/bot_role/min_turns).
    Raises RuntimeError on failure -- caller falls back to the scripted
    dialogue tree.
    """
    system_prompt = ROLEPLAY_SYSTEM_PROMPT.format(
        name=name, cefr=cefr, cefr_desc=_cefr_desc(cefr),
        bot_role=scenario["bot_role"], setting=scenario["setting"], min_turns=scenario["min_turns"],
    )
    messages = history[-12:] + [{"role": "user", "content": user_text}]
    result = ai_client.chat_json(system_prompt, messages)
    corrections_list = [
        {"matched": c.get("original", ""), "suggestion": c.get("suggestion", ""), "explanation": c.get("explanation", "")}
        for c in (result.get("corrections") or [])
    ]
    return {
        "reply": result.get("reply_fr", "..."),
        "hint_en": result.get("hint_en"),
        "corrections": corrections_list,
        "scene_ended": bool(result.get("scene_ended")),
    }


STORY_SYSTEM_PROMPT = """Tu es le narrateur ou la narratrice d'une histoire interactive en français pour \
{name} (niveau {cefr} CECR -- {cefr_desc}), qui l'écrit avec son frère/sa sœur.

Histoire : {story_title}. Voici ce qui s'est passé jusqu'ici :
{story_so_far}

{name} vient d'écrire ceci pour décider de la suite : "{contribution}"

Intègre son idée de façon créative et cohérente, puis continue l'histoire avec un court paragraphe \
(3 à 5 phrases) en français calibré au niveau {cefr}. Termine par une question ouverte qui invite la \
suite -- SAUF si l'histoire est arrivée à une fin naturelle et satisfaisante (après plusieurs \
chapitres), auquel cas conclus l'histoire et mets "story_ended": true, "prompt_fr": null.

Réponds STRICTEMENT en JSON valide, sans texte avant/après :
{{"paragraph_fr": "...", "prompt_fr": "... ou null", \
"corrections": [{{"original": "...", "suggestion": "...", "explanation": "..."}}], "story_ended": false}}"""


def respond_story_ai(story_title: str, story_so_far: str, contribution: str, cefr: str, name: str) -> dict:
    """AI-driven continuation of a collaborative story. Raises RuntimeError on failure."""
    system_prompt = STORY_SYSTEM_PROMPT.format(
        name=name, cefr=cefr, cefr_desc=_cefr_desc(cefr),
        story_title=story_title, story_so_far=story_so_far[-4000:], contribution=contribution,
    )
    result = ai_client.chat_json(system_prompt, [{"role": "user", "content": contribution}])
    corrections_list = [
        {"matched": c.get("original", ""), "suggestion": c.get("suggestion", ""), "explanation": c.get("explanation", "")}
        for c in (result.get("corrections") or [])
    ]
    return {
        "paragraph": result.get("paragraph_fr", "..."),
        "prompt": result.get("prompt_fr"),
        "corrections": corrections_list,
        "story_ended": bool(result.get("story_ended")),
    }


# ===========================================================================
# OFFLINE RULE-BASED FALLBACK (used automatically when no API key is set,
# or if an AI call fails for any reason)
# ===========================================================================

INTENTS = [
    {
        "id": "greeting",
        "keywords": [r"\bbonjour\b", r"\bsalut\b", r"\ballo\b", r"\bcoucou\b", r"^hi\b", r"^hello\b"],
        "responses": {
            "A1": ["Bonjour ! 😊 Ça va bien aujourd'hui ?", "Salut ! Comment ça va ?"],
            "A2": ["Salut ! Content(e) de te parler aujourd'hui. Quoi de neuf ?", "Bonjour ! Comment s'est passée ta journée ?"],
            "B1": ["Salut toi ! Alors, qu'est-ce qui t'occupe en ce moment ?", "Bonjour ! Raconte-moi un peu ta semaine."],
            "B2": ["Hé, ça fait plaisir de discuter ! Qu'est-ce qui t'amène aujourd'hui ?"],
        },
    },
    {
        "id": "how_are_you",
        "keywords": [r"comment ça va", r"comment vas[- ]tu", r"comment allez[- ]vous", r"\bça va\b\??$"],
        "responses": {
            "A1": ["Ça va très bien, merci ! Et toi, ça va ? 😊", "Je vais bien ! Et toi, comment tu te sens ?"],
            "A2": ["Ça va super bien aujourd'hui ! Et toi, comment se passe ta journée ?"],
            "B1": ["Je me sens plutôt en forme aujourd'hui, merci de demander ! Et de ton côté ?"],
            "B2": ["Franchement, je suis d'excellente humeur ! Et toi, quel est ton état d'esprit du jour ?"],
        },
    },
    {
        "id": "weather",
        "keywords": [r"météo", r"temps qu'il fait", r"il fait (beau|froid|chaud|mauvais)", r"\bneige\b", r"\bpleut\b"],
        "responses": {
            "A1": ["Ici, j'imagine qu'il fait beau ! ☀️ Et chez toi, quel temps fait-il ?"],
            "A2": ["La météo change vite en automne, non ? Il fait quel temps chez toi aujourd'hui ?"],
            "B1": ["Le temps a une grande influence sur l'humeur, tu ne trouves pas ? Quel temps préfères-tu ?"],
            "B2": ["Entre nous, je préfère les journées ensoleillées d'automne. Et toi, quelle saison te correspond le mieux ?"],
        },
    },
    {
        "id": "food",
        "keywords": [r"manger", r"nourriture", r"repas", r"déjeuner", r"dîner", r"souper", r"cuisine", r"plat"],
        "responses": {
            "A1": ["Miam ! 🍽️ Qu'est-ce que tu aimes manger le plus ?", "J'adore parler de nourriture ! Ton plat préféré, c'est quoi ?"],
            "A2": ["La cuisine, c'est un excellent sujet ! Qu'est-ce que tu as mangé aujourd'hui ?"],
            "B1": ["La gastronomie française et québécoise sont si différentes et délicieuses. Tu préfères laquelle ?"],
            "B2": ["Le rapport à la nourriture varie beaucoup selon les cultures. Quelle tradition culinaire t'intrigue le plus ?"],
        },
    },
    {
        "id": "family",
        "keywords": [r"\bsœur\b", r"\bfrère\b", r"\bfamille\b", r"\bparents\b"],
        "responses": {
            "A1": ["La famille, c'est important ! 👨‍👩‍👧 Tu es proche de ta sœur ?", "J'aime bien ce sujet ! Parle-moi de ta famille."],
            "A2": ["C'est chouette d'apprendre le français avec ta sœur ! Vous faites ça comment, ensemble ?"],
            "B1": ["Apprendre une langue à deux, ça motive beaucoup plus. Qu'est-ce que vous aimez faire ensemble ?"],
            "B2": ["Les liens familiaux jouent souvent un grand rôle dans la motivation à apprendre. Qu'en penses-tu ?"],
        },
    },
    {
        "id": "quebec_culture",
        "keywords": [r"québec", r"montréal", r"canada", r"cabane à sucre", r"érable", r"dépanneur"],
        "responses": {
            "A1": ["Le Québec, c'est magnifique ! ❄️🍁 Tu connais la cabane à sucre ?"],
            "A2": ["Le français québécois a des mots uniques, comme « magasiner » ou « dépanneur ». Tu en connais d'autres ?"],
            "B1": ["Le Québec a une culture francophone riche, très différente de la France. Qu'est-ce qui t'intéresse le plus là-dedans ?"],
            "B2": ["L'histoire et l'identité culturelle du Québec sont fascinantes. As-tu déjà visité, ou c'est un projet ?"],
        },
    },
    {
        "id": "weekend_plans",
        "keywords": [r"week[- ]?end", r"projet", r"prévois", r"vas faire"],
        "responses": {
            "A1": ["Le week-end, qu'est-ce que tu aimes faire ? 🎉"],
            "A2": ["Tu as des projets pour ce week-end ? Raconte-moi !"],
            "B1": ["Qu'est-ce qui te ferait plaisir de faire ce week-end, si tu avais du temps libre ?"],
            "B2": ["Comment envisages-tu de passer ton temps libre prochainement ?"],
        },
    },
    {
        "id": "thanks_bye",
        "keywords": [r"\bmerci\b", r"au revoir", r"à bientôt", r"à plus", r"\bbye\b"],
        "responses": {
            "A1": ["Avec plaisir ! 😊 À bientôt !", "De rien ! On continue plus tard ?"],
            "A2": ["Ce fut un plaisir de discuter avec toi ! À la prochaine."],
            "B1": ["Merci à toi pour cette belle conversation, à très vite !"],
            "B2": ["Ce fut un plaisir d'échanger avec toi, à bientôt pour la suite !"],
        },
    },
    {
        "id": "confused",
        "keywords": [r"je ne comprends pas", r"je comprends pas", r"comprends? pas", r"\?\?\?", r"quoi\b\??$"],
        "responses": {
            "A1": ["Pas de souci ! 🙂 Je répète plus simplement : comment tu te sens aujourd'hui -- bien, fatigué(e), content(e) ?"],
            "A2": ["Pas de problème, on ralentit. Dis-moi juste un mot : content(e), fatigué(e), ou curieux(se) ?"],
            "B1": ["Aucun souci, je reformule : qu'est-ce qui t'intéresse en ce moment, dans ta vie ou tes études ?"],
        },
    },
]

# Open-ended prompts to keep the conversation flowing when nothing matches --
# rotated so the same one doesn't repeat back-to-back.
FALLBACK_PROMPTS = {
    "A1": [
        "Raconte-moi ta journée en 2 ou 3 phrases ! 📝",
        "Quel est ton animal préféré ? 🐶🐱",
        "Qu'est-ce que tu as mangé ce matin ?",
        "Il fait quel temps chez toi aujourd'hui ?",
        "Tu préfères le café ou le thé ?",
    ],
    "A2": [
        "Qu'est-ce que tu as fait ce week-end dernier ?",
        "Décris-moi ta ville en quelques phrases.",
        "Quel est ton souvenir de vacances préféré ?",
        "Qu'est-ce que tu aimes faire après le travail ou l'école ?",
    ],
    "B1": [
        "Si tu pouvais visiter n'importe quel endroit francophone, ce serait où et pourquoi ?",
        "Quelle est une habitude que tu aimerais changer cette année ?",
        "Parle-moi d'un film ou d'un livre que tu as aimé récemment.",
    ],
    "B2": [
        "Quel sujet d'actualité t'intéresse en ce moment, et pourquoi ?",
        "Selon toi, qu'est-ce qui rend l'apprentissage d'une langue vraiment efficace ?",
    ],
    "C1": [
        "Quelle nuance culturelle entre le français de France et le français québécois trouves-tu la plus intéressante ?",
        "Comment décrirais-tu ta relation avec l'apprentissage des langues, avec le recul ?",
    ],
}

# A "looks like English, not French" heuristic -- common English function
# words that essentially never appear standalone in real French text. Any
# single hit is already a strong signal (these words just don't show up in
# French sentences), so unlike a "majority vote" approach we don't require
# multiple hits before flagging a short-to-medium message as English.
_ENGLISH_MARKERS = re.compile(
    r"\b(the|is|are|you|and|what|how|i'm|im|dont|don't|with|have|has|was|were|this|that|"
    r"am|want|need|really|would|should|please|yes)\b",
    re.IGNORECASE,
)


def _closest_level(levels_dict: dict, cefr: str) -> str:
    if cefr in levels_dict:
        return cefr
    idx = CEFR_FALLBACK_ORDER.index(cefr) if cefr in CEFR_FALLBACK_ORDER else 0
    for lvl in reversed(CEFR_FALLBACK_ORDER[: idx + 1]):
        if lvl in levels_dict:
            return lvl
    return next(iter(levels_dict))


def _looks_english(text: str) -> bool:
    return bool(_ENGLISH_MARKERS.search(text))


def respond_rulebased(user_text: str, cefr: str, last_prompt: str | None = None) -> dict:
    """
    Offline, rule-based fallback (see module docstring). Used automatically
    when no Claude API key is configured, or if an AI call fails.

    Returns:
        {
          "reply": str,               # French reply
          "hint_en": str | None,      # optional English gist, for A1 learners
          "corrections": [ ... ],     # from corrections.check()
          "matched_intent": str | None,
        }
    """
    text = user_text.strip()
    found_corrections = corrections.check(text)

    if _looks_english(text) and len(text.split()) > 2:
        reply = ("Essaie de répondre en français, même simplement -- c'est comme ça qu'on progresse ! 💪 "
                 "Par exemple, tu peux commencer par « Je pense que... » ou « Aujourd'hui, je... ».")
        return {"reply": reply, "hint_en": "Try answering in French, even simply -- that's how we improve!",
                "corrections": found_corrections, "matched_intent": "encourage_french", "source": "rulebased"}

    for intent in INTENTS:
        for pattern in intent["keywords"]:
            if re.search(pattern, text, re.IGNORECASE):
                level = _closest_level(intent["responses"], cefr)
                options = intent["responses"][level]
                reply = random.choice(options)
                return {"reply": reply, "hint_en": None, "corrections": found_corrections,
                        "matched_intent": intent["id"], "source": "rulebased"}

    # No intent matched -- comprehensible-input fallback: keep it going with
    # an open question at the right level, avoiding immediate repetition.
    level = cefr if cefr in FALLBACK_PROMPTS else _closest_level(FALLBACK_PROMPTS, cefr)
    options = [p for p in FALLBACK_PROMPTS[level] if p != last_prompt] or FALLBACK_PROMPTS[level]
    reply = random.choice(options)
    return {"reply": reply, "hint_en": None, "corrections": found_corrections, "matched_intent": None, "source": "rulebased"}


def respond(user_text: str, cefr: str, name: str = "toi", history: list | None = None,
            last_prompt: str | None = None) -> dict:
    """
    Top-level dispatcher used by the Chat page: tries real AI first (if a
    Claude API key is configured), and transparently falls back to the
    offline rule-based engine if no key is set or the call fails for any
    reason (offline, bad key, rate limit, etc.) so the app never breaks.
    """
    if ai_client.is_configured():
        try:
            return respond_ai(user_text, cefr, name, history or [])
        except RuntimeError as e:
            fallback = respond_rulebased(user_text, cefr, last_prompt)
            fallback["ai_error"] = str(e)
            return fallback
    return respond_rulebased(user_text, cefr, last_prompt)


def opening_line(cefr: str, name: str) -> str:
    lines = {
        "A1": f"Bonjour {name} ! 😊 Je suis ton tuteur de français. On commence en douceur -- comment tu te sens aujourd'hui ?",
        "A2": f"Salut {name} ! Prêt(e) à pratiquer un peu de français ? Raconte-moi comment s'est passée ta journée.",
        "B1": f"Bonjour {name} ! J'ai hâte de discuter avec toi aujourd'hui. Qu'est-ce qui t'occupe l'esprit en ce moment ?",
        "B2": f"Salut {name} ! On approfondit la conversation aujourd'hui -- quel sujet te tient à cœur en ce moment ?",
        "C1": f"Bonjour {name}, ravi de reprendre notre échange. De quoi as-tu envie de discuter aujourd'hui ?",
    }
    return lines.get(cefr, lines["A1"])
