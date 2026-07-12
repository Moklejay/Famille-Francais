"""
Page: Settings & Export -- Claude API key, CEFR level, customize
theme/avatar, back up or restore progress as JSON, and manage profiles.
"""

import copy
import json
import streamlit as st
from core import ui, storage, gamification as game, ai_client

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
db = st.session_state.db
name = st.session_state.active_profile

st.title("⚙️ Settings & Export")

st.subheader("🤖 AI Tutor (Claude)")
st.write("Add a Claude API key for truly adaptive conversation, role-play, and story "
         "-- without a key, the app uses a more limited but free and instant offline engine.")
st.caption("Need a key? Create one for free at "
           "[console.anthropic.com](https://console.anthropic.com/settings/keys) -- "
           "with the Haiku model, a few cents covers weeks of daily practice.")

current_key = ai_client.get_api_key()
key_col, model_col = st.columns([2, 1])
with key_col:
    key_input = st.text_input(
        "Claude API Key (Anthropic)", value="", type="password",
        placeholder="sk-ant-..." if not current_key else "A key is already configured (hidden)",
    )
with model_col:
    model_labels = list(ai_client.MODELS.keys())
    current_model = ai_client.get_model()
    default_idx = next((i for i, m in enumerate(ai_client.MODELS.values()) if m == current_model), 0)
    model_choice_label = st.selectbox("Model", model_labels, index=default_idx)
    model_choice = ai_client.MODELS[model_choice_label]

b1, b2, b3, b4 = st.columns(4)
if b1.button("💾 Use for this session"):
    if key_input:
        st.session_state["api_key_override"] = key_input
    st.session_state["api_model_override"] = model_choice
    st.success("Configured for this session (not saved to disk).")
    st.rerun()

if b2.button("📌 Save on this device"):
    key_to_save = key_input or current_key
    if key_to_save:
        ai_client.save_key_to_device(key_to_save, model_choice)
        st.success("Key saved locally to data/ai_config.json (never shared -- "
                    "see .gitignore).")
        st.rerun()
    else:
        st.error("Enter an API key first.")

if b3.button("🔌 Test connection"):
    if key_input:
        st.session_state["api_key_override"] = key_input
        st.session_state["api_model_override"] = model_choice
    ok, message = ai_client.test_connection()
    (st.success if ok else st.error)(message)

if b4.button("🗑️ Remove key"):
    ai_client.clear_saved_key()
    st.session_state.pop("api_key_override", None)
    st.session_state.pop("api_model_override", None)
    st.success("Key removed. Back to offline mode.")
    st.rerun()

st.caption(("🤖 AI enabled -- model: " + ai_client.get_model()) if ai_client.is_configured()
           else "📴 No key configured -- offline mode active.")

st.divider()

st.subheader("💾 Data storage")
if storage.gist_configured():
    st.success("✅ Persistent backup enabled (GitHub Gist) -- your progress survives "
               "hosting restarts.")
else:
    st.info("📁 Local storage only for now. If the app is hosted on Streamlit "
            "Community Cloud, progress may reset after a restart -- see "
            "DEPLOY_GUIDE.md (step 4) to enable free persistent backup via GitHub Gist.")
if st.session_state.get("_last_gist_error"):
    st.warning(f"⚠️ The last attempt to back up to GitHub Gist failed: "
               f"{st.session_state['_last_gist_error']} -- your data is still safe locally in the meantime.")

st.divider()

THEME_UNLOCK_LEVEL = {"Sunrise": 1, "Ocean": 3, "Autumn": 5, "Aurora": 10}
level = game.compute_level(profile["xp"])

st.subheader("🎨 Customization")
c1, c2, c3 = st.columns(3)
with c1:
    CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1"]
    new_level = c1.selectbox(
        "CEFR level", CEFR_LEVELS,
        index=CEFR_LEVELS.index(profile["level"]) if profile["level"] in CEFR_LEVELS else 0,
    )
    if new_level != profile["level"]:
        profile["level"] = new_level
        ui.save()
        st.success("Level updated!")

