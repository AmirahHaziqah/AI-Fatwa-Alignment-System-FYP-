import base64
import html
import os
import textwrap
from typing import Optional

import streamlit as st

from utils import get_score_tier, get_score_tier_colors, get_score_css_class

COLORS = {
    # Requested palette
    "linen": "#F5E9E2",
    "almond_silk": "#E3B5A4",
    "lobster_pink": "#D44D5C",
    "wine_plum": "#773344",
    "midnight_violet": "#160029",

    # Semantic aliases used across the dashboard
    "navy": "#160029",
    "navy_md": "#773344",
    "navy_lt": "#D44D5C",
    "slate": "#773344",
    "slate_lt": "#E3B5A4",
    "teal": "#D44D5C",
    "teal_lt": "#D44D5C",
    "accent_red": "#D44D5C",

    # Neutrals
    "white": "#FFFFFF",
    "off_white": "#F9F1EC",
    "surface": "#F5E9E2",
    "surface_alt": "#EED7CE",
    "border": "#E3B5A4",
    "muted": "#8B6771",

    # Text
    "text_primary": "#2A1421",
    "text_secondary": "#5D3945",
    "text_muted": "#8B6771",

    # Status colours
    "success": "#2E8B57",
    "warning": "#B7791F",
    "danger": "#B33A4A",
    "info": "#773344",
}


def _image_to_data_uri(image_path: Optional[str]) -> Optional[str]:
    if not image_path:
        return None
    if not os.path.exists(image_path):
        return None

    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    mime = mime_map.get(ext)
    if not mime:
        return None

    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return None


def apply_theme():
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Inter+Tight:wght@500;600;700;800&display=swap');

/* ── BASE FONT SIZE — optimized for perfect 100% zoom ── */
html {{
    font-size: 16px !important;
}}
body {{
    overflow-x: hidden !important;
    color: {COLORS["text_primary"]};
}}
.stApp {{
    overflow-x: hidden !important;
}}

* {{
    box-sizing: border-box;
}}

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

html {{
    scroll-behavior: smooth;
}}

/* ── APP BACKGROUND ──────────────────────────────────── */
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(180deg, #f4f6f9 0%, #efe6ea 100%) !important;
    color: {COLORS["text_primary"]};
}}

.block-container {{
    padding-top: 0.6rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 1400px !important;
    width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
}}

[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stToolbar"] {{ right: 1rem; }}

/* ── SIDEBAR ─────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    min-width: 280px !important;
    max-width: 280px !important;
    width: 280px !important;
    background: linear-gradient(180deg, #160029 0%, #773344 55%, #5f2840 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
    box-shadow: 16px 0 34px rgba(22,0,41,0.18) !important;
}}

[data-testid="stSidebar"] > div:first-child {{
    background: transparent !important;
    padding: 0.8rem 0.7rem 0.9rem 0.7rem !important;
}}

[data-testid="stSidebar"] * {{
    color: rgba(255,255,255,0.90) !important;
}}

[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li,
[data-testid="stSidebar"] .stMarkdown span {{
    color: rgba(255,255,255,0.82) !important;
}}

/* ── SIDEBAR BRAND ───────────────────────────────────── */
.sidebar-brand-card {{
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-left: 6px solid #d44d5c;
    border-radius: 18px;
    padding: 1.2rem 1rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 10px 24px rgba(33,50,65,0.22);
}}
.sidebar-brand-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 0.9rem;
    line-height: 1.3;
    color: #FFFFFF !important;
    margin-bottom: 0.25rem;
    font-weight: 700;
}}
.sidebar-brand-subtitle {{
    font-size: 0.8rem;
    line-height: 1.5;
    color: rgba(255,255,255,0.78) !important;
}}

/* ── SIDEBAR CLEAN HEADER ────────────────────────────── */
.sidebar-clean-header {{
    padding: 0.5rem 0.2rem 1rem 0.2rem !important;
    margin-bottom: 1rem !important;
}}

.sidebar-kicker-line {{
    width: 72px !important;
    height: 4px !important;
    background: {COLORS["teal_lt"]} !important;
    margin-bottom: 1rem !important;
    border-radius: 2px;
}}

.sidebar-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.5rem !important;
    line-height: 1.2 !important;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.025em !important;
    margin: 0 0 0.8rem 0 !important;
}}

.sidebar-subtitle {{
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem !important;
    line-height: 1.6 !important;
    font-weight: 400;
    color: rgba(255,255,255,0.78) !important;
    margin: 0;
}}

/* ── SIDEBAR WORKSPACE CARD ──────────────────────────── */
.sidebar-workspace-card {{
    background: rgba(255,255,255,0.08) !important;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(158,179,194,0.18) !important;
    box-shadow: 0 12px 26px rgba(13, 24, 47, 0.18) !important;
    border-radius: 18px !important;
    padding: 1rem !important;
    margin-bottom: 0.8rem;
}}

.sidebar-kicker {{
    display: inline-flex;
    align-items: center;
    padding: 0.28rem 0.7rem;
    border-radius: 999px;
    background: rgba(158,179,194,0.16) !important;
    color: #DCE7EE !important;
    border: 1px solid rgba(158,179,194,0.22) !important;
    font-size: 0.7rem !important;
    font-weight: 700;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}}

.sidebar-workspace-title {{
    font-size: 1.1rem;
    font-weight: 800;
    line-height: 1.3;
    color: #FFFFFF !important;
    margin-bottom: 0.25rem;
}}

.sidebar-workspace-subtitle {{
    font-size: 0.8rem;
    line-height: 1.5;
    color: rgba(255,255,255,0.78) !important;
    margin-bottom: 0.5rem;
}}

.sidebar-highlight-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.7rem !important;
    margin-top: 0.8rem;
}}

.sidebar-highlight-chip {{
    background: rgba(255,255,255,0.95) !important;
    border: 1px solid rgba(158,179,194,0.22) !important;
    border-top: 4px solid #1C7293 !important;
    border-radius: 14px;
    padding: 0.7rem 0.7rem;
}}

.sidebar-highlight-label {{
    font-size: 0.7rem;
    color: #5E7186 !important;
    margin-bottom: 0.25rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}

.sidebar-highlight-value {{
    font-size: 1.1rem !important;
    color: #162033 !important;
    font-weight: 800;
}}

/* ── SIDEBAR SECTION CARD ────────────────────────────── */
.sidebar-section-card {{
    background: rgba(255,255,255,0.08) !important;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(158,179,194,0.18) !important;
    box-shadow: 0 12px 26px rgba(13, 24, 47, 0.18) !important;
    border-radius: 18px !important;
    padding: 1rem !important;
    margin-bottom: 0.9rem !important;
}}

.sidebar-section-card * {{
    color: rgba(255,255,255,0.92) !important;
}}

.sidebar-section-title {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.8rem !important;
    font-weight: 800;
    margin-bottom: 0.7rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid rgba(158,179,194,0.2) !important;
    color: #DCE7EE !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}}

/* ── SIDEBAR PROGRESS ────────────────────────────────── */
.sidebar-progress-stack {{
    display: grid;
    gap: 0.7rem;
}}

.sidebar-progress-item {{
    display: grid;
    gap: 0.4rem;
}}

.sidebar-progress-top {{
    display: flex;
    justify-content: space-between;
    gap: 0.3rem;
    font-size: 0.8rem;
}}

.sidebar-progress-name {{
    color: rgba(255,255,255,0.82) !important;
    font-weight: 700;
}}

.sidebar-progress-value {{
    color: {COLORS["teal_lt"]} !important;
    font-weight: 800;
}}

.sidebar-progress-bar {{
    height: 8px !important;
    border-radius: 999px;
    background: rgba(255,255,255,0.10);
    overflow: hidden;
}}

.sidebar-progress-fill {{
    height: 100%;
    border-radius: 999px;
    box-shadow: 0 0 0 1px rgba(255,255,255,0.08) inset;
}}

/* ── SIDEBAR ACTION LIST ─────────────────────────────── */
.sidebar-action-list {{
    display: grid;
    gap: 0.6rem;
}}

.sidebar-action-item {{
    display: flex;
    gap: 0.7rem;
    align-items: flex-start;
    padding: 0.8rem 0.9rem;
    border-radius: 14px !important;
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(158,179,194,0.14) !important;
}}

.sidebar-action-icon {{
    width: 34px;
    height: 34px;
    min-width: 34px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #cb4a5e !important;
    color: #FFFFFF !important;
    font-size: 0.9rem;
    font-weight: 800;
}}

.sidebar-action-title {{
    font-size: 0.85rem;
    font-weight: 800;
    color: #FFFFFF !important;
    margin-bottom: 0.25rem;
}}

.sidebar-action-text {{
    font-size: 0.8rem;
    line-height: 1.5;
    color: rgba(255,255,255,0.78) !important;
}}

/* ── SIDEBAR MINI NOTE ───────────────────────────────── */
.sidebar-mini-note {{
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(158,179,194,0.14) !important;
    border-radius: 14px;
    padding: 0.9rem 1rem;
    color: rgba(255,255,255,0.88) !important;
    line-height: 1.5;
    font-size: 0.85rem;
}}

.sidebar-mini-note strong {{
    color: #FFFFFF !important;
}}

/* ── SIDEBAR TOPIC PILLS ─────────────────────────────── */
.sidebar-pill-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}}

.sidebar-topic-pill {{
    display: inline-flex;
    align-items: center;
    padding: 0.4rem 0.8rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.10) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    color: #ffd9e9 !important;
    font-size: 0.8rem;
    font-weight: 700;
    line-height: 1.2;
    box-shadow: 0 6px 12px rgba(0,0,0,0.12);
}}

/* ── SIDEBAR LEGEND CARD ─────────────────────────────── */
.sidebar-legend-card {{
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(158,179,194,0.14) !important;
    border-radius: 18px !important;
    padding: 1rem !important;
    margin-bottom: 0.9rem !important;
}}

.sidebar-legend-grid {{
    display: grid;
    gap: 0.5rem;
}}

.sidebar-legend-item {{
    display: flex;
    gap: 0.6rem;
    align-items: flex-start;
    padding: 0.7rem 0.8rem;
    border-radius: 14px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(158,179,194,0.14);
}}

.sidebar-legend-dot {{
    width: 12px;
    height: 12px;
    border-radius: 999px;
    margin-top: 0.2rem;
    box-shadow: 0 0 0 3px rgba(255,255,255,0.08);
}}

.sidebar-legend-name {{
    font-size: 0.85rem;
    font-weight: 800;
    color: #FFFFFF;
}}

.sidebar-legend-text {{
    font-size: 0.8rem;
    line-height: 1.4;
    color: rgba(255,255,255,0.74);
}}

