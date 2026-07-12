"""
gamification.py
-----------------
XP, game levels, streak bonuses, badges, and quest rotation.
Duolingo + Spotify Fusion Design
"""

from __future__ import annotations
from datetime import date
from core import content_bank as cb
from core import storage


def award_xp(profile: dict, amount: int, activity: str) -> dict:
    """Add XP/coins, log history, and return info about any level-up."""
    old_level = compute_level(profile["xp"])
    profile["xp"] += amount
    profile["coins"] += max(1, amount // 3)
    storage.log_history(profile, activity, amount)
    new_level = compute_level(profile["xp"])
    result = {
        "leveled_up": new_level > old_level,
        "old_level": old_level,
        "new_level": new_level,
        "unlock": cb.LEVEL_UNLOCKS.get(new_level)
    }
    return result


def compute_level(xp: int) -> int:
    level = 1
    for lvl, threshold in cb.GAME_LEVELS:
        if xp >= threshold:
            level = lvl
        else:
            break
    return level


def xp_to_next_level(xp: int):
    level = compute_level(xp)
    thresholds = dict(cb.GAME_LEVELS)
    next_level = level + 1
    if next_level not in thresholds:
        return None, None, 1.0  # maxed out
    current_floor = thresholds[level]
    next_ceiling = thresholds[next_level]
    progress = (xp - current_floor) / max(1, (next_ceiling - current_floor))
    return next_level, next_ceiling - xp, min(1.0, max(0.0, progress))


def record_daily_login(profile: dict) -> int:
    """Call once per page-load/session. Returns streak-milestone bonus XP."""
    before = profile["streak"]["last_active_date"]
    bonus = storage.touch_daily_activity(profile)
    after = profile["streak"]["last_active_date"]
    if after != before:
        bump_quest_progress(profile, "active_days", amount=1)
    if bonus:
        award_xp(profile, bonus, f"Streak bonus ({profile['streak']['current']} days) 🔥")
    return bonus


def new_badges(profile: dict) -> list:
    """Check all badge conditions; award any newly-earned badges."""
    earned = set(profile["badges"])
    newly = []

    def give(bid):
        if bid not in earned:
            profile["badges"].append(bid)
            newly.append(next(b for b in cb.BADGES if b["id"] == bid))

    if profile["messages_sent"] >= 1:
        give("first_message")
    if profile["messages_sent"] >= 60:
        give("first_hour")
    if profile["streak"]["longest"] >= 3:
        give("streak_3")
    if profile["streak"]["longest"] >= 7:
        give("streak_7")
    if profile["streak"]["longest"] >= 30:
        give("streak_30")
    if "cafe" in profile.get("scenarios_completed", []):
        give("cafe_master")
    if len(profile.get("scenarios_completed", [])) >= len(cb.SCENARIOS):
        give("scenario_5")
    if profile.get("stories_completed"):
        give("storyteller")

    quebec_words_known = sum(
        1 for wid in profile.get("vocab_srs", {}) 
        if (w := cb.vocab_by_id(wid)) and w["theme"] == "Quebec"
    )
    quebec_words_total = sum(1 for v in cb.VOCAB if v["theme"] == "Quebec")
    if quebec_words_known >= quebec_words_total:
        give("quebec_explorer")

    if profile.get("vocab_known_count", 0) >= min(20, len(cb.VOCAB)):
        give("vocab_50")
    if profile.get("vocab_known_count", 0) >= min(30, len(cb.VOCAB)):
        give("vocab_100")
    if compute_level(profile["xp"]) >= 5:
        give("level_5")
    if compute_level(profile["xp"]) >= 10:
        give("level_10")
    if profile.get("corrections_seen", 0) >= 20:
        give("corrector")

    return newly


# ---------------------------------------------------------------------------
# QUESTS
# ---------------------------------------------------------------------------
def _day_index() -> int:
    return date.today().timetuple().tm_yday


def _week_index() -> int:
    return date.today().isocalendar()[1]


def current_week_str() -> str:
    iso = date.today().isocalendar()
    return f"{iso[0]}-W{iso[1]}"


def get_todays_daily_quest() -> dict:
    return cb.QUESTS_DAILY[_day_index() % len(cb.QUESTS_DAILY)]


def get_this_weeks_weekly_quest() -> dict:
    return cb.QUESTS_WEEKLY[_week_index() % len(cb.QUESTS_WEEKLY)]


def ensure_quest_slots(profile: dict) -> None:
    """Reset the daily/weekly quest slot if the date/week has rolled over."""
    today = date.today().isoformat()
    week = current_week_str()

    daily = profile["quests"]["daily"]
    quest = get_todays_daily_quest()
    if daily.get("date") != today:
        profile["quests"]["daily"] = {"date": today, "quest_id": quest["id"], "done": False, "progress": 0}

    weekly = profile["quests"]["weekly"]
    wquest = get_this_weeks_weekly_quest()
    if weekly.get("week") != week:
        profile["quests"]["weekly"] = {"week": week, "quest_id": wquest["id"], "done": False, "progress": 0}


def bump_quest_progress(profile: dict, kind: str, amount: int = 1, target_value=None) -> list:
    """Advance quest progress for a given event kind."""
    ensure_quest_slots(profile)
    completed = []
    for slot_name, quest_lookup in (("daily", cb.QUESTS_DAILY), ("weekly", cb.QUESTS_WEEKLY)):
        slot = profile["quests"][slot_name]
        if slot["done"]:
            continue
        quest = next((q for q in quest_lookup if q["id"] == slot["quest_id"]), None)
        if not quest or quest["type"] != kind:
            continue
        if kind == "scenario":
            if target_value == quest["target"]:
                slot["done"] = True
        elif kind == "scenario_count":
            seen = slot.setdefault("scenario_ids_seen", [])
            if target_value is not None and target_value not in seen:
                seen.append(target_value)
            slot["progress"] = len(seen)
            if slot["progress"] >= quest["target"]:
                slot["done"] = True
        else:
            slot["progress"] = slot.get("progress", 0) + amount
            if slot["progress"] >= quest["target"]:
                slot["done"] = True
        if slot["done"]:
            award_xp(profile, quest["xp"], f"Quest completed: {quest['title']}")
            profile["coins"] += quest["coins"]
            completed.append(quest)
    return completed
