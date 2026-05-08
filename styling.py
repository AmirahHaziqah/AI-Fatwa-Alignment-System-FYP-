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
    "ink":         "#1A0A12",
    "ink_mid":     "#3D1A28",
    "ink_soft":    "#6B3A50",
    "crimson":     "#8B1A34",
    "rose":        "#C04060",
    "blush":       "#E0A0B0",
    "parchment":   "#F5EFE8",
    "cream":       "#FBF7F3",
    "paper":       "#FFFFFF",
    "gold":        "#B8902C",
    "gold_light":  "#EDD898",
    "sage":        "#2E7A56",
    "sand":        "#E0D4C8",
    "sand_mid":    "#C8B8A8",
    "border":      "#DDD0C5",
    "border_soft": "#EDE5DC",

    # legacy aliases kept so existing code doesn't break
    "linen":           "#F5EFE8",
    "almond_silk":     "#E0D4C8",
    "lobster_pink":    "#C04060",
    "wine_plum":       "#8B1A34",
    "midnight_violet": "#1A0A12",
    "navy":            "#1A0A12",
    "navy_md":         "#3D1A28",
    "navy_lt":         "#8B1A34",
    "slate":           "#3D1A28",
    "slate_lt":        "#E0A0B0",
    "teal":            "#C04060",
    "teal_lt":         "#C04060",
    "accent_red":      "#C04060",
    "white":           "#FFFFFF",
    "off_white":       "#FBF7F3",
    "surface":         "#F5EFE8",
    "surface_alt":     "#EDE5DC",
    "muted":           "#6B3A50",
    "text_primary":    "#1A0A12",
    "text_secondary":  "#3D1A28",
    "text_muted":      "#6B3A50",
    "success":         "#2E7A56",
    "warning":         "#B8902C",
    "danger":          "#8B1A34",
    "info":            "#3D1A28",
}


