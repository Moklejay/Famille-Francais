"""
storage.py
-----------
Persistence for Famille Français, with two backends:

1. LOCAL JSON FILE (default) -- data/family_data.json. Perfect when you
   run the app on your own computer, since the disk is always there.

2. GITHUB GIST (optional, recommended for hosted/shared use) -- if you
   configure GITHUB_TOKEN and GIST_ID (via Streamlit secrets or env
   vars), progress is read from and written to a private GitHub Gist
   instead. This matters because Streamlit Community Cloud's disk is
   *ephemeral* -- it can reset when the app restarts (after inactivity,
   redeploys, etc.), which would otherwise silently wipe streaks and XP.
   See DEPLOY_GUIDE.md for the 2-minute setup. If not configured, the app
   falls back to the local file automatically -- nothing breaks.

Both siblings can open the same hosted link from separate devices at the
same time. Because Streamlit keeps a separate in-memory copy of the whole
database per browser session, a naive "overwrite everything on save"
would let whoever saves last silently erase the other person's concurrent
progress. `merge_and_save()` (used by core/ui.py's save() helper) avoids
this: it only writes back the profile(s) *this* session actually changed
(including deletions -- see below), and always re-reads the freshest copy
of everything else first.

NOTE: `create_profile()` deliberately does NOT save on its own -- every
caller creates a profile and then calls ui.save() right after, which goes
through the safe merge path. If create_profile saved internally too, that
extra blind write could race with (and clobber) a concurrent session's
save in the brief window before the caller's own ui.save() runs.
"""

from __future__ import annotations
import json
import os
import copy
from datetime import date, datetime

try:
    import streamlit as st
except ImportError:
    st = None

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DATA_FILE = os.path.join(DATA_DIR, "family_data.json")
GIST_FILENAME = "family_data.json"

DEFAULT_PROFILE = {
    "level": "A1",
    "avatar": "🦊",
    "theme": "Sunrise",
    "xp": 0,
    "coins": 0,
    "streak": {"current": 0, "longest": 0, "last_active_date": None},
    "badges": [],
    "vocab_srs": {},          # word_id -> {interval, ease, due, reps}
    "vocab_known_count": 0,
    "vocab_known_ids": [],    # word_ids already counted toward vocab_known_count
    "messages_sent": 0,
    "corrections_seen": 0,
    "scenarios_completed": [],
    "story_progress": {},     # story_id -> chapter/turn index
    "stories_completed": [],  # story_ids that reached a natural ending
    "last_scenario_week": None,  # ISO year-week a scenario was last completed (joint quest recency)
    "last_story_week": None,     # ISO year-week Story Mode was last advanced (joint quest recency)
    "quests": {
        "daily": {"date": None, "quest_id": None, "done": False},
        "weekly": {"week": None, "quest_id": None, "done": False},
    },
    "history": [],            # [{date, xp, activity}]
    "created": None,
}

DEFAULT_DB = {
    "profiles": {},
    "joint_quests_completed": [],   # [{quest_id, date, participants}]
    "family_created": None,
}


# ---------------------------------------------------------------------------
# Gist backend (optional)
# ---------------------------------------------------------------------------
def _secret_get(key):
    if st is None:
        return None
    try:
        return st.secrets.get(key)
    except Exception:
        return None


def _gist_config():
    token = os.environ.get("GITHUB_TOKEN") or _secret_get("GITHUB_TOKEN")
    gist_id = os.environ.get("GIST_ID") or _secret_get("GIST_ID")
    if token and gist_id:
        return token, gist_id
    return None, None


def gist_configured() -> bool:
    token, gist_id = _gist_config()
    return bool(token and gist_id)


def _gist_headers(token):
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}


def _gist_load(token, gist_id) -> dict:
    import requests
    resp = requests.get(f"https://api.github.com/gists/{gist_id}", headers=_gist_headers(token), timeout=10)
    resp.raise_for_status()
    files = resp.json().get("files", {})
    entry = files.get(GIST_FILENAME)
    if not entry or not entry.get("content"):
        raise ValueError(f"Gist has no '{GIST_FILENAME}' file, or it's empty.")
    return json.loads(entry["content"])


def _gist_save(token, gist_id, db: dict) -> None:
    import requests
    payload = {"files": {GIST_FILENAME: {"content": json.dumps(db, ensure_ascii=False, indent=2)}}}
    resp = requests.patch(f"https://api.github.com/gists/{gist_id}", headers=_gist_headers(token),
                           json=payload, timeout=10)
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# Local file backend (default / always-on safety net)
# ---------------------------------------------------------------------------
def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_local() -> dict:
    _ensure_dir()
    if not os.path.exists(DATA_FILE):
        db = copy.deepcopy(DEFAULT_DB)
        db["family_created"] = date.today().isoformat()
        _save_local(db)
        return db
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return copy.deepcopy(DEFAULT_DB)


def _save_local(db: dict) -> None:
    _ensure_dir()
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def load_db() -> dict:
    """
    Load the family database. Prefers the GitHub Gist backend if
    GITHUB_TOKEN + GIST_ID are configured (survives hosted restarts);
    otherwise reads the local JSON file. Always returns a valid,
    forward-compatible dict (missing keys backfilled).
    """
    token, gist_id = _gist_config()
    db = None
    if token and gist_id:
        try:
            db = _gist_load(token, gist_id)
        except Exception:
            db = None  # fall through to local copy below

    if db is None:
        db = _load_local()

    # Backfill any missing top-level keys (forward-compatible)
    for k, v in DEFAULT_DB.items():
        db.setdefault(k, copy.deepcopy(v))
    # Backfill any missing per-profile keys too (e.g. after an app update
    # adds a new field like "stories_completed")
    for profile in db["profiles"].values():
        for k, v in DEFAULT_PROFILE.items():
            profile.setdefault(k, copy.deepcopy(v))
    return db