.sidebar-legend-note {{
    margin-top: 0.8rem;
    font-size: 0.8rem;
    line-height: 1.45;
    color: rgba(255,255,255,0.74);
}}

/* ── TABS ────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    background: #f5e9e2 !important;
    border-radius: 16px !important;
    padding: 6px !important;
    gap: 4px !important;
    border: 1px solid #e3b5a4 !important;
}}

.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    border-radius: 10px !important;
    color: #8b6771 !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1rem !important;
    border: none !important;
    transition: all 0.18s ease !important;
}}

.stTabs [aria-selected="true"] {{
    background: #cb4a5e !important;
    color: white !important;
    font-weight: 700 !important;
    box-shadow: 0 6px 18px rgba(119,51,68,0.20) !important;
}}

.stTabs [data-baseweb="tab-panel"] {{
    padding-top: 1.5rem;
}}

/* ── HERO BANNER (MAIN CONTENT) ──────────────────────── */
.hero-image-wrap {{
    position: relative;
    height: 200px !important;
    border-radius: 28px !important;
    overflow: hidden;
    margin-bottom: 1rem;
    border: 1px solid rgba(158,179,194,0.20);
    box-shadow: 0 18px 40px rgba(22, 0, 41, 0.14);
    background: linear-gradient(90deg, #0b2a56 0%, #4c224d 55%, #65104d 100%);
}}

.hero-single-image {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center;
    display: block;
    opacity: 0.62;
    filter: saturate(0.92) contrast(1.02) brightness(0.80);
}}

.hero-image-overlay {{
    position: absolute;
    inset: 0;
    z-index: 3;
    background:
        linear-gradient(
            90deg,
            rgba(8, 33, 69, 0.92) 0%,
            rgba(21, 28, 73, 0.78) 26%,
            rgba(56, 24, 72, 0.40) 52%,
            rgba(85, 14, 67, 0.24) 100%
        ) !important;
    display: flex;
    align-items: center;
    justify-content: flex-start !important;
    text-align: left !important;
    padding: 2rem 2rem;
}}

.hero-image-content {{
    width: 100%;
    max-width: 60% !important;
}}

.hero-kicker {{
    display: inline-flex;
    align-items: center;
    padding: 0.45rem 1rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.20);
    color: #ffffff;
    font-size: 0.8rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
    backdrop-filter: blur(4px);
}}

.hero-image-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 2rem !important;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.03em;
    color: #ffffff !important;
    margin: 0 0 0.6rem 0;
    text-shadow: 0 8px 18px rgba(0,0,0,0.20) !important;
}}

.hero-image-subtitle {{
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    font-weight: 500;
    line-height: 1.5;
    color: rgba(255,255,255,0.92) !important;
    margin: 0;
    max-width: 92%;
    text-shadow: 0 2px 8px rgba(0,0,0,0.18);
}}

/* ── SECTION BANNER ──────────────────────────────────── */
.section-banner {{
    position: relative;
    width: 100%;
    min-height: 90px;
    border-radius: 20px;
    overflow: hidden;
    margin: 1.5rem 0 1.2rem 0;
    border: 1px solid #e3b5a4;
    box-shadow: 0 10px 28px rgba(59, 29, 74, 0.06);
    background: linear-gradient(135deg, #160029, #773344);
}}

.section-banner-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #FFFFFF;
    margin: 0;
    text-shadow: 0 2px 8px rgba(15,32,68,0.25);
    letter-spacing: 0.01em;
}}

/* ── CARDS ───────────────────────────────────────────── */
.soft-card, .card {{
    background: #FFFFFF;
    border-radius: 18px !important;
    padding: 1.1rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 10px 28px rgba(22, 32, 51, 0.06) !important;
    color: #2a1421;
}}

.card {{ transition: all 0.22s ease; height: 100%; }}
.card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(15,32,68,0.10);
    border-color: #e3b5a4;
}}

