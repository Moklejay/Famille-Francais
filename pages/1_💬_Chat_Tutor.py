"""
Page: Chat Tutor -- free-form conversation with the French tutor. Uses
real Claude API conversation when a key is configured (Settings page),
and transparently falls back to the offline rule-based engine otherwise.
"""

from datetime import date
import streamlit as st
from core import ui, gamification as game, tutor_engine, content_bank as cb, ai_client, voice

st.set_page_config(page_title="Chat Tutor", page_icon="💬", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
name = st.session_state.active_profile

st.title("💬 Chat Tutor")
st.caption("Answer however you can -- what matters is trying!")
conv_on = voice.conversation_toggle(f"conv_mode_chat_{name}")
if conv_on:
    st.caption("🎙️ Conversation mode is on -- just talk, pause when you're done, and the tutor will answer out loud.")
else:
    st.caption("Type, or turn on conversation mode above to talk hands-free.")

with st.sidebar:
    st.markdown("---")
    if ai_client.is_configured():
        st.success(f"🤖 AI enabled ({ai_client.get_model()})")
    else:
        st.warning("📴 Offline mode (no API key)")
        st.caption("Add a key in **Settings** for truly adaptive conversation.")
    st.markdown("### 💡 Grammar tip of the day")
    tips = cb.GRAMMAR_TIPS.get(profile["level"], cb.GRAMMAR_TIPS["A1"])
    tip_title, tip_body = tips[date.today().toordinal() % len(tips)]
    st.markdown(f"**{tip_title}**")
    st.caption(tip_body)

hist_key = f"chat_history_{name}"
last_prompt_key = f"last_prompt_{name}"
celebration_key = f"celebration_{name}"

if hist_key not in st.session_state:
    opening = tutor_engine.opening_line(profile["level"], name)
    st.session_state[hist_key] = [{"role": "assistant", "content": opening}]
    st.session_state[last_prompt_key] = opening

# Show any celebration queued from the previous turn (level-up, badge, quest)
pending = st.session_state.pop(celebration_key, None)
if pending:
    if pending.get("ai_error"):
        st.info("ℹ️ The AI didn't respond this time (see details below) -- offline reply used instead.")
        with st.expander("Technical detail"):
            st.code(pending["ai_error"])
    ui.show_level_up(pending["xp_result"])
    ui.show_new_badges(pending["newly"])
    for q in pending["quests"]:
        st.success(f"🎯 Quest completed: **{q['title']}**! +{q['xp']} XP, +{q['coins']} coins.")

for i, msg in enumerate(st.session_state[hist_key]):
    with st.chat_message(msg["role"], avatar=(profile["avatar"] if msg["role"] == "user" else "🇫🇷")):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            voice.speak_button(msg["content"], key=f"chat_tutor_{name}_{i}")
        if msg.get("hint_en"):
            st.caption(f"💭 {msg['hint_en']}")
        if msg.get("new_vocab"):
            st.caption("🆕 " + " • ".join(f"**{v['fr']}** ({v['en']})" for v in msg["new_vocab"]))
        if msg.get("corrections"):
            with st.container(border=True):
                st.markdown("**✏️ Friendly note:**")
                for c in msg["corrections"]:
                    st.markdown(f"- You wrote *« {c['matched']} »* → it's more natural as **« {c['suggestion']} »**")
                    st.caption(c["explanation"])

if conv_on:
    last_msg = st.session_state[hist_key][-1]
    speak_text = last_msg["content"] if last_msg["role"] == "assistant" else None
    voice.conversation_loop(
        turn_id=str(len(st.session_state[hist_key])),
        conv_key=f"chat_tutor_{name}",
        speak_text=speak_text,
    )
else:
    mic_col, _ = st.columns([1, 8])
    with mic_col:
        mic_text = voice.mic_input(f"chat_tutor_mic_{name}") if voice.mic_available() else None

user_text = (mic_text if not conv_on else None) or st.chat_input("Write your reply in French...")

if user_text:
    st.session_state[hist_key].append({"role": "user", "content": user_text})

    # Plain-text history (no metadata) for the AI's conversational context
    plain_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state[hist_key][:-1]]

    result = tutor_engine.respond(
        user_text, profile["level"], name=name, history=plain_history,
        last_prompt=st.session_state.get(last_prompt_key),
    )

    profile["messages_sent"] += 1
    xp_result = game.award_xp(profile, 3, "Message sent in Chat")
    quest_done = game.bump_quest_progress(profile, "chat_count", amount=1)

    if result["corrections"]:
        profile["corrections_seen"] += len(result["corrections"])

    st.session_state[hist_key].append({
        "role": "assistant", "content": result["reply"],
        "hint_en": result.get("hint_en"), "corrections": result["corrections"],
        "new_vocab": result.get("new_vocab", []),
    })
    st.session_state[last_prompt_key] = result["reply"]

    newly = game.new_badges(profile)
    st.session_state[celebration_key] = {
        "xp_result": xp_result, "newly": newly, "quests": quest_done,
        "ai_error": result.get("ai_error"),
    }
    ui.save()
    st.rerun()
