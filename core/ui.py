"""
ui.py — ULTIMATE PREMIUM EDITION
---------------------------------
Famille Français — Duolingo + Spotify Fusion, pushed to the absolute limit.

Every pixel considered. Every interaction meaningful. Every animation purposeful.
"""

from __future__ import annotations
import copy
import streamlit as st
from core import storage, gamification as game, content_bank as cb

# ============================================================
# DESIGN TOKENS — EXPANDED PREMIUM PALETTE
# ============================================================

THEMES = {
    "Neon Green":  {"primary": "#58CC02", "primary_dark": "#4CAF00", "accent": "#89E219", "glow": "#58CC0240", "aurora": "#58CC0215", "warm": "#7CB342"},
    "Electric Blue": {"primary": "#1CB0F6", "primary_dark": "#1695D1", "accent": "#7CD5FF", "glow": "#1CB0F640", "aurora": "#1CB0F615", "warm": "#42A5F5"},
    "Vivid Purple": {"primary": "#CE82FF", "primary_dark": "#B76EF0", "accent": "#E9C4FF", "glow": "#CE82FF40", "aurora": "#CE82FF15", "warm": "#AB47BC"},
    "Coral Orange": {"primary": "#FF9600", "primary_dark": "#E68600", "accent": "#FFBC42", "glow": "#FF960040", "aurora": "#FF960015", "warm": "#FF7043"},
    "Hot Pink":     {"primary": "#FF4B4B", "primary_dark": "#E04343", "accent": "#FF8A8A", "glow": "#FF4B4B40", "aurora": "#FF4B4B15", "warm": "#EC407A"},
    "Teal Ocean":   {"primary": "#2DD4BF", "primary_dark": "#14B8A6", "accent": "#5EEAD4", "glow": "#2DD4BF40", "aurora": "#2DD4BF15", "warm": "#26A69A"},
    "Royal Gold":   {"primary": "#FFD700", "primary_dark": "#D4AF37", "accent": "#FFE44D", "glow": "#FFD70040", "aurora": "#FFD70015", "warm": "#FFC107"},
}

AVATARS = ["🐕", "🦊", "🐸", "🦄", "🐨", "🦋", "🐧", "🦁", "🐢", "🐙", "🦉", "🐲", "🦩", "🦥", "🦦", "🦈", "🦚"]
AVATAR_UNLOCK_LEVEL = {"🐕": 1, "🦊": 2, "🐸": 3, "🦄": 5, "🐙": 7, "🦉": 10, "🐲": 12, "🦩": 14, "🦥": 16, "🦦": 18, "🦈": 20, "🦚": 25}


def avatars_unlocked_at(level: int) -> list:
    return [a for a in AVATARS if level >= AVATAR_UNLOCK_LEVEL.get(a, 1)]


# ============================================================
# GLOBAL STYLES — ULTIMATE PREMIUM
# ============================================================

