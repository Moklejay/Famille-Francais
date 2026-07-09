"""
srs.py
-------
A lightweight SM-2-style spaced repetition scheduler for vocabulary review.
This is the "active recall + spaced repetition" pillar of the app: words
you know well surface less often; shaky words come back sooner.
"""

from __future__ import annotations
from datetime import date, timedelta
from core import content_bank as cb

# Card state: {"interval": days, "ease": float, "due": iso-date, "reps": int}


def _new_card() -> dict:
    return {"interval": 0, "ease": 2.5, "due": date.today().isoformat(), "reps": 0}


def due_cards(profile: dict, limit: int = 15) -> list:
    """Return vocab dicts that are due today (or new), capped at `limit`, from words unlocked at the user's CEFR level."""
    today = date.today().isoformat()
    unlocked = {v["id"]: v for v in cb.vocab_for_level(profile["level"])}

    due, new = [], []
    for word_id, word in unlocked.items():
        card = profile["vocab_srs"].get(word_id)
        if card is None:
            new.append(word)
        elif card["due"] <= today:
            due.append(word)

    # Prioritize overdue review, then fill remaining slots with new words
    result = due[:limit]
    if len(result) < limit:
        result += new[: limit - len(result)]
    return result


def grade_card(profile: dict, word_id: str, quality: int) -> dict:
    """
    quality: 0 (again/forgot) - 3 (hard) - 4 (good) - 5 (easy), SM-2 style.
    Updates the card and returns it.
    """
    card = profile["vocab_srs"].get(word_id, _new_card())

    if quality < 3:
        card["reps"] = 0
        card["interval"] = 1
    else:
        card["reps"] += 1
        if card["reps"] == 1:
            card["interval"] = 1
        elif card["reps"] == 2:
            card["interval"] = 3
        else:
            card["interval"] = round(card["interval"] * card["ease"])
        card["ease"] = max(1.3, card["ease"] + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

    card["due"] = (date.today() + timedelta(days=card["interval"])).isoformat()
    profile["vocab_srs"][word_id] = card

    # A word counts as "mastered" the first time it's ever passed (quality
    # >= 3), no matter how many attempts it took to get there. This is
    # tracked in its own list (separate from vocab_srs, which every word
    # enters on its very first grading regardless of pass/fail) so that a
    # word you initially got wrong still earns credit once you actually
    # learn it -- previously, only a correct FIRST attempt ever counted,
    # silently undercounting everyone's real progress and making the
    # vocab_50/vocab_100 badges harder to earn than intended.
    known_ids = profile.setdefault("vocab_known_ids", [])
    if quality >= 3 and word_id not in known_ids:
        known_ids.append(word_id)
        profile["vocab_known_count"] += 1

    return card
