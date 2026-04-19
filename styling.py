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

html {{ font-size: 8.5px !important; }}
body {{ overflow-x: hidden !important; }}
.stApp {{ overflow-x: hidden !important; }}

* {{
    box-sizing: border-box;
}}

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

html {{
    scroll-behavior: smooth;
}}

body {{
    color: {COLORS["text_primary"]};
}}

/* ── APP BACKGROUND ──────────────────────────────────── */
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(
        180deg,
        #f4f6f9 0%,
        #efe6ea 100%
    ) !important;
    color: {COLORS["text_primary"]};
}}

.block-container {{
    padding-top: 0.2rem !important;
    padding-left: 0.45rem !important;
    padding-right: 0.45rem !important;
    max-width: none !important;
    width: 100% !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
}}

[data-testid="stAppViewContainer"] {{
    margin: 0 !important;
}}

.main .block-container > div {{
    position: relative;
}}

[data-testid="stHeader"] {{
    background: transparent;
}}

[data-testid="stToolbar"] {{
    right: 1rem;
}}

/* ── SIDEBAR ─────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    min-width: 238px !important;
    max-width: 238px !important;
    width: 238px !important;
    background: linear-gradient(180deg, #160029 0%, #773344 55%, #5f2840 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
    box-shadow: 16px 0 34px rgba(22,0,41,0.18) !important;
}}

[data-testid="stSidebar"] > div:first-child {{
    background: transparent !important;
    padding: 0.4rem 0.4rem 0.55rem 0.4rem !important;
}}

/* Force all sidebar text to be light */
[data-testid="stSidebar"] * {{
    color: rgba(255,255,255,0.90) !important;
}}

[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li,
[data-testid="stSidebar"] .stMarkdown span {{
    color: rgba(255,255,255,0.82) !important;
}}

/* ── SIDEBAR HERO BANNER ─────────────────────────────── */
.sidebar-hero-wrap {{
    margin-bottom: 0.13rem;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 10px 28px rgba(0,0,0,0.2);
}}

.sidebar-hero-image {{
    width: 100%;
    height: auto;
    display: block;
    object-fit: cover;
}}

/* ── SIDEBAR BRAND ───────────────────────────────────── */
.sidebar-brand-card {{
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-left: 6px solid #d44d5c;
    border-radius: 18px;
    padding: 1.25rem 1.1rem;
    margin-bottom: 0.13rem;
    box-shadow: 0 10px 24px rgba(33,50,65,0.22);
    backdrop-filter: blur(4px);
}}
.sidebar-brand-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 0.73rem;
    line-height: 1.15;
    color: #FFFFFF !important;
    margin-bottom: 0.14rem;
}}
.sidebar-brand-subtitle {{
    font-size: 0.72rem;
    line-height: 1.45;
    color: rgba(255,255,255,0.78) !important;
}}

/* ── SIDEBAR WELCOME ─────────────────────────────────── */
.sidebar-welcome-wrap {{
    margin-bottom: 0.17rem;
}}

.sidebar-welcome-banner {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    padding: 0.55rem 0.7rem 1rem 1.15rem;
    position: relative;
    overflow: hidden;
}}

.sidebar-welcome-banner::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: {COLORS["teal_lt"]};
}}

.sidebar-clean-header {{
    padding: 0.4rem 0.15rem 1rem 0.15rem !important;
    margin-bottom: 0.85rem !important;
}}

.sidebar-kicker-line {{
    width: 72px !important;
    height: 4px !important;
    background: {COLORS["teal_lt"]} !important;
    margin-bottom: 0.9rem !important;
    border-radius: 2px;
}}

.sidebar-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.16rem !important;
    line-height: 1.08 !important;
    font-weight: 400;
    color: #FFFFFF;
    letter-spacing: -0.025em !important;
    margin: 0 0 0.8rem 0 !important;
}}

.sidebar-subtitle {{
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem !important;
    line-height: 1.62 !important;
    font-weight: 400;
    color: rgba(255,255,255,0.78) !important;
    margin: 0;
    max-width: 100% !important;
}}

/* ── SIDEBAR WORKSPACE CARD ──────────────────────────── */
.sidebar-workspace-card {{
    background: rgba(255,255,255,0.08) !important;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(158,179,194,0.18) !important;
    box-shadow: 0 12px 26px rgba(13, 24, 47, 0.18) !important;
    border-radius: 18px !important;
    padding: 0.72rem !important;
    margin-bottom: 0.12rem;
}}

.sidebar-kicker {{
    display: inline-flex;
    align-items: center;
    padding: 0.3rem 0.75rem;
    border-radius: 999px;
    background: rgba(158,179,194,0.16) !important;
    color: #DCE7EE !important;
    border: 1px solid rgba(158,179,194,0.22) !important;
    font-size: 0.68rem !important;
    font-weight: 700;
    margin-bottom: 0.08rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}}

.sidebar-workspace-title {{
    font-size: 0.88rem;
    font-weight: 800;
    line-height: 1.25;
    color: #FFFFFF !important;
    margin-bottom: 0.12rem;
}}

.sidebar-workspace-subtitle {{
    font-size: 0.72rem;
    line-height: 1.38;
    color: rgba(255,255,255,0.78) !important;
    margin-bottom: 0.08rem;
}}

.sidebar-highlight-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem !important;
}}

.sidebar-highlight-chip {{
    background: rgba(255,255,255,0.95) !important;
    border: 1px solid rgba(158,179,194,0.22) !important;
    border-top: 4px solid #1C7293 !important;
    border-radius: 14px;
    padding: 0.58rem 0.62rem;
}}

.sidebar-highlight-label {{
    font-size: 0.67rem;
    color: #5E7186 !important;
    margin-bottom: 0.2rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}

.sidebar-highlight-value {{
    font-size: 0.86rem !important;
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
    padding: 0.7rem !important;
    margin-bottom: 0.85rem !important;
}}

.sidebar-section-card * {{
    color: rgba(255,255,255,0.92) !important;
}}

.sidebar-section-title {{
    display: flex;
    align-items: center;
    gap: 0.18rem;
    font-size: 0.66rem !important;
    font-weight: 800;
    margin-bottom: 0.2rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid rgba(158,179,194,0.2) !important;
    color: #DCE7EE !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}}

/* ── SIDEBAR PROGRESS ────────────────────────────────── */
.sidebar-progress-stack {{
    display: grid;
    gap: 0.08rem;
}}

.sidebar-progress-item {{
    display: grid;
    gap: 0.34rem;
}}

.sidebar-progress-top {{
    display: flex;
    justify-content: space-between;
    gap: 0.18rem;
    font-size: 0.77rem;
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
    height: 10px !important;
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
    gap: 0.24rem;
}}

.sidebar-action-item {{
    display: flex;
    gap: 0.08rem;
    align-items: flex-start;
    padding: 0.62rem 0.68rem;
    border-radius: 14px !important;
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(158,179,194,0.14) !important;
}}

.sidebar-action-icon {{
    width: 28px;
    height: 28px;
    min-width: 28px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #cb4a5e !important;
    color: #FFFFFF !important;
    font-size: 0.66rem;
    font-weight: 800;
}}

.sidebar-action-title {{
    font-size: 0.72rem;
    font-weight: 800;
    color: #FFFFFF !important;
    margin-bottom: 0.12rem;
}}

.sidebar-action-text {{
    font-size: 0.66rem;
    line-height: 1.42;
    color: rgba(255,255,255,0.78) !important;
}}

/* ── SIDEBAR MINI NOTE ───────────────────────────────── */
.sidebar-mini-note {{
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(158,179,194,0.14) !important;
    border-radius: 14px;
    padding: 0.62rem 0.68rem;
    color: rgba(255,255,255,0.88) !important;
    line-height: 1.48;
}}

.sidebar-mini-note strong {{
    color: #FFFFFF !important;
}}

/* ── SIDEBAR TOPIC PILLS ─────────────────────────────── */
.sidebar-pill-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.18rem;
}}

.sidebar-topic-pill {{
    display: inline-flex;
    align-items: center;
    padding: 0.42rem 0.8rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.10) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    color: #ffd9e9 !important;
    font-size: 0.66rem;
    font-weight: 700;
    line-height: 1.2;
    box-shadow: 0 6px 12px rgba(0,0,0,0.12);
}}

/* ── SIDEBAR LEGEND CARD ─────────────────────────────── */
.sidebar-legend-card {{
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(158,179,194,0.14) !important;
    border-radius: 18px !important;
    padding: 0.7rem !important;
    margin-bottom: 0.85rem !important;
}}

.sidebar-legend-grid {{
    display: grid;
    gap: 0.18rem;
}}

.sidebar-legend-item {{
    display: flex;
    gap: 0.19rem;
    align-items: flex-start;
    padding: 0.68rem 0.75rem;
    border-radius: 14px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(158,179,194,0.14);
}}

.sidebar-legend-dot {{
    width: 12px;
    height: 12px;
    border-radius: 999px;
    margin-top: 0.24rem;
    box-shadow: 0 0 0 3px rgba(255,255,255,0.08);
}}

.sidebar-legend-name {{
    font-size: 0.82rem;
    font-weight: 800;
    color: #FFFFFF;
}}

.sidebar-legend-text {{
    font-size: 0.66rem;
    line-height: 1.38;
    color: rgba(255,255,255,0.74);
}}

.sidebar-legend-note {{
    margin-top: 0.8rem;
    font-size: 0.66rem;
    line-height: 1.38;
    color: rgba(255,255,255,0.74);
}}

