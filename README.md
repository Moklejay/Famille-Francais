# Handoff: Famille Français — Mobile UI (Home, Speak, Roleplay, Story, Quests, Profile)

## Overview
A premium, voice-first mobile UI for **Famille Français**, a French-immersion app for English speakers. The existing backend (github.com/Moklejay/Famille-Francais) is a Streamlit + Python app with real logic for profiles, XP/streak/coin gamification, spaced-repetition vocab review, an AI conversation tutor (Claude API), and browser-based voice I/O (Web Speech API). This handoff is a **new mobile frontend** designed to replace the Streamlit UI while reusing all of the existing Python logic as the backend/API layer.

The design's core premise: voice-first interaction is the primary mode on every learning screen (Speak / Roleplay / Story) — a big mic control drives a continuous listen-→-respond loop; typed text is an explicit secondary fallback, never the default UI.

## About the Design Files
The bundled file (`Home Lesson.dc.html`) is a **design reference built in HTML** — a working, interactive prototype showing intended layout, color, motion, and behavior for six screens (they live in one file, switched by the bottom tab bar's state, purely for prototyping convenience). It is **not production code to embed directly**. The task is to **recreate this design in the target codebase's real environment** — most likely a native or cross-platform mobile stack (React Native, Flutter, SwiftUI/Kotlin, or a mobile-web PWA if the team prefers shipping a web client against the existing Streamlit/Python backend) — using that stack's own component and state-management patterns, while matching this design pixel-for-pixel on values below.

Open the HTML file in a browser to interact with it directly: tap tabs to switch screens, tap the theme swatches/avatar tiles on Profile, tap the France/Québec toggle, tap "Buy" on the streak-freeze card, etc. — all of it is live so you can inspect exact computed styles and behavior.

## Fidelity
**High-fidelity.** Colors, type, spacing, radii, and copy below are final. Recreate pixel-perfectly in the target stack's own component library/primitives (do not import HTML/CSS as-is).

## Backend wiring — map UI to existing Python modules
This is the most important section for implementation. The UI has **no logic of its own** — every number and behavior below should be read from / written to the existing backend:

- **Profile / streak / XP / coins** — `core/storage.py` (`DEFAULT_PROFILE`, `touch_daily_activity`, `merge_and_save`) and `core/gamification.py` (`award_xp`, `compute_level`, `xp_to_next_level`, `record_daily_login`). The Home XP ring and "N XP to level N+1" label are a direct render of `xp_to_next_level()`. The streak chip is `profile["streak"]["current"]`.
- **Level-based unlocks (themes/avatars)** — `core/content_bank.py`'s `LEVEL_UNLOCKS` dict and `core/ui.py`'s `THEMES` + `AVATAR_UNLOCK_LEVEL`. The Profile screen's theme swatches and avatar tiles should gate on `compute_level(xp) >= unlock_level` exactly as the backend already does — the prototype hardcodes `Classic`(lvl 1)/`Sunrise`(lvl 3)/`Ocean`(lvl 5)/`City`(lvl 10, renamed from backend's "Aurora") to match `LEVEL_UNLOCKS`.
- **Coins / streak-freeze shop** — the backend has no streak-freeze purchase yet; this is a **new feature** the design adds a UI for (per product requirement that coins need a real sink). Implement it as: deduct 50 coins from `profile["coins"]`, increment a new `profile["streak_freezes"]` counter, and consume one automatically instead of resetting `streak.current` to 1 the next time `touch_daily_activity()` would otherwise detect a broken streak (`gap > 1`). This requires a small backend change in `core/storage.py::touch_daily_activity`.
- **Daily/weekly quests** — `core/gamification.py` (`get_todays_daily_quest`, `get_this_weeks_weekly_quest`, `bump_quest_progress`) and `core/content_bank.py` (`QUESTS_DAILY`, `QUESTS_WEEKLY`). Quest cards on Home/Quests render `profile["quests"]["daily"/"weekly"]` progress directly.
- **Badges** — `core/content_bank.py::BADGES` + `core/gamification.py::new_badges()`. The badge grid on Quests shows every entry in `BADGES`, dimmed unless its id is in `profile["badges"]`.
- **Vocab review due count** — `core/srs.py::due_cards(profile)` — the Home "N words to review" card is `len(due_cards(profile))`.
- **Chat Tutor (Speak)** — `core/tutor_engine.py::respond()` (tries `respond_ai`, falls back to `respond_rulebased`), fed by `core/voice.py`'s conversation loop (SpeechRecognition → `respond()` → SpeechSynthesis). The "AI active" chip reflects `ai_client.is_configured()`. The correction chip shown after a reply is the first entry of the `corrections` list `respond()` returns.
- **Roleplay** — `core/tutor_engine.py::respond_roleplay_ai()` with scenario data from `core/content_bank.py::SCENARIOS` (`setting`, `bot_role`, `min_turns`, offline `nodes` tree as fallback). Turn-progress dots = number of exchanges vs. `min_turns`.
- **Story Mode** — `core/tutor_engine.py::respond_story_ai()` with `core/content_bank.py::STORIES` (first chapter always shown verbatim; AI improvises afterward). Chapter-progress dots = story turn index.
- **Québécois vs. Metropolitan toggle** — **new UI concept**, not yet a backend field. Closest existing hook is `content_bank.py`'s `"theme": "Quebec"` tag on individual `VOCAB`/`SCENARIOS` entries. Recommend adding a `profile["track"]` field (`"metro" | "quebec"`) and filtering/prioritizing Quebec-tagged content (vocab, scenarios, culture notes) when set to `"quebec"`, while keeping both tracks accessing the same CEFR-gated content otherwise. This is a backend change to make alongside the frontend.
- **Voice loop mechanics** — the design's big mic control (idle → listening → speaking → idle) should drive/be driven by the same state machine as `core/voice.py`'s `conversation_loop()`: SpeechRecognition starts on tap (first-tap microphone permission gate), auto-sends on natural pause, plays the reply via SpeechSynthesis, then re-listens automatically. Manual mic (tap-to-start/stop) and typed fallback both remain available per `voice.py`'s existing dual-mode design.

