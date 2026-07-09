"""
Page: Roleplay Scenarios -- real-life dialogues (café, directions, market,
meeting a friend). When a Claude API key is configured, the tutor
improvises the scene live and in character; otherwise it falls back to a
scripted dialogue tree so the app still works offline.
"""

import streamlit as st
from core import ui, gamification as game, content_bank as cb, tutor_engine, ai_client

st.set_page_config(page_title="Jeux de rôle", page_icon="🎭", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
name = st.session_state.active_profile

st.title("🎭 Jeux de rôle")
st.caption("Vis une petite scène en français, comme si tu y étais vraiment.")

ai_mode = ai_client.is_configured()
with st.sidebar:
    st.markdown("---")
    st.success(f"🤖 Improvisation IA ({ai_client.get_model()})") if ai_mode else \
        st.warning("📴 Mode scénario scripté (aucune clé API)")

scenario_ids = list(cb.SCENARIOS.keys())
labels = [f"{cb.SCENARIOS[sid]['title']}  ({cb.SCENARIOS[sid]['cefr']})" for sid in scenario_ids]
choice = st.selectbox("Choisis une scène :", options=list(range(len(scenario_ids))),
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

    if st.button("🔄 Recommencer cette scène"):
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
                    st.markdown("**✏️ Petite remarque amicale :**")
                    for c in msg["corrections"]:
                        st.markdown(f"- *« {c['matched']} »* → **« {c['suggestion']} »**")
                        st.caption(c["explanation"])

    if st.session_state[ended_key]:
        st.success("✅ Scène terminée ! Choisis une autre scène ou recommence celle-ci.")
    else:
        user_reply = st.chat_input("Réponds dans la scène...")
        if user_reply:
            st.session_state[hist_key].append({"role": "user", "content": user_reply})
            plain_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state[hist_key][:-1]]
            try:
                result = tutor_engine.respond_roleplay_ai(scenario, user_reply, profile["level"], name, plain_history)
                st.session_state[hist_key].append({
                    "role": "assistant", "content": result["reply"],
                    "hint_en": result.get("hint_en"), "corrections": result["corrections"],
                })
                xp_result = game.award_xp(profile, 10, f"Jeu de rôle (IA) : {scenario['title']}")
                if result["corrections"]:
                    profile["corrections_seen"] += len(result["corrections"])
                if result["scene_ended"]:
                    st.session_state[ended_key] = True
                    game.award_xp(profile, 15, f"Scène terminée : {scenario['title']}")
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
                st.warning("L'IA n'a pas pu répondre cette fois -- réessaie dans un instant.")
                with st.expander("Détail technique"):
                    st.code(str(e))

# ===========================================================================
# OFFLINE SCRIPTED FALLBACK (dialogue tree)
# ===========================================================================
else:
    node_key = f"scenario_node_{name}_{scenario_id}"
    if node_key not in st.session_state:
        st.session_state[node_key] = scenario["start"]

    if st.button("🔄 Recommencer cette scène"):
        st.session_state[node_key] = scenario["start"]
        st.rerun()

    current_node_id = st.session_state[node_key]

    if current_node_id is None:
        st.success("✅ Scène terminée ! Choisis une autre scène ou reviens plus tard pour une nouvelle histoire.")
        st.stop()

    node = scenario["nodes"][current_node_id]

    with st.chat_message("assistant", avatar="🇫🇷"):
        st.markdown(f"### {node['bot_fr']}")
        st.caption(f"💭 {node['bot_en']}")

    if node["examples"]:
        with st.expander("💡 Besoin d'idées ? Exemples de réponses"):
            for ex in node["examples"]:
                st.markdown(f"- *{ex}*")

    if node["keywords"]:
        user_reply = st.chat_input("Réponds dans la scène...")
        if user_reply:
            matched = any(kw.lower() in user_reply.lower() for kw in node["keywords"])
            if matched:
                game.award_xp(profile, node["xp"], f"Jeu de rôle : {scenario['title']}")
                st.session_state[node_key] = node["next"]
                if node["next"] is None:
                    if scenario_id not in profile["scenarios_completed"]:
                        profile["scenarios_completed"].append(scenario_id)
                    game.bump_quest_progress(profile, "scenario", target_value=scenario_id)
                    game.bump_quest_progress(profile, "scenario_count", target_value=scenario_id)
                newly = game.new_badges(profile)
                ui.save()
                st.toast(f"+{node['xp']} XP !", icon="✨")
                st.rerun()
            else:
                st.warning("Presque ! Essaie d'utiliser un des mots suggérés ci-dessus, ou clique "
                           "« Continuer quand même » si tu veux avancer.")
                if st.button("Continuer quand même ➡️"):
                    st.session_state[node_key] = node["next"]
                    ui.save()
                    st.rerun()
    else:
        if st.button("Terminer la scène 🎉"):
            result = game.award_xp(profile, node["xp"], f"Jeu de rôle terminé : {scenario['title']}")
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
