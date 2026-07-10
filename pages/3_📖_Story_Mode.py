"""
Page: Story Mode -- collaborative storytelling in French. You read a
chapter, then write what happens next. With a Claude API key configured,
the AI genuinely weaves your contribution into the next paragraph and
decides when the story naturally concludes; without a key, it falls back
to a fixed sequence of pre-written chapters.
"""

import streamlit as st
from core import ui, gamification as game, content_bank as cb, tutor_engine, ai_client, voice

st.set_page_config(page_title="Story Mode", page_icon="📖", layout="wide")
ui.init_app_state()
profile = ui.require_profile()
ui.sidebar_switcher()
name = st.session_state.active_profile

st.title("📖 Story Mode")
st.caption("Your personal story -- pick it up where you left it, at your own pace.")
conv_on = voice.conversation_toggle(f"conv_mode_story_{name}")
if conv_on:
    st.caption("🎙️ Conversation mode is on -- just talk, pause when you're done, and the narrator will answer out loud.")
else:
    st.caption("Type, or turn on conversation mode above to talk hands-free.")

ai_mode = ai_client.is_configured()
with st.sidebar:
    st.markdown("---")
    if ai_mode:
        st.success(f"🤖 Adaptive AI story ({ai_client.get_model()})")
    else:
        st.warning("📴 Fixed chapters mode (no API key)")

story_ids = list(cb.STORIES.keys())
labels = [f"{cb.STORIES[sid]['title']} ({cb.STORIES[sid]['cefr']})" for sid in story_ids]
choice = st.selectbox("Choose a story:", options=list(range(len(story_ids))), format_func=lambda i: labels[i])
story_id = story_ids[choice]
story = cb.STORIES[story_id]

transcript_key = f"story_transcript_{name}_{story_id}"
ended_key = f"story_ended_{name}_{story_id}"

if transcript_key not in st.session_state:
    st.session_state[transcript_key] = []
if ended_key not in st.session_state:
    st.session_state[ended_key] = story_id in profile.get("stories_completed", [])

chapter_idx = profile["story_progress"].get(story_id, 0)


def _reset():
    profile["story_progress"][story_id] = 0
    if story_id in profile.get("stories_completed", []):
        profile["stories_completed"].remove(story_id)
    st.session_state[transcript_key] = []
    st.session_state[ended_key] = False
    ui.save()


if st.button("🔄 Restart this story"):
    _reset()
    st.rerun()

st.divider()

for i, entry in enumerate(st.session_state[transcript_key]):
    if entry["role"] == "narrator":
        st.markdown(entry["text"])
        voice.speak_button(entry["text"], key=f"story_{name}_{story_id}_{i}")
        if entry.get("corrections"):
            with st.container(border=True):
                st.markdown("**✏️ Friendly note on your last contribution:**")
                for c in entry["corrections"]:
                    st.markdown(f"- *« {c['matched']} »* → **« {c['suggestion']} »**")
                    st.caption(c["explanation"])
    else:
        with st.chat_message("user", avatar=profile["avatar"]):
            st.markdown(entry["text"])

first_chapter = cb.get_story_chapter(story_id, 0)

# Show the fixed opening chapter once, if we haven't started yet
if not st.session_state[transcript_key] and first_chapter:
    st.markdown(f"**Chapter 1**")
    st.markdown(first_chapter["fr"])
    voice.speak_button(first_chapter["fr"], key=f"story_first_{name}_{story_id}")
    if first_chapter["prompt"]:
        st.caption(f"✍️ {first_chapter['prompt']}")

if st.session_state[ended_key]:
    st.success("🎉 The End! Well done on this story.")
    st.balloons()
    st.stop()

