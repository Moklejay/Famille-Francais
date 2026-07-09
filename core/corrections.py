"""
corrections.py
----------------
Lightweight, rule-based detection of common beginner English->French
transfer mistakes. This is NOT a full grammar checker -- it's a curated
list of the highest-value patterns for English speakers learning French,
each with a warm, encouraging explanation (never just "wrong").

Add your own patterns as you spot recurring mistakes -- see README.
"""

from __future__ import annotations
import re

# Each entry: (regex pattern (case-insensitive), corrected example, explanation)
PATTERNS = [
    (r"\bje suis (\d{1,3}) ans\b",
     "j'ai {0} ans",
     "En français, on utilise AVOIR pour l'âge, pas ÊTRE : on dit « j'ai 20 ans », comme "
     "« I have 20 years », même si ça sonne bizarre en anglais !"),
    (r"\bje suis faim\b",
     "j'ai faim",
     "Pour la faim, on utilise aussi AVOIR : « j'ai faim » (littéralement 'I have hunger')."),
    (r"\bje suis soif\b",
     "j'ai soif",
     "Même chose pour la soif : « j'ai soif », pas « je suis soif »."),
    (r"\bje suis chaud\b",
     "j'ai chaud",
     "Attention : « je suis chaud » a un sens différent en français familier ! Pour parler de "
     "la température qu'on ressent, dis « j'ai chaud » (I am hot / I feel hot)."),
    (r"\bje suis froid\b",
     "j'ai froid",
     "Pour dire qu'on a froid, on dit « j'ai froid », avec AVOIR, pas ÊTRE."),
    (r"\bun fille\b",
     "une fille",
     "« Fille » est féminin, donc on dit « UNE fille », pas « un fille »."),
    (r"\bune garçon\b",
     "un garçon",
     "« Garçon » est masculin, donc on dit « UN garçon », pas « une garçon »."),
    (r"\bje veux que je\b",
     "je veux (+ infinitif)",
     "Quand le sujet est le même dans les deux parties, on n'utilise pas 'que' : « je veux "
     "partir », pas « je veux que je parte »."),
    (r"\bactuellement\b",
     "actuellement = 'currently' (pas 'actually')",
     "Faux ami classique ! « Actuellement » veut dire 'currently', pas 'actually'. Pour "
     "'actually', dis plutôt « en fait »."),
    (r"\bje suis excité\b",
     "j'ai hâte / je suis enthousiaste",
     "« Je suis excité » peut sonner ambigu en français. Pour l'enthousiasme, préfère « j'ai "
     "hâte » (I can't wait) ou « je suis enthousiaste »."),
    (r"\bbeaucoup de le\b",
     "beaucoup du",
     "'de' + 'le' se contracte toujours en 'du' : « beaucoup DU café », pas « beaucoup DE LE café »."),
    (r"\bje suis d'accord que\b",
     "je suis d'accord (avec ça) / je pense que",
     "« Je suis d'accord » s'utilise souvent seul ou avec 'avec' : « je suis d'accord avec toi »."),
]

_COMPILED = [(re.compile(p, re.IGNORECASE), fix, why) for p, fix, why in PATTERNS]


def check(text: str):
    """
    Scan `text` for known mistake patterns. Returns a list of dicts:
    {matched, suggestion, explanation} -- empty list if nothing found.
    Corrections are meant to be shown AFTER the bot's reply, framed
    positively (see tutor_engine.respond).
    """
    found = []
    for pattern, fix, why in _COMPILED:
        m = pattern.search(text)
        if m:
            try:
                suggestion = fix.format(*m.groups())
            except (IndexError, KeyError):
                suggestion = fix
            found.append({"matched": m.group(0), "suggestion": suggestion, "explanation": why})
    return found