with c2:
    unlocked_avatars = ui.avatars_unlocked_at(level)
    new_avatar = c2.selectbox(
        "Avatar", unlocked_avatars,
        index=unlocked_avatars.index(profile["avatar"]) if profile["avatar"] in unlocked_avatars else 0,
    )
    if new_avatar != profile["avatar"]:
        profile["avatar"] = new_avatar
        ui.save()
        st.rerun()
    locked_avatars = [a for a in ui.AVATARS if a not in unlocked_avatars]
    if locked_avatars:
        st.caption("🔒 " + ", ".join(f"{a} (level {ui.AVATAR_UNLOCK_LEVEL[a]})" for a in locked_avatars))

with c3:
    unlocked_themes = [t for t, lvl in THEME_UNLOCK_LEVEL.items() if level >= lvl]
    new_theme = c3.selectbox("Color theme", unlocked_themes,
                              index=unlocked_themes.index(profile["theme"]) if profile["theme"] in unlocked_themes else 0)
    if new_theme != profile["theme"]:
        profile["theme"] = new_theme
        ui.save()
        st.rerun()
    locked = [t for t in THEME_UNLOCK_LEVEL if t not in unlocked_themes]
    if locked:
        st.caption("🔒 " + ", ".join(f"{t} (level {THEME_UNLOCK_LEVEL[t]})" for t in locked))

st.divider()
st.subheader("💾 Backup & data export")
st.write("All data (every profile, XP, streaks, badges...) lives in a single "
         "JSON file. Download it to make a backup, or to move it to another computer.")

col_a, col_b = st.columns(2)
with col_a:
    st.download_button(
        "⬇️ Download backup (JSON)",
        data=json.dumps(db, ensure_ascii=False, indent=2),
        file_name="famille_francais_backup.json",
        mime="application/json",
        width="stretch",
    )
with col_b:
    uploaded = st.file_uploader("⬆️ Restore from a backup", type=["json"])
    if uploaded is not None:
        if st.button("Confirm restore (replaces current data)", type="primary"):
            new_db = json.load(uploaded)
            for k, v in storage.DEFAULT_DB.items():
                # NOTE: must deepcopy the default -- storage.DEFAULT_DB["profiles"]
                # is a mutable {} template shared at module scope. A plain
                # setdefault(k, v) would alias new_db["profiles"] directly to
                # that shared dict whenever a backup file is missing the key
                # (e.g. a hand-edited or malformed restore), so any later
                # profile creation/deletion would silently corrupt the
                # module-level template for every future fresh install in
                # this same running process.
                new_db.setdefault(k, copy.deepcopy(v))
            st.session_state.db = new_db
            # Reset the merge-diff baseline to match the restored data too --
            # otherwise a later save() in this same browser session would
            # diff against the stale pre-restore snapshot (harmless, but
            # would cause redundant/confusing merge behavior).
            st.session_state.db_snapshot = copy.deepcopy(new_db)
            storage.save_db(new_db)
            st.success("Data restored! Reloading...")
            st.rerun()

st.divider()
st.subheader("🗑️ Danger zone")
with st.expander("Reset or delete a profile"):
    target = st.selectbox("Profile", list(db["profiles"].keys()), key="danger_target")
    dcol1, dcol2 = st.columns(2)
    if dcol1.button("Reset this profile's progress"):
        avatar = db["profiles"][target]["avatar"]
        level_cefr = db["profiles"][target]["level"]
        storage.create_profile(db, target, level_cefr, avatar)
        ui.save()
        st.success(f"{target}'s progress has been reset.")
        st.rerun()
    if dcol2.button("Delete this profile permanently", type="secondary"):
        if len(db["profiles"]) > 1:
            del db["profiles"][target]
            ui.save()
            st.session_state.active_profile = next(iter(db["profiles"]))
            st.success(f"Profile {target} deleted.")
            st.rerun()
        else:
            st.error("Can't delete the last remaining profile.")
