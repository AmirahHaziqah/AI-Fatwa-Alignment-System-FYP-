import base64
import html
import os
import textwrap
from typing import Optional
import time

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from streamlit.components.v1 import html as components_html

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

/* ── BASE FONT SIZE — optimized for 100% zoom ── */
html {{
    font-size: 14px !important;
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

/* ── ANIMATIONS ──────────────────────────────────────── */
@keyframes fadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(20px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

@keyframes slideInLeft {{
    from {{
        opacity: 0;
        transform: translateX(-30px);
    }}
    to {{
        opacity: 1;
        transform: translateX(0);
    }}
}}

@keyframes slideInRight {{
    from {{
        opacity: 0;
        transform: translateX(30px);
    }}
    to {{
        opacity: 1;
        transform: translateX(0);
    }}
}}

@keyframes pulse {{
    0% {{ transform: scale(1); }}
    50% {{ transform: scale(1.02); }}
    100% {{ transform: scale(1); }}
}}

@keyframes shimmer {{
    0% {{ background-position: -1000px 0; }}
    100% {{ background-position: 1000px 0; }}
}}

@keyframes glow {{
    0% {{ box-shadow: 0 0 5px rgba(212,77,92,0.3); }}
    50% {{ box-shadow: 0 0 20px rgba(212,77,92,0.6); }}
    100% {{ box-shadow: 0 0 5px rgba(212,77,92,0.3); }}
}}

@keyframes slideInDown {{
    from {{
        transform: translateY(-100%);
        opacity: 0;
    }}
    to {{
        transform: translateY(0);
        opacity: 1;
    }}
}}

@keyframes fadeOutUp {{
    from {{
        opacity: 1;
        transform: translateY(0);
    }}
    to {{
        opacity: 0;
        transform: translateY(-100%);
    }}
}}

.fade-in-up {{
    animation: fadeInUp 0.6s ease-out;
}}

.slide-in-left {{
    animation: slideInLeft 0.5s ease-out;
}}

.slide-in-right {{
    animation: slideInRight 0.5s ease-out;
}}

.pulse-on-hover:hover {{
    animation: pulse 0.3s ease;
}}

/* Gradient text for headers */
.gradient-text {{
    background: linear-gradient(135deg, #773344 0%, #D44D5C 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    display: inline-block;
}}

/* ── APP BACKGROUND ──────────────────────────────────── */
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(180deg, #f4f6f9 0%, #efe6ea 100%) !important;
    color: {COLORS["text_primary"]};
}}

.block-container {{
    padding-top: 0.5rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 1400px !important;
    width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
}}

[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stToolbar"] {{ right: 1rem; }}

/* ── CUSTOM SCROLLBAR ────────────────────────────────── */
::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}

::-webkit-scrollbar-track {{
    background: #f1f1f1;
    border-radius: 10px;
}}

::-webkit-scrollbar-thumb {{
    background: linear-gradient(135deg, #773344 0%, #D44D5C 100%);
    border-radius: 10px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: linear-gradient(135deg, #D44D5C 0%, #773344 100%);
}}

/* ── SIDEBAR ─────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    min-width: 260px !important;
    max-width: 260px !important;
    width: 260px !important;
    background: linear-gradient(180deg, #160029 0%, #773344 55%, #5f2840 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
    box-shadow: 16px 0 34px rgba(22,0,41,0.18) !important;
    animation: slideInLeft 0.5s ease-out;
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
    transition: all 0.3s ease;
}}
.sidebar-brand-card:hover {{
    transform: translateX(4px);
    border-left-width: 8px;
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
    animation: slideInRight 0.4s ease-out;
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
    transition: all 0.3s ease;
}}
.sidebar-workspace-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 16px 32px rgba(13, 24, 47, 0.25) !important;
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
    transition: all 0.2s ease;
}}
.sidebar-highlight-chip:hover {{
    transform: scale(1.02);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
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
    transition: all 0.3s ease;
}}
.sidebar-section-card:hover {{
    transform: translateX(4px);
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
    transition: width 0.6s ease;
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
    transition: all 0.25s ease;
}}
.sidebar-action-item:hover {{
    transform: translateX(6px);
    background: rgba(255,255,255,0.1) !important;
    border-color: rgba(212,77,92,0.4) !important;
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
    transition: all 0.2s ease;
}}
.sidebar-action-item:hover .sidebar-action-icon {{
    transform: scale(1.05);
    background: #d44d5c !important;
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
    transition: all 0.2s ease;
}}
.sidebar-mini-note:hover {{
    background: rgba(255,255,255,0.1) !important;
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
    transition: all 0.2s ease;
}}
.sidebar-topic-pill:hover {{
    transform: scale(1.05);
    background: rgba(212,77,92,0.3) !important;
    border-color: #d44d5c !important;
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
    transition: all 0.2s ease;
}}
.sidebar-legend-item:hover {{
    background: rgba(255,255,255,0.1);
    transform: translateX(4px);
}}

.sidebar-legend-dot {{
    width: 12px;
    height: 12px;
    border-radius: 999px;
    margin-top: 0.2rem;
    box-shadow: 0 0 0 3px rgba(255,255,255,0.08);
    transition: all 0.2s ease;
}}
.sidebar-legend-item:hover .sidebar-legend-dot {{
    transform: scale(1.2);
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
    transition: all 0.25s ease !important;
}}

.stTabs [data-baseweb="tab"]:hover {{
    background: rgba(212,77,92,0.1) !important;
    transform: translateY(-1px);
}}

.stTabs [aria-selected="true"] {{
    background: #cb4a5e !important;
    color: white !important;
    font-weight: 700 !important;
    box-shadow: 0 6px 18px rgba(119,51,68,0.20) !important;
    animation: pulse 0.3s ease;
}}

.stTabs [data-baseweb="tab-panel"] {{
    padding-top: 1.5rem;
    animation: fadeInUp 0.4s ease-out;
}}

/* ── HERO BANNER (MAIN CONTENT) ──────────────────────── */
.hero-image-wrap {{
    position: relative;
    height: 130px !important;
    border-radius: 20px !important;
    overflow: hidden;
    margin-bottom: 0.8rem;
    border: 1px solid rgba(158,179,194,0.20);
    box-shadow: 0 12px 28px rgba(22, 0, 41, 0.12);
    background: linear-gradient(90deg, #0b2a56 0%, #4c224d 55%, #65104d 100%);
    animation: fadeInUp 0.6s ease-out;
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
    transition: transform 0.5s ease;
}}
.hero-image-wrap:hover .hero-single-image {{
    transform: scale(1.05);
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
    padding: 1.5rem 2rem;
}}

.hero-image-content {{
    width: 100%;
    max-width: 70% !important;
}}

.hero-kicker {{
    display: inline-flex;
    align-items: center;
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.20);
    color: #ffffff;
    font-size: 0.65rem !important;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
    backdrop-filter: blur(4px);
    transition: all 0.2s ease;
}}
.hero-kicker:hover {{
    background: rgba(212,77,92,0.3);
    transform: scale(1.02);
}}

.hero-image-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.3rem !important;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.03em;
    color: #ffffff !important;
    margin: 0 0 0.4rem 0;
    text-shadow: 0 4px 12px rgba(0,0,0,0.20) !important;
}}

.hero-image-subtitle {{
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem !important;
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
    min-height: 80px;
    border-radius: 20px;
    overflow: hidden;
    margin: 1rem 0 1rem 0;
    border: 1px solid #e3b5a4;
    box-shadow: 0 8px 20px rgba(59, 29, 74, 0.06);
    background: linear-gradient(135deg, #160029, #773344);
    transition: all 0.3s ease;
}}
.section-banner:hover {{
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(59, 29, 74, 0.12);
}}

.section-banner-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.2rem;
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
    padding: 1rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 8px 20px rgba(22, 32, 51, 0.06) !important;
    color: #2a1421;
    transition: all 0.3s ease;
}}

.card {{
    transition: all 0.3s ease;
    height: 100%;
    animation: fadeInUp 0.5s ease-out;
}}
.card:hover {{
    transform: translateY(-4px) !important;
    box-shadow: 0 16px 32px rgba(22, 32, 51, 0.12) !important;
    border-color: #d44d5c !important;
}}

.card-header {{
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #f5e9e2;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}}

/* ── METRIC CARDS ────────────────────────────────────── */
.metric-card {{
    background: #FFFFFF;
    border-radius: 16px !important;
    padding: 0.7rem 0.8rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 8px 20px rgba(22, 32, 51, 0.06) !important;
    text-align: center;
    height: 100%;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}}
.metric-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(22, 32, 51, 0.1) !important;
}}

.metric-card::before {{
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #d44d5c 0%, #773344 100%) !important;
    transition: height 0.2s ease;
}}
.metric-card:hover::before {{
    height: 5px;
}}

.metric-card-good::before {{ background: #06A77D !important; }}
.metric-card-mid::before  {{ background: #F1A208 !important; }}
.metric-card-low::before  {{ background: #A31621 !important; }}

.metric-label {{
    font-size: 0.7rem;
    font-weight: 700;
    color: #8b6771;
    margin-bottom: 0.4rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}

.metric-value {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #773344;
    line-height: 1.1;
    transition: all 0.2s ease;
}}
.metric-card:hover .metric-value {{
    transform: scale(1.02);
}}

.metric-value-good {{ color: #06A77D !important; }}
.metric-value-mid  {{ color: #C27D06 !important; }}
.metric-value-low  {{ color: #A31621 !important; }}

/* ── SECTION TITLES ──────────────────────────────────── */
.section-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: #773344;
    margin: 1.5rem 0 0.8rem 0;
    position: relative;
    display: inline-block;
    padding-bottom: 0.5rem;
    letter-spacing: -0.01em;
}}

.section-title::after {{
    content: '';
    position: absolute;
    left: 0; bottom: 0;
    width: 48px; height: 3px;
    background: linear-gradient(90deg, #d44d5c 0%, #773344 100%);
    border-radius: 2px;
    transition: width 0.3s ease;
}}
.section-title:hover::after {{
    width: 100%;
}}

.section-subtitle {{
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: #160029;
    margin: 1rem 0 0.7rem 0;
    letter-spacing: -0.01em;
}}

/* ── MESSAGE BOXES ───────────────────────────────────── */
.msg-box {{
    padding: 0.7rem 0.9rem;
    border-radius: 14px !important;
    margin: 0.8rem 0;
    background: #FFFFFF;
    border: 1px solid #e3b5a4;
    border-left: 5px solid #773344;
    box-shadow: 0 2px 6px rgba(15,32,68,0.05);
    color: #2a1421;
    line-height: 1.5;
    font-size: 0.85rem;
    transition: all 0.2s ease;
}}
.msg-box:hover {{
    transform: translateX(4px);
    box-shadow: 0 4px 10px rgba(15,32,68,0.08);
}}

.msg-box strong {{ color: #160029; }}
.msg-success {{ border-left-color: #06A77D !important; background: #f6fbf8 !important; }}
.msg-info    {{ border-left-color: #773344 !important; background: #faf4f8 !important; }}
.msg-warning {{ border-left-color: #F1A208 !important; background: #fff8ef !important; }}

/* ── KEYWORD CHIPS ───────────────────────────────────── */
.keyword-container {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.6rem;
}}

.keyword-match, .keyword-miss {{
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
    transition: all 0.2s ease;
}}
.keyword-match:hover, .keyword-miss:hover {{
    transform: scale(1.05);
}}

.keyword-match {{
    background: rgba(25,135,84,0.10) !important;
    color: #198754 !important;
    border: 1px solid rgba(25,135,84,0.18) !important;
}}
.keyword-match:hover {{
    background: rgba(25,135,84,0.2) !important;
    box-shadow: 0 2px 6px rgba(25,135,84,0.2);
}}

.keyword-miss {{
    background: rgba(180,35,79,0.08) !important;
    color: #b4234f !important;
    border: 1px solid rgba(180,35,79,0.18) !important;
}}
.keyword-miss:hover {{
    background: rgba(180,35,79,0.15) !important;
    box-shadow: 0 2px 6px rgba(180,35,79,0.15);
}}

/* ── FATWA BOX ───────────────────────────────────────── */
.fatwa-box {{
    background: #FFFFFF;
    border-radius: 16px !important;
    padding: 0.9rem 1rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 8px 20px rgba(22, 32, 51, 0.06) !important;
    color: #2a1421;
    margin-bottom: 0.7rem;
    transition: all 0.3s ease;
}}
.fatwa-box:hover {{
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(22, 32, 51, 0.1) !important;
    border-color: #d44d5c !important;
}}

.fatwa-meta-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-bottom: 0.5rem;
}}

.fatwa-meta-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.25rem 0.6rem;
    border-radius: 8px;
    background: #f5e9e2;
    border: 1px solid #e3b5a4;
    color: #5f2840;
    font-size: 0.7rem;
    font-weight: 600;
    transition: all 0.2s ease;
}}
.fatwa-meta-pill:hover {{
    background: #e3b5a4;
    transform: translateY(-1px);
}}

.fatwa-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.5rem;
    line-height: 1.3;
    word-break: break-word;
}}

.fatwa-text-panel {{
    background: linear-gradient(180deg, #ffffff 0%, #f9f1ec 100%);
    border: 1px solid #e3b5a4;
    border-radius: 12px;
    padding: 0.7rem 0.9rem;
    transition: all 0.2s ease;
}}
.fatwa-box:hover .fatwa-text-panel {{
    background: linear-gradient(180deg, #ffffff 0%, #fff5f0 100%);
}}

.fatwa-text-panel p {{
    margin: 0;
    color: #160029;
    line-height: 1.6;
    font-size: 0.85rem;
    white-space: pre-wrap;
    word-break: break-word;
}}

/* ── BADGES ──────────────────────────────────────────── */
.badge {{
    display: inline-block;
    padding: 0.25rem 0.7rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    transition: all 0.2s ease;
}}
.badge:hover {{
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}}

.badge-good {{ background: rgba(25,135,84,0.12) !important; color: #198754 !important; border: 1px solid rgba(25,135,84,0.26) !important; }}
.badge-mid  {{ background: rgba(194,125,6,0.12) !important; color: #9A6A18 !important; border: 1px solid rgba(194,125,6,0.24) !important; }}
.badge-low  {{ background: rgba(180,35,79,0.10) !important; color: #b4234f !important; border: 1px solid rgba(180,35,79,0.20) !important; }}

/* ── SCORE CIRCLE ────────────────────────────────────── */
.score-circle {{
    width: 110px; height: 110px;
    border-radius: 50%;
    margin: 0 auto;
    display: flex; align-items: center; justify-content: center;
    position: relative;
    box-shadow: 0 4px 16px rgba(15,32,68,0.14);
    transition: all 0.3s ease;
    animation: fadeInUp 0.5s ease-out;
}}
.score-circle:hover {{
    transform: scale(1.02);
    box-shadow: 0 8px 24px rgba(212,77,92,0.3);
    animation: glow 1.5s infinite;
}}

.score-circle::before {{
    content: '';
    position: absolute;
    width: 85px; height: 85px;
    border-radius: 50%;
    background: #FFFFFF;
}}

.score-circle-inner {{
    position: relative;
    z-index: 2;
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: #773344;
}}
.score-circle-good .score-circle-inner {{ color: #198754; }}
.score-circle-mid .score-circle-inner {{ color: #c27d06; }}
.score-circle-low .score-circle-inner {{ color: #b4234f; }}

/* ── INFO GRID ───────────────────────────────────────── */
.info-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 0.7rem;
}}

.info-item {{
    background: #EEF4F8;
    padding: 0.8rem;
    border-radius: 10px;
    border: 1px solid #e3b5a4;
    transition: all 0.2s ease;
}}
.info-item:hover {{
    transform: translateY(-2px);
    background: #e8f0f5;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}}

.info-label {{
    font-size: 0.7rem;
    font-weight: 700;
    color: #8b6771;
    margin-bottom: 0.2rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.info-value {{
    font-size: 0.9rem;
    font-weight: 600;
    color: #2a1421;
    word-break: break-word;
    white-space: normal;
    line-height: 1.4;
}}

/* ── DIVIDER ─────────────────────────────────────────── */
.divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, #e3b5a4, transparent);
    margin: 1.5rem 0;
    opacity: 0.8;
}}

/* ── RESULT CARDS ────────────────────────────────────── */
.result-card {{
    background: #FFFFFF;
    border-radius: 16px !important;
    padding: 0.8rem 1rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 8px 20px rgba(22, 32, 51, 0.06) !important;
    text-align: center;
    height: 100%;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}}
.result-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(22, 32, 51, 0.12) !important;
}}

.result-card::before {{
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #d44d5c 0%, #773344 100%) !important;
    transition: height 0.2s ease;
}}
.result-card:hover::before {{
    height: 5px;
}}

.result-card-good::before  {{ background: #06A77D !important; }}
.result-card-mid::before   {{ background: #F1A208 !important; }}
.result-card-low::before   {{ background: #A31621 !important; }}

.result-card-title {{
    color: #8b6771;
    font-weight: 700;
    font-size: 0.75rem;
    margin-bottom: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.result-card-score {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    margin: 0.3rem 0 0.4rem 0;
    transition: all 0.2s ease;
}}
.result-card:hover .result-card-score {{
    transform: scale(1.02);
}}

.result-card-score-good {{ color: #06A77D; }}
.result-card-score-mid  {{ color: #C27D06; }}
.result-card-score-low  {{ color: #A31621; }}

.result-card-text {{
    color: #5d3945;
    font-size: 0.8rem;
    line-height: 1.5;
}}

/* ── POINTS CARD ─────────────────────────────────────── */
.points-card {{
    background: #FFFFFF;
    border-radius: 16px !important;
    padding: 0.8rem 1rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 8px 20px rgba(22, 32, 51, 0.06) !important;
    height: 100%;
    transition: all 0.3s ease;
}}
.points-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(22, 32, 51, 0.1) !important;
}}

.points-card-header {{
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.4rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #e3b5a4;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

/* ── SMALL NOTE ──────────────────────────────────────── */
.small-note {{
    color: #8b6771;
    font-size: 0.8rem;
    line-height: 1.5;
}}

/* ── CHART CARD ──────────────────────────────────────── */
.chart-card {{
    background: #FFFFFF;
    border-radius: 16px !important;
    padding: 1rem 1rem 0.6rem 1rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 8px 20px rgba(22, 32, 51, 0.06) !important;
    margin-bottom: 0.7rem;
    transition: all 0.3s ease;
}}
.chart-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(22, 32, 51, 0.1) !important;
}}

/* ── BUTTONS ─────────────────────────────────────────── */
.stButton > button,
.stDownloadButton > button {{
    background: linear-gradient(135deg, #cb4a5e 0%, #d44d5c 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.35rem 0.8rem !important;
    font-size: 0.8rem !important;
    box-shadow: 0 8px 16px rgba(119,51,68,0.18) !important;
    transition: all 0.3s ease !important;
    letter-spacing: 0.01em !important;
    min-height: 36px !important;
}}

.stButton > button:hover,
.stDownloadButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 22px rgba(119,51,68,0.28) !important;
    background: linear-gradient(135deg, #d44d5c 0%, #e05568 100%) !important;
    color: white !important;
}}

.stButton > button:active,
.stDownloadButton > button:active {{
    transform: translateY(0px) !important;
    box-shadow: 0 4px 10px rgba(119,51,68,0.2) !important;
}}

/* ── INPUT LABELS ────────────────────────────────────── */
[data-testid="stTextArea"] label,
[data-testid="stTextInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label,
[data-testid="stRadio"] label:first-of-type {{
    color: #160029 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    margin-bottom: 0.3rem !important;
}}

/* ── RADIO / SEGMENTED INPUTS ────────────────────────── */
[data-testid="stRadio"] > div {{color:#2a1421 !important;}}
[data-testid="stRadio"] label {{color:#2a1421 !important; font-weight:600 !important; opacity:1 !important;}}
[data-testid="stRadio"] [role="radiogroup"] {{
    background: linear-gradient(180deg,#fffdfc 0%,#fbf3ee 100%) !important;
    border: 1px solid #e3b5a4 !important;
    border-radius: 20px !important;
    padding: 0.3rem !important;
    gap: 0.4rem !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.55);
}}
[data-testid="stRadio"] [role="radiogroup"] > label {{
    flex: 1 1 0 !important;
    justify-content: center !important;
    text-align: center !important;
    min-height: 36px !important;
    border-radius: 14px !important;
    padding: 0.3rem 0.6rem !important;
    transition: all 0.25s ease !important;
    border: 1px solid transparent !important;
}}
[data-testid="stRadio"] [role="radiogroup"] > label:hover {{
    background:#faf4f8 !important;
    transform: translateY(-1px);
}}
[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) {{
    background: linear-gradient(180deg,#d44d5c 0%,#cb4a5e 100%) !important;
    border-color: #cb4a5e !important;
    box-shadow: 0 6px 14px rgba(119,51,68,0.18) !important;
    transform: scale(1.02);
}}
[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) p {{color:#ffffff !important;}}
[data-testid="stRadio"] [role="radiogroup"] input {{display:none !important;}}
[data-testid="stRadio"] [role="radiogroup"] p {{color:#5d3945 !important;font-weight:700 !important;font-size:0.8rem !important;opacity:1 !important;}}

/* ── INPUT SURFACES ──────────────────────────────────── */
[data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stTextInputRootElement"],
.stTextInput > div > div {{
    background: #ffffff !important;
    border: 1.5px solid #e3b5a4 !important;
    border-radius: 16px !important;
    min-height: 44px !important;
    box-shadow: 0 6px 14px rgba(44, 21, 33, 0.06) !important;
    transition: all 0.25s ease !important;
}}
[data-testid="stMultiSelect"] [data-baseweb="select"] > div:hover,
[data-testid="stSelectbox"] [data-baseweb="select"] > div:hover,
[data-testid="stTextInputRootElement"]:hover,
.stTextInput > div > div:hover {{
    border-color: #d44d5c !important;
    transform: translateY(-1px);
}}

[data-testid="stMultiSelect"] [data-baseweb="select"] > div:focus-within,
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
[data-testid="stTextInputRootElement"]:focus-within,
.stTextInput > div > div:focus-within {{
    border-color: #b24758 !important;
    box-shadow: 0 0 0 3px rgba(212,77,92,0.12), 0 8px 20px rgba(44,21,33,0.08) !important;
}}

[data-testid="stMultiSelect"] [data-baseweb="tag"] {{
    background: linear-gradient(135deg, #f7c7cf 0%, #ef9cac 100%) !important;
    color:#4a2030 !important;
    border-radius:999px !important;
    border:1px solid rgba(178,71,88,0.18) !important;
    transition: all 0.2s ease;
}}
[data-testid="stMultiSelect"] [data-baseweb="tag"]:hover {{
    transform: scale(1.02);
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
    background: #ffffff !important;
    border: 1.5px solid #e3b5a4 !important;
    border-radius: 16px !important;
    box-shadow: 0 6px 14px rgba(44,21,33,0.06) !important;
    padding: 0.2rem !important;
    transition: all 0.25s ease !important;
}}
.stTextArea > div > div:hover {{
    border-color: #d44d5c !important;
    transform: translateY(-1px);
}}

.stTextArea > div > div:focus-within {{
    border-color: #b24758 !important;
    box-shadow: 0 0 0 3px rgba(212,77,92,0.12), 0 8px 20px rgba(44,21,33,0.08) !important;
}}

.stTextArea textarea {{
    background: transparent !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.6rem 0.8rem !important;
    color: #2a1421 !important;
    font-size: 0.85rem !important;
    font-family: 'Inter', sans-serif !important;
    line-height: 1.5 !important;
    box-shadow: none !important;
    min-height: 120px !important;
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
    font-size: 0.85rem !important;
}}

/* ── TEXT INPUT ──────────────────────────────────────── */
.stTextInput input {{
    background: transparent !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.4rem 0.6rem !important;
    color: #2a1421 !important;
    font-size: 0.85rem !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: none !important;
}}

/* ── SELECTBOX / MULTISELECT ─────────────────────────── */
[data-testid="stSelectbox"] > div > div,
.stSelectbox [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] > div > div {{
    background: transparent !important;
    border: none !important;
    border-radius: 14px !important;
    color: #2a1421 !important;
    font-size: 0.85rem !important;
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
    box-shadow: 0 8px 18px rgba(39,34,51,0.06);
    background: #FFFFFF;
    transition: all 0.2s ease;
}}
.light-table-wrap:hover {{
    box-shadow: 0 12px 24px rgba(39,34,51,0.1);
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
    font-size: 0.7rem;
    padding: 0.6rem 0.8rem;
    text-align: left;
    white-space: nowrap;
    letter-spacing: 0.03em;
    border-bottom: 1px solid rgba(0,0,0,0.05);
}}

.light-table thead th:first-child {{ border-radius: 16px 0 0 0; }}
.light-table thead th:last-child  {{ border-radius: 0 16px 0 0; }}

.light-table tbody td {{
    background: #FFFFFF;
    color: #2a1421;
    font-size: 0.75rem;
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid #e3b5a4;
    vertical-align: middle;
    line-height: 1.5;
    transition: all 0.2s ease;
}}

.light-table tbody tr:nth-child(even) td {{ background: #FCF8F5; }}
.light-table tbody tr:hover td {{
    background: #F8EFE8;
    transform: translateX(2px);
}}
.light-table tbody tr:last-child td {{ border-bottom: none; }}

/* ── OVERVIEW CHART CARD ─────────────────────────────── */
.overview-chart-card {{
    background: #FFFFFF;
    border-radius: 16px !important;
    padding: 0.6rem 0.9rem 0.9rem 1.1rem;
    border: 1px solid #D2DCE5 !important;
    box-shadow: 0 8px 20px rgba(22, 32, 51, 0.06) !important;
    margin-bottom: 0.7rem;
    transition: all 0.3s ease;
}}
.overview-chart-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(22, 32, 51, 0.1) !important;
}}

/* ── TOPIC CARDS ─────────────────────────────────────── */
.topic-card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.7rem;
}}

.topic-card {{
    background: #FFFFFF;
    border: 1px solid #e3b5a4;
    border-top: 4px solid #b24758;
    border-radius: 16px;
    padding: 0.9rem;
    box-shadow: 0 6px 14px rgba(39,34,51,0.06);
    transition: all 0.3s ease;
}}
.topic-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 12px 22px rgba(39,34,51,0.1);
    border-top-width: 5px;
}}

.topic-card-title {{
    font-size: 0.9rem;
    font-weight: 800;
    color: #2a1421;
    line-height: 1.4;
    margin-bottom: 0.3rem;
}}

.topic-card-pill {{
    display: inline-flex;
    align-items: center;
    padding: 0.3rem 0.7rem;
    border-radius: 999px;
    background: #f5e9e2;
    color: #160029;
    border: 1px solid #e3b5a4;
    font-size: 0.75rem;
    font-weight: 800;
    transition: all 0.2s ease;
}}
.topic-card:hover .topic-card-pill {{
    background: #e3b5a4;
}}

.topic-card-count {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 0.9rem;
    color: #773344;
}}

/* ── PAGER BAR ───────────────────────────────────────── */
.pager-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.4rem;
    flex-wrap: wrap;
    background: #FFFFFF;
    border: 1px solid #e3b5a4;
    border-left: 4px solid #b24758;
    border-radius: 12px;
    padding: 0.5rem 0.8rem;
    margin-bottom: 0.4rem;
    transition: all 0.2s ease;
}}
.pager-bar:hover {{
    border-left-width: 6px;
}}

.pager-note {{
    color: #8b6771;
    font-size: 0.8rem;
    line-height: 1.4;
}}

.pager-chip {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 80px;
    padding: 0.35rem 0.7rem;
    border-radius: 999px;
    background: #f5e9e2;
    color: #160029;
    border: 1px solid #e3b5a4;
    font-size: 0.75rem;
    font-weight: 700;
    transition: all 0.2s ease;
}}
.pager-chip:hover {{
    background: #e3b5a4;
    transform: scale(1.02);
}}

/* ── COMPARISON CARD ─────────────────────────────────── */
.comparison-card {{
    background: #FFFFFF;
    border-radius: 14px;
    padding: 0.9rem;
    border: 1px solid #e3b5a4;
    box-shadow: 0 2px 8px rgba(15,32,68,0.05);
    margin-bottom: 0.7rem;
    height: 100%;
    transition: all 0.3s ease;
}}
.comparison-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(15,32,68,0.08);
}}

.comparison-card-header {{
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.4rem;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid #f5e9e2;
    line-height: 1.3;
    word-break: break-word;
}}

/* ── ALIGNMENT RANKING ───────────────────────────────── */
.align-panel-title {{
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    font-weight: 700;
    color: #8b6771;
    margin-bottom: 0.4rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}

.align-rank-card {{
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #e3b5a4;
    box-shadow: 0 2px 6px rgba(15,32,68,0.04);
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.5rem;
    transition: all 0.25s ease;
}}
.align-rank-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 5px 12px rgba(15,32,68,0.07);
    border-color: #d44d5c;
}}

.align-rank-topic {{
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.3rem;
    line-height: 1.4;
    word-break: break-word;
}}

.align-rank-row {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.4rem;
    flex-wrap: wrap;
}}

.align-score {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    line-height: 1;
}}

.align-band {{
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}}

.align-n {{
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    color: #8b6771;
    margin-left: auto;
}}

.align-bar-bg {{
    background: #f5e9e2;
    border-radius: 99px;
    height: 6px;
    width: 100%;
    overflow: hidden;
}}

.align-bar-fill {{
    height: 100%;
    border-radius: 99px;
    transition: width 0.5s ease;
}}

.align-full-row {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0;
    border-bottom: 1px solid #e3b5a4;
    flex-wrap: nowrap;
    transition: all 0.2s ease;
}}
.align-full-row:hover {{
    background: #fcf8f5;
    transform: translateX(3px);
}}

.align-full-rank {{
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    min-width: 1.8rem;
    color: #8b6771;
}}

.align-full-topic {{
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: #2a1421;
    min-width: 140px;
    word-break: break-word;
    white-space: normal;
    line-height: 1.4;
}}

.align-full-score {{
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    min-width: 3rem;
    text-align: right;
}}

.align-full-n {{
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    color: #8b6771;
    min-width: 2.2rem;
}}

/* ── DONUT INSIGHT CARDS ─────────────────────────────── */
.donut-insight-card {{
    display: flex;
    align-items: stretch;
    gap: 0;
    background: #FFFFFF;
    border-radius: 10px;
    border: 1px solid #e3b5a4;
    box-shadow: 0 2px 6px rgba(15,32,68,0.04);
    margin-bottom: 0.5rem;
    overflow: hidden;
    transition: all 0.2s ease;
}}
.donut-insight-card:hover {{
    transform: translateX(3px);
    box-shadow: 0 4px 10px rgba(15,32,68,0.08);
}}

.donut-insight-accent {{
    width: 4px;
    min-height: 100%;
    flex-shrink: 0;
    border-radius: 0;
    transition: width 0.2s ease;
}}
.donut-insight-card:hover .donut-insight-accent {{
    width: 6px;
}}

.donut-insight-body {{
    padding: 0.6rem 0.9rem;
    flex: 1;
}}

.donut-insight-name {{
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: #160029;
    margin-bottom: 0.2rem;
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
    font-size: 1.2rem;
    font-weight: 700;
    color: #773344;
    line-height: 1;
}}

.donut-insight-pct {{
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    font-weight: 400;
    color: #8b6771;
}}

/* ── BATCH RESULT HELPERS ───────────────────────────── */
.batch-results-shell {{
    background: linear-gradient(180deg, #ffffff 0%, #f9f1ec 100%);
    border: 1px solid #e3b5a4;
    border-radius: 20px;
    padding: 0.9rem 1rem;
    box-shadow: 0 8px 18px rgba(44, 21, 33, 0.05);
    margin: 0.8rem 0 0.8rem 0;
    transition: all 0.3s ease;
}}
.batch-results-shell:hover {{
    box-shadow: 0 12px 24px rgba(44, 21, 33, 0.08);
}}

.batch-results-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #251329;
    margin-bottom: 0.2rem;
}}

.batch-results-copy,
.batch-readable-note,
.result-reading-guide-copy {{
    color: #6b5660;
    font-size: 0.8rem;
    line-height: 1.5;
}}

.batch-readable-note,
.result-reading-guide {{
    background: linear-gradient(180deg, #fffefe 0%, #f8efea 100%);
    border: 1px solid #e3b5a4;
    border-left: 4px solid #d44d5c;
    border-radius: 16px;
    padding: 0.7rem 0.9rem;
    margin: 0.8rem 0;
    box-shadow: 0 6px 14px rgba(44, 21, 33, 0.04);
    transition: all 0.2s ease;
}}
.batch-readable-note:hover,
.result-reading-guide:hover {{
    transform: translateX(3px);
    border-left-width: 5px;
}}

.result-reading-guide-title {{
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #a3195b;
    margin-bottom: 0.2rem;
}}

/* ── FOOTER ──────────────────────────────────────────── */
.footer-wrap {{
    text-align: center;
    margin-top: 2rem;
    padding: 1.2rem 1.5rem;
    border-top: 1px solid #e3b5a4;
    animation: fadeInUp 0.6s ease-out;
}}

.footer-wrap p {{
    color: #8b6771;
    font-size: 0.8rem;
    font-family: 'Inter', sans-serif;
    line-height: 1.5;
    margin: 0;
}}

/* ── TAB MINIMAL HERO ───────────────────────────────── */
.tab-minimal-hero {{
    background: linear-gradient(180deg,#fffdfc 0%,#fbf4ef 100%);
    border: 1px solid #e3b5a4;
    border-radius: 24px;
    padding: 0.9rem 1.1rem 0.8rem 1.1rem;
    box-shadow: 0 10px 22px rgba(41,22,35,0.04);
    margin: 0.1rem 0 0.8rem 0;
    transition: all 0.3s ease;
}}
.tab-minimal-hero:hover {{
    box-shadow: 0 14px 28px rgba(41,22,35,0.07);
}}

.tab-minimal-kicker {{
    color:#b01f55;
    font-size:0.65rem;
    font-weight:800;
    letter-spacing:0.14em;
    text-transform:uppercase;
    margin-bottom: 0.3rem;
}}

.tab-minimal-title {{
    font-family:'Inter Tight','Inter',sans-serif;
    font-size: 1.2rem;
    font-weight:800;
    color:#221221;
    line-height:1.1;
}}

.tab-minimal-copy {{
    color:#766772;
    font-size:0.8rem;
    line-height:1.6;
    margin-top: 0.4rem;
    max-width: 800px;
}}

/* ── WORKSPACE SHELL ────────────────────────────────── */
.workspace-shell {{
    background: linear-gradient(180deg,#ffffff 0%,#fbf5f1 100%);
    border: 1px solid #e3b5a4;
    border-radius: 20px;
    padding: 0.9rem 1rem;
    box-shadow: 0 8px 18px rgba(25,14,36,0.05);
    margin-bottom: 0.7rem;
    transition: all 0.3s ease;
}}
.workspace-shell:hover {{
    box-shadow: 0 10px 22px rgba(25,14,36,0.08);
}}

.workspace-kicker {{
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #773344;
    margin-bottom: 0.2rem;
}}

.workspace-title {{
    font-family:'Inter Tight','Inter',sans-serif;
    font-size: 0.95rem;
    color:#160029;
    line-height:1.15;
    margin: 0;
    font-weight: 700;
}}

.workspace-copy {{
    color:#5d3945;
    font-size:0.75rem;
    line-height:1.5;
    margin-top:0.2rem;
}}

/* ── SLIM LOADER ─────────────────────────────────────── */
.slim-loader-kicker {{
    font-size:0.65rem;
    font-weight:800;
    letter-spacing:0.12em;
    text-transform:uppercase;
    color:#a3195b;
    margin-bottom:0.2rem;
}}

.slim-loader-title {{
    font-size:0.9rem;
    font-weight:800;
    color:#251329;
    line-height:1.2;
    margin-bottom:0.2rem;
}}

.slim-loader-copy {{
    font-size:0.8rem;
    color:#766772;
    line-height:1.5;
}}

.slim-loader-side {{
    font-size:0.75rem;
    font-weight:800;
    color:#907785;
    white-space:nowrap;
    padding-bottom:0.1rem;
}}

.dataset-control-caption {{
    font-size:0.65rem;
    font-weight:800;
    letter-spacing:0.08em;
    text-transform:uppercase;
    color:#8b6771;
    margin:0 0 0.3rem 0.1rem;
}}

/* ── INPUT EDITOR ────────────────────────────────────── */
.input-editor-shell {{
    background:linear-gradient(180deg,#fffaf8 0%,#f8efea 100%);
    border:1px solid #e3b5a4;
    border-radius:18px;
    padding:0.7rem 0.9rem 0.6rem 0.9rem;
    margin:0.2rem 0 0.5rem 0;
    box-shadow:0 8px 18px rgba(25,14,36,0.04);
    transition: all 0.3s ease;
}}
.input-editor-shell:hover {{
    box-shadow:0 10px 22px rgba(25,14,36,0.07);
}}

.input-editor-kicker {{
    font-size:0.65rem;
    font-weight:800;
    text-transform:uppercase;
    letter-spacing:0.08em;
    color:#a3195b;
    margin-bottom:0.2rem;
}}

.input-editor-title {{
    font-size:0.85rem;
    font-weight:800;
    color:#241226;
    line-height:1.2;
}}

.input-editor-chip {{
    padding:0.3rem 0.7rem;
    border-radius:999px;
    background:#fff;
    border:1px solid #e3b5a4;
    color:#773344;
    font-size:0.7rem;
    font-weight:800;
    white-space:nowrap;
    transition: all 0.2s ease;
}}
.input-editor-chip:hover {{
    background:#e3b5a4;
    transform: scale(1.02);
}}

/* ── BATCH SHELL ─────────────────────────────────────── */
.batch-shell {{
    background:linear-gradient(180deg,#ffffff 0%,#f9f1ec 100%);
    border:1px solid #e3b5a4;
    border-radius:16px;
    padding:0.55rem 0.8rem 0.5rem 0.8rem;
    box-shadow:0 6px 16px rgba(25,14,36,0.04);
    margin:0.1rem 0 0.5rem 0;
    transition: all 0.3s ease;
}}
.batch-shell:hover {{
    box-shadow:0 10px 22px rgba(25,14,36,0.07);
}}

.batch-kicker {{
    font-size:0.6rem;
    font-weight:800;
    letter-spacing:0.08em;
    text-transform:uppercase;
    color:#a3195b;
    margin-bottom:0.15rem;
}}

.batch-title {{
    font-family:'Inter Tight','Inter',sans-serif;
    font-size:0.88rem;
    font-weight:700;
    color:#211120;
    line-height:1.15;
    margin-bottom:0.15rem;
}}

.batch-copy {{
    color:#6d5a68;
    font-size:0.72rem;
    line-height:1.45;
    max-width:800px;
}}

.batch-selection-note {{
    background:#fff7f4;
    border:1px solid #e3b5a4;
    border-radius:12px;
    padding:0.5rem 0.8rem;
    color:#5f4751;
    font-size:0.75rem;
    line-height:1.4;
    margin:0.4rem 0 0.6rem 0;
    transition: all 0.2s ease;
}}
.batch-selection-note:hover {{
    background:#fffaf8;
    transform: translateX(3px);
}}

.batch-selection-note strong {{
    color:#160029;
    font-size:0.85rem;
}}

/* ── CHART PANEL ─────────────────────────────────────── */
.chart-panel {{
    background:linear-gradient(180deg,#fffefe 0%,#f8efea 100%);
    border:1px solid #e3b5a4;
    border-radius:18px;
    padding:0.9rem 1rem 0.8rem 1rem;
    box-shadow:0 8px 18px rgba(25,14,36,0.04);
    margin:0.8rem 0 0.5rem 0;
    transition: all 0.3s ease;
}}
.chart-panel:hover {{
    box-shadow:0 10px 22px rgba(25,14,36,0.07);
}}

.chart-panel-title {{
    font-family:'Inter Tight','Inter',sans-serif;
    font-size:0.9rem;
    font-weight:700;
    color:#221221;
    margin-bottom:0.2rem;
}}

.chart-panel-copy {{
    color:#6d5a68;
    font-size:0.8rem;
    line-height:1.5;
}}

.chart-conclusion {{
    margin-top:0.6rem;
    padding:0.7rem 0.9rem;
    border-radius:14px;
    background:linear-gradient(180deg,#fffaf7 0%,#fff3ed 100%);
    border:1px solid #ead1c8;
    color:#6d5a68;
    font-size:0.8rem;
    line-height:1.5;
    transition: all 0.2s ease;
}}
.chart-conclusion:hover {{
    background:linear-gradient(180deg,#fffdfb 0%,#fff8f3 100%);
    transform: translateX(3px);
}}

/* ── EXPLORER CARDS ──────────────────────────────────── */
.explorer-instruction-card {{
    background:linear-gradient(180deg,#fffaf7 0%,#fff2ec 100%);
    border:1px solid #ead1c8;
    border-left:5px solid #b24758;
    border-radius:18px;
    padding:0.8rem 1rem;
    margin:0.5rem 0 0.8rem 0;
    box-shadow:0 8px 18px rgba(25,14,36,0.04);
    transition: all 0.3s ease;
}}
.explorer-instruction-card:hover {{
    transform: translateX(3px);
    border-left-width: 6px;
}}

.explorer-instruction-title {{
    font-size:0.7rem;
    font-weight:800;
    letter-spacing:0.12em;
    text-transform:uppercase;
    color:#a3195b;
    margin-bottom:0.3rem;
}}

.explorer-instruction-copy {{
    font-size:0.85rem;
    line-height:1.6;
    color:#634e59;
}}

.explorer-orb-grid {{
    display:grid;
    grid-template-columns:repeat(3,minmax(0,1fr));
    gap:0.8rem;
    margin:0.8rem 0 1rem 0;
}}

.explorer-orb {{
    background:linear-gradient(180deg,#fff 0%,#fbf3ef 100%);
    border:1px solid #ead1c8;
    border-radius:999px;
    padding:0.7rem 0.9rem;
    display:flex;
    align-items:center;
    gap:0.7rem;
    box-shadow:0 8px 16px rgba(25,14,36,0.04);
    min-height: 75px;
    transition: all 0.3s ease;
}}
.explorer-orb:hover {{
    transform: translateY(-3px);
    box-shadow:0 12px 22px rgba(25,14,36,0.08);
}}

.explorer-orb-icon {{
    width: 38px; height: 38px;
    border-radius: 999px;
    display: flex; align-items: center; justify-content: center;
    background:linear-gradient(135deg,#d44d5c 0%,#a63a52 100%);
    color:#fff; font-weight:800; font-size:0.85rem;
    box-shadow:0 6px 14px rgba(164,59,83,0.18);
    transition: all 0.2s ease;
}}
.explorer-orb:hover .explorer-orb-icon {{
    transform: scale(1.05);
}}

.explorer-orb-label {{
    font-size:0.6rem;
    font-weight:800;
    letter-spacing:0.08em;
    text-transform:uppercase;
    color:#8b6771;
    margin-bottom:0.15rem;
}}

.explorer-orb-value {{
    font-family:'Inter Tight','Inter',sans-serif;
    font-size:1rem;
    font-weight:700;
    color:#241226;
    line-height:1.05;
}}

.explorer-orb-note {{
    font-size:0.7rem;
    line-height:1.4;
    color:#7a6874;
    margin-top:0.1rem;
}}

/* ── TOPIC FOCUS GRID ────────────────────────────────── */
.topic-focus-grid {{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:0.7rem;
    margin:0.4rem 0 0.8rem 0;
}}

.topic-focus-card {{
    background:linear-gradient(180deg,#fff 0%,#faf4f0 100%);
    border:1px solid #e3b5a4;
    border-radius:14px;
    padding:0.7rem 0.8rem;
    transition: all 0.3s ease;
}}
.topic-focus-card:hover {{
    transform: translateY(-2px);
    box-shadow:0 6px 14px rgba(25,14,36,0.06);
}}

.topic-focus-label {{
    font-size:0.65rem;
    font-weight:800;
    letter-spacing:0.08em;
    text-transform:uppercase;
    color:#8b6771;
    margin-bottom:0.2rem;
}}

.topic-focus-value {{
    font-size:0.85rem;
    font-weight:800;
    color:#221221;
    line-height:1.3;
}}

/* ── SIM LITE SHELL ──────────────────────────────────── */
.sim-lite-shell {{
    background:linear-gradient(180deg,#ffffff 0%,#fbf3ef 100%);
    border:1px solid #e3b5a4;
    border-radius:20px;
    padding:0.8rem 0.9rem 0.7rem 0.9rem;
    box-shadow:0 8px 20px rgba(25,14,36,0.05);
    transition: all 0.3s ease;
}}
.sim-lite-shell:hover {{
    box-shadow:0 12px 26px rgba(25,14,36,0.08);
}}

.sim-lite-head {{display:flex;justify-content:space-between;align-items:flex-start;gap:0.7rem;margin-bottom:0.8rem;}}
.sim-lite-kicker {{color:#8b6771;font-size:0.65rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.2rem;}}
.sim-lite-title {{font-family:'Inter Tight','Inter',sans-serif;font-size:1.1rem;font-weight:800;color:#221221;}}
.sim-lite-pill {{padding:0.3rem 0.7rem;border-radius:999px;border:1px solid #d44d5c;font-weight:800;font-size:0.85rem;transition: all 0.2s ease;}}
.sim-lite-pill:hover {{background:#d44d5c;color:white;transform: scale(1.02);}}

.sim-lite-hero {{display:grid;grid-template-columns:100px 1fr;gap:0.8rem;align-items:center;margin-bottom:0.8rem;}}
.sim-lite-ring {{width:85px;height:85px;border-radius:999px;display:flex;align-items:center;justify-content:center;box-shadow:0 6px 14px rgba(25,14,36,0.07);transition: all 0.3s ease;}}
.sim-lite-ring:hover {{transform: scale(1.02);}}
.sim-lite-ring-inner {{width:62px;height:62px;border-radius:999px;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:inset 0 0 0 1px rgba(227,181,164,0.45);}}
.sim-lite-ring-inner strong {{font-family:'Inter Tight','Inter',sans-serif;font-size:1.1rem;line-height:1;}}
.sim-lite-ring-inner span {{font-size:0.65rem;color:#8b6771;margin-top:0.15rem;}}

.sim-lite-summary-title {{font-size:0.85rem;font-weight:800;color:#221221;margin-bottom:0.2rem;}}
.sim-lite-summary-copy {{font-size:0.8rem;line-height:1.5;color:#6d5a68;}}

.sim-lite-top-note {{
    display:block;background:#fff8f4;border:1px solid #ead1c8;
    border-radius:14px;padding:0.6rem 0.8rem;margin:0.7rem 0 0.7rem 0;
    transition: all 0.2s ease;
}}
.sim-lite-top-note:hover {{
    background:#fffbf8;
    transform: translateX(3px);
}}
.sim-lite-top-note-title {{display:block;font-size:0.65rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin-bottom:0.2rem;}}
.sim-lite-top-note-copy {{display:block;font-size:0.8rem;line-height:1.5;color:#6d5a68;}}

/* ── HISTORY OVERVIEW ────────────────────────────────── */
.history-table-title {{
    font-size:0.9rem;
    font-weight:800;
    color:#241226;
    margin-bottom:0.2rem;
}}

.history-table-copy {{
    font-size:0.8rem;
    line-height:1.5;
    color:#6d5a68;
    max-width:800px;
}}

/* ── LEADERBOARD ─────────────────────────────────────── */
.leaderboard-shell {{display:grid;gap:0.7rem;margin-top:0.7rem;}}

.leaderboard-card {{
    display:grid;
    grid-template-columns:50px 1fr auto;
    gap:0.8rem;
    align-items:center;
    background:linear-gradient(180deg,#fff 0%,#fbf3ef 100%);
    border:1px solid #e7c2b3;
    border-radius:16px;
    padding:0.8rem 1rem;
    box-shadow:0 6px 14px rgba(25,14,36,0.04);
    transition: all 0.3s ease;
}}
.leaderboard-card:hover {{
    transform: translateY(-2px);
    box-shadow:0 10px 20px rgba(25,14,36,0.08);
    border-color: #d44d5c;
}}

.leaderboard-rank {{
    width:38px;height:38px;border-radius:12px;
    background:#fff7f1;border:1px solid #e7c2b3;
    display:flex;align-items:center;justify-content:center;
    font-size:0.9rem;
    transition: all 0.2s ease;
}}
.leaderboard-card:hover .leaderboard-rank {{
    background:linear-gradient(135deg,#d44d5c 0%,#cb4a5e 100%);
    color: white;
    border-color: #d44d5c;
}}

.leaderboard-title {{font-size:0.9rem;font-weight:800;color:#221221;margin-bottom:0.15rem;}}
.leaderboard-meta {{font-size:0.75rem;color:#7a6874;line-height:1.4;margin-bottom:0.4rem;}}
.leaderboard-track {{height:6px;background:#f3dfd7;border-radius:999px;overflow:hidden;}}
.leaderboard-fill {{height:100%;background:linear-gradient(90deg,#d44d5c 0%,#b24758 100%);border-radius:999px;transition: width 0.5s ease;}}
.leaderboard-side {{text-align:right;min-width:80px;}}
.leaderboard-score {{font-size:1rem;font-weight:800;color:#221221;}}
.leaderboard-note {{font-size:0.7rem;color:#8b6771;line-height:1.3;}}

/* ── EMPTY REVIEW CARD ───────────────────────────────── */
.empty-review-card {{
    background:linear-gradient(180deg,#ffffff 0%,#f9f1ec 100%);
    border:1px solid #e3b5a4;
    border-radius:20px;
    padding:0.9rem 1rem 0.8rem 1rem;
    box-shadow:0 8px 18px rgba(25,14,36,0.05);
    min-height: 320px;
    display:flex;flex-direction:column;justify-content:space-between;
    transition: all 0.3s ease;
}}
.empty-review-card:hover {{
    box-shadow:0 10px 22px rgba(25,14,36,0.08);
}}

.empty-review-top {{display:flex;justify-content:space-between;gap:0.8rem;align-items:flex-start;margin-bottom:0.7rem;}}
.empty-review-title {{font-family:'Inter Tight','Inter',sans-serif;font-size:1.1rem;color:#160029;margin:0.05rem 0 0.2rem 0;font-weight:700;}}
.empty-review-copy {{color:#5d3945;font-size:0.8rem;line-height:1.5;}}
.empty-review-pill {{padding:0.3rem 0.7rem;border-radius:999px;background:#fff;border:1px solid #e3b5a4;color:#773344;font-weight:800;font-size:0.75rem;white-space:nowrap;transition: all 0.2s ease;}}
.empty-review-pill:hover {{background:#e3b5a4;transform: scale(1.02);}}
.empty-review-list {{display:grid;gap:0.5rem;margin-top:0.5rem;}}
.empty-review-item {{display:flex;gap:0.7rem;align-items:flex-start;padding:0.7rem 0.8rem;border-radius:14px;background:#fff;border:1px solid #e3b5a4;transition: all 0.2s ease;}}
.empty-review-item:hover {{transform: translateX(3px);border-color:#d44d5c;}}
.empty-review-icon {{width:30px;height:30px;min-width:30px;border-radius:10px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#d44d5c 0%,#b24758 100%);color:#fff;font-size:0.85rem;font-weight:800;}}
.empty-review-item strong {{display:block;color:#160029;font-size:0.8rem;margin-bottom:0.15rem;}}
.empty-review-item span {{display:block;color:#5d3945;font-size:0.75rem;line-height:1.4;}}
.empty-review-footer {{display:grid;grid-template-columns:repeat(3,1fr);gap:0.5rem;margin-top:0.8rem;}}
.empty-review-stat {{background:#fff;border:1px solid #e3b5a4;border-radius:14px;padding:0.6rem;text-align:center;transition: all 0.2s ease;}}
.empty-review-stat:hover {{transform: translateY(-2px);box-shadow:0 4px 10px rgba(0,0,0,0.04);}}
.empty-review-stat-label {{font-size:0.65rem;font-weight:800;color:#8b6771;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.15rem;}}
.empty-review-stat-value {{font-family:'Inter Tight','Inter',sans-serif;font-size:1rem;color:#160029;font-weight:700;}}

/* ── RESULT CARDS GRID ───────────────────────────────── */
.result-cards-grid {{
    display: grid;
    grid-template-columns: 1.05fr 1.35fr 1fr;
    gap: 1.2rem;
    margin: 0.8rem 0;
}}

@media (max-width: 900px) {{
    .result-cards-grid {{
        grid-template-columns: 1fr;
        gap: 1rem;
    }}
}}

/* ── SINGLE REVIEW RIGHT COL ────────────────────────── */
.single-review-right-col {{
    padding-left: 0.5rem;
}}

/* ── RESULT HERO CARD ───────────────────────────────── */
.result-hero-card {{
    background:linear-gradient(180deg,#ffffff 0%,#fcf7f3 100%);
    border:1px solid #e3b5a4;border-radius:20px;
    padding:0.9rem 1rem;box-shadow:0 10px 22px rgba(25,14,36,0.05);
    display:flex;justify-content:space-between;gap:0.8rem;
    align-items:flex-start;flex-wrap:wrap;margin:0.8rem 0 0.7rem 0;
    transition: all 0.3s ease;
}}
.result-hero-card:hover {{
    box-shadow:0 14px 26px rgba(25,14,36,0.08);
}}
.result-hero-kicker {{color:#8b6771;font-size:0.65rem;font-weight:800;text-transform:uppercase;letter-spacing:0.09em;margin-bottom:0.2rem;}}
.result-hero-title {{font-family:'Inter Tight','Inter',sans-serif;color:#160029;font-size:1rem;line-height:1.08;margin-bottom:0.2rem;font-weight:700;}}
.result-hero-copy {{color:#5d3945;font-size:0.75rem;line-height:1.5;max-width:700px;}}

/* ── RESPONSIVE ──────────────────────────────────────── */
@media (max-width: 1200px) {{
    [data-testid="stSidebar"] {{
        min-width: 260px !important;
        max-width: 260px !important;
        width: 260px !important;
    }}
}}

@media (max-width: 1100px) {{
    .hero-image-wrap {{ height: 120px !important; }}
    .hero-image-content {{ max-width: 65% !important; }}
    .hero-image-title {{ font-size: 1.1rem !important; }}
    .explorer-orb-grid {{ grid-template-columns: 1fr; }}
    .topic-focus-grid {{ grid-template-columns: 1fr 1fr; }}
}}

@media (max-width: 900px) {{
    .hero-image-content {{ max-width: 100% !important; }}
    .hero-image-title {{ font-size: 1rem !important; }}
    .hero-image-subtitle {{ font-size: 0.65rem !important; max-width: 100% !important; }}
    .topic-focus-grid {{ grid-template-columns: 1fr 1fr; }}
    .sim-lite-hero {{ grid-template-columns: 1fr; }}
    .sim-lite-ring {{ margin: 0 auto; }}
}}

@media (max-width: 768px) {{
    .block-container {{ padding-left: 0.8rem !important; padding-right: 0.8rem !important; }}
    .hero-image-wrap {{ height: 100px !important; border-radius: 16px !important; }}
    .hero-image-overlay {{ padding: 1rem 1.2rem; }}
    .hero-image-title {{ font-size: 0.9rem !important; }}
    .hero-image-subtitle {{ font-size: 0.6rem; line-height: 1.4; }}
    .topic-focus-grid {{ grid-template-columns: 1fr; }}
    .light-table {{ min-width: 500px; }}
}}

@media (max-width: 620px) {{
    .hero-image-wrap {{ height: 90px !important; }}
    .hero-image-title {{ font-size: 0.8rem !important; }}
}}

/* ── TOPIC DEEP-DIVE (Tab 5) ─────────────────────────── */
.topic-pick-shell {{
    background: linear-gradient(135deg, #ffffff 0%, #fef8f5 100%);
    border: 1px solid #e3b5a4;
    border-left: 4px solid #D44D5C;
    border-radius: 16px;
    padding: 1rem 1.2rem 0.9rem 1.2rem;
    margin: 0.6rem 0 0.4rem 0;
    box-shadow: 0 4px 12px rgba(119, 51, 68, 0.06);
}}

.topic-pick-kicker {{
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #a3195b;
    margin-bottom: 0.25rem;
}}

.topic-pick-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #211120;
    line-height: 1.2;
    margin-bottom: 0.3rem;
}}

.topic-pick-copy {{
    font-size: 0.78rem;
    color: #6d5a68;
    line-height: 1.5;
    max-width: 680px;
}}

.comparison-select-head {{
    background: #ffffff;
    border: 1px solid rgba(227, 181, 164, 0.4);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    margin: 0.8rem 0 0.4rem 0;
}}

.comparison-select-title {{
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: #211120;
    margin-bottom: 0.2rem;
}}

.comparison-select-copy {{
    font-size: 0.75rem;
    color: #6d5a68;
    line-height: 1.45;
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
    desc_html = f'<div class="small-note" style="margin-top:0.3rem;">{html.escape(description)}</div>' if description else ""
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
                <span style="font-size:0.75rem;">2026 Universiti Teknologi MARA</span>
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
            margin: 0.1rem 0 0.8rem 0;
            padding: 0.5rem 0.8rem;
            border-radius: 18px;
            border: 1px solid #e3b5a4;
            background: linear-gradient(180deg, #ffffff 0%, #fcf8fb 100%);
            box-shadow: 0 6px 16px rgba(22, 9, 28, 0.04);
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
            margin-bottom: 0.15rem;
        }
        .review-workspace-header h1 {
            margin: 0 0 0.2rem 0;
            color: #160029;
            font-family: 'Inter Tight', 'Inter', sans-serif;
            font-size: 1rem;
            line-height: 1.1;
            letter-spacing: -0.02em;
            font-weight: 700;
        }
        .review-workspace-header p {
            margin: 0;
            color: #5d5060;
            font-size: 0.75rem;
            line-height: 1.5;
            max-width: 680px;
        }
        .review-workspace-badges {
            display: flex;
            gap: 0.4rem;
            flex-wrap: wrap;
            justify-content: flex-end;
            flex: 0 0 auto;
        }
        .review-badge-card {
            min-width: 140px;
            background: linear-gradient(135deg, #162a63 0%, #4a1d62 55%, #7a1657 100%);
            border-radius: 14px;
            padding: 0.5rem 0.7rem;
            border: 1px solid rgba(253,3,99,0.14);
            box-shadow: 0 6px 14px rgba(20, 10, 33, 0.1);
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
            font-size: 0.75rem;
            line-height: 1.3;
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


# =========================================================
# INTERACTIVE VISUALIZATION COMPONENTS
# =========================================================

def render_interactive_gauge(score: float, title: str = "Alignment Score", height: int = 220):
    """Render an interactive gauge chart using Plotly."""
    import plotly.graph_objects as go
    
    tier = get_score_tier(score)
    if tier == "good":
        color = "#06A77D"
    elif tier == "moderate":
        color = "#F1A208"
    else:
        color = "#A31621"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': title, 'font': {'size': 16, 'color': COLORS["text_primary"]}},
        number={'suffix': "%", 'font': {'size': 32, 'color': color}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': COLORS["text_muted"]},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 1,
            'bordercolor': COLORS["border"],
            'steps': [
                {'range': [0, 50], 'color': "#FFCDD2"},
                {'range': [50, 70], 'color': "#FFF9C4"},
                {'range': [70, 100], 'color': "#C8E6C9"}
            ],
            'threshold': {
                'line': {'color': color, 'width': 3},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': COLORS["text_primary"]}
    )
    st.plotly_chart(fig, use_container_width=True)


def render_comparison_bar_chart(scores: dict, title: str = "Score Comparison", height: int = 350):
    """Render a horizontal bar chart comparing multiple scores."""
    import plotly.graph_objects as go
    
    labels = list(scores.keys())
    values = list(scores.values())
    
    colors = []
    for val in values:
        tier = get_score_tier(val)
        if tier == "good":
            colors.append("#06A77D")
        elif tier == "moderate":
            colors.append("#F1A208")
        else:
            colors.append("#A31621")
    
    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation='h',
        marker_color=colors,
        text=[f"{v:.1f}%" for v in values],
        textposition='outside',
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Score (%)",
        yaxis_title="",
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': COLORS["text_primary"]},
        xaxis=dict(range=[0, 100], gridcolor=COLORS["border"]),
        yaxis=dict(gridcolor=COLORS["border"])
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_radar_chart(categories: dict, title: str = "Performance by Category", height: int = 350):
    """Render a radar chart for multi-category performance."""
    import plotly.graph_objects as go
    
    labels = list(categories.keys())
    values = list(categories.values())
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=labels,
        fill='toself',
        marker=dict(color=COLORS["lobster_pink"], size=6),
        line=dict(color=COLORS["wine_plum"], width=2),
        hovertemplate="%{theta}: %{r:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=COLORS["border"]),
            angularaxis=dict(gridcolor=COLORS["border"], linecolor=COLORS["border"])
        ),
        title=title,
        height=height,
        margin=dict(l=50, r=50, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': COLORS["text_primary"]}
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_timeline_chart(data: list, x_key: str, y_key: str, title: str = "Trend Over Time", height: int = 300):
    """Render a line chart for timeline data."""
    import plotly.graph_objects as go
    
    x_values = [item[x_key] for item in data]
    y_values = [item[y_key] for item in data]
    
    latest_value = y_values[-1] if y_values else 0
    tier = get_score_tier(latest_value)
    if tier == "good":
        line_color = "#06A77D"
    elif tier == "moderate":
        line_color = "#F1A208"
    else:
        line_color = "#A31621"
    
    fig = go.Figure(go.Scatter(
        x=x_values,
        y=y_values,
        mode='lines+markers',
        line=dict(color=line_color, width=2),
        marker=dict(size=6, color=line_color),
        fill='tozeroy',
        fillcolor=f"rgba({int(line_color[1:3],16)},{int(line_color[3:5],16)},{int(line_color[5:7],16)},0.1)",
        hovertemplate="Date: %{x}<br>Score: %{y:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Score (%)",
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': COLORS["text_primary"]},
        yaxis=dict(range=[0, 100], gridcolor=COLORS["border"]),
        xaxis=dict(gridcolor=COLORS["border"])
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_donut_chart(values: dict, title: str = "Distribution", height: int = 260):
    """Render a donut chart for distribution data."""
    import plotly.graph_objects as go
    
    labels = list(values.keys())
    sizes = list(values.values())
    
    color_map = {
        "Good": "#06A77D",
        "Moderate": "#F1A208",
        "Weak": "#A31621"
    }
    colors = [color_map.get(label, COLORS["lobster_pink"]) for label in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=sizes,
        hole=0.4,
        marker_colors=colors,
        textinfo='label+percent',
        textposition='auto',
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>"
    )])
    
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': COLORS["text_primary"]},
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    
    st.plotly_chart(fig, use_container_width=True)


# =========================================================
# ANIMATION AND LOADING UTILITIES
# =========================================================

def render_skeleton_loader(height: int = 80, width: str = "100%", count: int = 1):
    """Render a skeleton loading animation."""
    skeletons = []
    for i in range(count):
        skeletons.append(f'<div class="skeleton" style="height: {height}px; width: {width}; margin-bottom: 0.8rem;"></div>')
    st.markdown(''.join(skeletons), unsafe_allow_html=True)


def render_toast_message(message: str, type: str = "info", duration: int = 3000):
    """Render a temporary toast notification."""
    bg_color = {
        "success": "#06A77D",
        "error": "#A31621",
        "warning": "#F1A208",
        "info": "#773344"
    }.get(type, "#773344")
    
    toast_html = f"""
    <div id="toast-message" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: {bg_color};
        color: white;
        padding: 10px 18px;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        z-index: 9999;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        animation: slideInRight 0.3s ease;
    ">
        {html.escape(message)}
    </div>
    <script>
        setTimeout(function() {{
            var toast = document.getElementById('toast-message');
            if(toast) {{
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.3s';
                setTimeout(function() {{ toast.remove(); }}, 300);
            }}
        }}, {duration});
    </script>
    """
    st.markdown(toast_html, unsafe_allow_html=True)


def render_confetti():
    """Render a confetti animation for celebration moments."""
    confetti_html = """
    <canvas id="confetti-canvas" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 9998;"></canvas>
    <script>
    (function() {
        var canvas = document.getElementById('confetti-canvas');
        if(!canvas) return;
        var ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        var particles = [];
        var colors = ['#06A77D', '#F1A208', '#D44D5C', '#773344', '#160029'];
        
        for(var i = 0; i < 100; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height - canvas.height,
                size: Math.random() * 5 + 2,
                speedY: Math.random() * 4 + 2,
                speedX: Math.random() * 2 - 1,
                color: colors[Math.floor(Math.random() * colors.length)],
                rotation: Math.random() * 360,
                rotationSpeed: Math.random() * 8 - 4
            });
        }
        
        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            var allDone = true;
            for(var i = 0; i < particles.length; i++) {
                var p = particles[i];
                p.y += p.speedY;
                p.x += p.speedX;
                p.rotation += p.rotationSpeed;
                if(p.y < canvas.height + 50) allDone = false;
                ctx.save();
                ctx.translate(p.x, p.y);
                ctx.rotate(p.rotation * Math.PI / 180);
                ctx.fillStyle = p.color;
                ctx.fillRect(-p.size/2, -p.size/2, p.size, p.size);
                ctx.restore();
            }
            if(!allDone) requestAnimationFrame(animate);
            else canvas.remove();
        }
        animate();
        
        setTimeout(function() {
            if(canvas) canvas.remove();
        }, 3000);
    })();
    </script>
    """
    st.markdown(confetti_html, unsafe_allow_html=True)