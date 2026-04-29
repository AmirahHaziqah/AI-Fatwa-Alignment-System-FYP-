# =========================================================
# fyp_dashboard.py
# =========================================================
import html
import os
import re
import textwrap
from datetime import datetime

import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from utils import (
    EXCEL_AVAILABLE,
    add_to_history,
    build_light_table_html,
    clear_history,
    export_to_excel,
    format_percent,
    get_score_band_label,
    get_score_color,
    get_score_css_class,
    get_score_tier,
    load_history_from_file,
    recent_topics_summary,
    safe_read_csv,
)

from scoring import (
    compare_states_within_question,
    detect_best_question,
    infer_topic_label,
    interpret,
    sbert_is_ready,
    load_sbert_engine,
)

from styling import (
    COLORS,
    apply_theme,
    create_score_circle,
    explain_metric,
    explain_score_band,
    render_footer,
    render_sidebar_theme_legend,
    render_hero_banner,
    render_dashboard_header,
    render_section_banner,
    render_sidebar_profile_card,
    render_sidebar_section,
    render_sidebar_topic_pills,
    render_sidebar_workspace,
    render_sidebar_action_list,
    render_sidebar_progress,
    render_fatwa_reference_card,
    render_review_workspace_header,
)

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="AI Fatwa Alignment Dashboard | ART Ruling Reviewer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme()


def apply_dashboard_polish():
    st.markdown("""
    <style>
    :root { 
        color-scheme: light !important;
        --primary-color: #D44D5C;
        --secondary-color: #773344;
        --success-color: #06A77D;
        --warning-color: #F1A208;
        --danger-color: #A31621;
    }
    
    /* Base styles - properly scaled for 100% zoom - FIXED */
    html {
        font-size: 14px !important;
    }
    
    .stApp {
        background-color: #f4f6f9 !important;
    }
    
    html, body, [data-testid="stAppViewContainer"] { 
        background-color: #f4f6f9 !important; 
        overflow-x: hidden !important;
    }
    
    [data-testid="stTextArea"] > div > div, 
    [data-testid="stTextArea"] [data-baseweb="textarea"], 
    [data-testid="stTextArea"] [data-testid="stTextAreaRootElement"] { 
        background: #ffffff !important; 
        background-color: #ffffff !important; 
        border: 1px solid #e3b5a4 !important;
        border-radius: 16px !important;
    }
    
    /* FIX: Text area text color - make it visible */
    .stTextArea textarea,
    .stTextArea textarea:focus,
    .stTextArea textarea:active {
        color: #2a1421 !important;
        background: #ffffff !important;
        -webkit-text-fill-color: #2a1421 !important;
    }
    
    .stTextArea textarea::placeholder {
        color: #a08b97 !important;
    }
    
    [data-testid="stAppViewContainer"] .block-container { 
        max-width: 1400px !important; 
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* ===== BEAUTIFUL METRIC CARDS ===== */
    .metric-beautiful-card {
        background: linear-gradient(135deg, #ffffff 0%, #fef8f5 100%);
        border-radius: 16px;
        padding: 0.8rem 0.6rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(119, 51, 68, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(227, 181, 164, 0.3);
        height: 100%;
    }
    
    .metric-beautiful-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(119, 51, 68, 0.12);
    }
    
    .metric-beautiful-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
    }
    
    .metric-beautiful-card.good::before { background: linear-gradient(90deg, #06A77D, #2E8B57); }
    .metric-beautiful-card.moderate::before { background: linear-gradient(90deg, #F1A208, #D4A04B); }
    .metric-beautiful-card.weak::before { background: linear-gradient(90deg, #A31621, #D44D5C); }
    
    .metric-beautiful-icon {
        width: 38px;
        height: 38px;
        margin: 0 auto 0.4rem auto;
        background: linear-gradient(135deg, #f9e6e0, #f5d5cc);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
    }
    
    .metric-beautiful-label {
        font-size: 0.65rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #8b6771;
        margin-bottom: 0.3rem;
    }
    
    .metric-beautiful-value {
        font-family: 'Inter Tight', 'Inter', sans-serif;
        font-size: 1.5rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.15rem;
    }
    
    .metric-beautiful-value.good { color: #06A77D; }
    .metric-beautiful-value.moderate { color: #D4A04B; }
    .metric-beautiful-value.weak { color: #A31621; }
    
    .metric-beautiful-sub {
        font-size: 0.6rem;
        color: #a08b97;
        margin-bottom: 0.3rem;
        font-weight: 600;
    }
    
    .metric-beautiful-desc {
        font-size: 0.65rem;
        color: #7a6874;
        line-height: 1.3;
        padding-top: 0.3rem;
        border-top: 1px solid rgba(227, 181, 164, 0.3);
        margin-top: 0.3rem;
    }
    
    /* Metric card grid */
    .metric-grid-4 {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.8rem;
        margin: 0.6rem 0;
    }
    
    @media (max-width: 768px) {
        .metric-grid-4 {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    @media (max-width: 480px) {
        .metric-grid-4 {
            grid-template-columns: 1fr;
        }
    }
    
    /* FIX: Result cards spacing - add gap between cards */
    .result-cards-grid {
        display: grid;
        grid-template-columns: 1.05fr 1.35fr 1fr;
        gap: 1.2rem;
        margin: 0.8rem 0;
    }
    
    /* FIX: Single review right column spacing */
    .single-review-right-col {
        padding-left: 0.5rem;
    }
    
    /* Sidebar - make it slightly narrower */
    [data-testid="stSidebar"] {
        min-width: 260px !important;
        max-width: 260px !important;
        width: 260px !important;
    }
    
    /* Header is now a compact bar — no image sizing needed */
    
    /* Tab minimal hero - smaller */
    .tab-minimal-hero {
        padding: 0.7rem 1rem 0.6rem 1rem !important;
    }
    
    .tab-minimal-title {
        font-size: 1.2rem !important;
    }
    
    .tab-minimal-copy {
        font-size: 0.8rem !important;
    }
    
    .tab-minimal-kicker {
        font-size: 0.65rem !important;
    }
    
    /* Input editor - smaller */
    .input-editor-shell {
        padding: 0.5rem 0.7rem 0.4rem 0.7rem !important;
    }
    
    .input-editor-title {
        font-size: 0.85rem !important;
    }
    
    .input-editor-kicker {
        font-size: 0.65rem !important;
    }
    
    /* Batch shell - smaller */
    .batch-shell {
        padding: 0.6rem 0.8rem 0.5rem 0.8rem !important;
    }
    
    .batch-title {
        font-size: 1rem !important;
    }
    
    .batch-copy {
        font-size: 0.8rem !important;
    }
    
    /* Similarity breakdown - smaller */
    .sim-lite-shell {
        padding: 0.6rem !important;
    }
    
    .sim-lite-title {
        font-size: 1.1rem !important;
    }
    
    .sim-lite-ring {
        width: 75px !important;
        height: 75px !important;
    }
    
    .sim-lite-ring-inner {
        width: 55px !important;
        height: 55px !important;
    }
    
    .sim-lite-ring-inner strong {
        font-size: 1.1rem !important;
    }
    
    .sim-lite-metric-value {
        font-size: 1.3rem !important;
    }
    
    /* Result hero - smaller */
    .result-hero-title {
        font-size: 1rem !important;
    }
    
    .result-hero-copy {
        font-size: 0.75rem !important;
    }
    
    /* Buttons - smaller */
    .stButton > button,
    .stDownloadButton > button {
        padding: 0.35rem 0.7rem !important;
        font-size: 0.75rem !important;
        min-height: 32px !important;
    }
    
    /* Text area - smaller */
    .stTextArea textarea {
        font-size: 0.8rem !important;
        min-height: 100px !important;
    }
    
    /* Explorer orbs - smaller */
    .explorer-orb {
        padding: 0.5rem 0.7rem !important;
        min-height: 60px !important;
    }
    
    .explorer-orb-icon {
        width: 38px !important;
        height: 38px !important;
        font-size: 0.75rem !important;
    }
    
    .explorer-orb-value {
        font-size: 1rem !important;
    }
    
    .explorer-orb-label {
        font-size: 0.6rem !important;
    }
    
    /* Workspace - smaller */
    .workspace-title {
        font-size: 0.95rem !important;
    }
    
    .workspace-copy {
        font-size: 0.75rem !important;
    }
    
    /* Points card - smaller */
    .points-card-header {
        font-size: 0.7rem !important;
    }
    
    .keyword-match, .keyword-miss {
        font-size: 0.7rem !important;
        padding: 0.25rem 0.7rem !important;
    }
    
    /* Light table - smaller */
    .light-table thead th {
        font-size: 0.7rem !important;
        padding: 0.5rem 0.7rem !important;
    }
    
    .light-table tbody td {
        font-size: 0.7rem !important;
        padding: 0.5rem 0.7rem !important;
    }
    
    /* Alignment cards - smaller */
    .align-rank-topic {
        font-size: 0.8rem !important;
    }
    
    .align-score {
        font-size: 0.85rem !important;
    }
    
    /* Metric cards */
    .metric-card {
        padding: 0.7rem 0.8rem !important;
    }
    
    .metric-value {
        font-size: 1.3rem !important;
    }
    
    .metric-label {
        font-size: 0.7rem !important;
    }
    
    /* ===== BEAUTIFUL POPUP TOAST ===== */
    @keyframes slideInDown {
        from {
            transform: translateY(-100%);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    @keyframes fadeOutUp {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-100%);
        }
    }
    
    .custom-toast-center {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        min-width: 320px;
        max-width: 420px;
        background: linear-gradient(135deg, #ffffff 0%, #f0faf5 100%);
        border-radius: 20px;
        box-shadow: 0 30px 50px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(6, 167, 125, 0.3);
        z-index: 99999;
        animation: slideInDown 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        overflow: hidden;
        border-left: 6px solid #06A77D;
    }
    
    .custom-toast-center.fade-out {
        animation: fadeOutUp 0.4s ease forwards;
    }
    
    .toast-header-center {
        background: linear-gradient(135deg, #06A77D, #2E8B57);
        padding: 0.8rem 1rem;
        display: flex;
        align-items: center;
        gap: 0.7rem;
    }
    
    .toast-icon-center {
        width: 36px;
        height: 36px;
        background: rgba(255,255,255,0.25);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        font-weight: bold;
    }
    
    .toast-title-center {
        flex: 1;
        color: white;
        font-weight: 800;
        font-size: 1rem;
        letter-spacing: 0.02em;
    }
    
    .toast-close-center {
        width: 28px;
        height: 28px;
        background: rgba(255,255,255,0.15);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 1.1rem;
        transition: all 0.2s;
    }
    
    .toast-close-center:hover {
        background: rgba(255,255,255,0.3);
        transform: scale(1.1);
    }
    
    .toast-body-center {
        padding: 1rem 1.2rem;
        background: linear-gradient(135deg, #ffffff, #f8fff9);
    }
    
    .toast-message-center {
        color: #1a5c3e;
        font-size: 0.9rem;
        line-height: 1.5;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .toast-detail-center {
        color: #2e8b57;
        font-size: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    
    .toast-detail-center span {
        background: #e8f5ef;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
    }
    
    /* Responsive */
    @media (max-width: 1200px) {
        html { font-size: 13px !important; }
        .result-cards-grid { gap: 0.8rem; }
    }
    
    @media (max-width: 900px) {
        html { font-size: 12px !important; }
        .result-cards-grid { grid-template-columns: 1fr; gap: 1rem; }
    }
    
    /* Fix for text area dark background issue */
    [data-testid="stTextArea"] {
        background: transparent !important;
    }
    
    .stTextArea textarea {
        background: #ffffff !important;
        color: #2a1421 !important;
        border: 1px solid #e3b5a4 !important;
        border-radius: 16px !important;
    }
    
    /* Fix for selectbox and multiselect */
    .stSelectbox select, .stMultiSelect select {
        color: #2a1421 !important;
    }

    /* ===== CRITICAL: Fix ALL button text color — prevent black buttons ===== */
    .stButton > button,
    .stDownloadButton > button,
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"] {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background: linear-gradient(135deg, #c44460 0%, #a83250 100%) !important;
        border: none !important;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background: linear-gradient(135deg, #d44d5c 0%, #b8405a 100%) !important;
    }
    .stButton > button *,
    .stDownloadButton > button * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
           


    /* ===== POLISHED DETAIL DRAWER CONTROL ===== */
    .detail-toggle-card {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr) auto;
        gap: 0.85rem;
        align-items: center;
        background: linear-gradient(135deg, #ffffff 0%, #fff7f4 100%);
        border: 1px solid #ead1c8;
        border-left: 5px solid #773344;
        border-radius: 20px;
        padding: 0.85rem 1rem;
        box-shadow: 0 10px 22px rgba(25, 14, 36, 0.055);
        margin: 0.4rem 0 0.8rem 0;
    }

    .detail-toggle-card-open {
        border-left-color: #D44D5C;
        background: linear-gradient(135deg, #ffffff 0%, #fff2ef 100%);
    }

    .detail-toggle-icon {
        width: 38px;
        height: 38px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #773344 0%, #D44D5C 100%);
        color: #ffffff;
        font-size: 0.9rem;
        font-weight: 900;
        box-shadow: 0 8px 16px rgba(119, 51, 68, 0.18);
    }

    .detail-toggle-kicker {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        padding: 0.18rem 0.55rem;
        border-radius: 999px;
        background: #f7ece7;
        border: 1px solid #ead1c8;
        color: #8b3b50;
        font-size: 0.62rem;
        font-weight: 850;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        margin-bottom: 0.22rem;
    }

    .detail-toggle-title {
        font-family: 'Inter Tight', 'Inter', sans-serif;
        font-size: 1rem;
        font-weight: 850;
        color: #241226;
        letter-spacing: -0.02em;
        line-height: 1.15;
    }

    .detail-toggle-sub {
        color: #6d5a68;
        font-size: 0.76rem;
        line-height: 1.5;
        margin-top: 0.22rem;
    }

    .detail-toggle-chips {
        display: flex;
        justify-content: flex-end;
        gap: 0.42rem;
        flex-wrap: wrap;
    }

    .detail-toggle-chips span {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.32rem 0.65rem;
        border-radius: 999px;
        background: #ffffff;
        border: 1px solid #ead1c8;
        color: #773344;
        font-size: 0.7rem;
        font-weight: 800;
        white-space: nowrap;
    }

    .detail-toggle-button-wrap {
        margin-top: 0.4rem;
    }

    .detail-toggle-button-wrap .stButton > button {
        min-height: 64px !important;
        border-radius: 18px !important;
        background: linear-gradient(135deg, #160029 0%, #773344 56%, #D44D5C 100%) !important;
        box-shadow: 0 10px 22px rgba(119, 51, 68, 0.2) !important;
        font-size: 0.78rem !important;
        font-weight: 850 !important;
    }

    .detail-drawer-body {
        margin-top: 0.25rem;
        padding: 0.75rem;
        border: 1px solid #ead1c8;
        border-radius: 24px;
        background: linear-gradient(180deg, rgba(255,255,255,0.74) 0%, rgba(255,248,244,0.92) 100%);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.65);
    }

    @media (max-width: 900px) {
        .detail-toggle-card {
            grid-template-columns: auto 1fr;
        }
        .detail-toggle-chips {
            grid-column: 1 / -1;
            justify-content: flex-start;
        }
    }

    /* ===== UNIFIED INPUT EDITOR CARD V2 ===== */
    /* Header part — top of the card, rounded top only */
    .input-editor-shell-v2 {
        background: linear-gradient(180deg, #fefcfe 0%, #f8f0f6 100%);
        border: 1px solid #dfd7e4;
        border-bottom: none;
        border-radius: 16px 16px 0 0;
        padding: 0.7rem 0.9rem 0.65rem 0.9rem;
        margin: 0.2rem 0 0 0;
        box-shadow: 0 4px 14px rgba(25,14,36,0.04);
        transition: all 0.3s ease;
    }

    .input-editor-v2-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.7rem;
    }

    /* Body wrapper — bottom of the card, rounded bottom only */
    .input-editor-v2-body {
        margin: 0 0 0.45rem 0;
    }

    /* Make the textarea connect seamlessly to the header */
    .input-editor-v2-body [data-testid="stTextArea"] > div > div,
    .input-editor-v2-body [data-baseweb="textarea"],
    .input-editor-v2-body textarea {
        border-radius: 0 0 14px 14px !important;
        border: 1px solid #dfd7e4 !important;
        border-top: 1px solid #e8ddf0 !important;
        margin-top: 0 !important;
        background: #ffffff !important;
        color: #2a1421 !important;
        box-shadow: 0 4px 14px rgba(25,14,36,0.04) !important;
    }

    .input-editor-v2-body [data-testid="stTextArea"] {
        margin-top: 0 !important;
    }

    /* ===== UNIFIED INPUT EDITOR CARD V2 ===== */
    .input-editor-shell-v2 {
        background: linear-gradient(180deg, #fefcfe 0%, #f8f0f6 100%);
        border: 1px solid #dfd7e4;
        border-bottom: none;
        border-radius: 16px 16px 0 0;
        padding: 0.7rem 0.9rem 0.65rem 0.9rem;
        margin: 0.2rem 0 0 0;
        box-shadow: 0 4px 14px rgba(25,14,36,0.04);
        transition: all 0.3s ease;
    }

    .input-editor-v2-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.7rem;
    }

    /* Make the textarea flush-connect to the header */
    .input-editor-v2-body {
        margin: 0 0 0.45rem 0;
    }

    .input-editor-v2-body [data-testid="stTextArea"] > div > div,
    .input-editor-v2-body [data-baseweb="textarea"],
    .input-editor-v2-body textarea {
        border-radius: 0 0 14px 14px !important;
        border: 1px solid #dfd7e4 !important;
        border-top: 1px solid #e8e0ed !important;
        background: #ffffff !important;
        color: #2a1421 !important;
        -webkit-text-fill-color: #2a1421 !important;
        box-shadow: 0 4px 10px rgba(25,14,36,0.04) !important;
        margin-top: 0 !important;
    }

    .input-editor-v2-body [data-testid="stTextArea"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* ===== IMPROVED DETAIL DRAWER BUTTON ===== */
    .detail-toggle-button-wrap {
        height: 100%;
        display: flex;
        align-items: stretch;
    }

    .detail-toggle-button-wrap .stButton {
        width: 100%;
        height: 100%;
    }

    .detail-toggle-button-wrap .stButton > button {
        height: 100% !important;
        min-height: 76px !important;
        border-radius: 18px !important;
        background: linear-gradient(160deg, #160029 0%, #773344 55%, #D44D5C 100%) !important;
        box-shadow: 0 8px 20px rgba(119, 51, 68, 0.22) !important;
        font-size: 0.8rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.01em !important;
        transition: all 0.25s ease !important;
        white-space: normal !important;
        line-height: 1.35 !important;
    }

    .detail-toggle-button-wrap .stButton > button:hover {
        box-shadow: 0 12px 28px rgba(119, 51, 68, 0.32) !important;
        transform: translateY(-2px) !important;
    }

    </style>
    """, unsafe_allow_html=True)


