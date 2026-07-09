"""
Famille Français -- Home / Family Dashboard
=============================================
Run with:  streamlit run app.py

This is the entry point: create/select profiles here, then use the pages
in the left sidebar (Chat Tutor, Role-play, Story Mode, Vocab Review,
Quests, Family Leaderboard, Settings & Export).
"""

import streamlit as st
from datetime import date
from core import storage, gamification as game, content_bank as cb, ui

st.set_page_config(page_title="Famille Français", page_icon="🇫🇷", layout="wide")
ui.init_app_state()

db = st.session_state.db

st.title("🇫🇷 Famille Français")
st.caption("Votre voyage d'immersion en français -- ensemble.")

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
    st.subheader("Bienvenue ! Créons vos deux profils pour commencer. 👋")
    st.write("Chaque personne choisit un nom, un niveau de départ (CECR), et un avatar.")
    cols = st.columns(2)
    new_profiles = []
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**Profil {i + 1}**")
            name = st.text_input(f"Prénom", key=f"name_{i}")
            level = st.selectbox("Niveau de départ (CECR)", ["A1", "A2", "B1", "B2", "C1"], key=f"level_{i}",
                                  help="Pas sûr(e) ? A1 = grand débutant, B1 = intermédiaire, C1 = avancé.")
            avatar = st.selectbox("Avatar", starter_avatars, key=f"avatar_{i}")
            new_profiles.append((name, level, avatar))
    if st.button("🚀 Créer nos profils", type="primary"):
        created_any = False
        for name, level, avatar in new_profiles:
            if name.strip():
                storage.create_profile(db, name.strip(), level, avatar)
                created_any = True
        if created_any:
            ui.save()
            st.session_state.active_profile = new_profiles[0][0].strip() or None
            st.rerun()
        else:
            st.error("Entrez au moins un prénom pour continuer.")
    st.stop()

# Allow adding a second/third profile later too
with st.expander("➕ Ajouter un autre profil (ex : toi ou ta sœur, si pas encore fait)"):
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    new_name = c1.text_input("Prénom", key="add_name")
    new_level = c2.selectbox("Niveau", ["A1", "A2", "B1", "B2", "C1"], key="add_level")
    new_avatar = c3.selectbox("Avatar", starter_avatars, key="add_avatar")
    if c4.button("Ajouter"):
        if new_name.strip() and new_name.strip() not in db["profiles"]:
            storage.create_profile(db, new_name.strip(), new_level, new_avatar)
            ui.save()
            st.rerun()
        else:
            st.error("Choisis un prénom unique.")

ui.sidebar_switcher()

if not st.session_state.active_profile:
    st.session_state.active_profile = names[0]

profile = db["profiles"][st.session_state.active_profile]
ui.inject_theme(profile.get("theme", "Sunrise"))
bonus = game.record_daily_login(profile)
game.ensure_quest_slots(profile)
newly = game.new_badges(profile)
joint = game.check_joint_quest(db)
if bonus or newly or joint:
    ui.save()
ui.show_new_badges(newly)
if joint:
    st.balloons()
    st.success(f"🤝 Défi fraternel réussi : **{joint['title']}** ! Toute la famille gagne +{joint['xp']} XP.")

st.divider()

# ---------------------------------------------------------------------------
# Family Journey Dashboard
# ---------------------------------------------------------------------------
st.header("👨‍👩‍👧‍👦 Le Voyage de la Famille")

family_xp = sum(p["xp"] for p in db["profiles"].values())
family_streak = max((p["streak"]["current"] for p in db["profiles"].values()), default=0)
family_words = sum(p["vocab_known_count"] for p in db["profiles"].values())
family_scenarios = sum(len(p["scenarios_completed"]) for p in db["profiles"].values())

c1, c2, c3, c4 = st.columns(4)
c1.metric("⭐ XP familial total", family_xp)
c2.metric("🔥 Meilleure série active", f"{family_streak} jours")
c3.metric("🧠 Mots appris (total)", family_words)
c4.metric("🎭 Jeux de rôle terminés", family_scenarios)

st.subheader("📊 Progression de chacun")
for name, p in db["profiles"].items():
    lvl = game.compute_level(p["xp"])
    with st.container(border=True):
        cols = st.columns([1, 3, 2, 2, 2])
        cols[0].markdown(f"## {p['avatar']}")
        cols[1].markdown(f"**{name}** -- Niveau {lvl} ({p['level']} CECR)")
        cols[1].progress(game.xp_to_next_level(p["xp"])[2])
        cols[2].metric("XP", p["xp"])
        cols[3].metric("🔥 Série", p["streak"]["current"])
        cols[4].metric("🏅 Badges", len(p["badges"]))

st.subheader("🎯 Défi fraternel de la semaine")
joint_quest = game.get_this_weeks_joint_quest()
week = f"{date.today().isocalendar()[0]}-W{date.today().isocalendar()[1]}"
done_already = any(j["quest_id"] == joint_quest["id"] and j["week"] == week for j in db["joint_quests_completed"])
with st.container(border=True):
    st.markdown(f"**{joint_quest['title']}**")
    st.write(joint_quest["desc"])
    st.caption(f"Récompense : +{joint_quest['xp']} XP et +{joint_quest['coins']} pièces pour chacun.")
    st.write("✅ Terminé cette semaine !" if done_already else "⏳ En cours...")

st.divider()
st.subheader("🏅 Vitrine des badges de la famille")
tabs = st.tabs(list(db["profiles"].keys()))
for tab, (name, p) in zip(tabs, db["profiles"].items()):
    with tab:
        if not p["badges"]:
            st.caption("Pas encore de badge -- lance-toi dans le Chat ou un Jeu de rôle !")
        else:
            badge_html = ""
            for bid in p["badges"]:
                b = next((x for x in cb.BADGES if x["id"] == bid), None)
                if b:
                    badge_html += f'<span class="badge-pill">{b["emoji"]}<br>{b["name"]}</span>'
            st.markdown(badge_html, unsafe_allow_html=True)

st.divider()
st.info("👉 Utilise le menu à gauche pour commencer : **Chat Tutor**, **Jeux de rôle**, **Mode Histoire**, "
        "**Révision Vocabulaire**, **Quêtes**, **Classement Famille**, ou **Réglages / Export**.")