.card-header {{
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.5rem;
    padding-bottom: 0.6rem;
    border-bottom: 2px solid #f5e9e2;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}}

/* ── METRIC CARDS ────────────────────────────────────── */
.metric-card {{
    background: #FFFFFF;
    border-radius: 18px !important;
    padding: 1rem 1.2rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 10px 28px rgba(22, 32, 51, 0.06) !important;
    text-align: center;
    height: 100%;
    position: relative;
    overflow: hidden;
}}

.metric-card::before {{
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 5px;
    background: linear-gradient(90deg, #d44d5c 0%, #773344 100%) !important;
}}

.metric-card-good::before {{ background: #06A77D !important; }}
.metric-card-mid::before  {{ background: #F1A208 !important; }}
.metric-card-low::before  {{ background: #A31621 !important; }}

/* TITLE HIERARCHY — KEY RULE: section title > card title > body text */

.metric-label {{
    font-size: 0.8rem;
    font-weight: 700;
    color: #8b6771;
    margin-bottom: 0.6rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}

.metric-value {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: #773344;
    line-height: 1.1;
}}

.metric-value-good {{ color: #06A77D !important; }}
.metric-value-mid  {{ color: #C27D06 !important; }}
.metric-value-low  {{ color: #A31621 !important; }}

/* ── SECTION TITLES ──────────────────────────────────── */
/* These are the BIG titles — visible, clear labels for each section */
.section-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #773344;
    margin: 1.8rem 0 1rem 0;
    position: relative;
    display: inline-block;
    padding-bottom: 0.6rem;
    letter-spacing: -0.01em;
}}

.section-title::after {{
    content: '';
    position: absolute;
    left: 0; bottom: 0;
    width: 48px; height: 3px;
    background: linear-gradient(90deg, #d44d5c 0%, #773344 100%);
    border-radius: 2px;
}}

/* Section subtitle — slightly smaller than main title */
.section-subtitle {{
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #160029;
    margin: 1.3rem 0 0.9rem 0;
    letter-spacing: -0.01em;
}}

/* ── MESSAGE BOXES ───────────────────────────────────── */
.msg-box {{
    padding: 0.85rem 1rem;
    border-radius: 16px !important;
    margin: 1rem 0;
    background: #FFFFFF;
    border: 1px solid #e3b5a4;
    border-left: 5px solid #773344;
    box-shadow: 0 2px 8px rgba(15,32,68,0.05);
    color: #2a1421;
    line-height: 1.6;
    font-size: 0.9rem;
}}

.msg-box strong {{ color: #160029; }}
.msg-success {{ border-left-color: #06A77D !important; background: #f6fbf8 !important; }}
.msg-info    {{ border-left-color: #773344 !important; background: #faf4f8 !important; }}
.msg-warning {{ border-left-color: #F1A208 !important; background: #fff8ef !important; }}

/* ── KEYWORD CHIPS ───────────────────────────────────── */
.keyword-container {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.85rem;
}}

.keyword-match, .keyword-miss {{
    display: inline-flex;
    align-items: center;
    padding: 0.4rem 1rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
}}

.keyword-match {{
    background: rgba(25,135,84,0.10) !important;
    color: #198754 !important;
    border: 1px solid rgba(25,135,84,0.18) !important;
}}

.keyword-miss {{
    background: rgba(180,35,79,0.08) !important;
    color: #b4234f !important;
    border: 1px solid rgba(180,35,79,0.18) !important;
}}

/* ── FATWA BOX ───────────────────────────────────────── */
.fatwa-box {{
    background: #FFFFFF;
    border-radius: 18px !important;
    padding: 1.1rem 1.2rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 10px 28px rgba(22, 32, 51, 0.06) !important;
    color: #2a1421;
    margin-bottom: 0.75rem;
}}

.fatwa-meta-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.7rem;
}}

.fatwa-meta-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.35rem 0.75rem;
    border-radius: 8px;
    background: #f5e9e2;
    border: 1px solid #e3b5a4;
    color: #5f2840;
    font-size: 0.8rem;
    font-weight: 600;
}}

/* Fatwa title — big enough to read easily */
.fatwa-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.7rem;
    line-height: 1.3;
    word-break: break-word;
}}

.fatwa-text-panel {{
    background: linear-gradient(180deg, #ffffff 0%, #f9f1ec 100%);
    border: 1px solid #e3b5a4;
    border-radius: 12px;
    padding: 0.9rem 1rem;
}}

/* Fatwa body text — comfortable reading size */
.fatwa-text-panel p {{
    margin: 0;
    color: #160029;
    line-height: 1.7;
    font-size: 0.95rem;
    white-space: pre-wrap;
    word-break: break-word;
}}

/* ── BADGES ──────────────────────────────────────────── */
.badge {{
    display: inline-block;
    padding: 0.3rem 0.85rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}}

.badge-good {{ background: rgba(25,135,84,0.12) !important; color: #198754 !important; border: 1px solid rgba(25,135,84,0.26) !important; }}
.badge-mid  {{ background: rgba(194,125,6,0.12) !important; color: #9A6A18 !important; border: 1px solid rgba(194,125,6,0.24) !important; }}
.badge-low  {{ background: rgba(180,35,79,0.10) !important; color: #b4234f !important; border: 1px solid rgba(180,35,79,0.20) !important; }}

/* ── SCORE CIRCLE ────────────────────────────────────── */
.score-circle {{
    width: 130px; height: 130px;
    border-radius: 50%;
    margin: 0 auto;
    display: flex; align-items: center; justify-content: center;
    position: relative;
    box-shadow: 0 4px 20px rgba(15,32,68,0.14);
}}

.score-circle::before {{
    content: '';
    position: absolute;
    width: 100px; height: 100px;
    border-radius: 50%;
    background: #FFFFFF;
}}

.score-circle-inner {{
    position: relative;
    z-index: 2;
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #773344;
}}
.score-circle-good .score-circle-inner {{ color: #198754; }}
.score-circle-mid .score-circle-inner {{ color: #c27d06; }}
.score-circle-low .score-circle-inner {{ color: #b4234f; }}

/* ── INFO GRID ───────────────────────────────────────── */
.info-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
    gap: 0.75rem;
}}

.info-item {{
    background: #EEF4F8;
    padding: 1rem;
    border-radius: 10px;
    border: 1px solid #e3b5a4;
}}

.info-label {{
    font-size: 0.8rem;
    font-weight: 700;
    color: #8b6771;
    margin-bottom: 0.3rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.info-value {{
    font-size: 1rem;
    font-weight: 600;
    color: #2a1421;
    word-break: break-word;
    white-space: normal;
    line-height: 1.4;
}}

/* ── DIVIDER ─────────────────────────────────────────── */
.divider {{
    height: 1px;
    background: #e3b5a4;
    margin: 2rem 0;
    opacity: 0.8;
}}

/* ── RESULT CARDS ────────────────────────────────────── */
.result-card {{
    background: #FFFFFF;
    border-radius: 18px !important;
    padding: 1rem 1.2rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 10px 28px rgba(22, 32, 51, 0.06) !important;
    text-align: center;
    height: 100%;
    position: relative;
    overflow: hidden;
}}

.result-card::before {{
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 5px;
    background: linear-gradient(90deg, #d44d5c 0%, #773344 100%) !important;
}}

.result-card-good::before  {{ background: #06A77D !important; }}
.result-card-mid::before   {{ background: #F1A208 !important; }}
.result-card-low::before   {{ background: #A31621 !important; }}

.result-card-title {{
    color: #8b6771;
    font-weight: 700;
    font-size: 0.8rem;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.result-card-score {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    margin: 0.4rem 0 0.5rem 0;
}}

.result-card-score-good {{ color: #06A77D; }}
.result-card-score-mid  {{ color: #C27D06; }}
.result-card-score-low  {{ color: #A31621; }}

.result-card-text {{
    color: #5d3945;
    font-size: 0.85rem;
    line-height: 1.55;
}}

/* ── POINTS CARD ─────────────────────────────────────── */
.points-card {{
    background: #FFFFFF;
    border-radius: 18px !important;
    padding: 1rem 1.2rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 10px 28px rgba(22, 32, 51, 0.06) !important;
    height: 100%;
}}

.points-card-header {{
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.5rem;
    padding-bottom: 0.55rem;
    border-bottom: 1px solid #e3b5a4;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

/* ── SMALL NOTE ──────────────────────────────────────── */
.small-note {{
    color: #8b6771;
    font-size: 0.85rem;
    line-height: 1.55;
}}

/* ── CHART CARD ──────────────────────────────────────── */
.chart-card {{
    background: #FFFFFF;
    border-radius: 18px !important;
    padding: 1.2rem 1.2rem 0.8rem 1.2rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 10px 28px rgba(22, 32, 51, 0.06) !important;
    margin-bottom: 0.75rem;
}}

/* ── BUTTONS ─────────────────────────────────────────── */
.stButton > button,
.stDownloadButton > button {{
    background: #cb4a5e !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.55rem 1.1rem !important;
    font-size: 0.9rem !important;
    box-shadow: 0 10px 22px rgba(119,51,68,0.18) !important;
    transition: all 0.18s ease !important;
    letter-spacing: 0.01em !important;
    min-height: 44px !important;
}}

.stButton > button:hover,
.stDownloadButton > button:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 16px rgba(15,32,68,0.24) !important;
    background: #b54256 !important;
    color: white !important;
}}

.stButton > button:active,
.stDownloadButton > button:active {{
    transform: translateY(0px) !important;
    box-shadow: 0 2px 6px rgba(15,32,68,0.14) !important;
}}

/* ── INPUT LABELS ────────────────────────────────────── */
[data-testid="stTextArea"] label,
[data-testid="stTextInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label,
[data-testid="stRadio"] label:first-of-type {{
    color: #160029 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    margin-bottom: 0.4rem !important;
}}

/* ── RADIO / SEGMENTED INPUTS ────────────────────────── */
[data-testid="stRadio"] > div {{color:#2a1421 !important;}}
[data-testid="stRadio"] label {{color:#2a1421 !important; font-weight:600 !important; opacity:1 !important;}}
[data-testid="stRadio"] [role="radiogroup"] {{
    background: linear-gradient(180deg,#fffdfc 0%,#fbf3ee 100%) !important;
    border: 1px solid #e3b5a4 !important;
    border-radius: 22px !important;
    padding: 0.4rem !important;
    gap: 0.5rem !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.55);
}}
[data-testid="stRadio"] [role="radiogroup"] > label {{
    flex: 1 1 0 !important;
    justify-content: center !important;
    text-align: center !important;
    min-height: 40px !important;
    border-radius: 16px !important;
    padding: 0.4rem 0.8rem !important;
    transition: all 0.18s ease !important;
    border: 1px solid transparent !important;
}}
[data-testid="stRadio"] [role="radiogroup"] > label:hover {{background:#faf4f8 !important;}}
[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) {{
    background: linear-gradient(180deg,#d44d5c 0%,#cb4a5e 100%) !important;
    border-color: #cb4a5e !important;
    box-shadow: 0 8px 18px rgba(119,51,68,0.18) !important;
}}
[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) p {{color:#ffffff !important;}}
[data-testid="stRadio"] [role="radiogroup"] input {{display:none !important;}}
[data-testid="stRadio"] [role="radiogroup"] p {{color:#5d3945 !important;font-weight:700 !important;font-size:0.85rem !important;opacity:1 !important;}}

/* ── INPUT SURFACES ──────────────────────────────────── */
[data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stTextInputRootElement"],
.stTextInput > div > div {{
    background: linear-gradient(180deg, #fffefe 0%, #fbf4ef 100%) !important;
    border: 1.5px solid #e3b5a4 !important;
    border-radius: 18px !important;
    min-height: 48px !important;
    box-shadow: 0 8px 18px rgba(44, 21, 33, 0.06) !important;
    transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
}}

[data-testid="stMultiSelect"] [data-baseweb="select"] > div:focus-within,
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
[data-testid="stTextInputRootElement"]:focus-within,
.stTextInput > div > div:focus-within {{
    border-color: #b24758 !important;
    box-shadow: 0 0 0 4px rgba(212,77,92,0.12), 0 12px 24px rgba(44,21,33,0.08) !important;
}}

[data-testid="stMultiSelect"] [data-baseweb="tag"] {{
    background: linear-gradient(135deg, #f7c7cf 0%, #ef9cac 100%) !important;
    color:#4a2030 !important;
    border-radius:999px !important;
    border:1px solid rgba(178,71,88,0.18) !important;
}}
[data-testid="stMultiSelect"] [data-baseweb="tag"] * {{color:#4a2030 !important;}}
[data-testid="stMultiSelect"] input,
[data-testid="stSelectbox"] input,
[data-testid="stMultiSelect"] div,
[data-testid="stSelectbox"] div {{color:#2a1421 !important;}}
[data-testid="stSelectbox"] svg,
[data-testid="stMultiSelect"] svg {{fill:#773344 !important;}}

/* ── TEXT AREA ───────────────────────────────────────── */
.stTextArea > div > div {{
    background: linear-gradient(180deg, #fffefe 0%, #fbf4ef 100%) !important;
    border: 1.5px solid #e3b5a4 !important;
    border-radius: 22px !important;
    box-shadow: 0 10px 24px rgba(44,21,33,0.06) !important;
    padding: 0.4rem !important;
    transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
}}

.stTextArea > div > div:focus-within {{
    border-color: #b24758 !important;
    box-shadow: 0 0 0 4px rgba(212,77,92,0.12), 0 14px 28px rgba(44,21,33,0.08) !important;
}}

.stTextArea textarea {{
    background: transparent !important;
    border: none !important;
    border-radius: 18px !important;
    padding: 0.8rem 0.9rem !important;
    color: #2a1421 !important;
    font-size: 0.9rem !important;
    font-family: 'Inter', sans-serif !important;
    line-height: 1.6 !important;
    box-shadow: none !important;
    min-height: 160px !important;
}}

.stTextArea textarea:focus {{
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}}

.stTextArea textarea::placeholder,
.stTextInput input::placeholder {{
    color: #9a7b87 !important;
    opacity: 1 !important;
    font-size: 0.9rem !important;
}}

/* ── TEXT INPUT ──────────────────────────────────────── */
.stTextInput input {{
    background: transparent !important;
    border: none !important;
    border-radius: 16px !important;
    padding: 0.5rem 0.7rem !important;
    color: #2a1421 !important;
    font-size: 0.9rem !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: none !important;
}}

/* ── SELECTBOX / MULTISELECT ─────────────────────────── */
[data-testid="stSelectbox"] > div > div,
.stSelectbox [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] > div > div {{
    background: transparent !important;
    border: none !important;
    border-radius: 16px !important;
    color: #2a1421 !important;
    font-size: 0.9rem !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: none !important;
}}

[data-testid="stSelectbox"] * ,
[data-testid="stMultiSelect"] * ,
.stSelectbox * {{
    color: #2a1421 !important;
    -webkit-text-fill-color: #2a1421 !important;
    opacity: 1 !important;
}}

/* ── LIGHT TABLE ─────────────────────────────────────── */
.light-table-wrap {{
    overflow-x: auto;
    border-radius: 18px;
    border: 1px solid #e3b5a4;
    box-shadow: 0 10px 24px rgba(39,34,51,0.08);
    background: #FFFFFF;
}}

.light-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    overflow: hidden;
    border-radius: 18px;
}}

/* Table headers — readable labels */
.light-table thead th {{
    background: #f7f0f5 !important;
    color: #773344 !important;
    font-weight: 700;
    font-size: 0.85rem;
    padding: 0.85rem 1rem;
    text-align: left;
    white-space: nowrap;
    letter-spacing: 0.03em;
    border-bottom: 1px solid rgba(0,0,0,0.05);
}}

.light-table thead th:first-child {{ border-radius: 18px 0 0 0; }}
.light-table thead th:last-child  {{ border-radius: 0 18px 0 0; }}

/* Table cell text — comfortable size */
.light-table tbody td {{
    background: #FFFFFF;
    color: #2a1421;
    font-size: 0.85rem;
    padding: 0.85rem 1rem;
    border-bottom: 1px solid #e3b5a4;
    vertical-align: middle;
    line-height: 1.6;
}}

.light-table tbody tr:nth-child(even) td {{ background: #FCF8F5; }}
.light-table tbody tr:hover td {{ background: #F8EFE8; transition: background 0.14s ease; }}
.light-table tbody tr:last-child td {{ border-bottom: none; }}

/* ── OVERVIEW CHART CARD ─────────────────────────────── */
.overview-chart-card {{
    background: #FFFFFF;
    border-radius: 18px !important;
    padding: 0.75rem 1rem 1rem 1.3rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 10px 28px rgba(22, 32, 51, 0.06) !important;
    margin-bottom: 0.75rem;
}}

/* ── TOPIC CARDS ─────────────────────────────────────── */
.topic-card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.75rem;
}}

.topic-card {{
    background: #FFFFFF;
    border: 1px solid #e3b5a4;
    border-top: 5px solid #b24758;
    border-radius: 18px;
    padding: 1.1rem;
    box-shadow: 0 8px 18px rgba(39,34,51,0.08);
}}

.topic-card-title {{
    font-size: 1rem;
    font-weight: 800;
    color: #2a1421;
    line-height: 1.45;
    margin-bottom: 0.4rem;
}}

.topic-card-pill {{
    display: inline-flex;
    align-items: center;
    padding: 0.4rem 0.8rem;
    border-radius: 999px;
    background: #f5e9e2;
    color: #160029;
    border: 1px solid #e3b5a4;
    font-size: 0.8rem;
    font-weight: 800;
}}

.topic-card-count {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1rem;
    color: #773344;
}}

/* ── PAGER BAR ───────────────────────────────────────── */
.pager-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    background: #FFFFFF;
    border: 1px solid #e3b5a4;
    border-left: 5px solid #b24758;
    border-radius: 14px;
    padding: 0.6rem 0.9rem;
    margin-bottom: 0.5rem;
}}

.pager-note {{
    color: #8b6771;
    font-size: 0.9rem;
    line-height: 1.5;
}}

.pager-chip {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 90px;
    padding: 0.45rem 0.9rem;
    border-radius: 999px;
    background: #f5e9e2;
    color: #160029;
    border: 1px solid #e3b5a4;
    font-size: 0.85rem;
    font-weight: 700;
}}

/* ── COMPARISON CARD ─────────────────────────────────── */
.comparison-card {{
    background: #FFFFFF;
    border-radius: 16px;
    padding: 1.2rem;
    border: 1px solid #e3b5a4;
    box-shadow: 0 2px 10px rgba(15,32,68,0.06);
    margin-bottom: 0.75rem;
    height: 100%;
}}

.comparison-card-header {{
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.55rem;
    padding-bottom: 0.55rem;
    border-bottom: 2px solid #f5e9e2;
    line-height: 1.3;
    word-break: break-word;
}}

/* ── ALIGNMENT RANKING ───────────────────────────────── */
.align-panel-title {{
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: #8b6771;
    margin-bottom: 0.55rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}

.align-rank-card {{
    background: #FFFFFF;
    border-radius: 14px;
    border: 1px solid #e3b5a4;
    box-shadow: 0 2px 8px rgba(15,32,68,0.05);
    padding: 0.85rem 1rem;
    margin-bottom: 0.6rem;
    transition: transform 0.16s ease, box-shadow 0.16s ease;
}}

.align-rank-card:hover {{
    transform: translateY(-1px);
    box-shadow: 0 5px 16px rgba(15,32,68,0.08);
}}

/* Rank card topic label */
.align-rank-topic {{
    font-family: 'Inter', sans-serif;
    font-size: 0.92rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.4rem;
    line-height: 1.4;
    word-break: break-word;
}}

.align-rank-row {{
    display: flex;
    align-items: center;
    gap: 0.55rem;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
}}

.align-score {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    line-height: 1;
}}

.align-band {{
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}}

.align-n {{
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
    color: #8b6771;
    margin-left: auto;
}}

.align-bar-bg {{
    background: #f5e9e2;
    border-radius: 99px;
    height: 7px;
    width: 100%;
    overflow: hidden;
}}

.align-bar-fill {{
    height: 100%;
    border-radius: 99px;
    transition: width 0.4s ease;
}}

.align-full-row {{
    display: flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid #e3b5a4;
    flex-wrap: nowrap;
}}

.align-full-rank {{
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    min-width: 2rem;
    color: #8b6771;
}}

.align-full-topic {{
    font-family: 'Inter', sans-serif;
    font-size: 0.92rem;
    color: #2a1421;
    min-width: 150px;
    word-break: break-word;
    white-space: normal;
    line-height: 1.4;
}}

.align-full-score {{
    font-family: 'Inter', sans-serif;
    font-size: 0.92rem;
    font-weight: 700;
    min-width: 3.5rem;
    text-align: right;
}}

.align-full-n {{
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
    color: #8b6771;
    min-width: 2.5rem;
}}

/* ── DONUT INSIGHT CARDS ─────────────────────────────── */
.donut-insight-card {{
    display: flex;
    align-items: stretch;
    gap: 0;
    background: #FFFFFF;
    border-radius: 10px;
    border: 1px solid #e3b5a4;
    box-shadow: 0 2px 8px rgba(15,32,68,0.05);
    margin-bottom: 0.55rem;
    overflow: hidden;
}}

.donut-insight-accent {{
    width: 5px;
    min-height: 100%;
    flex-shrink: 0;
    border-radius: 0;
}}

.donut-insight-body {{
    padding: 0.8rem 1rem;
    flex: 1;
}}

.donut-insight-name {{
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.25rem;
    word-break: break-word;
}}

.donut-insight-stats {{
    display: flex;
    align-items: baseline;
    gap: 0;
    flex-wrap: wrap;
}}

.donut-insight-count {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #773344;
    line-height: 1;
}}

.donut-insight-pct {{
    font-family: 'Inter', sans-serif;
    font-size: 0.88rem;
    font-weight: 400;
    color: #8b6771;
}}

/* ── BATCH RESULT HELPERS ───────────────────────────── */
.batch-results-shell {{
    background: linear-gradient(180deg, #ffffff 0%, #f9f1ec 100%);
    border: 1px solid #e3b5a4;
    border-radius: 24px;
    padding: 1.2rem 1.3rem;
    box-shadow: 0 12px 26px rgba(44, 21, 33, 0.06);
    margin: 1.1rem 0 1rem 0;
}}

.batch-results-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #251329;
    margin-bottom: 0.3rem;
}}

.batch-results-copy,
.batch-readable-note,
.result-reading-guide-copy {{
    color: #6b5660;
    font-size: 0.88rem;
    line-height: 1.6;
}}

.batch-readable-note,
.result-reading-guide {{
    background: linear-gradient(180deg, #fffefe 0%, #f8efea 100%);
    border: 1px solid #e3b5a4;
    border-left: 4px solid #d44d5c;
    border-radius: 20px;
    padding: 0.85rem 1rem;
    margin: 1rem 0;
    box-shadow: 0 8px 20px rgba(44, 21, 33, 0.05);
}}

.result-reading-guide-title {{
    font-size: 0.85rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #a3195b;
    margin-bottom: 0.25rem;
}}

.light-table-wrap {{
    width: 100%;
    overflow-x: auto;
    overflow-y: visible;
}}

/* ── FOOTER ──────────────────────────────────────────── */
.footer-wrap {{
    text-align: center;
    margin-top: 2.5rem;
    padding: 1.5rem 2rem;
    border-top: 1px solid #e3b5a4;
}}

.footer-wrap p {{
    color: #8b6771;
    font-size: 0.9rem;
    font-family: 'Inter', sans-serif;
    line-height: 1.55;
    margin: 0;
}}

/* ── TAB MINIMAL HERO ───────────────────────────────── */
/* The big section intro banner at top of each tab */
.tab-minimal-hero {{
    background: linear-gradient(180deg,#fffdfc 0%,#fbf4ef 100%);
    border: 1px solid #e3b5a4;
    border-radius: 28px;
    padding: 1.3rem 1.4rem 1.2rem 1.4rem;
    box-shadow: 0 14px 30px rgba(41,22,35,0.05);
    margin: 0.2rem 0 1.1rem 0;
}}

/* Section kicker label — small category label above the big title */
.tab-minimal-kicker {{
    color:#b01f55;
    font-size:0.78rem;
    font-weight:800;
    letter-spacing:0.16em;
    text-transform:uppercase;
    margin-bottom:0.5rem;
}}

/* Big tab title — this should be the most prominent text on the page */
.tab-minimal-title {{
    font-family:'Inter Tight','Inter',sans-serif;
    font-size:1.8rem;
    font-weight:800;
    color:#221221;
    line-height:1.1;
}}

/* Tab subtitle — description below the big title */
.tab-minimal-copy {{
    color:#766772;
    font-size:0.95rem;
    line-height:1.7;
    margin-top:0.55rem;
    max-width: 860px;
}}

/* ── WORKSPACE SHELL ────────────────────────────────── */
.workspace-shell {{
    background: linear-gradient(180deg,#ffffff 0%,#fbf5f1 100%);
    border: 1px solid #e3b5a4;
    border-radius: 24px;
    padding: 1.2rem 1.3rem;
    box-shadow: 0 10px 24px rgba(25,14,36,0.06);
    margin-bottom: 0.85rem;
}}

.workspace-kicker {{
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #773344;
    margin-bottom: 0.3rem;
}}

/* Card / panel title — clearly bigger than body text, smaller than section title */
.workspace-title {{
    font-family:'Inter Tight','Inter',sans-serif;
    font-size: 1.2rem;
    color:#160029;
    line-height:1.15;
    margin: 0;
    font-weight: 700;
}}

.workspace-copy {{
    color:#5d3945;
    font-size:0.9rem;
    line-height:1.65;
    margin-top:0.3rem;
}}

/* ── SLIM LOADER ─────────────────────────────────────── */
.slim-loader-kicker {{
    font-size:0.76rem;
    font-weight:800;
    letter-spacing:0.12em;
    text-transform:uppercase;
    color:#a3195b;
    margin-bottom:0.3rem;
}}

.slim-loader-title {{
    font-size:1.05rem;
    font-weight:800;
    color:#251329;
    line-height:1.2;
    margin-bottom:0.25rem;
}}

.slim-loader-copy {{
    font-size:0.9rem;
    color:#766772;
    line-height:1.68;
}}

.slim-loader-side {{
    font-size:0.85rem;
    font-weight:800;
    color:#907785;
    white-space:nowrap;
    padding-bottom:0.15rem;
}}

.dataset-control-caption {{
    font-size:0.76rem;
    font-weight:800;
    letter-spacing:0.08em;
    text-transform:uppercase;
    color:#8b6771;
    margin:0 0 0.4rem 0.1rem;
}}

/* ── INPUT EDITOR ────────────────────────────────────── */
.input-editor-shell {{
    background:linear-gradient(180deg,#fffaf8 0%,#f8efea 100%);
    border:1px solid #e3b5a4;
    border-radius:22px;
    padding:1rem 1.1rem 0.9rem 1.1rem;
    margin:0.3rem 0 0.7rem 0;
    box-shadow:0 10px 24px rgba(25,14,36,0.05);
}}

.input-editor-kicker {{
    font-size:0.76rem;
    font-weight:800;
    text-transform:uppercase;
    letter-spacing:0.08em;
    color:#a3195b;
    margin-bottom:0.25rem;
}}

.input-editor-title {{
    font-size:1.05rem;
    font-weight:800;
    color:#241226;
    line-height:1.3;
}}

.input-editor-chip {{
    padding:0.4rem 0.85rem;
    border-radius:999px;
    background:#fff;
    border:1px solid #e3b5a4;
    color:#773344;
    font-size:0.82rem;
    font-weight:800;
    white-space:nowrap;
}}

/* ── BATCH SHELL ─────────────────────────────────────── */
.batch-shell {{
    background:linear-gradient(180deg,#ffffff 0%,#f9f1ec 100%);
    border:1px solid #e3b5a4;
    border-radius:26px;
    padding:1.2rem 1.25rem 1rem 1.25rem;
    box-shadow:0 12px 28px rgba(25,14,36,0.06);
    margin:0.2rem 0 1rem 0;
}}

.batch-kicker {{
    font-size:0.76rem;
    font-weight:800;
    letter-spacing:0.08em;
    text-transform:uppercase;
    color:#a3195b;
    margin-bottom:0.25rem;
}}

.batch-title {{
    font-family:'Inter Tight','Inter',sans-serif;
    font-size:1.25rem;
    font-weight:700;
    color:#211120;
    line-height:1.15;
    margin-bottom:0.35rem;
}}

.batch-copy {{
    color:#6d5a68;
    font-size:0.9rem;
    line-height:1.7;
    max-width:860px;
}}

.batch-selection-note {{
    background:#fff7f4;
    border:1px solid #e3b5a4;
    border-radius:16px;
    padding:0.9rem 1rem;
    color:#5f4751;
    font-size:0.9rem;
    line-height:1.6;
    margin:0.85rem 0 1rem 0;
}}

.batch-selection-note strong {{
    color:#160029;
    font-size:1rem;
}}

/* ── CHART PANEL ─────────────────────────────────────── */
.chart-panel {{
    background:linear-gradient(180deg,#fffefe 0%,#f8efea 100%);
    border:1px solid #e3b5a4;
    border-radius:22px;
    padding:1.1rem 1.15rem 1rem 1.15rem;
    box-shadow:0 10px 24px rgba(25,14,36,0.05);
    margin:1.1rem 0 0.6rem 0;
}}

.chart-panel-title {{
    font-family:'Inter Tight','Inter',sans-serif;
    font-size:1rem;
    font-weight:700;
    color:#221221;
    margin-bottom:0.25rem;
}}

.chart-panel-copy {{
    color:#6d5a68;
    font-size:0.9rem;
    line-height:1.68;
}}

.chart-conclusion {{
    margin-top:0.8rem;
    padding:0.9rem 1rem;
    border-radius:16px;
    background:linear-gradient(180deg,#fffaf7 0%,#fff3ed 100%);
    border:1px solid #ead1c8;
    color:#6d5a68;
    font-size:0.9rem;
    line-height:1.7;
}}

/* ── EXPLORER CARDS ──────────────────────────────────── */
.explorer-instruction-card {{
    background:linear-gradient(180deg,#fffaf7 0%,#fff2ec 100%);
    border:1px solid #ead1c8;
    border-left:6px solid #b24758;
    border-radius:22px;
    padding:1rem 1.1rem;
    margin:0.7rem 0 1.1rem 0;
    box-shadow:0 10px 24px rgba(25,14,36,0.05);
}}

.explorer-instruction-title {{
    font-size:0.82rem;
    font-weight:800;
    letter-spacing:0.12em;
    text-transform:uppercase;
    color:#a3195b;
    margin-bottom:0.45rem;
}}

.explorer-instruction-copy {{
    font-size:0.95rem;
    line-height:1.78;
    color:#634e59;
}}

.explorer-orb-grid {{
    display:grid;
    grid-template-columns:repeat(3,minmax(0,1fr));
    gap:1rem;
    margin:1rem 0 1.2rem 0;
}}

.explorer-orb {{
    background:linear-gradient(180deg,#fff 0%,#fbf3ef 100%);
    border:1px solid #ead1c8;
    border-radius:999px;
    padding:1rem 1.1rem;
    display:flex;
    align-items:center;
    gap:0.9rem;
    box-shadow:0 10px 20px rgba(25,14,36,0.05);
    min-height:90px;
}}

.explorer-orb-icon {{
    width:52px; height:52px;
    border-radius:999px;
    display:flex; align-items:center; justify-content:center;
    background:linear-gradient(135deg,#d44d5c 0%,#a63a52 100%);
    color:#fff; font-weight:800; font-size:1rem;
    box-shadow:0 8px 18px rgba(164,59,83,0.22);
}}

.explorer-orb-label {{
    font-size:0.76rem;
    font-weight:800;
    letter-spacing:0.08em;
    text-transform:uppercase;
    color:#8b6771;
    margin-bottom:0.22rem;
}}

.explorer-orb-value {{
    font-family:'Inter Tight','Inter',sans-serif;
    font-size:1.5rem;
    font-weight:700;
    color:#241226;
    line-height:1.05;
}}

.explorer-orb-note {{
    font-size:0.85rem;
    line-height:1.55;
    color:#7a6874;
    margin-top:0.15rem;
}}

/* ── TOPIC FOCUS GRID ────────────────────────────────── */
.topic-focus-grid {{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:0.9rem;
    margin:0.5rem 0 1rem 0;
}}

.topic-focus-card {{
    background:linear-gradient(180deg,#fff 0%,#faf4f0 100%);
    border:1px solid #e3b5a4;
    border-radius:18px;
    padding:0.9rem 1rem;
}}

.topic-focus-label {{
    font-size:0.76rem;
    font-weight:800;
    letter-spacing:0.08em;
    text-transform:uppercase;
    color:#8b6771;
    margin-bottom:0.3rem;
}}

.topic-focus-value {{
    font-size:1rem;
    font-weight:800;
    color:#221221;
    line-height:1.35;
}}

/* ── SIM LITE SHELL ──────────────────────────────────── */
.sim-lite-shell {{
    background:linear-gradient(180deg,#ffffff 0%,#fbf3ef 100%);
    border:1px solid #e3b5a4;
    border-radius:24px;
    padding:1.1rem 1.15rem 1rem 1.15rem;
    box-shadow:0 12px 26px rgba(25,14,36,0.06);
}}

.sim-lite-head {{display:flex;justify-content:space-between;align-items:flex-start;gap:0.85rem;margin-bottom:1rem;}}
.sim-lite-kicker {{color:#8b6771;font-size:0.78rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.25rem;}}
.sim-lite-title {{font-family:'Inter Tight','Inter',sans-serif;font-size:1.45rem;font-weight:800;color:#221221;}}
.sim-lite-pill {{padding:0.44rem 0.9rem;border-radius:999px;border:1px solid #d44d5c;font-weight:800;font-size:1rem;}}

.sim-lite-hero {{display:grid;grid-template-columns:120px 1fr;gap:1rem;align-items:center;margin-bottom:1rem;}}
.sim-lite-ring {{width:100px;height:100px;border-radius:999px;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 18px rgba(25,14,36,0.08);}}
.sim-lite-ring-inner {{width:72px;height:72px;border-radius:999px;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:inset 0 0 0 1px rgba(227,181,164,0.45);}}
.sim-lite-ring-inner strong {{font-family:'Inter Tight','Inter',sans-serif;font-size:1.5rem;line-height:1;}}
.sim-lite-ring-inner span {{font-size:0.76rem;color:#8b6771;margin-top:0.2rem;}}

.sim-lite-summary-title {{font-size:1rem;font-weight:800;color:#221221;margin-bottom:0.3rem;}}
.sim-lite-summary-copy {{font-size:0.9rem;line-height:1.7;color:#6d5a68;}}

.sim-lite-top-note {{
    display:block;background:#fff8f4;border:1px solid #ead1c8;
    border-radius:16px;padding:0.85rem 0.95rem;margin:1rem 0 1rem 0;
}}
.sim-lite-top-note-title {{display:block;font-size:0.76rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin-bottom:0.25rem;}}
.sim-lite-top-note-copy {{display:block;font-size:0.9rem;line-height:1.65;color:#6d5a68;}}

.sim-lite-metric {{
    background:#fff;border:1px solid #ead1c8;border-radius:16px;
    padding:0.9rem 1rem;box-shadow:0 6px 16px rgba(25,14,36,0.04);
    min-height:110px;margin-bottom:0.7rem;text-align:center;
    display:flex;flex-direction:column;justify-content:center;
}}
.sim-lite-metric-label {{font-size:0.78rem;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;color:#8b6771;margin-bottom:0.35rem;}}
.sim-lite-metric-value {{font-family:'Inter Tight','Inter',sans-serif;font-size:1.8rem;font-weight:700;line-height:1;margin-bottom:0.35rem;text-align:center;}}
.sim-lite-metric-note {{font-size:0.88rem;line-height:1.6;color:#6d5a68;}}

/* ── HISTORY OVERVIEW ────────────────────────────────── */
.history-table-title {{
    font-size:1rem;
    font-weight:800;
    color:#241226;
    margin-bottom:0.25rem;
}}

.history-table-copy {{
    font-size:0.9rem;
    line-height:1.68;
    color:#6d5a68;
    max-width:860px;
}}

/* ── LEADERBOARD ─────────────────────────────────────── */
.leaderboard-shell {{display:grid;gap:0.9rem;margin-top:0.9rem;}}

.leaderboard-card {{
    display:grid;
    grid-template-columns:58px 1fr auto;
    gap:1rem;
    align-items:center;
    background:linear-gradient(180deg,#fff 0%,#fbf3ef 100%);
    border:1px solid #e7c2b3;
    border-radius:20px;
    padding:1rem 1.1rem;
    box-shadow:0 8px 18px rgba(25,14,36,0.05);
}}

.leaderboard-rank {{
    width:44px;height:44px;border-radius:14px;
    background:#fff7f1;border:1px solid #e7c2b3;
    display:flex;align-items:center;justify-content:center;
    font-size:1.1rem;
}}

.leaderboard-title {{font-size:1rem;font-weight:800;color:#221221;margin-bottom:0.2rem;}}
.leaderboard-meta {{font-size:0.85rem;color:#7a6874;line-height:1.55;margin-bottom:0.5rem;}}
.leaderboard-track {{height:8px;background:#f3dfd7;border-radius:999px;overflow:hidden;}}
.leaderboard-fill {{height:100%;background:linear-gradient(90deg,#d44d5c 0%,#b24758 100%);border-radius:999px;}}
.leaderboard-side {{text-align:right;min-width:90px;}}
.leaderboard-score {{font-size:1.15rem;font-weight:800;color:#221221;}}
.leaderboard-note {{font-size:0.8rem;color:#8b6771;line-height:1.4;}}

/* ── MINI EXPLAINER CARD ─────────────────────────────── */
.mini-explainer-card {{
    background:linear-gradient(180deg,#fffaf7 0%,#fff4ef 100%);
    border:1px solid #ead1c8;border-radius:18px;
    padding:1rem 1.05rem;color:#6d5a68;
    font-size:0.92rem;line-height:1.72;
    margin:0.6rem 0 1.1rem 0;
    box-shadow:0 10px 20px rgba(25,14,36,0.04);
}}
.mini-explainer-card strong {{color:#221221;}}

/* ── EMPTY REVIEW CARD ───────────────────────────────── */
.empty-review-card {{
    background:linear-gradient(180deg,#ffffff 0%,#f9f1ec 100%);
    border:1px solid #e3b5a4;
    border-radius:24px;
    padding:1.2rem 1.3rem 1.1rem 1.3rem;
    box-shadow:0 10px 24px rgba(25,14,36,0.06);
    min-height:360px;
    display:flex;flex-direction:column;justify-content:space-between;
}}

.empty-review-top {{display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;margin-bottom:0.85rem;}}
.empty-review-title {{font-family:'Inter Tight','Inter',sans-serif;font-size:1.3rem;color:#160029;margin:0.1rem 0 0.25rem 0;font-weight:700;}}
.empty-review-copy {{color:#5d3945;font-size:0.92rem;line-height:1.68;}}
.empty-review-pill {{padding:0.44rem 0.85rem;border-radius:999px;background:#fff;border:1px solid #e3b5a4;color:#773344;font-weight:800;font-size:0.84rem;white-space:nowrap;}}
.empty-review-list {{display:grid;gap:0.7rem;margin-top:0.6rem;}}
.empty-review-item {{display:flex;gap:0.85rem;align-items:flex-start;padding:0.9rem 1rem;border-radius:16px;background:#fff;border:1px solid #e3b5a4;}}
.empty-review-icon {{width:34px;height:34px;min-width:34px;border-radius:12px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#d44d5c 0%,#b24758 100%);color:#fff;font-size:0.95rem;font-weight:800;}}
.empty-review-item strong {{display:block;color:#160029;font-size:0.92rem;margin-bottom:0.18rem;}}
.empty-review-item span {{display:block;color:#5d3945;font-size:0.88rem;line-height:1.6;}}
.empty-review-footer {{display:grid;grid-template-columns:repeat(3,1fr);gap:0.7rem;margin-top:1rem;}}
.empty-review-stat {{background:#fff;border:1px solid #e3b5a4;border-radius:16px;padding:0.85rem;text-align:center;}}
.empty-review-stat-label {{font-size:0.74rem;font-weight:800;color:#8b6771;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.25rem;}}
.empty-review-stat-value {{font-family:'Inter Tight','Inter',sans-serif;font-size:1.25rem;color:#160029;font-weight:700;}}

/* ── ANALYSIS PANEL ──────────────────────────────────── */
.analysis-panel {{
    background:rgba(255,255,255,0.72);
    border:1px solid rgba(170,133,155,0.28);
    border-radius:26px;
    padding:1.2rem 1.3rem;
    box-shadow:0 14px 34px rgba(52,27,45,0.05);
    height:100%;
}}

.analysis-panel-title {{
    font-family:'Inter Tight','Inter',sans-serif;
    font-size:1.15rem;
    font-weight:700;
    color:#2d1830;
    margin:0 0 0.4rem 0;
}}

.analysis-panel-copy {{color:#6e6070;font-size:0.92rem;line-height:1.78;margin:0 0 1rem 0;}}

.analysis-steps {{display:grid;gap:0.9rem;margin-top:0.15rem;}}
.analysis-step {{display:grid;grid-template-columns:42px 1fr;gap:0.85rem;align-items:start;padding:0.1rem 0;}}
.analysis-step-no {{width:32px;height:32px;border-radius:999px;background:#f0e7ec;color:#a3195b;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:0.9rem;}}
.analysis-step-title {{font-weight:700;color:#35233b;font-size:0.95rem;margin-bottom:0.15rem;}}
.analysis-step-copy {{color:#746675;font-size:0.9rem;line-height:1.72;}}
.analysis-step + .analysis-step {{border-top:1px solid rgba(170,133,155,0.2);padding-top:0.9rem;}}

/* ── EDITORIAL ───────────────────────────────────────── */
.editorial-section {{padding:0.1rem 0 0.65rem 0;margin-bottom:0.9rem;}}
.editorial-kicker {{font-size:0.82rem;font-weight:800;letter-spacing:0.16em;text-transform:uppercase;color:#a3195b;margin-bottom:0.7rem;}}
.editorial-title {{font-family:'Inter Tight','Inter',sans-serif;font-size:2rem;line-height:1.08;font-weight:700;color:#221221;letter-spacing:-0.03em;margin:0 0 0.85rem 0;max-width:900px;}}
.editorial-copy {{max-width:980px;font-size:1rem;line-height:1.82;color:#6d5a68;margin:0;}}

/* ── BROWSE / FILTER ─────────────────────────────────── */
.browse-inline-head {{font-size:0.82rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin:0 0 0.4rem 0.08rem;}}
.browse-filter-chip-row {{display:flex;flex-wrap:wrap;gap:0.55rem;margin:0.6rem 0 0.95rem 0;padding-top:0.2rem;border-top:1px solid rgba(227,181,164,0.45);}}
.browse-filter-chip {{display:inline-flex;align-items:center;padding:0.42rem 0.85rem;border-radius:999px;background:#fff8f4;border:1px solid #e3b5a4;color:#773344;font-size:0.85rem;font-weight:700;}}

/* ── COMPARISON SELECT ───────────────────────────────── */
.comparison-select-title {{font-size:0.88rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;color:#8f6f7b;}}
.comparison-select-copy {{font-size:0.92rem;line-height:1.68;color:#6d5a68;margin-top:0.25rem;}}

/* ── TOPIC PICK SHELL ────────────────────────────────── */
.topic-pick-shell {{
    background:linear-gradient(180deg,#fffdfb 0%,#fbf3ef 100%);
    border:1px solid #e7c3b4;
    border-radius:24px;
    padding:1rem 1.15rem;
    box-shadow:0 10px 24px rgba(25,14,36,0.05);
    margin:0.5rem 0 1rem 0;
}}
.topic-pick-kicker {{font-size:0.78rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;color:#a3195b;margin-bottom:0.35rem;}}
.topic-pick-title {{font-family:'Inter Tight','Inter',sans-serif;font-size:1.2rem;font-weight:700;color:#241226;line-height:1.2;margin-bottom:0.35rem;}}
.topic-pick-copy {{font-size:0.95rem;line-height:1.75;color:#6d5a68;max-width:900px;}}

/* ── INLINE SECTION HEAD ─────────────────────────────── */
.inline-section-head {{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;margin:0.1rem 0 0.65rem 0;}}
.inline-section-label {{font-size:0.82rem;font-weight:800;letter-spacing:0.14em;text-transform:uppercase;color:#a3195b;margin-bottom:0.4rem;}}
.inline-section-title {{font-family:'Inter Tight','Inter',sans-serif;font-size:1.05rem;font-weight:700;color:#251329;line-height:1.2;}}
.inline-section-copy {{color:#766772;font-size:0.95rem;line-height:1.72;max-width:760px;}}

/* ── HISTORY OVERVIEW GRID ───────────────────────────── */
.history-overview-grid {{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem;align-items:start;}}
.history-overview-card {{background:linear-gradient(180deg,#fffdfb 0%,#fbf3ef 100%);border:1px solid #ead1c8;border-radius:28px;padding:1rem 1.1rem 1rem 1.1rem;box-shadow:0 12px 26px rgba(25,14,36,0.05);overflow:hidden;}}

/* ── MISC UTILS ──────────────────────────────────────── */
.metric-card-info {{margin-top:0.15rem;font-size:0.88rem;line-height:1.65;color:#6d5a68;text-align:center;}}
.metric-card-info strong {{display:block;color:#221221;margin-bottom:0.15rem;}}

.result-hero-card {{
    background:linear-gradient(180deg,#ffffff 0%,#fcf7f3 100%);
    border:1px solid #e3b5a4;border-radius:24px;
    padding:1.1rem 1.15rem;box-shadow:0 12px 28px rgba(25,14,36,0.06);
    display:flex;justify-content:space-between;gap:1rem;
    align-items:flex-start;flex-wrap:wrap;margin:1rem 0 0.9rem 0;
}}
.result-hero-kicker {{color:#8b6771;font-size:0.78rem;font-weight:800;text-transform:uppercase;letter-spacing:0.09em;margin-bottom:0.25rem;}}
.result-hero-title {{font-family:'Inter Tight','Inter',sans-serif;color:#160029;font-size:1.55rem;line-height:1.08;margin-bottom:0.35rem;font-weight:700;}}
.result-hero-copy {{color:#5d3945;font-size:0.95rem;line-height:1.68;max-width:760px;}}

/* ── TECH REVIEW TITLE ───────────────────────────────── */
.tech-review-title {{
    font-size:0.95rem;
    font-weight:700;
    color:#241226;
    margin:1rem 0 0.5rem 0;
}}

/* ── EDITORIAL META ──────────────────────────────────── */
.editorial-meta {{
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.8rem !important;
    margin-top: 1rem !important;
    padding-top: 0 !important;
    border-top: none !important;
}}

.editorial-meta span {{
    display: block;
    background: linear-gradient(180deg, #fffefe 0%, #f8efea 100%);
    border: 1px solid #e3b5a4;
    border-radius: 18px;
    padding: 0.7rem 0.85rem 0.9rem 1rem !important;
    color: #5d3945 !important;
    box-shadow: 0 10px 22px rgba(44, 21, 33, 0.05);
    line-height: 1.5;
    font-size: 0.9rem;
}}

.editorial-meta span:before {{
    content: '';
    display: inline-block;
    width: 10px; height: 10px;
    border-radius: 999px;
    background: linear-gradient(135deg, #d44d5c 0%, #b24758 100%);
    margin-right: 0.6rem;
    vertical-align: middle;
    position: static !important;
}}

/* ── DATASET PANEL ───────────────────────────────────── */
.dataset-side-panel {{
    background: linear-gradient(180deg, #fff 0%, #faf3ef 100%);
    border: 1px solid #e3b5a4;
    border-radius: 22px;
    padding: 1.1rem 1.15rem;
    box-shadow: 0 10px 22px rgba(25,14,36,0.05);
}}
.dataset-side-title {{font-family:'Inter Tight','Inter',sans-serif;font-size:1rem;font-weight:700;color:#251329;margin-bottom:0.2rem;}}
.dataset-side-subtitle {{font-size:0.88rem;line-height:1.6;color:#766772;margin-bottom:0.7rem;}}
.dataset-model-chip {{padding:0.4rem 0.85rem;border-radius:999px;background:#fff;border:1px solid #e3b5a4;color:#773344;font-size:0.85rem;font-weight:800;white-space:nowrap;}}
.dataset-stat-grid {{display:grid;grid-template-columns:repeat(2,1fr);gap:0.65rem;margin:0.7rem 0;}}
.dataset-stat-card {{background:#fff;border:1px solid #ead1c8;border-radius:14px;padding:0.75rem 0.85rem;}}
.dataset-stat-label {{font-size:0.74rem;font-weight:800;text-transform:uppercase;letter-spacing:0.06em;color:#8b6771;margin-bottom:0.18rem;}}
.dataset-stat-value {{font-family:'Inter Tight','Inter',sans-serif;font-size:1.3rem;font-weight:700;color:#241226;}}
.dataset-preview-box {{background:#fff8f4;border:1px solid #ead1c8;border-radius:14px;padding:0.8rem 0.9rem;margin-top:0.65rem;}}
.dataset-preview-label {{font-size:0.74rem;font-weight:800;text-transform:uppercase;letter-spacing:0.06em;color:#8b6771;margin-bottom:0.25rem;}}
.dataset-preview-text {{font-size:0.88rem;line-height:1.65;color:#5d3945;}}

/* ── SCORE METRIC TEXT ───────────────────────────────── */
.metric-value-text {{
    font-family:'Inter Tight','Inter',sans-serif !important;
    font-size:2rem !important;
    font-weight:700 !important;
    line-height:1.1 !important;
    color:#7d3347 !important;
    letter-spacing:-0.03em;
    word-break:break-word;
}}

/* ── SYSTEM PLAIN NOTE ───────────────────────────────── */
.system-plain-note {{
    padding:0.2rem 0 0.7rem 0;
    margin-bottom:0.5rem;
    color:#6d5a68;
    font-size:0.95rem;
    line-height:1.82;
}}
.system-plain-note strong {{color:#251329;}}

/* ── OVERVIEW CHART ──────────────────────────────────── */
.overview-kicker {{font-size:0.76rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;color:#9a7380;margin-bottom:0.25rem;}}
.overview-title {{font-family:'Inter Tight','Inter',sans-serif;font-size:1rem;font-weight:700;color:#231222;line-height:1.2;margin-bottom:0.2rem;}}
.overview-copy {{font-size:0.92rem;line-height:1.68;color:#6d5a68;margin-bottom:0.6rem;}}

/* ── RESPONSIVE ──────────────────────────────────────── */
@media (max-width: 1200px) {{
    [data-testid="stSidebar"] {{
        min-width: 300px !important;
        max-width: 300px !important;
        width: 300px !important;
    }}
}}

@media (max-width: 1100px) {{
    .hero-image-wrap {{ height: 180px !important; }}
    .hero-image-content {{ max-width: 65% !important; }}
    .hero-image-title {{ font-size: 1.75rem !important; }}
    .explorer-orb-grid {{ grid-template-columns: 1fr; }}
    .topic-focus-grid {{ grid-template-columns: 1fr 1fr; }}
}}

@media (max-width: 900px) {{
    .hero-image-content {{ max-width: 100% !important; }}
    .hero-image-title {{ font-size: 1.4rem !important; }}
    .hero-image-subtitle {{ font-size: 0.85rem !important; max-width: 100% !important; }}
    .history-overview-grid {{ grid-template-columns: 1fr; }}
    .topic-focus-grid {{ grid-template-columns: 1fr 1fr; }}
    .editorial-meta {{ grid-template-columns: 1fr; }}
    .leaderboard-card {{ grid-template-columns: 44px 1fr; }}
    .leaderboard-side {{ grid-column: 2; text-align: left; }}
    .sim-lite-hero {{ grid-template-columns: 1fr; }}
    .sim-lite-ring {{ margin: 0 auto; }}
}}

@media (max-width: 768px) {{
    .block-container {{ padding-left: 1rem !important; padding-right: 1rem !important; }}
    .hero-image-wrap {{ height: 200px !important; border-radius: 20px !important; }}
    .hero-image-overlay {{ padding: 1.5rem 1.5rem; }}
    .hero-image-title {{ font-size: 1.3rem !important; }}
    .hero-image-subtitle {{ font-size: 0.85rem; line-height: 1.5; }}
    .topic-focus-grid {{ grid-template-columns: 1fr; }}
    .explorer-summary-grid {{ grid-template-columns: 1fr 1fr; }}
    .light-table {{ min-width: 540px; }}
}}

@media (max-width: 620px) {{
    .hero-image-wrap {{ height: 160px !important; }}
    .hero-image-title {{ font-size: 1.2rem !important; }}
    .explorer-summary-grid {{ grid-template-columns: 1fr; }}
}}

</style>
""",
        unsafe_allow_html=True,
    )


# =========================================================
# UI HELPERS
# =========================================================

def explain_score_band(score):
    tier = get_score_tier(score)
    if tier == "good":
        return "✅ The AI answer is close to the fatwa guidance and shows good alignment. The response captures the key meaning and important conditions."
    if tier == "moderate":
        return "⚠️ The AI answer is moderately aligned. The response captures some key points, but important fatwa conditions still need review or are incomplete."
    return "❌ The AI answer is weakly aligned. The response does not closely match the fatwa guidance and should not be relied on without significant correction."

def explain_metric(label, value):
    try:
        value = float(value)
    except Exception:
        value = 0.0

    if label == "word":
        if value >= 70:
            return "Many important words and terms are similar."
        if value >= 40:
            return "Some important words and terms are similar."
        return "The word-level match is still low."

    if label == "meaning":
        if value >= 70:
            return "The meaning of the AI answer is very close to the fatwa."
        if value >= 40:
            return "The meaning is fairly close, but not fully accurate yet."
        return "The meaning is still quite different from the fatwa."

    if label == "keyword":
        if value >= 70:
            return "Most important fatwa points were mentioned."
        if value >= 40:
            return "Some important fatwa points were mentioned."
        return "Many important fatwa points were not mentioned."

    return ""


def create_score_circle(score):
    try:
        score = max(0, min(100, int(round(float(score)))))
    except Exception:
        score = 0

    tier = get_score_tier(score)
    ring_color, track_color, text_color = get_score_tier_colors(tier)
    css_class = f"score-circle score-circle-{get_score_css_class(tier)}"
    degrees = int(score * 3.6)
    return f"""
    <div class="{css_class}" style="background: conic-gradient({ring_color} {degrees}deg, {track_color} {degrees}deg);">
        <div class="score-circle-inner" style="color:{text_color};">{score}%</div>
    </div>
    """

def score_color(score: float) -> str:
    tier = get_score_tier(score)
    _, _, text_color = get_score_tier_colors(tier)
    return text_color


def score_css_band(score: float) -> str:
    return get_score_css_class(get_score_tier(score))


def render_score_value_html(score: float, suffix: str = "%", extra_class: str = "") -> str:
    """Render a score number with semantic colour — use inside any card."""
    colour = score_color(score)
    band = score_css_band(score)
    classes = f"result-card-score result-card-score-{band} {extra_class}".strip()
    try:
        display = f"{float(score):.1f}{suffix}"
    except Exception:
        display = f"-{suffix}"
    return f'<span class="{classes}" style="color:{colour};">{display}</span>'


def render_result_card_html(title: str, score: float, description: str = "") -> str:
    """Render a result card whose top border and score number both reflect the score band."""
    band = score_css_band(score)
    colour = score_color(score)
    try:
        score_display = f"{float(score):.1f}%"
    except Exception:
        score_display = "-"
    desc_html = f'<div class="result-card-text">{html.escape(description)}</div>' if description else ""
    return (
        f'<div class="result-card result-card-{band}">'
        f'  <div class="result-card-title">{html.escape(title)}</div>'
        f'  <div class="result-card-score result-card-score-{band}" style="color:{colour};">{score_display}</div>'
        f'  {desc_html}'
        f'</div>'
    )


def render_align_score_html(score: float) -> str:
    """Render an alignment score with correct semantic colour for ranking cards."""
    colour = score_color(score)
    band = score_css_band(score)
    try:
        display = f"{float(score):.1f}%"
    except Exception:
        display = "-"
    return f'<span class="align-score align-score-{band}" style="color:{colour};">{display}</span>'


def render_metric_card_html(label: str, value: float, description: str = "", is_score: bool = True) -> str:
    """Render a metric card whose top stripe and value colour reflect the score band."""
    band = score_css_band(value) if is_score else "info"
    colour = score_color(value) if is_score else COLORS["navy"]
    try:
        display = f"{float(value):.1f}%"
    except Exception:
        display = "-"
    stripe_class = f"metric-card metric-card-{band}" if is_score else "metric-card"
    desc_html = f'<div class="small-note" style="margin-top:0.4rem;">{html.escape(description)}</div>' if description else ""
    return (
        f'<div class="{stripe_class}">'
        f'  <div class="metric-label">{html.escape(label)}</div>'
        f'  <div class="metric-value metric-value-{band}" style="color:{colour};">{display}</div>'
        f'  {desc_html}'
        f'</div>'
    )


def render_header():
    html_block = textwrap.dedent("""
        <div class="header-main">
            <div>
                <h1>AI Fatwa Alignment Assessment System</h1>
                <p>Evaluate how closely an AI-generated answer matches fatwa guidance related to Assisted Reproductive Technology (ART)</p>
            </div>
        </div>
    """).strip()
    st.markdown(html_block, unsafe_allow_html=True)


def render_sidebar_profile_card(
    name: str,
    role: str,
    student_id: str,
    supervisor: str,
    institution: str,
    image_path: str = "profile_picture.jpg",
):
    image_uri = _image_to_data_uri(image_path)

    if image_uri:
        avatar_html = f'<img src="{image_uri}" alt="Profile Picture">'
    else:
        avatar_html = '<div class="sidebar-avatar-fallback">🎓</div>'

    profile_html = (
        f'<div class="sidebar-profile-card">'
        f'  <div class="sidebar-profile-top">'
        f'    <div class="sidebar-avatar">{avatar_html}</div>'
        f'    <div>'
        f'      <div class="sidebar-profile-name">{html.escape(name)}</div>'
        f'      <div class="sidebar-profile-role">{html.escape(role)}</div>'
        f'    </div>'
        f'  </div>'
        f'  <div class="sidebar-profile-grid">'
        f'    <div class="sidebar-profile-item">'
        f'      <div class="sidebar-profile-label">Student ID</div>'
        f'      <div class="sidebar-profile-value">{html.escape(student_id)}</div>'
        f'    </div>'
        f'    <div class="sidebar-profile-item">'
        f'      <div class="sidebar-profile-label">Supervisor</div>'
        f'      <div class="sidebar-profile-value">{html.escape(supervisor)}</div>'
        f'    </div>'
        f'    <div class="sidebar-profile-item">'
        f'      <div class="sidebar-profile-label">Institution</div>'
        f'      <div class="sidebar-profile-value">{html.escape(institution)}</div>'
        f'    </div>'
        f'  </div>'
        f'</div>'
    )

    st.markdown(profile_html, unsafe_allow_html=True)


def render_sidebar_section(title: str, icon: str = "•", body_html: str = ""):
    cleaned_body = body_html.strip()

    section_html = (
        f'<div class="sidebar-section-card">'
        f'  <div class="sidebar-section-title">{html.escape(icon)}&nbsp;&nbsp;{html.escape(title)}</div>'
        f'  {cleaned_body}'
        f'</div>'
    )

    st.markdown(section_html, unsafe_allow_html=True)


def render_sidebar_workspace(title: str, subtitle: str, primary_label: str, primary_value: str, secondary_label: str, secondary_value: str):
    html_block = (
        f'<div class="sidebar-workspace-card">'
        f'  <div class="sidebar-kicker">ART fatwa workspace</div>'
        f'  <div class="sidebar-workspace-title">{html.escape(title)}</div>'
        f'  <div class="sidebar-workspace-subtitle">{html.escape(subtitle)}</div>'
        f'  <div class="sidebar-highlight-row">'
        f'    <div class="sidebar-highlight-chip">'
        f'      <div class="sidebar-highlight-label">{html.escape(primary_label)}</div>'
        f'      <div class="sidebar-highlight-value">{html.escape(primary_value)}</div>'
        f'    </div>'
        f'    <div class="sidebar-highlight-chip">'
        f'      <div class="sidebar-highlight-label">{html.escape(secondary_label)}</div>'
        f'      <div class="sidebar-highlight-value">{html.escape(secondary_value)}</div>'
        f'    </div>'
        f'  </div>'
        f'</div>'
    )
    st.markdown(html_block, unsafe_allow_html=True)


def render_sidebar_action_list(items):
    rows = []
    for item in items:
        icon = html.escape(str(item.get("icon", "•")))
        title = html.escape(str(item.get("title", "")))
        text = html.escape(str(item.get("text", "")))
        rows.append(
            f'<div class="sidebar-action-item">'
            f'  <div class="sidebar-action-icon">{icon}</div>'
            f'  <div>'
            f'    <div class="sidebar-action-title">{title}</div>'
            f'    <div class="sidebar-action-text">{text}</div>'
            f'  </div>'
            f'</div>'
        )
    return f'<div class="sidebar-action-list">{"".join(rows)}</div>'


def render_sidebar_topic_pills(topics):
    if not topics:
        return '<div class="sidebar-mini-note"><strong>No recent topics yet.</strong><br>Run an analysis and the sidebar will start surfacing useful patterns.</div>'
    pills = ''.join([f'<span class="sidebar-topic-pill">{html.escape(str(topic))}</span>' for topic in topics])
    return f'<div class="sidebar-pill-row">{pills}</div>'


def render_sidebar_progress(items):
    rows = []
    for item in items:
        name = html.escape(str(item.get("name", "")))
        value = max(0.0, min(100.0, float(item.get("value", 0))))
        value_label = html.escape(str(item.get("label", f"{value:.0f}%")))
        tone = str(item.get("tone", "")).strip().lower()
        if tone == "red":
            fill = COLORS["danger"]
        elif tone == "yellow":
            fill = COLORS["warning"]
        elif tone == "green":
            fill = COLORS["success"]
        elif value >= 70:
            fill = COLORS["success"]
        elif value >= 50:
            fill = COLORS["warning"]
        else:
            fill = COLORS["danger"]
        rows.append(
            f'<div class="sidebar-progress-item">'
            f'  <div class="sidebar-progress-top">'
            f'    <div class="sidebar-progress-name">{name}</div>'
            f'    <div class="sidebar-progress-value">{value_label}</div>'
            f'  </div>'
            f'  <div class="sidebar-progress-bar"><div class="sidebar-progress-fill" style="width:{value:.1f}%; background:{fill};"></div></div>'
            f'</div>'
        )
    return f'<div class="sidebar-progress-stack">{"".join(rows)}</div>'


def render_sidebar_theme_legend():
    legend_html = """
    <div class="sidebar-section-card sidebar-legend-card">
        <div class="sidebar-section-title">◌◌ Score legend</div>
        <div class="sidebar-legend-grid">
            <div class="sidebar-legend-item">
                <span class="sidebar-legend-dot" style="background:#06A77D;"></span>
                <div>
                    <div class="sidebar-legend-name">Good</div>
                    <div class="sidebar-legend-text">70% and above</div>
                </div>
            </div>
            <div class="sidebar-legend-item">
                <span class="sidebar-legend-dot" style="background:#F1A208;"></span>
                <div>
                    <div class="sidebar-legend-name">Moderate</div>
                    <div class="sidebar-legend-text">50% to 69%</div>
                </div>
            </div>
            <div class="sidebar-legend-item">
                <span class="sidebar-legend-dot" style="background:#A31621;"></span>
                <div>
                    <div class="sidebar-legend-name">Weak</div>
                    <div class="sidebar-legend-text">Below 50%</div>
                </div>
            </div>
        </div>
        <div class="sidebar-legend-note">Colors represent alignment strength. <br> Scores show how closely AI responses match fatwa references. </div>
    </div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)


def render_hero_banner(
    image_path=None,
    title="AI Fatwa Alignment System",
    subtitle="How closely do AI responses align with Malaysian Assisted Reproductive Technology (ART) rulings?",
    kicker="Fatwa Alignment Dashboard",
):
    image_uri = _image_to_data_uri(image_path)

    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    safe_kicker = html.escape(kicker)

    if image_uri:
        html_block = f"""
        <div class="hero-image-wrap">
            <img class="hero-single-image" src="{image_uri}" alt="Hero banner">
            <div class="hero-image-overlay">
                <div class="hero-image-content">
                    <div class="hero-kicker">{safe_kicker}</div>
                    <div class="hero-image-title">{safe_title}</div>
                    <div class="hero-image-subtitle">{safe_subtitle}</div>
                </div>
            </div>
        </div>
        """
    else:
        html_block = f"""
        <div class="hero-image-wrap">
            <div class="hero-image-overlay">
                <div class="hero-image-content">
                    <div class="hero-kicker">{safe_kicker}</div>
                    <div class="hero-image-title">{safe_title}</div>
                    <div class="hero-image-subtitle">{safe_subtitle}</div>
                </div>
            </div>
        </div>
        """

    st.markdown(html_block, unsafe_allow_html=True)


def render_section_banner(title, image_path=None, subtitle="", kicker="Section Overview"):
    render_hero_banner(image_path=image_path, title=title, subtitle=subtitle or "Review, compare, and interpret each section with a consistent presentation layout.", kicker=kicker)


def render_fatwa_reference_card(
    state: str,
    topic: str,
    fatwa_text: str,
    question_text: str = "",
):
    state_safe = html.escape(state or "N/A")
    topic_safe = html.escape(topic or "N/A")
    question_safe = html.escape(question_text.strip()) if question_text else ""
    fatwa_text_safe = html.escape((fatwa_text or "").strip())

    question_html = ""
    if question_safe:
        question_html = f'<div class="fatwa-meta-pill">Question / Issue: {question_safe}</div>'

    card_html = (
        f'<div class="fatwa-box">'
        f'  <div class="fatwa-meta-row">'
        f'      <div class="fatwa-meta-pill">State / Source: {state_safe}</div>'
        f'      <div class="fatwa-meta-pill">Topic: {topic_safe}</div>'
        f'      {question_html}'
        f'  </div>'
        f'  <div class="fatwa-title">{topic_safe}</div>'
        f'  <div class="fatwa-text-panel">'
        f'      <p>{fatwa_text_safe}</p>'
        f'  </div>'
        f'</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)


def render_surface_card(title: str, subtitle: str = "", body_html: str = "", soft: bool = False):
    card_class = "panel-card-soft" if soft else "panel-card"
    subtitle_html = f'<div class="panel-card-subtitle">{subtitle}</div>' if subtitle else ""
    html_block = (
        f'<div class="{card_class}">'
        f'  <div class="panel-card-title">{html.escape(title)}</div>'
        f'  {subtitle_html}'
        f'  {body_html}'
        f'</div>'
    )
    st.markdown(html_block, unsafe_allow_html=True)


def render_footer():
    html_block = textwrap.dedent("""
        <div class="footer-wrap">
            <p>
                ★ Amirah Alyahaziqah Bt Mohd Jeffry ★ &nbsp;·&nbsp; Bachelor of Computer Science (Hons.)<br>
                <span style="font-size:0.85rem;">2026 Universiti Teknologi MARA</span>
            </p>
        </div>
    """).strip()
    st.markdown(html_block, unsafe_allow_html=True)


def render_review_workspace_header():
    st.markdown(
        """
        <style>
        .review-workspace-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin: 0.15rem 0 1rem 0;
            padding: 0.7rem 1rem;
            border-radius: 20px;
            border: 1px solid #e3b5a4;
            background: linear-gradient(180deg, #ffffff 0%, #fcf8fb 100%);
            box-shadow: 0 8px 20px rgba(22, 9, 28, 0.05);
        }
        .review-workspace-copy {
            min-width: 0;
        }
        .review-workspace-kicker {
            color: #773344;
            font-size: 0.8rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            margin-bottom: 0.18rem;
        }
        .review-workspace-header h1 {
            margin: 0 0 0.25rem 0;
            color: #160029;
            font-family: 'Inter Tight', 'Inter', sans-serif;
            font-size: 1.25rem;
            line-height: 1.1;
            letter-spacing: -0.02em;
            font-weight: 700;
        }
        .review-workspace-header p {
            margin: 0;
            color: #5d5060;
            font-size: 0.9rem;
            line-height: 1.55;
            max-width: 720px;
        }
        .review-workspace-badges {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            justify-content: flex-end;
            flex: 0 0 auto;
        }
        .review-badge-card {
            min-width: 160px;
            background: linear-gradient(135deg, #162a63 0%, #4a1d62 55%, #7a1657 100%);
            border-radius: 16px;
            padding: 0.6rem 0.8rem;
            border: 1px solid rgba(253,3,99,0.14);
            box-shadow: 0 8px 18px rgba(20, 10, 33, 0.12);
        }
        .review-badge-card span {
            display: block;
            color: rgba(255,255,255,0.62);
            font-size: 0.74rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.15rem;
        }
        .review-badge-card strong {
            color: #ffffff;
            font-size: 0.85rem;
            line-height: 1.35;
            font-weight: 700;
        }
        @media (max-width: 1100px) {
            .review-workspace-header {
                flex-direction: column;
                align-items: stretch;
            }
            .review-workspace-badges {
                justify-content: flex-start;
            }
        }
        </style>
        <div class="review-workspace-header">
            <div class="review-workspace-copy">
                <div class="review-workspace-kicker">Single Review</div>
                <h1>AI Fatwa Alignment Review</h1>
                <p>Compact scoring layout with a visible similarity breakdown and a cleaner result flow.</p>
            </div>
            <div class="review-workspace-badges">
                <div class="review-badge-card">
                    <span>Visual focus</span>
                    <strong>Score + similarity</strong>
                </div>
                <div class="review-badge-card">
                    <span>Model</span>
                    <strong>Lexical · Semantic · Coverage</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )