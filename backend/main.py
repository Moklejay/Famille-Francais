"""
Famille Français API -- FastAPI wrapper around the existing core/ Python
logic (storage, gamification, content_bank, srs, tutor_engine). This is
the backend for the real React rebuild; it exposes the same data/behavior
the old Streamlit app had, over HTTP, so any frontend can use it.

Adds two things the Streamlit app didn't have yet (per the design handoff):
  - profile["streak_freezes"] + a real streak-freeze purchase (coins sink)
  - profile["track"] ("metro" | "quebec") for the France/Québec toggle
"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import copy

from core import storage, gamification as game, content_bank as cb, srs, tutor_engine, ai_client

app = FastAPI(title="Famille Français API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the real frontend origin once deployed
    allow_methods=["*"],
    allow_headers=["*"],
)

STREAK_FREEZE_COST = 50


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _load():
    return storage.load_db()


def _save(db):
    return storage.save_db(db)


def _ensure_new_fields(profile: dict) -> None:
    """Backfill fields the old Streamlit app never had."""
    profile.setdefault("streak_freezes", 0)
    profile.setdefault("track", "metro")
    profile.setdefault("avatar_photo_url", None)


def _profile_view(profile: dict, name: str) -> dict:
    """Shape a profile dict into exactly what the Home screen needs."""
    _ensure_new_fields(profile)
    lvl = game.compute_level(profile["xp"])
    next_level, xp_left, progress = game.xp_to_next_level(profile["xp"])
    game.ensure_quest_slots(profile)
    daily = profile["quests"]["daily"]
    weekly = profile["quests"]["weekly"]
    daily_q = next((q for q in cb.QUESTS_DAILY if q["id"] == daily.get("quest_id")), None)
    weekly_q = next((q for q in cb.QUESTS_WEEKLY if q["id"] == weekly.get("quest_id")), None)

    return {
        "name": name,
        "avatar": profile["avatar"],
        "avatar_photo_url": profile.get("avatar_photo_url"),
        "level": lvl,
        "next_level": next_level,
        "cefr": profile["level"],
        "xp": profile["xp"],
        "xp_to_next": xp_left,
        "xp_progress": progress,
        "coins": profile["coins"],
        "streak": profile["streak"]["current"],
        "streak_freezes": profile["streak_freezes"],
        "streak_freeze_cost": STREAK_FREEZE_COST,
        "track": profile["track"],
        "vocab_due": len(srs.due_cards(profile)),
        "badges_earned": profile["badges"],
        "quests": {
            "daily": {**daily, "quest": daily_q},
            "weekly": {**weekly, "quest": weekly_q},
        },
    }


# ---------------------------------------------------------------------------
# profile
# ---------------------------------------------------------------------------
class CreateProfileRequest(BaseModel):
    name: str
    level: str = "A1"
    avatar: str = "🦊"


@app.get("/api/profiles")
def list_profiles():
    db = _load()
    return {"names": list(db["profiles"].keys())}


@app.post("/api/profiles")
def create_profile(req: CreateProfileRequest):
    db = _load()
    if req.name in db["profiles"]:
        raise HTTPException(400, "That name is already taken.")
    storage.create_profile(db, req.name, req.level, req.avatar)
    _save(db)
    return _profile_view(db["profiles"][req.name], req.name)


@app.get("/api/profiles/{name}")
def get_profile(name: str):
    db = _load()
    if name not in db["profiles"]:
        raise HTTPException(404, "No such profile.")
    profile = db["profiles"][name]

    # Daily login + quest slot rotation + badge check, same as the old
    # Streamlit app did on every page load.
    bonus = game.record_daily_login(profile)
    newly = game.new_badges(profile)
    _save(db)

    view = _profile_view(profile, name)
    view["daily_login_bonus_xp"] = bonus
    view["newly_earned_badges"] = newly
    return view


@app.post("/api/profiles/{name}/track")
def set_track(name: str, track: str):
    if track not in ("metro", "quebec"):
        raise HTTPException(400, "track must be 'metro' or 'quebec'")
    db = _load()
    profile = db["profiles"][name]
    _ensure_new_fields(profile)
    profile["track"] = track
    _save(db)
    return _profile_view(profile, name)


CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1"]


@app.post("/api/profiles/{name}/cefr")
def set_cefr(name: str, level: str):
    if level not in CEFR_LEVELS:
        raise HTTPException(400, f"level must be one of {CEFR_LEVELS}")
    db = _load()
    profile = db["profiles"][name]
    _ensure_new_fields(profile)
    profile["level"] = level
    _save(db)
    return _profile_view(profile, name)


# ---------------------------------------------------------------------------
# streak freeze (new coin sink)
# ---------------------------------------------------------------------------
@app.post("/api/profiles/{name}/streak-freeze/buy")
def buy_streak_freeze(name: str):
    db = _load()
    profile = db["profiles"][name]
    _ensure_new_fields(profile)
    if profile["coins"] < STREAK_FREEZE_COST:
        raise HTTPException(400, "Not enough coins.")
    profile["coins"] -= STREAK_FREEZE_COST
    profile["streak_freezes"] += 1
    _save(db)
    return _profile_view(profile, name)


# ---------------------------------------------------------------------------
# quests / badges (full lists, for the Quests screen later)
# ---------------------------------------------------------------------------
@app.get("/api/badges")
def all_badges():
    return {"badges": cb.BADGES}


@app.get("/api/quests/{name}")
def quests(name: str):
    db = _load()
    profile = db["profiles"][name]
    game.ensure_quest_slots(profile)
    _save(db)
    daily = profile["quests"]["daily"]
    weekly = profile["quests"]["weekly"]
    daily_q = next((q for q in cb.QUESTS_DAILY if q["id"] == daily.get("quest_id")), None)
    weekly_q = next((q for q in cb.QUESTS_WEEKLY if q["id"] == weekly.get("quest_id")), None)
    return {
        "daily": {**daily, "quest": daily_q},
        "weekly": {**weekly, "quest": weekly_q},
    }


# ---------------------------------------------------------------------------
# chat tutor (Speak)
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat/{name}")
def chat(name: str, req: ChatRequest):
    db = _load()
    profile = db["profiles"][name]

    result = tutor_engine.respond(req.message, profile["level"], name=name, history=[])

    profile["messages_sent"] += 1
    xp_result = game.award_xp(profile, 3, "Message sent in Chat")
    quest_done = game.bump_quest_progress(profile, "chat_count", amount=1)
    if result["corrections"]:
        profile["corrections_seen"] += len(result["corrections"])
    newly = game.new_badges(profile)
    _save(db)

    return {
        "reply": result["reply"],
        "corrections": result["corrections"],
        "new_vocab": result.get("new_vocab", []),
        "ai_error": result.get("ai_error"),
        "xp_result": xp_result,
        "quests_completed": quest_done,
        "newly_earned_badges": newly,
        "ai_active": ai_client.is_configured(),
    }


# ---------------------------------------------------------------------------
# story mode
# ---------------------------------------------------------------------------
STORY_BY_TRACK = {"metro": "voyage_provence", "quebec": "mystere_quebec"}


def _story_view(profile: dict, story_id: str) -> dict:
    story = cb.STORIES[story_id]
    idx = profile.setdefault("story_progress", {}).get(story_id, 0)
    idx = min(idx, len(story["chapters"]) - 1)
    chapter = story["chapters"][idx]
    is_last = idx >= len(story["chapters"]) - 1
    return {
        "story_id": story_id,
        "title": story["title"],
        "chapter_index": idx,
        "chapter_count": len(story["chapters"]),
        "chapter_fr": chapter["fr"],
        "prompt": chapter.get("prompt"),
        "choices": chapter.get("choices"),
        "is_last": is_last,
        "completed": story_id in profile.get("stories_completed", []),
    }


@app.get("/api/story/{name}")
def get_story(name: str, story_id: str | None = None):
    db = _load()
    profile = db["profiles"][name]
    _ensure_new_fields(profile)
    sid = story_id or STORY_BY_TRACK[profile["track"]]
    return _story_view(profile, sid)


@app.post("/api/story/{name}/advance")
def advance_story(name: str, story_id: str | None = None):
    db = _load()
    profile = db["profiles"][name]
    _ensure_new_fields(profile)
    sid = story_id or STORY_BY_TRACK[profile["track"]]
    story = cb.STORIES[sid]
    progress = profile.setdefault("story_progress", {})
    idx = progress.get(sid, 0)

    xp_result = None
    quest_done = []
    newly = []
    if idx < len(story["chapters"]) - 1:
        idx += 1
        progress[sid] = idx
        xp_result = game.award_xp(profile, 8, f"Story progress: {story['title']}")
        if idx >= len(story["chapters"]) - 1:
            completed = profile.setdefault("stories_completed", [])
            if sid not in completed:
                completed.append(sid)
            quest_done = game.bump_quest_progress(profile, "story", amount=1)
        newly = game.new_badges(profile)
    _save(db)

    view = _story_view(profile, sid)
    view["xp_result"] = xp_result
    view["quests_completed"] = quest_done
    view["newly_earned_badges"] = newly
    return view


# ---------------------------------------------------------------------------
# translate (English toggle for tutor replies)
# ---------------------------------------------------------------------------
class TranslateRequest(BaseModel):
    text: str


@app.post("/api/translate")
def translate(req: TranslateRequest):
    if not ai_client.is_configured():
        return {"available": False, "translation": None}
    try:
        result = ai_client.chat_json(
            system_prompt=(
                "Translate the French text the user sends into natural, casual English. "
                'Respond ONLY with valid JSON, no other text: {"en": "..."}'
            ),
            messages=[{"role": "user", "content": req.text}],
            max_tokens=300,
        )
        return {"available": True, "translation": result.get("en")}
    except RuntimeError:
        return {"available": False, "translation": None}


@app.get("/api/health")
def health():
    return {"ok": True}
