"""
Page: Roleplay Scenarios -- practice French in real-life situations.
PREMIUM EDITION — Duolingo + Spotify Fusion
"""

import streamlit as st
from core import ui, gamification as game, content_bank as cb, tutor_engine, ai_client, voice

st.set_page_config(page_title="Roleplay Scenarios", page_icon="🎭", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
name = st.session_state.active_profile

# ============================================================
# HERO HEADER
# ============================================================
st.markdown(f"""
<div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
    <div style="font-size: 2.5rem; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));">🎭</div>
    <div>
        <h1 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 900; font-size: 2rem;">
            Roleplay Scenarios
        </h1>
        <p style="margin: 4px 0 0; color: #9A9AAF; font-size: 1rem;">
            Practice real-life French conversations — café, directions, market, and more
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)

# AI status
ai_mode = ai_client.is_configured()
with st.sidebar:
    st.markdown("---")
    if ai_mode:
        st.success(f"🤖 Adaptive AI roleplay ({ai_client.get_model()})")
    else:
        st.warning("📴 Scripted mode (no API key)")

# ============================================================
# SCENARIO SELECTION — Premium cards
# ============================================================
st.subheader("Choose a scenario")

scenario_ids = list(cb.SCENARIOS.keys())
completed = set(profile.get("scenarios_completed", []))

cols = st.columns(len(scenario_ids))
for i, sid in enumerate(scenario_ids):
    sc = cb.SCENARIOS[sid]
    is_done = sid in completed
    with cols[i]:
        st.markdown(f"""
        <div class="activity-card" style="padding: 24px 18px; min-height: 200px;">
            <div class="icon" style="font-size: 2.5rem; margin-bottom: 12px;">
                {'✅' if is_done else '🎭'}
            </div>
            <h3 style="font-size: 1.1rem; margin-bottom: 6px;">{sc['title']}</h3>
            <p style="font-size: 0.85rem; color: #9A9AAF; margin-bottom: 8px;">{sc['description']}</p>
            <div style="display: inline-block; padding: 4px 12px; border-radius: 999px; 
                background: {'#58CC0220' if is_done else '#1A1A24'}; 
                border: 1px solid {'#58CC0240' if is_done else 'rgba(255,255,255,0.08)'};
                color: {'#58CC02' if is_done else '#9A9AAF'}; font-size: 0.75rem; font-weight: 700;">
                {sc['cefr']} {'• Completed' if is_done else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

choice = st.selectbox(
    "Select scenario to play:",
    options=scenario_ids,
    format_func=lambda s: f"{'✅ ' if s in completed else ''}{cb.SCENARIOS[s]['title']}",
    key="scenario_select"
)

scenario = cb.SCENARIOS[choice]
node_key = f"rp_node_{name}_{choice}"
history_key = f"rp_history_{name}_{choice}"

if node_key not in st.session_state:
    st.session_state[node_key] = scenario["start"]
if history_key not in st.session_state:
    st.session_state[history_key] = []

current_node_id = st.session_state[node_key]
history = st.session_state[history_key]

st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)

# ============================================================
# SCENARIO PLAY AREA
# ============================================================
st.subheader(f"🎭 {scenario['title']}")

# Voice toggle for this scenario
conv_on = voice.conversation_toggle(f"conv_mode_rp_{name}_{choice}")

if st.button("🔄 Restart this scenario", key=f"rp_restart_{choice}"):
    st.session_state[node_key] = scenario["start"]
    st.session_state[history_key] = []
    ui.save()
    st.rerun()

st.markdown("---")

# Show conversation history
for i, entry in enumerate(history):
    if entry["role"] == "bot":
        with st.chat_message("assistant", avatar="🎭"):
            st.markdown(entry["text"])
            voice.speak_button(entry["text"], key=f"rp_speak_{name}_{choice}_{i}")
            if entry.get("hint_en"):
                st.caption(f"💡 {entry['hint_en']}")
            if entry.get("corrections"):
                with st.container(border=True):
                    st.markdown("**✏️ Friendly corrections:**")
                    for c in entry["corrections"]:
                        st.markdown(f"- *« {c['matched']} »* → **« {c['suggestion']} »**")
                        st.caption(c["explanation"])
    else:
        with st.chat_message("user", avatar=profile["avatar"]):
            st.markdown(entry["text"])

# Current node
if current_node_id is None:
    # Scenario complete
    if choice not in completed:
        profile["scenarios_completed"].append(choice)
        result = game.award_xp(profile, 15, f"Roleplay: {scenario['title']}")
        game.bump_quest_progress(profile, "scenario", target_value=choice)
        game.bump_quest_progress(profile, "scenario_count", target_value=choice)
        newly = game.new_badges(profile)
        ui.save()
        ui.show_level_up(result)
        ui.show_new_badges(newly)

    st.success("🎉 Scenario complete! Great job!")
    st.balloons()
    st.stop()

node = scenario["nodes"][current_node_id]

# Show bot message
with st.chat_message("assistant", avatar="🎭"):
    st.markdown(node["bot_fr"])
    voice.speak_button(node["bot_fr"], key=f"rp_current_{name}_{choice}")
    if node.get("bot_en"):
        st.caption(f"💡 {node['bot_en']}")

# Examples
if node.get("examples"):
    with st.expander("💡 Need help? Show examples"):
        for ex in node["examples"]:
            st.markdown(f"- *{ex}*")

# Input
mic_text = None
if conv_on:
    if voice.conversation_gate(f"rp_conv_{name}_{choice}"):
        voice.conversation_loop(
            turn_id=str(len(history)),
            conv_key=f"rp_conv_{name}_{choice}",
            speak_text=node["bot_fr"],
        )
else:
    mic_col, _ = st.columns([1, 8])
    with mic_col:
        mic_text = voice.mic_input(f"rp_mic_{name}_{choice}") if voice.mic_available() else None

user_input = mic_text or st.chat_input("Your reply in French...")

if user_input:
    # Add to history
    st.session_state[history_key].append({"role": "user", "text": user_input})

    # Check keywords for progression
    matched = False
    for kw in node.get("keywords", []):
        if kw.lower() in user_input.lower():
            matched = True
            break

    # AI or rule-based response
    if ai_mode:
        try:
            plain_history = [{"role": m["role"].replace("bot", "assistant"), "content": m["text"]} 
                           for m in history[-8:]]
            result = tutor_engine.respond_roleplay_ai(
                scenario, user_input, profile["level"], name, plain_history
            )
            bot_reply = result["reply"]
            hint = result.get("hint_en")
            corrections = result.get("corrections", [])
            scene_ended = result.get("scene_ended", False)
        except Exception as e:
            bot_reply = node["bot_fr"]
            hint = None
            corrections = []
            scene_ended = False
            st.warning(f"AI mode failed, using scripted fallback: {e}")
    else:
        # Scripted fallback
        if matched or len(user_input.split()) >= 2:
            bot_reply = "Très bien ! Continuez..."
            hint = None
            corrections = []
            scene_ended = False
        else:
            bot_reply = "Je n'ai pas compris. Essayez encore !"
            hint = "I didn't understand. Try again!"
            corrections = []
            scene_ended = False

    st.session_state[history_key].append({
        "role": "bot",
        "text": bot_reply,
        "hint_en": hint,
        "corrections": corrections,
    })

    # Advance node
    if matched or (ai_mode and not scene_ended):
        st.session_state[node_key] = node.get("next")
    elif scene_ended:
        st.session_state[node_key] = None  # End scenario

    # XP
    xp_result = game.award_xp(profile, node.get("xp", 8), f"Roleplay: {scenario['title']}")
    profile["messages_sent"] += 1
    newly = game.new_badges(profile)
    ui.save()
    ui.show_new_badges(newly)
    ui.show_level_up(xp_result)

    st.rerun()
