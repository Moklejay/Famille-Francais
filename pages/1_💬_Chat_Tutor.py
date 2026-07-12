"""
Page: Chat Tutor -- free conversation with your French tutor.
PREMIUM EDITION — Duolingo + Spotify Fusion
"""

import streamlit as st
from core import ui, gamification as game, tutor_engine, ai_client, voice

st.set_page_config(page_title="Chat Tutor", page_icon="💬", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
name = st.session_state.active_profile

# ============================================================
# HERO HEADER
# ============================================================
st.markdown(f"""
<div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
    <div style="font-size: 2.5rem; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));">💬</div>
    <div>
        <h1 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 900; font-size: 2rem;">
            Chat Tutor
        </h1>
        <p style="margin: 4px 0 0; color: #9A9AAF; font-size: 1rem;">
            Free conversation in French — AI-adaptive or offline mode
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)

# Voice toggle
conv_on = voice.conversation_toggle(f"conv_mode_chat_{name}")
if conv_on:
    st.caption("🎙️ Conversation mode is on — just talk, pause when you're done, and the tutor will answer out loud.")
else:
    st.caption("Type your message, or turn on conversation mode above to talk hands-free.")

# AI status in sidebar
ai_mode = ai_client.is_configured()
with st.sidebar:
    st.markdown("---")
    if ai_mode:
        st.success(f"🤖 Adaptive AI tutor ({ai_client.get_model()})")
    else:
        st.warning("📴 Offline mode (rule-based replies)")

# ============================================================
# CHAT HISTORY
# ============================================================
chat_key = f"chat_history_{name}"
last_prompt_key = f"chat_last_prompt_{name}"

if chat_key not in st.session_state:
    st.session_state[chat_key] = []
if last_prompt_key not in st.session_state:
    st.session_state[last_prompt_key] = None

history = st.session_state[chat_key]

# Display existing messages
for i, msg in enumerate(history):
    if msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🎓"):
            st.markdown(msg["content"])
            voice.speak_button(msg["content"], key=f"chat_speak_{name}_{i}")
            if msg.get("hint_en"):
                st.caption(f"💡 {msg['hint_en']}")
            if msg.get("corrections"):
                with st.container(border=True):
                    st.markdown("**✏️ Friendly corrections:**")
                    for c in msg["corrections"]:
                        st.markdown(f"- *« {c['matched']} »* → **« {c['suggestion']} »**")
                        st.caption(c["explanation"])
            if msg.get("new_vocab"):
                with st.container(border=True):
                    st.markdown("**📚 New vocabulary:**")
                    for v in msg["new_vocab"]:
                        st.markdown(f"- **{v['fr']}** = {v['en']}")
    else:
        with st.chat_message("user", avatar=profile["avatar"]):
            st.markdown(msg["content"])

# Opening line if empty
if not history:
    opening = tutor_engine.opening_line(profile["level"], name)
    with st.chat_message("assistant", avatar="🎓"):
        st.markdown(opening)
        voice.speak_button(opening, key=f"chat_opening_{name}")
    st.session_state[chat_key].append({
        "role": "assistant",
        "content": opening,
        "hint_en": None,
        "corrections": [],
        "new_vocab": [],
    })

# ============================================================
# INPUT AREA
# ============================================================
mic_text = None
if conv_on:
    if voice.conversation_gate(f"chat_ai_{name}"):
        if history:
            last_msg = history[-1]
            speak_text = last_msg["content"] if last_msg["role"] == "assistant" else None
        else:
            speak_text = None
        voice.conversation_loop(
            turn_id=str(len(history)),
            conv_key=f"chat_ai_{name}",
            speak_text=speak_text,
        )
else:
    mic_col, _ = st.columns([1, 8])
    with mic_col:
        mic_text = voice.mic_input(f"chat_mic_{name}") if voice.mic_available() else None

user_input = mic_text or st.chat_input("Write in French...")

if user_input:
    # Add user message
    st.session_state[chat_key].append({"role": "user", "content": user_input})

    # Build plain-text history for the AI
    plain_history = [
        {"role": m["role"], "content": m["content"]}
        for m in history[-12:]
    ]

    # Get response
    try:
        result = tutor_engine.respond(
            user_input, profile["level"], name, plain_history,
            st.session_state[last_prompt_key]
        )
    except Exception as e:
        result = tutor_engine.respond_rulebased(user_input, profile["level"], st.session_state[last_prompt_key])
        result["ai_error"] = str(e)

    # Track last prompt
    st.session_state[last_prompt_key] = result.get("reply")

    # Add assistant response
    st.session_state[chat_key].append({
        "role": "assistant",
        "content": result["reply"],
        "hint_en": result.get("hint_en"),
        "corrections": result.get("corrections", []),
        "new_vocab": result.get("new_vocab", []),
        "source": result.get("source", "unknown"),
    })

    # Gamification
    profile["messages_sent"] += 1
    xp_result = game.award_xp(profile, 3, "Chat message")
    game.bump_quest_progress(profile, "chat_count", amount=1)

    if result.get("corrections"):
        profile["corrections_seen"] += len(result["corrections"])

    newly = game.new_badges(profile)
    ui.save()
    ui.show_new_badges(newly)
    ui.show_level_up(xp_result)

    st.rerun()