apply_dashboard_polish()


def resolve_header_banner_path():
    candidates = [
        "dashboard_background.png",
        "dashboard_background.jpg",
        "dashboard_background.jpeg",
        "dashboard_background.webp",
        "dashboard_background 3.png",
        "dashboard_background 3.jpg",
        "dashboard_background 3.jpeg",
        "dashboard_background 3.webp",
        "dashboard_background_3.png",
        "dashboard_background_3.jpg",
        "dashboard_background_3.jpeg",
        "dashboard_background_3.webp",
        "hero_banner.jpg",
        "hero_banner.png",
        "hero_banner.jpeg",
        "section_banner.jpg",
        "section_banner.png",
        "islamic_pattern.jpg",
    ]
    return next((p for p in candidates if os.path.exists(p)), None)


def resolve_banner_path():
    return resolve_header_banner_path()


# =========================================================
# BEAUTIFUL CENTERED POPUP TOAST FUNCTIONS
# =========================================================

def show_success_toast_center(message: str, details: list = None):
    """Display a centered success popup using components.html() — JS runs in a real document context."""
    details_items = ""
    if details:
        details_items = "".join(
            f'<div class="at-pill">✓ {html.escape(d)}</div>'
            for d in details
        )

    toast_html = f"""<!DOCTYPE html>
<html><head><style>body{{margin:0;padding:0;background:transparent;}}</style></head>
<body>
<script>
(function() {{
    var parentDoc = window.parent.document;
    var old = parentDoc.getElementById('amirahToast');
    if (old) old.parentNode.removeChild(old);

    if (!parentDoc.getElementById('amirahToastStyle')) {{
        var style = parentDoc.createElement('style');
        style.id = 'amirahToastStyle';
        style.textContent = `
            @keyframes atIn  {{ from{{opacity:0;transform:translate(-50%,-50%) scale(0.82)}} to{{opacity:1;transform:translate(-50%,-50%) scale(1)}} }}
            @keyframes atOut {{ from{{opacity:1;transform:translate(-50%,-50%) scale(1)}} to{{opacity:0;transform:translate(-50%,-50%) scale(0.88)}} }}
            @keyframes atBar {{ from{{transform:scaleX(1)}} to{{transform:scaleX(0)}} }}
            #amirahToast {{
                position:fixed; top:50%; left:50%;
                transform:translate(-50%,-50%);
                z-index:999999; min-width:340px; max-width:440px;
                background:#fff; border-radius:18px; overflow:hidden;
                box-shadow:0 20px 50px rgba(0,0,0,0.20),0 0 0 1px rgba(6,167,125,0.18);
                animation:atIn 0.38s cubic-bezier(0.34,1.56,0.64,1) forwards;
                font-family:'Inter',sans-serif;
            }}
            #amirahToast.at-hiding {{ animation:atOut 0.3s ease forwards; }}
            .at-hdr {{
                background:linear-gradient(135deg,#06A77D 0%,#049268 100%);
                padding:0.85rem 1.05rem;
                display:flex; align-items:center; gap:0.7rem;
            }}
            .at-check {{
                width:34px; height:34px; background:rgba(255,255,255,0.22);
                border-radius:50%; display:flex; align-items:center;
                justify-content:center; font-size:1.1rem; font-weight:900;
                color:#fff; flex-shrink:0;
            }}
            .at-ttl {{ flex:1; color:#fff; font-weight:800; font-size:0.92rem; letter-spacing:0.01em; }}
            .at-cls {{
                width:26px; height:26px; background:rgba(255,255,255,0.16);
                border-radius:50%; display:flex; align-items:center;
                justify-content:center; cursor:pointer; color:#fff;
                font-size:1rem; line-height:1; flex-shrink:0;
                transition:background 0.18s;
            }}
            .at-cls:hover {{ background:rgba(255,255,255,0.30); }}
            .at-bdy {{ padding:0.9rem 1.1rem 1rem 1.1rem; background:#f6fefb; }}
            .at-msg {{ color:#1a5c3e; font-size:0.86rem; font-weight:600; line-height:1.55; margin-bottom:0.5rem; }}
            .at-pills {{ display:flex; flex-wrap:wrap; gap:0.35rem; }}
            .at-pill {{
                background:#dff2eb; color:#1a7a56;
                font-size:0.7rem; font-weight:700;
                padding:0.2rem 0.6rem; border-radius:999px;
            }}
            .at-prog {{ height:3px; background:rgba(6,167,125,0.15); overflow:hidden; }}
            .at-prog-bar {{
                height:3px; background:#06A77D; width:100%;
                transform-origin:left; animation:atBar 4.2s linear forwards;
            }}
        `;
        parentDoc.head.appendChild(style);
    }}

    var t = parentDoc.createElement('div');
    t.id = 'amirahToast';
    t.innerHTML = '<div class="at-hdr"><div class="at-check">✓</div><div class="at-ttl">Response Loaded Successfully</div><div class="at-cls" id="atClose">✕</div></div><div class="at-bdy"><div class="at-msg">{html.escape(message)}</div><div class="at-pills">{details_items}</div></div><div class="at-prog"><div class="at-prog-bar"></div></div>';
    parentDoc.body.appendChild(t);

    function dismiss() {{
        var el = parentDoc.getElementById('amirahToast');
        if (!el || el._d) return;
        el._d = true;
        el.classList.add('at-hiding');
        setTimeout(function() {{ if (el.parentNode) el.parentNode.removeChild(el); }}, 320);
    }}
    parentDoc.getElementById('atClose').addEventListener('click', dismiss);
    setTimeout(dismiss, 4500);
}})();
</script>
</body></html>"""
    components.html(toast_html, height=0)


def show_success_toast(message: str, details: list = None):
    """Alias to the centered toast."""
    show_success_toast_center(message, details)


# =========================================================
# BEAUTIFUL METRIC CARD RENDERER
# =========================================================

def render_beautiful_metric_card(label: str, value: float, icon: str, description: str, sub_label: str = ""):
    """Render a beautiful metric card with icon and gradient."""
    
    if value >= 70:
        tier_class = "good"
        value_class = "good"
    elif value >= 50:
        tier_class = "moderate"
        value_class = "moderate"
    else:
        tier_class = "weak"
        value_class = "weak"
    
    if "Text" in label:
        desc_text = "Uses many of the same words." if value >= 70 else "Uses some of the same words." if value >= 50 else "Uses quite different words."
    elif "Meaning" in label:
        desc_text = "Very close in meaning." if value >= 70 else "Quite close in meaning." if value >= 50 else "Not very close in meaning."
    elif "Key" in label or "Points" in label:
        desc_text = "Most main points are included." if value >= 70 else "Some main points are included." if value >= 50 else "Important points are still missing."
    else:
        desc_text = description
    
    html_content = f"""
    <div class="metric-beautiful-card {tier_class}">
        <div class="metric-beautiful-icon">{icon}</div>
        <div class="metric-beautiful-label">{label}</div>
        <div class="metric-beautiful-value {value_class}">{value:.0f}%</div>
        <div class="metric-beautiful-sub">{sub_label}</div>
        <div class="metric-beautiful-desc">{desc_text}</div>
    </div>
    """
    
    st.markdown(html_content, unsafe_allow_html=True)


def render_beautiful_metric_grid(lexical_score, semantic_score, coverage_score, mean_alignment):
    """Render 4 beautiful metric cards in a grid."""
    
    st.markdown('<div class="metric-grid-4">', unsafe_allow_html=True)
    
    cols = st.columns(4, gap="small")
    metrics = [
        ("Text Match", lexical_score, "📝", "Words used", "Word overlap similarity"),
        ("Meaning Match", semantic_score, "🎯", "Same meaning", "Semantic understanding"),
        ("Key Points", coverage_score, "✓", "Main points", "Important conditions found"),
        ("Overall Fit", mean_alignment, "⚖️", "State match", "Average across state rulings"),
    ]
    
    for col, (label, score, icon, sub, desc) in zip(cols, metrics):
        with col:
            render_beautiful_metric_card(label, score, icon, desc, sub)
    
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# MISSING FUNCTIONS
# =========================================================

def _html(block: str) -> str:
    """Helper function to clean HTML blocks."""
    cleaned = textwrap.dedent(block).strip()
    return "\n".join(line.lstrip() for line in cleaned.splitlines())


def build_sidebar_score_guide_html():
    """Build the sidebar score guide HTML content."""
    return textwrap.dedent("""
    <div class='sidebar-action-list'>
        <div class='sidebar-action-item'>
            <div class='sidebar-action-icon'>1</div>
            <div>
                <div class='sidebar-action-title'>Start with the final score</div>
                <div class='sidebar-action-text'><strong>70% and above</strong> usually means the answer is close to the fatwa and covers the main conditions well.</div>
            </div>
        </div>
        <div class='sidebar-action-item'>
            <div class='sidebar-action-icon'>2</div>
            <div>
                <div class='sidebar-action-title'>Check the middle band carefully</div>
                <div class='sidebar-action-text'><strong>50% to 69%</strong> means the answer is partly right, but some important fatwa points may still be missing or unclear.</div>
            </div>
        </div>
        <div class='sidebar-action-item'>
            <div class='sidebar-action-icon'>3</div>
            <div>
                <div class='sidebar-action-title'>Do not rely on weak matches alone</div>
                <div class='sidebar-action-text'><strong>Below 50%</strong> usually means the answer is too far from the intended fatwa meaning and needs closer manual review.</div>
            </div>
        </div>
    </div>
    """).strip()


def build_sidebar_latest_bundle():
    """Get the latest analysis bundle for sidebar display."""
    current_bundle = st.session_state.get("current_analysis")
    if current_bundle:
        return current_bundle

    history = st.session_state.get("analysis_history", []) or []
    if not history:
        return None

    latest = history[-1]
    return {
        "topic_label": latest.get("topic_label", "-"),
        "best_state_name": latest.get("best_state", "-"),
        "final_match_score": latest.get("final_match_score", latest.get("alignment_score", 0)),
        "recommendation_label": latest.get("recommendation_label", "Moderate Alignment"),
        "confidence": latest.get("detection_confidence", "Unknown"),
        "compliance_level": latest.get("compliance_level", "Unclear"),
        "specific_issue": latest.get("specific_issue", "-"),
    }


# =========================================================
# SESSION STATE
# =========================================================
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = load_history_from_file()

if "current_analysis" not in st.session_state:
    st.session_state.current_analysis = None

if "batch_results_df" not in st.session_state:
    st.session_state.batch_results_df = None

if "batch_numeric_df" not in st.session_state:
    st.session_state.batch_numeric_df = None

if "browse_reset_pressed" not in st.session_state:
    st.session_state.browse_reset_pressed = False

if "fatwa_explorer_topic" not in st.session_state:
    st.session_state.fatwa_explorer_topic = "All topics"

if "fatwa_explorer_state" not in st.session_state:
    st.session_state.fatwa_explorer_state = "All states / sources"

if "single_review_model_ready" not in st.session_state:
    st.session_state.single_review_model_ready = False


# =========================================================
# DATA LOADING
# =========================================================
try:
    fatwa_df = safe_read_csv("fatwa_reference.csv")
except Exception as e:
    st.error(f"Unable to load fatwa_reference.csv: {e}")
    st.stop()

required_cols = {"question_id", "state", "fatwa_text"}
missing = required_cols - set(fatwa_df.columns)
if missing:
    st.error(f"Missing columns in fatwa_reference.csv: {', '.join(sorted(missing))}")
    st.stop()

fatwa_df["question_id"] = fatwa_df["question_id"].astype(str).str.strip()
fatwa_df["state"] = fatwa_df["state"].astype(str).str.strip()
fatwa_df["fatwa_text"] = fatwa_df["fatwa_text"].astype(str).str.strip()
fatwa_df["issue"] = fatwa_df["issue"].astype(str).str.strip() if "issue" in fatwa_df.columns else ""
fatwa_df["question_text"] = fatwa_df["question_text"].astype(str).str.strip() if "question_text" in fatwa_df.columns else ""

# Load pre-collected AI answers dataset
ai_answer_df = pd.DataFrame()
AI_DATASET_AVAILABLE = False

_ai_answer_candidates = [
    "ai_answer.csv",
    "fyp dataset_ai answer.csv",
    "fyp_dataset_ai_answer.csv",
]

for _candidate in _ai_answer_candidates:
    if not os.path.exists(_candidate):
        continue
    try:
        ai_answer_df = safe_read_csv(_candidate)
        rename_map = {}
        if "question_id" not in ai_answer_df.columns:
            for c in ai_answer_df.columns:
                if c.strip().lower() == "question_id":
                    rename_map[c] = "question_id"
        if "model" not in ai_answer_df.columns:
            for c in ai_answer_df.columns:
                if c.strip().lower() == "model":
                    rename_map[c] = "model"
        if "ai_answer_raw" not in ai_answer_df.columns:
            for c in ai_answer_df.columns:
                if c.strip().lower() in {"ai_answer_raw", "ai answer raw", "answer", "ai_answer"}:
                    rename_map[c] = "ai_answer_raw"
        if rename_map:
            ai_answer_df = ai_answer_df.rename(columns=rename_map)

        required_ai_cols = {"question_id", "model", "ai_answer_raw"}
        if not required_ai_cols.issubset(set(ai_answer_df.columns)):
            continue

        ai_answer_df["question_id"] = ai_answer_df["question_id"].astype(str).str.strip()
        ai_answer_df["model"] = ai_answer_df["model"].astype(str).str.strip()
        ai_answer_df["ai_answer_raw"] = ai_answer_df["ai_answer_raw"].astype(str).str.strip()
        AI_DATASET_AVAILABLE = True
        break
    except Exception:
        ai_answer_df = pd.DataFrame()
        AI_DATASET_AVAILABLE = False


# =========================================================
# HELPERS
# =========================================================
def safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def css_band(score):
    return get_score_css_class(get_score_tier(score))


def unpack_state_comparison(result):
    """Normalize compare_states_within_question output into (best_state_dict, results_df)."""
    if isinstance(result, tuple):
        best_state, state_results_df = result
    else:
        state_results_df = result if isinstance(result, pd.DataFrame) else pd.DataFrame()
        if isinstance(state_results_df, pd.DataFrame) and not state_results_df.empty:
            top_row = state_results_df.sort_values('alignment_score', ascending=False).iloc[0]
            best_state = top_row.to_dict()
            best_state.setdefault('best_match_alignment', top_row.get('alignment_score', 0))
            if 'mean_alignment' not in best_state:
                best_state['mean_alignment'] = float(state_results_df['alignment_score'].mean()) if 'alignment_score' in state_results_df.columns else 0.0
        else:
            best_state = {}
    if not isinstance(state_results_df, pd.DataFrame):
        state_results_df = pd.DataFrame()
    if hasattr(best_state, 'to_dict'):
        best_state = best_state.to_dict()
    if not isinstance(best_state, dict):
        best_state = {}
    return best_state, state_results_df


def ensure_analysis_dependencies() -> bool:
    if sbert_is_ready():
        return True
    st.error(
        "⚠️ The semantic similarity model (SBERT) is not available. Please install sentence-transformers and ensure all-MiniLM-L6-v2 is downloaded before running the analysis."
    )
    st.info(
        "💡 The final alignment score relies heavily on semantic similarity. Without SBERT, results will be unreliable."
    )
    return False


def ensure_similarity_engine_loaded():
    if st.session_state.get("single_review_model_ready"):
        return
    load_sbert_engine()
    st.session_state["single_review_model_ready"] = True


def reset_fatwa_explorer_filters():
    st.session_state['fatwa_explorer_topic'] = 'All topics'
    st.session_state['fatwa_explorer_state'] = 'All states / sources'


def paginate_with_buttons(prefix: str, total_rows: int, page_size: int = 5):
    total_pages = max(1, int(np.ceil(total_rows / page_size))) if total_rows else 1
    page_key = f"{prefix}_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    if st.session_state[page_key] > total_pages:
        st.session_state[page_key] = total_pages

    left, center, right = st.columns([1, 2, 1])
    with left:
        if st.button("◀ Previous", key=f"{prefix}_prev", use_container_width=True, disabled=st.session_state[page_key] <= 1):
            st.session_state[page_key] -= 1
            st.rerun()
    with center:
        st.markdown(
            f"<div class='pager-bar'><div class='pager-note'>Page {st.session_state[page_key]} of {total_pages}</div><div class='pager-actions'><span class='pager-chip'>{page_size} rows per page</span></div></div>",
            unsafe_allow_html=True
        )
    with right:
        if st.button("Next ▶", key=f"{prefix}_next", use_container_width=True, disabled=st.session_state[page_key] >= total_pages):
            st.session_state[page_key] += 1
            st.rerun()

    page = st.session_state[page_key]
    start = (page - 1) * page_size
    end = start + page_size
    return start, end, page, total_pages


def score_status_color(score):
    return get_score_color(score)


