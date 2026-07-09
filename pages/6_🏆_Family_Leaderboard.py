"""
Page: Family Leaderboard -- friendly sibling competition + combined
family score, plus progress charts (XP over time, words learned, activity).
"""

from collections import defaultdict
import pandas as pd
import streamlit as st
from core import ui, gamification as game

st.set_page_config(page_title="Classement Famille", page_icon="🏆", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
db = st.session_state.db

st.title("🏆 Classement de la Famille")
st.caption("Un peu de compétition amicale pour rester motivés ensemble !")

# ---------------------------------------------------------------------------
# Leaderboard table
# ---------------------------------------------------------------------------
rows = []
for pname, p in db["profiles"].items():
    rows.append({
        "Profil": f"{p['avatar']} {pname}",
        "Niveau de jeu": game.compute_level(p["xp"]),
        "XP": p["xp"],
        "🔥 Série actuelle": p["streak"]["current"],
        "🔥 Meilleure série": p["streak"]["longest"],
        "🧠 Mots appris": p["vocab_known_count"],
        "🎭 Scènes terminées": len(p["scenarios_completed"]),
        "🏅 Badges": len(p["badges"]),
        "🪙 Pièces": p["coins"],
    })

df = pd.DataFrame(rows).sort_values("XP", ascending=False).reset_index(drop=True)
medals = ["🥇", "🥈", "🥉"] + [""] * max(0, len(df) - 3)
df.insert(0, "Rang", medals[: len(df)])
st.dataframe(df, width="stretch", hide_index=True)

st.divider()

# ---------------------------------------------------------------------------
# Family combined score
# ---------------------------------------------------------------------------
c1, c2, c3 = st.columns(3)
c1.metric("⭐ Score familial total", sum(p["xp"] for p in db["profiles"].values()))
c2.metric("🧠 Mots appris (famille)", sum(p["vocab_known_count"] for p in db["profiles"].values()))
c3.metric("🎭 Scènes terminées (famille)", sum(len(p["scenarios_completed"]) for p in db["profiles"].values()))

st.divider()

# ---------------------------------------------------------------------------
# XP over time (cumulative, per profile)
# ---------------------------------------------------------------------------
st.subheader("📈 XP cumulé dans le temps")
series = {}
for pname, p in db["profiles"].items():
    daily_xp = defaultdict(int)
    for h in p["history"]:
        d = h["date"][:10]
        daily_xp[d] += h["xp"]
    if not daily_xp:
        continue
    dates = sorted(daily_xp.keys())
    cumulative, total = {}, 0
    for d in dates:
        total += daily_xp[d]
        cumulative[d] = total
    series[pname] = cumulative

if series:
    all_dates = sorted({d for s in series.values() for d in s.keys()})
    chart_df = pd.DataFrame(index=all_dates)
    for pname, cumulative in series.items():
        running = 0
        col = []
        for d in all_dates:
            if d in cumulative:
                running = cumulative[d]
            col.append(running)
        chart_df[pname] = col
    st.line_chart(chart_df)
else:
    st.caption("Pas encore assez de données -- commence à discuter dans le Chat Tutor !")

st.subheader("🎖️ Comparaison des badges")
badge_cols = st.columns(len(db["profiles"]) or 1)
for col, (pname, p) in zip(badge_cols, db["profiles"].items()):
    with col:
        st.markdown(f"**{p['avatar']} {pname}** -- {len(p['badges'])} badges")
