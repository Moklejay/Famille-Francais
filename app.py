"""
Famille Français -- Home / Your Journey Dashboard
==================================================
Run with: streamlit run app.py

This is the entry point: create/select profiles here, then use the pages
in the left sidebar (Chat Tutor, Role-play, Story Mode, Vocab Review,
Quests, Settings & Export).

NOTE ON LANGUAGE: the interface (buttons, labels, messages) is in English
on purpose -- so anyone can use the app comfortably, even if they aren't
the one learning French. The actual French PRACTICE content (the tutor's
replies, role-play dialogue, story text, vocabulary) stays in French,
since that's the whole point of the app.

NOTE ON MULTIPLE PROFILES: several people can still each have their own
profile on the same install (handy if more than one person wants to
practice) -- but progress is intentionally never compared between
profiles. There is no leaderboard and no aggregate "family" stats;
each profile only ever sees its own journey. This is a deliberate
choice: the app is about personal progression, not competition.
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
# Your Journey -- this profile's own progress only. No family aggregate,
# no leaderboard, no cross-profile comparison on purpose: the app is about
# personal progression, so the only stats shown here belong to whoever is
# currently active in the sidebar.
# ---------------------------------------------------------------------------
lvl = game.compute_level(profile["xp"])
st.header(f"{profile['avatar']} Your Journey")
st.caption(f"**{st.session_state.active_profile}** -- Level {lvl} ({profile['level']} CEFR)")
st.progress(game.xp_to_next_level(profile["xp"])[2])

c1, c2, c3, c4 = st.columns(4)
c1.metric("⭐ XP", profile["xp"])
c2.metric("🔥 Streak", f"{profile['streak']['current']} days")
c3.metric("🧠 Words learned", profile["vocab_known_count"])
c4.metric("🎭 Role-plays completed", len(profile["scenarios_completed"]))

st.subheader("🏅 Your badges")
if not profile["badges"]:
    st.caption("No badges yet -- jump into the Chat or a Role-play!")
else:
    badge_html = ""
    for bid in profile["badges"]:
        b = next((x for x in cb.BADGES if x["id"] == bid), None)
        if b:
            badge_html += f'<span class="badge-pill">{b["emoji"]}<br>{b["name"]}</span>'
    st.markdown(badge_html, unsafe_allow_html=True)

st.divider()
st.info("👉 Use the menu on the left to get started: **Chat Tutor**, **Role-play**, **Story Mode**, "
        "**Vocab Review**, **Quests**, or **Settings & Export**.")
