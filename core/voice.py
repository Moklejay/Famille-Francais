"""
voice.py
--------
Voice for Chat Tutor, Roleplay Scenarios, and Story Mode.

Two modes are offered:

1. Conversation mode (conversation_toggle + conversation_loop) -- the
   real "feels like a conversation" experience: turn it on once, then
   the page listens, waits for a natural pause in your speech to
   auto-send what you said (no "stop recording" click), reads the
   tutor's reply out loud automatically, and starts listening again on
   its own. This is built on the browser's native Web Speech API
   (SpeechRecognition + speechSynthesis) rather than a button-based
   recorder component, specifically because SpeechRecognition has
   built-in silence detection ("endpointing"): it stops itself the
   moment you stop talking, which is exactly the turn-taking behaviour
   a conversation needs and a manual start/stop button can't give you.

2. Manual mode (mic_input + speak_button) -- a click-based fallback for
   browsers/situations where the hands-free loop doesn't work well
   (e.g. Safari's limited SpeechRecognition support, noisy rooms, or
   just personal preference). Always available side-by-side with typing.

Neither mode requires an API key or sends audio anywhere -- both speech
recognition and speech synthesis run entirely in the visitor's browser.

Implementation note on conversation mode: Streamlit's Python side has no
way to be "pushed" a value the instant speech is recognized -- a rerun
only happens when a real widget changes. So conversation_loop() injects
a small script (via st.components.v1.html) that reaches into the
*parent* document (the actual app page, one level up from the tiny
helper iframe) and drives Streamlit's own chat input for us: it fills
the real textarea with the recognized text and clicks the real send
button, so from Streamlit's perspective a voice turn looks exactly like
the person typed a message and hit Enter. A sessionStorage guard keyed
by a "turn id" (typically the running message count) makes sure each
new message only triggers speak-then-listen once, not on every
unrelated Streamlit rerun (switching profiles, sidebar clicks, etc).
"""

from __future__ import annotations
import html
import json
import streamlit as st

try:
    from streamlit_mic_recorder import speech_to_text
    _MIC_AVAILABLE = True
except ImportError:
    _MIC_AVAILABLE = False


def mic_available() -> bool:
    """Whether the streamlit-mic-recorder package (used by manual mode)
    is installed."""
    return _MIC_AVAILABLE


# ---------------------------------------------------------------------------
# Conversation mode -- hands-free, silence-triggered turn-taking
# ---------------------------------------------------------------------------

def conversation_toggle(key: str, label: str = "🎙️ Conversation mode (hands-free)") -> bool:
    """
    A single on/off switch. When on, a page should hide its manual
    mic/listen controls and call conversation_loop() every rerun
    instead. Persists via Streamlit's own widget state.
    """
    return st.toggle(label, key=key)


