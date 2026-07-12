"""
Page: Settings & Export
Duolingo + Spotify Fusion Design
"""

import json
import os
from datetime import date
import streamlit as st
from core import ui, storage, ai_client, gamification as game, content_bank as cb

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
db = st.session_state.db

st.title("⚙️ Settings & Export")

# ============================================================
# PROFILE SETTINGS CARD
# ============================================================

st.subheader("👤 Profile Settings")
with st.container():
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"<div style='font-size: 5rem; text-align: center;'>{profile['avatar']}</div>", unsafe_allow_html=True)
        new_avatar = st.selectbox(
            "Change avatar",
            ui.avatars_unlocked_at(game.compute_level(profile["xp"])),
            index=ui.avatars_unlocked_at(game.compute_level(profile["xp"])).index(profile["avatar"]) if profile["avatar"] in ui.avatars_unlocked_at(game.compute_level(profile["xp"])) else 0
        )
    with col2:
        new_name = st.text_input("Display name", value=st.session_state.active_profile)
        new_level = st.selectbox("CEFR Level", ["A1", "A2", "B1", "B2", "C1"], index=["A1", "A2", "B1", "B2", "C1"].index(profile["level"]))
        new_theme = st.selectbox("Color Theme", list(ui.THEMES.keys()), index=list(ui.THEMES.keys()).index(profile.get("theme", "Neon Green")))

    if st.button("💾 Save Profile", type="primary", use_container_width=True):
        old_name = st.session_state.active_profile
        if new_name.strip() and new_name.strip() != old_name:
            if new_name.strip() not in db["profiles"]:
                db["profiles"][new_name.strip()] = db["profiles"].pop(old_name)
                st.session_state.active_profile = new_name.strip()
            else:
                st.error("That name is already taken!")
                st.stop()
        profile = db["profiles"][st.session_state.active_profile]
        profile["avatar"] = new_avatar
        profile["level"] = new_level
        profile["theme"] = new_theme
        ui.save()
        st.success("Profile updated! 🎉")
        st.rerun()

st.divider()

# ============================================================
# AI API KEY CARD
# ============================================================

st.subheader("🤖 AI Tutor Settings")
with st.container():
    st.caption("Add your Claude API key for adaptive AI conversation, role-play, and storytelling.")

    current_key = ai_client.get_api_key()
    current_model = ai_client.get_model()
    key_source = ai_client.key_source()

    if current_key:
        st.markdown(f"""
        <div style="background: #181818; border: 2px solid rgba(88,204,2,0.3); border-radius: 16px; padding: 16px; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <div style="font-size: 1.5rem;">✅</div>
                <div style="font-family: 'Nunito', sans-serif; font-weight: 800; color: #58CC02;">AI is active</div>
            </div>
            <div style="color: #A7A7A7; font-size: 0.9rem;">
                Model: <strong>{current_model}</strong><br>
                Key source: {key_source}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: #181818; border: 2px solid rgba(255,150,0,0.3); border-radius: 16px; padding: 16px; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <div style="font-size: 1.5rem;">📴</div>
                <div style="font-family: 'Nunito', sans-serif; font-weight: 800; color: #FF9600;">Offline mode</div>
            </div>
            <div style="color: #A7A7A7; font-size: 0.9rem;">
                The app works without a key using rule-based responses. Add a key for adaptive AI.
            </div>
        </div>
        """, unsafe_allow_html=True)

    api_key = st.text_input("Claude API Key", value=current_key or "", type="password", placeholder="sk-ant-...")
    model = st.selectbox("Model", list(ai_client.MODELS.keys()), index=list(ai_client.MODELS.keys()).index(next((k for k, v in ai_client.MODELS.items() if v == current_model), list(ai_client.MODELS.keys())[0])))

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save to Device", use_container_width=True):
            if api_key.strip():
                ai_client.save_key_to_device(api_key.strip(), ai_client.MODELS[model])
                st.success("Key saved! ✅")
                st.rerun()
            else:
                st.error("Enter a key first.")
    with col2:
        if st.button("🧪 Test Connection", use_container_width=True):
            if api_key.strip():
                st.session_state["api_key_override"] = api_key.strip()
                st.session_state["api_model_override"] = ai_client.MODELS[model]
                ok, msg = ai_client.test_connection()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.error("Enter a key to test.")
    with col3:
        if st.button("🗑️ Clear Saved Key", use_container_width=True):
            ai_client.clear_saved_key()
            st.session_state.pop("api_key_override", None)
            st.success("Key cleared! ✅")
            st.rerun()

st.divider()

# ============================================================
# BACKUP / EXPORT CARD
# ============================================================

st.subheader("💾 Backup & Export")
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Download Backup", use_container_width=True):
            backup_json = json.dumps(db, ensure_ascii=False, indent=2)
            st.download_button(
                "Click to download",
                backup_json,
                file_name=f"famille_francais_backup_{date.today().isoformat()}.json",
                mime="application/json",
                use_container_width=True
            )
    with col2:
        uploaded = st.file_uploader("📤 Restore from Backup", type="json")
        if uploaded:
            try:
                restored = json.loads(uploaded.read().decode("utf-8"))
                if "profiles" in restored:
                    db["profiles"] = restored["profiles"]
                    ui.save()
                    st.success("Backup restored! 🎉")
                    st.rerun()
                else:
                    st.error("Invalid backup file.")
            except Exception as e:
                st.error(f"Error: {e}")

    # Gist status
    if storage.gist_configured():
        st.markdown("""
        <div style="background: #181818; border: 2px solid rgba(88,204,2,0.2); border-radius: 12px; padding: 12px; margin-top: 12px;">
            <span style="color: #58CC02;">✅</span> Persistent backup enabled (GitHub Gist)
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: #181818; border: 2px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 12px; margin-top: 12px;">
            <span style="color: #A7A7A7;">💡</span> For hosted deployment, add GITHUB_TOKEN and GIST_ID to Streamlit secrets for persistent backup.
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ============================================================
# DANGER ZONE
# ============================================================

st.subheader("⚠️ Danger Zone")
with st.expander("Delete this profile"):
    st.warning("This cannot be undone!")
    confirm = st.text_input(f'Type "{st.session_state.active_profile}" to confirm deletion')
    if st.button("🗑️ Delete Profile", type="primary"):
        if confirm == st.session_state.active_profile:
            del db["profiles"][st.session_state.active_profile]
            ui.save()
            st.session_state.active_profile = None
            st.success("Profile deleted.")
            st.rerun()
        else:
            st.error("Name doesn't match.")