def inject_theme(theme_name: str):
    t = THEMES.get(theme_name, THEMES["Neon Green"])
    primary = t["primary"]
    primary_dark = t["primary_dark"]
    accent = t["accent"]
    glow = t["glow"]
    aurora = t["aurora"]
    warm = t["warm"]

    # Core palette
    bg = "#08080D"
    bg_gradient = "#0C0C14"
    surface = "#111118"
    surface_hi = "#1A1A24"
    surface_glow = "rgba(17,17,24,0.9)"
    border = "rgba(255,255,255,0.05)"
    border_hover = "rgba(255,255,255,0.12)"
    border_accent = f"{primary}25"
    text = "#F5F5FA"
    text_muted = "#9A9AAF"
    text_dim = "#525266"
    text_subtle = "#3A3A4A"

    # Semantic colors
    success = "#58CC02"
    warning = "#FF9600"
    error = "#FF4B4B"
    info = "#1CB0F6"
    crown = "#FFD700"
    fire = "#FF5E00"

    # Shadows
    shadow_sm = "0 2px 8px rgba(0,0,0,0.3)"
    shadow_md = "0 8px 24px rgba(0,0,0,0.4)"
    shadow_lg = "0 16px 48px rgba(0,0,0,0.5)"
    shadow_glow = f"0 0 30px {glow}, 0 0 60px {glow}30"
    shadow_inner = "inset 0 2px 4px rgba(0,0,0,0.2)"

    st.markdown(
        f"""
        <style>
        /* ── FONTS ─────────────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        html, body, .stApp {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: {bg};
            color: {text};
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: optimizeLegibility;
        }}

        /* Outfit for headings — geometric, modern, premium */
        h1, h2, h3, h4, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
            font-family: 'Outfit', sans-serif !important;
            font-weight: 800 !important;
            letter-spacing: -0.03em;
            line-height: 1.15;
            color: {text};
        }}
        h1 {{ font-size: 2.5rem !important; }}
        h2 {{ font-size: 1.8rem !important; }}
        h3 {{ font-size: 1.4rem !important; }}

        /* Mono for data/numbers */
        .mono {{ font-family: 'JetBrains Mono', monospace !important; }}

        /* ── AURORA BACKGROUND — animated mesh gradient ─────────── */
        .stApp {{
            background:
                radial-gradient(ellipse 1000px 700px at 10% -5%, {aurora} 0%, transparent 50%),
                radial-gradient(ellipse 800px 600px at 90% 5%, {glow}12 0%, transparent 45%),
                radial-gradient(ellipse 500px 400px at 50% 105%, {aurora} 0%, transparent 40%),
                radial-gradient(ellipse 300px 300px at 70% 50%, {warm}08 0%, transparent 50%),
                linear-gradient(180deg, {bg_gradient} 0%, {bg} 40%, {bg} 100%);
            background-attachment: fixed;
            min-height: 100vh;
        }}

        /* ── CUSTOM SCROLLBAR — ultra-sleek ────────────────────── */
        ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; margin: 4px; }}
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, {text_subtle}, {text_dim});
            border-radius: 999px;
            border: 2px solid transparent;
            background-clip: padding-box;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: linear-gradient(180deg, {text_dim}, {text_muted});
        }}
        ::-webkit-scrollbar-corner {{ background: transparent; }}

        /* ── TEXT SELECTION ────────────────────────────────────── */
        ::selection {{
            background: {primary}35;
            color: #FFFFFF;
            text-shadow: 0 0 8px {primary}60;
        }}

        /* ── SIDEBAR — frosted glass rail ──────────────────────── */
        section[data-testid="stSidebar"] {{
            background: rgba(5,5,8,0.92);
            backdrop-filter: blur(24px) saturate(200%);
            -webkit-backdrop-filter: blur(24px) saturate(200%);
            border-right: 1px solid {border};
        }}
        section[data-testid="stSidebar"] .block-container {{
            padding-top: 1.2rem;
        }}

        /* ── SIDEBAR NAV — premium pill system ─────────────────── */
        [data-testid="stSidebarNav"] {{ padding: 0 12px; }}
        [data-testid="stSidebarNav"] a, [data-testid="stSidebarNavLink"] {{
            border-radius: 14px;
            margin: 3px 0;
            padding: 11px 16px !important;
            color: {text_muted} !important;
            font-weight: 700;
            font-family: 'Outfit', sans-serif;
            font-size: 14px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1.5px solid transparent;
            position: relative;
            overflow: hidden;
        }}
        [data-testid="stSidebarNav"] a:hover, [data-testid="stSidebarNavLink"]:hover {{
            background: {surface};
            color: {text} !important;
            transform: translateX(3px);
            border-color: {border_hover};
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"], [data-testid="stSidebarNavLink"][aria-current="page"] {{
            background: linear-gradient(135deg, {primary}12, {primary}05);
            color: {primary} !important;
            border-color: {primary}30;
            box-shadow: 0 0 24px {glow}, inset 0 1px 0 rgba(255,255,255,0.05);
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"]::before {{
            content: "";
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 3px;
            height: 50%;
            background: linear-gradient(180deg, {primary}, {accent});
            border-radius: 0 3px 3px 0;
            box-shadow: 0 0 8px {primary}80;
        }}

        /* ── BUTTONS — 3D physical with shimmer ────────────────── */
        .stButton > button, .stFormSubmitButton > button {{
            background: linear-gradient(180deg, {primary}, {primary_dark}) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 16px !important;
            border-bottom: 4px solid {primary_dark} !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 800 !important;
            font-size: 15px !important;
            letter-spacing: 0.02em;
            padding: 14px 28px !important;
            transition: all 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
            box-shadow: 0 4px 0 {primary_dark}, 0 8px 24px {glow}, inset 0 1px 0 rgba(255,255,255,0.15);
            position: relative;
            overflow: hidden;
        }}
        .stButton > button::after {{
            content: "";
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 60%);
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        }}
        .stButton > button::before {{
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent);
            transition: left 0.6s ease;
            pointer-events: none;
        }}
        .stButton > button:hover::before {{
            left: 100%;
        }}
        .stButton > button:hover::after {{
            opacity: 1;
        }}
        .stButton > button:hover {{
            filter: brightness(1.15) saturate(1.1);
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 7px 0 {primary_dark}, 0 14px 36px {glow}, inset 0 1px 0 rgba(255,255,255,0.2);
        }}
        .stButton > button:active {{
            transform: translateY(2px) scale(0.98);
            box-shadow: 0 2px 0 {primary_dark}, 0 4px 12px {glow};
            border-bottom-width: 2px !important;
            transition: all 0.08s ease;
        }}
        .stButton > button:disabled {{
            opacity: 0.35;
            filter: grayscale(0.7) brightness(0.8);
            box-shadow: none;
            border-bottom: none !important;
            transform: none;
            cursor: not-allowed;
        }}

        /* Secondary/outline variant */
        .stButton > button[kind="secondary"] {{
            background: {surface} !important;
            color: {text} !important;
            border: 1.5px solid {border} !important;
            border-bottom: 4px solid rgba(255,255,255,0.04) !important;
            box-shadow: 0 4px 0 rgba(255,255,255,0.03), inset 0 1px 0 rgba(255,255,255,0.03);
        }}
        .stButton > button[kind="secondary"]:hover {{
            background: {surface_hi} !important;
            border-color: {border_hover} !important;
            box-shadow: 0 4px 0 rgba(255,255,255,0.05), 0 8px 24px rgba(0,0,0,0.2);
        }}

        /* ── INPUTS — glassmorphic with focus ring ────────────── */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div, [data-testid="stChatInput"] {{
            background: {surface} !important;
            border-radius: 16px !important;
            border: 1.5px solid {border} !important;
            color: {text} !important;
            font-family: 'Inter', sans-serif;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }}
        div[data-baseweb="input"]:focus-within > div, div[data-baseweb="select"]:focus-within > div,
        div[data-baseweb="textarea"]:focus-within > div {{
            border-color: {primary} !important;
            box-shadow: 0 0 0 4px {glow}, 0 0 24px {glow}, inset 0 2px 4px rgba(0,0,0,0.1);
        }}
        input, textarea, [data-testid="stChatInput"] textarea {{
            color: {text} !important;
            font-family: 'Inter', sans-serif !important;
            caret-color: {primary};
            font-size: 15px !important;
        }}
        [data-testid="stChatInput"] textarea::placeholder {{
            color: {text_dim} !important;
            font-weight: 400;
        }}

        /* ── METRICS — premium stat cards ──────────────────────── */
        div[data-testid="stMetric"] {{
            background: {surface_glow};
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid {border};
            border-radius: 24px;
            padding: 24px 20px;
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        div[data-testid="stMetric"]::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, {primary}, {accent}, transparent);
            opacity: 0;
            transition: opacity 0.35s ease;
        }}
        div[data-testid="stMetric"]::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 50% 0%, {primary}08, transparent 70%);
            opacity: 0;
            transition: opacity 0.35s ease;
            pointer-events: none;
        }}
        div[data-testid="stMetric"]:hover {{
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 20px 50px rgba(0,0,0,0.45), 0 0 0 1px {primary}18;
            border-color: {primary}20;
        }}
        div[data-testid="stMetric"]:hover::before,
        div[data-testid="stMetric"]:hover::after {{
            opacity: 1;
        }}
        div[data-testid="stMetricValue"] {{
            font-family: 'Outfit', sans-serif !important;
            font-weight: 900 !important;
            font-size: 2.4rem !important;
            background: linear-gradient(135deg, {primary}, {accent});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.02em;
        }}
        div[data-testid="stMetricLabel"] {{
            color: {text_muted} !important;
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            font-size: 0.85rem;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }}

        /* ── PROGRESS BARS — animated shimmer ──────────────────── */
        div[data-testid="stProgress"] > div {{
            background: {surface_hi};
            border-radius: 999px;
            height: 12px;
            overflow: hidden;
            position: relative;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
        }}
        div[data-testid="stProgress"] > div > div {{
            background: linear-gradient(90deg, {primary}, {accent});
            border-radius: 999px;
            transition: width 0.7s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        div[data-testid="stProgress"] > div > div::after {{
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
            animation: progress-shimmer 2s ease-in-out infinite;
        }}
        @keyframes progress-shimmer {{
            0% {{ left: -100%; }}
            100% {{ left: 100%; }}
        }}

        /* ── CARDS / CONTAINERS — elevated glass ──────────────── */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {surface_glow};
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid {border} !important;
            border-radius: 28px !important;
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 15%;
            right: 15%;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 50% 0%, {primary}06, transparent 60%);
            opacity: 0;
            transition: opacity 0.35s ease;
            pointer-events: none;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
            background: rgba(26,26,36,0.85);
            border-color: {primary}20 !important;
            transform: translateY(-4px);
            box-shadow: 0 24px 56px rgba(0,0,0,0.35), 0 0 0 1px {primary}12;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:hover::after {{
            opacity: 1;
        }}

        /* ── CHAT MESSAGES — premium bubbles ────────────────────── */
        [data-testid="stChatMessage"] {{
            background: {surface};
            border: 1px solid {border};
            border-radius: 24px;
            padding: 18px 22px;
            margin-bottom: 14px;
            transition: all 0.25s ease;
            position: relative;
        }}
        [data-testid="stChatMessage"]:hover {{
            border-color: {border_hover};
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
            transform: translateX(2px);
        }}
        [data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"] {{
            background: linear-gradient(135deg, {primary}25, {primary}10);
            border-radius: 50%;
            border: 2px solid {primary}40;
            box-shadow: 0 0 12px {primary}30;
        }}
        [data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"] {{
            background: {surface_hi};
            border-radius: 50%;
            border: 2px solid {border};
        }}

        /* ── TABS — underline with glow ────────────────────────── */
        button[data-baseweb="tab"] {{
            color: {text_muted};
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            font-size: 15px;
            padding: 14px 22px !important;
            transition: all 0.2s ease;
            letter-spacing: 0.01em;
        }}
        button[data-baseweb="tab"]:hover {{
            color: {text};
            background: rgba(255,255,255,0.02);
            border-radius: 12px 12px 0 0;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {primary};
        }}
        div[data-baseweb="tab-highlight"] {{
            background: linear-gradient(90deg, {primary}, {accent}) !important;
            height: 3px !important;
            border-radius: 999px;
            box-shadow: 0 0 10px {glow};
        }}

        /* ── SELECT BOXES ──────────────────────────────────────── */
        div[data-baseweb="select"] {{
            background: {surface} !important;
            border-radius: 16px !important;
        }}
        div[data-baseweb="select"] > div {{
            border-radius: 16px !important;
            border: 1.5px solid {border} !important;
            transition: all 0.2s ease;
        }}
        div[data-baseweb="select"] > div:hover {{
            border-color: {border_hover} !important;
        }}

        /* ── ALERTS / TOASTS — glass with accent bar ───────────── */
        div[data-testid="stAlert"] {{
            border-radius: 24px;
            border: 1px solid {border};
            background: {surface_glow};
            backdrop-filter: blur(16px);
            overflow: hidden;
            position: relative;
            transition: all 0.2s ease;
        }}
        div[data-testid="stAlert"]::before {{
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(180deg, {primary}, {accent});
            box-shadow: 0 0 8px {primary}50;
        }}
        div[data-testid="stAlert"] [data-testid="stAlertContent"] {{
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            font-size: 15px;
        }}
        div[data-testid="stAlert"]:hover {{
            border-color: {primary}20;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }}

        /* ── EXPANDER ──────────────────────────────────────────── */
        details {{
            background: {surface};
            border: 1px solid {border};
            border-radius: 24px;
            overflow: hidden;
            transition: all 0.2s ease;
        }}
        details:hover {{
            border-color: {border_hover};
        }}
        details summary {{
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            padding: 18px 24px;
            cursor: pointer;
            transition: background 0.2s ease;
            font-size: 15px;
        }}
        details summary:hover {{
            background: {surface_hi};
        }}

        /* ── SLIDER ────────────────────────────────────────────── */
        div[data-testid="stSlider"] {{ padding: 12px 0; }}
        div[data-testid="stSlider"] > div > div {{
            background: {surface_hi} !important;
            height: 8px !important;
            border-radius: 999px;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
        }}
        div[data-testid="stSlider"] > div > div > div {{
            background: linear-gradient(90deg, {primary}, {accent}) !important;
        }}
        div[data-testid="stSlider"] [role="slider"] {{
            background: {primary} !important;
            border: 3px solid {bg} !important;
            box-shadow: 0 0 0 2px {primary}, 0 4px 16px {glow} !important;
            width: 20px !important;
            height: 20px !important;
        }}

        /* ── CHECKBOX / RADIO ──────────────────────────────────── */
        div[data-baseweb="checkbox"] > div > div, div[data-baseweb="radio"] > div > div {{
            border-color: {border} !important;
            background: {surface} !important;
            transition: all 0.2s ease;
        }}
        div[data-baseweb="checkbox"] [data-checked="true"] > div > div,
        div[data-baseweb="radio"] [data-checked="true"] > div > div {{
            background: linear-gradient(135deg, {primary}, {accent}) !important;
            border-color: {primary} !important;
            box-shadow: 0 0 12px {glow};
        }}

        /* ── TOOLTIP ───────────────────────────────────────────── */
        .stTooltip {{
            background: {surface_hi} !important;
            border: 1px solid {border} !important;
            border-radius: 14px !important;
            box-shadow: 0 12px 40px rgba(0,0,0,0.5) !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 13px !important;
            padding: 10px 16px !important;
        }}

        /* ── DIVIDER — premium gradient line ───────────────────── */
        .premium-divider {{
            height: 1px;
            background: linear-gradient(90deg, transparent, {border_hover}, transparent);
            margin: 40px 0;
            border: none;
            position: relative;
        }}
        .premium-divider::before {{
            content: "";
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 6px;
            height: 6px;
            background: {primary};
            border-radius: 50%;
            box-shadow: 0 0 12px {primary}60;
        }}

        /* ============================================================
           GAMIFICATION COMPONENTS — ULTIMATE PREMIUM
           ============================================================ */

        /* Streak badge — animated flame with depth */
        .streak-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            border-radius: 999px;
            background: linear-gradient(135deg, {fire}, #FF3D00);
            color: #FFFFFF;
            font-family: 'Outfit', sans-serif;
            font-weight: 900;
            font-size: 1.1rem;
            box-shadow: 0 4px 16px {fire}40, 0 0 0 1px rgba(255,255,255,0.1), inset 0 1px 0 rgba(255,255,255,0.15);
            animation: flame-pulse 2.5s ease-in-out infinite;
            position: relative;
            overflow: hidden;
        }}
        .streak-badge::before {{
            content: "";
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
            animation: flame-rotate 4s linear infinite;
        }}
        .streak-badge span {{
            position: relative;
            z-index: 1;
        }}
        @keyframes flame-pulse {{
            0%, 100% {{ transform: scale(1); box-shadow: 0 4px 16px {fire}40; }}
            50% {{ transform: scale(1.06); box-shadow: 0 6px 28px {fire}60; }}
        }}
        @keyframes flame-rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}

        /* XP pill — glass with gradient text */
        .xp-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 16px;
            border-radius: 999px;
            background: linear-gradient(135deg, {primary}15, {primary}05);
            border: 1px solid {primary}20;
            backdrop-filter: blur(8px);
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            font-size: 0.9rem;
            color: {primary};
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        /* Quest cards — glass with top glow */
        .quest-card {{
            border: 1px solid {border};
            border-radius: 28px;
            padding: 28px;
            margin-bottom: 16px;
            background: {surface_glow};
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        .quest-card::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, {primary}50, transparent);
            opacity: 0;
            transition: opacity 0.35s ease;
        }}
        .quest-card::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 50% 0%, {primary}08, transparent 60%);
            opacity: 0;
            transition: opacity 0.35s ease;
            pointer-events: none;
        }}
        .quest-card:hover {{
            border-color: {primary}25;
            transform: translateY(-4px);
            box-shadow: 0 20px 50px rgba(0,0,0,0.35), 0 0 0 1px {primary}12;
        }}
        .quest-card:hover::before,
        .quest-card:hover::after {{
            opacity: 1;
        }}
        .quest-card.completed {{
            border-color: {success}25;
            background: linear-gradient(135deg, {surface_glow}, {success}06);
        }}
        .quest-card.completed::before {{
            background: linear-gradient(90deg, transparent, {success}50, transparent);
            opacity: 1;
        }}
        .quest-card.completed::after {{
            background: radial-gradient(circle at 50% 0%, {success}08, transparent 60%);
            opacity: 1;
        }}

        /* Badge pills — 3D hover with glow */
        .badge-pill {{
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: {surface};
            border: 1.5px solid {border};
            border-radius: 24px;
            padding: 22px 18px;
            margin: 6px;
            text-align: center;
            min-width: 120px;
            transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative;
            overflow: hidden;
            cursor: default;
        }}
        .badge-pill::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 45%;
            background: linear-gradient(180deg, rgba(255,255,255,0.04), transparent);
            pointer-events: none;
            border-radius: 24px 24px 0 0;
        }}
        .badge-pill::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 50% 100%, {primary}06, transparent 70%);
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        }}
        .badge-pill:hover {{
            transform: translateY(-8px) scale(1.1);
            border-color: {primary}35;
            box-shadow: 0 24px 48px rgba(0,0,0,0.35), 0 0 30px {glow}, 0 0 0 1px {primary}15;
        }}
        .badge-pill:hover::after {{
            opacity: 1;
        }}
        .badge-pill .emoji {{
            font-size: 2.4rem;
            margin-bottom: 8px;
            filter: drop-shadow(0 3px 6px rgba(0,0,0,0.3));
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative;
            z-index: 1;
        }}
        .badge-pill:hover .emoji {{
            transform: scale(1.25) rotate(-8deg);
            filter: drop-shadow(0 6px 12px rgba(0,0,0,0.4));
        }}
        .badge-pill .name {{
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            font-size: 0.85rem;
            color: {text};
            position: relative;
            z-index: 1;
        }}
        .badge-pill .desc {{
            font-size: 0.7rem;
            color: {text_dim};
            margin-top: 4px;
            line-height: 1.3;
            position: relative;
            z-index: 1;
        }}
        .badge-pill.unlocked {{
            border-color: {crown}45;
            background: linear-gradient(135deg, {surface}, {crown}08);
            box-shadow: 0 4px 16px {crown}15;
        }}
        .badge-pill.unlocked:hover {{
            box-shadow: 0 24px 48px rgba(0,0,0,0.35), 0 0 30px {crown}25, 0 0 0 1px {crown}15;
        }}
        .badge-pill.locked {{
            opacity: 0.45;
            filter: saturate(0.3);
        }}
        .badge-pill.locked .emoji {{
            filter: grayscale(1) brightness(0.5);
        }}
        .badge-pill.locked .name {{
            color: {text_dim};
        }}

        /* Level ring — conic gradient with depth */
        .level-ring {{
            width: 92px;
            height: 92px;
            border-radius: 50%;
            background: conic-gradient({primary} 0% var(--progress), {surface_hi} var(--progress) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            box-shadow: 0 0 24px {glow}, inset 0 2px 8px rgba(0,0,0,0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .level-ring:hover {{
            transform: scale(1.08);
            box-shadow: 0 0 36px {glow}, inset 0 2px 8px rgba(0,0,0,0.3);
        }}
        .level-ring::before {{
            content: "";
            position: absolute;
            width: 72px;
            height: 72px;
            border-radius: 50%;
            background: {bg};
            box-shadow: inset 0 2px 8px rgba(0,0,0,0.5), 0 0 0 1px {border};
        }}
        .level-ring span {{
            position: relative;
            z-index: 1;
            font-family: 'Outfit', sans-serif;
            font-weight: 900;
            font-size: 1.7rem;
            background: linear-gradient(135deg, {primary}, {accent});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        /* Activity cards — premium hover with glow */
        .activity-card {{
            background: {surface};
            border: 1.5px solid {border};
            border-radius: 28px;
            padding: 36px 28px;
            text-align: center;
            transition: all 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative;
            overflow: hidden;
            cursor: pointer;
        }}
        .activity-card::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 100%;
            background: linear-gradient(180deg, {primary}0A, transparent 55%);
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        .activity-card::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 50% 0%, {primary}08, transparent 60%);
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        }}
        .activity-card:hover {{
            transform: translateY(-10px) scale(1.04);
            border-color: {primary}30;
            box-shadow: 0 28px 64px rgba(0,0,0,0.45), 0 0 0 1px {primary}18, 0 0 50px {glow};
        }}
        .activity-card:hover::before,
        .activity-card:hover::after {{
            opacity: 1;
        }}
        .activity-card .icon {{
            font-size: 4rem;
            margin-bottom: 20px;
            transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
            filter: drop-shadow(0 4px 10px rgba(0,0,0,0.3));
            position: relative;
            z-index: 1;
        }}
        .activity-card:hover .icon {{
            transform: scale(1.2) rotate(-10deg);
            filter: drop-shadow(0 8px 20px rgba(0,0,0,0.4));
        }}
        .activity-card h3 {{
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            margin: 0 0 10px;
            font-size: 1.4rem;
            position: relative;
            z-index: 1;
        }}
        .activity-card p {{
            margin: 0;
            color: {text_muted};
            font-size: 0.95rem;
            line-height: 1.5;
            position: relative;
            z-index: 1;
        }}

        /* Status cards — colored accent variants */
        .status-card {{
            background: {surface_glow};
            backdrop-filter: blur(20px);
            border: 1px solid {border};
            border-radius: 24px;
            padding: 24px;
            transition: all 0.25s ease;
            position: relative;
            overflow: hidden;
        }}
        .status-card::before {{
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(180deg, {primary}, {accent});
            opacity: 0;
            transition: opacity 0.25s ease;
        }}
        .status-card:hover {{
            border-color: {border_hover};
            transform: translateX(4px);
        }}
        .status-card:hover::before {{
            opacity: 1;
        }}
        .status-card.success {{
            border-color: {success}25;
            background: linear-gradient(135deg, {surface_glow}, {success}06);
        }}
        .status-card.success::before {{
            background: linear-gradient(180deg, {success}, {success}80);
            opacity: 1;
        }}
        .status-card.warning {{
            border-color: {warning}25;
            background: linear-gradient(135deg, {surface_glow}, {warning}06);
        }}
        .status-card.warning::before {{
            background: linear-gradient(180deg, {warning}, {warning}80);
            opacity: 1;
        }}
        .status-card .icon {{
            font-size: 1.6rem;
            margin-bottom: 10px;
        }}
        .status-card .title {{
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            margin: 0 0 6px;
            font-size: 1.1rem;
        }}
        .status-card .detail {{
            color: {text_muted};
            font-size: 0.9rem;
            line-height: 1.4;
        }}

        /* Skeleton loading */
        .skeleton {{
            background: linear-gradient(90deg, {surface_hi} 25%, {surface} 50%, {surface_hi} 75%);
            background-size: 200% 100%;
            animation: skeleton-shimmer 1.5s ease-in-out infinite;
            border-radius: 14px;
        }}
        @keyframes skeleton-shimmer {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}

        /* Toast notifications — glass slide-in */
        .toast-container {{
            position: fixed;
            top: 24px;
            right: 24px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 12px;
            pointer-events: none;
        }}
        .toast {{
            background: {surface_glow};
            backdrop-filter: blur(24px);
            border: 1px solid {border};
            border-radius: 20px;
            padding: 18px 28px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            gap: 14px;
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            font-size: 15px;
            animation: toast-slide-in 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
            pointer-events: auto;
            max-width: 420px;
        }}
        .toast.success {{ border-left: 4px solid {success}; }}
        .toast.error {{ border-left: 4px solid {error}; }}
        .toast.info {{ border-left: 4px solid {info}; }}
        @keyframes toast-slide-in {{
            from {{ opacity: 0; transform: translateX(50px) scale(0.9); }}
            to {{ opacity: 1; transform: translateX(0) scale(1); }}
        }}
        @keyframes toast-slide-out {{
            from {{ opacity: 1; transform: translateX(0); }}
            to {{ opacity: 0; transform: translateX(50px); }}
        }}

        /* Floating particles for celebrations */
        @keyframes float-up {{
            0% {{ transform: translateY(0) scale(1) rotate(0deg); opacity: 1; }}
            100% {{ transform: translateY(-150px) scale(0.2) rotate(720deg); opacity: 0; }}
        }}
        @keyframes float-down {{
            0% {{ transform: translateY(0) scale(1); opacity: 1; }}
            100% {{ transform: translateY(150px) scale(0.2); opacity: 0; }}
        }}
        @keyframes float-side {{
            0% {{ transform: translateX(0) scale(1); opacity: 1; }}
            100% {{ transform: translateX(var(--dx)) scale(0.3); opacity: 0; }}
        }}
        @keyframes spin-slow {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        @keyframes pulse-glow {{
            0%, 100% {{ box-shadow: 0 0 20px {glow}; }}
            50% {{ box-shadow: 0 0 40px {glow}, 0 0 60px {glow}40; }}
        }}
        .celebration-particle {{
            position: fixed;
            pointer-events: none;
            z-index: 9999;
            border-radius: 50%;
        }}

        /* Staggered fade-in for lists */
        .stagger-in > * {{
            opacity: 0;
            animation: stagger-fade 0.6s ease-out forwards;
        }}
        .stagger-in > *:nth-child(1) {{ animation-delay: 0.04s; }}
        .stagger-in > *:nth-child(2) {{ animation-delay: 0.08s; }}
        .stagger-in > *:nth-child(3) {{ animation-delay: 0.12s; }}
        .stagger-in > *:nth-child(4) {{ animation-delay: 0.16s; }}
        .stagger-in > *:nth-child(5) {{ animation-delay: 0.20s; }}
        .stagger-in > *:nth-child(6) {{ animation-delay: 0.24s; }}
        .stagger-in > *:nth-child(7) {{ animation-delay: 0.28s; }}
        .stagger-in > *:nth-child(8) {{ animation-delay: 0.32s; }}
        @keyframes stagger-fade {{
            from {{ opacity: 0; transform: translateY(16px) scale(0.97); }}
            to {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}

        /* Glow pulse for special elements */
        .glow-pulse {{
            animation: pulse-glow 2s ease-in-out infinite;
        }}

        /* Focus states */
        *:focus-visible {{
            outline: 2.5px solid {primary};
            outline-offset: 3px;
            border-radius: 6px;
        }}

        /* Reduced motion */
        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# APP STATE & PROFILE MANAGEMENT
# ============================================================

def init_app_state():
    if "db" not in st.session_state:
        st.session_state.db = storage.load_db()
        st.session_state.db_snapshot = copy.deepcopy(st.session_state.db)
    if "active_profile" not in st.session_state:
        st.session_state.active_profile = None


def save():
    merged, status = storage.merge_and_save(
        st.session_state.db, st.session_state.get("db_snapshot", st.session_state.db)
    )
    st.session_state.db = merged
    st.session_state.db_snapshot = copy.deepcopy(merged)
    if status.get("gist_ok") is False:
        st.session_state["_last_gist_error"] = status.get("gist_error")
    elif status.get("gist_ok") is True:
        st.session_state.pop("_last_gist_error", None)
    return status


def require_profile():
    init_app_state()
    if not st.session_state.active_profile or st.session_state.active_profile not in st.session_state.db["profiles"]:
        st.warning("👋 Choose your profile first on the Home page!")
        st.stop()
    profile = st.session_state.db["profiles"][st.session_state.active_profile]
    inject_theme(profile.get("theme", "Neon Green"))
    bonus = game.record_daily_login(profile)
    game.ensure_quest_slots(profile)
    if bonus:
        st.toast(f"🔥 Streak bonus! +{bonus} XP", icon="🔥")
    if bonus:
        save()
        profile = st.session_state.db["profiles"][st.session_state.active_profile]
    return profile


# ============================================================
# SIDEBAR — ULTIMATE PREMIUM
# ============================================================

def sidebar_switcher():
    db = st.session_state.db
    names = list(db["profiles"].keys())
    if not names:
        return

    with st.sidebar:
        st.markdown("### 👤 Who's learning?")
        current = st.session_state.active_profile if st.session_state.active_profile in names else names[0]

        profile_options = {}
        for n in names:
            p = db["profiles"][n]
            lvl = game.compute_level(p["xp"])
            profile_options[f"{p['avatar']} {n}  •  Lvl {lvl}"] = n

        current_label = f"{db['profiles'][current]['avatar']} {current}  •  Lvl {game.compute_level(db['profiles'][current]['xp'])}"
        choice_label = st.selectbox(
            "Switch profile",
            list(profile_options.keys()),
            index=list(profile_options.keys()).index(current_label) if current_label in profile_options else 0,
            key="profile_switcher",
            label_visibility="collapsed"
        )
        choice = profile_options[choice_label]

        if choice != st.session_state.active_profile:
            st.session_state.active_profile = choice
            st.rerun()

        profile = db["profiles"][choice]

        # Streak badge with flame
        streak = profile["streak"]["current"]
        st.markdown(
            f'<div class="streak-badge"><span>🔥 {streak} day streak</span></div>',
            unsafe_allow_html=True
        )

        # Level ring
        level = game.compute_level(profile["xp"])
        _, xp_left, progress = game.xp_to_next_level(profile["xp"])
        progress_pct = int(progress * 100)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(
                f'<div class="level-ring" style="--progress: {progress_pct}%;"><span>{level}</span></div>',
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(f"**Level {level}**")
            if xp_left is not None:
                st.markdown(f'<span class="xp-pill">⭐ {xp_left} XP to next</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="xp-pill">👑 Max level!</span>', unsafe_allow_html=True)
            st.markdown(f"🪙 **{profile['coins']}** coins")

        st.caption(f"CEFR: **{profile['level']}**")

        if st.session_state.get("_last_gist_error"):
            st.caption("⚠️ Backup unavailable (see Settings)")

        st.markdown("---")


# ============================================================
# CELEBRATION HELPERS — ULTIMATE
# ============================================================

def show_new_badges(newly: list):
    for b in newly:
        st.balloons()
        st.success(f"🏅 **{b['emoji']} {b['name']}** unlocked! {b['desc']}")


def show_level_up(result: dict):
    if result.get("leveled_up"):
        st.balloons()
        st.success(f"🎉 **Level {result['new_level']}!** {result.get('unlock', '')}")
        # Multi-directional confetti burst
        colors = ["#58CC02", "#1CB0F6", "#CE82FF", "#FF9600", "#FF4B4B", "#FFD700", "#2DD4BF", "#FF5E00", "#E040FB", "#00E676"]
        st.markdown(
            f"""
            <script>
            (function() {{
                const colors = {colors};
                for (let i = 0; i < 60; i++) {{
                    const p = document.createElement('div');
                    p.className = 'celebration-particle';
                    const size = Math.random() * 12 + 6;
                    const isUp = Math.random() > 0.4;
                    const isSide = Math.random() > 0.7;
                    const dx = (Math.random() - 0.5) * 200;
                    let anim, startY;
                    if (isSide) {{
                        p.style.setProperty('--dx', dx + 'px');
                        anim = 'float-side';
                        startY = '50';
                    }} else if (isUp) {{
                        anim = 'float-up';
                        startY = '65';
                    }} else {{
                        anim = 'float-down';
                        startY = '35';
                    }}
                    p.style.cssText = 'position:fixed;left:' + Math.random()*100 + 'vw;top:' + startY + 'vh;' +
                        'width:' + size + 'px;height:' + size + 'px;' +
                        'border-radius:' + (Math.random() > 0.4 ? '50%' : '3px') + ';' +
                        'background:' + colors[Math.floor(Math.random()*colors.length)] + ';' +
                        'box-shadow:0 0 ' + (size*2.5) + 'px ' + colors[Math.floor(Math.random()*colors.length)] + '50,' +
                        '0 0 ' + (size*4) + 'px ' + colors[Math.floor(Math.random()*colors.length)] + '20;' +
                        'animation:' + anim + ' ' + (Math.random()*1.5+1.5) + 's ease-out forwards;' +
                        'animation-delay:' + (Math.random()*0.3) + 's;';
                    document.body.appendChild(p);
                    setTimeout(() => p.remove(), 3500);
                }}
            }})();
            </script>
            """,
            unsafe_allow_html=True,
        )
