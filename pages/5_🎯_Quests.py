"""
Page: Quests -- daily quest, weekly quest, and the full badge gallery
PREMIUM EDITION — Duolingo + Spotify Fusion
"""

from datetime import date
import streamlit as st
from core import ui, gamification as game, content_bank as cb

st.set_page_config(page_title="Quests", page_icon="🎯", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
db = st.session_state.db

# Get theme colors
theme_name = profile.get("theme", "Neon Green")
t = ui.THEMES.get(theme_name, ui.THEMES["Neon Green"])
primary = t["primary"]
success = "#58CC02"  # Keep success green as a semantic color (not theme-dependent)

# ============================================================
# HERO HEADER
# ============================================================
st.markdown(f"""
<div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
    <div style="font-size: 2.5rem; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));">🎯</div>
    <div>
        <h1 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 900; font-size: 2rem;">
            Quests & Challenges
        </h1>
        <p style="margin: 4px 0 0; color: #9A9AAF; font-size: 1rem;">
            Daily and weekly challenges to keep your streak alive
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)

# ============================================================
# DAILY & WEEKLY QUEST CARDS
# ============================================================

col1, col2 = st.columns(2)

with col1:
    st.subheader("☀️ Today's Quest")
    daily = profile["quests"]["daily"]
    quest = next((q for q in cb.QUESTS_DAILY if q["id"] == daily["quest_id"]), None)
    if quest is None:
        quest = game.get_todays_daily_quest()
        profile["quests"]["daily"] = {"date": date.today().isoformat(), "quest_id": quest["id"],
                                       "done": False, "progress": 0}
        daily = profile["quests"]["daily"]
        ui.save()

    progress = daily.get("progress", 0)
    is_done = daily["done"]
    card_class = "quest-card completed" if is_done else "quest-card"
    progress_pct = min(1.0, progress / quest["target"]) if quest["type"] != "scenario" else (1.0 if is_done else 0.0)

    st.markdown(f"""
    <div class="{card_class}">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <div style="font-size: 2.5rem;">{'✅' if is_done else '🎯'}</div>
            <div>
                <h3 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 800;">{quest['title']}</h3>
                <p style="margin: 4px 0 0; color: #9A9AAF;">{quest['desc']}</p>
            </div>
        </div>
        {f'<div style="background: {success}; color: #fff; padding: 8px 16px; border-radius: 999px; display: inline-block; font-family: Outfit, sans-serif; font-weight: 800;">✓ Completed!</div>' if is_done else ''}
    </div>
    """, unsafe_allow_html=True)

    if not is_done and quest["type"] != "scenario":
        st.progress(progress_pct, text=f"{min(progress, quest['target'])}/{quest['target']}")
    st.caption(f"Reward: +{quest['xp']} XP, +{quest['coins']} 🪙")

with col2:
    st.subheader("📅 This Week's Quest")
    weekly = profile["quests"]["weekly"]
    wquest = next((q for q in cb.QUESTS_WEEKLY if q["id"] == weekly["quest_id"]), None)
    if wquest is None:
        wquest = game.get_this_weeks_weekly_quest()
        week = f"{date.today().isocalendar()[0]}-W{date.today().isocalendar()[1]}"
        profile["quests"]["weekly"] = {"week": week, "quest_id": wquest["id"], "done": False, "progress": 0}
        weekly = profile["quests"]["weekly"]
        ui.save()

    w_progress = weekly.get("progress", 0)
    w_is_done = weekly["done"]
    w_card_class = "quest-card completed" if w_is_done else "quest-card"
    w_progress_pct = min(1.0, w_progress / wquest["target"])

    st.markdown(f"""
    <div class="{w_card_class}">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <div style="font-size: 2.5rem;">{'✅' if w_is_done else '📅'}</div>
            <div>
                <h3 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 800;">{wquest['title']}</h3>
                <p style="margin: 4px 0 0; color: #9A9AAF;">{wquest['desc']}</p>
            </div>
        </div>
        {f'<div style="background: {success}; color: #fff; padding: 8px 16px; border-radius: 999px; display: inline-block; font-family: Outfit, sans-serif; font-weight: 800;">✓ Completed!</div>' if w_is_done else ''}
    </div>
    """, unsafe_allow_html=True)

    if not w_is_done:
        st.progress(w_progress_pct, text=f"{min(w_progress, wquest['target'])}/{wquest['target']}")
    st.caption(f"Reward: +{wquest['xp']} XP, +{wquest['coins']} 🪙")

st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)

# ============================================================
# BADGE GALLERY
# ============================================================

st.subheader("🏅 Badge Gallery")
st.caption("Earn badges by completing activities and reaching milestones")

# Create rows of 4 badges each
for row_start in range(0, len(cb.BADGES), 4):
    cols = st.columns(4)
    for i in range(4):
        idx = row_start + i
        if idx >= len(cb.BADGES):
            break
        badge = cb.BADGES[idx]
        unlocked = badge["id"] in profile["badges"]
        with cols[i]:
            status_class = "unlocked" if unlocked else "locked"
            lock_icon = "" if unlocked else '<div style="position: absolute; top: 8px; right: 8px; font-size: 1rem;">🔒</div>'
            st.markdown(f"""
            <div style="position: relative;">
                {lock_icon}
                <div class="badge-pill {status_class}">
                    <div class="emoji">{badge['emoji']}</div>
                    <div class="name">{badge['name']}</div>
                    <div style="font-size: 0.7rem; color: #6A6A6A; margin-top: 4px;">{badge['desc']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
