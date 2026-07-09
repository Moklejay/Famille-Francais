"""
ai_client.py
-------------
Thin wrapper around the Claude API (Anthropic) for real, adaptive French
conversation. Everything else in this app (gamification, SRS, storage)
works with zero external calls -- only this module talks to the network,
and only once you've supplied an API key.

Key storage, in order of priority:
  1. st.session_state["api_key_override"]  -- set for this browser session only
     (e.g. pasted in Settings but not saved to disk).
  2. data/ai_config.json -- saved locally on YOUR machine if you click
     "Save key on this device" in Settings. This file is gitignored --
     never commit it or push it to a public repo.
  3. st.secrets["ANTHROPIC_API_KEY"] -- used automatically when deployed on
     Streamlit Community Cloud with a Secret configured in the app's
     dashboard (Settings -> Secrets). This is the recommended way to set
     the key for a hosted/shared deployment.
  4. ANTHROPIC_API_KEY environment variable -- useful for other hosting
     setups, or if you prefer not to store it in a file.

If no key is configured anywhere, every function here returns cleanly
with `configured=False` so the rest of the app can fall back to the
offline, rule-based engine without crashing.
"""

from __future__ import annotations
import json
import os
import re

try:
    import streamlit as st
except ImportError:  # allows unit-testing this module without a Streamlit runtime
    st = None

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CONFIG_FILE = os.path.join(DATA_DIR, "ai_config.json")

MODELS = {
    "Claude Haiku 4.5 (rapide, économique -- recommandé)": "claude-haiku-4-5-20251001",
    "Claude Sonnet 5 (plus riche, un peu plus lent)": "claude-sonnet-5",
}
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def _session_get(key, default=None):
    if st is not None and hasattr(st, "session_state"):
        return st.session_state.get(key, default)
    return default


def _secret_get(key, default=None):
    """Read from Streamlit Cloud's Secrets manager, if available. Never raises."""
    if st is None:
        return default
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def _read_config_file() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_key_to_device(api_key: str, model: str) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"api_key": api_key, "model": model}, f)


def clear_saved_key() -> None:
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)


def get_api_key() -> str | None:
    override = _session_get("api_key_override")
    if override:
        return override
    cfg = _read_config_file()
    if cfg.get("api_key"):
        return cfg["api_key"]
    secret = _secret_get("ANTHROPIC_API_KEY")
    if secret:
        return secret
    return os.environ.get("ANTHROPIC_API_KEY")


def get_model() -> str:
    override = _session_get("api_model_override")
    if override:
        return override
    cfg = _read_config_file()
    if cfg.get("model"):
        return cfg["model"]
    secret = _secret_get("ANTHROPIC_MODEL")
    if secret:
        return secret
    return DEFAULT_MODEL


def is_configured() -> bool:
    return bool(get_api_key())


def key_source() -> str:
    """For diagnostics in the Settings page -- where the active key came from."""
    if _session_get("api_key_override"):
        return "session (not saved)"
    if _read_config_file().get("api_key"):
        return "data/ai_config.json (this device)"
    if _secret_get("ANTHROPIC_API_KEY"):
        return "Streamlit secrets"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "environment variable"
    return "none"


def _extract_json(text: str) -> dict:
    text = text.strip()
    # Strip ```json ... ``` fences if the model added them despite instructions
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"Could not parse JSON from model output: {text[:200]!r}")


def chat_json(system_prompt: str, messages: list, max_tokens: int = 700) -> dict:
    """
    messages: [{"role": "user"|"assistant", "content": "..."}]
    Returns the parsed JSON dict from the model's reply.
    Raises RuntimeError on any failure (missing key, network, bad JSON) --
    callers should catch this and fall back to the offline engine.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("Aucune clé API configurée.")

    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError("Le package 'anthropic' n'est pas installé (pip install anthropic).") from e

    try:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=get_model(),
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        text = "".join(block.text for block in resp.content if hasattr(block, "text"))
        return _extract_json(text)
    except Exception as e:  # noqa: BLE001 -- deliberately broad: any failure -> fallback
        raise RuntimeError(f"Erreur d'appel à l'API Claude : {e}") from e


def test_connection() -> tuple[bool, str]:
    """Quick sanity check used by the Settings page's 'Tester la connexion' button."""
    try:
        result = chat_json(
            system_prompt='Réponds strictement avec ce JSON, rien d\'autre : {"ok": true}',
            messages=[{"role": "user", "content": "test"}],
            max_tokens=20,
        )
        if result.get("ok"):
            return True, f"Connexion réussie avec le modèle {get_model()} !"
        return False, f"Réponse inattendue du modèle : {result}"
    except RuntimeError as e:
        return False, str(e)
