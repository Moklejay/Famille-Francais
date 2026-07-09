"""
Famille Français -- Home / Family Dashboard
=============================================
Run with:  streamlit run app.py

This is the entry point: create/select profiles here, then use the pages
in the left sidebar (Chat Tutor, Role-play, Story Mode, Vocab Review,
Quests, Family Leaderboard, Settings & Export).

NOTE ON LANGUAGE: the interface (buttons, labels, messages) is in English
on purpose -- so anyone can use the app comfortably, even if they aren't
the one learning French. The actual French PRACTICE content (the tutor's
replies, role-play dialogue, story text, vocabulary) stays in French,
since that's the whole point of the app.
"""

import streamlit as st
from core import storage, gamification as game, content_bank as cb, ui

st.set_page_config(page_title="Famille Français", page_icon="🇫🇷", layout="wide")
ui.init_app_state()

db = st.session_state.db

st.title("🇫🇷 Famille Français")
st.caption("Your French immersion journey.")

# ---------------------------------------------------------------------------
# Profile creation / selection
# ---------------------------------------------------------------------------
names = list(db["profiles"].keys())

# Brand-new profiles always start at game level 1, so only offer avatars
# that are actually unlocked at level 1 here -- the couple of "special"
# avatars promised as level-up rewards (content_bank.LEVEL_UNLOCKS) stay
# locked until the profile actually reaches that level (see Settings).
starter_avatars = ui.avatars_unlocked_at(1)

if not names:
    st.subheader("Welcome! Let's set up your profile. 👋")
    st.write("Pick a name, a starting level (CEFR), and an avatar.")
    name = st.text_input("Name")
    level = st.selectbox("Starting level (CEFR)", ["A1", "A2", "B1", "B2", "C1"],
                          help="Not sure? A1 = complete beginner, B1 = intermediate, C1 = advanced.")
    avatar = st.selectbox("Avatar", starter_avatars)
    if st.button("🚀 Create my profile", type="primary"):
        if name.strip():
            storage.create_profile(db, name.strip(), level, avatar)
            ui.save()
            st.session_state.active_profile = name.strip()
            st.rerun()
        else:
            st.error("Enter a name to continue.")
    st.stop()

# Allow adding more profiles later too (e.g. inviting someone else to use the app).
# Uses a form with clear_on_submit so the fields reset after adding someone --
# otherwise the just-typed name silently lingers in the box (looks like nothing
# happened, and re-clicking "Add" without editing it would just hit the
# "choose a unique name" error since that name is now taken).
with st.expander("➕ Add another profile"):
    with st.form("add_profile_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        new_name = c1.text_input("Name")
        new_level = c2.selectbox("Level", ["A1", "A2", "B1", "B2", "C1"])
        new_avatar = c3.selectbox("Avatar", starter_avatars)
        submitted = c4.form_submit_button("Add")
    if submitted:
        if new_name.strip() and new_name.strip() not in db["profiles"]:
            storage.create_profile(db, new_name.strip(), new_level, new_avatar)
            ui.save()
            st.rerun()
        else:
            st.error("Choose a unique name.")

ui.sidebar_switcher()

if not st.session_state.active_profile:
    st.session_state.active_profile = names[0]

profile = db["profiles"][st.session_state.active_profile]
ui.inject_theme(profile.get("theme", "Sunrise"))
bonus = game.record_daily_login(profile)
game.ensure_quest_slots(profile)
newly = game.new_badges(profile)
if bonus or newly:
    ui.save()
ui.show_new_badges(newly)

st.divider()

# ---------------------------------------------------------------------------
# Family Journey Dashboard
# ---------------------------------------------------------------------------
st.header("👨‍👩‍👧‍👦 The Family Journey")

family_xp = sum(p["xp"] for p in db["profiles"].values())
family_streak = max((p["streak"]["current"] for p in db["profiles"].values()), default=0)
family_words = sum(p["vocab_known_count"] for p in db["profiles"].values())
family_scenarios = sum(len(p["scenarios_completed"]) for p in db["profiles"].values())

c1, c2, c3, c4 = st.columns(4)
c1.metric("⭐ Total family XP", family_xp)
c2.metric("🔥 Best active streak", f"{family_streak} days")
c3.metric("🧠 Words learned (total)", family_words)
c4.metric("🎭 Role-plays completed", family_scenarios)

st.subheader("📊 Everyone's progress")
for name, p in db["profiles"].items():
    lvl = game.compute_level(p["xp"])
    with st.container(border=True):
        cols = st.columns([1, 3, 2, 2, 2])
        cols[0].markdown(f"## {p['avatar']}")
        cols[1].markdown(f"**{name}** -- Level {lvl} ({p['level']} CEFR)")
        cols[1].progress(game.xp_to_next_level(p["xp"])[2])
        cols[2].metric("XP", p["xp"])
        cols[3].metric("🔥 Streak", p["streak"]["current"])
        cols[4].metric("🏅 Badges", len(p["badges"]))

st.subheader("🏅 Family badge showcase")
tabs = st.tabs(list(db["profiles"].keys()))
for tab, (name, p) in zip(tabs, db["profiles"].items()):
    with tab:
        if not p["badges"]:
            st.caption("No badges yet -- jump into the Chat or a Role-play!")
        else:
            badge_html = ""
            for bid in p["badges"]:
                b = next((x for x in cb.BADGES if x["id"] == bid), None)
                if b:
                    badge_html += f'<span class="badge-pill">{b["emoji"]}<br>{b["name"]}</span>'
            st.markdown(badge_html, unsafe_allow_html=True)

st.divider()
st.info("👉 Use the menu on the left to get started: **Chat Tutor**, **Role-play**, **Story Mode**, "
        "**Vocab Review**, **Quests**, **Family Leaderboard**, or **Settings & Export**.")
