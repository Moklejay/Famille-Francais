"""
Page: Quests -- daily quest, weekly quest, this week's sibling joint
quest, and the full badge gallery (locked + unlocked) for motivation.
"""

from datetime import date
import streamlit as st
from core import ui, gamification as game, content_bank as cb

st.set_page_config(page_title="Quêtes", page_icon="🎯", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
db = st.session_state.db

st.title("🎯 Quêtes & Défis")

col1, col2 = st.columns(2)

with col1:
    st.subheader("☀️ Quête du jour")
    daily = profile["quests"]["daily"]
    quest = next((q for q in cb.QUESTS_DAILY if q["id"] == daily["quest_id"]), None)
    if quest is None:
        # The stored quest_id doesn't match anything in today's content bank
        # (e.g. content_bank.py's quest list changed after this slot was
        # assigned). Self-heal by re-rolling today's slot instead of
        # crashing the whole page -- mirrors the defensive lookup pattern
        # already used in gamification.bump_quest_progress().
        quest = game.get_todays_daily_quest()
        profile["quests"]["daily"] = {"date": date.today().isoformat(), "quest_id": quest["id"],
                                       "done": False, "progress": 0}
        daily = profile["quests"]["daily"]
        ui.save()
    with st.container(border=True):
        st.markdown(f"**{quest['title']}**")
        st.write(quest["desc"])
        progress = daily.get("progress", 0)
        if quest["type"] != "scenario":
            st.progress(min(1.0, progress / quest["target"]), text=f"{min(progress, quest['target'])}/{quest['target']}")
        st.caption(f"Récompense : +{quest['xp']} XP, +{quest['coins']} 🪙")
        st.markdown("✅ **Terminée !**" if daily["done"] else "⏳ En cours...")

with col2:
    st.subheader("📅 Quête de la semaine")
    weekly = profile["quests"]["weekly"]
    wquest = next((q for q in cb.QUESTS_WEEKLY if q["id"] == weekly["quest_id"]), None)
    if wquest is None:
        wquest = game.get_this_weeks_weekly_quest()
        week = f"{date.today().isocalendar()[0]}-W{date.today().isocalendar()[1]}"
        profile["quests"]["weekly"] = {"week": week, "quest_id": wquest["id"], "done": False, "progress": 0}
        weekly = profile["quests"]["weekly"]
        ui.save()
    with st.container(border=True):
        st.markdown(f"**{wquest['title']}**")
        st.write(wquest["desc"])
        progress = weekly.get("progress", 0)
        st.progress(min(1.0, progress / wquest["target"]), text=f"{min(progress, wquest['target'])}/{wquest['target']}")
        st.caption(f"Récompense : +{wquest['xp']} XP, +{wquest['coins']} 🪙")
        st.markdown("✅ **Terminée !**" if weekly["done"] else "⏳ En cours...")

st.divider()
st.subheader("🤝 Défi fraternel de la semaine")
joint_quest = game.get_this_weeks_joint_quest()
week = f"{date.today().isocalendar()[0]}-W{date.today().isocalendar()[1]}"
done_already = any(j["quest_id"] == joint_quest["id"] and j["week"] == week for j in db["joint_quests_completed"])
with st.container(border=True):
    st.markdown(f"**{joint_quest['title']}**")
    st.write(joint_quest["desc"])
    st.caption(f"Récompense pour chacun : +{joint_quest['xp']} XP, +{joint_quest['coins']} 🪙")
    if len(db["profiles"]) < 2:
        st.info("Ajoute un deuxième profil (page d'accueil) pour débloquer les défis fraternels !")
    else:
        st.markdown("✅ **Réussi cette semaine !**" if done_already else "⏳ Chacun doit faire sa part cette semaine...")

st.divider()
st.subheader("🏅 Galerie des badges")
st.caption("Badges débloqués en couleur, badges à venir en gris.")

cols = st.columns(4)
for i, badge in enumerate(cb.BADGES):
    unlocked = badge["id"] in profile["badges"]
    with cols[i % 4]:
        with st.container(border=True):
            st.markdown(f"## {badge['emoji'] if unlocked else '🔒'}")
            st.markdown(f"**{badge['name']}**" if unlocked else f"*{badge['name']}*")
            st.caption(badge["desc"])
