"""
voice.py
--------
Voice input/output helpers shared by Chat Tutor, Roleplay Scenarios, and
Story Mode.

STT (speak to the app): uses the `streamlit_mic_recorder` component's
`speech_to_text()` helper, which wraps the browser's native Web Speech
API (SpeechRecognition). No API key, no server-side audio processing --
recognition happens in the visitor's own browser (Chrome/Edge support it
well; Safari/Firefox support is partial, so we always keep the text input
as a fallback right next to the mic button).

TTS (hear the tutor reply): uses the browser's native `speechSynthesis`,
injected via `st.components.v1.html`. Also fully client-side, free, no
extra package needed for this half.

Both are best-effort: if the visitor's browser doesn't support the Web
Speech API, the mic button will simply show nothing to transcribe, and
the "listen" button will silently no-op. Every page keeps its existing
text input/chat log fully working either way -- voice is additive, not a
replacement path.
"""

from __future__ import annotations
import html
import streamlit as st

try:
    from streamlit_mic_recorder import speech_to_text
    _MIC_AVAILABLE = True
except ImportError:
    _MIC_AVAILABLE = False


def mic_available() -> bool:
    """Whether the streamlit-mic-recorder package is installed. Pages use
    this to decide whether to show the mic button at all (it should
    always be True once requirements.txt is deployed, but this keeps the
    page from crashing if a dependency install is ever mid-flight)."""
    return _MIC_AVAILABLE


def mic_input(key: str, lang: str = "fr-FR") -> str | None:
    """
    Renders a small round mic button. While recording, the button pulses;
    on stop, the browser's speech recognizer transcribes what was said
    and this returns the resulting French text (None if nothing new was
    transcribed since the last call).

    key: a unique widget key per call site (e.g. "chat_tutor_mic",
    "roleplay_mic_<scenario_id>", "story_mic_<story_id>") -- must be
    unique per page/context or Streamlit will collide widget state.
    """
    if not _MIC_AVAILABLE:
        return None
    text = speech_to_text(
        language=lang,
        start_prompt="🎤",
        stop_prompt="⏹️",
        just_once=True,
        use_container_width=False,
        key=key,
    )
    return text or None


def speak_button(text: str, key: str, lang: str = "fr-FR", label: str = "🔊"):
    """
    Renders a tiny inline button that reads `text` aloud in French using
    the browser's built-in speechSynthesis voice. Picks the best-matching
    fr-FR (or fr-*) voice available on the visitor's device; falls back
    to the browser default voice if none is installed.

    Safe against HTML/JS injection: `text` is JSON-escaped before being
    embedded in the generated script.
    """
    import json
    safe_text = json.dumps(text or "")
    safe_lang = json.dumps(lang)
    # Use a random-ish DOM id per call so multiple buttons on one page
    # don't collide.
    btn_id = f"speak_{key}".replace("-", "_").replace(" ", "_")

    st.components.v1.html(
        f"""
        <button id="{btn_id}" title="Écouter" style="
            background:#232325; color:#fff; border:1px solid rgba(255,255,255,0.15);
            border-radius:999px; padding:4px 10px; cursor:pointer; font-size:0.9rem;
        ">{html.escape(label)} Écouter</button>
        <script>
        (function() {{
            const btn = document.getElementById("{btn_id}");
            if (!btn) return;
            btn.addEventListener("click", function() {{
                if (!('speechSynthesis' in window)) {{
                    btn.textContent = "Non supporté";
                    btn.disabled = true;
                    return;
                }}
                window.speechSynthesis.cancel();
                const utter = new SpeechSynthesisUtterance({safe_text});
                utter.lang = {safe_lang};
                utter.rate = 0.95;
                const voices = window.speechSynthesis.getVoices();
                const frVoice = voices.find(v => v.lang && v.lang.toLowerCase().startsWith('fr'));
                if (frVoice) utter.voice = frVoice;
                window.speechSynthesis.speak(utter);
            }});
        }})();
        </script>
        """,
        height=40,
    )