## Screens / Views
All screens share one 390×844 mobile canvas, near-black shell, and the same header + bottom tab bar (see "Shared chrome" below). Only the scrollable body content changes per tab.

### 1. Home ("Learn" tab)
**Purpose:** Daily dashboard — one clear "today's session" the app already picked (no lesson chooser), gamification status, and quick links into the rest of the app.
**Layout (top → bottom, 20px side padding):**
1. Shared header (see below).
2. **XP/session card** — full-width, `border-radius:20px`, background `rgba(10,10,12,0.96)`, `border:1px solid rgba(255,255,255,0.09)`, `box-shadow:0 8px 22px rgba(0,0,0,0.4)`, `padding:16px`, flex row `gap:16px`:
   - Left: 84×84px circular XP ring — `conic-gradient(accent 0deg {progress*360}deg, rgba(255,255,255,0.09) {progress*360}deg 360deg)`, with an inner 64×64px circle (card's own bg color) centered on top showing the level number (Poppins 800 20px) and "LEVEL" caption (10px, `#7C7C86`, letter-spacing .04em).
   - Right (flex:1): "{xpToNext} XP to level {n+1}" label (12px, `#9A9AA2`), a 6px rounded progress bar (track `rgba(255,255,255,0.08)`, fill = accent color), then "Today's session" label (same style) and a row of 3 flex-1 5px-tall pill segments (session-step dots: filled = accent, unfilled = `rgba(255,255,255,0.12)`).
3. **Track toggle** — right-aligned pill switch, `background:#181818`, `border:1px solid rgba(255,255,255,0.08)`, `border-radius:999px`, `padding:4px`. Two segments "🇫🇷 France" / "🍁 Québec", active segment gets `background:{accent}` `color:#FFF`, inactive `color:#9A9AA2`. Tapping swaps both the segment state and the hero photo below.
4. **Hero lesson card** — 190px tall, `border-radius:22px`, full-bleed photo (`object-fit:cover`) of the picked scenario (café scene for France track, sugar-shack photo for Québec track), a bottom-anchored gradient scrim (`linear-gradient(180deg, transparent 35%, rgba(11,11,13,0.92) 100%)`), and over it: a small pill tag ("ROLEPLAY", `background:{accent}E6`), title (Poppins 700 21px), and meta line ("Order a coffee and a croissant · 8 min", 12.5px `#C7C7CE`).
5. **Voice CTA** — centered column: a 132×132px stage holding two concentric pulsing ring outlines (`border:2px solid accent@45%/30%`, `animation: scale 1→1.35 + fade, 2.2s ease-out infinite`, second ring delayed 0.4s) around a 104×104px solid-accent circle with a white mic glyph (SVG: rounded rect + arc + stem). The fox mascot illustration sits overlapping bottom-left of the stage. Below: status title (Poppins 700 16px — "Tap to talk" / "Listening…"), a subtext line (13px `#9A9AA2`), and a small underlined "Type a message instead" link (12.5px, accent-tinted). Tapping the mic toggles listening state (brightens to a lighter accent shade + adds the pulse box-shadow animation while active).
6. **Quests** — up to 2 quest cards (see shared quest-card spec below), pulled from the daily + weekly quest slots.
7. **Vocab review row** — card with a 42×42px rounded-12px icon tile (🧠 on accent-tinted bg), "{N} words to review" / "Spaced repetition" two-line label, and a pill "Review" button (solid accent bg).
8. **Badges** — horizontal scroll row of up to ~6 badge chips (see shared badge-chip spec).

### 2. Speak (Chat Tutor)
**Purpose:** Open-ended voice conversation with the AI tutor.
**Layout:** Header row "Chat Tutor" + an "🤖 AI active" pill (accent-tinted). A "last exchange" card shows the tutor's last French line (15px, weight 600) with its English gist beneath (12.5px, `#9A9AA2`). Below that, the same voice-CTA pattern as Home but scaled up (152×152 stage, 120×120 circle, 38px mic glyph) with mascot at a smaller 58px scale. A conditional gold-tinted correction chip ("✏️ 1 gentle correction from your last reply") appears beneath when not actively listening.

### 3. Roleplay
**Purpose:** In-character voice scene tied to a scenario (café, directions, market, meeting a friend, sugar shack for Québec track).
**Layout:** 180px full-bleed scene photo card (same scrim treatment as Home's hero) with scenario title (Poppins 700 19px) + one-line description. Below: a turn-progress row of 3 pill segments (26×5px, active = accent). A bot-line card (centered, 14.5px weight 600) shows the current in-character line. Then a smaller voice CTA (120×120 stage / 92×92 circle / 30px glyph, single pulse ring only) with a status label ("Tap to respond in character" / "Listening…").

### 4. Story Mode
**Purpose:** Collaborative storytelling — narrated chapters, voice responses continue the story.
**Layout:** 170px illustration card (full-bleed image, same scrim) with story title overlay. A 5-segment chapter-progress row (flex-1 5px pills). A chapter card shows the current French paragraph (14px, line-height 1.6) plus the open prompt question in accent-tinted text (12.5px, weight 600). Below: voice CTA at 112×112 stage / 86×86 circle / 28px glyph, single pulse ring, status "Tap to continue the story" / "Listening…".

### 5. Quests
**Purpose:** Full quest list + badge gallery (this is the deeper version of Home's condensed quest/badge sections).
**Layout:** "Quests" heading, then every quest card (daily + weekly, each carrying a "Daily"/"Weekly" tag pill instead of being pre-filtered) using the shared quest-card spec. Below: "Badge gallery" heading and a **4-column CSS grid** (`gap:10px`) of every entry in `BADGES`, using the shared badge-chip spec at a slightly smaller icon size (aspect-ratio:1 square tiles instead of a horizontal scroll row).

### 6. Profile
**Purpose:** Identity, level-gated cosmetic unlocks, and the coin sink (streak-freeze purchase).
**Layout:**
1. Centered column: 84×84px circular avatar (photo or emoji, see Avatar system below) with a `3px solid {accent}88` ring, a small 28×28px camera-glyph edit badge bottom-right (accent-filled circle, white stroke icon) that opens the device's file picker, name (Poppins 700 18px), "Level {n} · {CEFR}" caption, and an "Upload a photo" text link beneath.
2. **Coin / streak-freeze card** — coin icon image (42×42px circular) + "{coins} coins" / "Streak freeze — 50 🪙 · {N} owned" two-line label, and a "Buy" pill button (accent bg, 40% opacity when coins < 50) that deducts 50 coins and increments owned-freezes count, with inline feedback text ("Streak freeze added!" / "Not enough coins").
3. **Themes** — row of 4 flex-1 square tiles (`border-radius:16px`, filled with the theme's actual color, `box-shadow:0 6px 14px rgba(0,0,0,0.35)`), each showing a 🔒 if locked-by-level or a white ✓ if it's the active selection, label beneath (theme name if unlocked, "Lvl {n}" if not), 40% opacity when locked. Tapping an unlocked tile re-themes the **entire app's accent color** live (see Theme system below) and, for three of the four themes, swaps the app's background to a full-bleed themed photo.
4. **Avatars** — row of 6 flex-1 circular tiles (photo option + 5 emoji options), gradient bg fill, ring color = accent when selected else faint white, small bottom-right badge showing 🔒 (locked) or accent ✓ (selected). Tapping an unlocked tile changes the header + Profile avatar everywhere.

## Shared chrome
- **Header** (present at the top of every screen's scroll body): 52×52px circular avatar (`2px solid {accent}88`) at left, name (Poppins 700 19px) + "Level {n} · {CEFR}" (13px `#9A9AA2`) beside it; on the right, two pill chips — streak (small orange dot + count) and coins (16×16px coin icon image + count).
- **Bottom tab bar**: fixed row, `background:#0F0F12`, `border-top:1px solid rgba(255,255,255,0.08)`, `padding:10px 6px 20px 6px` (20px bottom = safe-area). 6 items — Home/Learn, Speak, Roleplay, Story, Quests, Profile — each a 22×22px line-icon (2px stroke) over a 9.5px bold label; active tab's icon+label render in the accent color, inactive in `#6B6B76`.
- **Quest card**: `background:#141417`, `border:1px solid rgba(255,255,255,0.07)`, `border-radius:16px`, `padding:14px 16px`. Header row: icon+title (13.5px weight 700) left, reward chips right (or a Daily/Weekly tag on the Quests screen). Description (12px `#9A9AA2`). 6px progress bar (track `rgba(255,255,255,0.08)`, fill = accent). Reward chips: XP chip (`background:accent@16%`, `color:` a lightened accent shade) and coins chip (icon image + `+N`, gold-tinted `background:rgba(244,193,78,0.16)` `color:#F4C14E`).
- **Badge chip**: rounded-16px tile with the badge emoji at ~24px, name caption beneath (10px `#9A9AA2`); earned = `background:accent@14%` / `border:accent@40%` / full opacity; unearned = dark flat bg / faint border / 35% opacity.
- **Voice mic button** (all 4 variants: Home/Speak/Roleplay/Story): solid-accent circle with a white mic glyph (rounded rect capsule + arc + stem, stroke-based SVG), wrapped in 1–2 pulsing ring outlines. Listening state swaps the fill to a lightened accent tint and adds a `box-shadow` pulse keyframe (`0 0 0 0` → `0 0 0 22px` fading accent-tinted shadow, 1.6s loop).

## Theme system (accent + wallpaper)
Every screen computes one `accent` color from the active theme and threads it through **every** accent-tinted surface: the XP ring, all progress bar fills, all mic-button fills/pulse rings, the track-toggle active segment, the active tab color, badge earned bg/border, quest XP chips, both avatar-photo border rings, the hero-card type tag, and the Profile Buy button. There is no second brand color — everything accent-tinted recolors together.

| Theme | Unlock level | Accent hex | Wallpaper |
|---|---|---|---|
| Classic | 1 (default) | `#2F5FE0` | none — ambient dual radial-gradient glow (accent @28%/@14%) top-left/right |
| Sunrise | 3 | `#FF6F59` | `assets/themes/sunrise-paris-bg.png` (Paris skyline, sunset) |
| Ocean | 5 | `#1F8A9E` | `assets/themes/ocean-france-bg.jpg` (coastal beach) |
| City | 10 (renamed from backend's "Aurora") | `#7C5CBF` | `assets/themes/city-quebec-bg.jpg` (Château Frontenac street view) |

Wallpaper rendering: full-bleed `<img>` behind all content at `opacity:0.85`, plus a top-to-bottom scrim `linear-gradient(180deg, rgba(11,11,13,0.2) 0%, rgba(11,11,13,0.55) 55%, #0B0B0D 100%)` so foreground text/cards stay legible.

"Listening" mic-fill tint is computed as the accent color lightened by ~28/255 per RGB channel (not a separate hardcoded blue) so it stays in-theme.

## Avatar system
Options: the user's uploaded photo (default: a placeholder photo bundled at `assets/avatar-user.png`), plus 5 emoji avatars matching the backend's `AVATARS` list — 🦊 (lvl 1), 🐨 (lvl 1), 🦋 (lvl 1), 🐸 (lvl 7, matches backend `AVATAR_UNLOCK_LEVEL`), 🦄 (lvl 12, matches backend). Selecting an option updates the header avatar and the Profile avatar immediately (client-side state in the prototype; should write to `profile["avatar"]`/a new `profile["avatar_photo_url"]` field in the real app). Photo upload uses a native file picker → should upload to backend storage and persist a URL rather than a data-URI in production.

## Mascot
Dachshund-in-a-French-beret vector-style character (`assets/mascot-fox.png`, transparent PNG) used as a "guide" beside the voice CTA on Home and Speak. Reproduce at any size — it's a flat illustration, not a photo, so it should scale cleanly as an SVG/vector asset in the target app if the source vector is available; otherwise treat the PNG as final art at 2x/3x export resolutions.

## Design Tokens
- **Colors:** shell background `#0B0B0D`; card surface `#141417` / header avatar ring bg `#181818`; borders `rgba(255,255,255,0.07–0.09)`; primary text `#FFFFFF`; secondary text `#9A9AA2`; tertiary/icon-inactive `#6B6B76`; muted label `#7C7C86`; streak-flame dot `#FF8A3D`; coin/gold accents `#F4C14E` (chip text) on `rgba(244,193,78,0.16)` (chip bg); accent color is theme-driven (table above).
- **Typography:** Headings/display — **Poppins** 600/700/800. Body/UI — **Inter** 400/500/600/700. Sizes in use: 9–9.5px (tab labels, badge captions), 10–12.5px (captions, meta, chip text), 13–15px (body/labels), 16–19px (section/status titles), 20–21px (ring level number, hero title).
- **Radii:** 12px (small icon tiles), 14–16px (badges, avatar-option tiles), 16–20px (cards), 22px (hero/scene photo cards), 999px (pills/buttons/progress tracks).
- **Shadows:** cards use `0 8px 22px rgba(0,0,0,0.4)` (XP card) or none (flat cards); mic button `0 10px 30px {accent}@45%`; avatar/theme tiles `0 6px 14px rgba(0,0,0,0.35)`.
- **Spacing:** 20px screen side padding; 14–20px gaps between stacked sections; 6–10px gaps within card internals.
- **Canvas:** 390×844 (iPhone-class mobile viewport); safe-area bottom padding baked into the tab bar (20px).

## Assets
All paths below are **relative to this folder's root** — identical to how `Home Lesson.dc.html` references them (`<img src="mascot-fox.png">`, `<img src="scenes/cafe-striped-awning.jpg">`, etc.), so the prototype opens correctly as-is and the same relative paths can be dropped straight into the target app's asset pipeline:
- `avatar-user.png` — default profile photo placeholder. A fully opaque square photo crop (no transparency needed — it's a photo, not an icon).
- `coin-daisy.png` — coin icon (circular gold coin illustration). **Real transparency** outside the coin's circular edge (verified 21.5% fully-transparent pixels) — safe to place on any background color.
- `mascot-fox.png` — mascot illustration (dachshund in a beret). **Real transparency** around the character (verified 35% fully-transparent pixels) — scales cleanly on any background.
- `scenes/cafe-striped-awning.jpg` — France-track hero/roleplay photo (Parisian café).
- `scenes/quebec-sugar-shack.png` — Québec-track hero/roleplay photo (illustrated sugar shack).
- `scenes/quebec-street-illustration.png` — Story Mode chapter illustration (Old Québec street).
- `scenes-spare/*.jpg` — additional Paris café/street photos supplied for variety; not yet wired into a screen — good candidates for additional Roleplay scenarios or a future scene-rotation feature.
- `themes/sunrise-paris-bg.png`, `themes/ocean-france-bg.jpg`, `themes/city-quebec-bg.jpg` — the three theme wallpapers described above.

All photos/illustrations were supplied directly by the user during design review; none are AI-generated placeholders and none require replacement. **If any image fails to open/decode on your end, that's a transfer problem, not a source problem** — every file above was verified immediately before this bundle was assembled (dimensions + real alpha-channel checks passed). Re-download the zip rather than re-requesting new source images.

## Files
- `Home Lesson.dc.html` — the interactive reference prototype (all 6 screens, live state). Open directly in any browser.