def _image_to_data_uri(image_path: Optional[str]) -> Optional[str]:
    if not image_path:
        return None
    if not os.path.exists(image_path):
        return None
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
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
    st.markdown("""
<style>
/* ─────────────────────────────────────────────────────────
   TYPEFACES
   Cormorant Garamond  →  display / headings / numbers
   DM Sans             →  body / UI labels
   DM Mono             →  code / chips
───────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400;1,600&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=DM+Mono:wght@400;500&display=swap');

/* ─────────────────────────────────────────────────────────
   DESIGN TOKENS
───────────────────────────────────────────────────────── */
:root {
    --ink:          #1A0A12;
    --ink-mid:      #3D1A28;
    --ink-soft:     #6B3A50;
    --crimson:      #8B1A34;
    --rose:         #C04060;
    --blush:        #E0A0B0;
    --parchment:    #F5EFE8;
    --cream:        #FBF7F3;
    --paper:        #FFFFFF;
    --gold:         #B8902C;
    --gold-lt:      #EDD898;
    --sage:         #2E7A56;
    --sand:         #E0D4C8;
    --sand-mid:     #C8B8A8;
    --border:       #DDD0C5;
    --border-soft:  #EDE5DC;

    --sh-sm: 0 1px 2px rgba(26,10,18,.04), 0 3px 8px rgba(26,10,18,.04);
    --sh-md: 0 2px 4px rgba(26,10,18,.04), 0 8px 24px rgba(26,10,18,.07);
    --sh-lg: 0 4px 8px rgba(26,10,18,.04), 0 20px 48px rgba(26,10,18,.10);

    --r-sm:  6px;
    --r-md:  12px;
    --r-lg:  18px;
    --r-xl:  24px;
}

/* ─────────────────────────────────────────────────────────
   KEYFRAMES
───────────────────────────────────────────────────────── */
@keyframes fadeUp    { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeIn    { from{opacity:0} to{opacity:1} }
@keyframes slideLeft { from{opacity:0;transform:translateX(-18px)} to{opacity:1;transform:translateX(0)} }
@keyframes barGrow   { from{transform:scaleX(0)} to{transform:scaleX(1)} }
@keyframes shimmer   { 0%{background-position:-600px 0} 100%{background-position:600px 0} }
@keyframes slideInDown {
    from{opacity:0;transform:translate(-50%,-60%) scale(.88)}
    to  {opacity:1;transform:translate(-50%,-50%) scale(1)}
}
@keyframes fadeOutUp {
    from{opacity:1;transform:translate(-50%,-50%) scale(1)}
    to  {opacity:0;transform:translate(-50%,-60%) scale(.90)}
}

/* ─────────────────────────────────────────────────────────
   BASE
───────────────────────────────────────────────────────── */
*,*::before,*::after { box-sizing:border-box; }
html { scroll-behavior:smooth; font-size:14px !important; }
body, html, [class*="css"] {
    font-family:'DM Sans', system-ui, sans-serif !important;
    color:var(--ink);
    -webkit-font-smoothing:antialiased;
    -moz-osx-font-smoothing:grayscale;
    overflow-x:hidden !important;
}
strong { font-weight:600 !important; }
.stApp { background:var(--parchment) !important; overflow-x:hidden !important; }
[data-testid="stAppViewContainer"] { background:var(--parchment) !important; }
.block-container {
    padding-top:0.3rem !important;
    padding-left:1.1rem !important;
    padding-right:1.1rem !important;
    max-width:1400px !important;
    width:100% !important;
    margin:0 auto !important;
}
[data-testid="stHeader"] { background:transparent !important; }
[data-testid="stToolbar"] { right:1rem; }

/* ─────────────────────────────────────────────────────────
   SCROLLBAR
───────────────────────────────────────────────────────── */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:var(--parchment); }
::-webkit-scrollbar-thumb { background:var(--sand-mid); border-radius:99px; }
::-webkit-scrollbar-thumb:hover { background:var(--rose); }

/* ─────────────────────────────────────────────────────────
   SIDEBAR  ·  deep ink canvas
───────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    min-width:260px !important;
    max-width:260px !important;
    width:260px !important;
    background:var(--ink) !important;
    border-right:1px solid rgba(255,255,255,.06) !important;
    box-shadow:8px 0 40px rgba(26,10,18,.28) !important;
}
[data-testid="stSidebar"] > div:first-child {
    background:transparent !important;
    padding:1rem .8rem 1.2rem .8rem !important;
}
[data-testid="stSidebar"] * { color:rgba(255,255,255,.88) !important; }
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li,
[data-testid="stSidebar"] .stMarkdown span { color:rgba(255,255,255,.70) !important; }

.sidebar-clean-header {
    padding:.4rem .1rem 1rem .1rem !important;
    border-bottom:1px solid rgba(255,255,255,.07) !important;
    margin-bottom:.9rem !important;
}
.sidebar-kicker-line {
    width:24px !important; height:2px !important;
    background:var(--gold) !important;
    margin-bottom:.7rem !important; border-radius:2px;
}
.sidebar-title {
    font-family:'Cormorant Garamond', Georgia, serif !important;
    font-size:1.55rem !important; font-weight:500;
    color:#FFF !important; letter-spacing:.01em !important;
    line-height:1.1 !important; margin:0 0 .45rem 0 !important;
}
.sidebar-subtitle {
    font-size:.72rem !important; line-height:1.6 !important;
    color:rgba(255,255,255,.45) !important; margin:0;
}
.sidebar-workspace-card {
    background:rgba(255,255,255,.05) !important;
    border:1px solid rgba(255,255,255,.07) !important;
    border-radius:var(--r-md) !important;
    padding:.85rem !important; margin-bottom:.6rem;
    transition:background .2s;
}
.sidebar-workspace-card:hover { background:rgba(255,255,255,.08) !important; }
.sidebar-kicker {
    display:inline-flex; align-items:center;
    padding:.18rem .55rem; border-radius:99px;
    background:rgba(184,144,44,.18) !important;
    color:var(--gold-lt) !important;
    border:1px solid rgba(184,144,44,.28) !important;
    font-size:.6rem !important; font-weight:600;
    margin-bottom:.42rem;
    text-transform:uppercase; letter-spacing:.12em;
}
.sidebar-workspace-title {
    font-size:.86rem; font-weight:600; line-height:1.3;
    color:#FFF !important; margin-bottom:.12rem;
}
.sidebar-workspace-subtitle {
    font-size:.72rem; line-height:1.5;
    color:rgba(255,255,255,.50) !important; margin-bottom:.5rem;
}
.sidebar-highlight-row {
    display:grid; grid-template-columns:1fr 1fr;
    gap:.45rem !important; margin-top:.6rem;
}
.sidebar-highlight-chip {
    background:rgba(255,255,255,.07) !important;
    border:1px solid rgba(255,255,255,.10) !important;
    border-top:2px solid var(--gold) !important;
    border-radius:var(--r-sm); padding:.5rem .6rem;
    transition:background .2s;
}
.sidebar-highlight-chip:hover { background:rgba(255,255,255,.11) !important; }
.sidebar-highlight-label {
    font-size:.56rem; color:rgba(255,255,255,.40) !important;
    margin-bottom:.15rem; font-weight:600;
    text-transform:uppercase; letter-spacing:.09em;
}
.sidebar-highlight-value {
    font-family:'Cormorant Garamond', Georgia, serif !important;
    font-size:1.3rem !important; color:#FFF !important; font-weight:500; line-height:1;
}
.sidebar-section-card {
    background:rgba(255,255,255,.04) !important;
    border:1px solid rgba(255,255,255,.07) !important;
    border-radius:var(--r-md) !important;
    padding:.78rem !important; margin-bottom:.6rem !important;
    transition:background .2s;
}
.sidebar-section-card:hover { background:rgba(255,255,255,.07) !important; }
.sidebar-section-card * { color:rgba(255,255,255,.88) !important; }
.sidebar-section-title {
    display:flex; align-items:center; gap:.4rem;
    font-size:.6rem !important; font-weight:600;
    margin-bottom:.55rem; padding-bottom:.48rem;
    border-bottom:1px solid rgba(255,255,255,.07) !important;
    color:rgba(255,255,255,.38) !important;
    letter-spacing:.12em !important; text-transform:uppercase !important;
}
.sidebar-progress-stack { display:grid; gap:.55rem; }
.sidebar-progress-item  { display:grid; gap:.26rem; }
.sidebar-progress-top   { display:flex; justify-content:space-between; font-size:.74rem; }
.sidebar-progress-name  { color:rgba(255,255,255,.68) !important; font-weight:500; }
.sidebar-progress-value { color:var(--gold-lt) !important; font-weight:600; font-size:.74rem; }
.sidebar-progress-bar   { height:3px !important; border-radius:99px; background:rgba(255,255,255,.08); overflow:hidden; }
.sidebar-progress-fill  { height:100%; border-radius:99px; animation:barGrow .6s ease-out; transform-origin:left; }
.sidebar-action-list { display:grid; gap:.42rem; }
.sidebar-action-item {
    display:flex; gap:.55rem; align-items:flex-start;
    padding:.68rem .78rem; border-radius:var(--r-sm) !important;
    background:rgba(255,255,255,.04) !important;
    border:1px solid rgba(255,255,255,.07) !important;
    transition:all .18s;
}
.sidebar-action-item:hover {
    background:rgba(255,255,255,.08) !important;
    border-color:rgba(184,144,44,.28) !important;
    transform:translateX(3px);
}
.sidebar-action-icon {
    width:26px; height:26px; min-width:26px; border-radius:5px;
    display:flex; align-items:center; justify-content:center;
    background:rgba(184,144,44,.20) !important;
    color:var(--gold-lt) !important; font-size:.78rem; font-weight:700; flex-shrink:0;
}
.sidebar-action-title { font-size:.76rem; font-weight:600; color:#FFF !important; margin-bottom:.15rem; }
.sidebar-action-text  { font-size:.69rem; line-height:1.5; color:rgba(255,255,255,.50) !important; }
.sidebar-mini-note {
    background:rgba(255,255,255,.04) !important;
    border:1px solid rgba(255,255,255,.07) !important;
    border-radius:var(--r-sm); padding:.72rem .82rem;
    color:rgba(255,255,255,.68) !important; line-height:1.55; font-size:.74rem;
}
.sidebar-mini-note strong { color:#FFF !important; }
.sidebar-pill-row { display:flex; flex-wrap:wrap; gap:.38rem; }
.sidebar-topic-pill {
    display:inline-flex; align-items:center;
    padding:.26rem .68rem; border-radius:99px;
    background:rgba(255,255,255,.06) !important;
    border:1px solid rgba(255,255,255,.09) !important;
    color:rgba(255,255,255,.68) !important; font-size:.69rem; font-weight:500;
    transition:all .18s;
}
.sidebar-topic-pill:hover {
    background:rgba(184,144,44,.18) !important;
    border-color:rgba(184,144,44,.35) !important;
    color:var(--gold-lt) !important;
}
.sidebar-legend-card {
    background:rgba(255,255,255,.04) !important;
    border:1px solid rgba(255,255,255,.07) !important;
    border-radius:var(--r-md) !important;
    padding:.78rem !important; margin-bottom:.6rem !important;
}
.sidebar-legend-grid { display:grid; gap:.38rem; }
.sidebar-legend-item { display:flex; gap:.5rem; align-items:center; font-size:.72rem; color:rgba(255,255,255,.70) !important; }
.sidebar-legend-dot  { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.sidebar-legend-label { font-weight:500; }
.sidebar-legend-range { color:rgba(255,255,255,.38) !important; font-size:.65rem; margin-left:auto; }
.sidebar-brand-card {
    background:rgba(255,255,255,.05);
    border:1px solid rgba(255,255,255,.07);
    border-left:2px solid var(--gold);
    border-radius:var(--r-sm);
    padding:.88rem .82rem; margin-bottom:.55rem;
    transition:background .2s;
}
.sidebar-brand-card:hover { background:rgba(255,255,255,.08); }
.sidebar-brand-title {
    font-family:'Cormorant Garamond', Georgia, serif !important;
    font-size:.98rem; font-weight:500;
    color:#FFF !important; margin-bottom:.15rem; line-height:1.3;
}
.sidebar-brand-subtitle { font-size:.68rem; line-height:1.55; color:rgba(255,255,255,.45) !important; }

/* ─────────────────────────────────────────────────────────
   TABS
───────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background:transparent !important;
    border-bottom:1px solid var(--border) !important;
    gap:0 !important; padding:0 !important;
}
.stTabs [data-baseweb="tab"] {
    background:transparent !important; border:none !important;
    color:var(--ink-soft) !important;
    font-family:'DM Sans', sans-serif !important;
    font-size:.82rem !important; font-weight:500 !important;
    padding:.55rem 1rem !important; border-radius:0 !important;
    border-bottom:2px solid transparent !important;
    transition:all .18s;
}
.stTabs [data-baseweb="tab"]:hover { color:var(--crimson) !important; background:rgba(139,26,52,.04) !important; }
.stTabs [aria-selected="true"] { color:var(--crimson) !important; border-bottom-color:var(--crimson) !important; font-weight:600 !important; }
.stTabs [data-baseweb="tab-highlight"] { display:none !important; }
.stTabs [data-baseweb="tab-border"]    { display:none !important; }
.stTabs [data-baseweb="tab-panel"]     { padding:0 !important; }

/* ─────────────────────────────────────────────────────────
   BUTTONS
───────────────────────────────────────────────────────── */
.stButton > button,
.stDownloadButton > button {
    font-family:'DM Sans', sans-serif !important;
    font-size:.77rem !important; font-weight:600 !important;
    letter-spacing:.02em !important;
    background:var(--crimson) !important;
    color:#FFF !important; -webkit-text-fill-color:#FFF !important;
    border:none !important;
    border-radius:var(--r-sm) !important;
    padding:.44rem .84rem !important; min-height:34px !important;
    box-shadow:0 1px 2px rgba(139,26,52,.15), 0 4px 10px rgba(139,26,52,.12) !important;
    transition:all .18s !important;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    background:var(--rose) !important;
    box-shadow:0 2px 4px rgba(139,26,52,.15), 0 8px 18px rgba(139,26,52,.18) !important;
    transform:translateY(-1px) !important;
    color:#FFF !important; -webkit-text-fill-color:#FFF !important;
}
.stButton > button *, .stDownloadButton > button * { color:#FFF !important; -webkit-text-fill-color:#FFF !important; }
.stButton > button[kind="secondary"] {
    background:var(--paper) !important;
    color:var(--crimson) !important; -webkit-text-fill-color:var(--crimson) !important;
    border:1px solid var(--border) !important;
    box-shadow:var(--sh-sm) !important;
}
.stButton > button[kind="secondary"]:hover {
    background:var(--cream) !important;
    border-color:var(--blush) !important;
    color:var(--crimson) !important; -webkit-text-fill-color:var(--crimson) !important;
    transform:translateY(-1px) !important;
    box-shadow:var(--sh-md) !important;
}
.stButton > button[kind="secondary"] * { color:var(--crimson) !important; -webkit-text-fill-color:var(--crimson) !important; }

/* ─────────────────────────────────────────────────────────
   FORM CONTROLS
───────────────────────────────────────────────────────── */
.stTextArea textarea,
.stTextArea [data-baseweb="textarea"],
.stTextArea [data-testid="stTextArea"] > div > div {
    background:var(--paper) !important;
    color:var(--ink) !important; -webkit-text-fill-color:var(--ink) !important;
    border:1px solid var(--border) !important;
    border-radius:var(--r-md) !important;
    font-family:'DM Sans', sans-serif !important;
    font-size:.83rem !important; line-height:1.65 !important;
    transition:border-color .18s, box-shadow .18s;
}
.stTextArea textarea:focus {
    border-color:var(--crimson) !important;
    box-shadow:0 0 0 3px rgba(139,26,52,.08) !important;
    outline:none;
}
.stTextArea textarea::placeholder { color:var(--sand-mid) !important; }
[data-testid="stTextArea"] { background:transparent !important; }

[data-baseweb="select"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background:var(--paper) !important;
    border:1px solid var(--border) !important;
    border-radius:var(--r-sm) !important;
    color:var(--ink) !important; font-size:.82rem !important;
}

/* ─────────────────────────────────────────────────────────
   RADIO BUTTONS  ·  pill-toggle style
───────────────────────────────────────────────────────── */
[data-testid="stRadio"] [role="radiogroup"] {
    display:grid !important;
    grid-template-columns:repeat(2,1fr) !important;
    gap:.45rem !important;
    background:transparent !important; box-shadow:none !important;
}
[data-testid="stRadio"] [role="radiogroup"] > label {
    min-height:46px !important;
    border-radius:var(--r-sm) !important;
    border:1px solid var(--border) !important;
    background:var(--paper) !important;
    box-shadow:var(--sh-sm) !important;
    display:flex !important; align-items:center !important;
    padding:.48rem .78rem !important;
    transition:all .18s !important; cursor:pointer;
}
[data-testid="stRadio"] [role="radiogroup"] > label:hover {
    border-color:var(--blush) !important; background:var(--cream) !important;
}
[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) {
    background:var(--crimson) !important; border-color:var(--crimson) !important;
    box-shadow:0 4px 12px rgba(139,26,52,.22) !important;
}
[data-testid="stRadio"] [role="radiogroup"] p {
    font-size:.78rem !important; font-weight:500 !important; color:var(--ink-mid) !important;
}
[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) p {
    color:#fff !important; -webkit-text-fill-color:#fff !important; font-weight:600 !important;
}

/* ─────────────────────────────────────────────────────────
   DASHBOARD HEADER
───────────────────────────────────────────────────────── */
.dash-header-wrap {
    position:relative; border-radius:var(--r-lg); margin-bottom:.6rem;
    overflow:hidden; min-height:160px; background:var(--ink);
    box-shadow:var(--sh-lg); border:1px solid rgba(255,255,255,.04);
}
.dash-header-wrap::after {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg, transparent, var(--gold) 40%, var(--gold) 60%, transparent);
}
.dash-header-overlay-img,
.dash-header-overlay-plain {
    position:absolute; inset:0;
    background:linear-gradient(108deg, rgba(26,10,18,.97) 0%, rgba(61,26,40,.88) 45%, rgba(26,10,18,.55) 80%, rgba(26,10,18,.25) 100%);
    display:flex; align-items:center;
    padding:2rem 2.2rem; z-index:2;
}
.dash-header-left { flex:1; min-width:0; }
.dash-header-kicker {
    display:inline-flex; align-items:center; gap:.42rem;
    padding:.2rem .68rem; border-radius:99px;
    background:rgba(184,144,44,.18); border:1px solid rgba(184,144,44,.30);
    color:var(--gold-lt); font-size:.6rem; font-weight:600;
    letter-spacing:.12em; text-transform:uppercase; margin-bottom:.55rem;
}
.dash-header-title {
    font-family:'Cormorant Garamond', Georgia, serif;
    font-size:2.2rem; font-weight:500; line-height:1.06;
    letter-spacing:-.01em; color:#fff; margin:0 0 .4rem 0;
}
.dash-header-subtitle {
    font-size:.84rem; font-weight:400; line-height:1.65;
    color:rgba(255,255,255,.60); margin:0; max-width:560px;
}

/* ─────────────────────────────────────────────────────────
   SECTION BANNER
───────────────────────────────────────────────────────── */
.section-banner {
    position:relative; width:100%; min-height:62px;
    border-radius:var(--r-md); overflow:hidden;
    margin:.75rem 0; border:1px solid rgba(255,255,255,.05);
    background:var(--ink-mid); box-shadow:var(--sh-md);
}
.section-banner-title {
    font-family:'Cormorant Garamond', Georgia, serif;
    font-size:1.2rem; font-weight:500; color:#FFF; margin:0;
}

/* ─────────────────────────────────────────────────────────
   TAB INTRO HERO
───────────────────────────────────────────────────────── */
.tab-minimal-hero {
    background:var(--paper);
    border:1px solid var(--border-soft);
    border-radius:var(--r-md);
    padding:.9rem 1.1rem .82rem;
    margin:.2rem 0 .75rem;
    box-shadow:var(--sh-sm);
}
.tab-minimal-kicker {
    color:var(--crimson); font-size:.6rem; font-weight:600;
    letter-spacing:.14em; text-transform:uppercase; margin-bottom:.2rem;
}
.tab-minimal-title {
    font-family:'Cormorant Garamond', Georgia, serif;
    font-size:1.45rem; font-weight:500; color:var(--ink); line-height:1.1;
}
.tab-minimal-copy { color:var(--ink-soft); font-size:.78rem; line-height:1.6; margin-top:.28rem; }

/* ─────────────────────────────────────────────────────────
   CARDS
───────────────────────────────────────────────────────── */
.soft-card, .card {
    background:var(--paper);
    border-radius:var(--r-md) !important;
    padding:1rem 1.1rem;
    border:1px solid var(--border-soft) !important;
    box-shadow:var(--sh-sm) !important;
    color:var(--ink);
    transition:box-shadow .2s, transform .2s;
}
.card:hover { transform:translateY(-2px) !important; box-shadow:var(--sh-md) !important; border-color:var(--sand) !important; }
.card-header {
    font-size:.63rem; font-weight:600; color:var(--ink-soft);
    margin-bottom:.48rem; padding-bottom:.42rem;
    border-bottom:1px solid var(--border-soft);
    letter-spacing:.08em; text-transform:uppercase;
}

/* ─────────────────────────────────────────────────────────
   METRIC CARDS
───────────────────────────────────────────────────────── */
.metric-card {
    background:var(--paper);
    border-radius:var(--r-md) !important;
    padding:.85rem .9rem;
    border:1px solid var(--border-soft) !important;
    box-shadow:var(--sh-sm) !important;
    text-align:center; height:100%;
    position:relative; overflow:hidden;
    transition:box-shadow .2s, transform .2s;
}
.metric-card:hover { transform:translateY(-2px); box-shadow:var(--sh-md) !important; }
.metric-card::before {
    content:""; position:absolute; top:0; left:0; right:0;
    height:2px; background:var(--crimson);
}
.metric-card-good::before { background:var(--sage); }
.metric-card-mid::before  { background:var(--gold); }
.metric-card-low::before  { background:var(--crimson); }
.metric-label {
    font-size:.6rem; font-weight:600; color:var(--ink-soft);
    margin-bottom:.28rem; letter-spacing:.09em; text-transform:uppercase;
}
.metric-value {
    font-family:'Cormorant Garamond', Georgia, serif;
    font-size:1.8rem; font-weight:500; color:var(--crimson); line-height:1;
}
.metric-value-good { color:var(--sage) !important; }
.metric-value-mid  { color:var(--gold) !important; }
.metric-value-low  { color:var(--crimson) !important; }

/* ─────────────────────────────────────────────────────────
   SECTION TITLES
───────────────────────────────────────────────────────── */
.section-title {
    font-family:'Cormorant Garamond', Georgia, serif;
    font-size:1.3rem; font-weight:500; color:var(--ink);
    margin:1.2rem 0 .55rem 0;
    display:flex; align-items:center; gap:.5rem;
}
.section-title::before {
    content:''; display:block; width:3px; height:1em;
    background:var(--crimson); border-radius:2px; flex-shrink:0;
}
.section-subtitle { font-size:.88rem; font-weight:600; color:var(--ink); margin:.75rem 0 .5rem 0; }

/* ─────────────────────────────────────────────────────────
   MESSAGE BOXES
───────────────────────────────────────────────────────── */
.msg-box {
    padding:.62rem .88rem; border-radius:var(--r-sm) !important;
    margin:.62rem 0; background:var(--cream);
    border:1px solid var(--border-soft); border-left:3px solid var(--crimson);
    color:var(--ink); line-height:1.55; font-size:.82rem;
}
.msg-box strong { color:var(--ink); }
.msg-success { border-left-color:var(--sage) !important; background:#F0F8F4 !important; }
.msg-info    { border-left-color:#5A6EAF !important;    background:#F2F4FA !important; }
.msg-warning { border-left-color:var(--gold) !important; background:#FBF6EC !important; }

/* ─────────────────────────────────────────────────────────
   SCORE CIRCLE
───────────────────────────────────────────────────────── */
.score-circle {
    width:100px; height:100px; border-radius:50%;
    margin:0 auto;
    display:flex; align-items:center; justify-content:center;
    position:relative; box-shadow:var(--sh-md); transition:transform .2s;
}
.score-circle:hover { transform:scale(1.04); }
.score-circle::before {
    content:''; position:absolute;
    width:74px; height:74px; border-radius:50%; background:var(--paper);
}
.score-circle-inner {
    position:relative; z-index:2;
    font-family:'Cormorant Garamond', Georgia, serif;
    font-size:1.3rem; font-weight:600; color:var(--crimson);
}
.score-circle-good .score-circle-inner { color:var(--sage); }
.score-circle-mid  .score-circle-inner { color:var(--gold); }
.score-circle-low  .score-circle-inner { color:var(--crimson); }

/* ─────────────────────────────────────────────────────────
   KEYWORD CHIPS
───────────────────────────────────────────────────────── */
.keyword-container { display:flex; flex-wrap:wrap; gap:.28rem; margin-top:.48rem; }
.keyword-match, .keyword-miss {
    display:inline-flex; align-items:center;
    padding:.17rem .52rem; border-radius:99px;
    font-size:.67rem; font-weight:500;
    font-family:'DM Mono', monospace;
}
.keyword-match { background:rgba(46,122,86,.08) !important; color:var(--sage) !important; border:1px solid rgba(46,122,86,.20) !important; }
.keyword-miss  { background:rgba(139,26,52,.07) !important; color:var(--crimson) !important; border:1px solid rgba(139,26,52,.15) !important; }

/* ─────────────────────────────────────────────────────────
   BADGES
───────────────────────────────────────────────────────── */
.badge { display:inline-block; padding:.17rem .52rem; border-radius:99px; font-size:.67rem; font-weight:600; letter-spacing:.02em; }
.badge-good { background:rgba(46,122,86,.10) !important; color:var(--sage) !important;    border:1px solid rgba(46,122,86,.20) !important; }
.badge-mid  { background:rgba(184,144,44,.10) !important; color:var(--gold) !important;   border:1px solid rgba(184,144,44,.22) !important; }
.badge-low  { background:rgba(139,26,52,.08) !important;  color:var(--crimson) !important; border:1px solid rgba(139,26,52,.16) !important; }

/* ─────────────────────────────────────────────────────────
   FATWA BOX
───────────────────────────────────────────────────────── */
.fatwa-box {
    background:var(--paper); border-radius:var(--r-md) !important;
    padding:.88rem 1.05rem;
    border:1px solid var(--border-soft) !important;
    box-shadow:var(--sh-sm) !important;
    color:var(--ink); margin-bottom:.62rem;
    transition:box-shadow .2s, transform .2s;
}
.fatwa-box:hover { transform:translateY(-1px); box-shadow:var(--sh-md) !important; }
.fatwa-meta-row  { display:flex; flex-wrap:wrap; gap:.28rem; margin-bottom:.48rem; }
.fatwa-meta-pill {
    display:inline-flex; align-items:center;
    padding:.17rem .48rem; border-radius:4px;
    background:var(--parchment); border:1px solid var(--sand);
    color:var(--ink-mid); font-size:.66rem; font-weight:500;
}
.fatwa-title {
    font-family:'Cormorant Garamond', Georgia, serif;
    font-size:1.05rem; font-weight:500; color:var(--ink);
    margin-bottom:.38rem; line-height:1.3;
}
.fatwa-text-panel {
    background:var(--parchment); border:1px solid var(--sand);
    border-radius:var(--r-sm); padding:.68rem .88rem;
}
.fatwa-text-panel p { margin:0; color:var(--ink); line-height:1.7; font-size:.82rem; white-space:pre-wrap; }

/* ─────────────────────────────────────────────────────────
   INFO GRID
───────────────────────────────────────────────────────── */
.info-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(148px,1fr)); gap:.55rem; }
.info-item { background:var(--cream); padding:.68rem; border-radius:var(--r-sm); border:1px solid var(--border-soft); transition:background .18s; }
.info-item:hover { background:var(--parchment); }
.info-label { font-size:.6rem; font-weight:600; color:var(--ink-soft); text-transform:uppercase; letter-spacing:.08em; margin-bottom:.26rem; }
.info-value { font-size:.87rem; font-weight:600; color:var(--ink); line-height:1.3; }

/* ─────────────────────────────────────────────────────────
   POINTS CARD
───────────────────────────────────────────────────────── */
.points-card {
    background:var(--paper); border-radius:var(--r-md) !important;
    padding:.78rem .98rem;
    border:1px solid var(--border-soft) !important;
    box-shadow:var(--sh-sm) !important; height:100%;
}
.points-card-header {
    font-size:.6rem; font-weight:600; color:var(--ink-soft);
    margin-bottom:.38rem; padding-bottom:.32rem;
    border-bottom:1px solid var(--border-soft);
    text-transform:uppercase; letter-spacing:.08em;
}

/* ─────────────────────────────────────────────────────────
   SMALL NOTE / PLAIN NOTE
───────────────────────────────────────────────────────── */
.small-note      { color:var(--ink-soft); font-size:.76rem; line-height:1.55; }
.system-plain-note { color:var(--ink-soft); font-size:.8rem; line-height:1.6; padding:.5rem 0; margin-bottom:.28rem; }

/* ─────────────────────────────────────────────────────────
   LIGHT TABLE
───────────────────────────────────────────────────────── */
.light-table-wrap { overflow-x:auto; border-radius:var(--r-sm); }
.light-table { width:100%; border-collapse:collapse; font-size:.78rem; min-width:480px; }
.light-table thead th {
    background:var(--ink) !important; color:rgba(255,255,255,.82) !important;
    font-weight:600; font-size:.65rem; letter-spacing:.07em; text-transform:uppercase;
    padding:.58rem .82rem; text-align:left; border-bottom:none;
}
.light-table thead th:first-child { border-radius:var(--r-sm) 0 0 0; }
.light-table thead th:last-child  { border-radius:0 var(--r-sm) 0 0; }
.light-table tbody tr  { border-bottom:1px solid var(--border-soft); }
.light-table tbody tr:last-child { border-bottom:none; }
.light-table tbody tr:hover { background:var(--cream) !important; }
.light-table tbody td { padding:.52rem .82rem; color:var(--ink); vertical-align:middle; }
.light-table-compact td, .light-table-compact th { padding:.42rem .68rem !important; }
.light-table-cell { display:block; }

/* ─────────────────────────────────────────────────────────
   PAGER
───────────────────────────────────────────────────────── */
.pager-bar {
    display:flex; align-items:center; justify-content:space-between;
    gap:.55rem; padding:.38rem .68rem;
    background:var(--paper); border:1px solid var(--border-soft);
    border-radius:var(--r-sm); margin-bottom:.38rem;
}
.pager-note { color:var(--ink-soft); font-size:.72rem; }
.pager-chip {
    display:inline-flex; align-items:center;
    padding:.2rem .58rem; border-radius:99px;
    background:var(--parchment); color:var(--ink-mid);
    border:1px solid var(--border); font-size:.67rem; font-weight:500;
}

/* ─────────────────────────────────────────────────────────
   COMPARISON CARD
───────────────────────────────────────────────────────── */
.comparison-card {
    background:var(--paper); border-radius:var(--r-md);
    padding:.82rem .92rem; border:1px solid var(--border-soft);
    box-shadow:var(--sh-sm); margin-bottom:.58rem; height:100%;
    transition:box-shadow .2s, transform .2s;
}
.comparison-card:hover { transform:translateY(-2px); box-shadow:var(--sh-md); }
.comparison-card-header { font-size:.81rem; font-weight:600; color:var(--ink); margin-bottom:.38rem; padding-bottom:.32rem; border-bottom:1px solid var(--border-soft); line-height:1.3; }

/* ─────────────────────────────────────────────────────────
   ALIGNMENT RANKING
───────────────────────────────────────────────────────── */
.align-panel-title { font-size:.6rem; font-weight:600; color:var(--ink-soft); margin-bottom:.38rem; letter-spacing:.08em; text-transform:uppercase; }
.align-rank-card {
    background:var(--paper); border-radius:var(--r-sm);
    border:1px solid var(--border-soft); box-shadow:var(--sh-sm);
    padding:.58rem .78rem; margin-bottom:.38rem; transition:box-shadow .18s;
}
.align-rank-card:hover { box-shadow:var(--sh-md); }
.align-rank-topic  { font-size:.77rem; font-weight:500; color:var(--ink); margin-bottom:.22rem; line-height:1.4; }
.align-rank-row    { display:flex; align-items:center; gap:.38rem; margin-bottom:.28rem; flex-wrap:wrap; }
.align-score       { font-family:'Cormorant Garamond', Georgia, serif; font-size:1.15rem; font-weight:500; line-height:1; }
.align-band        { font-size:.67rem; font-weight:500; }
.align-n           { font-size:.64rem; color:var(--ink-soft); margin-left:auto; }
.align-bar-bg      { background:var(--parchment); border-radius:99px; height:3px; width:100%; overflow:hidden; }
.align-bar-fill    { height:100%; border-radius:99px; }
.align-full-row    { display:flex; align-items:center; gap:.38rem; padding:.3rem 0 .3rem .28rem; border-bottom:1px solid var(--border-soft); transition:background .15s; }
.align-full-row:hover { background:var(--cream); }
.align-full-rank   { font-size:.67rem; font-weight:500; min-width:1.5rem; color:var(--ink-soft); }
.align-full-topic  { font-size:.79rem; color:var(--ink); min-width:128px; line-height:1.4; }
.align-full-score  { font-size:.81rem; font-weight:600; min-width:2.8rem; text-align:right; }
.align-full-n      { font-size:.64rem; color:var(--ink-soft); min-width:2rem; }

/* ─────────────────────────────────────────────────────────
   DONUT INSIGHT CARDS
───────────────────────────────────────────────────────── */
.donut-insight-card {
    display:flex; align-items:stretch; gap:0;
    background:var(--paper); border-radius:var(--r-sm);
    border:1px solid var(--border-soft); box-shadow:var(--sh-sm);
    margin-bottom:.38rem; overflow:hidden; transition:box-shadow .18s;
}
.donut-insight-card:hover { box-shadow:var(--sh-md); }
.donut-insight-accent { width:3px; min-height:100%; flex-shrink:0; }
.donut-insight-body   { padding:.48rem .78rem; flex:1; }
.donut-insight-name   { font-size:.81rem; font-weight:500; color:var(--ink); margin-bottom:.12rem; }
.donut-insight-stats  { display:flex; align-items:baseline; flex-wrap:wrap; }
.donut-insight-count  { font-family:'Cormorant Garamond', Georgia, serif; font-size:1.25rem; font-weight:500; color:var(--crimson); line-height:1; }
.donut-insight-pct    { font-size:.72rem; color:var(--ink-soft); }

/* ─────────────────────────────────────────────────────────
   BATCH RESULT HELPERS
───────────────────────────────────────────────────────── */
.batch-results-shell {
    background:var(--paper);
    border:1px solid var(--border-soft); border-radius:var(--r-md);
    padding:.82rem .98rem; box-shadow:var(--sh-sm); margin:.62rem 0;
}
.batch-results-title { font-size:.9rem; font-weight:600; color:var(--ink); margin-bottom:.12rem; }
.batch-results-copy, .batch-readable-note { color:var(--ink-soft); font-size:.76rem; line-height:1.55; }
.batch-readable-note, .result-reading-guide {
    background:var(--cream); border:1px solid var(--border-soft);
    border-left:3px solid var(--crimson); border-radius:var(--r-sm);
    padding:.58rem .82rem; margin:.62rem 0;
}
.result-reading-guide-copy { color:var(--ink-soft); font-size:.78rem; line-height:1.55; }
.result-reading-guide-title {
    font-size:.6rem; font-weight:600; letter-spacing:.09em;
    text-transform:uppercase; color:var(--crimson); margin-bottom:.12rem;
}

/* ─────────────────────────────────────────────────────────
   FOOTER
───────────────────────────────────────────────────────── */
.footer-wrap {
    text-align:center; margin-top:2.5rem;
    padding:1.2rem 1.5rem;
    border-top:1px solid var(--border-soft);
}
.footer-wrap p { color:var(--ink-soft); font-size:.72rem; font-family:'DM Sans', sans-serif; line-height:1.55; margin:0; }

/* ─────────────────────────────────────────────────────────
   WORKSPACE SHELL
───────────────────────────────────────────────────────── */
.workspace-shell {
    background:var(--paper);
    border:1px solid var(--border-soft); border-radius:var(--r-md);
    padding:.78rem .92rem; box-shadow:var(--sh-sm); margin-bottom:.58rem;
}
.workspace-kicker { font-size:.6rem; font-weight:600; letter-spacing:.09em; text-transform:uppercase; color:var(--crimson); margin-bottom:.12rem; }
.workspace-title  { font-size:.9rem; color:var(--ink); font-weight:600; margin:0; }
.workspace-copy   { color:var(--ink-soft); font-size:.72rem; line-height:1.55; margin-top:.12rem; }

/* ─────────────────────────────────────────────────────────
   DATASET LOADER CARDS
───────────────────────────────────────────────────────── */
.ds-loader-card, .ds-loader-card-v3, .dataset-loader-minimal {
    background:var(--paper);
    border:1px solid var(--border-soft); border-left:3px solid var(--crimson);
    border-radius:var(--r-md); padding:.82rem .98rem .72rem; margin-bottom:.48rem;
    box-shadow:var(--sh-sm);
}
.ds-loader-v3-kicker, .ds-loader-kicker, .slim-loader-kicker {
    font-size:.6rem; font-weight:600; letter-spacing:.12em;
    text-transform:uppercase; color:var(--crimson); margin-bottom:.12rem;
}
.ds-loader-v3-title, .ds-loader-title, .slim-loader-title {
    font-size:.87rem; font-weight:600; color:var(--ink); line-height:1.2;
}
.ds-loader-v3-badge, .ds-loader-badge {
    display:inline-flex; align-items:center;
    padding:.17rem .52rem; border-radius:99px;
    background:rgba(139,26,52,.08); border:1px solid rgba(139,26,52,.18);
    color:var(--crimson); font-size:.61rem; font-weight:600;
}
.ds-loader-v3-hint, .ds-loader-copy, .slim-loader-copy { font-size:.71rem; color:var(--ink-soft); line-height:1.5; margin-top:.1rem; }
.ds-col-label, .ds-loader-col-label, .dataset-control-caption, .flow-field-label {
    font-size:.6rem; font-weight:600; text-transform:uppercase;
    letter-spacing:.09em; color:var(--ink-soft); margin-bottom:.18rem;
}
.ds-loader-top  { display:flex; align-items:flex-start; justify-content:space-between; gap:.78rem; margin-bottom:.52rem; }
.ds-loader-controls { display:grid; grid-template-columns:1fr 1fr auto; gap:.58rem; align-items:end; }
.ds-loader-divider  { height:1px; background:var(--border-soft); margin:.62rem 0 0; }
.slim-loader-head   { display:flex; justify-content:space-between; align-items:flex-end; gap:.58rem; margin-bottom:.48rem; }
.slim-loader-side   { font-size:.7rem; font-weight:600; color:var(--ink-soft); white-space:nowrap; }

.ds-qa-preview {
    background:var(--parchment); border:1px solid var(--sand);
    border-radius:var(--r-sm); padding:.78rem .92rem; margin:.42rem 0 .18rem;
}
.ds-qa-label  { font-size:.6rem; font-weight:600; text-transform:uppercase; letter-spacing:.1em; margin-bottom:.26rem; display:flex; align-items:center; gap:.32rem; }
.ds-qa-q-label { color:var(--crimson); }
.ds-qa-a-label { color:var(--sage); }
.ds-qa-text   { font-size:.81rem; line-height:1.65; border-radius:var(--r-sm); padding:.48rem .72rem; color:var(--ink); }
.ds-qa-q-text { background:rgba(139,26,52,.05); border-left:2px solid var(--rose); }
.ds-qa-a-text { background:rgba(46,122,86,.05); border-left:2px solid var(--sage); max-height:110px; overflow-y:auto; }
.ds-qa-divider { height:1px; background:var(--sand); margin:.58rem 0; }
.ds-qa-model-chip {
    display:inline-block; background:rgba(139,26,52,.08); color:var(--crimson);
    padding:.1rem .42rem; border-radius:99px;
    font-size:.59rem; font-weight:600; margin-left:.28rem;
    border:1px solid rgba(139,26,52,.15);
}

/* ─────────────────────────────────────────────────────────
   INPUT EDITOR
───────────────────────────────────────────────────────── */
.input-editor-shell, .input-editor-shell-v2 {
    background:var(--paper); border:1px solid var(--border-soft);
    border-radius:var(--r-md); padding:.62rem .88rem .52rem;
    margin:.18rem 0 .38rem; box-shadow:var(--sh-sm);
}
.input-editor-kicker { font-size:.6rem; font-weight:600; text-transform:uppercase; letter-spacing:.09em; color:var(--crimson); margin-bottom:.12rem; }
.input-editor-title  { font-size:.83rem; font-weight:600; color:var(--ink); line-height:1.2; }
.input-editor-chip   { padding:.2rem .58rem; border-radius:99px; background:var(--parchment); border:1px solid var(--sand); color:var(--crimson); font-size:.65rem; font-weight:600; }
.input-editor-head, .input-editor-v2-head, .ds-loader-v3-head { display:flex; justify-content:space-between; align-items:flex-start; gap:.58rem; }
.input-editor-copy   { line-height:1.5; }

.ai-input-card {
    background:var(--paper); border:1px solid var(--border-soft);
    border-radius:var(--r-md); padding:.72rem .98rem .58rem; margin-top:.65rem;
    box-shadow:var(--sh-sm);
}
.ai-input-card--filled   { border-color:var(--blush); }
.ai-input-card-header    { display:flex; justify-content:space-between; align-items:center; gap:.58rem; }
.ai-input-card-header-left { display:flex; align-items:center; gap:.52rem; }
.ai-input-card-icon {
    width:26px; height:26px; background:var(--crimson); border-radius:var(--r-sm);
    display:flex; align-items:center; justify-content:center; font-size:.78rem;
    flex-shrink:0; box-shadow:0 2px 6px rgba(139,26,52,.20);
}
.ai-input-card-kicker { font-size:.57rem; font-weight:600; text-transform:uppercase; letter-spacing:.12em; color:var(--crimson); margin-bottom:.06rem; }
.ai-input-card-title  { font-size:.83rem; font-weight:600; color:var(--ink); }
.ai-input-card-meta   { display:flex; align-items:center; gap:.32rem; flex-wrap:wrap; flex-shrink:0; }
.ai-input-wc, .ai-input-hint-chip {
    padding:.17rem .52rem; border-radius:99px;
    background:var(--parchment); color:var(--ink-mid);
    border:1px solid var(--border); font-size:.61rem; font-weight:500;
}
.ai-input-badge { padding:.17rem .52rem; border-radius:99px; background:var(--crimson); color:#fff; font-size:.61rem; font-weight:600; }

/* ─────────────────────────────────────────────────────────
   BATCH / FILTER SHELLS
───────────────────────────────────────────────────────── */
.batch-shell, .batch-filter-grid {
    background:var(--paper); border:1px solid var(--border-soft);
    border-radius:var(--r-md); padding:.58rem .82rem .52rem;
    box-shadow:var(--sh-sm); margin:.1rem 0 .48rem;
}
.batch-kicker { font-size:.6rem; font-weight:600; letter-spacing:.09em; text-transform:uppercase; color:var(--crimson); margin-bottom:.1rem; }
.batch-title  { font-size:.87rem; font-weight:600; color:var(--ink); line-height:1.15; }
.batch-copy   { color:var(--ink-soft); font-size:.72rem; line-height:1.5; }
.batch-shell-head { display:flex; justify-content:space-between; align-items:flex-start; gap:.58rem; }
.batch-selection-note {
    background:var(--cream); border:1px solid var(--border-soft);
    border-radius:var(--r-sm); padding:.48rem .72rem;
    color:var(--ink-soft); font-size:.72rem; line-height:1.45; margin:.38rem 0;
}
.batch-selection-note strong { color:var(--ink); }

/* ─────────────────────────────────────────────────────────
   CHART PANEL
───────────────────────────────────────────────────────── */
.chart-panel {
    background:var(--paper); border:1px solid var(--border-soft);
    border-radius:var(--r-md); padding:.82rem .98rem .72rem;
    box-shadow:var(--sh-sm); margin:.62rem 0 .48rem;
}
.chart-panel-title { font-size:.87rem; font-weight:600; color:var(--ink); margin-bottom:.12rem; }
.chart-panel-copy  { color:var(--ink-soft); font-size:.75rem; line-height:1.5; }
.chart-conclusion  {
    margin-top:.48rem; padding:.58rem .78rem; border-radius:var(--r-sm);
    background:var(--cream); border:1px solid var(--border-soft);
    color:var(--ink-soft); font-size:.75rem; line-height:1.55;
}

/* ─────────────────────────────────────────────────────────
   LEADERBOARD
───────────────────────────────────────────────────────── */
.leaderboard-card {
    background:var(--paper); border:1px solid var(--border-soft);
    border-radius:var(--r-sm); padding:.68rem .82rem;
    display:flex; align-items:center; gap:.68rem;
    box-shadow:var(--sh-sm); transition:box-shadow .18s;
}
.leaderboard-card:hover   { box-shadow:var(--sh-md); }
.leaderboard-card-top     { border-left:3px solid var(--gold); }
.leaderboard-rank         { font-size:1.2rem; width:26px; text-align:center; flex-shrink:0; }
.leaderboard-main         { flex:1; min-width:0; }
.leaderboard-title        { font-size:.82rem; font-weight:600; color:var(--ink); margin-bottom:.12rem; }
.leaderboard-meta         { font-size:.67rem; color:var(--ink-soft); margin-bottom:.32rem; }
.leaderboard-track        { height:3px; background:var(--parchment); border-radius:99px; overflow:hidden; }
.leaderboard-fill         { height:100%; background:var(--crimson); border-radius:99px; }
.leaderboard-side         { text-align:right; flex-shrink:0; }
.leaderboard-score        { font-family:'Cormorant Garamond', Georgia, serif; font-size:1.3rem; font-weight:500; color:var(--crimson); line-height:1; }
.leaderboard-note         { font-size:.64rem; color:var(--ink-soft); margin-top:.12rem; }

/* ─────────────────────────────────────────────────────────
   EXPLORER CARDS
───────────────────────────────────────────────────────── */
.explorer-instruction-card {
    background:var(--paper); border:1px solid var(--border-soft);
    border-left:3px solid var(--crimson); border-radius:var(--r-md);
    padding:.72rem .98rem; margin:.38rem 0 .62rem; box-shadow:var(--sh-sm);
}
.explorer-instruction-title { font-size:.6rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--crimson); margin-bottom:.22rem; }
.explorer-instruction-copy  { font-size:.81rem; line-height:1.65; color:var(--ink-soft); }
.explorer-orb-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.65rem; margin:.62rem 0 .82rem; }
.explorer-orb {
    background:var(--paper); border:1px solid var(--border-soft);
    border-radius:var(--r-md); padding:.58rem .78rem;
    display:flex; align-items:center; gap:.58rem;
    box-shadow:var(--sh-sm); min-height:60px; transition:box-shadow .2s;
}
.explorer-orb:hover { box-shadow:var(--sh-md); }
.explorer-orb-icon {
    width:30px; height:30px; border-radius:var(--r-sm);
    display:flex; align-items:center; justify-content:center;
    background:var(--crimson); color:#fff; font-weight:700; font-size:.74rem;
    box-shadow:0 2px 8px rgba(139,26,52,.20); flex-shrink:0;
}
.explorer-orb-label { font-size:.57rem; font-weight:600; letter-spacing:.09em; text-transform:uppercase; color:var(--ink-soft); margin-bottom:.08rem; }
.explorer-orb-value { font-family:'Cormorant Garamond', Georgia, serif; font-size:1.02rem; font-weight:500; color:var(--ink); line-height:1.05; }

/* ─────────────────────────────────────────────────────────
   TOPIC PICK / FOCUS
───────────────────────────────────────────────────────── */
.topic-pick-shell {
    background:var(--paper); border:1px solid var(--border-soft);
    border-radius:var(--r-md); padding:.88rem .98rem; margin-bottom:.65rem; box-shadow:var(--sh-sm);
}
.topic-pick-kicker { font-size:.6rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--crimson); margin-bottom:.18rem; }
.topic-pick-title  { font-family:'Cormorant Garamond', Georgia, serif; font-size:1.2rem; font-weight:500; color:var(--ink); margin-bottom:.18rem; }
.topic-pick-copy   { font-size:.77rem; color:var(--ink-soft); line-height:1.6; }
.topic-focus-grid  { display:grid; grid-template-columns:repeat(4,1fr); gap:.55rem; margin:.55rem 0; }
.topic-focus-card  { background:var(--paper); border:1px solid var(--border-soft); border-radius:var(--r-sm); padding:.62rem .72rem; box-shadow:var(--sh-sm); text-align:center; }
.topic-focus-label { font-size:.6rem; font-weight:600; color:var(--ink-soft); letter-spacing:.08em; text-transform:uppercase; margin-bottom:.18rem; }
.topic-focus-value { font-family:'Cormorant Garamond', Georgia, serif; font-size:1.3rem; font-weight:500; color:var(--crimson); }

/* ─────────────────────────────────────────────────────────
   COMPARISON SELECT HEAD
───────────────────────────────────────────────────────── */
.comparison-select-head   { display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; margin-bottom:.58rem; }
.comparison-select-title  { font-size:.87rem; font-weight:600; color:var(--ink); margin-bottom:.1rem; }
.comparison-select-copy   { font-size:.72rem; color:var(--ink-soft); line-height:1.5; }

/* ─────────────────────────────────────────────────────────
   HISTORY TABLE
───────────────────────────────────────────────────────── */
.history-table-shell {
    background:var(--paper); border:1px solid var(--border-soft);
    border-radius:var(--r-md); padding:.82rem .98rem;
    box-shadow:var(--sh-sm); margin-bottom:.62rem;
}
.history-table-head  { display:flex; justify-content:space-between; align-items:flex-start; gap:.78rem; margin-bottom:.62rem; }
.history-table-title { font-size:.88rem; font-weight:600; color:var(--ink); margin-bottom:.12rem; }
.history-table-copy  { font-size:.72rem; color:var(--ink-soft); line-height:1.5; }
.history-table-pill  {
    padding:.2rem .62rem; border-radius:99px; white-space:nowrap;
    background:var(--parchment); border:1px solid var(--border);
    color:var(--ink-mid); font-size:.64rem; font-weight:600;
}

/* ─────────────────────────────────────────────────────────
   DIVIDERS
───────────────────────────────────────────────────────── */
.divider      { height:1px; background:var(--border-soft); margin:1.15rem 0; }
.soft-divider { height:1px; background:var(--border-soft); margin:.48rem 0; }

/* ─────────────────────────────────────────────────────────
   INLINE FLOW / STEP WIZARD
───────────────────────────────────────────────────────── */
.flow-steps-line { display:grid; grid-template-columns:repeat(3,auto); justify-content:start; gap:.58rem; margin-bottom:.65rem; }
.flow-step-mini  { display:flex; align-items:center; gap:.32rem; font-size:.7rem; color:var(--ink-soft); font-weight:500; }
.flow-step-mini.is-active { color:var(--crimson); font-weight:600; }
.flow-step-dot {
    width:20px; height:20px; border-radius:50%;
    background:var(--parchment); border:1px solid var(--border);
    display:flex; align-items:center; justify-content:center;
    font-size:.61rem; font-weight:700; color:var(--ink-soft); flex-shrink:0;
}
.flow-step-mini.is-active .flow-step-dot { background:var(--crimson); border-color:var(--crimson); color:#fff; }
.flow-selected-preview {
    display:flex; justify-content:space-between; align-items:flex-start; gap:.48rem;
    background:var(--parchment); border:1px solid var(--sand);
    border-radius:var(--r-sm); padding:.52rem .72rem; margin:.48rem 0 .58rem;
}
.flow-selected-kicker   { font-size:.6rem; font-weight:600; text-transform:uppercase; letter-spacing:.09em; color:var(--ink-soft); margin-bottom:.1rem; }
.flow-selected-question { font-size:.79rem; color:var(--ink); font-weight:500; line-height:1.4; }
.flow-selected-chip     { padding:.17rem .52rem; border-radius:99px; white-space:nowrap; background:var(--crimson); color:#fff; font-size:.61rem; font-weight:600; flex-shrink:0; align-self:flex-start; }
.flow-action-cell       { display:flex; align-items:flex-end; height:100%; }

/* ─────────────────────────────────────────────────────────
   TAB 1 SECTION HEADERS
───────────────────────────────────────────────────────── */
.tab1-section         { margin:.28rem 0 .48rem; }
.tab1-section-header  { display:flex; align-items:center; gap:.58rem; min-height:30px; }
.tab1-section-step    {
    width:24px; height:24px; border-radius:var(--r-sm);
    background:var(--crimson); color:#fff;
    display:flex; align-items:center; justify-content:center;
    font-size:.7rem; font-weight:700; flex-shrink:0;
}
.tab1-section-title    { font-size:.88rem; font-weight:600; color:var(--ink); letter-spacing:-.01em; }
.tab1-section-subtitle { font-size:.74rem; color:var(--ink-soft); }
.tab1-section-rule     { flex:1; height:1px; background:var(--border-soft); }
.mode-choice-wrap      { margin-bottom:.58rem; }

/* ─────────────────────────────────────────────────────────
   LOADED ANSWER PANEL
───────────────────────────────────────────────────────── */
.loaded-answer-panel {
    background:var(--parchment); border:1px solid var(--sand);
    border-left:3px solid var(--crimson);
    border-radius:var(--r-md); padding:.72rem .88rem; margin-top:.65rem; min-height:78px;
}
.loaded-answer-panel-title {
    font-size:.6rem; font-weight:600; letter-spacing:.09em;
    text-transform:uppercase; color:var(--crimson); margin-bottom:.32rem;
    display:flex; align-items:center; gap:.38rem;
}
.loaded-answer-text { font-size:.79rem; line-height:1.65; color:var(--ink); white-space:pre-wrap; max-height:128px; overflow-y:auto; }

/* ─────────────────────────────────────────────────────────
   EMPTY REVIEW CARD
───────────────────────────────────────────────────────── */
.empty-review-card   { background:var(--paper); border:1px solid var(--border-soft) !important; border-radius:var(--r-md) !important; box-shadow:var(--sh-sm) !important; padding:1.2rem; }
.empty-review-top    { display:flex; align-items:flex-start; justify-content:space-between; gap:.78rem; margin-bottom:.95rem; }
.empty-review-title  { font-family:'Cormorant Garamond', Georgia, serif; font-size:1.3rem; font-weight:500; color:var(--ink); margin:.12rem 0; }
.empty-review-copy   { font-size:.75rem; color:var(--ink-soft); line-height:1.55; }
.empty-review-pill   { padding:.22rem .68rem; border-radius:99px; background:var(--parchment); border:1px solid var(--border); color:var(--ink-soft); font-size:.64rem; font-weight:600; white-space:nowrap; }
.empty-guide         { display:grid; gap:.55rem; }
.empty-guide-item    { display:flex; gap:.58rem; align-items:flex-start; padding:.58rem .72rem; border-radius:var(--r-sm); background:var(--cream); border:1px solid var(--border-soft); }
.empty-guide-num     { width:20px; height:20px; border-radius:50%; flex-shrink:0; background:var(--crimson); color:#fff; display:flex; align-items:center; justify-content:center; font-size:.63rem; font-weight:700; }
.empty-guide-title   { font-size:.77rem; font-weight:600; color:var(--ink); margin-bottom:.08rem; }
.empty-guide-copy    { font-size:.69rem; color:var(--ink-soft); line-height:1.5; }

/* ─────────────────────────────────────────────────────────
   ACTION BAR
───────────────────────────────────────────────────────── */
.action-bar-modern {
    display:grid; grid-template-columns:minmax(0,1fr) 200px;
    gap:.68rem; align-items:center; margin-top:.78rem;
    background:var(--paper); border:1px solid var(--border-soft);
    border-radius:var(--r-md); padding:.68rem; box-shadow:var(--sh-sm);
}
.action-hint { font-size:.77rem; color:var(--ink-soft); line-height:1.45; padding-left:.28rem; }

/* ─────────────────────────────────────────────────────────
   SCORE / REVIEW PANES
───────────────────────────────────────────────────────── */
.review-left-shell, .score-shell {
    background:var(--paper); border:1px solid var(--border-soft);
    border-radius:var(--r-md); padding:.68rem .82rem; box-shadow:var(--sh-sm);
}
.pane-title-row { display:flex; align-items:center; justify-content:space-between; gap:.68rem; margin-bottom:.38rem; }
.pane-kicker { font-size:.6rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--crimson); margin-bottom:.15rem; }
.pane-title  { font-size:.9rem; font-weight:600; color:var(--ink); }
.pane-copy   { font-size:.69rem; color:var(--ink-soft); line-height:1.35; margin-top:.1rem; }
.pane-chip   { padding:.26rem .62rem; border-radius:99px; background:var(--crimson); color:#fff; font-size:.61rem; font-weight:600; }

/* ─────────────────────────────────────────────────────────
   DETAIL TOGGLE / DRAWER
───────────────────────────────────────────────────────── */
.detail-toggle-card, .detail-inline-card {
    background:var(--paper);
    border:1px solid var(--border-soft); border-left:3px solid var(--crimson);
    border-radius:var(--r-md); padding:.78rem .92rem;
    box-shadow:var(--sh-sm); margin:.78rem 0 .28rem;
    display:flex; align-items:center; gap:.82rem;
    transition:box-shadow .18s;
}
.detail-toggle-card-open, .detail-inline-card--open { box-shadow:var(--sh-md); }
.detail-toggle-icon, .detail-inline-icon {
    width:32px; height:32px; border-radius:var(--r-sm); flex-shrink:0;
    display:flex; align-items:center; justify-content:center;
    background:var(--crimson); color:#fff; font-size:.86rem; font-weight:700;
    box-shadow:0 2px 8px rgba(139,26,52,.20);
}
.detail-toggle-kicker, .detail-inline-kicker { font-size:.57rem; font-weight:600; letter-spacing:.10em; text-transform:uppercase; color:var(--crimson); margin-bottom:.08rem; }
.detail-toggle-title, .detail-inline-title   { font-size:.88rem; font-weight:600; color:var(--ink); line-height:1.2; }
.detail-toggle-sub, .detail-inline-sub       { font-size:.69rem; color:var(--ink-soft); margin-top:.08rem; }
.detail-toggle-chips, .detail-inline-chips   { display:flex; gap:.32rem; flex-wrap:wrap; margin-left:auto; flex-shrink:0; }
.detail-chip          { padding:.2rem .52rem; border-radius:99px; background:var(--paper); border:1px solid var(--border); color:var(--crimson); font-size:.64rem; font-weight:600; white-space:nowrap; }
.detail-chip--state   { background:var(--crimson); color:#fff; border-color:transparent; }
.detail-inline-left   { display:flex; align-items:center; gap:.62rem; flex:1; min-width:0; }
.detail-drawer-body   { margin-top:.22rem; padding:.72rem; border:1px solid var(--border-soft); border-radius:var(--r-lg); background:var(--cream); }
.detail-toggle-button-wrap .stButton > button {
    min-height:60px !important; border-radius:var(--r-lg) !important;
    background:var(--ink) !important;
    box-shadow:var(--sh-md) !important;
    font-size:.76rem !important; font-weight:600 !important;
}

/* ─────────────────────────────────────────────────────────
   RESULT CARDS
───────────────────────────────────────────────────────── */
.result-card {
    background:var(--paper); border:1px solid var(--border-soft);
    border-radius:var(--r-md); padding:.82rem .92rem;
    box-shadow:var(--sh-sm); position:relative; overflow:hidden; height:100%;
}
.result-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; }
.result-card-good::before { background:var(--sage); }
.result-card-mid::before  { background:var(--gold); }
.result-card-low::before  { background:var(--crimson); }
.result-card-title { font-size:.63rem; font-weight:600; color:var(--ink-soft); text-transform:uppercase; letter-spacing:.08em; margin-bottom:.38rem; }
.result-card-score { font-family:'Cormorant Garamond', Georgia, serif; font-size:2rem; font-weight:500; line-height:1; }
.result-card-text  { font-size:.72rem; color:var(--ink-soft); line-height:1.55; margin-top:.38rem; }

/* ─────────────────────────────────────────────────────────
   SIM BREAKDOWN  (sbd-)
───────────────────────────────────────────────────────── */
.sbd-stack { width:100%; }
.sbd-card  {
    width:100%; box-sizing:border-box;
    background:var(--paper); border:1px solid var(--border-soft);
    border-radius:var(--r-xl); padding:1rem 1.1rem; box-shadow:var(--sh-md);
}
.sbd-header  { display:flex; justify-content:space-between; align-items:flex-start; gap:.68rem; margin-bottom:.72rem; }
.sbd-kicker  { font-size:.6rem; font-weight:600; text-transform:uppercase; letter-spacing:.12em; color:var(--crimson); margin-bottom:.12rem; }
.sbd-title   { font-family:'Cormorant Garamond', Georgia, serif; font-size:1.4rem; font-weight:500; color:var(--ink); letter-spacing:-.01em; line-height:1; }
.sbd-pill    { padding:.23rem .68rem; border-radius:99px; border:1px solid; font-weight:600; font-size:.72rem; white-space:nowrap; }
.sbd-hero    { display:grid; grid-template-columns:96px minmax(0,1fr); gap:.88rem; align-items:center; padding:.62rem 0 .82rem; }
.sbd-ring    { width:94px; height:94px; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow:var(--sh-md); flex-shrink:0; }
.sbd-ring-inner {
    width:66px; height:66px; border-radius:50%; background:var(--paper);
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    box-shadow:inset 0 0 0 1px rgba(26,10,18,.06);
}
.sbd-ring-inner strong { font-family:'Cormorant Garamond', Georgia, serif; font-size:1.62rem; font-weight:500; line-height:1; }
.sbd-ring-inner span   { font-size:.57rem; color:var(--ink-soft); margin-top:.08rem; font-weight:500; }
.sbd-verdict-label { font-size:.9rem; font-weight:600; margin-bottom:.2rem; line-height:1.12; }
.sbd-verdict-copy  { font-size:.74rem; color:var(--ink-soft); line-height:1.58; }
.sbd-soft-line     { height:1px; background:var(--border-soft); margin:.12rem 0 .68rem; }
.sbd-metric-grid   { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.52rem; }
.sbd-metric-inline {
    min-width:0; padding:.62rem;
    border:1px solid var(--border-soft); border-radius:var(--r-md);
    background:var(--cream); box-shadow:var(--sh-sm);
}
.sbd-mini-top    { display:flex; justify-content:space-between; align-items:center; gap:.28rem; margin-bottom:.42rem; }
.sbd-mini-icon   { width:24px; height:24px; border-radius:var(--r-sm); display:inline-flex; align-items:center; justify-content:center; background:var(--parchment); color:var(--crimson); font-size:.68rem; font-weight:700; flex-shrink:0; }
.sbd-mini-status { display:inline-flex; align-items:center; padding:.11rem .36rem; border-radius:99px; border:1px solid; font-size:.51rem; font-weight:700; letter-spacing:.04em; text-transform:uppercase; }
.sbd-mini-label  { font-size:.55rem; font-weight:600; letter-spacing:.09em; text-transform:uppercase; color:var(--ink-soft); }
.sbd-mini-value  { font-family:'Cormorant Garamond', Georgia, serif; font-size:1.42rem; font-weight:500; line-height:1; margin:.22rem 0 .06rem; }
.sbd-mini-sub    { font-size:.55rem; color:var(--ink-soft); font-weight:500; padding-bottom:.28rem; margin-bottom:.28rem; border-bottom:1px solid var(--border-soft); }
.sbd-mini-desc   { font-size:.65rem; line-height:1.35; color:var(--ink-soft); }
.sbd-read-box    { margin-top:.68rem; border:1px solid var(--border-soft); border-radius:var(--r-sm); padding:.58rem .72rem; background:var(--parchment); display:flex; align-items:center; gap:.62rem; }
.sbd-read-label  { flex:0 0 auto; display:inline-flex; align-items:center; border-radius:99px; padding:.18rem .58rem; background:var(--crimson); color:#fff; font-size:.59rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; }
.sbd-read-copy   { font-size:.71rem; color:var(--ink-soft); line-height:1.48; }

/* ─────────────────────────────────────────────────────────
   FATWA REFERENCE CARD
───────────────────────────────────────────────────────── */
.fatwa-ref-card    { background:var(--paper); border:1px solid var(--border-soft); border-radius:var(--r-md); padding:.82rem .98rem; box-shadow:var(--sh-sm); height:100%; }
.fatwa-ref-kicker  { font-size:.6rem; font-weight:600; text-transform:uppercase; letter-spacing:.1em; color:var(--crimson); margin-bottom:.18rem; }
.fatwa-ref-title   { font-family:'Cormorant Garamond', Georgia, serif; font-size:1.05rem; font-weight:500; color:var(--ink); margin-bottom:.38rem; }
.fatwa-ref-source  { font-size:.67rem; color:var(--ink-soft); margin-bottom:.58rem; }
.fatwa-ref-text    { font-size:.79rem; line-height:1.7; color:var(--ink); }

/* ─────────────────────────────────────────────────────────
   BROWSE / FILTER
───────────────────────────────────────────────────────── */
.browse-inline-head { font-size:.64rem; font-weight:600; letter-spacing:.07em; text-transform:uppercase; color:var(--ink-soft); margin:0 0 .26rem .08rem; }
.browse-filter-chip-row { display:flex; flex-wrap:wrap; gap:.32rem; margin:.38rem 0 .62rem; }
.browse-filter-chip {
    display:inline-flex; align-items:center;
    padding:.22rem .62rem; border-radius:99px;
    background:var(--parchment); color:var(--ink-mid);
    border:1px solid var(--border); font-size:.69rem; font-weight:500;
    transition:background .15s;
}
.browse-filter-chip:hover { background:var(--sand); }

/* ─────────────────────────────────────────────────────────
   BATCH GUIDE CARD
───────────────────────────────────────────────────────── */
.batch-guide-card { background:var(--paper); border:1px solid var(--border-soft); border-left:3px solid var(--crimson); border-radius:var(--r-md); padding:.82rem .98rem; box-shadow:var(--sh-sm); }
.batch-guide-kicker { font-size:.6rem; font-weight:600; letter-spacing:.10em; text-transform:uppercase; color:var(--crimson); margin-bottom:.48rem; }
.batch-guide-step  { display:flex; gap:.42rem; align-items:flex-start; font-size:.79rem; line-height:1.55; color:var(--ink-soft); margin-bottom:.38rem; }
.batch-guide-step strong { color:var(--crimson); font-size:.82rem; flex-shrink:0; }

/* ─────────────────────────────────────────────────────────
   TECH REVIEW TITLE
───────────────────────────────────────────────────────── */
.tech-review-title { font-size:.7rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:var(--ink-soft); margin:.65rem 0 .28rem; }

/* ─────────────────────────────────────────────────────────
   GRADIENT UTILITY
───────────────────────────────────────────────────────── */
.gradient-text {
    background:linear-gradient(135deg, var(--crimson) 0%, var(--rose) 60%);
    -webkit-background-clip:text; background-clip:text;
    color:transparent; display:inline-block;
}

/* ─────────────────────────────────────────────────────────
   RESPONSIVE
───────────────────────────────────────────────────────── */
@media (max-width:1200px) {
    [data-testid="stSidebar"] { min-width:250px !important; max-width:250px !important; width:250px !important; }
    .sbd-metric-grid { grid-template-columns:repeat(2,minmax(0,1fr)) !important; }
}
@media (max-width:1100px) {
    .explorer-orb-grid { grid-template-columns:1fr !important; }
    .topic-focus-grid  { grid-template-columns:1fr 1fr !important; }
    .sbd-hero          { grid-template-columns:1fr !important; }
    .sbd-ring          { margin:0 auto !important; }
}
@media (max-width:900px) {
    .action-bar-modern { grid-template-columns:1fr !important; }
    .topic-focus-grid  { grid-template-columns:1fr 1fr !important; }
    [data-testid="stRadio"] [role="radiogroup"] { grid-template-columns:1fr !important; }
    .light-table { min-width:480px; }
}
@media (max-width:768px) {
    .block-container { padding-left:.6rem !important; padding-right:.6rem !important; }
    .dash-header-title { font-size:1.6rem !important; }
    .dash-header-overlay-img, .dash-header-overlay-plain { padding:1.4rem 1.4rem; }
    .topic-focus-grid  { grid-template-columns:1fr !important; }
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# UI HELPERS
# =========================================================

def explain_score_band(score):
    tier = get_score_tier(score)
    if tier == "good":
        return "✅ High Alignment — The AI answer closely matches the fatwa guidance and is considered reliable. The response captures the key ruling and important conditions."
    if tier == "moderate":
        return "⚠️ Moderate Alignment — The AI answer partially matches the fatwa. Some key rulings or conditions are missing or imprecise. Review before relying on this response."
    return "❌ Low Alignment — The AI answer does not closely match the fatwa guidance. It is not reliable and should not be used without significant correction."

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
    colour = score_color(score)
    band = score_css_band(score)
    classes = f"result-card-score result-card-score-{band} {extra_class}".strip()
    try:
        display = f"{float(score):.1f}{suffix}"
    except Exception:
        display = f"-{suffix}"
    return f'<span class="{classes}" style="color:{colour};">{display}</span>'


def render_result_card_html(title: str, score: float, description: str = "") -> str:
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
    colour = score_color(score)
    band = score_css_band(score)
    try:
        display = f"{float(score):.1f}%"
    except Exception:
        display = "-"
    return f'<span class="align-score align-score-{band}" style="color:{colour};">{display}</span>'


def render_metric_card_html(label: str, value: float, description: str = "", is_score: bool = True) -> str:
    band = score_css_band(value) if is_score else "info"
    colour = score_color(value) if is_score else COLORS["ink"]
    try:
        display = f"{float(value):.1f}%"
    except Exception:
        display = "-"
    stripe_class = f"metric-card metric-card-{band}" if is_score else "metric-card"
    desc_html = f'<div class="small-note" style="margin-top:.3rem;">{html.escape(description)}</div>' if description else ""
    return (
        f'<div class="{stripe_class}">'
        f'  <div class="metric-label">{html.escape(label)}</div>'
        f'  <div class="metric-value metric-value-{band}" style="color:{colour};">{display}</div>'
        f'  {desc_html}'
        f'</div>'
    )


def show_success_toast_center(title: str, lines: list = None, duration_ms: int = 3200):
    lines = lines or []
    lines_html = "".join(
        f'<div style="font-size:.76rem;color:rgba(255,255,255,.80);margin-top:.18rem;line-height:1.5;">{html.escape(l)}</div>'
        for l in lines
    )
    toast_html = f"""
    <div id="ct-toast" style="
        position:fixed; top:50%; left:50%; transform:translate(-50%,-50%) scale(1);
        background:var(--ink, #1A0A12);
        border:1px solid rgba(255,255,255,.10);
        border-top:2px solid #B8902C;
        border-radius:14px;
        padding:1.1rem 1.5rem;
        min-width:280px; max-width:420px;
        box-shadow:0 24px 60px rgba(26,10,18,.35), 0 8px 20px rgba(26,10,18,.20);
        z-index:99999;
        text-align:center;
        animation:slideInDown .3s cubic-bezier(.22,.68,0,1.2) forwards;
        font-family:'DM Sans',sans-serif;
    ">
      <div style="font-size:.9rem;font-weight:600;color:#FFF;margin-bottom:.1rem;">{html.escape(title)}</div>
      {lines_html}
    </div>
    <script>
    (function(){{
        setTimeout(function(){{
            var t=document.getElementById('ct-toast');
            if(t){{
                t.style.animation='fadeOutUp .3s ease forwards';
                setTimeout(function(){{if(t)t.remove();}},320);
            }}
        }},{duration_ms});
    }})();
    </script>
    """
    components_html(toast_html, height=0)


def render_hero_banner(title: str, subtitle: str, kicker: str = "", image_path: str = None):
    img_uri = _image_to_data_uri(image_path) if image_path else None
    img_tag = f'<img src="{img_uri}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.55;" />' if img_uri else ""
    overlay_class = "dash-header-overlay-img" if img_uri else "dash-header-overlay-plain"
    kicker_html = f'<div class="dash-header-kicker">{html.escape(kicker)}</div>' if kicker else ""
    html_block = f"""
    <div class="dash-header-wrap">
        {img_tag}
        <div class="{overlay_class}">
            <div class="dash-header-left">
                {kicker_html}
                <div class="dash-header-title">{html.escape(title)}</div>
                <div class="dash-header-subtitle">{html.escape(subtitle)}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html_block, unsafe_allow_html=True)


def render_sidebar_profile(title: str, subtitle: str):
    profile_html = f"""
    <div class="sidebar-brand-card">
        <div class="sidebar-brand-title">{html.escape(title)}</div>
        <div class="sidebar-brand-subtitle">{html.escape(subtitle)}</div>
    </div>
    """
    st.markdown(profile_html, unsafe_allow_html=True)


def render_sidebar_section_header(label: str, icon: str = ""):
    icon_html = f'<span>{html.escape(icon)}</span>' if icon else ""
    section_html = f"""
    <div class="sidebar-section-title">
        {icon_html}{html.escape(label)}
    </div>
    """
    st.markdown(section_html, unsafe_allow_html=True)


def render_tab_hero(kicker: str, title: str, copy: str = ""):
    copy_html = f'<div class="tab-minimal-copy">{html.escape(copy)}</div>' if copy else ""
    html_block = f"""
    <div class="tab-minimal-hero">
        <div class="tab-minimal-kicker">{html.escape(kicker)}</div>
        <div class="tab-minimal-title">{html.escape(title)}</div>
        {copy_html}
    </div>
    """
    st.markdown(html_block, unsafe_allow_html=True)


def render_section_banner(title: str, subtitle: str = "", image_path: str = None, height: int = 72):
    img_uri = _image_to_data_uri(image_path) if image_path else None
    img_tag = f'<img src="{img_uri}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.45;" />' if img_uri else ""
    sub_html = f'<div style="color:rgba(255,255,255,.62);font-size:.76rem;margin-top:.22rem;">{html.escape(subtitle)}</div>' if subtitle else ""
    html_block = f"""
    <div class="section-banner" style="min-height:{height}px;">
        {img_tag}
        <div style="position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;padding:1rem 1.4rem;background:linear-gradient(108deg,rgba(26,10,18,.96) 0%,rgba(61,26,40,.85) 55%,rgba(26,10,18,.45) 100%);z-index:2;">
            <div class="section-banner-title">{html.escape(title)}</div>
            {sub_html}
        </div>
    </div>
    """
    st.markdown(html_block, unsafe_allow_html=True)


# ─── Plotly theme helpers ────────────────────────────────────────────────────

def _plotly_base_layout(height: int, title: str = "") -> dict:
    return dict(
        title=title,
        height=height,
        margin=dict(l=12, r=12, t=38 if title else 12, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=COLORS["ink"], size=11),
    )


def render_bar_chart(
    labels: list, values: list,
    title: str = "", height: int = 280,
    color_by_tier: bool = True,
):
    colors = []
    for v in values:
        tier = get_score_tier(v)
        colors.append({"good": COLORS["sage"], "moderate": COLORS["gold"]}.get(tier, COLORS["crimson"]))

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors if color_by_tier else COLORS["crimson"],
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    layout = _plotly_base_layout(height, title)
    layout.update(
        xaxis=dict(gridcolor=COLORS["border_soft"], tickfont=dict(size=10)),
        yaxis=dict(range=[0, 100], gridcolor=COLORS["border_soft"], tickfont=dict(size=10)),
        bargap=0.35,
    )
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def render_radar_chart(categories: dict, title: str = "Performance by Category", height: int = 340):
    labels = list(categories.keys())
    values = list(categories.values())
    fig = go.Figure(data=go.Scatterpolar(
        r=values, theta=labels, fill='toself',
        marker=dict(color=COLORS["rose"], size=5),
        line=dict(color=COLORS["crimson"], width=2),
        hovertemplate="%{theta}: %{r:.1f}%<extra></extra>",
    ))
    layout = _plotly_base_layout(height, title)
    layout.update(polar=dict(
        radialaxis=dict(visible=True, range=[0, 100], gridcolor=COLORS["border_soft"]),
        angularaxis=dict(gridcolor=COLORS["border_soft"], linecolor=COLORS["border_soft"]),
    ))
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def render_timeline_chart(data: list, x_key: str, y_key: str, title: str = "Trend Over Time", height: int = 280):
    x_values = [item[x_key] for item in data]
    y_values = [item[y_key] for item in data]
    latest = y_values[-1] if y_values else 0
    tier = get_score_tier(latest)
    line_color = {"good": COLORS["sage"], "moderate": COLORS["gold"]}.get(tier, COLORS["crimson"])
    r, g, b = int(line_color[1:3], 16), int(line_color[3:5], 16), int(line_color[5:7], 16)
    fig = go.Figure(go.Scatter(
        x=x_values, y=y_values,
        mode='lines+markers',
        line=dict(color=line_color, width=2),
        marker=dict(size=5, color=line_color),
        fill='tozeroy',
        fillcolor=f"rgba({r},{g},{b},0.08)",
        hovertemplate="Date: %{x}<br>Score: %{y:.1f}%<extra></extra>",
    ))
    layout = _plotly_base_layout(height, title)
    layout.update(
        xaxis=dict(gridcolor=COLORS["border_soft"], tickfont=dict(size=10)),
        yaxis=dict(range=[0, 100], gridcolor=COLORS["border_soft"], tickfont=dict(size=10)),
    )
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def render_donut_chart(values: dict, title: str = "Distribution", height: int = 250):
    labels = list(values.keys())
    sizes  = list(values.values())
    color_map = {
        "Good": COLORS["sage"], "High Alignment": COLORS["sage"],
        "Moderate": COLORS["gold"], "Moderate Alignment": COLORS["gold"],
        "Weak": COLORS["crimson"], "Low Alignment": COLORS["crimson"], "Low": COLORS["crimson"],
    }
    colors = [color_map.get(l, COLORS["rose"]) for l in labels]
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=sizes, hole=0.42,
        marker_colors=colors,
        textinfo='label+percent', textposition='auto',
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    )])
    layout = _plotly_base_layout(height, title)
    layout.update(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5, font=dict(size=10)),
    )
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