# ===========================================================================
# AI-DRIVEN MODE -- open-ended continuation
# ===========================================================================
if ai_mode:
    mic_text = None
    if conv_on:
        transcript = st.session_state[transcript_key]
        if not transcript:
            speak_text = first_chapter["fr"] if first_chapter else None
        else:
            last_entry = transcript[-1]
            speak_text = last_entry["text"] if last_entry["role"] == "narrator" else None
        voice.conversation_loop(
            turn_id=str(len(transcript)),
            conv_key=f"story_ai_{name}_{story_id}",
            speak_text=speak_text,
        )
    else:
        mic_col, _ = st.columns([1, 8])
        with mic_col:
            mic_text = voice.mic_input(f"story_ai_mic_{name}_{story_id}") if voice.mic_available() else None
    contribution = mic_text or st.chat_input("Write what happens next, in French...")
    if contribution:
        if not st.session_state[transcript_key]:
            st.session_state[transcript_key].append({"role": "narrator", "text": f"**Chapter 1**\n\n{first_chapter['fr']}"})
        st.session_state[transcript_key].append({"role": "user", "text": contribution})

        story_so_far = "\n\n".join(e["text"] for e in st.session_state[transcript_key] if e["role"] == "narrator")
        try:
            result = tutor_engine.respond_story_ai(story["title"], story_so_far, contribution, profile["level"], name)
            chapter_idx += 1
            next_text = f"**Chapter {chapter_idx + 1}**\n\n{result['paragraph']}"
            if result.get("prompt"):
                next_text += f"\n\n✍️ *{result['prompt']}*"
            st.session_state[transcript_key].append({
                "role": "narrator", "text": next_text, "corrections": result["corrections"],
            })
            profile["story_progress"][story_id] = chapter_idx
            game.award_xp(profile, 12, f"Story: {story['title']}")
            game.bump_quest_progress(profile, "story", amount=1)
            if result["corrections"]:
                profile["corrections_seen"] += len(result["corrections"])

            if result["story_ended"]:
                st.session_state[ended_key] = True
                if story_id not in profile["stories_completed"]:
                    profile["stories_completed"].append(story_id)
                game.award_xp(profile, 20, f"Story completed: {story['title']}")

            newly = game.new_badges(profile)
            ui.save()
            ui.show_new_badges(newly)
            st.rerun()
        except RuntimeError as e:
            st.session_state[transcript_key].pop()  # remove the unanswered user turn
            st.warning("The AI couldn't continue the story this time -- try again in a moment.")
            with st.expander("Technical detail"):
                st.code(str(e))

# ===========================================================================
# OFFLINE FALLBACK -- fixed chapter sequence
# ===========================================================================
else:
    chapter = cb.get_story_chapter(story_id, chapter_idx)

    if chapter is None:
        if story_id not in profile["stories_completed"]:
            profile["stories_completed"].append(story_id)
            ui.save()
        st.success("🎉 The End! Well done on this story.")
        st.balloons()
        st.stop()

    if chapter_idx > 0:
        st.markdown(f"**Chapter {chapter_idx + 1}**")
        st.markdown(chapter["fr"])
        voice.speak_button(chapter["fr"], key=f"story_chapter_{name}_{story_id}_{chapter_idx}")

    if chapter["prompt"]:
        if chapter_idx > 0:
            st.caption(f"✍️ {chapter['prompt']}")
        mic_text = None
        if conv_on:
            voice.conversation_loop(
                turn_id=str(chapter_idx),
                conv_key=f"story_offline_{name}_{story_id}",
                speak_text=chapter["fr"],
            )
        else:
            mic_col, _ = st.columns([1, 8])
            with mic_col:
                mic_text = voice.mic_input(f"story_offline_mic_{name}_{story_id}_{chapter_idx}") if voice.mic_available() else None
        contribution = mic_text or st.chat_input("Write what happens next, in French...")
        if contribution:
            st.session_state[transcript_key].append({"role": "narrator", "text": f"**Chapter {chapter_idx + 1}**\n\n{chapter['fr']}"})
            st.session_state[transcript_key].append({"role": "user", "text": contribution})
            game.award_xp(profile, 12, f"Story: {story['title']}")
            profile["story_progress"][story_id] = chapter_idx + 1
            game.bump_quest_progress(profile, "story", amount=1)
            newly = game.new_badges(profile)
            ui.save()
            st.toast("+12 XP! The next chapter awaits.", icon="📖")
            st.rerun()
    else:
        if st.button("Finish the story 🎉"):
            st.session_state[transcript_key].append({"role": "narrator", "text": f"**Chapter {chapter_idx + 1}**\n\n{chapter['fr']}"})
            result = game.award_xp(profile, 20, f"Story completed: {story['title']}")
            profile["story_progress"][story_id] = chapter_idx + 1
            if story_id not in profile["stories_completed"]:
                profile["stories_completed"].append(story_id)
            newly = game.new_badges(profile)
            ui.save()
            ui.show_level_up(result)
            ui.show_new_badges(newly)
            st.rerun()