def short_text(text, max_len=40):
    text = "" if pd.isna(text) else str(text).strip()
    if not text:
        return "-"
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def short_topic_label(text):
    text = "" if pd.isna(text) else str(text).strip()
    if not text:
        return "-"

    replacements = {
        "Surrogacy": "Surrogacy",
        "Gamete Implantation for Reproduction": "Gamete Implant.",
        "IVF": "IVF",
        "Human Milk Bank": "Milk Bank",
        "Abortion due to fetal abnormality": "Abortion: Fetal Abn.",
        "Abortion for maternal health": "Abortion: Maternal",
        "Abortion ruling": "Abortion",
        "Abortion resulting from rape": "Abortion: Rape",
        "Abortion of fetus conceived through zina": "Abortion: Zina",
        "Abortion for OKU victims": "Abortion: OKU",
        "Abortion in high-risk groups": "Abortion: High-Risk",
        "Provision of contraceptives": "Contraceptives",
        "Contraceptives for unmarried individuals": "Contra: Unmarried",
        "Contraceptives for rape victims": "Contra: Rape Victims",
        "Contraceptives for adolescents": "Contra: Adolescents",
        "Contraceptives for HIV/AIDS prevention": "Contra: HIV/AIDS",
        "Abortion due to genetic disease (Example, Thalassemia)": "Abortion: Genetic",
        "Abortion of Foetus with Thalassemia": "Abortion: Thalassemia",
        "Sperm Bank": "Sperm Bank",
        "Human Cloning (Reproductive)": "Clone: Repro",
        "Human Cloning (Therapeutic)": "Clone: Therapy",
        "Stem Cell Research": "Stem Cell",
    }
    return replacements.get(text, text)


def format_numeric_for_table(value, digits=2):
    value = pd.to_numeric(value, errors="coerce")
    if pd.isna(value):
        return "-"
    return f"{float(value):.{digits}f}"


def explain_topic_row(row):
    issue = str(row.get("issue", "")).strip()
    qtext = str(row.get("question_text", "")).strip()

    if issue and qtext:
        return f"{issue}: {short_text(qtext, 70)}"
    if issue:
        return issue
    if qtext:
        return short_text(qtext, 70)
    return "-"


def get_specific_issue(best_question_row):
    issue = str(best_question_row.get("issue", "")).strip()
    qtext = str(best_question_row.get("question_text", "")).strip()

    if qtext:
        return qtext
    if issue:
        return issue
    return "No specific issue identified"


def get_recommendation(semantic_similarity, coverage, final_match_score):
    """Return a plain-language result label and explanation for end users."""
    final_match_score = safe_float(final_match_score)

    if final_match_score >= 70:
        return {
            "label": "Strong Alignment",
            "reason": "The answer is close to the fatwa meaning and covers most of the important points.",
        }
    elif final_match_score >= 50:
        return {
            "label": "Moderate Alignment",
            "reason": "The answer matches in some parts, but a few important fatwa points may still be missing or unclear.",
        }
    else:
        return {
            "label": "Low Alignment",
            "reason": "The answer is still far from the fatwa meaning, so it should not be relied on without careful checking.",
        }


def classify_shariah_compliance(
    final_match_score,
    lexical_similarity,
    semantic_similarity,
    coverage,
    confidence,
    matched_keywords,
    missing_keywords,
    ai_text
):
    final_match_score = safe_float(final_match_score)
    lexical_similarity = safe_float(lexical_similarity)
    semantic_similarity = safe_float(semantic_similarity)
    coverage = safe_float(coverage)

    matched_keywords = matched_keywords or "-"
    missing_keywords = missing_keywords or "-"
    ai_text = (ai_text or "").strip()

    missing_list = [] if missing_keywords == "-" else [x.strip() for x in missing_keywords.split(",") if x.strip()]

    critical_terms = {
        "haram", "harus", "nasab", "suami", "isteri", "penderma",
        "donor", "ovum", "sperma", "embrio", "ibu", "tumpang",
        "bank", "air", "mani"
    }
    missing_critical = [kw for kw in missing_list if kw.lower() in critical_terms]

    if len(ai_text) < 20 or confidence == "Low":
        return {
            "level": "Unclear",
            "reason": "The response is too short or the detected topic confidence is low, so the system cannot judge compliance reliably."
        }

    if final_match_score >= 80 and semantic_similarity >= 75 and coverage >= 65 and len(missing_critical) <= 1:
        return {
            "level": "Fully Compliant",
            "reason": "The response is highly aligned with the selected fatwa, captures the main meaning correctly, and covers most important Shariah points."
        }

    if final_match_score >= 60 and semantic_similarity >= 55:
        if missing_critical:
            return {
                "level": "Partially Compliant",
                "reason": f"The response is generally aligned, but some important Shariah points are still missing, such as: {', '.join(missing_critical[:4])}."
            }
        return {
            "level": "Partially Compliant",
            "reason": "The response is generally aligned, but it is still incomplete or not precise enough on some important conditions."
        }

    if final_match_score < 45 or semantic_similarity < 40:
        return {
            "level": "Non-Compliant",
            "reason": "The response is weakly aligned with the fatwa and may conflict with the expected ruling or omit core legal conditions."
        }

    return {
        "level": "Unclear",
        "reason": "The response does not provide enough reliable alignment evidence for a confident compliance judgment."
    }