# ─── Skeleton / loading ──────────────────────────────────────────────────────

def render_skeleton_loader(height: int = 80, width: str = "100%", count: int = 1):
    skeletons = []
    for _ in range(count):
        skeletons.append(
            f'<div style="height:{height}px;width:{width};border-radius:8px;'
            f'background:linear-gradient(90deg,var(--border-soft,#EDE5DC) 25%,var(--cream,#FBF7F3) 50%,var(--border-soft,#EDE5DC) 75%);'
            f'background-size:600px 100%;animation:shimmer 1.4s linear infinite;margin-bottom:.75rem;"></div>'
        )
    st.markdown("".join(skeletons), unsafe_allow_html=True)


def render_toast_message(message: str, type: str = "info", duration: int = 3000):
    bg = {"success": COLORS["sage"], "error": COLORS["crimson"], "warning": COLORS["gold"], "info": COLORS["ink_mid"]}.get(type, COLORS["ink_mid"])
    toast_html = f"""
    <div id="toast-msg" style="
        position:fixed;bottom:20px;right:20px;
        background:{bg};color:white;
        padding:10px 18px;border-radius:8px;
        box-shadow:0 4px 12px rgba(0,0,0,.15);
        z-index:9999;font-family:'DM Sans',sans-serif;font-size:.78rem;
    ">{html.escape(message)}</div>
    <script>
    setTimeout(function(){{
        var t=document.getElementById('toast-msg');
        if(t){{t.style.opacity='0';t.style.transition='opacity .3s';setTimeout(function(){{t.remove();}},300);}}
    }},{duration});
    </script>
    """
    st.markdown(toast_html, unsafe_allow_html=True)


