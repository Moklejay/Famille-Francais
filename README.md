# 🇫🇷 Famille Français

A daily-habit French immersion app for two (or more) siblings, built as a
**Streamlit** app with a **real Claude API-powered tutor** for genuinely
adaptive conversation, role-play, and storytelling. No account system,
no cloud database -- your progress lives in one JSON file on your machine.

---

## 1. Architecture overview

```
famille_francais/
├── app.py                          # Home: profile creation + Family Journey dashboard
├── requirements.txt
├── .gitignore                       # keeps your API key and progress out of git
├── data/
│   ├── family_data.json            # created automatically -- all progress lives here
│   └── ai_config.json              # created if you click "Save key on this device"
├── core/
│   ├── storage.py                  # JSON load/save, profile creation, streak tracking
│   ├── content_bank.py             # vocab, scenarios, stories, quests, badges (EDIT ME to add content)
│   ├── gamification.py             # XP, levels, badges, quest rotation, joint quests
│   ├── srs.py                      # SM-2-lite spaced repetition scheduler
│   ├── corrections.py              # offline rule-based error correction (fallback mode)
│   ├── ai_client.py                # Claude API wrapper: key storage, model choice, JSON calls
│   ├── tutor_engine.py             # conversation logic -- real AI, with offline fallback
│   └── ui.py                       # shared sidebar, themes, celebration widgets
└── pages/
    ├── 1_💬_Chat_Tutor.py           # free conversation
    ├── 2_🎭_Roleplay_Scenarios.py   # café / directions / market / meeting a friend
    ├── 3_📖_Mode_Histoire.py        # collaborative storytelling
    ├── 4_🧠_Vocab_Review.py         # spaced-repetition flashcards
    ├── 5_🎯_Quests.py               # daily/weekly/joint quests + badge gallery
    ├── 6_🏆_Family_Leaderboard.py   # sibling leaderboard + progress charts
    └── 7_⚙️_Settings_Export.py      # API key, CEFR level, theme/avatar, backup/restore
```

**How the AI is used.** Once you add a Claude API key (Settings page),
three pages become genuinely adaptive:

- **Chat Tutor** -- open-ended conversation. Claude replies only in French,
  calibrated to the learner's CEFR level, and returns structured
  corrections separately from its reply (so the conversation itself never
  gets interrupted by grammar talk).
- **Roleplay Scenarios** -- Claude improvises in character (a café waiter,
  a passer-by in Old Quebec, etc.) and reacts to whatever you actually
  write, rather than following a fixed script. It decides for itself when
  the scene reaches a natural end.
- **Story Mode** -- Claude weaves your contribution into the next
  paragraph of the story and keeps going until it judges the story has
  reached a satisfying conclusion.

**Without a key**, all three pages fall back automatically to an offline,
rule-based mode (pattern-matched replies, scripted dialogue trees, fixed
story chapters) so the app still works instantly, for free, with zero
setup -- useful for a first look, or if the API is ever unreachable. Every
page shows which mode is active in the sidebar (🤖 IA activée / 📴 Mode
hors-ligne). Gamification, spaced-repetition vocab, quests, and the family
dashboard work identically either way -- only the "chatbot" behavior changes.

Streamlit automatically turns everything in `pages/` into sidebar
navigation -- that's why the filenames start with numbers and emoji.

---

## 2. Running it locally

**Requirements:** Python 3.9+.

```bash
cd famille_francais
pip install -r requirements.txt
streamlit run app.py
```

Your browser opens automatically at `http://localhost:8501`. Create your
two profiles (name, starting CEFR level, avatar), then go to
**⚙️ Réglages** to add your Claude API key.

### Getting a Claude API key
1. Go to [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
   and sign up / log in.
2. Create a new API key, copy it (starts with `sk-ant-...`).
3. In the app's **Réglages** page, paste it in, pick a model, and either:
   - **"Utiliser pour cette session"** -- kept in memory only, gone when
     you close the browser tab (safest, re-enter each time), or
   - **"Sauvegarder sur cet appareil"** -- written to `data/ai_config.json`
     on your machine so you don't have to re-enter it daily. This file is
     already in `.gitignore` -- **never commit or share it.**
4. Click **"Tester la connexion"** to confirm it works.

**Cost:** with the default model (Claude Haiku 4.5), a full day of chatting
plus a role-play scene plus a story turn typically costs a small fraction
of a cent to a few cents. Anthropic bills per token used, no subscription
required -- see [current pricing](https://www.anthropic.com/pricing) on
their site. Claude Sonnet 5 is also selectable for richer, slightly slower
replies at a higher (still modest) per-message cost.

**Using it together:** easiest is one of you running it and sharing the
screen/laptop, switching "Profil actif" in the sidebar between turns. For
simultaneous use from two devices, Streamlit also serves over your local
network: run with `streamlit run app.py --server.address 0.0.0.0` and open
`http://<your-computer's-LAN-IP>:8501` from her device on the same Wi-Fi.

---

## 3. Deployment / sharing options

### Option A -- Streamlit Community Cloud (free, easiest link to share)
1. Push this folder to a GitHub repo (`.gitignore` already keeps your key
   and data out of it).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, click "New app", point it at `app.py` in your repo.
3. Add your Claude API key as a **Secret** in the app's settings
   (`ANTHROPIC_API_KEY = "sk-ant-..."`) instead of pasting it in the UI --
   `ai_client.py` automatically checks this environment variable too.
4. You get a shareable URL like `https://your-app.streamlit.app`.

   ⚠️ **Note on persistence:** Streamlit Community Cloud's filesystem is
   not permanently persistent across app restarts/redeploys. Two options:
   - **Automatic (recommended):** add `GITHUB_TOKEN` + `GIST_ID` secrets so
     progress is saved to a private GitHub Gist instead of local disk --
     see **DEPLOY_GUIDE.md, Step 4** for the 3-minute setup. Once
     configured, the **⚙️ Réglages** page shows "✅ Sauvegarde persistante
     activée (GitHub Gist)".
   - **Manual:** periodically use **Réglages → Télécharger la sauvegarde**
     to back up your progress, and **Restaurer** if the cloud instance
     ever resets.

### Option B -- Run locally (most reliable for daily use)
Just `streamlit run app.py` as above. Progress never leaves your computer;
only your chat messages are sent to Anthropic's API when the AI is active.

### Option C -- A shared home server / Raspberry Pi
Same `streamlit run app.py --server.address 0.0.0.0 --server.port 8501`,
left running, port-forwarded if you want access away from home.

---

## 4. Customization tips (do this together!)

Everything pedagogical lives in **`core/content_bank.py`** -- you don't
need to touch any other file to add content:

- **More vocabulary:** add entries to the `VOCAB` list (needs `id`, `cefr`,
  `theme`, `fr`, `en`, `ex_fr`, `ex_en`).
- **More role-play scenes:** add a new entry to `SCENARIOS` with a
  `setting` and `bot_role` (used in AI mode) plus the `nodes` dialogue
  tree (used in offline mode).
- **More stories:** extend `STORIES` -- only the first chapter is ever
  shown verbatim; in AI mode, Claude improvises everything after that.
- **More quests:** add to `QUESTS_DAILY`, `QUESTS_WEEKLY`, or `JOINT_QUESTS`.
- **More badges:** add to `BADGES`, then add the unlock condition in
  `gamification.py`'s `new_badges()`.
- **Tune XP amounts / level thresholds:** `GAME_LEVELS` and the `award_xp`
  calls scattered through `pages/*.py`.
- **Tune the AI's personality/strictness:** edit the system prompts at the
  top of `core/tutor_engine.py` (`CHAT_SYSTEM_PROMPT`, `ROLEPLAY_SYSTEM_PROMPT`,
  `STORY_SYSTEM_PROMPT`) -- e.g. make corrections stricter, add more
  Quebec-specific culture, change how playful vs. formal the tone is.
- **Offline-mode corrections:** append to `PATTERNS` in `core/corrections.py`.
- **New color themes:** add to `THEMES` in `core/ui.py` and
  `THEME_UNLOCK_LEVEL` in the Settings page.
- **New unlockable avatars:** add the emoji to `AVATARS` and its unlock
  level to `AVATAR_UNLOCK_LEVEL`, both in `core/ui.py`.

---

## 5. Pedagogical rationale

- **Comprehensible Input (Krashen, i+1):** every system prompt explicitly
  instructs Claude to calibrate to the learner's CEFR level and stay one
  small notch above what's fully mastered -- understandable with effort,
  never overwhelming. Emoji "gestures" and short English hints (in AI and
  offline mode alike) give context clues instead of translating everything.
- **Active recall + spaced repetition:** the Vocab Review page uses an
  SM-2-style scheduler -- words you know well are shown less often, shaky
  words resurface sooner, which is the most evidence-backed way to move
  vocabulary into long-term memory.
- **Contextual embedding:** vocabulary and grammar are always practiced
  inside a full sentence, a role-play, or a story -- never as bare word
  lists -- because words learned in context stick better and transfer to
  real use.
- **Low-anxiety, positive corrections:** Claude is explicitly instructed to
  never correct mid-reply -- mistakes are returned in a separate
  "corrections" field, shown warmly and after the fact, framed as "here's
  a natural way to say that" plus a short explanation. This reduces the
  affective filter Krashen identifies as a major barrier to acquisition.
- **Genuine adaptivity:** because the tutor is a real model rather than a
  script, it can follow tangents, answer real questions about French or
  Quebec culture, and react to things you actually say -- essential for
  the "meaningful interaction" that makes comprehensible input effective
  rather than rote.
- **Gamification for habit formation:** streaks, XP, levels, badges, and
  quests mirror what makes apps like Duolingo sticky -- visible daily
  progress, small variable rewards, and loss-aversion around streaks --
  channeled toward a genuinely useful daily habit.
- **Social/collaborative accountability:** the shared Family dashboard,
  leaderboard, and joint sibling quests add social commitment, which
  significantly boosts follow-through versus practicing alone.

---

## 6. Known limitations (so expectations are set correctly)

- The AI calls Anthropic's API over the network -- if you're offline, or
  the key/quota is invalid, the app automatically and silently falls back
  to the offline rule-based mode for that turn (with a small notice) so a
  bad connection never breaks the session.
- Offline mode (no key) is intentionally simpler: pattern-matched replies
  and a curated list of common mistakes rather than true understanding.
- Two people using the app *at the exact same moment* on the same machine
  will need to take turns (switch profile in the sidebar) unless you run
  it on a shared network as described above.
- Your chat messages are sent to Anthropic's API when the AI is active
  (standard for any API-backed AI feature) -- see Anthropic's
  [privacy policy](https://www.anthropic.com/legal/privacy) if that matters to you.

Bonne chance, et amusez-vous bien ! 🥐🍁
