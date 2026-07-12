"""
ui.py
------
Shared Streamlit UI bits: theme CSS, sidebar profile switcher, XP/streak
widgets, and small celebration helpers used across every page.

Also owns the "safe save" pattern (see save() below) that lets multiple
people use the hosted app from separate devices at the same time without
one of them silently overwriting another's progress.

DESIGN SYSTEM NOTE: the app uses a single dark, "premium app" shell
(near-black surfaces, card elevation, bold rounded typography) inspired by
modern media apps like Spotify. The four THEMES below no longer swap the
whole page to a pastel background -- instead each one is an accent color
(buttons, active nav, progress bars, badges) layered on the same dark
shell, so the existing level-gated "unlock a theme" reward system keeps
working exactly as before, it just changes an accent instead of a mood.
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
    """
    Inject the app's global dark "premium app" stylesheet, accented with
    the given theme's primary color.

    Everything here targets Streamlit's stable data-testid hooks rather
    than internal class names (which change between Streamlit versions),
    and every text color is set explicitly -- Streamlit Cloud's own theme
    default (which can be light or dark depending on the deploy) is never
    relied on, since that's exactly what caused the earlier illegible-text
    bug: inherited color with no explicit override.
    """
    t = THEMES.get(theme_name, THEMES["Sunrise"])
    accent = t["primary"]
    accent_soft = t["accent"]

    bg = "#0B0B0D"          # page shell -- near-black, slightly warm
    surface = "#181818"     # cards, containers
    surface_hi = "#232325"  # hovered / raised surface
    border = "rgba(255,255,255,0.08)"
    text = "#FFFFFF"
    muted = "#B3B3B3"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');

        html, body, .stApp {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        /* Never touch Streamlit's own Material Symbols icon glyphs (sidebar
           chevrons, expander arrows, menu kebab, etc) -- overriding their
           font-family is what makes an icon glyph render as literal text
           like "keyboard_arrow_right" instead of an arrow. */
        [data-testid*="Icon"], .material-symbols-outlined, .material-icons,
        span[class*="stIcon"] {{
            font-family: 'Material Symbols Outlined', 'Material Symbols Rounded', 'Material Icons' !important;
        }}
        h1, h2, h3, h4, .stApp [data-testid="stMarkdownContainer"] h1,
        .stApp [data-testid="stMarkdownContainer"] h2, .stApp [data-testid="stMarkdownContainer"] h3 {{
            font-family: 'Poppins', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.01em;
        }}

        /* ---- Page shell ---------------------------------------------------- */
        .stApp {{
            background:
                radial-gradient(1100px circle at 8% -12%, {accent_soft}2E 0%, transparent 45%),
                radial-gradient(900px circle at 100% 0%, {accent}1A 0%, transparent 40%),
                {bg};
            color: {text};
        }}
        section[data-testid="stSidebar"] {{
            background: #000000;
            color: {text};
            border-right: 1px solid {border};
        }}
        .stApp p, .stApp span, .stApp label, .stApp li,
        section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {{ color: {text}; }}
        [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{
            color: {muted} !important;
        }}
        [data-testid="stHeader"] {{ background: transparent; }}

        /* ---- Sidebar page navigation, styled like a media-app rail --------- */
        [data-testid="stSidebarNav"] a, [data-testid="stSidebarNavLink"] {{
            border-radius: 8px;
            margin: 2px 8px;
            padding: 8px 12px !important;
            color: {muted} !important;
            font-weight: 600;
            transition: background 0.15s ease, color 0.15s ease;
        }}
        [data-testid="stSidebarNav"] a:hover, [data-testid="stSidebarNavLink"]:hover {{
            background: rgba(255,255,255,0.08);
            color: {text} !important;
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"], [data-testid="stSidebarNavLink"][aria-current="page"] {{
            background: {accent}26;
            color: {accent} !important;
        }}

        /* ---- Buttons --------------------------------------------------------*/
        .stButton > button, .stFormSubmitButton > button, [data-testid="stChatInputSubmitButton"] {{
            background: {accent} !important;
            color: #0B0B0D !important;
            border: none !important;
            border-radius: 999px !important;
            font-weight: 700 !important;
            padding: 0.5rem 1.4rem !important;
            transition: transform 0.12s ease, filter 0.12s ease;
            box-shadow: 0 4px 14px {accent}40;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            transform: translateY(-1px) scale(1.02);
            filter: brightness(1.08);
        }}
        .stButton > button:disabled {{ opacity: 0.4; box-shadow: none; }}

        /* ---- Inputs, selects, chat input -------------------------------------*/
        div[data-baseweb="input"], div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"], textarea, [data-testid="stChatInput"] {{
            background: {surface} !important;
            color: {text} !important;
            border-radius: 12px !important;
            border: 1px solid {border} !important;
        }}
        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within,
        div[data-baseweb="textarea"]:focus-within {{
            border-color: {accent} !important;
            box-shadow: 0 0 0 1px {accent} !important;
        }}
        input, textarea {{ color: {text} !important; }}
        [data-testid="stChatInput"] textarea::placeholder {{ color: {muted} !important; }}

        /* ---- Metrics ----------------------------------------------------- */
        div[data-testid="stMetric"] {{
            background: {surface};
            border: 1px solid {border};
            border-radius: 14px;
            padding: 12px 16px;
        }}
        div[data-testid="stMetricValue"] {{ color: {accent} !important; font-family:'Poppins',sans-serif; }}
        div[data-testid="stMetricLabel"] {{ color: {muted} !important; }}

        /* ---- Progress bars, styled like a playback bar -------------------- */
        div[data-testid="stProgress"] > div {{ background: rgba(255,255,255,0.12); border-radius: 999px; }}
        div[data-testid="stProgress"] > div > div {{ background: {accent}; border-radius: 999px; }}

        /* ---- Bordered containers -> elevated cards ------------------------- */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {surface};
            border: 1px solid {border} !important;
            border-radius: 16px !important;
            transition: background 0.15s ease;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{ background: {surface_hi}; }}

        /* ---- Chat messages, styled as message bubbles ----------------------*/
        [data-testid="stChatMessage"] {{
            background: {surface};
            border: 1px solid {border};
            border-radius: 18px;
            padding: 10px 6px;
            margin-bottom: 10px;
        }}
        [data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"],
        [data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"] {{
            background: {accent}22;
            border-radius: 50%;
        }}

        /* ---- Tabs ------------------------------------------------------- */
        button[data-baseweb="tab"] {{ color: {muted}; font-weight: 600; }}
        button[data-baseweb="tab"][aria-selected="true"] {{ color: {accent}; }}
        div[data-baseweb="tab-highlight"] {{ background-color: {accent} !important; }}

        /* ---- Alerts / toasts, kept legible on dark surfaces ---------------- */
        div[data-testid="stAlert"] {{ border-radius: 12px; }}

        /* ---- App-specific classes used directly in page markup ------------ */
        .streak-badge {{
            display:inline-block; padding: 6px 14px; border-radius: 999px;
            background: {accent}26; color: {accent}; font-weight: 700;
            font-size: 1.1rem; margin-bottom: 8px; border: 1px solid {accent}55;
        }}
        .quest-card {{
            border: 1px solid {border}; border-radius: 16px; padding: 16px 20px;
            margin-bottom: 10px; background: {surface}; color: {text};
        }}
        .badge-pill {{
            display:inline-block; background:{surface}; border: 1px solid {accent}55;
            border-radius: 12px; padding: 10px 12px; margin: 4px; text-align:center;
            font-size: 0.85rem; color: {text};
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