def conversation_loop(
    turn_id: str,
    conv_key: str,
    speak_text: str | None,
    lang: str = "fr-FR",
    chat_input_selector: str = '[data-testid="stChatInput"] textarea',
):
    """
    Drives one turn of the hands-free loop. Call every rerun while
    conversation mode is on for that page.

    turn_id: changes exactly when a new message/turn has appeared
        (e.g. str(len(history)), or a node/chapter id) -- used so each
        turn only auto-speaks/auto-listens once, even though Streamlit
        may rerun the script for unrelated reasons.
    conv_key: a stable key namespacing this conversation (e.g.
        f"chat_tutor_{profile_name}") so different pages/profiles don't
        collide in sessionStorage.
    speak_text: the latest tutor/narrator line to read aloud before
        listening for the reply, or None to skip straight to listening
        (nothing new to say yet).
    """
    payload = json.dumps({
        "turnId": str(turn_id),
        "storageKey": f"ff_conv_{conv_key}",
        "speakText": speak_text or "",
        "lang": lang,
        "inputSelector": chat_input_selector,
    })
    st.components.v1.html(
        f"""
        <div id="ff-voice-status" style="font-family:'Inter',sans-serif;font-size:0.8rem;color:#B3B3B3;padding:2px 0;"></div>
        <script>
        (function() {{
            const cfg = {payload};
            const pdoc = window.parent.document;
            const pwin = window.parent;
            const already = sessionStorage.getItem(cfg.storageKey) === cfg.turnId;
            if (already) return;
            sessionStorage.setItem(cfg.storageKey, cfg.turnId);

            function setStatus(text) {{
                const el = document.getElementById('ff-voice-status');
                if (el) el.textContent = text;
            }}

            function submitText(text) {{
                const ta = pdoc.querySelector(cfg.inputSelector);
                if (!ta) {{ setStatus('⚠️ Could not find the message box.'); return; }}
                const setter = Object.getOwnPropertyDescriptor(pwin.HTMLTextAreaElement.prototype, 'value').set;
                setter.call(ta, text);
                ta.dispatchEvent(new pwin.Event('input', {{bubbles: true}}));
                setTimeout(function() {{
                    const btn = pdoc.querySelector('[data-testid="stChatInputSubmitButton"]');
                    if (btn && !btn.disabled) {{
                        btn.click();
                    }} else {{
                        ta.dispatchEvent(new pwin.KeyboardEvent('keydown', {{key: 'Enter', code: 'Enter', bubbles: true}}));
                    }}
                }}, 150);
            }}

            function startListening() {{
                const SR = pwin.webkitSpeechRecognition || pwin.SpeechRecognition;
                if (!SR) {{ setStatus('🎙️ Voice not supported in this browser -- type your reply instead.'); return; }}
                setStatus('🎙️ Listening -- speak, then just pause when you\\'re done...');
                let rec;
                try {{ rec = new SR(); }} catch (err) {{ setStatus('⚠️ Mic unavailable: ' + err); return; }}
                rec.lang = cfg.lang;
                rec.continuous = false;
                rec.interimResults = false;
                rec.maxAlternatives = 1;
                rec.onresult = function(e) {{
                    const text = e.results[0][0].transcript;
                    if (text && text.trim()) {{
                        setStatus('✅ Sending: “' + text + '”');
                        submitText(text.trim());
                    }}
                }};
                rec.onerror = function(e) {{
                    if (e.error === 'no-speech' || e.error === 'audio-capture') {{
                        setTimeout(startListening, 300);
                    }} else if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {{
                        setStatus('⚠️ Microphone blocked -- allow mic access for this site, then toggle conversation mode off and on again.');
                    }} else {{
                        setStatus('⚠️ ' + e.error + ' -- retrying...');
                        setTimeout(startListening, 800);
                    }}
                }};
                try {{ rec.start(); }} catch (err) {{ setTimeout(startListening, 500); }}
            }}

            if (cfg.speakText && ('speechSynthesis' in pwin)) {{
                setStatus('🔊 Speaking...');
                pwin.speechSynthesis.cancel();
                const utter = new pwin.SpeechSynthesisUtterance(cfg.speakText);
                utter.lang = cfg.lang;
                utter.rate = 0.95;
                const voices = pwin.speechSynthesis.getVoices();
                const wanted = cfg.lang.slice(0, 2).toLowerCase();
                const frVoice = voices.find(function(v) {{ return v.lang && v.lang.toLowerCase().indexOf(wanted) === 0; }});
                if (frVoice) utter.voice = frVoice;
                utter.onend = startListening;
                utter.onerror = startListening;
                pwin.speechSynthesis.speak(utter);
            }} else {{
                startListening();
            }}
        }})();
        </script>
        """,
        height=26,
    )


# ---------------------------------------------------------------------------
# Manual mode -- click-based fallback, always available
# ---------------------------------------------------------------------------

def mic_input(key: str, lang: str = "fr-FR") -> str | None:
    """Renders a small round mic button (manual start/stop). Returns the
    transcribed French text once, or None."""
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
    """Renders a tiny inline button that reads `text` aloud on click."""
    safe_text = json.dumps(text or "")
    safe_lang = json.dumps(lang)
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
