"""
ui.py
------
Shared Streamlit UI bits: theme CSS, sidebar profile switcher, XP/streak
widgets, and small celebration helpers used across every page.

Also owns the "safe save" pattern (see save() below) that lets multiple
people use the hosted app from separate devices at the same time without
one of them silently overwriting another's progress.
"""

from __future__ import annotations
import copy
import streamlit as st
from core import storage, gamification as game, content_bank as cb

THEMES = {
    "Sunrise": {"primary": "#FF6F59", "bg": "#FFF6F0", "accent": "#FFC1B6"},
    "Ocean": {"primary": "#1F8A9E", "bg": "#F0F9FA", "accent": "#B6E4EA"},
    "Autumn": {"primary": "#C9762C", "bg": "#FBF3E9", "accent": "#F0C79A"},
    "Aurora": {"primary": "#7C5CBF", "bg": "#F5F1FB", "accent": "#D6C9F0"},
}

AVATARS = ["🦊", "🐸", "🦄", "🐨", "🦋", "🐧", "🦁", "🐢"]

# A couple of avatars are level-locked rewards -- content_bank.LEVEL_UNLOCKS
# already promises "Special avatar unlocked" at these levels, so Settings
# and profile creation need to actually gate them the same way
# THEME_UNLOCK_LEVEL gates themes below, otherwise the "unlock" is just
# text with nothing behind it (every avatar was pickable from level 1).
AVATAR_UNLOCK_LEVEL = {"🐸": 7, "🦄": 12}


def avatars_unlocked_at(level: int) -> list:
    """Avatars selectable at a given game level. Anything not listed in
    AVATAR_UNLOCK_LEVEL is available from level 1, i.e. from profile
    creation onward."""
    return [a for a in AVATARS if level >= AVATAR_UNLOCK_LEVEL.get(a, 1)]


def inject_theme(theme_name: str):
    t = THEMES.get(theme_name, THEMES["Sunrise"])
    # Streamlit Cloud can default to a dark theme, where body text is white.
    # Our themes only ever set a light pastel background -- without an
    # explicit text color here, headers/labels/captions inherit that white
    # and become unreadable against the light background (numbers still
    # showed up because stMetricValue is colored explicitly below). These
    # two colors are Streamlit's own default *light*-theme text colors, so
    # they read cleanly against every pastel background we ship.
    text_color = "#31333F"
    muted_text = "#5C5F66"
    st.markdown(
        f"""
        <style>
        .stApp {{ background-color: {t['bg']}; color: {text_color}; }}
        section[data-testid="stSidebar"] {{ background-color: {t['bg']}; color: {text_color}; }}
        .stApp p, .stApp span, .stApp label, .stApp li,
        section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {{ color: {text_color}; }}
        [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{
            color: {muted_text} !important;
        }}
        div[data-testid="stMetricValue"] {{ color: {t['primary']}; }}
        div[data-testid="stMetricLabel"] {{ color: {muted_text}; }}
        .streak-badge {{
            display:inline-block; padding: 6px 14px; border-radius: 999px;
            background: {t['accent']}; color: {t['primary']}; font-weight: 700;
            font-size: 1.1rem; margin-bottom: 8px;
        }}
        .quest-card {{
            border: 2px solid {t['accent']}; border-radius: 14px; padding: 14px 18px;
            margin-bottom: 10px; background: white; color: {text_color};
        }}
        .badge-pill {{
            display:inline-block; background:{t['accent']}; border-radius: 10px;
            padding: 8px 10px; margin: 4px; text-align:center; font-size: 0.85rem;
            color: {t['primary']};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_app_state():
    if "db" not in st.session_state:
        st.session_state.db = storage.load_db()
        # Snapshot of "what the database looked like when we loaded it" --
        # used by save() to figure out what *this* session actually changed,
        # so we never blindly clobber someone else's concurrent edits.
        st.session_state.db_snapshot = copy.deepcopy(st.session_state.db)
    if "active_profile" not in st.session_state:
        st.session_state.active_profile = None


def save():
    """
    Persist the in-memory db safely: only the profile(s) this session
    actually modified get written; everything else is re-read fresh first
    (so someone's concurrent session on another device isn't overwritten).
    Refreshes st.session_state.db to the merged, authoritative result.
    """
    merged, status = storage.merge_and_save(
        st.session_state.db, st.session_state.get("db_snapshot", st.session_state.db)
    )
    st.session_state.db = merged
    st.session_state.db_snapshot = copy.deepcopy(merged)

    if status.get("gist_ok") is False:
        st.session_state["_last_gist_error"] = status.get("gist_error")
    elif status.get("gist_ok") is True:
        st.session_state.pop("_last_gist_error", None)
    return status


def require_profile():
    """Call at top of every page (except app.py). Stops the page with a
    friendly message if no profile is selected yet."""
    init_app_state()
    if not st.session_state.active_profile or st.session_state.active_profile not in st.session_state.db["profiles"]:
        st.warning("👋 Choose your profile first on the Home page!")
        st.stop()
    profile = st.session_state.db["profiles"][st.session_state.active_profile]
    inject_theme(profile.get("theme", "Sunrise"))
    bonus = game.record_daily_login(profile)
    game.ensure_quest_slots(profile)
    if bonus:
        st.toast(f"🔥 Streak bonus! +{bonus} XP", icon="🔥")
    if bonus:
        # Persist the streak update right away, in case this session never
        # visits a page that saves for another reason (e.g. only checking
        # Quests or the Leaderboard) -- otherwise a closed tab would lose it.
        save()
        profile = st.session_state.db["profiles"][st.session_state.active_profile]
    return profile


def sidebar_switcher():
    db = st.session_state.db
    names = list(db["profiles"].keys())
    if not names:
        return
    with st.sidebar:
        st.markdown("### 👤 Active profile")
        current = st.session_state.active_profile if st.session_state.active_profile in names else names[0]
        choice = st.selectbox("Who's playing?", names, index=names.index(current), key="profile_switcher")
        if choice != st.session_state.active_profile:
            st.session_state.active_profile = choice
            st.rerun()
        profile = db["profiles"][choice]
        st.markdown(f"### {profile['avatar']} {choice}")
        st.markdown(f'<span class="streak-badge">🔥 {profile["streak"]["current"]} days</span>', unsafe_allow_html=True)
        level = game.compute_level(profile["xp"])
        st.metric("Level", level, help=f"{profile['xp']} XP total")
        _, xp_left, progress = game.xp_to_next_level(profile["xp"])
        if xp_left is not None:
            st.progress(progress, text=f"{xp_left} XP to level {level + 1}")
        else:
            st.progress(1.0, text="Max level reached! 🎉")
        st.metric("🪙 Coins", profile["coins"])
        st.caption(f"CEFR level: **{profile['level']}**")
        if st.session_state.get("_last_gist_error"):
            st.caption("⚠️ Persistent backup unavailable right now (see Settings).")


def show_new_badges(newly: list):
    for b in newly:
        st.balloons()
        st.success(f"🏅 New badge unlocked: **{b['emoji']} {b['name']}** -- {b['desc']}")


def show_level_up(result: dict):
    if result.get("leveled_up"):
        st.balloons()
        st.success(f"🎉 Level up! You're now level {result['new_level']}!")
        if result.get("unlock"):
            st.info(result["unlock"])