/* ── TABS ────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    background: #f5e9e2 !important;
    border-radius: 14px !important;
    padding: 3px !important;
    gap: 2px !important;
    border: 1px solid #e3b5a4 !important;
}}

.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    border-radius: 8px !important;
    color: #8b6771 !important;
    font-weight: 500 !important;
    font-size: 0.7rem !important;
    padding: 0.32rem 0.65rem !important;
    border: none !important;
    transition: all 0.18s ease !important;
}}

.stTabs [aria-selected="true"] {{
    background: #cb4a5e !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 6px 18px rgba(119,51,68,0.20) !important;
}}

.stTabs [data-baseweb="tab-panel"] {{
    padding-top: 0.45rem;
}}

/* ── HEADER ──────────────────────────────────────────── */
.header-main {{
    background: linear-gradient(180deg, rgba(255,255,255,1) 0%, rgba(253,249,252,1) 100%) !important;
    padding: 1.6rem 2rem;
    margin-bottom: 1.4rem;
    border: 1px solid #e3b5a4;
    border-left: 5px solid #d44d5c !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 28px rgba(59, 29, 74, 0.06) !important;
    display: flex;
    align-items: center;
    gap: 0.18rem;
}}

.header-main h1 {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.1rem;
    font-weight: 400;
    color: #773344 !important;
    margin: 0 0 0.35rem 0;
    letter-spacing: -0.01em;
    line-height: 1.2;
}}

.header-main p {{
    color: #8b6771 !important;
    font-size: 0.7rem;
    font-weight: 400;
    margin: 0;
    line-height: 1.38;
}}

/* ── HERO BANNER (MAIN CONTENT) ──────────────────────── */

.hero-banner {{
    position: relative;
    border-radius: 24px;
    overflow: hidden;
    padding: 2.5rem 2rem;
    color: white;

    background-image: url('dashboard_background.png');
    background-size: 100% 100% !important;
    background-repeat: no-repeat;
    background-position: center;
    
    /* optional overlay */
    background-color: rgba(0,0,0,0.4);
    background-blend-mode: overlay;
}}


.hero-image-wrap {{
    position: relative;
    width: 100%;
    aspect-ratio: 1384 / 250;
    max-height: none !important;
    min-height: 0 !important;
    height: auto !important;
    border-radius: 28px !important;
    overflow: hidden;
    margin-bottom: 0.25rem;
    border: 1px solid rgba(158,179,194,0.20);
    box-shadow: 0 18px 40px rgba(22, 0, 41, 0.14);
    background: #85414f;
}}


.hero-single-image {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center center;
    display: block;
    opacity: 0.90;
    filter: saturate(0.98) contrast(1.00) brightness(0.86);
}}

.hero-bg-fill {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: 72% center;
    opacity: 0.58;
    filter: saturate(0.92) contrast(1.02) brightness(0.78);
    transform: scale(1.03);
}}

.hero-main-image {{
    position: absolute;
    right: 4%;
    bottom: 0;
    height: 100%;
    width: auto;
    max-width: 44%;
    object-fit: contain;
    object-position: right bottom;
    z-index: 2;
    filter: saturate(0.95) contrast(1.02) brightness(0.92);
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
    padding: 1.4rem 1.8rem;
}}

.hero-image-content {{
    width: 100%;
    max-width: 48% !important;
}}

.hero-kicker {{
    display: inline-flex;
    align-items: center;
    padding: 0.48rem 1rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.20);
    color: #ffffff;
    font-size: 0.66rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.13rem;
    backdrop-filter: blur(4px);
}}

.hero-image-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.18rem !important;
    font-weight: 800;
    line-height: 1.04;
    letter-spacing: -0.03em;
    color: #ffffff !important;
    margin: 0 0 0.7rem 0;
    text-shadow: 0 8px 18px rgba(0,0,0,0.20) !important;
}}

.hero-image-subtitle {{
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    line-height: 1.38;
    color: rgba(255,255,255,0.92) !important;
    margin: 0;
    max-width: 92%;
    text-shadow: 0 2px 8px rgba(0,0,0,0.18);
}}

@media (max-width: 900px) {{
    .hero-image-wrap {{
        aspect-ratio: 1384 / 340;
        max-height: none !important;
    }}

    .hero-image-overlay {{
        padding: 1.15rem 1.2rem;
    }}

    .hero-image-content {{
        max-width: 100% !important;
    }}

    .hero-image-title {{
        font-size: 1.45rem !important;
    }}

    .hero-image-subtitle {{
        font-size: 0.66rem;
        max-width: 100%;
    }}
}}



/* ── SECTION BANNER ──────────────────────────────────── */
.section-banner {{
    position: relative;
    width: 100%;
    min-height: 95px;
    border-radius: 20px;
    overflow: hidden;
    margin: 1.4rem 0 1.1rem 0;
    border: 1px solid #e3b5a4;
    box-shadow: 0 10px 28px rgba(59, 29, 74, 0.06);
    background: linear-gradient(135deg, #160029, #773344);
}}

.section-banner img {{
    width: 100%;
    height: 100%;
    min-height: 95px;
    max-height: 90px;
    object-fit: cover;
    display: block;
}}

.section-banner-overlay {{
    position: absolute;
    inset: 0;
    background: rgba(27,59,111,0.48);
    display: flex;
    align-items: center;
    justify-content: center;
}}

.section-banner-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.4rem;
    font-weight: 400;
    color: #FFFFFF;
    margin: 0;
    text-shadow: 0 2px 8px rgba(15,32,68,0.25);
    letter-spacing: 0.01em;
}}

/* ── CARDS ───────────────────────────────────────────── */
.soft-card, .card {{
    background: #FFFFFF;
    border-radius: 18px !important;
    padding: 0.82rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 10px 28px rgba(22, 32, 51, 0.06) !important;
    color: #2a1421;
}}

.card {{
    transition: all 0.22s ease;
    height: 100%;
}}

.card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(15,32,68,0.10);
    border-color: #e3b5a4;
}}

