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
     "In French, you use AVOIR (to have) for age, not ÊTRE (to be): you say « j'ai 20 ans » -- "
     "literally \"I have 20 years\" -- even though that sounds odd in English!"),
    (r"\bje suis faim\b",
     "j'ai faim",
     "For hunger too, French uses AVOIR: « j'ai faim » (literally \"I have hunger\")."),
    (r"\bje suis soif\b",
     "j'ai soif",
     "Same for thirst: « j'ai soif », not « je suis soif »."),
    (r"\bje suis chaud\b",
     "j'ai chaud",
     "Careful: « je suis chaud » has a different meaning in casual French! To talk about "
     "feeling hot, say « j'ai chaud » (I am hot / I feel hot)."),
    (r"\bje suis froid\b",
     "j'ai froid",
     "To say you're cold, it's « j'ai froid », with AVOIR, not ÊTRE."),
    (r"\bun fille\b",
     "une fille",
     "« Fille » is feminine, so it's « UNE fille », not « un fille »."),
    (r"\bune garçon\b",
     "un garçon",
     "« Garçon » is masculine, so it's « UN garçon », not « une garçon »."),
    (r"\bje veux que je\b",
     "je veux (+ infinitive)",
     "When the subject is the same in both parts, you don't use 'que': « je veux "
     "partir », not « je veux que je parte »."),
    (r"\bactuellement\b",
     "actuellement = 'currently' (not 'actually')",
     "Classic false friend! « Actuellement » means 'currently', not 'actually'. For "
     "'actually', use « en fait » instead."),
    (r"\bje suis excité\b",
     "j'ai hâte / je suis enthousiaste",
     "« Je suis excité » can sound ambiguous in French. For enthusiasm, prefer « j'ai "
     "hâte » (I can't wait) or « je suis enthousiaste »."),
    (r"\bbeaucoup de le\b",
     "beaucoup du",
     "'de' + 'le' always contracts to 'du': « beaucoup DU café », not « beaucoup DE LE café »."),
    (r"\bje suis d'accord que\b",
     "je suis d'accord (avec ça) / je pense que",
     "« Je suis d'accord » is often used alone or with 'avec': « je suis d'accord avec toi »."),
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
