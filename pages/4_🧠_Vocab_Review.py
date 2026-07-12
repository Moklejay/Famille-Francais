"""
Page: Vocab Review -- spaced repetition flashcards.
PREMIUM EDITION — Duolingo + Spotify Fusion
"""

import streamlit as st
from core import ui, gamification as game, content_bank as cb, srs, voice

st.set_page_config(page_title="Vocab Review", page_icon="🧠", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
name = st.session_state.active_profile

# ============================================================
# HERO HEADER
# ============================================================
st.markdown(f"""
<div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
    <div style="font-size: 2.5rem; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));">🧠</div>
    <div>
        <h1 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 900; font-size: 2rem;">
            Vocab Review
        </h1>
        <p style="margin: 4px 0 0; color: #9A9AAF; font-size: 1rem;">
            Spaced repetition flashcards — words you know well appear less often
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)

# ============================================================
# DUE CARDS
# ============================================================
cards = srs.due_cards(profile, limit=15)

if not cards:
    st.markdown("""
    <div class="status-card success" style="text-align: center; padding: 48px 32px;">
        <div class="icon" style="font-size: 3rem; margin-bottom: 16px;">🎉</div>
        <div class="title" style="font-size: 1.4rem; margin-bottom: 8px;">All caught up!</div>
        <div class="detail" style="font-size: 1rem;">No vocabulary cards are due right now. Come back tomorrow for your next review!</div>
    </div>
    """, unsafe_allow_html=True)

    # Show grammar tip
    level = profile["level"]
    tips = cb.GRAMMAR_TIPS.get(level, cb.GRAMMAR_TIPS.get("A1", []))
    if tips:
        st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
        st.subheader("📚 Grammar Tip")
        tip_title, tip_body = tips[0]
        st.markdown(f"""
        <div class="quest-card" style="border-left: 3px solid #1CB0F6;">
            <h4 style="margin: 0 0 8px; color: #1CB0F6;">{tip_title}</h4>
            <p style="margin: 0; color: #9A9AAF; line-height: 1.6;">{tip_body}</p>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

st.caption(f"{len(cards)} card{'s' if len(cards) > 1 else ''} due for review")

# ============================================================
# FLASHCARD SESSION STATE
# ============================================================
card_idx_key = f"vocab_idx_{name}"
show_back_key = f"vocab_show_back_{name}"

if card_idx_key not in st.session_state:
    st.session_state[card_idx_key] = 0
if show_back_key not in st.session_state:
    st.session_state[show_back_key] = False

card_idx = st.session_state[card_idx_key]
show_back = st.session_state[show_back_key]

if card_idx >= len(cards):
    # Session complete
    st.markdown("""
    <div class="status-card success" style="text-align: center; padding: 48px 32px;">
        <div class="icon" style="font-size: 3rem; margin-bottom: 16px;">🎉</div>
        <div class="title" style="font-size: 1.4rem; margin-bottom: 8px;">Session complete!</div>
        <div class="detail" style="font-size: 1rem;">Great work reviewing your vocabulary today.</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Start another session", type="primary", use_container_width=True):
        st.session_state[card_idx_key] = 0
        st.session_state[show_back_key] = False
        st.rerun()
    st.stop()

card = cards[card_idx]
progress = card_idx / len(cards)

# Progress bar
st.progress(progress, text=f"Card {card_idx + 1} of {len(cards)}")

# ============================================================
# FLASHCARD
# ============================================================
st.markdown(f"""
<div style="margin: 24px 0;">
    <div style="display: inline-block; padding: 4px 14px; border-radius: 999px; 
        background: #1A1A24; border: 1px solid rgba(255,255,255,0.08); color: #9A9AAF; 
        font-size: 0.8rem; font-weight: 700; margin-bottom: 16px;">
        {card['theme']} • {card['cefr']}
    </div>
</div>
""", unsafe_allow_html=True)

# Card front
st.markdown(f"""
<div style="background: #111118; border: 1px solid rgba(255,255,255,0.08); border-radius: 28px; 
    padding: 48px 32px; text-align: center; margin-bottom: 24px; position: relative; overflow: hidden;">
    <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; 
        background: linear-gradient(90deg, #58CC02, #89E219);"></div>
    <div style="font-size: 2.2rem; font-weight: 800; color: #F5F5FA; margin-bottom: 16px; 
        font-family: 'Outfit', sans-serif;">
        {card['fr']}
    </div>
    <div style="font-size: 1rem; color: #9A9AAF;">
        {card['en']}
    </div>
</div>
""", unsafe_allow_html=True)

voice.speak_button(card["fr"], key=f"vocab_speak_{name}_{card_idx}")

# Example sentence (always visible)
if card.get("ex_fr"):
    st.markdown(f"""
    <div style="background: rgba(28,176,246,0.08); border: 1px solid rgba(28,176,246,0.15); 
        border-radius: 20px; padding: 20px 24px; margin: 20px 0;">
        <div style="font-size: 1rem; color: #F5F5FA; line-height: 1.6; margin-bottom: 8px;">
            {card['ex_fr']}
        </div>
        <div style="font-size: 0.9rem; color: #9A9AAF;">
            {card['ex_en']}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# GRADING BUTTONS
# ============================================================
st.subheader("How well did you know this?")

grade_cols = st.columns(4)
grades = [
    ("😵 Again", 0, "#FF4B4B", "Start this card over — it'll come back soon"),
    ("🤔 Hard", 3, "#FF9600", "You got it, but it was tough — review in 1 day"),
    ("🙂 Good", 4, "#1CB0F6", "Solid recall — review in a few days"),
    ("😎 Easy", 5, "#58CC02", " effortless — review in a week or more"),
]

for i, (label, quality, color, desc) in enumerate(grades):
    with grade_cols[i]:
        if st.button(label, key=f"grade_{name}_{card_idx}_{quality}", use_container_width=True):
            srs.grade_card(profile, card["id"], quality)
            game.award_xp(profile, 5, "Vocab review")
            game.bump_quest_progress(profile, "vocab_review", amount=1)
            newly = game.new_badges(profile)
            ui.save()
            ui.show_new_badges(newly)
            st.session_state[card_idx_key] = card_idx + 1
            st.rerun()
        st.caption(f"<span style='color: {color}; font-size: 0.75rem;'>{desc}</span>", unsafe_allow_html=True)

st.markdown("---")

# Skip button
if st.button("⏭️ Skip this card", key=f"skip_{name}_{card_idx}"):
    st.session_state[card_idx_key] = card_idx + 1
    st.rerun()
