"""
Page: Settings & Export -- Claude API key, CEFR level, customize
theme/avatar, back up or restore progress as JSON, and manage profiles.
"""

import copy
import json
import streamlit as st
from core import ui, storage, gamification as game, ai_client

st.set_page_config(page_title="Réglages", page_icon="⚙️", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
db = st.session_state.db
name = st.session_state.active_profile

st.title("⚙️ Réglages & Export")

st.subheader("🤖 Tuteur IA (Claude)")
st.write("Ajoute une clé API Claude pour une conversation, des jeux de rôle et une histoire "
         "vraiment adaptatifs -- sans clé, l'app utilise un moteur hors-ligne plus limité mais "
         "gratuit et instantané.")
st.caption("Besoin d'une clé ? Crée-en une gratuitement sur "
           "[console.anthropic.com](https://console.anthropic.com/settings/keys) -- "
           "avec le modèle Haiku, quelques centimes couvrent des semaines de pratique quotidienne.")

current_key = ai_client.get_api_key()
key_col, model_col = st.columns([2, 1])
with key_col:
    key_input = st.text_input(
        "Clé API Claude (Anthropic)", value="", type="password",
        placeholder="sk-ant-..." if not current_key else "Une clé est déjà configurée (masquée)",
    )
with model_col:
    model_labels = list(ai_client.MODELS.keys())
    current_model = ai_client.get_model()
    default_idx = next((i for i, m in enumerate(ai_client.MODELS.values()) if m == current_model), 0)
    model_choice_label = st.selectbox("Modèle", model_labels, index=default_idx)
    model_choice = ai_client.MODELS[model_choice_label]

b1, b2, b3, b4 = st.columns(4)
if b1.button("💾 Utiliser pour cette session"):
    if key_input:
        st.session_state["api_key_override"] = key_input
    st.session_state["api_model_override"] = model_choice
    st.success("Configuré pour cette session (non sauvegardé sur le disque).")
    st.rerun()

if b2.button("📌 Sauvegarder sur cet appareil"):
    key_to_save = key_input or current_key
    if key_to_save:
        ai_client.save_key_to_device(key_to_save, model_choice)
        st.success("Clé sauvegardée localement dans data/ai_config.json (jamais partagée -- "
                    "voir .gitignore).")
        st.rerun()
    else:
        st.error("Entre d'abord une clé API.")

if b3.button("🔌 Tester la connexion"):
    if key_input:
        st.session_state["api_key_override"] = key_input
        st.session_state["api_model_override"] = model_choice
    ok, message = ai_client.test_connection()
    (st.success if ok else st.error)(message)

if b4.button("🗑️ Supprimer la clé"):
    ai_client.clear_saved_key()
    st.session_state.pop("api_key_override", None)
    st.session_state.pop("api_model_override", None)
    st.success("Clé supprimée. Retour au mode hors-ligne.")
    st.rerun()

st.caption(("🤖 IA activée -- modèle : " + ai_client.get_model()) if ai_client.is_configured()
           else "📴 Aucune clé configurée -- mode hors-ligne actif.")

st.divider()

st.subheader("💾 Stockage des données")
if storage.gist_configured():
    st.success("✅ Sauvegarde persistante activée (GitHub Gist) -- ta progression survit aux "
               "redémarrages de l'hébergement.")
else:
    st.info("📁 Stockage local uniquement pour l'instant. Si l'app est hébergée sur Streamlit "
            "Community Cloud, la progression peut être réinitialisée après un redémarrage -- voir "
            "DEPLOY_GUIDE.md (étape 4) pour activer une sauvegarde persistante gratuite via GitHub Gist.")
if st.session_state.get("_last_gist_error"):
    st.warning(f"⚠️ La dernière tentative de sauvegarde sur GitHub Gist a échoué : "
               f"{st.session_state['_last_gist_error']} -- tes données restent sûres localement en attendant.")

st.divider()

THEME_UNLOCK_LEVEL = {"Sunrise": 1, "Océan": 3, "Automne": 5, "Aurore": 10}
level = game.compute_level(profile["xp"])

st.subheader("🎨 Personnalisation")
c1, c2, c3 = st.columns(3)
with c1:
    CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1"]
    new_level = c1.selectbox(
        "Niveau CECR", CEFR_LEVELS,
        index=CEFR_LEVELS.index(profile["level"]) if profile["level"] in CEFR_LEVELS else 0,
    )
    if new_level != profile["level"]:
        profile["level"] = new_level
        ui.save()
        st.success("Niveau mis à jour !")

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
        st.caption("🔒 " + ", ".join(f"{a} (niveau {ui.AVATAR_UNLOCK_LEVEL[a]})" for a in locked_avatars))

with c3:
    unlocked_themes = [t for t, lvl in THEME_UNLOCK_LEVEL.items() if level >= lvl]
    new_theme = c3.selectbox("Thème de couleur", unlocked_themes,
                              index=unlocked_themes.index(profile["theme"]) if profile["theme"] in unlocked_themes else 0)
    if new_theme != profile["theme"]:
        profile["theme"] = new_theme
        ui.save()
        st.rerun()
    locked = [t for t in THEME_UNLOCK_LEVEL if t not in unlocked_themes]
    if locked:
        st.caption("🔒 " + ", ".join(f"{t} (niveau {THEME_UNLOCK_LEVEL[t]})" for t in locked))

st.divider()
st.subheader("💾 Sauvegarde & partage des données")
st.write("Toutes les données (tous les profils, XP, séries, badges...) sont dans un seul "
         "fichier JSON. Télécharge-le pour faire une sauvegarde, ou pour le transférer sur un autre ordinateur.")

col_a, col_b = st.columns(2)
with col_a:
    st.download_button(
        "⬇️ Télécharger la sauvegarde (JSON)",
        data=json.dumps(db, ensure_ascii=False, indent=2),
        file_name="famille_francais_sauvegarde.json",
        mime="application/json",
        width="stretch",
    )
with col_b:
    uploaded = st.file_uploader("⬆️ Restaurer depuis une sauvegarde", type=["json"])
    if uploaded is not None:
        if st.button("Confirmer la restauration (remplace les données actuelles)", type="primary"):
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
            st.success("Données restaurées ! Rechargement...")
            st.rerun()

st.divider()
st.subheader("🗑️ Zone danger")
with st.expander("Réinitialiser ou supprimer un profil"):
    target = st.selectbox("Profil concerné", list(db["profiles"].keys()), key="danger_target")
    dcol1, dcol2 = st.columns(2)
    if dcol1.button("Réinitialiser la progression de ce profil"):
        avatar = db["profiles"][target]["avatar"]
        level_cefr = db["profiles"][target]["level"]
        storage.create_profile(db, target, level_cefr, avatar)
        ui.save()
        st.success(f"Progression de {target} réinitialisée.")
        st.rerun()
    if dcol2.button("Supprimer ce profil définitivement", type="secondary"):
        if len(db["profiles"]) > 1:
            del db["profiles"][target]
            ui.save()
            st.session_state.active_profile = next(iter(db["profiles"]))
            st.success(f"Profil {target} supprimé.")
            st.rerun()
        else:
            st.error("Impossible de supprimer le dernier profil restant.")