.card-header {{
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.08rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #f5e9e2;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}}

/* ── METRIC CARDS ────────────────────────────────────── */
.metric-card {{
    background: #FFFFFF;
    border-radius: 18px !important;
    padding: 1.1rem 1.2rem;
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
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #d44d5c 0%, #773344 100%) !important;
}}

.metric-card-good::before {{ background: #06A77D !important; }}
.metric-card-mid::before  {{ background: #F1A208 !important; }}
.metric-card-low::before  {{ background: #A31621 !important; }}

.metric-label {{
    font-size: 0.72rem;
    font-weight: 700;
    color: #8b6771;
    margin-bottom: 0.5rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}

.metric-value {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.35rem;
    font-weight: 400;
    color: #773344;
    line-height: 1.2;
}}

.metric-value-good {{ color: #06A77D !important; }}
.metric-value-mid  {{ color: #C27D06 !important; }}
.metric-value-low  {{ color: #A31621 !important; }}

/* ── SECTION TITLES ──────────────────────────────────── */
.section-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.36rem;
    font-weight: 400;
    color: #773344;
    margin: 1.8rem 0 1.1rem 0;
    position: relative;
    display: inline-block;
    padding-bottom: 0.6rem;
    letter-spacing: -0.01em;
}}

.section-title::after {{
    content: '';
    position: absolute;
    left: 0;
    bottom: 0;
    width: 48px;
    height: 3px;
    background: linear-gradient(90deg, #d44d5c 0%, #773344 100%);
    border-radius: 2px;
}}

.section-subtitle {{
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    font-weight: 600;
    color: #160029;
    margin: 1.2rem 0 0.85rem 0;
    letter-spacing: -0.01em;
}}

/* ── MESSAGE BOXES ───────────────────────────────────── */
.msg-box {{
    padding: 0.55rem 0.75rem;
    border-radius: 16px !important;
    margin: 0.85rem 0;
    background: #FFFFFF;
    border: 1px solid #e3b5a4;
    border-left: 5px solid #773344;
    box-shadow: 0 2px 8px rgba(15,32,68,0.05);
    color: #2a1421;
    line-height: 1.45;
    font-size: 0.72rem;
}}

.msg-box strong {{
    color: #160029;
}}

.msg-success {{
    border-left-color: #06A77D !important;
    background: #f6fbf8 !important;
}}

.msg-info {{
    border-left-color: #773344 !important;
    background: #faf4f8 !important;
}}

.msg-warning {{
    border-left-color: #F1A208 !important;
    background: #fff8ef !important;
}}

/* ── KEYWORD CHIPS ───────────────────────────────────── */
.keyword-container {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.08rem;
    margin-top: 0.85rem;
}}

.keyword-match, .keyword-miss {{
    display: inline-flex;
    align-items: center;
    padding: 0.36rem 0.85rem;
    border-radius: 6px;
    font-size: 0.83rem;
    font-weight: 500;
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
    padding: 0.5rem 0.6rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 10px 28px rgba(22, 32, 51, 0.06) !important;
    color: #2a1421;
    margin-bottom: 0.08rem;
}}

.fatwa-meta-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.15rem;
    margin-bottom: 0.15rem;
}}

.fatwa-meta-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.09rem;
    padding: 0.3rem 0.65rem;
    border-radius: 6px;
    background: #f5e9e2;
    border: 1px solid #e3b5a4;
    color: #5f2840;
    font-size: 0.66rem;
    font-weight: 500;
}}

.fatwa-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 400;
    color: #160029;
    margin-bottom: 0.18rem;
    line-height: 1.25;
    word-break: break-word;
}}

.fatwa-text-panel {{
    background: linear-gradient(180deg, #ffffff 0%, #f9f1ec 100%);
    border: 1px solid #e3b5a4;
    border-radius: 8px;
    padding: 0.5rem 0.65rem;
}}

.fatwa-text-panel p {{
    margin: 0;
    color: #160029;
    line-height: 1.45;
    font-size: 0.68rem;
    white-space: pre-wrap;
    word-break: break-word;
}}

/* ── BADGES ──────────────────────────────────────────── */
.badge {{
    display: inline-block;
    padding: 0.28rem 0.8rem;
    border-radius: 5px;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}}

.badge-good {{
    background: rgba(25,135,84,0.12) !important;
    color: #198754 !important;
    border: 1px solid rgba(25,135,84,0.26) !important;
}}

.badge-mid {{
    background: rgba(194,125,6,0.12) !important;
    color: #9A6A18 !important;
    border: 1px solid rgba(194,125,6,0.24) !important;
}}

.badge-low {{
    background: rgba(180,35,79,0.10) !important;
    color: #b4234f !important;
    border: 1px solid rgba(180,35,79,0.20) !important;
}}

/* ── SCORE CIRCLE ────────────────────────────────────── */
.score-circle {{
    width: 136px;
    height: 136px;
    border-radius: 50%;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow: 0 4px 20px rgba(15,32,68,0.14);
}}

.score-circle::before {{
    content: '';
    position: absolute;
    width: 108px;
    height: 108px;
    border-radius: 50%;
    background: #FFFFFF;
}}

.score-circle-inner {{
    position: relative;
    z-index: 2;
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.28rem;
    font-weight: 400;
    color: #773344;
}}
.score-circle-good .score-circle-inner {{ color: #198754; }}
.score-circle-mid .score-circle-inner {{ color: #c27d06; }}
.score-circle-low .score-circle-inner {{ color: #b4234f; }}

/* ── INFO GRID ───────────────────────────────────────── */
.info-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
    gap: 0.08rem;
}}

.info-item {{
    background: #EEF4F8;
    padding: 0.9rem;
    border-radius: 8px;
    border: 1px solid #e3b5a4;
}}

.info-label {{
    font-size: 0.72rem;
    font-weight: 700;
    color: #8b6771;
    margin-bottom: 0.08rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.info-value {{
    font-size: 0.96rem;
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
    margin: 1.8rem 0;
    opacity: 0.8;
}}

/* ── RESULT CARDS ────────────────────────────────────── */
.result-card {{
    background: #FFFFFF;
    border-radius: 18px !important;
    padding: 0.85rem 0.82rem;
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
    height: 4px;
    background: linear-gradient(90deg, #d44d5c 0%, #773344 100%) !important;
}}

.result-card-good::before  {{ background: #06A77D !important; }}
.result-card-mid::before   {{ background: #F1A208 !important; }}
.result-card-low::before   {{ background: #A31621 !important; }}

.result-card-title {{
    color: #8b6771;
    font-weight: 600;
    font-size: 0.66rem;
    margin-bottom: 0.15rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.result-card-score {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.28rem;
    font-weight: 400;
    margin: 0.3rem 0 0.5rem 0;
}}

.result-card-score-good {{ color: #06A77D; }}
.result-card-score-mid  {{ color: #C27D06; }}
.result-card-score-low  {{ color: #A31621; }}

.result-card-text {{
    color: #5d3945;
    font-size: 0.68rem;
    line-height: 1.42;
}}

/* ── POINTS CARD ─────────────────────────────────────── */
.points-card {{
    background: #FFFFFF;
    border-radius: 18px !important;
    padding: 0.82rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 10px 28px rgba(22, 32, 51, 0.06) !important;
    height: 100%;
}}

.points-card-header {{
    font-family: 'Inter', sans-serif;
    font-size: 0.66rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.08rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e3b5a4;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

/* ── SMALL NOTE ──────────────────────────────────────── */
.small-note {{
    color: #8b6771;
    font-size: 0.7rem;
    line-height: 1.42;
}}

/* ── CHART CARD ──────────────────────────────────────── */
.chart-card {{
    background: #FFFFFF;
    border-radius: 18px !important;
    padding: 1rem 1rem 0.6rem 1rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 10px 28px rgba(22, 32, 51, 0.06) !important;
    margin-bottom: 0.13rem;
}}

/* ── SIMILARITY BREAKDOWN (BEAUTIFUL CARD) ───────────── */
.similarity-visual-shell {{
    background: linear-gradient(135deg, #ffffff 0%, #faf4f8 100%);
    border: 1px solid #e3b5a4;
    border-radius: 24px;
    padding: 0.9rem;
    box-shadow: 0 12px 28px rgba(25, 14, 36, 0.08);
    margin-bottom: 0.13rem;
}}

.similarity-visual-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #e3b5a4;
}}

.similarity-visual-kicker {{
    color: #773344;
    font-size: 0.7rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.2rem;
}}

.similarity-visual-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 0.96rem;
    color: #160029;
}}

.similarity-score-pill {{
    background: rgba(253,3,99,0.12);
    border: 1.5px solid #d44d5c;
    border-radius: 40px;
    padding: 0.5rem 1.2rem;
}}

.similarity-score-pill span {{
    color: #d44d5c;
    font-weight: 800;
    font-size: 0.66rem;
}}

.similarity-ring-row {{
    display: flex;
    align-items: center;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
}}

.similarity-ring {{
    width: 130px;
    height: 95px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    flex-shrink: 0;
}}

.similarity-ring-inner {{
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: #ffffff;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
}}

.similarity-ring-inner strong {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.8rem;
    line-height: 1;
}}

.similarity-ring-inner span {{
    font-size: 0.7rem;
    color: #8b6771;
}}

.similarity-ring-copy h3 {{
    margin: 0 0 0.4rem 0;
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    color: #160029;
}}

.similarity-ring-copy p {{
    margin: 0;
    color: #5d3945;
    line-height: 1.42;
}}

.similarity-mini-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.08rem;
    margin-bottom: 1.5rem;
}}

.similarity-mini-card {{
    background: #f9f1ec;
    border-radius: 12px;
    padding: 0.75rem;
    border-left: 4px solid #e3b5a4;
}}

.similarity-mini-card span {{
    color: #8b6771;
    font-size: 0.7rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    display: block;
    margin-bottom: 0.13rem;
}}

.similarity-mini-card strong {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.4rem;
    font-weight: 400;
    display: block;
    margin-bottom: 0.2rem;
}}

.similarity-mini-card p {{
    margin: 0;
    color: #5d3945;
    font-size: 0.66rem;
    line-height: 1.5;
}}

.similarity-bars-wrap {{
    background: #f9f1ec;
    border-radius: 18px;
    padding: 1rem;
    border: 1px solid #e3b5a4;
}}

.similarity-bars-title {{
    color: #8b6771;
    font-size: 0.66rem;
    font-weight: 800;
    text-transform: uppercase;
    margin-bottom: 0.13rem;
    letter-spacing: 0.05em;
}}

.similarity-bar-row {{
    display: flex;
    align-items: center;
    gap: 0.08rem;
    margin-bottom: 0.2rem;
}}

.similarity-bar-row label {{
    width: 80px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #773344;
}}

.similarity-bar-track {{
    flex: 1;
    height: 8px;
    background: #e3b5a4;
    border-radius: 10px;
    overflow: hidden;
}}

.similarity-bar-fill {{
    height: 100%;
    border-radius: 10px;
    background: linear-gradient(90deg, #d44d5c, #b24758);
}}

.similarity-bar-row strong {{
    width: 40px;
    text-align: right;
    color: #160029;
    font-size: 0.85rem;
    font-weight: 700;
}}

/* ── BUTTONS ─────────────────────────────────────────── */
.stButton > button,
.stDownloadButton > button {{
    background: #cb4a5e !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.34rem 0.78rem !important;
    font-size: 0.7rem !important;
    box-shadow: 0 10px 22px rgba(119,51,68,0.18) !important;
    transition: all 0.18s ease !important;
    letter-spacing: 0.01em !important;
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
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    margin-bottom: 0.35rem !important;
}}



/* ── RADIO / SEGMENTED INPUTS ────────────────────────── */
[data-testid="stRadio"] > div {{color:#2a1421 !important;}}
[data-testid="stRadio"] label {{color:#2a1421 !important; font-weight:600 !important; opacity:1 !important;}}
[data-testid="stRadio"] [role="radiogroup"] {{
    background: linear-gradient(180deg,#fffdfc 0%,#fbf3ee 100%) !important;
    border: 1px solid #e3b5a4 !important;
    border-radius: 22px !important;
    padding: 0.4rem !important;
    gap: 0.45rem !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.55);
}}
[data-testid="stRadio"] [role="radiogroup"] > label {{
    flex: 1 1 0 !important;
    justify-content: center !important;
    text-align: center !important;
    min-height: 44px !important;
    border-radius: 16px !important;
    padding: 0.55rem 0.85rem !important;
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
[data-testid="stRadio"] [role="radiogroup"] p {{color:#5d3945 !important;font-weight:700 !important;font-size:0.88rem !important;opacity:1 !important;}}

/* ── INPUT SURFACES / LIGHTER SELECTS ───────────────── */
[data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stTextInputRootElement"],
.stTextInput > div > div {{
    background: linear-gradient(180deg, #fffefe 0%, #fbf4ef 100%) !important;
    border: 1.5px solid #e3b5a4 !important;
    border-radius: 18px !important;
    min-height: 58px !important;
    box-shadow: 0 8px 18px rgba(44, 21, 33, 0.06) !important;
    transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease !important;
}}

[data-testid="stMultiSelect"] [data-baseweb="select"] > div:hover,
[data-testid="stSelectbox"] [data-baseweb="select"] > div:hover,
[data-testid="stTextInputRootElement"]:hover,
.stTextInput > div > div:hover {{
    border-color: #d49287 !important;
    box-shadow: 0 10px 22px rgba(44, 21, 33, 0.08) !important;
}}

[data-testid="stMultiSelect"] [data-baseweb="select"] > div:focus-within,
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
[data-testid="stTextInputRootElement"]:focus-within,
.stTextInput > div > div:focus-within {{
    border-color: #b24758 !important;
    box-shadow: 0 0 0 4px rgba(212,77,92,0.12), 0 12px 24px rgba(44,21,33,0.08) !important;
    transform: translateY(-1px);
}}

[data-testid="stMultiSelect"] [data-baseweb="tag"] {{
    background: linear-gradient(135deg, #f7c7cf 0%, #ef9cac 100%) !important;
    color:#4a2030 !important;
    border-radius:999px !important;
    border:1px solid rgba(178,71,88,0.18) !important;
    box-shadow:none !important;
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
    padding: 0.35rem !important;
    transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease !important;
}}

.stTextArea > div > div:focus-within {{
    border-color: #b24758 !important;
    box-shadow: 0 0 0 4px rgba(212,77,92,0.12), 0 14px 28px rgba(44,21,33,0.08) !important;
    transform: translateY(-1px);
}}

.stTextArea textarea {{
    background: transparent !important;
    border: none !important;
    border-radius: 18px !important;
    padding: 0.65rem 0.7rem 0.72rem 0.7rem !important;
    color: #2a1421 !important;
    font-size: 0.74rem !important;
    font-family: 'Inter', sans-serif !important;
    line-height: 1.45 !important;
    box-shadow: none !important;
    min-height: 72px !important;
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
}}

/* ── TEXT INPUT ──────────────────────────────────────── */
.stTextInput input {{
    background: transparent !important;
    border: none !important;
    border-radius: 16px !important;
    padding: 0.38rem 0.5rem !important;
    color: #2a1421 !important;
    font-size: 0.74rem !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: none !important;
}}

.stTextInput input:focus {{
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}}

/* ── SELECTBOX / MULTISELECT ─────────────────────────── */
[data-testid="stSelectbox"] > div > div,
.stSelectbox [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] > div > div {{
    background: transparent !important;
    border: none !important;
    border-radius: 16px !important;
    color: #2a1421 !important;
    font-size: 0.74rem !important;
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
    border-radius: 16px;
    border: 1px solid #e3b5a4;
    box-shadow: 0 10px 24px rgba(39,34,51,0.08);
    background: #FFFFFF;
}}

.light-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    overflow: hidden;
    border-radius: 16px;
}}

.light-table thead th {{
    background: #f7f0f5 !important;
    color: #773344 !important;
    font-weight: 700;
    font-size: 0.66rem;
    padding: 0.48rem 0.56rem;
    text-align: left;
    white-space: nowrap;
    letter-spacing: 0.03em;
    border-bottom: 1px solid rgba(0,0,0,0.05);
}}

.light-table thead th:first-child {{
    border-radius: 16px 0 0 0;
}}

.light-table thead th:last-child {{
    border-radius: 0 16px 0 0;
}}

.light-table tbody td {{
    background: #FFFFFF;
    color: #2a1421;
    font-size: 0.68rem;
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid #e3b5a4;
    vertical-align: middle;
    line-height: 1.48;
}}

.light-table tbody tr:nth-child(even) td {{
    background: #FCF8F5;
}}

.light-table tbody tr:hover td {{
    background: #F8EFE8;
    transition: background 0.14s ease;
}}

.light-table tbody tr:last-child td {{
    border-bottom: none;
}}

/* ── OVERVIEW CHART CARD ─────────────────────────────── */
.overview-chart-card {{
    background: #FFFFFF;
    border-radius: 18px !important;
    padding: 0.55rem 0.75rem 0.85rem 1.2rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 10px 28px rgba(22, 32, 51, 0.06) !important;
    margin-bottom: 0.18rem;
}}

.overview-chart-header {{
    display: flex;
    align-items: center;
    gap: 0.18rem;
    font-family: 'Inter', sans-serif;
    font-size: 0.68rem;
    font-weight: 700;
    color: #160029;
    flex-wrap: wrap;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}

/* ── TOPIC CARDS ─────────────────────────────────────── */
.topic-card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.18rem;
}}

.topic-card {{
    background: #FFFFFF;
    border: 1px solid #e3b5a4;
    border-top: 5px solid #b24758;
    border-radius: 16px;
    padding: 1rem;
    box-shadow: 0 8px 18px rgba(39,34,51,0.08);
}}

.topic-card-title {{
    font-size: 0.96rem;
    font-weight: 800;
    color: #2a1421;
    line-height: 1.45;
    margin-bottom: 0.18rem;
}}

.topic-card-meta {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.6rem;
}}

.topic-card-pill {{
    display: inline-flex;
    align-items: center;
    padding: 0.38rem 0.74rem;
    border-radius: 999px;
    background: #f5e9e2;
    color: #160029;
    border: 1px solid #e3b5a4;
    font-size: 0.66rem;
    font-weight: 800;
}}

.topic-card-count {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 0.96rem;
    color: #773344;
}}

/* ── PAGER BAR ───────────────────────────────────────── */
.pager-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.08rem;
    flex-wrap: wrap;
    background: #FFFFFF;
    border: 1px solid #e3b5a4;
    border-left: 5px solid #b24758;
    border-radius: 14px;
    padding: 0.55rem 0.7rem;
    margin-bottom: 0.08rem;
}}

.pager-note {{
    color: #8b6771;
    font-size: 0.72rem;
    line-height: 1.5;
}}

.pager-actions {{
    display: flex;
    gap: 0.08rem;
    align-items: center;
}}

.pager-chip {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 90px;
    padding: 0.5rem 0.85rem;
    border-radius: 999px;
    background: #f5e9e2;
    color: #160029;
    border: 1px solid #e3b5a4;
    font-size: 0.8rem;
    font-weight: 700;
}}

/* ── COMPARISON CARD ─────────────────────────────────── */
.comparison-card {{
    background: #FFFFFF;
    border-radius: 12px;
    padding: 1.2rem;
    border: 1px solid #e3b5a4;
    box-shadow: 0 2px 10px rgba(15,32,68,0.06);
    margin-bottom: 0.11rem;
    height: 100%;
}}

.comparison-card-header {{
    font-family: 'Inter', sans-serif;
    font-size: 0.68rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.15rem;
    padding-bottom: 0.45rem;
    border-bottom: 2px solid #f5e9e2;
    line-height: 1.3;
    word-break: break-word;
}}

/* ── ALIGNMENT RANKING ───────────────────────────────── */
.align-panel-title {{
    font-family: 'Inter', sans-serif;
    font-size: 0.66rem;
    font-weight: 700;
    color: #8b6771;
    margin-bottom: 0.2rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}

.align-rank-card {{
    background: #FFFFFF;
    border-radius: 10px;
    border: 1px solid #e3b5a4;
    box-shadow: 0 2px 8px rgba(15,32,68,0.05);
    padding: 0.55rem 0.75rem;
    margin-bottom: 0.15rem;
    transition: transform 0.16s ease, box-shadow 0.16s ease;
}}

.align-rank-card:hover {{
    transform: translateY(-1px);
    box-shadow: 0 5px 16px rgba(15,32,68,0.08);
}}

.align-rank-topic {{
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    color: #160029;
    margin-bottom: 0.15rem;
    line-height: 1.4;
    word-break: break-word;
}}

.align-rank-row {{
    display: flex;
    align-items: center;
    gap: 0.08rem;
    margin-bottom: 0.45rem;
    flex-wrap: wrap;
}}

.align-score {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.25rem;
    font-weight: 400;
    line-height: 1;
}}

.align-band {{
    font-family: 'Inter', sans-serif;
    font-size: 0.66rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}}

.align-n {{
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    color: #8b6771;
    margin-left: auto;
}}

.align-bar-bg {{
    background: #f5e9e2;
    border-radius: 99px;
    height: 5px;
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
    gap: 0.18rem;
    padding: 0.45rem 0;
    border-bottom: 1px solid #e3b5a4;
    flex-wrap: nowrap;
}}

.align-full-rank {{
    font-family: 'Inter', sans-serif;
    font-size: 0.66rem;
    font-weight: 700;
    min-width: 2rem;
    color: #8b6771;
}}

.align-full-topic {{
    font-family: 'Inter', sans-serif;
    font-size: 0.83rem;
    color: #2a1421;
    min-width: 150px;
    word-break: break-word;
    white-space: normal;
    line-height: 1.4;
}}

.align-full-score {{
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    min-width: 3.5rem;
    text-align: right;
}}

.align-full-n {{
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    color: #8b6771;
    min-width: 2.5rem;
}}

/* ── DONUT INSIGHT CARDS ─────────────────────────────── */
.donut-insight-card {{
    display: flex;
    align-items: stretch;
    gap: 0;
    background: #FFFFFF;
    border-radius: 8px;
    border: 1px solid #e3b5a4;
    box-shadow: 0 2px 8px rgba(15,32,68,0.05);
    margin-bottom: 0.15rem;
    overflow: hidden;
}}

.donut-insight-accent {{
    width: 4px;
    min-height: 100%;
    flex-shrink: 0;
    border-radius: 0;
}}

.donut-insight-body {{
    padding: 0.65rem 0.9rem;
    flex: 1;
}}

.donut-insight-name {{
    font-family: 'Inter', sans-serif;
    font-size: 0.68rem;
    font-weight: 600;
    color: #160029;
    margin-bottom: 0.18rem;
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
    font-size: 1.3rem;
    font-weight: 400;
    color: #773344;
    line-height: 1;
}}

.donut-insight-pct {{
    font-family: 'Inter', sans-serif;
    font-size: 0.66rem;
    font-weight: 400;
    color: #8b6771;
}}



/* ── EDITORIAL META PILLS ───────────────────────────── */
.editorial-meta {{
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.75rem !important;
    margin-top: 1.1rem !important;
    padding-top: 0 !important;
    border-top: none !important;
}}

.editorial-meta span {{
    display: block;
    background: linear-gradient(180deg, #fffefe 0%, #f8efea 100%);
    border: 1px solid #e3b5a4;
    border-radius: 18px;
    padding: 0.6rem 0.8rem 0.9rem 1rem !important;
    color: #5d3945 !important;
    box-shadow: 0 10px 22px rgba(44, 21, 33, 0.05);
    line-height: 1.38;
}}

.editorial-meta span:before {{
    content: '';
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 999px;
    background: linear-gradient(135deg, #d44d5c 0%, #b24758 100%);
    margin-right: 0.6rem;
    vertical-align: middle;
    position: static !important;
}}

/* ── BATCH RESULT HELPERS ───────────────────────────── */
.batch-results-shell {{
    background: linear-gradient(180deg, #ffffff 0%, #f9f1ec 100%);
    border: 1px solid #e3b5a4;
    border-radius: 24px;
    padding: 1rem 1.05rem;
    box-shadow: 0 12px 26px rgba(44, 21, 33, 0.06);
    margin: 1rem 0 0.9rem 0;
}}

.batch-results-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 0.66rem;
    font-weight: 700;
    color: #251329;
    margin-bottom: 0.2rem;
}}

.batch-results-copy,
.batch-readable-note,
.result-reading-guide-copy {{
    color: #6b5660;
    font-size: 0.72rem;
    line-height: 1.5;
}}

.batch-readable-note,
.result-reading-guide {{
    background: linear-gradient(180deg, #fffefe 0%, #f8efea 100%);
    border: 1px solid #e3b5a4;
    border-left: 4px solid #d44d5c;
    border-radius: 20px;
    padding: 0.48rem 0.56rem;
    margin: 0.95rem 0;
    box-shadow: 0 8px 20px rgba(44, 21, 33, 0.05);
}}

.result-reading-guide-title {{
    font-size: 0.66rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #a3195b;
    margin-bottom: 0.15rem;
}}

/* safer table area for larger batch outputs */
.light-table-wrap {{
    width: 100%;
    overflow-x: auto;
    overflow-y: visible;
}}

@media (max-width: 900px) {{
    .editorial-meta {{
        grid-template-columns: 1fr;
    }}
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
    font-size: 0.72rem;
    font-family: 'Inter', sans-serif;
    line-height: 1.45;
    margin: 0;
}}

/* ── RESPONSIVE ──────────────────────────────────────── */
@media (max-width: 1200px) {{
    [data-testid="stSidebar"] {{
        min-width: 260px !important;
        max-width: 260px !important;
        width: 260px !important;
    }}
}}

@media (max-width: 1100px) {{
    .hero-image-wrap {{
        height: 180px !important;
    }}
    .hero-main-image {{
        max-width: 46%;
        right: 2%;
    }}
    .hero-image-content {{
        max-width: 60% !important;
    }}
    .hero-image-title {{
        font-size: 2.05rem !important;
    }}
}}

@media (max-width: 992px) {{
    .hero-image-title {{
        font-size: 1.9rem !important;
    }}
    .hero-image-subtitle {{
        font-size: 0.73rem;
    }}
    .section-banner-title {{
        font-size: 1.25rem;
    }}
    .similarity-ring-row {{
        flex-direction: column;
        text-align: center;
    }}
    .similarity-mini-grid {{
        grid-template-columns: 1fr;
    }}
}}

@media (max-width: 768px) {{
    .block-container {{
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
    .header-main {{
        padding: 1.2rem 1.4rem !important;
    }}
    .header-main h1 {{
        font-size: 0.66rem;
    }}
    .hero-image-wrap {{
        height: 240px !important;
        border-radius: 24px !important;
    }}
    .hero-main-image {{
        opacity: 0.42;
        max-width: 58%;
        right: -2%;
    }}
    .hero-image-overlay {{
        padding: 1.4rem 1.4rem;
    }}
    .hero-image-content {{
        max-width: 82% !important;
    }}
    .hero-image-title {{
        font-size: 1.7rem !important;
    }}
    .hero-image-subtitle {{
        font-size: 0.7rem;
        line-height: 1.5;
    }}
    .hero-kicker {{
        font-size: 0.68rem;
        padding: 0.4rem 0.8rem;
        margin-bottom: 0.08rem;
    }}
    .section-banner {{
        min-height: 110px;
    }}
    .section-banner-title {{
        font-size: 0.7rem;
    }}
    .light-table {{
        min-width: 520px;
    }}
    .similarity-bar-row {{
        flex-wrap: wrap;
    }}
    .similarity-bar-row label {{
        width: 100%;
    }}
}}


@media (max-width: 620px) {{
    .hero-image-wrap {{
        height: 90px !important;
    }}
    .hero-main-image {{
        display: none;
    }}
    .hero-image-content {{
        max-width: 100% !important;
    }}
    .hero-image-title {{
        font-size: 1.5rem !important;
    }}
    .hero-image-subtitle {{
        font-size: 0.72rem;
    }}
}}

/* ── MINIMAL TAB HERO ───────────────────────────────── */
.tab-minimal-hero {{
    background: linear-gradient(180deg,#fffdfc 0%,#fbf4ef 100%);
    border: 1px solid #e3b5a4;
    border-radius: 28px;
    padding: 0.55rem 0.75rem 1.1rem 1.2rem;
    box-shadow: 0 14px 30px rgba(41,22,35,0.05);
    margin: 0.15rem 0 0.85rem 0;
}}
.tab-minimal-kicker {{
    color:#b01f55;
    font-size:0.74rem;
    font-weight:800;
    letter-spacing:0.16em;
    text-transform:uppercase;
    margin-bottom:0.35rem;
}}
.tab-minimal-title {{
    font-family:'Inter Tight','Inter',sans-serif;
    font-size:1.15rem;
    font-weight:800;
    color:#221221;
    line-height:1.2;
}}
.tab-minimal-copy {{
    color:#766772;
    font-size:0.95rem;
    line-height:1.65;
    margin-top:0.45rem;
}}
.mini-explainer-card {{
    background: linear-gradient(180deg,#fffefe 0%,#faf4f8 100%);
    border:1px solid #e8c8ba;
    border-radius:18px;
    padding:0.85rem 0.95rem;
    color:#654857;
    font-size:0.88rem;
    line-height:1.65;
    margin:0.65rem 0 0.8rem 0;
    box-shadow:0 8px 22px rgba(41,22,35,0.04);
}}
.mini-explainer-card strong {{color:#221221;}}

.chart-conclusion {{
    margin-top:0.7rem;
    background:linear-gradient(180deg,#fffefe 0%,#faf4f8 100%);
    border:1px solid #e8c8ba;
    border-radius:16px;
    padding:0.75rem 0.9rem;
    color:#654857;
    font-size:0.86rem;
    line-height:1.6;
}}
.chart-conclusion strong {{color:#221221;}}

.result-hero-card {{
    background:linear-gradient(180deg,#ffffff 0%,#fcf7f3 100%);
    border:1px solid #e3b5a4;
    border-radius:24px;
    padding:1.05rem 1.1rem;
    box-shadow:0 12px 28px rgba(25,14,36,0.06);
    display:flex;
    justify-content:space-between;
    gap:1rem;
    align-items:flex-start;
    flex-wrap:wrap;
    margin:0.95rem 0 0.8rem 0;
}}
.result-hero-kicker {{color:#8b6771;font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:0.09em;margin-bottom:0.2rem;}}
.result-hero-title {{font-family:'DM Serif Display',serif;color:#160029;font-size:1.8rem;line-height:1.05;margin-bottom:0.3rem;}}
.result-hero-copy {{color:#5d3945;font-size:0.96rem;line-height:1.65;max-width:760px;}}
.result-hero-badges {{display:flex;gap:0.5rem;flex-wrap:wrap;justify-content:flex-end;}}
.result-hero-badge {{padding:0.46rem 0.92rem;border-radius:999px;font-size:0.8rem;font-weight:800;white-space:nowrap;border:1px solid #e3b5a4;background:#fff;}}
.result-hero-badge.soft {{background:#f5e9e2;color:#773344;border-color:#e6d8e2;}}
.result-hero-badge.score {{background:#fff;}}
.compact-summary-card {{background:#fff;border:1px solid #e3b5a4;border-radius:18px;padding:0.92rem 0.95rem;box-shadow:0 8px 22px rgba(25,14,36,0.05);min-height:94px;}}
.compact-summary-label {{color:#8b6771;font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.3rem;}}
.compact-summary-value {{color:#160029;font-size:1.02rem;font-weight:800;line-height:1.45;}}
.fatwa-focus-card {{background:#fff;border-radius:22px;padding:1rem 1.05rem;border:1px solid #e3b5a4;box-shadow:0 8px 22px rgba(25,14,36,0.06);margin-top:0.85rem;height:100%;}}
.fatwa-focus-head {{display:flex;justify-content:space-between;gap:0.7rem;align-items:flex-start;flex-wrap:wrap;margin-bottom:0.45rem;}}
.fatwa-focus-title {{font-family:'DM Serif Display',serif;color:#160029;font-size:1.24rem;}}
.fatwa-focus-copy {{color:#8b6771;font-size:0.88rem;line-height:1.55;margin-top:0.18rem;}}
.fatwa-focus-chip {{padding:0.38rem 0.82rem;border-radius:999px;background:#f5e9e2;border:1px solid #e6d8e2;color:#773344;font-size:0.78rem;font-weight:800;}}
.fatwa-focus-pill-row {{display:flex;flex-wrap:wrap;gap:0.45rem;margin:0.75rem 0 0.85rem 0;}}
.fatwa-focus-pill {{padding:0.35rem 0.75rem;border-radius:999px;background:#f9f1ec;border:1px solid #e6d8e2;color:#773344;font-size:0.78rem;font-weight:700;}}
.fatwa-focus-text {{background:#f9f1ec;border:1px solid #e3b5a4;border-radius:18px;padding:1rem;color:#2a1421;font-size:0.96rem;line-height:1.85;white-space:pre-wrap;}}
.insight-side-card {{background:#fff;border-radius:22px;padding:1rem 1.05rem;border:1px solid #e3b5a4;box-shadow:0 8px 22px rgba(25,14,36,0.06);margin-top:0.85rem;height:100%;}}
.insight-side-title {{font-family:'DM Serif Display',serif;color:#160029;font-size:1.18rem;margin-bottom:0.35rem;}}
.insight-side-copy {{color:#5d3945;font-size:0.9rem;line-height:1.7;}}
.insight-mini-grid {{display:grid;grid-template-columns:1fr 1fr;gap:0.7rem;margin-top:0.95rem;}}
.insight-mini-card {{background:#f5e9e2;border:1px solid #e3b5a4;border-radius:16px;padding:0.8rem;}}
.insight-mini-label {{color:#8b6771;font-size:0.7rem;font-weight:800;text-transform:uppercase;letter-spacing:0.06em;}}
.insight-mini-value {{color:#160029;font-size:0.98rem;font-weight:800;margin-top:0.18rem;line-height:1.4;}}
.coverage-card {{margin-top:0.85rem;}}
@media (max-width: 900px) {{
  .result-hero-card {{padding:0.95rem;}}
  .result-hero-title {{font-size:1.55rem;}}
  .insight-mini-grid {{grid-template-columns:1fr;}}
}}

/* ── SIMPLIFIED SIMILARITY BREAKDOWN ────────────────── */
.sim-lite-shell {{
    background: linear-gradient(180deg,#ffffff 0%,#fbf4ef 100%);
    border:1px solid #e3b5a4;
    border-radius:24px;
    padding:1rem;
    box-shadow:0 12px 26px rgba(25,14,36,0.06);
}}
.sim-lite-head {{display:flex;justify-content:space-between;align-items:flex-start;gap:0.8rem;margin-bottom:0.85rem;}}
.sim-lite-kicker {{color:#8b6771;font-size:0.7rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.18rem;}}
.sim-lite-title {{font-family:'Inter Tight','Inter',sans-serif;font-size:1.12rem;font-weight:800;color:#221221;}}
.sim-lite-pill {{padding:0.38rem 0.8rem;border-radius:999px;border:1px solid #d44d5c;font-weight:800;font-size:0.84rem;}}
.sim-lite-hero {{display:flex;gap:0.9rem;align-items:center;background:#fff;border:1px solid #ead1c8;border-radius:20px;padding:0.9rem;}}
.sim-lite-ring {{width:96px;height:96px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;}}
.sim-lite-ring-inner {{width:70px;height:70px;border-radius:50%;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;}}
.sim-lite-ring-inner strong {{font-family:'DM Serif Display',serif;font-size:1.5rem;line-height:1;}}
.sim-lite-ring-inner span {{font-size:0.66rem;color:#8b6771;}}
.sim-lite-summary-title {{font-size:1.08rem;font-weight:800;color:#221221;margin-bottom:0.2rem;}}
.sim-lite-summary-copy {{font-size:0.84rem;color:#6d5a68;line-height:1.55;}}
.sim-lite-metric {{background:#fff;border:1px solid #ead1c8;border-radius:18px;padding:0.9rem;margin-top:0.8rem;}}
.sim-lite-metric-label {{color:#8b6771;font-size:0.7rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.28rem;}}
.sim-lite-metric-value {{font-size:1.8rem;font-weight:800;line-height:1;}}
.sim-lite-metric-note {{color:#8b6771;font-size:0.82rem;line-height:1.45;margin-top:0.32rem;}}
.sim-lite-bottom {{display:grid;gap:0.8rem;margin-top:0.8rem;}}
.sim-lite-note-card {{background:#fff;border:1px solid #ead1c8;border-radius:18px;padding:0.9rem;}}
.sim-lite-note-label {{color:#8b6771;font-size:0.7rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.24rem;}}
.sim-lite-note-title {{font-size:1rem;font-weight:800;color:#221221;}}
.sim-lite-note-copy {{color:#5d3945;font-size:0.86rem;line-height:1.6;}}

/* ── TOPIC PICKER ───────────────────────────────────── */
.topic-pick-shell {{
    background:linear-gradient(180deg,#fffefe 0%,#fbf3ef 100%);
    border:1px solid #e3b5a4;
    border-radius:24px;
    padding:1rem 1.05rem;
    margin:0.2rem 0 0.75rem 0;
    box-shadow:0 12px 24px rgba(41,22,35,0.05);
}}
.topic-pick-kicker {{color:#b01f55;font-size:0.72rem;font-weight:800;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;}}
.topic-pick-title {{font-family:'Inter Tight','Inter',sans-serif;font-size:1.08rem;font-weight:800;color:#221221;margin-bottom:0.25rem;}}
.topic-pick-copy {{color:#766772;font-size:0.9rem;line-height:1.65;}}
.topic-select-shell [data-baseweb="select"] > div {{
    background:linear-gradient(180deg,#fffefe 0%,#fbf4ef 100%) !important;
    border:1.5px solid #e3b5a4 !important;
    border-radius:18px !important;
    min-height:58px !important;
    box-shadow:0 8px 18px rgba(41,22,35,0.04) !important;
}}
@media (max-width: 900px) {{
    .sim-lite-hero {{flex-direction:column;align-items:flex-start;}}
}}

        

/* ===== BEST-EFFORT COMPACT / LOW-SCROLL MODE ===== */
html {{
    font-size: 13px !important;
}}
body {{
    line-height: 1.35 !important;
}}
[data-testid="stSidebar"] {{
    min-width: 252px !important;
    max-width: 252px !important;
    width: 252px !important;
}}
[data-testid="stSidebar"] > div:first-child {{
    padding: 0.45rem 0.45rem 0.55rem 0.45rem !important;
}}
.block-container {{
    padding-top: 0.15rem !important;
    padding-left: 0.45rem !important;
    padding-right: 0.45rem !important;
    padding-bottom: 0.35rem !important;
}}
.main .block-container {{
    max-width: calc(100vw - 270px) !important;
}}
[data-testid="stVerticalBlock"] {{
    gap: 0.45rem !important;
}}
.element-container,
.stMarkdown,
.stAlert {{
    margin-bottom: 0.25rem !important;
}}
.stTabs [data-baseweb="tab-list"] {{
    padding: 4px !important;
    gap: 2px !important;
    border-radius: 12px !important;
}}
.stTabs [data-baseweb="tab"] {{
    font-size: 0.66rem !important;
    padding: 0.38rem 0.78rem !important;
    min-height: 36px !important;
}}
.stButton > button,
.stDownloadButton > button {{
    font-size: 0.8rem !important;
    padding: 0.48rem 0.95rem !important;
    border-radius: 10px !important;
    min-height: 40px !important;
}}
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stTextInputRootElement"],
.stTextInput > div > div {{
    min-height: 46px !important;
    border-radius: 14px !important;
}}
.stTextInput input {{
    font-size: 0.86rem !important;
    padding: 0.38rem 0.55rem !important;
}}
.stTextArea > div > div {{
    border-radius: 18px !important;
    padding: 0.2rem !important;
}}
.stTextArea textarea {{
    font-size: 0.7rem !important;
    line-height: 1.5 !important;
    min-height: 140px !important;
    padding: 0.72rem 0.82rem 0.75rem 0.82rem !important;
}}
.card,
.soft-card,
.metric-card,
.result-card,
.points-card,
.chart-card,
.overview-chart-card,
.topic-card,
.fatwa-box,
.sidebar-section-card,
.sidebar-workspace-card {{
    border-radius: 16px !important;
}}
.metric-card,
.result-card,
.points-card,
.chart-card,
.overview-chart-card,
.topic-card,
.fatwa-box {{
    padding: 0.85rem !important;
}}
.metric-label,
.result-card-title,
.card-header,
.overview-chart-header {{
    font-size: 0.68rem !important;
}}
.metric-value,
.result-card-score,
.score-circle-inner {{
    font-size: 1.6rem !important;
}}
.section-title {{
    font-size: 1.12rem !important;
    margin: 1rem 0 0.6rem 0 !important;
    padding-bottom: 0.35rem !important;
}}
.section-subtitle {{
    font-size: 0.72rem !important;
    margin: 0.75rem 0 0.45rem 0 !important;
}}
.msg-box,
.small-note,
.info-label,
.info-value,
.result-card-text,
.sidebar-action-text,
.sidebar-workspace-subtitle,
.sidebar-subtitle,
.hero-image-subtitle {{
    font-size: 0.66rem !important;
}}
.sidebar-title {{
    font-size: 1.12rem !important;
}}
.sidebar-brand-card,
.sidebar-section-card,
.sidebar-workspace-card {{
    padding: 0.8rem !important;
}}
.sidebar-highlight-chip {{
    padding: 0.62rem 0.68rem !important;
}}
.sidebar-highlight-value {{
    font-size: 0.95rem !important;
}}
.hero-image-wrap {{
    max-height: 180px !important;
    border-radius: 22px !important;
}}
.hero-image-overlay {{
    padding: 1rem 1.25rem !important;
}}
.hero-image-title {{
    font-size: 1.52rem !important;
    margin-bottom: 0.38rem !important;
}}
.hero-image-subtitle {{
    max-width: 470px !important;
}}
.score-circle {{
    width: 108px !important;
    height: 108px !important;
}}
.score-circle::before {{
    width: 84px !important;
    height: 84px !important;
}}
.light-table thead th,
.light-table tbody td {{
    padding: 0.5rem 0.58rem !important;
    font-size: 0.74rem !important;
}}
@media (max-width: 1200px) {{
    html {{ font-size: 12.5px !important; }}
    [data-testid="stSidebar"] {{
        min-width: 236px !important;
        max-width: 236px !important;
        width: 236px !important;
    }}
    .main .block-container {{
        max-width: calc(100vw - 250px) !important;
    }}
}}
@media (max-width: 900px) {{
    html {{ font-size: 12px !important; }}
    .main .block-container {{
        max-width: 100vw !important;
    }}
}}


/* ===== FINAL COMPACT OVERRIDES ===== */
.main .block-container {{max-width: calc(100vw - 252px) !important;}}
[data-testid="stSidebar"] {{box-shadow: 10px 0 22px rgba(22,0,41,0.15) !important;}}
.hero-image-overlay {{padding: 0.75rem 0.9rem !important;}}
.hero-image-content {{max-width: 38% !important;}}
.hero-kicker {{padding: 0.24rem 0.55rem; font-size: 0.58rem !important; margin-bottom: 0.22rem;}}
.stButton > button,.stDownloadButton > button {{min-height: 34px !important; border-radius: 9px !important;}}
.stTextArea > div > div {{border-radius: 14px !important; padding: 0.16rem !important;}}
[data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stTextInputRootElement"],
.stTextInput > div > div {{min-height: 38px !important; border-radius: 13px !important;}}
.metric-card,.result-card,.points-card,.chart-card,.soft-card,.card,.fatwa-box,.overview-chart-card {{border-radius: 14px !important;}}
@media (max-width: 1400px) {{.main .block-container {{max-width: calc(100vw - 244px) !important;}}}}
@media (max-width: 1100px) {{
  html {{font-size: 10.5px !important;}}
  [data-testid="stSidebar"] {{min-width: 220px !important; max-width: 220px !important; width: 220px !important;}}
  .main .block-container {{max-width: calc(100vw - 226px) !important;}}
  .hero-image-content {{max-width: 46% !important;}}
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
        <div class="sidebar-legend-note">Colors represent alignment Strength. <br> Scores indicate how closely AI responses match fatwa references. </div>
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
                <span style="font-size:0.78rem;">2026 Universiti Teknologi MARA</span>
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
            gap: 0.08rem;
            margin: 0.1rem 0 0.85rem 0;
            padding: 0.5rem 0.6rem;
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
            font-size: 0.7rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            margin-bottom: 0.13rem;
        }
        .review-workspace-header h1 {
            margin: 0 0 0.2rem 0;
            color: #160029;
            font-family: 'Inter Tight', 'Inter', sans-serif;
            font-size: 1.1rem;
            line-height: 1.05;
            letter-spacing: -0.02em;
        }
        .review-workspace-header p {
            margin: 0;
            color: #5d5060;
            font-size: 0.7rem;
            line-height: 1.38;
            max-width: 720px;
        }
        .review-workspace-badges {
            display: flex;
            gap: 0.18rem;
            flex-wrap: wrap;
            justify-content: flex-end;
            flex: 0 0 auto;
        }
        .review-badge-card {
            min-width: 170px;
            background: linear-gradient(135deg, #162a63 0%, #4a1d62 55%, #7a1657 100%);
            border-radius: 16px;
            padding: 0.55rem 0.7rem;
            border: 1px solid rgba(253,3,99,0.14);
            box-shadow: 0 8px 18px rgba(20, 10, 33, 0.12);
        }
        .review-badge-card span {
            display: block;
            color: rgba(255,255,255,0.62);
            font-size: 0.65rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.1rem;
        }
        .review-badge-card strong {
            color: #ffffff;
            font-size: 0.74rem;
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

        /* ── UNIFIED RESULT CARD (TAB 1) ─────────────────── */
        .unified-result-card {{
            background: linear-gradient(135deg, #ffffff 0%, #fbf5f1 50%, #f5ebe4 100%);
            border: 1.5px solid #e3b5a4;
            border-radius: 24px;
            padding: 1.5rem 1.6rem;
            box-shadow: 0 12px 32px rgba(25, 14, 36, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.6);
            margin: 0.8rem 0 1.2rem 0;
            backdrop-filter: blur(4px);
        }}

        .unified-result-grid {{
            display: grid;
            grid-template-columns: 1fr 1.4fr 1fr;
            gap: 1.25rem;
            align-items: stretch;
            min-width: 0;
        }}

        .unified-result-section {{
            padding: 1rem 1.05rem;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(255, 248, 244, 0.82) 100%);
            border: 1.2px solid rgba(227, 181, 164, 0.68);
            border-radius: 18px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            min-width: 0;
            word-break: break-word;
            overflow-wrap: anywhere;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
        }}

        .recommendation-section {{
            background: linear-gradient(180deg, #fff8f4 0%, #fff1f1 100%);
            border-top: 4px solid #d44d5c;
        }}

        .reference-section {{
            background: linear-gradient(180deg, #fffdfb 0%, #faf3f7 100%);
            border-top: 4px solid #773344;
        }}

        .metrics-section {{
            background: linear-gradient(180deg, #fffdf8 0%, #f9f1ec 100%);
            border-top: 4px solid #d98c3f;
        }}

        .unified-result-section:hover {{
            border-color: rgba(212, 77, 92, 0.4);
            box-shadow: 0 8px 20px rgba(212, 77, 92, 0.1);
            transform: translateY(-2px);
        }}

        .unified-result-label {{
            font-size: 0.70rem;
            font-weight: 850;
            letter-spacing: 0.10em;
            text-transform: uppercase;
            color: #a3195b;
            margin-bottom: 0.16rem;
            opacity: 0.95;
        }}

        .unified-result-value {{
            font-family: 'DM Serif Display', serif;
            font-size: 1.32rem;
            color: #160029;
            font-weight: 700;
            margin-bottom: 0.18rem;
            line-height: 1.2;
            letter-spacing: -0.01em;
            overflow-wrap: anywhere;
        }}

        .unified-result-explanation {{
            font-size: 0.72rem;
            line-height: 1.45;
            color: #5d3945;
            background: linear-gradient(135deg, rgba(212, 77, 92, 0.12) 0%, rgba(212, 77, 92, 0.06) 100%);
            padding: 0.55rem 0.7rem;
            border-radius: 14px;
            border-left: 4px solid #d44d5c;
            position: relative;
        }}

        .unified-result-explanation::before {{
            content: '';
            position: absolute;
            top: -1px;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, rgba(212, 77, 92, 0.2), transparent);
            border-radius: 14px 14px 0 0;
        }}

        .unified-result-subtext {{
            font-size: 0.8rem;
            line-height: 1.58;
            color: #5d3945;
            margin-top: 0.35rem;
            overflow-wrap: anywhere;
            word-break: break-word;
            white-space: normal;
        }}

        .unified-result-subtext strong {{
            color: #160029;
            font-weight: 750;
        }}

        .metrics-pill-row {{
            display: flex;
            gap: 0.24rem;
            flex-wrap: wrap;
            margin-bottom: 0.13rem;
        }}

        .metrics-mini-pill {{
            background: linear-gradient(135deg, #ffffff 0%, #f9f1ec 100%);
            border: 1.2px solid #e3b5a4;
            border-radius: 16px;
            padding: 0.6rem 0.7rem;
            text-align: center;
            flex: 1;
            min-width: 70px;
            transition: all 0.2s ease;
            position: relative;
            box-shadow: 0 2px 8px rgba(25, 14, 36, 0.04);
        }}

        .metrics-mini-pill:hover {{
            border-color: #d44d5c;
            box-shadow: 0 4px 12px rgba(212, 77, 92, 0.12);
            transform: translateY(-1px);
        }}

        .metrics-mini-label {{
            font-size: 0.67rem;
            font-weight: 820;
            color: #a3195b;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            margin-bottom: 0.1rem;
        }}

        .metrics-mini-value {{
            font-family: 'DM Serif Display', serif;
            font-size: 0.73rem;
            font-weight: 700;
            color: #160029;
            line-height: 1.2;
        }}

        .metrics-overall {{
            font-size: 0.83rem;
            line-height: 1.42;
            color: #2e6b52;
            background: linear-gradient(135deg, #E6F7F1 0%, #f0fdf9 100%);
            padding: 0.75rem 0.95rem;
            border-radius: 12px;
            border-left: 4px solid #06A77D;
            font-weight: 550;
            position: relative;
        }}

        .metrics-overall strong {{
            color: #06A77D;
            font-weight: 750;
            font-size: 1.02em;
        }}

        .reference-section {{
            position: relative;
        }}

        .reference-section::after {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 80px;
            height: 80px;
            background: radial-gradient(circle, rgba(227, 181, 164, 0.1) 0%, transparent 70%);
            border-radius: 100%;
            pointer-events: none;
        }}

        .recommendation-section {{
            background: linear-gradient(135deg, rgba(212, 77, 92, 0.10) 0%, rgba(212, 77, 92, 0.05) 100%);
            border-color: rgba(212, 77, 92, 0.35);
            position: relative;
        }}

        .recommendation-section::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: linear-gradient(180deg, #d44d5c 0%, rgba(212, 77, 92, 0) 100%);
            border-radius: 18px 0 0 18px;
        }}

        @media (max-width: 1200px) {{
            .unified-result-grid {{
                grid-template-columns: 1fr;
                gap: 0.08rem;
            }}
        }}

        /* ── IMPROVED LIGHT TABLE ────────────────────────── */
        .light-table-wrap {{
            border-radius: 20px;
            overflow: hidden;
            border: 1.2px solid #e3b5a4;
            background: linear-gradient(180deg, #ffffff 0%, #faf7f4 100%);
            box-shadow: 0 8px 24px rgba(25, 14, 36, 0.06);
        }}

        .light-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .light-table thead {{
            background: linear-gradient(90deg, #f5e9e2 0%, #fbf5f1 50%, #f5ebe4 100%);
            border-bottom: 2px solid #e3b5a4;
        }}

        .light-table thead th {{
            padding: 0.5rem 0.6rem;
            text-align: left;
            font-size: 0.73rem;
            font-weight: 820;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            color: #a3195b;
            font-variant: small-caps;
            position: relative;
        }}

        .light-table thead th::first-letter {{
            font-variant: normal;
        }}

        .light-table tbody tr {{
            border-bottom: 1px solid rgba(227, 181, 164, 0.25);
            transition: all 0.2s ease;
            background: #ffffff;
        }}

        .light-table tbody tr:hover {{
            background: linear-gradient(90deg, rgba(227, 181, 164, 0.12) 0%, rgba(227, 181, 164, 0.06) 100%);
            box-shadow: inset 0 0 12px rgba(227, 181, 164, 0.1);
        }}

        .light-table tbody tr:nth-child(even) {{
            background: rgba(227, 181, 164, 0.02);
        }}

        .light-table tbody tr:nth-child(even):hover {{
            background: linear-gradient(90deg, rgba(227, 181, 164, 0.12) 0%, rgba(227, 181, 164, 0.06) 100%);
        }}

        .light-table tbody td {{
            padding: 0.95rem 1.1rem;
            font-size: 0.68rem;
            color: #5d3945;
            word-break: break-word;
            line-height: 1.5;
        }}

        .light-table tbody strong {{
            color: #160029;
            font-weight: 700;
        }}

        .light-table tbody tr:first-child td {{
            padding-top: 1rem;
        }}

        .light-table tbody tr:last-child td {{
            padding-bottom: 1rem;
        }}

        .pager-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.95rem 1.3rem;
            background: linear-gradient(90deg, #f9f1ec 0%, #fbf5f1 100%);
            border: 1.2px solid #e3b5a4;
            border-radius: 16px;
            margin-bottom: 0.08rem;
            font-size: 0.82rem;
            color: #5d3945;
            box-shadow: 0 4px 12px rgba(25, 14, 36, 0.04);
        }}

        .pager-note {{
            font-weight: 620;
            color: #773344;
        }}

        /* ── BATCH RESULTS IMPROVEMENTS ──────────────────── */
        .batch-results-shell {{
            background: linear-gradient(135deg, #ffffff 0%, #fbf5f1 50%, #f5ebe4 100%);
            border: 1.5px solid #e3b5a4;
            border-radius: 24px;
            padding: 0.9rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 12px 32px rgba(25, 14, 36, 0.08);
        }}

        .batch-results-title {{
            font-family: 'DM Serif Display', serif;
            font-size: 0.66rem;
            color: #160029;
            margin-bottom: 0.18rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}

        .batch-results-copy {{
            font-size: 0.66rem;
            color: #5d3945;
            line-height: 1.42;
        }}

        .metric-card {{
            background: linear-gradient(135deg, #ffffff 0%, #faf7f4 100%);
            border: 1.2px solid #e3b5a4;
            border-radius: 18px;
            padding: 1.2rem 1rem;
            text-align: center;
            box-shadow: 0 6px 16px rgba(25, 14, 36, 0.05);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}

        .metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #d44d5c 0%, #d44d5c 50%, transparent 100%);
        }}

        .metric-card:hover {{
            border-color: #d44d5c;
            box-shadow: 0 10px 28px rgba(212, 77, 92, 0.12);
            transform: translateY(-4px);
        }}

        .metric-label {{
            font-size: 0.66rem;
            font-weight: 820;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #a3195b;
            margin-bottom: 0.15rem;
        }}

        .metric-value {{
            font-family: 'DM Serif Display', serif;
            font-size: 1.35rem;
            color: #160029;
            font-weight: 700;
            line-height: 1.2;
        }}

        /* ── RESULT HERO CARD IMPROVEMENTS ──────────────── */
        .result-hero-card {{
            background: linear-gradient(135deg, #ffffff 0%, #fbf5f1 100%);
            border: 1.5px solid #e3b5a4;
            border-radius: 24px;
            padding: 1.5rem 1.6rem;
            margin-bottom: 1.4rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 2rem;
            box-shadow: 0 12px 32px rgba(25, 14, 36, 0.08);
        }}

        .result-hero-main {{
            flex: 1;
        }}

        .result-hero-kicker {{
            font-size: 0.66rem;
            font-weight: 820;
            letter-spacing: 0.10em;
            text-transform: uppercase;
            color: #a3195b;
            margin-bottom: 0.5rem;
        }}

        .result-hero-title {{
            font-family: 'DM Serif Display', serif;
            font-size: 1.19rem;
            color: #160029;
            margin-bottom: 0.13rem;
            font-weight: 700;
            line-height: 1.15;
            letter-spacing: -0.02em;
        }}

        .result-hero-copy {{
            font-size: 0.66rem;
            color: #5d3945;
            line-height: 1.42;
        }}

        .result-hero-badges {{
            display: flex;
            gap: 0.8rem;
            flex-wrap: wrap;
            justify-content: flex-end;
        }}

        .result-hero-badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.55rem 1rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 650;
            white-space: nowrap;
            transition: all 0.2s ease;
            border: 1.2px solid;
        }}

        .result-hero-badge.soft {{
            background: rgba(227, 181, 164, 0.15);
            border-color: rgba(227, 181, 164, 0.4);
            color: #773344;
        }}

        .result-hero-badge.soft:hover {{
            background: rgba(227, 181, 164, 0.25);
            box-shadow: 0 4px 12px rgba(227, 181, 164, 0.2);
        }}

        .result-hero-badge.score {{
            background: rgba(255, 255, 255, 0.6);
            font-weight: 700;
            backdrop-filter: blur(4px);
        }}

        /* ── SECTION SEPARATORS & DIVIDERS ──────────────── */
        .section-subtitle {{
            font-family: 'Inter Tight', 'Inter', sans-serif;
            font-size: 0.96rem;
            font-weight: 700;
            color: #160029;
            margin: 1.2rem 0 0.8rem 0;
            letter-spacing: -0.01em;
        }}

        .divider {{
            height: 1.5px;
            background: linear-gradient(90deg, rgba(212, 77, 92, 0.2), rgba(212, 77, 92, 0.05) 50%, rgba(212, 77, 92, 0.2));
            margin: 1.5rem 0;
            border-radius: 999px;
        }}

        /* ── INPUT & FILTER IMPROVEMENTS ────────────────── */
        .stTextInput input,
        .stSelectbox select {{
            background: linear-gradient(180deg, #ffffff 0%, #f9f1ec 100%) !important;
            border: 1.2px solid #e3b5a4 !important;
            border-radius: 14px !important;
            color: #160029 !important;
            font-size: 0.9rem !important;
            padding: 0.75rem 1rem !important;
            transition: all 0.2s ease !important;
        }}

        .stTextInput input:focus,
        .stSelectbox select:focus {{
            border-color: #d44d5c !important;
            box-shadow: 0 0 0 3px rgba(212, 77, 92, 0.1) !important;
        }}

        /* ── KEYWORD CHIPS & TAGS ────────────────────────── */
        .keyword-match {{
            display: inline-block;
            padding: 0.5rem 0.85rem;
            margin: 0.4rem 0.4rem 0.4rem 0;
            background: linear-gradient(135deg, #E6F7F1 0%, #f0fdf9 100%);
            border: 1.2px solid rgba(6, 168, 125, 0.3);
            border-radius: 999px;
            color: #2e6b52;
            font-size: 0.82rem;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 2px 6px rgba(6, 168, 125, 0.08);
        }}

        .keyword-match:hover {{
            background: linear-gradient(135deg, #d6f5f1 0%, #e0fdfb 100%);
            border-color: rgba(6, 168, 125, 0.6);
            box-shadow: 0 4px 12px rgba(6, 168, 125, 0.15);
            transform: translateY(-2px);
        }}

        .keyword-miss {{
            display: inline-block;
            padding: 0.5rem 0.85rem;
            margin: 0.4rem 0.4rem 0.4rem 0;
            background: linear-gradient(135deg, #FBEAEC 0%, #fdf0f3 100%);
            border: 1.2px solid rgba(212, 77, 92, 0.3);
            border-radius: 999px;
            color: #a31621;
            font-size: 0.82rem;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 2px 6px rgba(212, 77, 92, 0.08);
        }}

        .keyword-miss:hover {{
            background: linear-gradient(135deg, #fbdae3 0%, #fde6ed 100%);
            border-color: rgba(212, 77, 92, 0.6);
            box-shadow: 0 4px 12px rgba(212, 77, 92, 0.15);
            transform: translateY(-2px);
        }}

        /* ── BUTTON STYLING ─────────────────────────────── */
        .stButton > button {{
            background: linear-gradient(135deg, #d44d5c 0%, #b24758 100%);
            color: #ffffff !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: 700 !important;
            font-size: 0.9rem !important;
            letter-spacing: 0.05em !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 8px 16px rgba(212, 77, 92, 0.25) !important;
            text-transform: uppercase;
        }}

        .stButton > button:hover {{
            background: linear-gradient(135deg, #b24758 0%, #a23d4a 100%) !important;
            box-shadow: 0 12px 28px rgba(212, 77, 92, 0.35) !important;
            transform: translateY(-2px) !important;
        }}

        .stButton > button:active {{
            transform: translateY(0px) !important;
        }}

        /* ── DOWNLOAD BUTTON STYLING ────────────────────── */
        .stDownloadButton > button {{
            background: linear-gradient(135deg, #f5e9e2 0%, #fbf5f1 100%);
            color: #773344 !important;
            border: 1.5px solid #e3b5a4 !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
            transition: all 0.2s ease !important;
        }}

        .stDownloadButton > button:hover {{
            background: linear-gradient(135deg, #e3b5a4 0%, #f5e9e2 100%);
            border-color: #d44d5c !important;
            box-shadow: 0 6px 16px rgba(212, 77, 92, 0.15) !important;
        }}

        /* ── CARD CONTAINERS ────────────────────────────── */
        .points-card {{
            background: linear-gradient(135deg, #ffffff 0%, #faf7f4 100%);
            border: 1.2px solid #e3b5a4;
            border-radius: 20px;
            padding: 0.6rem 0.8rem;
            box-shadow: 0 8px 20px rgba(25, 14, 36, 0.05);
            transition: all 0.3s ease;
        }}

        .points-card:hover {{
            border-color: #d44d5c;
            box-shadow: 0 12px 32px rgba(212, 77, 92, 0.1);
        }}

        .points-card-header {{
            font-size: 0.82rem;
            font-weight: 820;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #a3195b;
            margin-bottom: 0.11rem;
        }}

        .keyword-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.15rem;
        }}

        /* ── RESPONSIVE IMPROVEMENTS ────────────────────── */
        @media (max-width: 768px) {{
            .result-hero-card {{
                flex-direction: column;
                align-items: flex-start;
                gap: 0.08rem;
            }}

            .result-hero-badges {{
                justify-content: flex-start;
                width: 100%;
            }}

            .metric-value {{
                font-size: 0.96rem;
            }}

            .unified-result-value {{
                font-size: 0.66rem;
            }}
        }}

        

/* ===== SCALE HANDLED BY BASE 8.5px FONT-SIZE ===== */

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