def save_db(db: dict) -> dict:
    """
    Always saves a local copy first (fast, always works within the running
    session). If a Gist backend is configured, also pushes there so
    progress survives a hosted restart. Returns a small status dict for
    the Settings page to show any sync issue (never raises).

    NOTE: this overwrites the ENTIRE database. Prefer merge_and_save() from
    application code (see core/ui.py's save() helper) so that two people
    using the app from separate devices at the same time can't clobber
    each other's progress -- see module docstring.
    """
    status = {"local_ok": True, "gist_ok": None, "gist_error": None}
    try:
        _save_local(db)
    except Exception as e:
        status["local_ok"] = False
        status["local_error"] = str(e)

    token, gist_id = _gist_config()
    if token and gist_id:
        try:
            _gist_save(token, gist_id, db)
            status["gist_ok"] = True
        except Exception as e:
            status["gist_ok"] = False
            status["gist_error"] = str(e)
    return status


def merge_and_save(db: dict, snapshot: dict) -> tuple[dict, dict]:
    """
    Safely persist `db` (this browser session's in-memory state) without
    clobbering concurrent changes from someone else's session (e.g. your
    sister using the app on her phone at the same moment).

    `snapshot` is the database exactly as it looked when this session
    loaded it (or last saved). We re-read the freshest copy from disk/Gist,
    then for each profile: if it's unchanged since `snapshot`, we leave the
    freshly-read version alone (so we don't stomp on someone else's newer
    edit to a profile we didn't touch); if it DID change in our session, our
    version wins for that profile. A profile that existed in `snapshot` but
    is missing from `db` was deliberately deleted this session (e.g. the
    Settings page's "Supprimer ce profil" button) -- that deletion is
    replayed onto the freshly-read copy too. The joint-quest-completion log
    is append-only, so we union it rather than replace it.

    Returns (merged_db, save_status) -- call sites should replace their
    in-memory db with `merged_db` afterwards so their view reflects the
    authoritative state (including anything the other person just saved).
    """
    live = load_db()

    old_profiles = snapshot.get("profiles", {})
    current_profiles = db.get("profiles", {})

    # Profiles present in the old snapshot but missing now were explicitly
    # deleted in this session -- replay that deletion onto the live copy.
    for name in set(old_profiles) - set(current_profiles):
        live["profiles"].pop(name, None)

    for name, profile in current_profiles.items():
        if old_profiles.get(name) != profile:
            live["profiles"][name] = profile        # we changed this one -> ours wins
        else:
            live["profiles"].setdefault(name, profile)  # unseen elsewhere -> keep it

    seen = {(j.get("quest_id"), j.get("week")) for j in live.get("joint_quests_completed", [])}
    for j in db.get("joint_quests_completed", []):
        key = (j.get("quest_id"), j.get("week"))
        if key not in seen:
            live["joint_quests_completed"].append(j)
            seen.add(key)

    live["family_created"] = live.get("family_created") or db.get("family_created")

    status = save_db(live)
    return live, status


def create_profile(db: dict, name: str, level: str = "A1", avatar: str = "🦊") -> dict:
    """Adds a new profile to `db` in memory. Does NOT save -- call
    ui.save() afterwards (every current call site already does)."""
    profile = copy.deepcopy(DEFAULT_PROFILE)
    profile["level"] = level
    profile["avatar"] = avatar
    profile["created"] = date.today().isoformat()
    db["profiles"][name] = profile
    return db


def get_profile(db: dict, name: str) -> dict:
    return db["profiles"][name]


def touch_daily_activity(profile: dict) -> int:
    """
    Update the streak for today's activity. Returns bonus XP earned for the
    streak milestone (0 if none). Call this once per session the first time
    the user does *anything* (send a message, review a card, etc.).
    """
    today = date.today()
    last = profile["streak"]["last_active_date"]
    if last == today.isoformat():
        return 0  # already counted today

    if last is not None:
        last_date = date.fromisoformat(last)
        gap = (today - last_date).days
        if gap <= 0:
            # last_active_date is in the future relative to "today" (clock
            # skew between server/device, or a timezone edge case around
            # midnight). Don't touch the streak or overwrite the stored
            # date with something earlier -- just wait for a real new day.
            return 0
        elif gap == 1:
            profile["streak"]["current"] += 1
        else:
            profile["streak"]["current"] = 1  # streak broken, restart
    else:
        profile["streak"]["current"] = 1

    profile["streak"]["longest"] = max(profile["streak"]["longest"], profile["streak"]["current"])
    profile["streak"]["last_active_date"] = today.isoformat()

    milestone_bonuses = {3: 15, 7: 40, 14: 80, 30: 200, 60: 450, 100: 800}
    return milestone_bonuses.get(profile["streak"]["current"], 0)


def log_history(profile: dict, activity: str, xp: int) -> None:
    profile["history"].append({
        "date": datetime.now().isoformat(timespec="seconds"),
        "activity": activity,
        "xp": xp,
    })
    # Keep history from growing unbounded
    if len(profile["history"]) > 500:
        profile["history"] = profile["history"][-500:]