def render_confetti():
    confetti_html = """
    <canvas id="cf-canvas" style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9998;"></canvas>
    <script>
    (function(){
        var c=document.getElementById('cf-canvas');if(!c)return;
        var ctx=c.getContext('2d');c.width=window.innerWidth;c.height=window.innerHeight;
        var p=[],colors=['#2E7A56','#B8902C','#C04060','#8B1A34','#1A0A12'];
        for(var i=0;i<90;i++){p.push({x:Math.random()*c.width,y:Math.random()*c.height-c.height,
            sz:Math.random()*5+2,vy:Math.random()*4+2,vx:Math.random()*2-1,
            rot:Math.random()*360,rv:Math.random()*8-4,
            col:colors[Math.floor(Math.random()*colors.length)]});}
        function draw(){ctx.clearRect(0,0,c.width,c.height);var done=true;
            for(var i=0;i<p.length;i++){var q=p[i];q.y+=q.vy;q.x+=q.vx;q.rot+=q.rv;
                if(q.y<c.height+50)done=false;
                ctx.save();ctx.translate(q.x,q.y);ctx.rotate(q.rot*Math.PI/180);
                ctx.fillStyle=q.col;ctx.fillRect(-q.sz/2,-q.sz/2,q.sz,q.sz);ctx.restore();}
            if(!done)requestAnimationFrame(draw);else c.remove();}
        draw();setTimeout(function(){if(c)c.remove();},3000);
    })();
    </script>
    """
    st.markdown(confetti_html, unsafe_allow_html=True)