"""
Page: Roleplay Scenarios -- real-life dialogues (café, directions, market,
meeting a friend). When a Claude API key is configured, the tutor
improvises the scene live and in character; otherwise it falls back to a
scripted dialogue tree so the app still works offline.
"""

import streamlit as st
from core import ui, gamification as game, content_bank as cb, tutor_engine, ai_client

st.set_page_config(page_title="Role-play", page_icon="🎭", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
name = st.session_state.active_profile

st.title("🎭 Role-play")
st.caption("Live out a little scene in French, as if you were really there.")

ai_mode = ai_client.is_configured()
with st.sidebar:
    st.markdown("---")
    st.success(f"🤖 AI improv ({ai_client.get_model()})") if ai_mode else \
        st.warning("📴 Scripted scenario mode (no API key)")

scenario_ids = list(cb.SCENARIOS.keys())
labels = [f"{cb.SCENARIOS[sid]['title']}  ({cb.SCENARIOS[sid]['cefr']})" for sid in scenario_ids]
choice = st.selectbox("Choose a scene:", options=list(range(len(scenario_ids))),
                       format_func=lambda i: labels[i])
scenario_id = scenario_ids[choice]
scenario = cb.SCENARIOS[scenario_id]
st.info(scenario["description"])

# ===========================================================================
# AI-DRIVEN MODE
# ===========================================================================
if ai_mode:
    hist_key = f"roleplay_ai_hist_{name}_{scenario_id}"
    ended_key = f"roleplay_ai_ended_{name}_{scenario_id}"

    if hist_key not in st.session_state:
        opening = scenario["nodes"][scenario["start"]]["bot_fr"]
        st.session_state[hist_key] = [{"role": "assistant", "content": opening}]
        st.session_state[ended_key] = False

    if st.button("🔄 Restart this scene"):
        opening = scenario["nodes"][scenario["start"]]["bot_fr"]
        st.session_state[hist_key] = [{"role": "assistant", "content": opening}]
        st.session_state[ended_key] = False
        st.rerun()

    for msg in st.session_state[hist_key]:
        with st.chat_message(msg["role"], avatar=(profile["avatar"] if msg["role"] == "user" else "🇫🇷")):
            st.markdown(msg["content"])
            if msg.get("hint_en"):
                st.caption(f"💭 {msg['hint_en']}")
            if msg.get("corrections"):
                with st.container(border=True):
                    st.markdown("**✏️ Friendly note:**")
                    for c in msg["corrections"]:
                        st.markdown(f"- *« {c['matched']} »* → **« {c['suggestion']} »**")
                        st.caption(c["explanation"])

    if st.session_state[ended_key]:
        st.success("✅ Scene complete! Pick another scene or restart this one.")
    else:
        user_reply = st.chat_input("Reply in the scene...")
        if user_reply:
            st.session_state[hist_key].append({"role": "user", "content": user_reply})
            plain_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state[hist_key][:-1]]
            try:
                result = tutor_engine.respond_roleplay_ai(scenario, user_reply, profile["level"], name, plain_history)
                st.session_state[hist_key].append({
                    "role": "assistant", "content": result["reply"],
                    "hint_en": result.get("hint_en"), "corrections": result["corrections"],
                })
                xp_result = game.award_xp(profile, 10, f"Role-play (AI): {scenario['title']}")
                if result["corrections"]:
                    profile["corrections_seen"] += len(result["corrections"])
                if result["scene_ended"]:
                    st.session_state[ended_key] = True
                    game.award_xp(profile, 15, f"Scene completed: {scenario['title']}")
                    if scenario_id not in profile["scenarios_completed"]:
                        profile["scenarios_completed"].append(scenario_id)
                    game.bump_quest_progress(profile, "scenario", target_value=scenario_id)
                    game.bump_quest_progress(profile, "scenario_count", target_value=scenario_id)
                newly = game.new_badges(profile)
                ui.save()
                ui.show_new_badges(newly)
                st.rerun()
            except RuntimeError as e:
                st.session_state[hist_key].pop()  # remove the unanswered user turn
                st.warning("The AI couldn't respond this time -- try again in a moment.")
                with st.expander("Technical detail"):
                    st.code(str(e))

# ===========================================================================
# OFFLINE SCRIPTED FALLBACK (dialogue tree)
# ===========================================================================
else:
    node_key = f"scenario_node_{name}_{scenario_id}"
    if node_key not in st.session_state:
        st.session_state[node_key] = scenario["start"]

    if st.button("🔄 Restart this scene"):
        st.session_state[node_key] = scenario["start"]
        st.rerun()

    current_node_id = st.session_state[node_key]

    if current_node_id is None:
        st.success("✅ Scene complete! Pick another scene, or come back later for a new one.")
        st.stop()

    node = scenario["nodes"][current_node_id]

    with st.chat_message("assistant", avatar="🇫🇷"):
        st.markdown(f"### {node['bot_fr']}")
        st.caption(f"💭 {node['bot_en']}")

    if node["examples"]:
        with st.expander("💡 Need ideas? Example replies"):
            for ex in node["examples"]:
                st.markdown(f"- *{ex}*")

    if node["keywords"]:
        user_reply = st.chat_input("Reply in the scene...")
        if user_reply:
            matched = any(kw.lower() in user_reply.lower() for kw in node["keywords"])
            if matched:
                game.award_xp(profile, node["xp"], f"Role-play: {scenario['title']}")
                st.session_state[node_key] = node["next"]
                if node["next"] is None:
                    if scenario_id not in profile["scenarios_completed"]:
                        profile["scenarios_completed"].append(scenario_id)
                    game.bump_quest_progress(profile, "scenario", target_value=scenario_id)
                    game.bump_quest_progress(profile, "scenario_count", target_value=scenario_id)
                newly = game.new_badges(profile)
                ui.save()
                st.toast(f"+{node['xp']} XP!", icon="✨")
                st.rerun()
            else:
                st.warning("Almost! Try using one of the suggested words above, or click "
                           "\"Continue anyway\" if you want to move on.")
                if st.button("Continue anyway ➡️"):
                    st.session_state[node_key] = node["next"]
                    ui.save()
                    st.rerun()
    else:
        if st.button("Finish the scene 🎉"):
            result = game.award_xp(profile, node["xp"], f"Role-play completed: {scenario['title']}")
            if scenario_id not in profile["scenarios_completed"]:
                profile["scenarios_completed"].append(scenario_id)
            game.bump_quest_progress(profile, "scenario", target_value=scenario_id)
            game.bump_quest_progress(profile, "scenario_count", target_value=scenario_id)
            newly = game.new_badges(profile)
            st.session_state[node_key] = None
            ui.save()
            ui.show_level_up(result)
            ui.show_new_badges(newly)
            st.rerun()
