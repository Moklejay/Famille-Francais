"""
Page: Vocab Review -- spaced-repetition flashcards (SM-2 lite). This is
the "active recall + spaced repetition" pillar: words you know well come
back less often, shaky words come back sooner.
"""

import random
import streamlit as st
from core import ui, gamification as game, srs, content_bank as cb

st.set_page_config(page_title="Vocab Review", page_icon="🧠", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
name = st.session_state.active_profile

st.title("🧠 Vocab Review")
st.caption("Cards in context -- not just isolated words -- to lock vocabulary into memory.")

queue_key = f"vocab_queue_{name}"
idx_key = f"vocab_idx_{name}"
reveal_key = f"vocab_reveal_{name}"

if queue_key not in st.session_state:
    st.session_state[queue_key] = srs.due_cards(profile, limit=12)
    st.session_state[idx_key] = 0
    st.session_state[reveal_key] = False

if st.button("🔄 New review session"):
    st.session_state[queue_key] = srs.due_cards(profile, limit=12)
    st.session_state[idx_key] = 0
    st.session_state[reveal_key] = False
    st.rerun()

queue = st.session_state[queue_key]
idx = st.session_state[idx_key]

st.progress(min(1.0, idx / max(1, len(queue))), text=f"Card {min(idx + 1, len(queue))} / {len(queue)}")

if not queue or idx >= len(queue):
    st.success("✅ No more cards to review for now -- come back later, or change your CEFR level "
               "in Settings to unlock more vocabulary!")
    st.stop()

word = queue[idx]

with st.container(border=True):
    st.markdown(f"## {word['fr']}")
    st.caption(f"Theme: {word['theme']} • Level {word['cefr']}")
    if not st.session_state[reveal_key]:
        if st.button("👁️ Reveal translation", type="primary"):
            st.session_state[reveal_key] = True
            st.rerun()
    else:
        st.markdown(f"**Translation:** {word['en']}")
        st.markdown(f"*« {word['ex_fr']} »*")
        st.caption(word["ex_en"])

        st.write("Did you know this word?")
        cols = st.columns(4)
        grade_labels = [("😵 Forgot", 0), ("😅 Hard", 3), ("🙂 Good", 4), ("😎 Easy", 5)]
        for col, (label, quality) in zip(cols, grade_labels):
            if col.button(label, key=f"grade_{word['id']}_{quality}"):
                srs.grade_card(profile, word["id"], quality)
                xp = 2 if quality >= 3 else 1
                game.award_xp(profile, xp, f"Review: {word['fr']}")
                game.bump_quest_progress(profile, "vocab_review", amount=1)
                if quality >= 3 and word["theme"] == "Quebec":
                    game.bump_quest_progress(profile, "vocab_theme", amount=1)
                newly = game.new_badges(profile)
                st.session_state[idx_key] += 1
                st.session_state[reveal_key] = False
                ui.save()
                ui.show_new_badges(newly)
                st.rerun()

st.divider()
st.caption(f"📚 Total words mastered: **{profile['vocab_known_count']}**")