def clean_history_dataframe(history_df: pd.DataFrame) -> pd.DataFrame:
    df = history_df.copy()

    expected_columns = [
        "timestamp",
        "topic_label",
        "specific_issue",
        "detection_confidence",
        "best_state",
        "final_match_score",
        "mean_alignment",
        "lexical_similarity",
        "semantic_similarity",
        "coverage",
        "compliance_level",
        "compliance_reason",
        "recommendation_label",
        "recommendation_reason",
    ]

    for col in expected_columns:
        if col not in df.columns:
            if col == "final_match_score" and "alignment_score" in df.columns:
                df[col] = df["alignment_score"]
            else:
                df[col] = ""

    text_cols = [
        "timestamp",
        "topic_label",
        "specific_issue",
        "detection_confidence",
        "best_state",
        "compliance_level",
        "compliance_reason",
        "recommendation_label",
        "recommendation_reason",
    ]
    for col in text_cols:
        df[col] = df[col].fillna("").astype(str).replace("nan", "").str.strip()

    numeric_cols = ["final_match_score", "mean_alignment", "lexical_similarity", "semantic_similarity", "coverage"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["topic_label"] = df["topic_label"].replace("", "Related Fatwa Topic")
    df["specific_issue"] = df["specific_issue"].replace("", "-")
    df["best_state"] = df["best_state"].replace("", "-")
    df["detection_confidence"] = df["detection_confidence"].replace("", "Unknown")
    df["compliance_level"] = df["compliance_level"].replace("", "Unclear")
    df["compliance_reason"] = df["compliance_reason"].replace("", "-")
    df["recommendation_label"] = df["recommendation_label"].replace("", "Moderate Alignment")
    df["recommendation_reason"] = df["recommendation_reason"].replace("", "-")

    return df


def get_history_df() -> pd.DataFrame:
    raw_df = pd.DataFrame(st.session_state.get("analysis_history", []))
    if raw_df.empty:
        return pd.DataFrame()
    return clean_history_dataframe(raw_df)


def get_score_band(score):
    return get_score_band_label(score)


def build_history_display_table(history_df: pd.DataFrame) -> pd.DataFrame:
    display_df = history_df.copy()

    if "timestamp" in display_df.columns:
        display_df["_sort_time"] = pd.to_datetime(display_df["timestamp"], errors="coerce")
        display_df = display_df.sort_values("_sort_time", ascending=False).drop(columns=["_sort_time"])

    display_df["Final Score"] = display_df["final_match_score"].apply(lambda x: format_percent(x, 1))
    display_df["Meaning"] = display_df["semantic_similarity"].apply(lambda x: format_percent(x, 1))
    display_df["Text"] = display_df["lexical_similarity"].apply(lambda x: format_percent(x, 1))
    display_df["Key Points"] = display_df["coverage"].apply(lambda x: format_percent(x, 1))
    display_df["Review"] = display_df["recommendation_label"].replace("", "Moderate Alignment")

    display_df = display_df.rename(columns={
        "timestamp": "Time",
        "topic_label": "Topic",
        "specific_issue": "Issue",
        "best_state": "Best Match"
    })

    display_df["Topic"] = display_df["Topic"].apply(short_topic_label)
    display_df["Issue"] = display_df["Issue"].apply(lambda x: short_text(x, 64))
    display_df["Best Match"] = display_df["Best Match"].apply(lambda x: short_text(x, 24))
    display_df["Review"] = display_df["Review"].apply(lambda x: short_text(x, 22))

    display_df = display_df[["Time", "Topic", "Issue", "Best Match", "Review", "Final Score", "Meaning", "Text", "Key Points"]]
    return display_df.reset_index(drop=True)


def build_advanced_topic_display(question_scores: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "issue",
        "question_text",
        "topic_score",
        "confidence",
        "keyword_overlap",
        "sbert",
        "issue_sbert",
        "rule_boost",
    ]
    df = question_scores.copy()

    for col in cols:
        if col not in df.columns:
            df[col] = ""

    df = df[cols].head(5).copy()

    df["Database Topic"] = df["issue"].astype(str).replace("nan", "").replace("", "-")
    df["Closest Reference Question"] = df.apply(explain_topic_row, axis=1)
    df["Topic Match Score"] = df["topic_score"].apply(lambda x: format_numeric_for_table(x, 2))
    df["System Confidence"] = df["confidence"].astype(str).replace("nan", "").replace("", "Unknown")
    df["Keyword Clue"] = df["keyword_overlap"].apply(lambda x: format_numeric_for_table(x, 2))
    df["Meaning Clue"] = df["sbert"].apply(lambda x: format_numeric_for_table(x, 2))
    df["Issue Focus Clue"] = df["issue_sbert"].apply(lambda x: format_numeric_for_table(x, 2))
    df["Alias Clue"] = df["rule_boost"].apply(lambda x: format_numeric_for_table(x, 2))

    return df[
        [
            "Database Topic",
            "Closest Reference Question",
            "Topic Match Score",
            "System Confidence",
            "Keyword Clue",
            "Meaning Clue",
            "Issue Focus Clue",
            "Alias Clue",
        ]
    ].copy()


def build_advanced_state_display(state_results: pd.DataFrame) -> pd.DataFrame:
    cols = ["state", "issue", "alignment_score", "lexical_similarity", "semantic_similarity", "coverage"]
    df = state_results.copy()

    for col in cols:
        if col not in df.columns:
            df[col] = ""

    df = df[cols].head(5).copy()

    df["Fatwa Source"] = df["state"].astype(str).replace("nan", "").replace("", "-")
    df["Issue"] = df["issue"].astype(str).replace("nan", "").replace("", "-")
    df["Final Match Score"] = df["alignment_score"].apply(lambda x: format_numeric_for_table(x, 2))
    df["Word Match"] = df["lexical_similarity"].apply(lambda x: format_numeric_for_table(x, 2))
    df["Meaning Match"] = df["semantic_similarity"].apply(lambda x: format_numeric_for_table(x, 2))
    df["Key Fatwa Points"] = df["coverage"].apply(lambda x: format_numeric_for_table(x, 2))

    return df[
        [
            "Fatwa Source",
            "Issue",
            "Final Match Score",
            "Word Match",
            "Meaning Match",
            "Key Fatwa Points"
        ]
    ].copy()


def render_technical_help_box():
    st.markdown("""
    <div class="msg-box msg-info">
        <strong>How to read the technical tables</strong><br>
        <strong>Database Topic</strong> shows the topic group found in your fatwa database.<br>
        <strong>Closest Reference Question</strong> shows which fatwa question looked most similar to the AI answer.<br>
        <strong>Topic Match Score</strong> shows how strongly the system thinks the answer belongs to that topic.<br>
        <strong>Keyword Clue</strong> shows matching important fatwa terms.<br>
        <strong>Meaning Clue</strong> shows overall semantic similarity against the full fatwa text.<br>
        <strong>Issue Focus Clue</strong> shows similarity to the database issue label and question wording only.<br>
        <strong>Alias Clue</strong> shows how strongly direct topic aliases such as "IVF" or "ibu tumpang" were detected in the answer.
    </div>
    """, unsafe_allow_html=True)


def render_history_overview(history_df: pd.DataFrame):
    chart_df = history_df.copy()
    if chart_df.empty:
        return

    chart_df = chart_df.reset_index(drop=True)
    chart_df["run_no"] = np.arange(1, len(chart_df) + 1)
    chart_df["final_match_score"] = pd.to_numeric(chart_df["final_match_score"], errors="coerce").fillna(0)
    chart_df["Band"] = chart_df["final_match_score"].apply(get_score_band_label)

    band_counts = (
        chart_df["Band"]
        .value_counts()
        .reindex(["Weak", "Moderate", "Good"], fill_value=0)
        .rename_axis("Category")
        .reset_index(name="Count")
    )
    band_counts["Color"] = band_counts["Category"].map({"Weak": "#b51224", "Moderate": "#f0a400", "Good": "#11a579"})

    bar_chart = alt.Chart(band_counts).mark_bar(size=58, cornerRadiusTopLeft=10, cornerRadiusTopRight=10).encode(
        x=alt.X("Category:N", sort=["Weak", "Moderate", "Good"], title=None, axis=alt.Axis(labelAngle=0, labelPadding=12, labelFontSize=13, labelColor="#314760", labelFontWeight="bold")),
        y=alt.Y("Count:Q", title="No. of Analyses", axis=alt.Axis(labelColor="#314760", titleColor="#314760", gridColor="#d9e6ef")),
        color=alt.Color("Color:N", scale=None, legend=None),
        tooltip=[alt.Tooltip("Category:N"), alt.Tooltip("Count:Q")]
    ).properties(height=270, background="#fbf5f1").configure_view(stroke="#ead8d0", fill="#fffaf7")

    threshold_df = pd.DataFrame({"y": [70]})
    line_base = alt.Chart(chart_df).encode(
        x=alt.X("run_no:Q", title="Analysis No.", axis=alt.Axis(labelColor="#314760", titleColor="#314760", gridColor="#d9e6ef")),
        y=alt.Y("final_match_score:Q", title="Match Score (%)", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(labelColor="#314760", titleColor="#314760", gridColor="#d9e6ef")),
        tooltip=[alt.Tooltip("run_no:Q", title="Analysis"), alt.Tooltip("final_match_score:Q", title="Score", format=".1f")]
    )
    trend_chart = (
        line_base.mark_line(point=alt.OverlayMarkDef(size=55, filled=True), strokeWidth=3, color="#385673")
        + alt.Chart(threshold_df).mark_rule(strokeDash=[8, 5], color="#d16b77", strokeWidth=2).encode(y="y:Q")
    ).properties(height=270, background="#fbf5f1").configure_view(stroke="#ead8d0", fill="#fffaf7")

    weak_count = int(band_counts.loc[band_counts["Category"] == "Weak", "Count"].sum()) if not band_counts.empty else 0
    moderate_count = int(band_counts.loc[band_counts["Category"] == "Moderate", "Count"].sum()) if not band_counts.empty else 0
    good_count = int(band_counts.loc[band_counts["Category"] == "Good", "Count"].sum()) if not band_counts.empty else 0
    latest_score = safe_float(chart_df["final_match_score"].iloc[-1]) if not chart_df.empty else 0.0
    avg_score = safe_float(chart_df["final_match_score"].mean()) if not chart_df.empty else 0.0
    best_score = safe_float(chart_df["final_match_score"].max()) if not chart_df.empty else 0.0
    main_pattern = max([(weak_count, 'Weak'), (moderate_count, 'Moderate'), (good_count, 'Good')])[1]

    history_col1, history_col2 = st.columns(2, gap="large")

    with history_col1:
        st.markdown("""
        <div style='background:linear-gradient(180deg,#fff7f8 0%,#f9eeef 100%);border:1px solid #e7c3b4;border-left:6px solid #9f3448;border-radius:24px;padding:1.15rem 1.2rem;box-shadow:0 8px 18px rgba(25,14,36,0.04);'>
            <div style='display:inline-flex;align-items:center;padding:0.3rem 0.78rem;border-radius:999px;background:#fff;border:1px solid #e2c1b6;color:#8f6f7b;font-size:0.72rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.7rem;'>History</div>
            <div style='font-family:"Inter Tight","Inter",sans-serif;font-size:1.15rem;font-weight:800;color:#241226;margin-bottom:0.25rem;'>Alignment band distribution</div>
            <div style='font-size:0.9rem;color:#6d5a68;line-height:1.7;'>How many saved analyses fall into weak, moderate, and good match ranges.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:1.35rem;'></div>", unsafe_allow_html=True)
        st.altair_chart(bar_chart, use_container_width=True)
        st.markdown(f"""
        <div style='display:flex;gap:0.8rem;margin-top:0.75rem;flex-wrap:wrap;'>
            <div style='font-size:0.88rem;padding:0.5rem 0.8rem;border-radius:12px;background:#fff;border:1px solid #ead1c8;color:#8f4455;'><strong>Weak:</strong> {weak_count}</div>
            <div style='font-size:0.88rem;padding:0.5rem 0.8rem;border-radius:12px;background:#fff;border:1px solid #ead1c8;color:#8f4455;'><strong>Moderate:</strong> {moderate_count}</div>
            <div style='font-size:0.88rem;padding:0.5rem 0.8rem;border-radius:12px;background:#fff;border:1px solid #ead1c8;color:#8f4455;'><strong>Good:</strong> {good_count}</div>
        </div>
        <div style='margin-top:0.8rem;font-size:0.9rem;color:#6d5a68;line-height:1.7;padding:0.95rem 1rem;border-radius:18px;background:#fff8f4;border:1px solid #ead1c8;'>
            <strong style='color:#241226;'>Main pattern:</strong> {main_pattern} appears most often in your saved runs.
        </div>
        """, unsafe_allow_html=True)

    with history_col2:
        st.markdown("""
        <div style='background:linear-gradient(180deg,#fff7f8 0%,#f9eeef 100%);border:1px solid #e7c3b4;border-left:6px solid #9f3448;border-radius:24px;padding:1.15rem 1.2rem;box-shadow:0 8px 18px rgba(25,14,36,0.04);'>
            <div style='display:inline-flex;align-items:center;padding:0.3rem 0.78rem;border-radius:999px;background:#fff;border:1px solid #e2c1b6;color:#8f6f7b;font-size:0.72rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.7rem;'>Trend</div>
            <div style='font-family:"Inter Tight","Inter",sans-serif;font-size:1.15rem;font-weight:800;color:#241226;margin-bottom:0.25rem;'>Match score movement over time</div>
            <div style='font-size:0.9rem;color:#6d5a68;line-height:1.7;'>Follow the score pattern across saved runs. The dashed line marks the 70% stronger-alignment line.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:1.35rem;'></div>", unsafe_allow_html=True)
        st.altair_chart(trend_chart, use_container_width=True)
        st.markdown(f"""
        <div style='display:flex;gap:0.8rem;margin-top:0.75rem;flex-wrap:wrap;'>
            <div style='font-size:0.88rem;padding:0.5rem 0.8rem;border-radius:12px;background:#fff;border:1px solid #ead1c8;color:#8f4455;'><strong>Latest:</strong> {latest_score:.1f}%</div>
            <div style='font-size:0.88rem;padding:0.5rem 0.8rem;border-radius:12px;background:#fff;border:1px solid #ead1c8;color:#8f4455;'><strong>Average:</strong> {avg_score:.1f}%</div>
            <div style='font-size:0.88rem;padding:0.5rem 0.8rem;border-radius:12px;background:#fff;border:1px solid #ead1c8;color:#8f4455;'><strong>Best:</strong> {best_score:.1f}%</div>
            <div style='font-size:0.88rem;padding:0.5rem 0.8rem;border-radius:12px;background:#fff;border:1px solid #ead1c8;color:#8f4455;'><strong>70% line</strong></div>
            <div style='font-size:0.88rem;padding:0.5rem 0.8rem;border-radius:12px;background:#fff;border:1px solid #ead1c8;color:#8f4455;'><strong>{len(chart_df)} saved runs</strong></div>
        </div>
        <div style='margin-top:0.8rem;font-size:0.9rem;color:#6d5a68;line-height:1.7;padding:0.95rem 1rem;border-radius:18px;background:#fff8f4;border:1px solid #ead1c8;'>
            <strong style='color:#241226;'>Quick read:</strong> Use this chart to see whether recent saved analyses are improving and how often results get close to or pass the 70% line.
        </div>
        """, unsafe_allow_html=True)


def clean_preview_text(text: str, max_len: int = 260) -> str:
    text = "" if pd.isna(text) else str(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "No preview is available for the current selection."
    return text if len(text) <= max_len else text[: max_len - 3].rstrip() + "..."


def render_minimal_tab_intro(kicker: str, title: str, sentence: str = "", extra_class: str = ""):
    sentence_html = f"<div class='tab-minimal-copy'>{html.escape(sentence)}</div>" if sentence else ""
    hero_class = f"tab-minimal-hero {extra_class}".strip()
    st.markdown(_html(f"""
    <div class='{hero_class}'>
        <div class='tab-minimal-kicker'>{html.escape(kicker)}</div>
        <div class='tab-minimal-title'>{html.escape(title)}</div>
        {sentence_html}
    </div>
    """), unsafe_allow_html=True)


def render_batch_score_chart(num_df: pd.DataFrame):
    if num_df is None or num_df.empty:
        return
    required_cols = {"label", "model", "score", "semantic", "lexical", "coverage"}
    if not required_cols.issubset(num_df.columns):
        return

    chart_df = num_df.copy()
    for col in ["score", "semantic", "lexical", "coverage"]:
        chart_df[col] = pd.to_numeric(chart_df[col], errors="coerce").fillna(0)
    chart_df["model"] = chart_df["model"].astype(str).fillna("Manual")
    chart_df["label"] = chart_df["label"].astype(str)
    if chart_df.empty:
        return

    # Inner function for leaderboard cards
    def _render_leaderboard_cards(rank_df, title, subtitle, entity_col='model'):
        st.markdown(_html(f"""
        <div class='chart-panel'>
            <div class='chart-panel-title'>{html.escape(title)}</div>
            <div class='chart-panel-copy'>{html.escape(subtitle)}</div>
        </div>
        """), unsafe_allow_html=True)
        
        medal_map = {0: '🥇', 1: '🥈', 2: '🥉'}
        
        for idx, (_, row) in enumerate(rank_df.iterrows()):
            medal = medal_map.get(idx, f"#{idx+1}")
            score = safe_float(row['score'])
            metric_line = f"Meaning {safe_float(row.get('semantic',0)):.0f}% · Text {safe_float(row.get('lexical',0)):.0f}% · Key points {safe_float(row.get('coverage',0)):.0f}%"
            count_text = f"{int(row['responses'])} responses reviewed" if 'responses' in row.index else 'overall fit'
            card_class = "leaderboard-card leaderboard-card-top" if idx == 0 else "leaderboard-card"
            
            st.markdown(_html(f"""
            <div class='{card_class}' style='margin-bottom: 0.8rem;'>
                <div class='leaderboard-rank'>{medal}</div>
                <div class='leaderboard-main'>
                    <div class='leaderboard-title'>{html.escape(str(row[entity_col]))}</div>
                    <div class='leaderboard-meta'>{html.escape(metric_line)}</div>
                    <div class='leaderboard-track'><div class='leaderboard-fill' style='width:{min(score,100):.1f}%;'></div></div>
                </div>
                <div class='leaderboard-side'>
                    <div class='leaderboard-score'>{score:.1f}%</div>
                    <div class='leaderboard-note'>{html.escape(count_text)}</div>
                </div>
            </div>
            """), unsafe_allow_html=True)

    # Inner function for grouped bars
    def _render_grouped_bars(metric_df, entity_col, title, subtitle):
        chart_src = metric_df[[entity_col, 'semantic', 'lexical', 'coverage']].copy()
        chart_src = chart_src.rename(columns={entity_col: 'Entity', 'semantic': 'Meaning match', 'lexical': 'Text match', 'coverage': 'Key points'})
        chart_long = chart_src.melt(id_vars='Entity', var_name='Metric', value_name='Score')
        metric_order = ['Meaning match', 'Text match', 'Key points']
        entity_order = metric_df[entity_col].astype(str).tolist()
        color_range = ['#c94f63', '#d9785f', '#c78900', '#8b6771']

        base = alt.Chart(chart_long).encode(
            x=alt.X('Metric:N', sort=metric_order, title=None, axis=alt.Axis(labelAngle=0, labelPadding=14, labelFontSize=12, labelColor='#5d3945', labelFontWeight='bold')),
            xOffset=alt.XOffset('Entity:N', sort=entity_order),
            y=alt.Y('Score:Q', title='Score (%)', scale=alt.Scale(domain=[0,100]), axis=alt.Axis(values=[0,20,40,60,80,100], labelColor='#7a6874', titleColor='#5d3945', gridColor='#ead8d0')),
            color=alt.Color('Entity:N', sort=entity_order, legend=alt.Legend(title='Model / response', orient='bottom', labelColor='#5d3945', titleColor='#221221'), scale=alt.Scale(range=color_range[:max(1,len(entity_order))])),
            tooltip=[alt.Tooltip('Entity:N', title='Item'), alt.Tooltip('Metric:N'), alt.Tooltip('Score:Q', format='.1f')]
        )
        bars = base.mark_bar(size=34, cornerRadiusTopLeft=10, cornerRadiusTopRight=10)
        text_marks = alt.Chart(chart_long).mark_text(dy=-10, color='#5d3945', fontSize=11, fontWeight='bold').encode(
            x=alt.X('Metric:N', sort=metric_order), 
            xOffset=alt.XOffset('Entity:N', sort=entity_order), 
            y=alt.Y('Score:Q', scale=alt.Scale(domain=[0,100])), 
            text=alt.Text('Score:Q', format='.0f')
        )
        final_chart = (
            alt.layer(bars, text_marks)
            .properties(height=320, background='#fbf5f1')
            .configure_view(stroke='#ead8d0', fill='#fffaf7')
            .configure_axis(domainColor='#d9b6a8', tickColor='#d9b6a8')
            .configure_legend(orient='bottom', labelColor='#5d3945', titleColor='#221221')
        )
        st.markdown(_html(f"""
        <div style='margin-bottom:1rem;'>
            <div style='font-family:"Inter Tight","Inter",sans-serif;font-size:1.15rem;font-weight:800;color:#160029;margin-bottom:0.35rem;'>{html.escape(title)}</div>
        </div>
        """), unsafe_allow_html=True)
        st.altair_chart(final_chart, use_container_width=True, theme=None)
        metric_means = {
            'Meaning match': safe_float(metric_df['semantic'].mean()),
            'Text match': safe_float(metric_df['lexical'].mean()),
            'Key points': safe_float(metric_df['coverage'].mean()),
        }
        strongest_metric = max(metric_means, key=metric_means.get)
        top_entity = metric_df.sort_values('score', ascending=False).iloc[0][entity_col]
        st.markdown(f"<div class='chart-conclusion'><strong>Conclusion:</strong> <strong>{html.escape(str(top_entity))}</strong> stays strongest overall, and <strong>{html.escape(str(strongest_metric))}</strong> is the clearest place to see the biggest gap.</div>", unsafe_allow_html=True)

    # Main logic
    multi_model = chart_df["model"].nunique() > 1 and not set(chart_df["model"].unique()).issubset({"Manual"})
    c1, c2 = st.columns(2, gap="medium")

    if multi_model:
        summary_df = (
            chart_df.groupby("model", as_index=False)
            .agg(score=("score", "mean"), semantic=("semantic", "mean"), lexical=("lexical", "mean"), coverage=("coverage", "mean"), responses=("label", "count"))
            .sort_values("score", ascending=False)
            .reset_index(drop=True)
        )
        with c1:
            _render_leaderboard_cards(summary_df, '🏆 Model Leaderboard', 'This ranking shows which AI model gave the strongest overall average fit.', entity_col='model')
            best = summary_df.iloc[0]
            second = summary_df.iloc[1] if len(summary_df) > 1 else None
            margin = f" by {best['score'] - second['score']:.1f} points" if second is not None else ''
            st.markdown(f"<div class='chart-conclusion' style='margin-top:0.5rem;'><strong>Conclusion:</strong> <strong>{html.escape(str(best['model']))}</strong> is the most reliable overall performer{margin}.</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div style='height:4.2rem;'></div>", unsafe_allow_html=True)
            _render_grouped_bars(summary_df, 'model', 'Metric comparison by model', 'Each metric group shows the models side by side.')
    else:
        summary_df = (
            chart_df.groupby('label', as_index=False)
            .agg(score=('score','mean'), semantic=('semantic','mean'), lexical=('lexical','mean'), coverage=('coverage','mean'))
            .sort_values('score', ascending=False)
            .reset_index(drop=True)
        )
        with c1:
            _render_leaderboard_cards(summary_df, '🏆 Response Leaderboard', 'A simple ranking of which response matched the fatwa reference best overall.', entity_col='label')
            best = summary_df.iloc[0]
            st.markdown(f"<div class='chart-conclusion' style='margin-top:0.5rem;'><strong>Conclusion:</strong> <strong>{html.escape(str(best['label']))}</strong> gives the strongest overall fit at {best['score']:.1f}%.</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div style='height:4.2rem;'></div>", unsafe_allow_html=True)
            _render_grouped_bars(summary_df, 'label', 'Metric comparison by response', 'Side-by-side bars make it easier to compare meaning match, text match, and key fatwa points.')
            
def render_similarity_breakdown(bundle: dict):
    """Render the similarity breakdown — original design: sim-lite shell + note + 4 metric cards."""
    final_match_score = safe_float(bundle.get("final_match_score"))
    lexical_score     = safe_float(bundle.get("lexical_score"))
    semantic_score    = safe_float(bundle.get("semantic_score"))
    coverage_score    = safe_float(bundle.get("coverage_score"))
    mean_alignment    = safe_float(bundle.get("mean_alignment"))

    score_color  = score_status_color(final_match_score)
    ring_degrees = max(0.0, min(360.0, final_match_score * 3.6))
    conclusion_label = "Strong Alignment" if final_match_score >= 70 else "Moderate Alignment" if final_match_score >= 50 else "Low Alignment"
    conclusion_copy  = ("This final score means the answer is close to the fatwa and gets most important points right."
                        if final_match_score >= 70 else
                        "This final score means the answer is partly correct, but some important points still need checking."
                        if final_match_score >= 50 else
                        "This final score means the answer is not close enough to the fatwa yet and needs careful review.")

    st.markdown(_html(f"""
    <div class='sim-lite-shell'>
        <div class='sim-lite-head'>
            <div>
                <div class='sim-lite-kicker'>Similarity breakdown</div>
                <div class='sim-lite-title'>Final Score</div>
            </div>
            <div class='sim-lite-pill' style='background:{score_color}14;border-color:{score_color};color:{score_color};'>{final_match_score:.1f}%</div>
        </div>
        <div class='sim-lite-hero'>
            <div class='sim-lite-ring' style='background:conic-gradient({score_color} 0deg {ring_degrees:.1f}deg,#ead1c8 {ring_degrees:.1f}deg 360deg);'>
                <div class='sim-lite-ring-inner'>
                    <strong style='color:{score_color};'>{int(round(final_match_score))}</strong>
                    <span>Final score</span>
                </div>
            </div>
            <div class='sim-lite-summary'>
                <div class='sim-lite-summary-title'>{html.escape(conclusion_label)}</div>
                <div class='sim-lite-summary-copy alt'>{html.escape(conclusion_copy)}</div>
            </div>
        </div>
        <div class='sim-lite-top-note'>
            <span class='sim-lite-top-note-title'>How to read this section</span>
            <span class='sim-lite-top-note-copy'>Read each box separately: text = wording overlap, meaning = closest meaning, key points = important fatwa conditions found, overall fit = strength across the matched state rulings.</span>
        </div>
    </div>
    """), unsafe_allow_html=True)

    render_beautiful_metric_grid(lexical_score, semantic_score, coverage_score, mean_alignment)


def render_single_review_result_dashboard(bundle: dict):
    final_match_score = safe_float(bundle.get("final_match_score"))
    semantic_score = safe_float(bundle.get("semantic_score"))
    lexical_score = safe_float(bundle.get("lexical_score"))
    coverage_score = safe_float(bundle.get("coverage_score"))
    mean_alignment = safe_float(bundle.get("mean_alignment"))
    topic_label = str(bundle.get("topic_label", "-"))
    specific_issue = str(bundle.get("specific_issue", "-"))
    best_state = str(bundle.get("best_state_name", "-"))
    recommendation_label = str(bundle.get("recommendation_label", "Moderate Alignment"))
    recommendation_reason = str(bundle.get("recommendation_reason", ""))
    compliance_level = str(bundle.get("compliance_level", "Unclear"))
    confidence = str(bundle.get("confidence", "Unknown"))
    fatwa_text = str(bundle.get("fatwa_text", "")).strip()
    issue_name = str(bundle.get("issue_name", "")).strip() or topic_label or "N/A"
    matched_list = bundle.get("matched_list", [])
    missing_list = bundle.get("missing_list", [])
    tone = score_status_color(final_match_score)

    preview_reference = html.escape((fatwa_text[:180] + "...") if fatwa_text and len(fatwa_text) > 180 else (fatwa_text or "No text available"))
    result_title = "Strong Alignment" if final_match_score >= 70 else "Moderate Alignment" if final_match_score >= 50 else "Low Alignment"
    result_summary = "This answer is generally close to the matched fatwa and covers the main ruling points." if final_match_score >= 70 else "This answer is partly correct, but some important ruling details still need human review." if final_match_score >= 50 else "This answer is still too far from the fatwa, so it needs careful checking before anyone relies on it."
    action_label = "Good to Use" if final_match_score >= 70 else "Needs Review" if final_match_score >= 50 else "Not Reliable"
    action_note = "Use as a strong draft, then do a quick final check." if final_match_score >= 70 else "Check the fatwa text before accepting this answer." if final_match_score >= 50 else "Rewrite or review this answer manually first."
    confidence_copy = "The topic match looks clear." if confidence == "High" else "The topic match looks fairly clear." if confidence == "Medium" else "The topic match is less certain."
    compliance_copy = "It follows the ruling well." if compliance_level == "Fully Compliant" else "Some parts fit, but it still needs review." if compliance_level == "Partially Compliant" else "It does not fit the ruling closely." if compliance_level == "Non-Compliant" else "The status is not clear yet and needs manual review."
    recommendation_copy = html.escape(recommendation_reason) if recommendation_reason else html.escape(result_summary)
    review_status_copy = html.escape("This final score means the answer is close to the fatwa and gets most important points right." if final_match_score >= 70 else "This final score means the answer is partly correct, but some important points still need checking." if final_match_score >= 50 else "This final score means the answer is not close enough to the fatwa yet and needs careful review.")

    st.markdown(_html(f"""
    <div class='result-hero-card'>
        <div class='result-hero-main'>
            <div class='result-hero-kicker'>Review result</div>
            <div class='result-hero-title'>{html.escape(topic_label)}</div>
            <div class='result-hero-copy'>{html.escape(specific_issue)}</div>
            <div style='margin-top:0.9rem;display:flex;flex-wrap:wrap;gap:0.55rem;'>
                <span style='display:inline-flex;align-items:center;padding:0.42rem 0.82rem;border-radius:999px;background:{tone}12;border:1px solid {tone};color:{tone};font-size:0.8rem;font-weight:800;'>{format_percent(final_match_score,1)} overall</span>
                <span style='display:inline-flex;align-items:center;padding:0.42rem 0.82rem;border-radius:999px;background:#fff;border:1px solid #ead1c8;color:#6d5a68;font-size:0.8rem;font-weight:700;'>Confidence: {html.escape(confidence_copy)}</span>
                <span style='display:inline-flex;align-items:center;padding:0.42rem 0.82rem;border-radius:999px;background:#fff;border:1px solid #ead1c8;color:#6d5a68;font-size:0.8rem;font-weight:700;'>Status: {html.escape(compliance_copy)}</span>
            </div>
        </div>
    </div>
    """), unsafe_allow_html=True)

    # Use a properly formatted f-string without syntax errors
    result_html = f"""
    <div class="result-cards-grid">
        <div style='background:linear-gradient(180deg,#fff8f4 0%,#fff2ef 100%);border:1px solid #ead1c8;border-top:5px solid {tone};border-radius:28px;padding:1.2rem 1.2rem 1.1rem 1.2rem;box-shadow:0 14px 28px rgba(25,14,36,0.05);min-width:0;'>
            <div style='font-size:0.72rem;font-weight:850;letter-spacing:0.11em;text-transform:uppercase;color:#a3195b;margin-bottom:0.65rem;'>Result summary</div>
            <div style='display:flex;align-items:flex-start;justify-content:space-between;gap:0.8rem;margin-bottom:0.8rem;'>
                <div>
                    <div style='font-family:"Inter Tight","Inter",sans-serif;font-size:1.55rem;font-weight:850;letter-spacing:-0.03em;line-height:1.04;color:#241226;margin-bottom:0.2rem;'>{html.escape(result_title)}</div>
                    <div style='font-size:0.96rem;line-height:1.72;color:#6d5a68;max-width:95%;'>{html.escape(recommendation_copy)}</div>
                </div>
                <div style='min-width:88px;height:88px;border-radius:22px;background:linear-gradient(135deg,{tone} 0%,#ffffff 145%);padding:1px;box-shadow:0 10px 22px rgba(25,14,36,0.10);'>
                    <div style='height:100%;border-radius:21px;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;'>
                        <div style='font-family:"Inter Tight","Inter",sans-serif;font-size:1.7rem;font-weight:800;color:{tone};line-height:1;'>{int(round(final_match_score))}</div>
                        <div style='font-size:0.72rem;color:#8b6771;margin-top:0.18rem;'>score</div>
                    </div>
                </div>
            </div>
            <div style='margin:0.15rem 0 0.75rem 0;padding:0.95rem 1rem;border-radius:20px;background:linear-gradient(135deg,#fff 0%,#fff6f2 100%);border:1px solid #ead1c8;box-shadow:0 8px 18px rgba(25,14,36,0.04);'>
                <div style='font-size:0.72rem;font-weight:850;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin-bottom:0.18rem;'>Review status</div>
                <div style='font-family:"Inter Tight","Inter",sans-serif;font-size:1.2rem;font-weight:800;line-height:1.15;color:{tone};margin-bottom:0.22rem;'>{html.escape(action_label)}</div>
                <div style='font-size:0.9rem;line-height:1.7;color:#6d5a68;'>{review_status_copy}</div>
            </div>
            <div style='display:grid;gap:0.55rem;'>
                <div style='padding:0.82rem 0.9rem;border-radius:18px;background:#fff;border:1px solid #ead1c8;display:flex;gap:0.65rem;align-items:flex-start;'><div style='width:28px;height:28px;border-radius:10px;background:{tone}14;color:{tone};display:flex;align-items:center;justify-content:center;font-weight:900;'>1</div><div style='font-size:0.88rem;line-height:1.6;color:#6d5a68;'><strong style='color:#241226;'>What this means:</strong> {html.escape(result_summary)}</div></div>
                <div style='padding:0.82rem 0.9rem;border-radius:18px;background:#fff;border:1px solid #ead1c8;display:flex;gap:0.65rem;align-items:flex-start;'><div style='width:28px;height:28px;border-radius:10px;background:#f7ece7;color:#b24758;display:flex;align-items:center;justify-content:center;font-weight:900;'>2</div><div style='font-size:0.88rem;line-height:1.6;color:#6d5a68;'><strong style='color:#241226;'>What to do:</strong> {html.escape(action_note)}</div></div>
                <div style='padding:0.82rem 0.9rem;border-radius:18px;background:#fff;border:1px solid #ead1c8;display:flex;gap:0.65rem;align-items:flex-start;'><div style='width:28px;height:28px;border-radius:10px;background:#f7ece7;color:#b24758;display:flex;align-items:center;justify-content:center;font-weight:900;'>3</div><div style='font-size:0.88rem;line-height:1.6;color:#6d5a68;'><strong style='color:#241226;'>History label:</strong> {html.escape(recommendation_label)}</div></div>
            </div>
        </div>
        <div style='background:linear-gradient(180deg,#fffdfb 0%,#faf3f7 100%);border:1px solid #ead1c8;border-top:5px solid #773344;border-radius:28px;padding:1.2rem 1.2rem 1.1rem 1.2rem;box-shadow:0 14px 28px rgba(25,14,36,0.05);min-width:0;'>
            <div style='font-size:0.72rem;font-weight:850;letter-spacing:0.11em;text-transform:uppercase;color:#a3195b;margin-bottom:0.65rem;'>Closest fatwa source</div>
            <div style='display:flex;align-items:flex-start;justify-content:space-between;gap:0.75rem;margin-bottom:0.8rem;'>
                <div style='min-width:0;'>
                    <div style='font-family:"Inter Tight","Inter",sans-serif;font-size:1.5rem;font-weight:800;letter-spacing:-0.03em;line-height:1.08;color:#241226;overflow-wrap:anywhere;'>{html.escape(best_state)}</div>
                    <div style='margin-top:0.22rem;font-size:0.92rem;line-height:1.65;color:#6d5a68;'>This is the state fatwa source that matched the answer most closely.</div>
                </div>
                <div style='padding:0.42rem 0.8rem;border-radius:999px;background:#fff;border:1px solid #ead1c8;color:#773344;font-size:0.76rem;font-weight:800;white-space:nowrap;'>Best source</div>
            </div>
            <div style='display:grid;grid-template-columns:1fr 1fr;gap:0.7rem;margin-bottom:0.7rem;'>
                <div style='padding:0.9rem 0.95rem;border-radius:18px;background:#fff;border:1px solid #ead1c8;'>
                    <div style='font-size:0.7rem;font-weight:850;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin-bottom:0.22rem;'>Issue matched</div>
                    <div style='font-size:0.98rem;line-height:1.58;color:#241226;font-weight:700;overflow-wrap:anywhere;'>{html.escape(issue_name)}</div>
                </div>
                <div style='padding:0.9rem 0.95rem;border-radius:18px;background:#fff;border:1px solid #ead1c8;'>
                    <div style='font-size:0.7rem;font-weight:850;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin-bottom:0.22rem;'>Why it matters</div>
                    <div style='font-size:0.88rem;line-height:1.6;color:#6d5a68;'>Read this fatwa first when you want to confirm whether the AI answer can be accepted.</div>
                </div>
            </div>
            <div style='padding:0.95rem 1rem;border-radius:20px;background:linear-gradient(135deg,#fff 0%,#fff8f4 100%);border:1px solid #ead1c8;'>
                <div style='font-size:0.7rem;font-weight:850;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin-bottom:0.28rem;'>Reference preview</div>
                <div style='font-size:0.92rem;line-height:1.72;color:#6d5a68;overflow-wrap:anywhere;'>{preview_reference}</div>
            </div>
        </div>
        <div style='background:linear-gradient(180deg,#fffdf8 0%,#f9f1ec 100%);border:1px solid #ead1c8;border-top:5px solid #d98c3f;border-radius:28px;padding:1.2rem 1.2rem 1.1rem 1.2rem;box-shadow:0 14px 28px rgba(25,14,36,0.05);min-width:0;'>
            <div style='font-size:0.72rem;font-weight:850;letter-spacing:0.11em;text-transform:uppercase;color:#a3195b;margin-bottom:0.65rem;'>Easy score guide</div>
            <div style='display:grid;gap:0.7rem;'>
                <div style='padding:0.9rem 0.95rem;border-radius:18px;background:#fff;border:1px solid #ead1c8;'><div style='display:flex;align-items:center;justify-content:space-between;gap:0.6rem;'><div><div style='font-size:0.82rem;font-weight:800;color:#8b6771;text-transform:uppercase;letter-spacing:0.06em;'>Meaning</div><div style='font-size:0.8rem;color:#6d5a68;margin-top:0.12rem;'>Same ruling idea</div></div><div style='font-family:"Inter Tight","Inter",sans-serif;font-size:1.4rem;font-weight:800;color:#241226;'>{format_percent(semantic_score,1)}</div></div><div style='height:8px;border-radius:999px;background:#f1e2da;overflow:hidden;margin-top:0.55rem;'><div style='height:100%;width:{max(0,min(100,safe_float(semantic_score)))}%;background:linear-gradient(90deg,#773344 0%,#b24758 100%);border-radius:999px;'></div></div></div>
                <div style='padding:0.9rem 0.95rem;border-radius:18px;background:#fff;border:1px solid #ead1c8;'><div style='display:flex;align-items:center;justify-content:space-between;gap:0.6rem;'><div><div style='font-size:0.82rem;font-weight:800;color:#8b6771;text-transform:uppercase;letter-spacing:0.06em;'>Text</div><div style='font-size:0.8rem;color:#6d5a68;margin-top:0.12rem;'>Similar wording</div></div><div style='font-family:"Inter Tight","Inter",sans-serif;font-size:1.4rem;font-weight:800;color:#241226;'>{format_percent(lexical_score,1)}</div></div><div style='height:8px;border-radius:999px;background:#f1e2da;overflow:hidden;margin-top:0.55rem;'><div style='height:100%;width:{max(0,min(100,safe_float(lexical_score)))}%;background:linear-gradient(90deg,#d98c3f 0%,#f1a208 100%);border-radius:999px;'></div></div></div>
                <div style='padding:0.9rem 0.95rem;border-radius:18px;background:#fff;border:1px solid #ead1c8;'><div style='display:flex;align-items:center;justify-content:space-between;gap:0.6rem;'><div><div style='font-size:0.82rem;font-weight:800;color:#8b6771;text-transform:uppercase;letter-spacing:0.06em;'>Key points</div><div style='font-size:0.8rem;color:#6d5a68;margin-top:0.12rem;'>Important conditions found</div></div><div style='font-family:"Inter Tight","Inter",sans-serif;font-size:1.4rem;font-weight:800;color:#241226;'>{format_percent(coverage_score,1)}</div></div><div style='height:8px;border-radius:999px;background:#f1e2da;overflow:hidden;margin-top:0.55rem;'><div style='height:100%;width:{max(0,min(100,safe_float(coverage_score)))}%;background:linear-gradient(90deg,#3a7f56 0%,#06A77D 100%);border-radius:999px;'></div></div></div>
            </div>
            <div style='margin-top:0.78rem;padding:0.95rem 1rem;border-radius:20px;background:linear-gradient(135deg,#fff 0%,#fff7f1 100%);border:1px solid #ead1c8;'>
                <div style='display:flex;align-items:flex-end;justify-content:space-between;gap:0.6rem;'>
                    <div>
                        <div style='font-size:0.72rem;font-weight:850;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin-bottom:0.22rem;'>Overall fit</div>
                        <div style='font-family:"Inter Tight","Inter",sans-serif;font-size:2rem;font-weight:800;line-height:1;color:#241226;'>{format_percent(mean_alignment,1)}</div>
                    </div>
                    <div style='padding:0.38rem 0.7rem;border-radius:999px;background:#fff;border:1px solid #ead1c8;color:#773344;font-size:0.76rem;font-weight:800;'>State average</div>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(result_html, unsafe_allow_html=True)

    k1, k2 = st.columns(2, gap="medium")
    with k1:
        matched_html = "".join(f"<span class='keyword-match'>{html.escape(kw)}</span>" for kw in matched_list) if matched_list else "<div class='small-note'>No important fatwa points were clearly identified here.</div>"
        st.markdown(_html(f"""
        <div class='points-card coverage-card'>
            <div class='points-card-header'>Mentioned by the AI</div>
            <div class='keyword-container'>{matched_html}</div>
        </div>
        """), unsafe_allow_html=True)
    with k2:
        missing_html = "".join(f"<span class='keyword-miss'>{html.escape(kw)}</span>" for kw in missing_list) if missing_list else "<div class='small-note'>No major missing points were detected.</div>"
        st.markdown(_html(f"""
        <div class='points-card coverage-card'>
            <div class='points-card-header'>Still missing</div>
            <div class='keyword-container'>{missing_html}</div>
        </div>
        """), unsafe_allow_html=True)

# =========================================================
# COMPACT HEADER
# =========================================================
def render_dashboard_shell_header(title="AI Fatwa Alignment System", subtitle="How closely do AI responses align with Malaysian Assisted Reproductive Technology (ART) rulings?", kicker="Fatwa Alignment Dashboard"):
    st.markdown(
        """
        <style>
        .dashboard-shell-header { margin-bottom: 0; }
        /* Remove any extra spacing Streamlit adds before tabs */
        .stTabs { margin-top: 0 !important; }
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]:first-child {
            gap: 0 !important;
        }
        </style>
        <div class="dashboard-shell-header"></div>
        """,
        unsafe_allow_html=True,
    )
    render_dashboard_header(title=title, subtitle=subtitle, kicker=kicker)


section_banner_path = resolve_header_banner_path()

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-clean-header compact-sidebar-header">
            <div class="sidebar-kicker-line"></div>
            <h1 class="sidebar-title">Fatwa Alignment</h1>
            <h3 class="sidebar-subtitle">Review, score, and compare how well AI answers align with Malaysian ART fatwa guidance.</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not sbert_is_ready():
        st.markdown(
            "<div class='msg-box msg-warning'><strong>⚠️ Semantic model not loaded.</strong> Some scores may be missing or incomplete. Please check your sentence-transformers installation.</div>",
            unsafe_allow_html=True,
        )

    total_analyses = len(st.session_state.analysis_history)
    score_list = [
        safe_float(r.get("final_match_score", r.get("alignment_score", np.nan)), np.nan)
        for r in st.session_state.analysis_history
    ]
    score_list = [s for s in score_list if not pd.isna(s)]
    avg_score_sidebar = np.mean(score_list) if score_list else 0
    high_count = sum(1 for s in score_list if get_score_tier(s) == "good")
    moderate_count = sum(1 for s in score_list if get_score_tier(s) == "moderate")
    weak_count = sum(1 for s in score_list if get_score_tier(s) == "weak")
    recent_topics = recent_topics_summary(st.session_state.analysis_history, max_items=5)
    score_health = (high_count / len(score_list) * 100) if score_list else 0
    current_bundle = build_sidebar_latest_bundle()

    render_sidebar_workspace(
        title="Review workspace",
        subtitle="Analyze one answer, compare batches, and inspect fatwa evidence.",
        primary_label="Saved runs",
        primary_value=str(total_analyses),
        secondary_label="Average",
        secondary_value=f"{avg_score_sidebar:.1f}%",
    )

    render_sidebar_section(
        "Recent focus",
        "◎",
        render_sidebar_topic_pills(recent_topics if recent_topics else ["No recent topics"])
    )

    render_sidebar_section(
        "Session pulse",
        "◔",
        render_sidebar_progress([
            {"name": "Strong matches", "value": score_health, "label": f"{high_count}", "tone": "green"},
            {"name": "Moderate cases", "value": (moderate_count / len(score_list) * 100) if score_list else 0, "label": f"{moderate_count}", "tone": "yellow"},
            {"name": "Weak cases", "value": (weak_count / len(score_list) * 100) if score_list else 0, "label": f"{weak_count}", "tone": "red"},
        ])
    )

    render_sidebar_section(
        "How to use this page",
        "✓",
        build_sidebar_score_guide_html()
    )


# =========================================================
# GLOBAL HEADER + TABS
# =========================================================
render_dashboard_shell_header(
    title="AI Fatwa Alignment Dashboard",
    subtitle="How closely do AI Responses align with Malaysian ART rulings?",
    kicker="⚖️  Fatwa Alignment Reviewer · Assisted Reproductive Technology (ART)",
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    " Single Review",
    " Batch Review",
    " History & Export",
    " Fatwa Explorer",
    " Topic Explorer",
])

# =========================================================
# TAB 1 - Single Review
# =========================================================
with tab1:
    render_minimal_tab_intro(
        "Single review",
        "Closest fatwa alignment",
        "Check one answer and see how closely it matches the most relevant fatwa.",
        extra_class="single-review-hero"
    )

    # ── Shared section header style ───────────────────────────────────────────
    st.markdown("""
    <style>
    .tab1-section {
        margin: 0 0 0.5rem 0;
    }
    .tab1-section-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 0.55rem;
    }
    .tab1-section-step {
        width: 22px; height: 22px; border-radius: 6px;
        background: linear-gradient(135deg, #773344, #a3195b);
        color: #fff; font-size: 0.65rem; font-weight: 900;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
    }
    .tab1-section-title {
        font-size: 0.72rem; font-weight: 800; text-transform: uppercase;
        letter-spacing: 0.1em; color: #5a3d4a;
    }
    .tab1-section-rule {
        flex: 1; height: 1px;
        background: linear-gradient(90deg, #e2ccd4, transparent);
    }
    .tab1-two-col {
        display: grid;
        grid-template-columns: 0.58fr 0.42fr;
        gap: 1rem;
        align-items: start;
    }
    </style>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # SECTION 1 — Input
    # ══════════════════════════════════════════════════════
    st.markdown("""
    <div class="tab1-section">
        <div class="tab1-section-header">
            <div class="tab1-section-step">1</div>
            <div class="tab1-section-title">Load or paste an AI answer</div>
            <div class="tab1-section-rule"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    review_left, review_right = st.columns([0.58, 0.42], gap="medium")

    with review_left:
        # ── Dataset loader ────────────────────────────────────────────────────
        if AI_DATASET_AVAILABLE:
            question_map = (
                fatwa_df[["question_id", "question_text"]]
                .drop_duplicates("question_id")
                .sort_values("question_id")
            )
            question_options = {
                row["question_text"] if row["question_text"] else row["question_id"]: row["question_id"]
                for _, row in question_map.iterrows()
            }
            available_models = sorted(ai_answer_df["model"].unique().tolist())

            selected_question_text = st.session_state.get("ds_question_select")
            if not selected_question_text or selected_question_text not in question_options:
                selected_question_text = next(iter(question_options.keys()))

            selected_model = st.session_state.get("ds_model_select")
            if not selected_model or not available_models or selected_model not in available_models:
                selected_model = available_models[0] if available_models else ""

            # Loader header — redesigned beautiful card
            st.markdown(_html("""
            <div class='ds-loader-card'>
                <div class='ds-loader-top'>
                    <div>
                        <div class='ds-loader-kicker'>📂 Load a Saved Answer</div>
                        <div class='ds-loader-title'>Quick load from dataset</div>
                    </div>
                    <div class='ds-loader-badge'>⬇ Select &amp; Load</div>
                </div>
                <div class='ds-loader-copy'>Pick a question and AI model to instantly load a saved response into the review area below.</div>
                <div style='display:grid; grid-template-columns: 1fr 1fr auto; gap:0.6rem; align-items:end;'>
                    <div><div class='ds-loader-col-label'>📋 Question</div></div>
                    <div><div class='ds-loader-col-label'>🤖 AI Model</div></div>
                    <div><div class='ds-loader-col-label'>⚡ Action</div></div>
                </div>
            </div>
            """), unsafe_allow_html=True)

            ctrl1, ctrl2, ctrl3 = st.columns([0.48, 0.32, 0.20], gap="small")
            with ctrl1:
                selected_question_text = st.selectbox(
                    "Question",
                    options=list(question_options.keys()),
                    index=list(question_options.keys()).index(selected_question_text),
                    key="ds_question_select",
                    label_visibility="collapsed"
                )
            with ctrl2:
                selected_model = st.selectbox(
                    "AI Model",
                    options=available_models,
                    index=available_models.index(selected_model) if selected_model in available_models else 0,
                    key="ds_model_select",
                    label_visibility="collapsed"
                )
            with ctrl3:
                load_btn = st.button(
                    "Load",
                    use_container_width=True,
                    key="ds_load_btn_primary",
                    help="Load the selected response"
                )

            selected_qid = question_options[selected_question_text]
            question_subset = ai_answer_df[ai_answer_df["question_id"] == selected_qid].copy()
            selected_match = question_subset[question_subset["model"] == selected_model]

            if load_btn:
                if not selected_match.empty:
                    st.session_state["ai_input"] = selected_match.iloc[0]["ai_answer_raw"]
                    st.session_state["load_success_toast"] = True
                    st.rerun()
                else:
                    st.warning(f"⚠️ No saved response found for model '{selected_model}'")

            st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)

        # ── Text area ─────────────────────────────────────────────────────────
        st.markdown(_html("""
            <div class='input-editor-shell-v2'>
                <div class='input-editor-v2-head'>
                    <div>
                        <div class='input-editor-kicker'>✍️ YOUR RESPONSE</div>
                        <div class='input-editor-title'>Paste the AI answer you want to check</div>
                        <div class='input-editor-copy' style='font-size: 0.7rem; color: #7a6874; margin-top: 0.2rem;'>
                            💡 Longer, detailed answers give more accurate scores.
                        </div>
                    </div>
                    <div class='input-editor-chip'>Single review</div>
                </div>
            </div>
        """), unsafe_allow_html=True)

        st.markdown('<div class="input-editor-v2-body">', unsafe_allow_html=True)
        ai_response = st.text_area(
            "AI Response Input",
            height=140,
            placeholder="Example: \"In Islam, surrogacy is generally not permitted because it can mix lineages...\"\n\nPaste your full AI-generated answer here.",
            key="ai_input",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.pop('load_success_toast', False):
            show_success_toast_center(
                "✓ Response loaded successfully!",
                ["Ready for review", "Click Analyze to see results"]
            )

    # ── Right column: score summary ───────────────────────────────────────────
    with review_right:
        st.markdown("""
        <div class="tab1-section">
            <div class="tab1-section-header">
                <div class="tab1-section-step">2</div>
                <div class="tab1-section-title">Score summary</div>
                <div class="tab1-section-rule"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div class='single-review-right-col'>", unsafe_allow_html=True)
        if st.session_state.get("current_analysis"):
            render_similarity_breakdown(st.session_state["current_analysis"])
        else:
            st.markdown(_html(f"""
            <div class='empty-review-card'>
                <div>
                    <div class='empty-review-top'>
                        <div>
                            <div class='workspace-kicker'>Similarity breakdown</div>
                            <h3 class='empty-review-title'>Your result summary will appear here</h3>
                            <div class='empty-review-copy'>Run a single review to see the final score, meaning match, keyword coverage, and the closest state fatwa in one place.</div>
                        </div>
                        <div class='empty-review-pill'>Ready to analyze</div>
                    </div>
                    <div class='empty-review-list'>
                        <div class='empty-review-item'><div class='empty-review-icon'>1</div><div><strong>Paste a complete answer</strong><span>Longer and more specific AI answers usually produce more reliable similarity and coverage scoring.</span></div></div>
                        <div class='empty-review-item'><div class='empty-review-icon'>2</div><div><strong>Review the matched fatwa</strong><span>The system compares the answer with the closest question, then checks which state fatwa aligns best.</span></div></div>
                        <div class='empty-review-item'><div class='empty-review-icon'>3</div><div><strong>Use the score carefully</strong><span>The final score supports review, but the fatwa text and missing points still matter for interpretation.</span></div></div>
                    </div>
                </div>
                <div class='empty-review-footer'>
                    <div class='empty-review-stat'><div class='empty-review-stat-label'>Analyses saved</div><div class='empty-review-stat-value'>{total_analyses}</div></div>
                    <div class='empty-review-stat'><div class='empty-review-stat-label'>Average score</div><div class='empty-review-stat-value'>{avg_score_sidebar:.1f}%</div></div>
                    <div class='empty-review-stat'><div class='empty-review-stat-label'>Good threshold</div><div class='empty-review-stat-value'>70%+</div></div>
                </div>
            </div>
            """), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # ACTION ROW — Analyze + Clear, always under both columns
    # ══════════════════════════════════════════════════════
    st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
    b1, b2, _spacer = st.columns([0.38, 0.20, 0.42], gap="small")
    with b1:
        analyze_btn = st.button("🔍 Analyze This Response", use_container_width=True, key="analyze_single")
    with b2:
        clear_btn = st.button("🗑️ Clear History", use_container_width=True, key="clear_all_single")

    if clear_btn:
        clear_history()
        show_success_toast_center("✓ History cleared successfully!", ["All saved analyses have been removed"])
        st.rerun()

    if analyze_btn:
        if not ai_response.strip():
            st.warning("⚠️ Please paste or load an AI response before running the analysis.")
        elif not ensure_analysis_dependencies():
            st.stop()
        else:
            with st.spinner("🔍 Analyzing response — this may take a few seconds..."):
                ensure_similarity_engine_loaded()
                best_question, question_scores = detect_best_question(ai_response, fatwa_df)
                detected_subset = fatwa_df[fatwa_df["question_id"] == best_question["question_id"]].copy()
                best_state, state_results = unpack_state_comparison(compare_states_within_question(ai_response, detected_subset))
                if not best_state or state_results.empty:
                    st.warning("⚠️ No state-level fatwa comparison could be generated. Try a longer or more specific answer.")
                    st.stop()

                topic_label = infer_topic_label(best_question, detected_subset)
                specific_issue = get_specific_issue(best_question)
                confidence = best_question.get("confidence", "Unknown")
                final_match_score = safe_float(best_state["best_match_alignment"])
                lexical_score = safe_float(best_state["lexical_similarity"])
                semantic_score = safe_float(best_state["semantic_similarity"])
                coverage_score = safe_float(best_state["coverage"])
                mean_alignment = safe_float(best_state["mean_alignment"])

                recommendation = get_recommendation(semantic_score, coverage_score, final_match_score)
                recommendation_label = recommendation["label"]
                recommendation_reason = recommendation["reason"]

                compliance_result = classify_shariah_compliance(
                    final_match_score=final_match_score,
                    lexical_similarity=lexical_score,
                    semantic_similarity=semantic_score,
                    coverage=coverage_score,
                    confidence=confidence,
                    matched_keywords=best_state.get("matched_keywords", "-"),
                    missing_keywords=best_state.get("missing_keywords", "-"),
                    ai_text=ai_response
                )

                compliance_level = compliance_result["level"]
                compliance_reason = compliance_result["reason"]

                analysis_record = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "topic_label": topic_label,
                    "specific_issue": specific_issue,
                    "detection_confidence": confidence,
                    "best_state": best_state["state"],
                    "final_match_score": round(float(final_match_score), 2) if not pd.isna(final_match_score) else 0.0,
                    "mean_alignment": round(float(mean_alignment), 2) if not pd.isna(mean_alignment) else 0.0,
                    "lexical_similarity": round(float(lexical_score), 2) if not pd.isna(lexical_score) else 0.0,
                    "semantic_similarity": round(float(semantic_score), 2) if not pd.isna(semantic_score) else 0.0,
                    "coverage": round(float(coverage_score), 2) if not pd.isna(coverage_score) else 0.0,
                    "compliance_level": compliance_level,
                    "compliance_reason": compliance_reason,
                    "recommendation_label": recommendation_label,
                    "recommendation_reason": recommendation_reason,
                }
                add_to_history(analysis_record)

                st.session_state.current_analysis = {
                    "best_state_name": best_state.get("state", "-"),
                    "topic_label": topic_label,
                    "specific_issue": specific_issue,
                    "confidence": confidence,
                    "final_match_score": final_match_score,
                    "lexical_score": lexical_score,
                    "semantic_score": semantic_score,
                    "coverage_score": coverage_score,
                    "best_match_alignment": safe_float(best_state.get("best_match_alignment")),
                    "mean_alignment": mean_alignment,
                    "recommendation_label": recommendation_label,
                    "recommendation_reason": recommendation_reason,
                    "compliance_level": compliance_level,
                    "compliance_reason": compliance_reason,
                    "fatwa_text": best_state.get("fatwa_text", ""),
                    "issue_name": best_state.get("issue", ""),
                    "matched_list": best_state.get("matched_keywords", "-").split(", ") if best_state.get("matched_keywords", "-") != "-" else [],
                    "missing_list": best_state.get("missing_keywords", "-").split(", ") if best_state.get("missing_keywords", "-") != "-" else [],
                    "question_scores": question_scores.to_dict("records") if isinstance(question_scores, pd.DataFrame) else [],
                    "state_results": state_results.to_dict("records") if isinstance(state_results, pd.DataFrame) else [],
                }
                
                st.session_state["show_detail_cards"] = False  # collapse on new analysis
                st.rerun()

    if st.session_state.get("current_analysis"):
        if "show_detail_cards" not in st.session_state:
            st.session_state["show_detail_cards"] = False

        current_preview = st.session_state["current_analysis"]
        final_match_score_preview = safe_float(current_preview.get("final_match_score"))
        result_label_preview = (
            "Strong Alignment" if final_match_score_preview >= 70
            else "Moderate Alignment" if final_match_score_preview >= 50
            else "Low Alignment"
        )
        detail_state_preview = "Open" if st.session_state["show_detail_cards"] else "Hidden"
        detail_button_label = "Hide detailed review" if st.session_state["show_detail_cards"] else "View detailed review"
        detail_button_help = (
            "Hide the larger evidence cards."
            if st.session_state["show_detail_cards"]
            else "Show the larger evidence cards, source card, score guide, and key points."
        )
        detail_icon = "▲" if st.session_state["show_detail_cards"] else "▼"
        detail_panel_class = "detail-toggle-card detail-toggle-card-open" if st.session_state["show_detail_cards"] else "detail-toggle-card"

        st.markdown(_html(f"""
        <div class='tab1-section' style='margin-top:1rem;'>
            <div class='tab1-section-header'>
                <div class='tab1-section-step'>3</div>
                <div class='tab1-section-title'>Detailed review</div>
                <div class='tab1-section-rule'></div>
            </div>
        </div>
        """), unsafe_allow_html=True)

        detail_card_col, detail_button_col = st.columns([0.65, 0.35], gap="medium")
        with detail_card_col:
            st.markdown(_html(f"""
            <div class='{detail_panel_class}'>
                <div class='detail-toggle-icon'>{detail_icon}</div>
                <div class='detail-toggle-main'>
                    <div class='detail-toggle-kicker'>Evidence drawer</div>
                    <div class='detail-toggle-title'>Detailed Review &amp; Fatwa Evidence</div>
                    <div class='detail-toggle-sub'>Source, score guide, and key points are kept behind this drawer so the main score stays clean.</div>
                </div>
                <div class='detail-toggle-chips'>
                    <span>{html.escape(result_label_preview)}</span>
                    <span>{format_percent(final_match_score_preview, 1)}</span>
                    <span>{detail_state_preview}</span>
                </div>
            </div>
            """), unsafe_allow_html=True)
        with detail_button_col:
            st.markdown("<div class='detail-toggle-button-wrap'>", unsafe_allow_html=True)
            if st.button(detail_button_label, key="detail_toggle_btn", use_container_width=True, help=detail_button_help):
                st.session_state["show_detail_cards"] = not st.session_state["show_detail_cards"]
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state["show_detail_cards"]:
            st.markdown("<div class='detail-drawer-body'>", unsafe_allow_html=True)
            render_single_review_result_dashboard(st.session_state["current_analysis"])
            st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("📊 View advanced comparison details", expanded=False):
            current = st.session_state["current_analysis"]
            question_scores_df = pd.DataFrame(current.get("question_scores", []))
            state_results_df = pd.DataFrame(current.get("state_results", []))
            topic_debug_df = build_advanced_topic_display(question_scores_df) if not question_scores_df.empty else pd.DataFrame()
            state_debug_df = build_advanced_state_display(state_results_df) if not state_results_df.empty else pd.DataFrame()

            render_technical_help_box()
            st.markdown("<div class='tech-review-title'>How the system chose the topic</div>", unsafe_allow_html=True)
            st.markdown(build_light_table_html(topic_debug_df), unsafe_allow_html=True)
            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
            st.markdown("<div class='tech-review-title'>How the system chose the best fatwa source</div>", unsafe_allow_html=True)
            st.markdown(build_light_table_html(state_debug_df), unsafe_allow_html=True)
            
# =========================================================
# TAB 2 - Batch Review
# =========================================================
with tab2:
    render_minimal_tab_intro(
        "Batch review",
        "Structured comparison across responses",
        "Compare several answers side by side and see which model performs better."
    )

    batch_mode = st.radio(
        "Choose input method",
        options=["Load from dataset", "Manual input"],
        horizontal=True,
        key="batch_mode_radio"
    )

    responses_to_run = []

    if batch_mode == "Load from dataset" and AI_DATASET_AVAILABLE:
        available_models_b = sorted(ai_answer_df["model"].unique().tolist())
        question_map_b = (
            fatwa_df[["question_id", "question_text"]]
            .drop_duplicates("question_id")
            .sort_values("question_id")
        )

        st.markdown("<div class='batch-filter-grid'>", unsafe_allow_html=True)
        bc1, bc2 = st.columns([0.4, 0.6])
        with bc1:
            selected_models_b = st.multiselect(
                "Select AI Models",
                options=available_models_b,
                default=available_models_b,
                key="batch_models_select"
            )
        with bc2:
            q_options_b = {
                (row["question_text"] if row["question_text"] else row["question_id"]): row["question_id"]
                for _, row in question_map_b.iterrows()
            }
            selected_questions_b = st.multiselect(
                "Select Questions (leave empty = all)",
                options=list(q_options_b.keys()),
                key="batch_questions_select"
            )
        st.markdown("</div>", unsafe_allow_html=True)

        filtered_df = ai_answer_df.copy()
        if selected_models_b:
            filtered_df = filtered_df[filtered_df["model"].isin(selected_models_b)]
        if selected_questions_b:
            selected_qids = [q_options_b[q] for q in selected_questions_b]
            filtered_df = filtered_df[filtered_df["question_id"].isin(selected_qids)]

        st.markdown(f"<div class='batch-selection-note'><strong>{len(filtered_df)}</strong> responses are ready for batch review.</div>", unsafe_allow_html=True)

        for _, row in filtered_df.iterrows():
            q_text = question_map_b[question_map_b["question_id"] == row["question_id"]]["question_text"]
            label = q_text.iloc[0][:60] if not q_text.empty else row["question_id"]
            responses_to_run.append((label, row["model"], row["ai_answer_raw"]))

        run_batch_btn = st.button(
            f"▶ Run Batch Analysis ({len(responses_to_run)} responses)",
            use_container_width=True,
            key="batch_dataset_run"
        )

    else:
        mc1, mc2 = st.columns([0.68, 0.32])
        with mc1:
            st.markdown("<div class='input-editor-shell batch-manual-shell'><div class='input-editor-head'><div><div class='input-editor-kicker'>Manual batch input</div><div class='input-editor-title'>Paste one answer per block</div></div><div class='input-editor-chip'>Split with ---</div></div></div>", unsafe_allow_html=True)
            batch_responses = st.text_area(
                "Enter multiple responses (separate with ---)",
                height=280,
                placeholder="Paste the first answer here...\n\n---\n\nPaste the second answer here...\n\n---\n\nAdd as many as you need, separated by ---",
                key="batch_input"
            )
        with mc2:
            st.markdown(_html("""
            <div class='batch-guide-card'>
                <div class='batch-guide-kicker'>How to paste responses</div>
                <div class='batch-guide-step'><strong>1.</strong><span>Paste the first answer as a full paragraph.</span></div>
                <div class='batch-guide-step'><strong>2.</strong><span>Add <strong>---</strong> on a new line.</span></div>
                <div class='batch-guide-step'><strong>3.</strong><span>Paste the next answer and repeat for the rest.</span></div>
            </div>
            """), unsafe_allow_html=True)

        if batch_responses.strip():
            manual_texts = [r.strip() for r in batch_responses.split("---") if r.strip()]
            responses_to_run = [(f"Response {i+1}", "Manual", t) for i, t in enumerate(manual_texts)]

        st.markdown(f"<div class='batch-selection-note'><strong>{len(responses_to_run)}</strong> responses are ready for batch review.</div>", unsafe_allow_html=True)
        run_batch_btn = st.button("▶  Run Batch Analysis", use_container_width=True, key="batch_analyze")

    if run_batch_btn:
        if not responses_to_run:
            st.warning("⚠️ Please load or paste at least one response before running batch analysis.")
        elif not ensure_analysis_dependencies():
            st.stop()
        else:
            with st.spinner("🔍 Running batch analysis — please wait..."):
                batch_results = []
                batch_numeric = []
                for label, model_name, response_text in responses_to_run:
                    best_question_row, question_scores_df = detect_best_question(response_text, fatwa_df)
                    if best_question_row is None or question_scores_df.empty:
                        continue
                    current_question_id = str(best_question_row["question_id"])
                    state_subset = fatwa_df[fatwa_df["question_id"].astype(str).str.strip() == current_question_id].copy()
                    best_state_bundle, state_results_df = unpack_state_comparison(compare_states_within_question(response_text, state_subset))
                    if state_results_df.empty or not best_state_bundle:
                        continue
                    best_state_row = state_results_df.sort_values("alignment_score", ascending=False).iloc[0]
                    interp_label, _ = interpret(best_state_row["alignment_score"])
                    compliance = classify_shariah_compliance(
                        final_match_score=best_state_row["alignment_score"],
                        lexical_similarity=best_state_row.get("lexical_similarity", 0),
                        semantic_similarity=best_state_row.get("semantic_similarity", 0),
                        coverage=best_state_row.get("coverage", 0),
                        confidence=best_question_row.get("confidence", "Unknown"),
                        matched_keywords=best_state_row.get("matched_keywords", "-"),
                        missing_keywords=best_state_row.get("missing_keywords", "-"),
                        ai_text=response_text,
                    )
                    batch_results.append({
                        "Label": label,
                        "Model": model_name,
                        "Detected Topic": short_topic_label(best_question_row.get("issue", "Related Fatwa Topic")),
                        "Best State": best_state_row.get("state", "-"),
                        "Final Match": format_percent(best_state_row.get("alignment_score", 0), 1),
                        "Meaning Match": format_percent(best_state_row.get("semantic_similarity", 0), 1),
                        "Text Match": format_percent(best_state_row.get("lexical_similarity", 0), 1),
                        "Key Points": format_percent(best_state_row.get("coverage", 0), 1),
                        "Recommendation": interp_label,
                        "Compliance": compliance.get("level", "Unclear"),
                    })
                    batch_numeric.append({
                        "label": label,
                        "model": model_name,
                        "score": safe_float(best_state_row.get("alignment_score", 0)),
                        "semantic": safe_float(best_state_row.get("semantic_similarity", 0)),
                        "lexical": safe_float(best_state_row.get("lexical_similarity", 0)),
                        "coverage": safe_float(best_state_row.get("coverage", 0)),
                    })

                st.session_state.batch_results_df = pd.DataFrame(batch_results) if batch_results else None
                st.session_state.batch_numeric_df = pd.DataFrame(batch_numeric) if batch_numeric else None

    if st.session_state.get("batch_results_df") is None:
        pass
    elif st.session_state.batch_results_df.empty:
        st.warning("No valid responses were available for batch analysis.")
    else:
        batch_df = st.session_state.batch_results_df.copy()
        num_df = st.session_state.batch_numeric_df.copy() if st.session_state.get("batch_numeric_df") is not None else pd.DataFrame()

        st.markdown("<div class='batch-results-shell'><div class='batch-results-title'>Batch analysis summary</div><div class='batch-results-copy'>See which model performed better, which state matched best, and how strong each answer was overall.</div></div>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        summary_cards = [
            ("Responses reviewed", str(len(batch_df))),
            ("Average fit", f"{num_df['score'].mean():.1f}%" if not num_df.empty else "-"),
            ("Average meaning match", f"{num_df['semantic'].mean():.1f}%" if not num_df.empty else "-"),
            ("Average key points", f"{num_df['coverage'].mean():.1f}%" if not num_df.empty else "-"),
        ]
        for col, (label, value) in zip([m1, m2, m3, m4], summary_cards):
            with col:
                st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value' style='font-size:1.5rem'>{value}</div></div>", unsafe_allow_html=True)

        render_batch_score_chart(num_df)
        st.markdown("<div class='batch-readable-note'><strong>Quick guide:</strong> final match is the overall result, meaning match shows how close the answer is in meaning, text match shows wording overlap, and key points shows how many important fatwa conditions were covered.</div>", unsafe_allow_html=True)
        batch_page_size = 5
        batch_start, batch_end, batch_page, batch_total_pages = paginate_with_buttons("batch_results", len(batch_df), batch_page_size)
        st.markdown(build_light_table_html(batch_df.iloc[batch_start:batch_end]), unsafe_allow_html=True)
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button("📥  Download as CSV", batch_df.to_csv(index=False), f"batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)
        with dl2:
            if EXCEL_AVAILABLE:
                st.download_button("📊  Download as Excel", export_to_excel(batch_df), f"batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)


# =========================================================
# TAB 3 - History & Export
# =========================================================
with tab3:
    render_minimal_tab_intro(
        "History and export",
        "Saved alignment runs",
        "Review past results, spot score trends, and export your analysis records in one place."
    )

    if st.session_state.analysis_history:
        history_df = get_history_df()

        st.markdown("<h3 class='section-subtitle'>Performance Dashboard</h3>", unsafe_allow_html=True)
        h1, h2, h3, h4 = st.columns(4)

        with h1:
            st.markdown(
                f"<div class='metric-card'><div class='metric-label'>Total Analyses</div><div class='metric-value'>{len(history_df)}</div></div>",
                unsafe_allow_html=True
            )
        with h2:
            st.markdown(
                f"<div class='metric-card'><div class='metric-label'>Average Score</div><div class='metric-value'>{history_df['final_match_score'].mean():.1f}%</div></div>",
                unsafe_allow_html=True
            )
        with h3:
            st.markdown(
                f"<div class='metric-card'><div class='metric-label'>Highest Score</div><div class='metric-value'>{history_df['final_match_score'].max():.1f}%</div></div>",
                unsafe_allow_html=True
            )
        with h4:
            recommendation_mode = history_df["recommendation_label"].mode()
            most_common_recommendation = recommendation_mode.iloc[0] if not recommendation_mode.empty else "-"
            st.markdown(
                f"<div class='metric-card'><div class='metric-label'>Most Common Recommendation</div><div class='metric-value' style='font-size:1.25rem;'>{most_common_recommendation}</div></div>",
                unsafe_allow_html=True
            )

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        st.markdown("<h3 class='section-subtitle'>History Overview</h3>", unsafe_allow_html=True)
        st.markdown("<div class='system-plain-note'>The history overview tracks how saved analyses move across the main fit score over time and how results distribute across alignment bands.</div>", unsafe_allow_html=True)

        render_history_overview(history_df)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        st.markdown("<h3 class='section-subtitle'>History Table</h3>", unsafe_allow_html=True)
        st.markdown(_html("""
        <div class='history-table-shell'>
            <div class='history-table-head'>
                <div>
                    <div class='history-table-title'>Compact review table</div>
                    <div class='history-table-copy'>This version keeps only the fields users usually compare first, so the table fits the screen more cleanly without horizontal swiping.</div>
                </div>
                <div class='history-table-pill'>Screen-fit layout</div>
            </div>
        """), unsafe_allow_html=True)

        search_term = st.text_input(
            "🔍 Search by topic, issue, state, recommendation, or compliance",
            placeholder="Enter search term...",
            key="history_search"
        )
        display_df = build_history_display_table(history_df)

        if search_term:
            filtered_df = display_df[
                display_df["Topic"].astype(str).str.contains(search_term, case=False, na=False) |
                display_df["Issue"].astype(str).str.contains(search_term, case=False, na=False) |
                display_df["Best Match"].astype(str).str.contains(search_term, case=False, na=False) |
                display_df["Review"].astype(str).str.contains(search_term, case=False, na=False)
            ]
        else:
            filtered_df = display_df

        history_page_size = 5
        history_start, history_end, history_page, history_total_pages = paginate_with_buttons("history_table", len(filtered_df), history_page_size)
        if len(filtered_df):
            st.markdown(
                f"<div class='pager-bar'><div class='pager-note'>Showing {history_start + 1} to {min(history_end, len(filtered_df))} of {len(filtered_df)} analyses.</div><div class='pager-note'>Page {history_page} of {history_total_pages}</div></div>",
                unsafe_allow_html=True
            )
        st.markdown(build_light_table_html(filtered_df.iloc[history_start:history_end]), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("<h3 class='section-subtitle'>Export Options</h3>", unsafe_allow_html=True)

        export_df = history_df.copy()
        if "timestamp" in export_df.columns:
            export_df["_sort_time"] = pd.to_datetime(export_df["timestamp"], errors="coerce")
            export_df = export_df.sort_values("_sort_time", ascending=False).drop(columns=["_sort_time"])

        export_df["final_match_score"] = export_df["final_match_score"].apply(lambda x: format_percent(x, 1))
        export_df["mean_alignment"] = export_df["mean_alignment"].apply(lambda x: format_percent(x, 1))
        export_df["word_match"] = export_df["lexical_similarity"].apply(lambda x: format_percent(x, 1))
        export_df["meaning_match"] = export_df["semantic_similarity"].apply(lambda x: format_percent(x, 1))
        export_df["key_fatwa_points"] = export_df["coverage"].apply(lambda x: format_percent(x, 1))

        export_df = export_df.rename(columns={
            "timestamp": "Timestamp",
            "topic_label": "Detected Topic",
            "specific_issue": "Specific Issue",
            "detection_confidence": "Topic Detection Confidence",
            "best_state": "Best Match",
            "recommendation_label": "Recommendation",
            "recommendation_reason": "Recommendation Reason",
            "compliance_level": "Compliance",
            "compliance_reason": "Compliance Reason",
        })

        export_df["Detected Topic"] = export_df["Detected Topic"].apply(short_topic_label)

        export_df = export_df[
            [
                "Timestamp",
                "Detected Topic",
                "Specific Issue",
                "Topic Detection Confidence",
                "Best Match",
                "Recommendation",
                "Recommendation Reason",
                "Compliance",
                "Compliance Reason",
                "final_match_score",
                "mean_alignment",
                "word_match",
                "meaning_match",
                "key_fatwa_points"
            ]
        ]

        e1, e2, e3, e4 = st.columns(4)

        with e1:
            csv = export_df.to_csv(index=False)
            st.download_button(
                "📄  Download as CSV",
                csv,
                f"analysis_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True
            )

        with e2:
            if EXCEL_AVAILABLE:
                excel = export_to_excel(export_df)
                st.download_button(
                    "📊  Download as Excel",
                    excel,
                    f"analysis_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.info("Excel export unavailable. Please install openpyxl.")

        with e3:
            json_str = export_df.to_json(indent=2, orient="records")
            st.download_button(
                "📋  Download as JSON",
                json_str,
                f"analysis_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json",
                use_container_width=True
            )

        with e4:
            summary = f"""Analysis Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}


=== STATISTICS ===
Total Analyses: {len(history_df)}
Average Score: {history_df['final_match_score'].mean():.1f}%
Highest Score: {history_df['final_match_score'].max():.1f}%
Lowest Score: {history_df['final_match_score'].min():.1f}%

=== RECOMMENDATION ===
{history_df['recommendation_label'].value_counts().to_string()}

=== COMPLIANCE ===
{history_df['compliance_level'].value_counts().to_string()}

=== TOPICS ===
{history_df['topic_label'].value_counts().head(10).to_string()}
"""
            st.download_button(
                "📑  Download Summary Report",
                summary,
                f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain",
                use_container_width=True
            )

        if st.button("🗑️ Clear All History", use_container_width=True, key="clear_history_tab"):
            clear_history()
            show_success_toast_center("✓ History cleared successfully!", ["All saved analyses have been removed"])
            st.rerun()
    else:
        st.markdown("""
        <div class="msg-box msg-warning" style="text-align:center; padding:3rem;">
            <h3 style="margin-bottom:0.75rem;">📂 No History Yet</h3>
            <p class="small-note">You haven't run any analyses yet. Go to <strong>Single Review</strong> or <strong>Batch Review</strong> and analyse some responses — they will appear here automatically.</p>
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# TAB 4 - Fatwa Explorer
# =========================================================
with tab4:
    render_minimal_tab_intro(
        "Fatwa explorer",
        "Reference fatwa search and browsing",
        "Browse the reference database by topic, state, or keyword."
    )
    st.markdown("""
    <div class='explorer-instruction-card'>
        <div class='explorer-instruction-title'>How to use this page</div>
        <div class='explorer-instruction-copy'>Start by choosing a topic, then narrow by state or source if needed. Use <strong>Show all</strong> to clear the filters again. The cards below update instantly, so you can move from a broad browse to the exact official fatwa text more easily.</div>
    </div>
    """, unsafe_allow_html=True)

    explorer_topics = ["All topics"] + sorted([t for t in fatwa_df["issue"].fillna("").astype(str).str.strip().unique().tolist() if t])
    explorer_states = ["All states / sources"] + sorted([s for s in fatwa_df["state"].fillna("").astype(str).str.strip().unique().tolist() if s])

    ex1, ex2, ex3 = st.columns([1, 1, 0.42], gap='medium')
    with ex1:
        st.markdown("<div class='browse-inline-head'>📚 Choose a topic</div>", unsafe_allow_html=True)
        selected_topic_filter = st.selectbox(
            "Choose a topic",
            explorer_topics,
            key="fatwa_explorer_topic",
            label_visibility='collapsed'
        )
    with ex2:
        st.markdown("<div class='browse-inline-head'>📍 Choose a state / source</div>", unsafe_allow_html=True)
        selected_state_filter = st.selectbox(
            "Choose a state / source",
            explorer_states,
            key="fatwa_explorer_state",
            label_visibility='collapsed'
        )
    with ex3:
        st.markdown("<div class='browse-inline-head'>🔄 Reset filters</div>", unsafe_allow_html=True)
        st.button("Show all", key="browse_reset_filters", use_container_width=True, on_click=reset_fatwa_explorer_filters)

    active_topic = selected_topic_filter if selected_topic_filter != 'All topics' else 'All topics'
    active_state = selected_state_filter if selected_state_filter != 'All states / sources' else 'All states / sources'
    st.markdown(f"<div class='browse-filter-chip-row'><span class='browse-filter-chip'>📌 Topic: {html.escape(active_topic)}</span><span class='browse-filter-chip'>📍 State / source: {html.escape(active_state)}</span></div>", unsafe_allow_html=True)

    filtered_fatwa = fatwa_df.copy()
    if selected_topic_filter != "All topics":
        filtered_fatwa = filtered_fatwa[filtered_fatwa["issue"].astype(str).str.strip() == selected_topic_filter]
    if selected_state_filter != "All states / sources":
        filtered_fatwa = filtered_fatwa[filtered_fatwa["state"].astype(str).str.strip() == selected_state_filter]

    result_topics = filtered_fatwa["issue"].astype(str).str.strip().replace('', np.nan).dropna().nunique()
    result_states = filtered_fatwa["state"].astype(str).str.strip().replace('', np.nan).dropna().nunique()
    st.markdown(f"""
    <div class='explorer-orb-grid'>
        <div class='explorer-orb'>
            <div class='explorer-orb-icon'>📄</div>
            <div><div class='explorer-orb-label'>Records found</div><div class='explorer-orb-value'>{len(filtered_fatwa)}</div><div class='explorer-orb-note'>Official fatwa entries currently visible</div></div>
        </div>
        <div class='explorer-orb'>
            <div class='explorer-orb-icon'>🏷️</div>
            <div><div class='explorer-orb-label'>Topics shown</div><div class='explorer-orb-value'>{result_topics}</div><div class='explorer-orb-note'>Distinct issue groups in the filtered list</div></div>
        </div>
        <div class='explorer-orb'>
            <div class='explorer-orb-icon'>🗺️</div>
            <div><div class='explorer-orb-label'>States shown</div><div class='explorer-orb-value'>{result_states}</div><div class='explorer-orb-note'>States or sources represented right now</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not filtered_fatwa.empty:
        display_rows = filtered_fatwa.head(8).reset_index(drop=True)
        for start_idx in range(0, len(display_rows), 2):
            cols = st.columns(2, gap='medium')
            for col_idx, row_idx in enumerate(range(start_idx, min(start_idx + 2, len(display_rows)))):
                row = display_rows.iloc[row_idx]
                with cols[col_idx]:
                    render_fatwa_reference_card(
                        state=str(row.get("state", "")),
                        topic=str(row.get("issue", "")),
                        fatwa_text=str(row.get("fatwa_text", "")),
                        question_text=str(row.get("question_text", "")).strip(),
                    )
    else:
        st.markdown("""
        <div class="msg-box msg-warning" style="text-align:center; padding:2rem;">
            <strong>📭 No matching fatwa records found.</strong><br>
            <span class="small-note">Try selecting a different topic or state, or click <em>Show all</em> to clear your filters.</span>
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# TAB 5 - Topic Explorer 
# =========================================================
with tab5:
    html_escape_mod = html  # use top-level html import already available

    render_minimal_tab_intro(
        "Topic explorer",
        "Compare states on a topic",
        "See topic coverage, compare states, and read fatwa texts side by side."
    )
    st.markdown("""
    <div class='explorer-instruction-card'>
        <div class='explorer-instruction-title'>How the topic view works</div>
        <div class='explorer-instruction-copy'>This page reads from your saved analysis history. The charts update as your history grows, so the rankings and difficulty view always reflect the latest saved runs. After that, choose one topic below to compare state coverage and read the fatwa wording side by side.</div>
    </div>
    """, unsafe_allow_html=True)

    analysis_df = fatwa_df.copy()
    analysis_df["issue"] = analysis_df["issue"].fillna("").astype(str).str.strip()
    analysis_df["state"] = analysis_df["state"].fillna("").astype(str).str.strip()
    analysis_df["fatwa_text"] = analysis_df["fatwa_text"].fillna("").astype(str).str.strip()
    analysis_df["question_text"] = analysis_df["question_text"].fillna("").astype(str).str.strip()
    analysis_df["issue_display"] = analysis_df["issue"].replace("", "Uncategorized")

    all_topics = sorted(analysis_df["issue_display"].unique().tolist())
    all_states = sorted([s for s in analysis_df["state"].unique().tolist() if s])

    topic_counts_full = (
        analysis_df.groupby("issue_display")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.markdown(
            f"<div class='metric-card'><div class='metric-label'>Topics in Database</div>"
            f"<div class='metric-value'>{len(all_topics)}</div></div>",
            unsafe_allow_html=True
        )
    with sc2:
        st.markdown(
            f"<div class='metric-card'><div class='metric-label'>Total Fatwa Entries</div>"
            f"<div class='metric-value'>{len(analysis_df)}</div></div>",
            unsafe_allow_html=True
        )
    with sc3:
        st.markdown(
            f"<div class='metric-card'><div class='metric-label'>States & Sources</div>"
            f"<div class='metric-value'>{len(all_states)}</div></div>",
            unsafe_allow_html=True
        )
    with sc4:
        most_covered = topic_counts_full.iloc[0]["issue_display"] if not topic_counts_full.empty else "-"
        st.markdown(
            f"<div class='metric-card'><div class='metric-label'>Most Covered Topic</div>"
            f"<div class='metric-value' style='font-size:1.1rem; line-height:1.3;'>"
            f"{short_topic_label(most_covered)}</div></div>",
            unsafe_allow_html=True
        )

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    chart_bg = "transparent"
    label_col = "#132C47"

    st.markdown("<h3 class='section-subtitle'>📊 Fatwa Distribution by Category</h3>", unsafe_allow_html=True)
    st.markdown("""
    <div class="msg-box msg-info" style="margin-bottom:0.6rem; border-left-color:#773344; background:#faf3f7;">
        This shows what proportion of all fatwa records fall under each broad topic category.
        Hover over a slice to see the exact count and percentage.
    </div>
    """, unsafe_allow_html=True)

    def broad_category(topic):
        t = str(topic).lower()
        if "abortion" in t:
            return "Abortion"
        if "contra" in t or "contraceptive" in t:
            return "Contraceptives"
        if "clone" in t or "cloning" in t or "stem cell" in t:
            return "Cloning & Stem Cell"
        if "ivf" in t or "gamete" in t or "surrogacy" in t or "sperm" in t or "milk bank" in t:
            return "ART & Reproductive"
        return "Other"

    donut_df = analysis_df.copy()
    donut_df["category"] = donut_df["issue_display"].apply(broad_category)
    donut_counts = (
        donut_df.groupby("category")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    total_donut = donut_counts["count"].sum()
    donut_counts["pct"] = (donut_counts["count"] / total_donut * 100).round(1)

    donut_palette = ["#160029", "#B24758", "#D98C3F", "#8E2F4F", "#6F3A4F"]

    d1, d2 = st.columns([1.2, 0.8])

    with d1:
        donut_chart = (
            alt.Chart(donut_counts)
            .mark_arc(innerRadius=70, outerRadius=120, cornerRadius=6, padAngle=0.02)
            .encode(
                theta=alt.Theta("count:Q", stack=True),
                color=alt.Color(
                    "category:N",
                    scale=alt.Scale(
                        domain=donut_counts["category"].tolist(),
                        range=donut_palette[: len(donut_counts)],
                    ),
                    legend=alt.Legend(
                        title=None,
                        labelFontSize=12,
                        labelColor=label_col,
                        symbolSize=120,
                        orient="bottom",
                        columns=2,
                    ),
                ),
                tooltip=[
                    alt.Tooltip("category:N", title="Category"),
                    alt.Tooltip("count:Q", title="Fatwas"),
                    alt.Tooltip("pct:Q", title="Percentage", format=".1f"),
                ],
            )
            .properties(height=360, padding={"top": 30, "bottom": 10, "left": 10, "right": 10}, background=chart_bg)
            .configure_view(stroke=None, fill=chart_bg)
        )
        st.altair_chart(donut_chart, use_container_width=True)

    with d2:
        st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
        for _, row in donut_counts.iterrows():
            cat = row["category"]
            cnt = row["count"]
            pct = row["pct"]
            cidx = donut_counts["category"].tolist().index(cat)
            c_hex = donut_palette[cidx % len(donut_palette)]
            st.markdown(f"""
            <div class="donut-insight-card">
                <div class="donut-insight-accent" style="background:{c_hex};"></div>
                <div class="donut-insight-body">
                    <div class="donut-insight-name">{cat}</div>
                    <div class="donut-insight-stats">
                        <span class="donut-insight-count">{cnt}</span>
                        <span class="donut-insight-pct">&nbsp;fatwas &nbsp;·&nbsp; {pct}%</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    st.markdown("<h3 class='section-subtitle'>🤖 AI Alignment Score by Topic</h3>", unsafe_allow_html=True)
    st.markdown("""
    <div class="msg-box msg-info" style="margin-bottom:1rem; border-left-color:#773344; background:#faf3f7;">
        Topics are ranked by how well AI models aligned with their fatwas on average.
        High scores mean AI responses were semantically close to the official fatwa.
        Low scores reveal where AI struggled the most — useful for your FYP analysis.
    </div>
    """, unsafe_allow_html=True)

    history_df = get_history_df()

    if history_df.empty or "topic_label" not in history_df.columns or "final_match_score" not in history_df.columns:
        st.markdown("""
        <div class="msg-box msg-warning">
            📂 No analysis history found yet. Run some responses through
            <strong>Single Review</strong> or <strong>Batch Review</strong> first,
            then come back here to see topic-level alignment rankings.
        </div>
        """, unsafe_allow_html=True)
    else:
        valid_history_df = history_df.copy()
        valid_history_df["topic_label"] = valid_history_df["topic_label"].fillna("").astype(str).str.strip()
        valid_history_df = valid_history_df[valid_history_df["topic_label"] != ""]
        valid_history_df["final_match_score"] = pd.to_numeric(valid_history_df["final_match_score"], errors="coerce")
        valid_history_df = valid_history_df[valid_history_df["final_match_score"].notna()]

        topic_scores = (
            valid_history_df
            .groupby("topic_label")["final_match_score"]
            .agg(["mean", "count"])
            .reset_index()
            .rename(columns={
                "topic_label": "topic",
                "mean": "avg_score",
                "count": "responses"
            })
            .sort_values("avg_score", ascending=False)
            .reset_index(drop=True)
        )

        topic_scores["avg_score"] = pd.to_numeric(topic_scores["avg_score"], errors="coerce").fillna(0.0).round(1)
        topic_scores["short_label"] = topic_scores["topic"].apply(short_topic_label)
        topic_scores["rank"] = range(1, len(topic_scores) + 1)

        def score_band(s):
            if s >= 70:
                return "Good", "#06A77D", "●"
            if s >= 50:
                return "Moderate", "#C27D06", "●"
            return "Weak", "#A31621", "●"

        top3 = topic_scores.head(3)
        bot3 = topic_scores.tail(3).iloc[::-1]

        hi_col, lo_col = st.columns(2)

        with hi_col:
            st.markdown("<div class='align-panel-title'>🏆 Highest Alignment</div>", unsafe_allow_html=True)
            for _, r in top3.iterrows():
                band, color, icon = score_band(r["avg_score"])
                st.markdown(f"""
                <div class="align-rank-card" style="border-left:4px solid {color};">
                    <div class="align-rank-topic">{r['short_label']}</div>
                    <div class="align-rank-row">
                        <span class="align-score" style="color:{color};">{r['avg_score']}%</span>
                        <span class="align-band" style="color:{color};">{icon} {band}</span>
                        <span class="align-n">{int(r['responses'])} response{'s' if r['responses'] != 1 else ''}</span>
                    </div>
                    <div class="align-bar-bg">
                        <div class="align-bar-fill" style="width:{min(r['avg_score'], 100)}%;background:{color};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with lo_col:
            st.markdown("<div class='align-panel-title'>⚠️ Lowest Alignment</div>", unsafe_allow_html=True)
            for _, r in bot3.iterrows():
                band, color, icon = score_band(r["avg_score"])
                st.markdown(f"""
                <div class="align-rank-card" style="border-left:4px solid {color};">
                    <div class="align-rank-topic">{r['short_label']}</div>
                    <div class="align-rank-row">
                        <span class="align-score" style="color:{color};">{r['avg_score']}%</span>
                        <span class="align-band" style="color:{color};">{icon} {band}</span>
                        <span class="align-n">{int(r['responses'])} response{'s' if r['responses'] != 1 else ''}</span>
                    </div>
                    <div class="align-bar-bg">
                        <div class="align-bar-fill" style="width:{min(r['avg_score'], 100)}%;background:{color};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with st.expander("📋 See full ranking for all topics"):
            for _, r in topic_scores.iterrows():
                band, color, icon = score_band(r["avg_score"])
                st.markdown(f"""
                <div class="align-full-row">
                    <span class="align-full-rank" style="color:{color};">#{int(r['rank'])}</span>
                    <span class="align-full-topic">{r['short_label']}</span>
                    <div class="align-bar-bg" style="flex:1;margin:0 0.8rem;">
                        <div class="align-bar-fill" style="width:{min(r['avg_score'], 100)}%;background:{color};"></div>
                    </div>
                    <span class="align-full-score" style="color:{color};">{r['avg_score']}%</span>
                    <span class="align-full-n">({int(r['responses'])})</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        st.markdown("<h3 class='section-subtitle'>📈 Topic Difficulty — Harder vs Easier for AI</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="msg-box msg-info" style="margin-bottom:1rem; border-left-color:#773344; background:#faf3f7;">
            This section ranks topics from harder to easier based on the same average alignment scores.
            Scores of 70% and above are treated as good, 50% to 69.9% as moderate, and below 50% as weak.
        </div>
        """, unsafe_allow_html=True)

        topic_perf = (
            valid_history_df.groupby("topic_label")["final_match_score"]
            .agg(["mean", "count"])
            .reset_index()
            .rename(columns={"mean": "avg_score", "count": "total_responses"})
        )

        topic_perf = topic_perf[topic_perf["total_responses"] >= 1].copy()
        topic_perf["avg_score"] = pd.to_numeric(topic_perf["avg_score"], errors="coerce").fillna(0.0).round(1)
        topic_perf["short_label"] = topic_perf["topic_label"].apply(short_topic_label)

        hardest_topics = topic_perf.sort_values(["avg_score", "total_responses"], ascending=[True, False]).head(3)
        easiest_topics = topic_perf.sort_values(["avg_score", "total_responses"], ascending=[False, False]).head(3)

        dcol1, dcol2 = st.columns(2)

        with dcol1:
            st.markdown("<div class='align-panel-title'>🔴 Hardest Topics for AI</div>", unsafe_allow_html=True)
            for i, (_, row) in enumerate(hardest_topics.iterrows(), start=1):
                s = row['avg_score']
                sc = "#A31621" if s < 50 else "#C27D06" if s < 70 else "#06A77D"
                st.markdown(f"""
                <div class="align-rank-card" style="border-left:4px solid #A31621;">
                    <div class="align-rank-topic">#{i} {row['short_label']}</div>
                    <div class="align-rank-row">
                        <span class="align-score" style="color:{sc};">{s}%</span>
                        <span class="align-band" style="color:#A31621;">⚑ Harder Topic</span>
                        <span class="align-n">{int(row['total_responses'])} record{'s' if row['total_responses'] != 1 else ''}</span>
                    </div>
                    <div class="align-bar-bg">
                        <div class="align-bar-fill" style="width:{min(s, 100)}%;background:#A31621;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with dcol2:
            st.markdown("<div class='align-panel-title'>🟢 Easiest Topics for AI</div>", unsafe_allow_html=True)
            for i, (_, row) in enumerate(easiest_topics.iterrows(), start=1):
                s = row['avg_score']
                sc = "#A31621" if s < 50 else "#C27D06" if s < 70 else "#06A77D"
                st.markdown(f"""
                <div class="align-rank-card" style="border-left:4px solid #06A77D;">
                    <div class="align-rank-topic">#{i} {row['short_label']}</div>
                    <div class="align-rank-row">
                        <span class="align-score" style="color:{sc};">{s}%</span>
                        <span class="align-band" style="color:#06A77D;">✔ More Stable</span>
                        <span class="align-n">{int(row['total_responses'])} record{'s' if row['total_responses'] != 1 else ''}</span>
                    </div>
                    <div class="align-bar-bg">
                        <div class="align-bar-fill" style="width:{min(s, 100)}%;background:#06A77D;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    st.markdown("<h3 class='section-subtitle'>🔍 Topic Deep-Dive — Compare State Fatwas Side by Side</h3>", unsafe_allow_html=True)
    st.markdown("<div class='topic-pick-shell'><div class='topic-pick-kicker'>State comparison workspace</div><div class='topic-pick-title'>Choose one topic and compare all state fatwas clearly</div><div class='topic-pick-copy'>This section helps you see coverage, missing states, and the full fatwa wording side by side in one place.</div></div>", unsafe_allow_html=True)

    topic_options = topic_counts_full["issue_display"].tolist()

    st.markdown("""
    <div class='comparison-select-head'>
        <div>
            <div class='comparison-select-title'>Choose a topic</div>
            <div class='comparison-select-copy'>Pick one topic to see which states cover it, where coverage is missing, and how the actual fatwa wording compares side by side.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    selected_topic = st.selectbox(
        "Choose a topic",
        options=topic_options,
        index=0 if topic_options else None,
        key="topic_analysis_select"
    )

    if selected_topic:
        selected_df = analysis_df[analysis_df["issue_display"] == selected_topic].copy()
        covering_states = sorted([s for s in selected_df["state"].dropna().unique().tolist() if s])
        missing_states = sorted([s for s in all_states if s not in covering_states])

        st.markdown(f"""
        <div class='topic-focus-grid'>
            <div class='topic-focus-card'><div class='topic-focus-label'>Selected topic</div><div class='topic-focus-value'>{html_escape_mod.escape(short_topic_label(selected_topic))}</div></div>
            <div class='topic-focus-card'><div class='topic-focus-label'>Fatwa records</div><div class='topic-focus-value'>{len(selected_df)}</div></div>
            <div class='topic-focus-card'><div class='topic-focus-label'>States covering</div><div class='topic-focus-value'>{len(covering_states)}</div></div>
            <div class='topic-focus-card'><div class='topic-focus-label'>States missing</div><div class='topic-focus-value'>{len(missing_states)}</div></div>
        </div>
        """, unsafe_allow_html=True)

        # (summary already shown in the topic-focus-grid above)

        st.markdown("<h3 class='section-subtitle'>States That Cover This Topic</h3>", unsafe_allow_html=True)

        if covering_states:
            chips_html = "".join(
                [f"<span class='keyword-match'>{html_escape_mod.escape(s)}</span>" for s in covering_states]
            )
        else:
            chips_html = "<span class='small-note'>No states found for this topic.</span>"

        st.markdown(f"""
        <div class="points-card">
            <div class="points-card-header">Covered By</div>
            <div class="keyword-container">{chips_html}</div>
        </div>
        """, unsafe_allow_html=True)

        if missing_states:
            st.markdown("<h3 class='section-subtitle'>States With No Fatwa on This Topic</h3>", unsafe_allow_html=True)
            missing_chips_html = "".join(
                [f"<span class='keyword-miss'>{html_escape_mod.escape(s)}</span>" for s in missing_states]
            )
            st.markdown(f"""
            <div class="points-card">
                <div class="points-card-header">Coverage Gaps</div>
                <div class="keyword-container">{missing_chips_html}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        st.markdown("<h3 class='section-subtitle'>Side-by-Side Fatwa Comparison</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="msg-box msg-info" style="margin-bottom:0.8rem; border-left-color:#773344; background:#faf3f7;">
            Each column shows one state's fatwa ruling on this topic.
            Scroll horizontally if there are many states.
        </div>
        """, unsafe_allow_html=True)

        if covering_states:
            chunk_size = 2
            state_chunks = [
                covering_states[i:i + chunk_size]
                for i in range(0, len(covering_states), chunk_size)
            ]

            for chunk in state_chunks:
                cols = st.columns(len(chunk))
                for col, state_name in zip(cols, chunk):
                    state_rows = selected_df[selected_df["state"] == state_name]
                    with col:
                        for _, row in state_rows.iterrows():
                            fatwa_text_val = str(row.get("fatwa_text", "")).strip()
                            question_text_val = str(row.get("question_text", "")).strip()

                            question_line = (
                                f'<div class="fatwa-meta-pill" style="margin-bottom:0.6rem;">Reference: '
                                f'{html_escape_mod.escape(question_text_val)}</div>'
                                if question_text_val else ""
                            )

                            st.markdown(f"""
                            <div class="comparison-card">
                                <div class="comparison-card-header">{html_escape_mod.escape(state_name)}</div>
                                {question_line}
                                <div class="fatwa-text-panel">
                                    <p>{html_escape_mod.escape(fatwa_text_val) if fatwa_text_val else "<em>No fatwa text available.</em>"}</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="msg-box msg-warning" style="text-align:center; padding:2rem;">
                <strong>No fatwa records found for this topic.</strong>
            </div>
            """, unsafe_allow_html=True)


# =========================================================
# FOOTER
# =========================================================
render_footer()