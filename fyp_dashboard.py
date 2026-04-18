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
    page_title="AI Fatwa Alignment Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme()


def apply_dashboard_polish():
    st.markdown("""
    <style>
    .workspace-shell {background:linear-gradient(180deg,#ffffff 0%,#fbf5f1 100%);border:1px solid #e3b5a4;border-radius:24px;padding:1.05rem 1.1rem;box-shadow:0 10px 24px rgba(25,14,36,0.06);margin-bottom:0.85rem;}
    .workspace-shell-tight {padding:0.95rem 1rem;}
    .workspace-title-row {display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;margin-bottom:0.55rem;}
    .workspace-kicker {font-size:0.72rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#773344;margin-bottom:0.22rem;}
    .workspace-title {font-family:'DM Serif Display',serif;font-size:1.38rem;color:#160029;line-height:1.1;margin:0;}
    .workspace-copy {color:#5d3945;font-size:0.9rem;line-height:1.65;margin-top:0.25rem;}
    .workspace-chip-row {display:flex;flex-wrap:wrap;gap:0.55rem;margin-top:0.6rem;}
    .workspace-chip {display:inline-flex;align-items:center;padding:0.42rem 0.78rem;border-radius:999px;background:#fff;border:1px solid #e3b5a4;color:#773344;font-size:0.76rem;font-weight:700;box-shadow:0 2px 6px rgba(25,14,36,0.04);}
    .input-help-note {background:#f7ece7;border:1px solid #e3b5a4;border-left:4px solid #b24758;border-radius:16px;padding:0.85rem 0.95rem;color:#5d3945;font-size:0.88rem;line-height:1.65;margin:0.55rem 0 0.8rem 0;}
    .input-help-note strong {color:#160029;}
    .empty-review-card {background:linear-gradient(180deg,#ffffff 0%,#f9f1ec 100%);border:1px solid #e3b5a4;border-radius:24px;padding:1rem 1rem 1.05rem 1rem;box-shadow:0 10px 24px rgba(25,14,36,0.06);min-height:380px;display:flex;flex-direction:column;justify-content:space-between;}
    .empty-review-top {display:flex;justify-content:space-between;gap:0.9rem;align-items:flex-start;margin-bottom:0.7rem;}
    .empty-review-title {font-family:'DM Serif Display',serif;font-size:1.25rem;color:#160029;margin:0.1rem 0 0.2rem 0;}
    .empty-review-copy {color:#5d3945;font-size:0.88rem;line-height:1.65;}
    .empty-review-pill {padding:0.42rem 0.8rem;border-radius:999px;background:#fff;border:1px solid #e3b5a4;color:#773344;font-weight:800;font-size:0.78rem;white-space:nowrap;}
    .empty-review-list {display:grid;gap:0.7rem;margin-top:0.5rem;}
    .empty-review-item {display:flex;gap:0.75rem;align-items:flex-start;padding:0.85rem 0.9rem;border-radius:16px;background:#fff;border:1px solid #e3b5a4;}
    .empty-review-icon {width:34px;height:34px;min-width:34px;border-radius:12px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#d44d5c 0%,#b24758 100%);color:#fff;font-size:0.92rem;font-weight:800;}
    .empty-review-item strong {display:block;color:#160029;font-size:0.84rem;margin-bottom:0.12rem;}
    .empty-review-item span {display:block;color:#5d3945;font-size:0.8rem;line-height:1.55;}
    .empty-review-footer {display:grid;grid-template-columns:repeat(3,1fr);gap:0.65rem;margin-top:0.9rem;}
    .empty-review-stat {background:#fff;border:1px solid #e3b5a4;border-radius:16px;padding:0.8rem;text-align:center;}
    .empty-review-stat-label {font-size:0.68rem;font-weight:800;color:#8b6771;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.24rem;}
    .empty-review-stat-value {font-family:'DM Serif Display',serif;font-size:1.15rem;color:#160029;}
    .single-result-anchor {margin-top:0.9rem;}
    .sidebar-insight-list {display:grid;gap:0.65rem;}
    .sidebar-insight-card {background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.11);border-radius:14px;padding:0.8rem 0.85rem;}
    .sidebar-insight-label {font-size:0.68rem;font-weight:800;letter-spacing:0.07em;text-transform:uppercase;color:rgba(255,255,255,0.58)!important;margin-bottom:0.18rem;}
    .sidebar-insight-value {font-size:0.86rem;font-weight:700;color:#ffffff!important;line-height:1.45;}
    .sidebar-insight-copy {font-size:0.78rem;line-height:1.55;color:rgba(255,255,255,0.76)!important;margin-top:0.2rem;}
    .sidebar-checklist {margin:0;padding-left:0;list-style:none;display:grid;gap:0.58rem;}
    .sidebar-checklist li {position:relative;padding-left:1.2rem;color:rgba(255,255,255,0.82)!important;font-size:0.82rem;line-height:1.55;}
    .sidebar-checklist li:before {content:'✓';position:absolute;left:0;top:0;color:#fdc7df;font-weight:800;}
    .hero-image-wrap {height:250px!important;border-radius:28px!important;}
    .hero-image-overlay {justify-content:flex-start!important;text-align:left!important;padding:2rem 2.2rem!important;background:linear-gradient(90deg,rgba(10,35,68,0.80),rgba(107,22,80,0.52))!important;}
    .hero-image-title {font-size:2.35rem!important;}
    .hero-image-subtitle {max-width:760px!important;}
    .sidebar-workspace-card,.sidebar-section-card {border-radius:20px!important;}
    .metric-card,.result-card,.points-card,.fatwa-box,.card,.overview-chart-card {border-radius:20px!important;}
    .topic-card {border-radius:18px!important;}
    @media (max-width: 900px) {.empty-review-footer {grid-template-columns:1fr;}}
    .editorial-section {padding:0.1rem 0 0.55rem 0;margin-bottom:0.8rem;}
    .editorial-kicker {font-size:0.78rem;font-weight:800;letter-spacing:0.16em;text-transform:uppercase;color:#a3195b;margin-bottom:0.7rem;}
    .editorial-title {font-family:'Inter Tight', 'Inter', sans-serif;font-size:2.05rem;line-height:1.08;font-weight:700;color:#221221;letter-spacing:-0.03em;margin:0 0 0.8rem 0;max-width:900px;}
    .editorial-copy {max-width:980px;font-size:1.06rem;line-height:1.8;color:#6d5a68;margin:0;}
    .editorial-meta {display:flex;flex-wrap:wrap;gap:1rem;margin-top:1rem;padding-top:0.95rem;border-top:1px solid rgba(163,25,91,0.12);font-size:0.9rem;color:#7f7180;}
    .editorial-meta span {position:relative;padding-left:0.95rem;}
    .editorial-meta span:before {content:'';position:absolute;left:0;top:0.52rem;width:4px;height:4px;border-radius:999px;background:#cc5d76;}
    .editorial-line {height:1px;background:linear-gradient(90deg, rgba(163,25,91,0.16), rgba(163,25,91,0.04));margin:1rem 0 1.15rem 0;}
.editorial-line-tight {margin:0.75rem 0 1rem 0;}
    .tab-minimal-hero {background:linear-gradient(180deg,#fffdfc 0%,#fbf2ee 100%);border:1px solid rgba(227,181,164,0.9);border-radius:26px;padding:1.15rem 1.2rem 1rem 1.2rem;box-shadow:0 12px 28px rgba(44,21,33,0.05);margin:0.05rem 0 0.35rem 0;}
    .tab-minimal-kicker {font-size:0.72rem;font-weight:800;letter-spacing:0.14em;text-transform:uppercase;color:#a3195b;margin-bottom:0.38rem;}
    .tab-minimal-title {font-family:'Inter Tight','Inter',sans-serif;font-size:1.88rem;font-weight:700;line-height:1.06;color:#221221;letter-spacing:-0.03em;margin:0;}
    .tab-minimal-copy {margin-top:0.55rem;max-width:860px;color:#6d5a68;font-size:0.96rem;line-height:1.75;}
    .inline-section-head {display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;margin:0.05rem 0 0.55rem 0;}
    .inline-section-label {font-size:0.8rem;font-weight:800;letter-spacing:0.14em;text-transform:uppercase;color:#a3195b;margin-bottom:0.35rem;}
    .inline-section-title {font-family:'Inter Tight', 'Inter', sans-serif;font-size:1.08rem;font-weight:700;color:#251329;line-height:1.2;}
    .inline-section-copy {color:#766772;font-size:0.94rem;line-height:1.7;max-width:760px;}
    .inline-section-side {font-size:0.88rem;font-weight:700;color:#907785;white-space:nowrap;align-self:center;}
    .dataset-loader-minimal {padding:0 0 0.4rem 0;margin-bottom:0.2rem;}
    .slim-loader-head {display:flex;justify-content:space-between;align-items:flex-end;gap:1rem;padding:0.2rem 0 0.55rem 0;border-bottom:1px solid rgba(178,71,88,0.14);margin-bottom:0.75rem;}
    .slim-loader-kicker {font-size:0.72rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;color:#a3195b;margin-bottom:0.22rem;}
    .slim-loader-title {font-size:1.04rem;font-weight:800;color:#251329;line-height:1.2;margin-bottom:0.18rem;}
    .slim-loader-copy {font-size:0.9rem;color:#766772;line-height:1.65;}
    .slim-loader-side {font-size:0.82rem;font-weight:800;color:#907785;white-space:nowrap;padding-bottom:0.15rem;}
    .dataset-control-caption {font-size:0.72rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin:0 0 0.35rem 0.1rem;}
    .floating-success-toast {position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:9999;background:rgba(255,255,255,0.96);border:1px solid #d4a04b;border-radius:22px;box-shadow:0 24px 50px rgba(25,14,36,0.18);padding:1rem 1.2rem;min-width:320px;max-width:420px;text-align:center;backdrop-filter:blur(8px);animation:toast-pop 0.25s ease-out;}
    .floating-success-icon {width:54px;height:54px;border-radius:999px;background:linear-gradient(135deg,#f3c96c 0%,#d4a04b 100%);display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.4rem;font-weight:800;margin:0 auto 0.6rem auto;}
    .floating-success-title {font-size:1rem;font-weight:800;color:#251329;margin-bottom:0.22rem;}
    .floating-success-copy {font-size:0.88rem;line-height:1.6;color:#6d5a68;}
    @keyframes toast-pop {from {opacity:0;transform:translate(-50%,-46%);} to {opacity:1;transform:translate(-50%,-50%);}}
    .micro-copy {font-size:0.93rem;line-height:1.75;color:#7b6d78;margin:0.35rem 0 1rem 0;}
    .analysis-panel {background:rgba(255,255,255,0.72);border:1px solid rgba(170,133,155,0.28);border-radius:26px;padding:1.2rem 1.25rem;box-shadow:0 14px 34px rgba(52,27,45,0.05);height:100%;}
    .analysis-panel-title {font-family:'Inter Tight', 'Inter', sans-serif;font-size:1.15rem;font-weight:700;color:#2d1830;margin:0 0 0.35rem 0;}
    .analysis-panel-copy {color:#6e6070;font-size:0.95rem;line-height:1.75;margin:0 0 0.9rem 0;}
    .analysis-steps {display:grid;gap:0.85rem;margin-top:0.1rem;}
    .analysis-step {display:grid;grid-template-columns:40px 1fr;gap:0.8rem;align-items:start;padding:0.05rem 0;}
    .analysis-step-no {width:32px;height:32px;border-radius:999px;background:#f0e7ec;color:#a3195b;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:0.9rem;}
    .analysis-step-title {font-weight:700;color:#35233b;font-size:0.98rem;margin-bottom:0.12rem;}
    .analysis-step-copy {color:#746675;font-size:0.9rem;line-height:1.7;}
    .analysis-step + .analysis-step {border-top:1px solid rgba(170,133,155,0.2);padding-top:0.85rem;}
    .system-plain-note {padding:0.15rem 0 0.65rem 0;margin-bottom:0.45rem;color:#6d5a68;font-size:0.98rem;line-height:1.8;}
    .system-plain-note strong {color:#251329;}
    .input-editor-shell {background:linear-gradient(180deg,#fffaf8 0%,#f8efea 100%);border:1px solid #e3b5a4;border-radius:22px;padding:1rem 1rem 0.85rem 1rem;margin:0.25rem 0 0.65rem 0;box-shadow:0 10px 24px rgba(25,14,36,0.05);}
    .batch-manual-shell {margin-bottom:0.55rem;}
    .input-editor-head {display:flex;align-items:flex-start;justify-content:space-between;gap:0.8rem;margin-bottom:0.45rem;}
    .input-editor-kicker {font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:0.08em;color:#a3195b;margin-bottom:0.18rem;}
    .input-editor-title {font-size:1rem;font-weight:800;color:#241226;line-height:1.3;}
    .input-editor-note {color:#6f5c68;font-size:0.9rem;line-height:1.7;}
    .input-editor-chip {padding:0.38rem 0.78rem;border-radius:999px;background:#fff;border:1px solid #e3b5a4;color:#773344;font-size:0.76rem;font-weight:800;white-space:nowrap;}
    .batch-shell {background:linear-gradient(180deg,#ffffff 0%,#f9f1ec 100%);border:1px solid #e3b5a4;border-radius:26px;padding:1.1rem 1.15rem 1rem 1.15rem;box-shadow:0 12px 28px rgba(25,14,36,0.06);margin:0.15rem 0 0.95rem 0;}
    .batch-shell-head {display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;}
    .batch-kicker {font-size:0.72rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#a3195b;margin-bottom:0.2rem;}
    .batch-title {font-family:'Inter Tight','Inter',sans-serif;font-size:1.22rem;font-weight:700;color:#211120;line-height:1.15;margin-bottom:0.28rem;}
    .batch-copy {color:#6d5a68;font-size:0.92rem;line-height:1.72;max-width:860px;}
    .batch-pill {padding:0.42rem 0.82rem;border-radius:999px;background:#fff;border:1px solid #e3b5a4;color:#773344;font-size:0.78rem;font-weight:800;white-space:nowrap;}
    .batch-filter-grid {margin-bottom:0.2rem;}
    .batch-selection-note {background:#fff7f4;border:1px solid #e3b5a4;border-radius:16px;padding:0.85rem 0.95rem;color:#5f4751;font-size:0.9rem;line-height:1.55;margin:0.75rem 0 0.9rem 0;}
    .batch-selection-note strong {color:#160029;font-size:1rem;}
    .batch-guide-card {background:linear-gradient(180deg,#fff 0%,#f9f1ec 100%);border:1px solid #e3b5a4;border-radius:22px;padding:1rem;box-shadow:0 10px 24px rgba(25,14,36,0.05);}
    .batch-guide-kicker {font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:0.08em;color:#a3195b;margin-bottom:0.65rem;}
    .batch-guide-step {display:flex;gap:0.65rem;align-items:flex-start;padding:0.72rem 0;border-top:1px solid rgba(178,71,88,0.14);color:#5d3945;font-size:0.88rem;line-height:1.6;}
    .batch-guide-step:first-of-type {border-top:none;padding-top:0;}
    .batch-guide-step strong {width:1rem;color:#b24758;display:inline-block;}
    .chart-panel {background:linear-gradient(180deg,#fffefe 0%,#f8efea 100%);border:1px solid #e3b5a4;border-radius:22px;padding:1rem 1.05rem 0.9rem 1.05rem;box-shadow:0 10px 24px rgba(25,14,36,0.05);margin:1rem 0 0.5rem 0;}
    .chart-panel-title {font-family:'Inter Tight','Inter',sans-serif;font-size:1.08rem;font-weight:700;color:#221221;margin-bottom:0.18rem;}
    .chart-panel-copy {color:#6d5a68;font-size:0.9rem;line-height:1.65;}
    .chart-panel-copy strong {color:#251329;}
    .chart-panel-note {margin-top:0.45rem;font-size:0.82rem;color:#8b6771;line-height:1.55;}
    @media (max-width: 980px) {.editorial-title {font-size:1.75rem;}.batch-shell-head,.input-editor-head {flex-direction:column;}.batch-pill,.input-editor-chip {white-space:normal;}}
    
    .leaderboard-shell {display:grid;gap:0.8rem;margin-top:0.8rem;}
    .leaderboard-card {display:grid;grid-template-columns:58px 1fr auto;gap:0.9rem;align-items:center;background:linear-gradient(180deg,#fff 0%,#fbf3ef 100%);border:1px solid #e7c2b3;border-radius:20px;padding:0.95rem 1rem;box-shadow:0 8px 18px rgba(25,14,36,0.05);}
    .leaderboard-card-top {border-color:#d4a04b;box-shadow:0 12px 22px rgba(25,14,36,0.08);}
    .leaderboard-rank {width:44px;height:44px;border-radius:14px;background:#fff7f1;border:1px solid #e7c2b3;display:flex;align-items:center;justify-content:center;font-size:1.1rem;}
    .leaderboard-title {font-size:1rem;font-weight:800;color:#221221;margin-bottom:0.15rem;}
    .leaderboard-meta {font-size:0.82rem;color:#7a6874;line-height:1.5;margin-bottom:0.45rem;}
    .leaderboard-track {height:8px;background:#f3dfd7;border-radius:999px;overflow:hidden;}
    .leaderboard-fill {height:100%;background:linear-gradient(90deg,#d44d5c 0%,#b24758 100%);border-radius:999px;}
    .leaderboard-side {text-align:right;min-width:92px;}
    .leaderboard-score {font-size:1.1rem;font-weight:800;color:#221221;}
    .leaderboard-note {font-size:0.75rem;color:#8b6771;line-height:1.4;}
    .grouped-chart-shell {background:linear-gradient(180deg,#fffdfc 0%,#fbf2ee 100%);border:1px solid #e3b5a4;border-radius:22px;padding:1rem 1rem 0.85rem 1rem;box-shadow:0 10px 24px rgba(25,14,36,0.05);margin-top:0.2rem;}
    .grouped-chart-head {padding:0 0 0.9rem 0;margin-bottom:0.8rem;border-bottom:1px solid rgba(227,181,164,0.45);}
    .grouped-chart-title {font-family:'Inter Tight','Inter',sans-serif;font-size:1.08rem;font-weight:700;color:#221221;margin-bottom:0.18rem;}
    .grouped-chart-copy {color:#6d5a68;font-size:0.9rem;line-height:1.68;max-width:860px;}
    .browse-filter-header {display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;margin:0.25rem 0 0.35rem 0;}
    .browse-selector-intro {background:linear-gradient(180deg,#fffdfa 0%,#fdf6f1 100%);border:1px solid #ead1c8;border-radius:20px;padding:0.95rem 1rem;margin:0.55rem 0 0.85rem 0;box-shadow:0 10px 24px rgba(25,14,36,0.04);}
    .browse-selector-intro-kicker {color:#8b6771;font-size:0.7rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.22rem;}
    .browse-selector-intro-copy {color:#6d5a68;font-size:0.9rem;line-height:1.65;}
    .browse-toolbar-shell {display:flex;justify-content:space-between;align-items:center;gap:1rem;padding:0.2rem 0 0.75rem 0;margin:0.35rem 0 0.4rem 0;border-bottom:1px solid rgba(227,181,164,0.45);}
    .browse-toolbar-title {font-size:1rem;font-weight:800;color:#251329;margin-bottom:0.18rem;}
    .browse-toolbar-copy {font-size:0.9rem;color:#6d5a68;line-height:1.65;max-width:720px;}
    .browse-toolbar-pills {display:flex;flex-wrap:wrap;gap:0.45rem;justify-content:flex-end;}
    .browse-filter-title {font-size:1.12rem;font-weight:800;color:#221221;}
    .browse-filter-copy {font-size:0.9rem;color:#6d5a68;line-height:1.68;max-width:860px;}
    .browse-filter-stat-row {display:flex;flex-wrap:wrap;gap:0.55rem;margin:0.45rem 0 0.2rem 0;}
    .browse-filter-stat {display:inline-flex;align-items:center;padding:0.4rem 0.8rem;border-radius:999px;background:#fff8f4;border:1px solid #e3b5a4;color:#773344;font-size:0.78rem;font-weight:700;}
    .browse-inline-head {font-size:0.78rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin:0 0 0.38rem 0.08rem;}
    .browse-filter-chip-row {display:flex;flex-wrap:wrap;gap:0.5rem;margin:0.55rem 0 0.85rem 0;}
    .browse-filter-chip {display:inline-flex;align-items:center;padding:0.38rem 0.75rem;border-radius:999px;background:#fff8f4;border:1px solid #e3b5a4;color:#773344;font-size:0.77rem;font-weight:700;}
    .explorer-summary-grid {display:grid;grid-template-columns:repeat(3,1fr);gap:0.8rem;margin:0.6rem 0 1rem 0;}
    .explorer-summary-card {background:linear-gradient(180deg,#fff 0%,#fbf3ef 100%);border:1px solid #e3b5a4;border-radius:18px;padding:0.95rem 1rem;}
    .explorer-summary-label {font-size:0.72rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin-bottom:0.28rem;}
    .explorer-summary-value {font-size:1.35rem;font-weight:800;color:#221221;}
    .topic-focus-grid {display:grid;grid-template-columns:repeat(4,1fr);gap:0.8rem;margin:0.3rem 0 0.9rem 0;}
    .topic-focus-card {background:linear-gradient(180deg,#fff 0%,#faf4f0 100%);border:1px solid #e3b5a4;border-radius:18px;padding:0.85rem 0.95rem;}
    .topic-focus-label {font-size:0.7rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin-bottom:0.24rem;}
    .topic-focus-value {font-size:1rem;font-weight:800;color:#221221;line-height:1.35;}
    .sim-lite-shell {background:linear-gradient(180deg,#ffffff 0%,#fbf3ef 100%);border:1px solid #e3b5a4;border-radius:24px;padding:1rem;box-shadow:0 12px 24px rgba(25,14,36,0.06);}
    .sim-lite-title {font-size:1.22rem;font-weight:800;}
    .sim-lite-top-note {display:flex;flex-direction:column;gap:0.12rem;background:linear-gradient(180deg,#fffaf7 0%,#fff5ef 100%);border:1px solid #ead1c8;border-radius:18px;padding:0.82rem 0.9rem;margin-bottom:0.8rem;box-shadow:0 6px 16px rgba(25,14,36,0.04);}
    .sim-lite-top-note-title {font-size:0.72rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;}
    .sim-lite-top-note-copy {font-size:0.85rem;line-height:1.55;color:#6d5a68;}
    .sim-lite-summary-badges {display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.6rem;}
    .sim-lite-mini-badge {display:inline-flex;align-items:center;padding:0.34rem 0.7rem;border-radius:999px;background:#fff7f2;border:1px solid #ead1c8;color:#773344;font-size:0.76rem;font-weight:700;}
    .sim-lite-metric {min-height:118px;}
    .fatwa-box {background:linear-gradient(180deg,#fff 0%,#fcf5f1 100%) !important;border:1px solid #d9cfe6 !important;box-shadow:0 12px 26px rgba(22,32,51,0.05) !important;padding:1.15rem !important;}
    .fatwa-title {font-size:1.18rem !important;margin-bottom:0.7rem !important;}
    .fatwa-text-panel {background:#fffdfb !important;border-radius:14px !important;padding:1rem 1.05rem !important;}
    .fatwa-meta-pill {border-radius:999px !important;background:#fff8f4 !important;}
    .topic-select-shell {background:linear-gradient(180deg,#fff 0%,#fbf4ef 100%);border:1px solid #e3b5a4;border-radius:22px;padding:0.9rem 1rem;box-shadow:0 10px 20px rgba(25,14,36,0.05);margin-bottom:1rem;}
    .topic-select-shell [data-baseweb="select"] > div {min-height:60px !important;border-radius:16px !important;background:#fff !important;border:1px solid #ead1c8 !important;}
    .batch-shell.compact {padding:0.9rem 1rem;}
    @media (max-width: 980px) {.explorer-summary-grid,.topic-focus-grid {grid-template-columns:1fr 1fr;} .leaderboard-card {grid-template-columns:44px 1fr;}.leaderboard-side {grid-column:2;text-align:left;}}
    @media (max-width: 980px) {.browse-toolbar-shell {flex-direction:column;align-items:flex-start;} .browse-toolbar-pills {justify-content:flex-start;} .explorer-summary-grid,.topic-focus-grid {grid-template-columns:1fr 1fr;} .leaderboard-card {grid-template-columns:44px 1fr;}.leaderboard-side {grid-column:2;text-align:left;}}
    @media (max-width: 680px) {.explorer-summary-grid,.topic-focus-grid {grid-template-columns:1fr;}}

    .single-review-hero {margin-bottom:0.95rem !important;padding:1.25rem 1.3rem 1.1rem 1.3rem !important;}
    .single-review-hero .tab-minimal-title {font-size:2rem !important;max-width:980px;}
    .single-review-hero .tab-minimal-copy {max-width:980px !important;}
    .single-review-right-col {margin-top:0.7rem;}
    .single-review-right-col .sim-lite-shell {margin-top:0.2rem;}
    @media (min-width: 992px) {.single-review-right-col {margin-top:1.15rem;}}
    .sim-lite-shell {background:linear-gradient(180deg,#ffffff 0%,#fbf3ef 100%);border:1px solid #e3b5a4;border-radius:24px;padding:1rem 1rem 0.95rem 1rem;box-shadow:0 12px 24px rgba(25,14,36,0.06);}
    .sim-lite-head {display:flex;align-items:flex-start;justify-content:space-between;gap:0.85rem;margin-bottom:0.9rem;}
    .sim-lite-kicker {font-size:0.72rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin-bottom:0.2rem;}
    .sim-lite-title {font-family:'Inter Tight','Inter',sans-serif;font-size:1.8rem;font-weight:700;line-height:1.08;color:#221221;}
    .sim-lite-pill {padding:0.42rem 0.9rem;border-radius:999px;border:1px solid #e3b5a4;background:#fff7f4;font-size:1rem;font-weight:800;white-space:nowrap;}
    .sim-lite-hero {display:grid;grid-template-columns:120px 1fr;gap:1rem;align-items:center;margin-bottom:0.85rem;}
    .sim-lite-ring {width:108px;height:108px;border-radius:999px;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 18px rgba(25,14,36,0.08);}
    .sim-lite-ring-inner {width:78px;height:78px;border-radius:999px;background:#fff;display:flex;align-items:center;justify-content:center;flex-direction:column;box-shadow:inset 0 0 0 1px rgba(227,181,164,0.45);}
    .sim-lite-ring-inner strong {font-family:'Inter Tight','Inter',sans-serif;font-size:1.7rem;line-height:1;}
    .sim-lite-ring-inner span {font-size:0.72rem;color:#8b6771;margin-top:0.2rem;}
    .sim-lite-summary-title {font-size:1.05rem;font-weight:800;color:#221221;margin-bottom:0.28rem;}
    .sim-lite-summary-copy {font-size:0.9rem;line-height:1.7;color:#6d5a68;}
    .sim-lite-top-note {display:block;background:#fff8f4;border:1px solid #ead1c8;border-radius:16px;padding:0.82rem 0.9rem;margin:0.85rem 0 0.9rem 0;}
    .sim-lite-top-note-title {display:block;font-size:0.72rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin-bottom:0.2rem;}
    .sim-lite-top-note-copy {display:block;font-size:0.84rem;line-height:1.6;color:#6d5a68;}
    .sim-lite-metric {background:#fff;border:1px solid #ead1c8;border-radius:16px;padding:0.9rem 0.95rem;box-shadow:0 6px 16px rgba(25,14,36,0.04);min-height:124px;margin-bottom:0.65rem;text-align:center;display:flex;flex-direction:column;justify-content:center;}
    .sim-lite-metric-label {font-size:0.74rem;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;color:#8b6771;margin-bottom:0.34rem;}
    .sim-lite-metric-value {font-family:'Inter Tight','Inter',sans-serif;font-size:1.85rem;font-weight:700;line-height:1;margin-bottom:0.34rem;text-align:center;}
    .sim-lite-metric-note {font-size:0.82rem;line-height:1.55;color:#6d5a68;}
    @media (max-width: 900px) {.sim-lite-hero {grid-template-columns:1fr;}.sim-lite-ring {margin:0 auto;}}
    .mini-explainer-card {background:linear-gradient(180deg,#fffaf7 0%,#fff4ef 100%);border:1px solid #ead1c8;border-radius:18px;padding:0.9rem 1rem;color:#6d5a68;font-size:0.92rem;line-height:1.7;margin:0.5rem 0 1rem 0;box-shadow:0 10px 20px rgba(25,14,36,0.04);}
    .mini-explainer-card strong {color:#221221;}
    .fatwa-browser-shell {background:linear-gradient(180deg,#fffdfb 0%,#fbf3ef 100%);border:1px solid #e3b5a4;border-radius:24px;padding:1rem 1rem 0.8rem 1rem;box-shadow:0 12px 24px rgba(25,14,36,0.05);margin:0.8rem 0 1rem 0;}
    .fatwa-browser-topline {display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;margin-bottom:0.7rem;}
    .fatwa-browser-title {font-size:1.08rem;font-weight:800;color:#221221;margin-bottom:0.22rem;}
    .fatwa-browser-copy {font-size:0.9rem;line-height:1.68;color:#6d5a68;max-width:820px;}
    .fatwa-browser-stats {display:flex;flex-wrap:wrap;gap:0.5rem;margin:0.55rem 0 0.3rem 0;}
    .fatwa-browser-pills {display:flex;flex-wrap:wrap;gap:0.5rem;justify-content:flex-start;margin:0.3rem 0 0.8rem 0;}
    .fatwa-browser-shell .stButton > button {min-height:3.2rem;}
    .browse-filter-chip-row {padding-top:0.2rem;border-top:1px solid rgba(227,181,164,0.45);}
    @media (max-width: 980px) {.fatwa-browser-topline {flex-direction:column;}}
    @media (max-width: 1100px) {
        div[style*='grid-template-columns:1.15fr 1.45fr 1fr'] {grid-template-columns:1fr !important;}
        div[style*='grid-template-columns:repeat(3,minmax(84px,1fr))'] {grid-template-columns:repeat(3,minmax(70px,1fr)) !important;min-width:0 !important;}
    }
    @media (max-width: 980px) {
        div[style*='grid-template-columns:repeat(3,minmax(84px,1fr))'] {grid-template-columns:1fr !important;}
    }


    .metric-value-text {font-family:'Inter Tight','Inter',sans-serif !important;font-size:2.15rem !important;font-weight:700 !important;line-height:1.15 !important;color:#7d3347 !important;letter-spacing:-0.03em;word-break:break-word;}
    .overview-kicker {font-size:0.72rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;color:#9a7380;margin-bottom:0.25rem;}
    .overview-title {font-family:'Inter Tight','Inter',sans-serif;font-size:1.14rem;font-weight:700;color:#231222;line-height:1.2;margin-bottom:0.2rem;}
    .overview-copy {font-size:0.9rem;line-height:1.65;color:#6d5a68;margin-bottom:0.55rem;}
    .overview-chart-frame {background:linear-gradient(180deg,#fffdfc 0%,#fbf2ee 100%);border:1px solid #ead1c8;border-radius:24px;padding:1rem 1rem 0.7rem 1rem;box-shadow:0 10px 24px rgba(25,14,36,0.05);overflow:hidden;display:flex;flex-direction:column;}
    .overview-chart-head {display:flex;align-items:flex-start;justify-content:space-between;gap:0.9rem;margin-bottom:0.25rem;padding:0.9rem 1rem;border-radius:18px;background:linear-gradient(135deg,#fff7f3 0%,#f8e7ea 100%);border:1px solid #ead1c8;box-shadow:inset 0 1px 0 rgba(255,255,255,0.75);}
    .overview-chart-body {position:relative;z-index:1;margin-top:0.55rem;padding-top:0.75rem;border-top:1px solid rgba(234,209,200,0.72);}
    .overview-chart-head.category {border-left:6px solid #b24758;}
    .overview-chart-head.trend {border-left:6px solid #773344;}
    .overview-chart-title-wrap {min-width:0;}
    .overview-chart-tag {display:inline-flex;align-items:center;padding:0.28rem 0.68rem;border-radius:999px;background:#ffffff;border:1px solid #ead1c8;color:#8f6f7b;font-size:0.68rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.45rem;}
    .overview-chart-frame .overview-title {margin-bottom:0.22rem;}
    .overview-chart-frame .overview-copy {margin-bottom:0;}
    .fatwa-browser-title {font-family:'Inter Tight','Inter',sans-serif;font-size:1.9rem;font-weight:700;letter-spacing:-0.03em;color:#251329;margin-bottom:0.3rem;}
    .fatwa-browser-copy {font-size:1rem;line-height:1.8;color:#6d5a68;max-width:860px;}
    .explorer-instruction-card {background:linear-gradient(180deg,#fffaf7 0%,#fff2ec 100%);border:1px solid #ead1c8;border-left:6px solid #b24758;border-radius:22px;padding:1rem 1.1rem;margin:0.65rem 0 1rem 0;box-shadow:0 10px 24px rgba(25,14,36,0.05);}
    .explorer-instruction-title {font-size:0.78rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;color:#a3195b;margin-bottom:0.35rem;}
    .explorer-instruction-copy {font-size:0.96rem;line-height:1.78;color:#634e59;}
    .explorer-orb-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;margin:0.8rem 0 1.1rem 0;}
    .explorer-orb {background:linear-gradient(180deg,#fff 0%,#fbf3ef 100%);border:1px solid #ead1c8;border-radius:999px;padding:1rem 1.15rem;display:flex;align-items:center;gap:0.9rem;box-shadow:0 10px 20px rgba(25,14,36,0.05);min-height:92px;}
    .explorer-orb-icon {width:54px;height:54px;border-radius:999px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#d44d5c 0%,#a63a52 100%);color:#fff;font-weight:800;font-size:1.05rem;box-shadow:0 8px 18px rgba(164,59,83,0.22);}
    .explorer-orb-label {font-size:0.74rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin-bottom:0.18rem;}
    .explorer-orb-value {font-family:'Inter Tight','Inter',sans-serif;font-size:1.5rem;font-weight:700;color:#241226;line-height:1.05;}
    .explorer-orb-note {font-size:0.82rem;line-height:1.5;color:#7a6874;margin-top:0.1rem;}
    .donut-insight-card {display:flex;gap:0.62rem;align-items:center;background:linear-gradient(180deg,#fff 0%,#faf4f0 100%);border:1px solid #e8c4b6;border-radius:16px;padding:0.58rem 0.68rem;box-shadow:0 6px 14px rgba(25,14,36,0.04);margin-bottom:0.48rem;min-height:auto;}
    .donut-insight-accent {width:5px;border-radius:999px;align-self:stretch;min-height:unset;}
    .donut-insight-body {display:flex;flex-direction:column;justify-content:center;min-width:0;}
    .donut-insight-name {font-family:'Inter Tight','Inter',sans-serif;font-size:0.86rem;font-weight:700;color:#251329;margin-bottom:0.08rem;line-height:1.2;}
    .donut-insight-stats {display:flex;align-items:baseline;gap:0.14rem;flex-wrap:wrap;}
    .donut-insight-count {font-family:'Inter Tight','Inter',sans-serif;font-size:1.18rem;font-weight:700;color:#7d3347;line-height:1;}
    .donut-insight-pct {font-size:0.78rem;color:#8b6771;line-height:1.35;}
    .align-panel-title {font-size:0.9rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;color:#8f6f7b;margin:0.2rem 0 0.65rem 0;}
    .align-rank-card {background:linear-gradient(180deg,#ffffff 0%,#fbf3ef 100%);border:1px solid #e8c4b6;border-radius:22px;padding:0.95rem 1rem 0.9rem 1rem;box-shadow:0 10px 22px rgba(25,14,36,0.04);margin-bottom:0.75rem;}
    .align-rank-topic {font-family:'Inter Tight','Inter',sans-serif;font-size:1.02rem;font-weight:700;color:#261428;line-height:1.25;margin-bottom:0.45rem;}
    .align-rank-row {display:flex;align-items:center;gap:0.55rem;flex-wrap:wrap;margin-bottom:0.55rem;}
    .align-score {font-family:'Inter Tight','Inter',sans-serif;font-size:1.05rem;font-weight:700;}
    .align-band {font-size:0.86rem;font-weight:700;}
    .align-n {margin-left:auto;font-size:0.84rem;color:#8b6771;}
    .align-bar-bg {height:6px;border-radius:999px;background:#efe2dc;overflow:hidden;}
    .align-bar-fill {height:100%;border-radius:999px;}
    .align-full-row {display:flex;align-items:center;gap:0.65rem;padding:0.65rem 0;border-bottom:1px solid rgba(232,196,182,0.6);}
    .align-full-row:last-child {border-bottom:none;}
    .align-full-rank {font-weight:800;min-width:38px;}
    .align-full-topic {font-weight:700;color:#261428;min-width:180px;max-width:260px;}
    .align-full-score {font-weight:800;min-width:58px;text-align:right;}
    .align-full-n {font-size:0.82rem;color:#8b6771;min-width:42px;text-align:right;}
    .topic-pick-shell {background:linear-gradient(180deg,#fffdfb 0%,#fbf3ef 100%);border:1px solid #e7c3b4;border-radius:24px;padding:1rem 1.05rem;box-shadow:0 10px 24px rgba(25,14,36,0.05);margin:0.4rem 0 0.95rem 0;}
    .topic-pick-kicker {font-size:0.74rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;color:#a3195b;margin-bottom:0.3rem;}
    .topic-pick-title {font-family:'Inter Tight','Inter',sans-serif;font-size:1.2rem;font-weight:700;color:#241226;line-height:1.2;margin-bottom:0.3rem;}
    .topic-pick-copy {font-size:0.95rem;line-height:1.75;color:#6d5a68;max-width:900px;}
    .comparison-select-head {display:flex;justify-content:space-between;align-items:flex-end;gap:1rem;margin:0.1rem 0 0.5rem 0;}
    .comparison-select-title {font-size:0.8rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;color:#8f6f7b;}
    .comparison-select-copy {font-size:0.92rem;line-height:1.65;color:#6d5a68;margin-top:0.2rem;}
    .comparison-card {background:linear-gradient(180deg,#fff 0%,#fbf4f0 100%);border:1px solid #e8c4b6;border-radius:22px;padding:1rem;box-shadow:0 10px 22px rgba(25,14,36,0.05);margin-bottom:0.9rem;}
    .comparison-card-header {font-family:'Inter Tight','Inter',sans-serif;font-size:1.1rem;font-weight:700;color:#251329;margin-bottom:0.6rem;}
    @media (max-width: 980px) {.explorer-orb-grid {grid-template-columns:1fr;} .explorer-orb {border-radius:24px;} .align-full-row {flex-wrap:wrap;} .align-full-topic {max-width:none;min-width:unset;}}


    .chart-panel-plain {padding:0 0 0.45rem 0;margin-bottom:0.25rem;}
    .chart-panel-plain .chart-panel-title {margin-bottom:0.2rem;}
    .chart-panel-plain .chart-panel-copy {margin-bottom:0;max-width:860px;}
    .chart-conclusion {margin-top:0.7rem;padding:0.85rem 0.95rem;border-radius:16px;background:linear-gradient(180deg,#fffaf7 0%,#fff3ed 100%);border:1px solid #ead1c8;color:#6d5a68;font-size:0.88rem;line-height:1.65;}
    .history-overview-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem;align-items:start;}
    .history-overview-card {background:linear-gradient(180deg,#fffdfb 0%,#fbf3ef 100%);border:1px solid #ead1c8;border-radius:28px;padding:1rem 1rem 0.95rem 1rem;box-shadow:0 12px 26px rgba(25,14,36,0.05);overflow:hidden;}
    .history-overview-head {display:flex;flex-direction:column;gap:0.9rem;padding:0.95rem 1rem;border-radius:22px;background:linear-gradient(135deg,#fff9f6 0%,#f8e8eb 100%);border:1px solid #ead1c8;box-shadow:inset 0 1px 0 rgba(255,255,255,0.72);margin-bottom:0.85rem;}
    .history-overview-head.category {border-left:6px solid #b24758;}
    .history-overview-head.trend {border-left:6px solid #773344;}
    .history-overview-tag {display:inline-flex;align-items:center;width:max-content;padding:0.34rem 0.74rem;border-radius:999px;background:#fff;border:1px solid #ead1c8;color:#9a7380;font-size:0.72rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;}
    .history-overview-title {font-family:'Inter Tight','Inter',sans-serif;font-size:2rem;font-weight:800;letter-spacing:-0.04em;line-height:1.02;color:#241226;margin:0 0 0.38rem 0;}
    .history-overview-copy {font-size:0.98rem;line-height:1.75;color:#6d5a68;max-width:640px;}
    .history-overview-stat-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0.45rem;}
    .history-overview-stat {padding:0.72rem 0.78rem;border-radius:18px;background:#fff;border:1px solid #ead1c8;text-align:center;}
    .history-overview-stat-label {font-size:0.68rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;}
    .history-overview-stat-value {margin-top:0.2rem;font-size:1.02rem;font-weight:800;color:#241226;}
    .history-overview-body {padding-top:1rem;margin-top:0.35rem;border-top:1px solid rgba(234,209,200,0.72);}
    .history-overview-footer {display:flex;gap:0.55rem;flex-wrap:wrap;margin-top:0.95rem;}
    .history-overview-chip {display:inline-flex;align-items:center;padding:0.36rem 0.72rem;border-radius:999px;background:#fff;border:1px solid #ead1c8;color:#773344;font-size:0.76rem;font-weight:800;}
    .history-overview-note-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0.55rem;margin-top:1rem;}
    .history-overview-note {padding:0.75rem 0.85rem;border-radius:18px;background:#fff;border:1px solid #ead1c8;font-size:0.88rem;line-height:1.55;color:#6d5a68;}
    .history-overview-note strong {display:block;font-size:0.7rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#8b6771;margin-bottom:0.18rem;}
    .light-table-wrap {margin-top:0.75rem;border:1px solid #ead1c8;border-radius:24px;overflow:hidden;background:linear-gradient(180deg,#fffdfb 0%,#fbf3ef 100%);box-shadow:0 12px 24px rgba(25,14,36,0.04);}
    .light-table {width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;}
    .light-table thead th {background:#f5eef2;color:#773344;font-size:0.76rem;font-weight:800;letter-spacing:0.06em;padding:0.9rem 0.85rem;text-align:left;border-bottom:1px solid #ead1c8;white-space:normal;vertical-align:top;}
    .light-table tbody td {padding:0.9rem 0.85rem;border-bottom:1px solid #f0dfd8;color:#3a2430;font-size:0.88rem;line-height:1.6;vertical-align:top;word-break:break-word;overflow-wrap:anywhere;white-space:normal;}
    .light-table tbody tr:nth-child(even) td {background:rgba(255,255,255,0.45);}
    .light-table tbody tr:last-child td {border-bottom:none;}
    .light-table-cell {display:block;}
    .history-table-shell {background:linear-gradient(180deg,#fffdfb 0%,#fbf3ef 100%);border:1px solid #e7c3b4;border-radius:24px;padding:0.95rem 1rem 1rem 1rem;box-shadow:0 10px 24px rgba(25,14,36,0.05);}
    .history-table-head {display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;margin-bottom:0.75rem;}
    .history-table-title {font-size:1.02rem;font-weight:800;color:#241226;margin-bottom:0.2rem;}
    .history-table-copy {font-size:0.9rem;line-height:1.65;color:#6d5a68;max-width:860px;}
    .history-table-pill {display:inline-flex;align-items:center;padding:0.4rem 0.8rem;border-radius:999px;background:#fff7f4;border:1px solid #ead1c8;color:#773344;font-size:0.78rem;font-weight:800;white-space:nowrap;}
    .metric-card-info {margin-top:0.1rem;font-size:0.84rem;line-height:1.6;color:#6d5a68;text-align:center;}
    .metric-card-info strong {display:block;color:#221221;margin-bottom:0.12rem;}
    .sim-lite-summary-copy.alt {font-size:0.9rem;line-height:1.75;color:#6d5a68;}
    @media (max-width: 1150px) {.history-overview-grid {grid-template-columns:1fr;} .history-overview-stat-grid{grid-template-columns:1fr 1fr 1fr;} }
    @media (max-width: 820px) {.history-overview-note-grid,.history-overview-stat-grid {grid-template-columns:1fr;} .history-table-head{flex-direction:column;} .light-table, .light-table thead, .light-table tbody, .light-table th, .light-table td, .light-table tr {display:block;} .light-table thead {display:none;} .light-table tbody tr {padding:0.55rem 0;border-bottom:1px solid #ead1c8;} .light-table tbody td {display:grid;grid-template-columns:130px 1fr;gap:0.75rem;align-items:start;padding:0.55rem 0.9rem;background:transparent !important;border-bottom:none;} .light-table tbody td::before {content:attr(data-label);font-size:0.72rem;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;color:#8b6771;} }

</style>
    """, unsafe_allow_html=True)


def build_sidebar_current_review_html(bundle):
    if not bundle:
        return (
            "<div class='sidebar-mini-note'><strong>No analysis selected yet.</strong><br>"
            "Run a review to see the detected topic, best state match, score band, and compliance summary here.</div>"
        )

    topic = html.escape(str(bundle.get('topic_label', '-')))
    state = html.escape(str(bundle.get('best_state_name', '-')))
    issue = html.escape(str(bundle.get('specific_issue', '-')))
    score = safe_float(bundle.get('final_match_score'))
    rec = html.escape(str(bundle.get('recommendation_label', 'Moderate Alignment')))
    conf = html.escape(str(bundle.get('confidence', 'Unknown')))
    comp = html.escape(str(bundle.get('compliance_level', 'Unclear')))
    band = get_score_band_label(score)
    tone = score_status_color(score)
    return textwrap.dedent(f"""
    <div class='sidebar-insight-list'>
        <div class='sidebar-insight-card' style='background:rgba(255,255,255,0.09);'>
            <div class='sidebar-insight-label'>Current result</div>
            <div class='sidebar-insight-value' style='display:flex;align-items:center;justify-content:space-between;gap:0.5rem;'>
                <span>{score:.1f}%</span>
                <span style='padding:0.28rem 0.6rem;border-radius:999px;background:{tone}22;border:1px solid {tone};color:#fff;font-size:0.72rem;font-weight:800;'>{band}</span>
            </div>
            <div class='sidebar-insight-copy'>{rec} · {comp}</div>
        </div>
        <div class='sidebar-insight-card'>
            <div class='sidebar-insight-label'>Detected topic</div>
            <div class='sidebar-insight-value'>{topic}</div>
            <div class='sidebar-insight-copy'>Issue: {issue}</div>
        </div>
        <div class='sidebar-insight-card'>
            <div class='sidebar-insight-label'>Best matching state</div>
            <div class='sidebar-insight-value'>{state}</div>
            <div class='sidebar-insight-copy'>Confidence: {conf}</div>
        </div>
    </div>
    """).strip()


def build_sidebar_score_guide_html():
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


def render_single_review_empty_state(total_analyses, avg_score_sidebar, recent_topics):
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


def build_sidebar_latest_bundle():
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
        "Semantic similarity model is not available. Please install and load sentence-transformers / all-MiniLM-L6-v2 before running analysis."
    )
    st.info(
        "Why this matters: your final score depends heavily on semantic similarity, so running without SBERT can make results misleading."
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

def get_detected_topic_explanation(topic_label, specific_issue):
    topic_label = str(topic_label).strip()
    specific_issue = str(specific_issue).strip()

    if specific_issue and specific_issue != "No specific issue identified":
        if topic_label and topic_label.lower() in specific_issue.lower():
            return (
                f"The system matched the response directly to the topic '{topic_label}' "
                f"and linked it to the closest reference issue: '{specific_issue}'."
            )
        return (
            f"The system classified the response under the broader topic "
            f"'{topic_label}' and matched it most closely to the specific issue: "
            f"'{specific_issue}'."
        )

    return (
        f"The system classified the response under the broader topic '{topic_label}', "
        f"but no clearer specific issue could be extracted from the matched reference."
    )

def get_badge_html(label: str) -> str:
    if label in {"High", "Good Match", "Strong Match", "Fully Compliant", "High Alignment", "Strong Alignment"}:
        return '<span class="badge badge-good">{}</span>'.format(label)
    if label in {"Medium", "Moderate Match", "Partially Compliant", "Needs Review", "Partial Alignment", "Moderate Alignment"}:
        return '<span class="badge badge-mid">{}</span>'.format(label)
    return '<span class="badge badge-low">{}</span>'.format(label)

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

def get_learning_note(topic_label):
    topic_label = str(topic_label).strip()

    notes = {
        "IVF": {
            "title": "Fatwa Learning Insight",
            "text": "IVF is generally permissible only when the sperm and ovum come from a legally married husband and wife, and the procedure happens within the valid marriage period."
        },
        "Surrogacy": {
            "title": "Fatwa Learning Insight",
            "text": "Surrogacy is generally prohibited because it may create confusion in lineage, motherhood, and family rights under Islamic law."
        },
        "Gamete Implantation for Reproduction": {
            "title": "Fatwa Learning Insight",
            "text": "Gamete implantation cases are usually assessed based on whether the reproductive material belongs only to the legally married couple and whether lineage remains protected."
        },
        "Human Milk Bank": {
            "title": "Fatwa Learning Insight",
            "text": "Human milk bank issues are sensitive because milk feeding may establish mahram relationships, and uncontrolled donation can create uncertainty in nasab and kinship."
        },
        "Sperm Bank": {
            "title": "Fatwa Learning Insight",
            "text": "Sperm banks are generally prohibited because third-party sperm introduces lineage and paternity concerns that conflict with core Islamic family principles."
        },
        "Abortion due to fetal abnormality": {
            "title": "Fatwa Learning Insight",
            "text": "Abortion cases involving fetal abnormality are usually discussed carefully based on severity, timing, and whether there is serious harm or hardship recognized in Islamic legal reasoning."
        },
        "Abortion for maternal health": {
            "title": "Fatwa Learning Insight",
            "text": "Where the mother faces serious danger, preserving life becomes a major consideration in the ruling, so maternal health may strongly affect the fatwa outcome."
        },
        "Abortion ruling": {
            "title": "Fatwa Learning Insight",
            "text": "General abortion rulings are not assessed only by wording. Timing of pregnancy, level of harm, and legal circumstances are often central to the fatwa."
        },
        "Abortion resulting from rape": {
            "title": "Fatwa Learning Insight",
            "text": "Cases involving rape are discussed with greater sensitivity, but the ruling still depends on conditions such as harm, timing, and wider Islamic legal principles."
        },
        "Abortion of fetus conceived through zina": {
            "title": "Fatwa Learning Insight",
            "text": "A pregnancy resulting from zina does not automatically change every ruling. Islamic legal discussion still considers the status of the fetus and the limits of abortion."
        },
        "Abortion for OKU victims": {
            "title": "Fatwa Learning Insight",
            "text": "Cases involving OKU victims require extra ethical sensitivity and are usually assessed through protection, hardship, and harm-minimization principles."
        },
        "Abortion in high-risk groups": {
            "title": "Fatwa Learning Insight",
            "text": "High-risk pregnancy rulings often focus on medical risk and the preservation of life, especially when continuing the pregnancy may cause severe harm."
        },
        "Provision of contraceptives": {
            "title": "Fatwa Learning Insight",
            "text": "Contraceptive rulings usually depend on purpose, method, and whether their use remains within acceptable Islamic ethical and family boundaries."
        },
        "Contraceptives for unmarried individuals": {
            "title": "Fatwa Learning Insight",
            "text": "For unmarried individuals, contraceptive discussions often involve wider moral and social concerns, not only the function of the contraceptive method itself."
        },
        "Contraceptives for rape victims": {
            "title": "Fatwa Learning Insight",
            "text": "Contraceptive use for rape victims is usually discussed through harm reduction, dignity, and emergency circumstances in Islamic legal reasoning."
        },
        "Contraceptives for adolescents": {
            "title": "Fatwa Learning Insight",
            "text": "Contraceptive use involving adolescents is often assessed not only medically, but also through moral, educational, and social protection concerns."
        },
        "Contraceptives for HIV/AIDS prevention": {
            "title": "Fatwa Learning Insight",
            "text": "In HIV/AIDS prevention, the ruling may involve public harm reduction, health protection, and ethical boundaries regarding preventive methods."
        },
        "Abortion due to genetic disease (Example, Thalassemia)": {
            "title": "Fatwa Learning Insight",
            "text": "Genetic disease cases are often evaluated based on severity, certainty of diagnosis, and whether the condition creates serious hardship that affects the ruling."
        },
        "Abortion of Foetus with Thalassemia": {
            "title": "Fatwa Learning Insight",
            "text": "Thalassemia-related abortion cases are typically assessed through medical seriousness, timing of pregnancy, and the balance between hardship and protection of life."
        },
        "Human Cloning (Reproductive)": {
            "title": "Fatwa Learning Insight",
            "text": "Reproductive cloning is generally rejected because it raises major concerns about human dignity, lineage, and the natural structure of family creation."
        },
        "Human Cloning (Therapeutic)": {
            "title": "Fatwa Learning Insight",
            "text": "Therapeutic cloning may be discussed differently from reproductive cloning, but it still requires close ethical review regarding source, purpose, and limits."
        },
        "Stem Cell Research": {
            "title": "Fatwa Learning Insight",
            "text": "Stem cell research is usually assessed based on the source of the cells, the intended benefit, and whether the method respects Islamic ethical boundaries."
        },
    }

    default_note = {
        "title": "Fatwa Learning Insight",
        "text": "This topic should be understood not only through wording similarity, but also through underlying Islamic principles such as lineage, harm prevention, dignity, and family rights."
    }

    return notes.get(topic_label, default_note)

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


    st.markdown(_html("""
    <div class='result-reading-guide'>
        <div class='result-reading-guide-title'>How to read this result</div>
        <div class='result-reading-guide-copy'><strong>Text match</strong> checks similar wording, <strong>Meaning match</strong> checks whether the answer says the same idea, <strong>Key points</strong> checks whether important fatwa conditions were mentioned, and <strong>Overall fit</strong> shows the broader strength across state fatwa comparisons.</div>
    </div>
    """), unsafe_allow_html=True)

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
        st.markdown(_html("""
        <div style='background:linear-gradient(180deg,#fff7f8 0%,#f9eeef 100%);border:1px solid #e7c3b4;border-left:6px solid #9f3448;border-radius:24px;padding:1.15rem 1.2rem;box-shadow:0 8px 18px rgba(25,14,36,0.04);'>
            <div style='display:inline-flex;align-items:center;padding:0.3rem 0.78rem;border-radius:999px;background:#fff;border:1px solid #e2c1b6;color:#8f6f7b;font-size:0.72rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.7rem;'>History</div>
            <div style='font-family:"Inter Tight","Inter",sans-serif;font-size:1.15rem;font-weight:800;color:#241226;margin-bottom:0.25rem;'>Alignment band distribution</div>
            <div style='font-size:0.9rem;color:#6d5a68;line-height:1.7;'>How many saved analyses fall into weak, moderate, and good match ranges.</div>
        </div>
        """), unsafe_allow_html=True)
        st.markdown("<div style='height:1.35rem;'></div>", unsafe_allow_html=True)
        st.altair_chart(bar_chart, use_container_width=True)
        st.markdown(_html(f"""
        <div style='display:flex;gap:0.8rem;margin-top:0.75rem;flex-wrap:wrap;'>
            <div style='font-size:0.88rem;padding:0.5rem 0.8rem;border-radius:12px;background:#fff;border:1px solid #ead1c8;color:#8f4455;'><strong>Weak:</strong> {weak_count}</div>
            <div style='font-size:0.88rem;padding:0.5rem 0.8rem;border-radius:12px;background:#fff;border:1px solid #ead1c8;color:#8f4455;'><strong>Moderate:</strong> {moderate_count}</div>
            <div style='font-size:0.88rem;padding:0.5rem 0.8rem;border-radius:12px;background:#fff;border:1px solid #ead1c8;color:#8f4455;'><strong>Good:</strong> {good_count}</div>
        </div>
        <div style='margin-top:0.8rem;font-size:0.9rem;color:#6d5a68;line-height:1.7;padding:0.95rem 1rem;border-radius:18px;background:#fff8f4;border:1px solid #ead1c8;'>
            <strong style='color:#241226;'>Main pattern:</strong> {main_pattern} appears most often in your saved runs.
        </div>
        """), unsafe_allow_html=True)

    with history_col2:
        st.markdown(_html("""
        <div style='background:linear-gradient(180deg,#fff7f8 0%,#f9eeef 100%);border:1px solid #e7c3b4;border-left:6px solid #9f3448;border-radius:24px;padding:1.15rem 1.2rem;box-shadow:0 8px 18px rgba(25,14,36,0.04);'>
            <div style='display:inline-flex;align-items:center;padding:0.3rem 0.78rem;border-radius:999px;background:#fff;border:1px solid #e2c1b6;color:#8f6f7b;font-size:0.72rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.7rem;'>Trend</div>
            <div style='font-family:"Inter Tight","Inter",sans-serif;font-size:1.15rem;font-weight:800;color:#241226;margin-bottom:0.25rem;'>Match score movement over time</div>
            <div style='font-size:0.9rem;color:#6d5a68;line-height:1.7;'>Follow the score pattern across saved runs. The dashed line marks the 70% stronger-alignment line.</div>
        </div>
        """), unsafe_allow_html=True)
        st.markdown("<div style='height:1.35rem;'></div>", unsafe_allow_html=True)
        st.altair_chart(trend_chart, use_container_width=True)
        st.markdown(_html(f"""
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
        """), unsafe_allow_html=True)

def clean_preview_text(text: str, max_len: int = 260) -> str:
    text = "" if pd.isna(text) else str(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "No preview is available for the current selection."
    return text if len(text) <= max_len else text[: max_len - 3].rstrip() + "..."

def build_dataset_snapshot_html(
    selected_question_text: str,
    selected_model: str,
    selected_response: str,
    total_rows: int,
    total_questions: int,
    selected_model_count: int,
    total_models: int,
) -> str:
    preview_raw = clean_preview_text(selected_response, 10000)
    preview_text = html.escape(clean_preview_text(selected_response, 240))
    question_text = html.escape(clean_preview_text(selected_question_text, 96))
    words = len(preview_raw.split())
    chars = len(preview_raw)
    coverage_pct = int(round((selected_model_count / total_models) * 100)) if total_models else 0
    density_pct = max(8, min(100, int(round(words))))
    depth_pct = max(8, min(100, int(round((chars / 240) * 100)))) if chars else 8

    return f"""
    <div class="dataset-side-panel">
        <div class="dataset-side-header">
            <div>
                <div class="dataset-side-title">Dataset snapshot</div>
                <div class="dataset-side-subtitle">Clean summary for the currently selected question and model.</div>
            </div>
            <div class="dataset-model-chip">{html.escape(selected_model or "Model")}</div>
        </div>

        <div class="dataset-stat-grid">
            <div class="dataset-stat-card">
                <div class="dataset-stat-label">Saved rows</div>
                <div class="dataset-stat-value">{total_rows}</div>
            </div>
            <div class="dataset-stat-card">
                <div class="dataset-stat-label">Questions</div>
                <div class="dataset-stat-value">{total_questions}</div>
            </div>
            <div class="dataset-stat-card">
                <div class="dataset-stat-label">Words</div>
                <div class="dataset-stat-value">{words}</div>
            </div>
            <div class="dataset-stat-card">
                <div class="dataset-stat-label">Characters</div>
                <div class="dataset-stat-value">{chars}</div>
            </div>
        </div>

        <div class="dataset-ring-row">
            <div class="dataset-ring" style="--dataset-ring:{coverage_pct}%;">
                <div class="dataset-ring-inner">
                    <strong>{coverage_pct}%</strong>
                    <span>coverage</span>
                </div>
            </div>
            <div class="dataset-ring-copy">
                <div class="dataset-ring-title">Model availability</div>
                <div class="dataset-ring-text">{selected_model_count} of {total_models} saved model variants are available for this question.</div>
            </div>
        </div>

        <div class="dataset-mini-bars">
            <div class="dataset-mini-bar-row">
                <span class="dataset-mini-bar-label">Model coverage</span>
                <div class="dataset-mini-bar-track"><div class="dataset-mini-bar-fill" style="width:{coverage_pct}%;"></div></div>
                <span class="dataset-mini-bar-value">{coverage_pct}%</span>
            </div>
            <div class="dataset-mini-bar-row">
                <span class="dataset-mini-bar-label">Preview density</span>
                <div class="dataset-mini-bar-track"><div class="dataset-mini-bar-fill secondary" style="width:{density_pct}%;"></div></div>
                <span class="dataset-mini-bar-value">{words}</span>
            </div>
            <div class="dataset-mini-bar-row">
                <span class="dataset-mini-bar-label">Text depth</span>
                <div class="dataset-mini-bar-track"><div class="dataset-mini-bar-fill tertiary" style="width:{depth_pct}%;"></div></div>
                <span class="dataset-mini-bar-value">{chars}</span>
            </div>
        </div>

        <div class="dataset-preview-box">
            <div class="dataset-preview-label">Selected question</div>
            <div class="dataset-preview-text">{question_text}</div>
        </div>

        <div class="dataset-preview-box dataset-preview-box-soft">
            <div class="dataset-preview-label">Response preview</div>
            <div class="dataset-preview-text">{preview_text}</div>
        </div>
    </div>
    """

def _html(block: str) -> str:
    cleaned = textwrap.dedent(block).strip()
    # Streamlit markdown can interpret indented HTML lines as code blocks.
    # Strip leading indentation from each line so HTML renders as HTML instead of
    # appearing as raw hard-coded markup in the UI.
    return "\n".join(line.lstrip() for line in cleaned.splitlines())


def render_editorial_intro(kicker: str, title: str, copy: str, meta_items=None):
    meta_items = meta_items or []
    meta_html = ""
    if meta_items:
        meta_html = "<div class='editorial-meta'>" + "".join(f"<span>{html.escape(str(item))}</span>" for item in meta_items) + "</div>"
    st.markdown(_html(f"""
    <div class='editorial-section'>
        <div class='editorial-kicker'>{html.escape(kicker)}</div>
        <h2 class='editorial-title'>{html.escape(title)}</h2>
        <div class='editorial-copy'>{html.escape(copy)}</div>
        {meta_html}
    </div>
    """), unsafe_allow_html=True)


def render_inline_section(label: str, title: str, copy: str, side_text: str = ""):
    side_html = f"<div class='inline-section-side'>{html.escape(side_text)}</div>" if side_text else ""
    st.markdown(_html(f"""
    <div class='inline-section-head'>
        <div>
            <div class='inline-section-label'>{html.escape(label)}</div>
            <div class='inline-section-title'>{html.escape(title)}</div>
            <div class='inline-section-copy'>{html.escape(copy)}</div>
        </div>
        {side_html}
    </div>
    """), unsafe_allow_html=True)


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
            <div class='{card_class}'>
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
        text_marks = alt.Chart(chart_long).mark_text(dy=-10, color='#5d3945', fontSize=11, fontWeight='bold').encode(x=alt.X('Metric:N', sort=metric_order), xOffset=alt.XOffset('Entity:N', sort=entity_order), y=alt.Y('Score:Q', scale=alt.Scale(domain=[0,100])), text=alt.Text('Score:Q', format='.0f'))
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
            _render_leaderboard_cards(summary_df, 'Model leaderboard', 'This ranking shows which AI model gave the strongest overall average fit. Read the small metric line under each model to see why it placed there.', entity_col='model')
            best = summary_df.iloc[0]
            second = summary_df.iloc[1] if len(summary_df) > 1 else None
            margin = f" by {best['score'] - second['score']:.1f} points" if second is not None else ''
            st.markdown(f"<div class='chart-conclusion'><strong>Conclusion:</strong> <strong>{html.escape(str(best['model']))}</strong> is the most reliable overall performer{margin}.</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div style='height:4.2rem;'></div>", unsafe_allow_html=True)
            _render_grouped_bars(summary_df, 'model', 'Metric comparison by model', 'Each metric group shows the models side by side so users can quickly see who was stronger in meaning, wording, and key fatwa coverage.')
    else:
        summary_df = (
            chart_df.groupby('label', as_index=False)
            .agg(score=('score','mean'), semantic=('semantic','mean'), lexical=('lexical','mean'), coverage=('coverage','mean'))
            .sort_values('score', ascending=False)
            .reset_index(drop=True)
        )
        with c1:
            _render_leaderboard_cards(summary_df, 'Response leaderboard', 'A simple ranking of which response matched the fatwa reference best overall.', entity_col='label')
            best = summary_df.iloc[0]
            st.markdown(f"<div class='chart-conclusion'><strong>Conclusion:</strong> <strong>{html.escape(str(best['label']))}</strong> gives the strongest overall fit at {best['score']:.1f}%.</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div style='height:4.2rem;'></div>", unsafe_allow_html=True)
            _render_grouped_bars(summary_df, 'label', 'Metric comparison by response', 'Side-by-side bars make it easier to compare meaning match, text match, and key fatwa points for each response.')

def render_circular_metric_chart(metric_name: str, score: float, description: str):
    """Render a circular progress chart (donut) for a single metric."""
    score_val = max(0, min(100, score))
    color = "#06A77D" if score_val >= 70 else "#F1A208" if score_val >= 50 else "#A31621"
    degrees = int(score_val * 3.6)
    
    html_content = f"""
    <div style="text-align: center; padding: 0.2rem;">
        <div style="position: relative; width: 80px; height: 80px; margin: 0 auto;">
            <div style="width: 80px; height: 80px; border-radius: 50%; background: conic-gradient({color} {degrees}deg, #e6d8e2 {degrees}deg); display: flex; align-items: center; justify-content: center;">
                <div style="width: 60px; height: 60px; border-radius: 50%; background: #ffffff; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <strong style="font-family: 'DM Serif Display', serif; font-size: 1rem; color: {color};">{score_val:.0f}%</strong>
                </div>
            </div>
        </div>
        <div style="margin-top: 0.4rem;">
            <div style="font-weight: 700; font-size: 0.7rem; color: #3b1d4a;">{metric_name}</div>
            <div style="font-size: 0.6rem; color: #8b6771; margin-top: 0.1rem;">{description}</div>
        </div>
    </div>
    """
    
    st.markdown(html_content, unsafe_allow_html=True)

def render_metric_circular_grid(lexical_score, semantic_score, coverage_score, mean_alignment):
    """Render 4 circular metric charts in a grid."""
    
    col1, col2, col3, col4 = st.columns(4, gap="small")
    
    with col1:
        render_circular_metric_chart("TF-IDF", lexical_score, "Word overlap")
    
    with col2:
        render_circular_metric_chart("SBERT", semantic_score, "Meaning match")
    
    with col3:
        render_circular_metric_chart("Coverage", coverage_score, "Key terms found")
    
    with col4:
        render_circular_metric_chart("Mean Align", mean_alignment, "Avg across states")
        
def build_metric_explainer_text(metric_key: str, score: float) -> str:
    score = safe_float(score)
    if metric_key == "text":
        return "Uses many of the same words." if score >= 70 else "Uses some of the same words." if score >= 50 else "Uses quite different words."
    if metric_key == "meaning":
        return "Very close in meaning." if score >= 70 else "Quite close in meaning." if score >= 50 else "Not very close in meaning."
    if metric_key == "key_points":
        return "Most main points are included." if score >= 70 else "Some main points are included." if score >= 50 else "Important points are still missing."
    return "Strong across state rulings." if score >= 70 else "Mixed across state rulings." if score >= 50 else "Weak across state rulings."


def build_score_method_copy(final_match_score, lexical_score, semantic_score, coverage_score, mean_alignment):
    final_match_score = safe_float(final_match_score)
    if final_match_score >= 70:
        return "This final score means the answer is close to the fatwa and gets most important points right."
    if final_match_score >= 50:
        return "This final score means the answer is partly correct, but some important points still need checking."
    return "This final score means the answer is not close enough to the fatwa yet and needs careful review."


def build_confidence_explainer(confidence: str) -> str:
    confidence = str(confidence).strip().lower()
    if confidence == "high":
        return "The topic match looks clear."
    if confidence == "medium":
        return "The topic match looks fairly clear."
    return "The topic match is less certain."


def build_compliance_explainer(level: str) -> str:
    level = str(level).strip().lower()
    if level == "fully compliant":
        return "It follows the ruling well."
    if level == "partially compliant":
        return "Some parts fit, but it still needs review."
    if level == "non-compliant":
        return "It does not fit the ruling closely."
    return "The status is not clear yet and needs manual review."


def build_professional_result_label(score: float) -> str:
    score = safe_float(score)
    if score >= 70:
        return "Strong Alignment"
    if score >= 50:
        return "Moderate Alignment"
    return "Low Alignment"


def get_action_label(score: float) -> str:
    score = safe_float(score)
    if score >= 70:
        return "Good to Use"
    if score >= 50:
        return "Needs Review"
    return "Not Reliable"


def build_user_result_title(score: float) -> str:
    return build_professional_result_label(score)


def build_user_result_summary(score: float) -> str:
    score = safe_float(score)
    if score >= 70:
        return "This answer is generally close to the matched fatwa and covers the main ruling points."
    if score >= 50:
        return "This answer is partly correct, but some important ruling details still need human review."
    return "This answer is still too far from the fatwa, so it needs careful checking before anyone relies on it."


def build_action_note(score: float) -> str:
    score = safe_float(score)
    if score >= 70:
        return "Use as a strong draft, then do a quick final check."
    if score >= 50:
        return "Check the fatwa text before accepting this answer."
    return "Rewrite or review this answer manually first."


def render_similarity_breakdown(bundle: dict):
    final_match_score = safe_float(bundle.get("final_match_score"))
    lexical_score = safe_float(bundle.get("lexical_score"))
    semantic_score = safe_float(bundle.get("semantic_score"))
    coverage_score = safe_float(bundle.get("coverage_score"))
    mean_alignment = safe_float(bundle.get("mean_alignment"))

    score_color = score_status_color(final_match_score)
    ring_degrees = max(0.0, min(360.0, final_match_score * 3.6))
    conclusion_copy = build_score_method_copy(final_match_score, lexical_score, semantic_score, coverage_score, mean_alignment)
    conclusion_label = build_professional_result_label(final_match_score)

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

    metric_items = [
        ("Text match", lexical_score, "text", "Words used"),
        ("Meaning match", semantic_score, "meaning", "Same meaning"),
        ("Key points", coverage_score, "key_points", "Main points"),
        ("Overall fit", mean_alignment, "overall", "State match"),
    ]
    cols = st.columns(2, gap='small')
    for idx, (label, value, key_name, subhead) in enumerate(metric_items):
        tone = score_status_color(value)
        with cols[idx % 2]:
            st.markdown(_html(f"""
            <div class='sim-lite-metric'>
                <div class='sim-lite-metric-label'>{html.escape(label)}</div>
                <div class='sim-lite-metric-value' style='color:{tone};'>{int(round(value))}%</div>
                <div class='metric-card-info'><strong style='color:#221221;'>{html.escape(subhead)}.</strong> {html.escape(build_metric_explainer_text(key_name, value))}</div>
            </div>
            """), unsafe_allow_html=True)

def render_single_review_result_dashboard(bundle: dict):
    final_match_score = safe_float(bundle.get("final_match_score"))
    semantic_score = safe_float(bundle.get("semantic_score"))
    lexical_score = safe_float(bundle.get("lexical_score"))
    coverage_score = safe_float(bundle.get("coverage_score"))
    mean_alignment = safe_float(bundle.get("mean_alignment"))
    topic_label = str(bundle.get("topic_label", "-"))
    specific_issue = str(bundle.get("specific_issue", "-"))
    best_state = str(bundle.get("best_state_name", "-"))
    recommendation_label = str(bundle.get("recommendation_label", build_professional_result_label(final_match_score)))
    recommendation_reason = str(bundle.get("recommendation_reason", ""))
    compliance_level = str(bundle.get("compliance_level", "Unclear"))
    confidence = str(bundle.get("confidence", "Unknown"))
    fatwa_text = str(bundle.get("fatwa_text", "")).strip()
    issue_name = str(bundle.get("issue_name", "")).strip() or topic_label or "N/A"
    matched_list = bundle.get("matched_list", [])
    missing_list = bundle.get("missing_list", [])
    tone = score_status_color(final_match_score)

    preview_reference = html.escape((fatwa_text[:180] + "...") if fatwa_text and len(fatwa_text) > 180 else (fatwa_text or "No text available"))
    result_title = build_user_result_title(final_match_score)
    result_summary = build_user_result_summary(final_match_score)
    action_label = get_action_label(final_match_score)
    action_note = build_action_note(final_match_score)
    confidence_copy = build_confidence_explainer(confidence)
    compliance_copy = build_compliance_explainer(compliance_level)
    recommendation_copy = html.escape(recommendation_reason) if recommendation_reason else html.escape(result_summary)
    review_status_copy = html.escape(build_score_method_copy(final_match_score, lexical_score, semantic_score, coverage_score, mean_alignment))

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

    st.markdown(_html(f"""
    <div style='margin:0.95rem 0 1.25rem 0;'>
        <div style='display:grid;grid-template-columns:1.05fr 1.35fr 1fr;gap:1rem;'>
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
    </div>
    """), unsafe_allow_html=True)


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
    banner_path = resolve_header_banner_path()
    st.markdown(
        """
        <style>
        .dashboard-shell-header {margin-bottom: 1.2rem;}
        </style>
        <div class="dashboard-shell-header"></div>
        """,
        unsafe_allow_html=True,
    )
    render_hero_banner(banner_path, title=title, subtitle=subtitle, kicker=kicker)

section_banner_path = resolve_header_banner_path()

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-clean-header compact-sidebar-header">
            <div class="sidebar-kicker-line"></div>
            <h1 class="sidebar-title">AI Fatwa Review</h1>
            <h3 class="sidebar-subtitle">A structured approach to reviewing and validating AI-generated responses.</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not sbert_is_ready():
        st.markdown(
            "<div class='msg-box msg-warning'><strong>SBERT unavailable.</strong> Semantic scoring may be incomplete.</div>",
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
render_dashboard_shell_header()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Single Review",
    "Batch Review",
    "History & Export",
    "Fatwa Explorer",
    "Topic Explorer"
])

# =========================================================
# TAB 1
# =========================================================
# =========================================================
# Inside fyp_dashboard.py - TAB 1 section with reduced spacing
# =========================================================

with tab1:

    render_minimal_tab_intro(
        "Single review",
        "Closest fatwa alignment",
        "Check one answer and see how closely it matches the most relevant fatwa.",
        extra_class="single-review-hero"
    )

    review_left, review_right = st.columns([0.58, 0.42], gap="small")

    with review_left:

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

            st.markdown(_html("""
            <div class='slim-loader-head'>
                <div>
                    <div class='slim-loader-kicker'>Load a saved answer</div>
                    <div class='slim-loader-title'>Input source</div>
                    <div class='slim-loader-copy'>Pick a saved question and AI model to place an existing response into the review area instantly.</div>
                </div>
                <div class='slim-loader-side'>Dataset quick load</div>
            </div>
            """), unsafe_allow_html=True)
            st.markdown("<div class='dataset-loader-minimal'>", unsafe_allow_html=True)

            ctrl1, ctrl2, ctrl3 = st.columns([0.5, 0.23, 0.27], gap="small")
            with ctrl1:
                st.markdown("<div class='dataset-control-caption'>Question</div>", unsafe_allow_html=True)
                selected_question_text = st.selectbox(
                    "Question",
                    options=list(question_options.keys()),
                    index=list(question_options.keys()).index(selected_question_text),
                    key="ds_question_select",
                    label_visibility="collapsed"
                )
            with ctrl2:
                st.markdown("<div class='dataset-control-caption'>AI model</div>", unsafe_allow_html=True)
                selected_model = st.selectbox(
                    "AI Model",
                    options=available_models,
                    index=available_models.index(selected_model) if selected_model in available_models else 0,
                    key="ds_model_select",
                    label_visibility="collapsed"
                )
            with ctrl3:
                st.markdown("<div class='dataset-control-caption'>Action</div>", unsafe_allow_html=True)
                load_btn = st.button("Load response →", use_container_width=True, key="ds_load_btn_primary")

            st.markdown("</div>", unsafe_allow_html=True)

            selected_qid = question_options[selected_question_text]
            question_subset = ai_answer_df[ai_answer_df["question_id"] == selected_qid].copy()
            selected_match = question_subset[question_subset["model"] == selected_model]

            if load_btn:
                if not selected_match.empty:
                    st.session_state["ai_input"] = selected_match.iloc[0]["ai_answer_raw"]
                    st.session_state["load_success_toast"] = True
                    st.rerun()
                else:
                    st.warning(f"No pre-collected response found for {selected_model}.")

        st.markdown(_html("""
            <div class='input-editor-shell'>
                <div class='input-editor-head'>
                    <div>
                        <div class='input-editor-kicker'>Response workspace</div>
                        <div class='input-editor-title'>Paste the answer you want to review</div>
                    </div>
                    <div class='input-editor-chip'>Single answer</div>
                </div>
            </div>
        """), unsafe_allow_html=True)
        ai_response = st.text_area(
            "AI Response Input",
            height=260,
            placeholder="Paste the answer here or load one from the dataset above...",
            key="ai_input",
            label_visibility="collapsed"
        )

        if st.session_state.pop('load_success_toast', False):
            st.markdown("""
            <div class='floating-success-toast'>
                <div class='floating-success-icon'>✓</div>
                <div class='floating-success-title'>Saved response loaded</div>
                <div class='floating-success-copy'>The selected dataset answer has been placed into the response workspace and is ready for review.</div>
            </div>
            """, unsafe_allow_html=True)

        b1, b2 = st.columns([0.62, 0.38], gap="small")
        with b1:
            analyze_btn = st.button("Analyze response", use_container_width=True, key="analyze_single")
        with b2:
            clear_btn = st.button("Clear history", use_container_width=True, key="clear_all_single")
    with review_right:
        st.markdown("<div class='single-review-right-col'>", unsafe_allow_html=True)
        if st.session_state.get("current_analysis"):
            render_similarity_breakdown(st.session_state["current_analysis"])
        else:
            render_single_review_empty_state(total_analyses, avg_score_sidebar, recent_topics)
        st.markdown("</div>", unsafe_allow_html=True)


    # Remove the extra spacing by not adding additional empty divs
    # The result will appear directly below without extra margin

    if clear_btn:
        clear_history()
        st.success("History cleared successfully.")
        st.rerun()

    if analyze_btn:
        if not ai_response.strip():
            st.warning("Please paste an AI response before analyzing.")
        elif not ensure_analysis_dependencies():
            st.stop()
        else:
            with st.spinner("Analyzing response..."):
                ensure_similarity_engine_loaded()
                best_question, question_scores = detect_best_question(ai_response, fatwa_df)
                detected_subset = fatwa_df[fatwa_df["question_id"] == best_question["question_id"]].copy()
                best_state, state_results = unpack_state_comparison(compare_states_within_question(ai_response, detected_subset))
                if not best_state or state_results.empty:
                    st.warning("No state-level fatwa comparison could be generated for this response.")
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
                    "final_match_score": final_match_score,
                    "mean_alignment": mean_alignment,
                    "lexical_similarity": lexical_score,
                    "semantic_similarity": semantic_score,
                    "coverage": coverage_score,
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
                
                st.rerun()

    # Result appears directly below with minimal spacing
    if st.session_state.get("current_analysis"):
        render_single_review_result_dashboard(st.session_state["current_analysis"])

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
# TAB 2
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


    st.markdown(_html("""
    <div class='batch-shell compact'>
        <div class='batch-shell-head'>
            <div>
                <div class='batch-kicker'>Review builder</div>
                <div class='batch-title'>Batch comparison</div>
                <div class='batch-copy'>Compare several saved or manual answers in one view.</div>
            </div>
        </div>
    </div>
    """), unsafe_allow_html=True)

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
            f"Run Batch Analysis ({len(responses_to_run)} responses)",
            use_container_width=True,
            key="batch_dataset_run"
        )

    else:

        mc1, mc2 = st.columns([0.68, 0.32])
        with mc1:
            st.markdown("<div class='input-editor-shell batch-manual-shell'><div class='input-editor-head'><div><div class='input-editor-kicker'>Manual batch input</div><div class='input-editor-title'>Paste one answer per block</div></div><div class='input-editor-chip'>Split with ---</div></div></div>", unsafe_allow_html=True)
            batch_responses = st.text_area(
                "Enter multiple responses (separate with ---)",
                height=300,
                placeholder="Response 1...\n\n---\n\nResponse 2...\n\n---\n\nResponse 3...",
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
        run_batch_btn = st.button("Start Batch Analysis", use_container_width=True, key="batch_analyze")

    if run_batch_btn:
        if not responses_to_run:
            st.warning("Please choose or paste at least one response before starting batch analysis.")
        elif not ensure_analysis_dependencies():
            st.stop()
        else:
            with st.spinner("Running batch analysis..."):
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
            st.download_button("Download CSV", batch_df.to_csv(index=False), f"batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)
        with dl2:
            if EXCEL_AVAILABLE:
                st.download_button("Download Excel", export_to_excel(batch_df), f"batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# =========================================================
# TAB 3
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
            "Search by topic, issue, state, recommendation, or compliance",
            placeholder="Enter search term...",
            key="history_search"
        )
        display_df = build_history_display_table(history_df)

        if search_term:
            filtered_df = display_df[
                display_df["Detected Topic"].astype(str).str.contains(search_term, case=False, na=False) |
                display_df["Specific Issue"].astype(str).str.contains(search_term, case=False, na=False) |
                display_df["Best Match"].astype(str).str.contains(search_term, case=False, na=False) |
                display_df["Recommendation"].astype(str).str.contains(search_term, case=False, na=False) |
                display_df["Compliance"].astype(str).str.contains(search_term, case=False, na=False)
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
                "CSV",
                csv,
                f"analysis_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True
            )

        with e2:
            if EXCEL_AVAILABLE:
                excel = export_to_excel(export_df)
                st.download_button(
                    "Excel",
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
                "JSON",
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
                "Report",
                summary,
                f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain",
                use_container_width=True
            )

        if st.button("Clear All History", use_container_width=True, key="clear_history_tab"):
            clear_history()
            st.success("History cleared successfully.")
            st.rerun()
    else:
        st.markdown("""
        <div class="msg-box msg-warning" style="text-align:center; padding:3rem;">
            <h3 style="margin-bottom:1rem;">No Analysis History</h3>
            <p class="small-note">Start by analyzing AI responses in the Single Analysis tab.</p>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# TAB 4  —  Fatwa Explorer
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

    topic_counts = (
        fatwa_df.groupby("issue")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    total_topics = topic_counts["issue"].nunique()
    total_fatwas = len(fatwa_df)
    total_states = fatwa_df["state"].nunique()

    st.markdown("<div style='height:0.35rem;'></div>", unsafe_allow_html=True)

    explorer_topics = ["All topics"] + sorted([t for t in fatwa_df["issue"].fillna("").astype(str).str.strip().unique().tolist() if t])
    explorer_states = ["All states / sources"] + sorted([s for s in fatwa_df["state"].fillna("").astype(str).str.strip().unique().tolist() if s])

    ex1, ex2, ex3 = st.columns([1, 1, 0.42], gap='medium')
    with ex1:
        st.markdown("<div class='browse-inline-head'>Choose a topic</div>", unsafe_allow_html=True)
        selected_topic_filter = st.selectbox(
            "Choose a topic",
            explorer_topics,
            key="fatwa_explorer_topic",
            label_visibility='collapsed'
        )
    with ex2:
        st.markdown("<div class='browse-inline-head'>Choose a state / source</div>", unsafe_allow_html=True)
        selected_state_filter = st.selectbox(
            "Choose a state / source",
            explorer_states,
            key="fatwa_explorer_state",
            label_visibility='collapsed'
        )
    with ex3:
        st.markdown("<div class='browse-inline-head'>Reset filters</div>", unsafe_allow_html=True)
        st.button("Show all", key="browse_reset_filters", use_container_width=True, on_click=reset_fatwa_explorer_filters)

    active_topic = selected_topic_filter if selected_topic_filter != 'All topics' else 'All topics'
    active_state = selected_state_filter if selected_state_filter != 'All states / sources' else 'All states / sources'
    st.markdown(f"<div class='browse-filter-chip-row'><span class='browse-filter-chip'>Topic: {html.escape(active_topic)}</span><span class='browse-filter-chip'>State / source: {html.escape(active_state)}</span></div>", unsafe_allow_html=True)

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
            <div class='explorer-orb-icon'>#</div>
            <div><div class='explorer-orb-label'>Records found</div><div class='explorer-orb-value'>{len(filtered_fatwa)}</div><div class='explorer-orb-note'>Official fatwa entries currently visible</div></div>
        </div>
        <div class='explorer-orb'>
            <div class='explorer-orb-icon'>T</div>
            <div><div class='explorer-orb-label'>Topics shown</div><div class='explorer-orb-value'>{result_topics}</div><div class='explorer-orb-note'>Distinct issue groups in the filtered list</div></div>
        </div>
        <div class='explorer-orb'>
            <div class='explorer-orb-icon'>S</div>
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
            <strong>No matching fatwa found.</strong><br>
            <span class="small-note">Choose another topic or state to continue browsing the reference database.</span>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# TAB 5  —  Topic Analysis
# =========================================================
with tab5:
    import html as html_escape_mod

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
            f"<div class='metric-card'><div class='metric-label'>Unique Topics</div>"
            f"<div class='metric-value'>{len(all_topics)}</div></div>",
            unsafe_allow_html=True
        )
    with sc2:
        st.markdown(
            f"<div class='metric-card'><div class='metric-label'>Total Fatwa Records</div>"
            f"<div class='metric-value'>{len(analysis_df)}</div></div>",
            unsafe_allow_html=True
        )
    with sc3:
        st.markdown(
            f"<div class='metric-card'><div class='metric-label'>States / Sources</div>"
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

    st.markdown("<h3 class='section-subtitle'>Fatwa Distribution by Category</h3>", unsafe_allow_html=True)
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

    st.markdown("<h3 class='section-subtitle'>AI Alignment Score by Topic</h3>", unsafe_allow_html=True)
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
            No analysis history found yet. Run some responses through
            <strong>Single Analysis</strong> or <strong>Batch Analysis</strong> first,
            then come back here to see topic-level alignment rankings.
        </div>
        """, unsafe_allow_html=True)
    else:
        valid_history_df = history_df.copy()
        valid_history_df["topic_label"] = valid_history_df["topic_label"].fillna("").astype(str).str.strip()
        valid_history_df = valid_history_df[valid_history_df["topic_label"] != ""]

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

        topic_scores["avg_score"] = topic_scores["avg_score"].round(1)
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
            st.markdown("<div class='align-panel-title'>Highest Alignment</div>", unsafe_allow_html=True)
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
            st.markdown("<div class='align-panel-title'>Lowest Alignment</div>", unsafe_allow_html=True)
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

        with st.expander("See full ranking for all topics"):
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

        st.markdown("<h3 class='section-subtitle'>Topic Difficulty Analysis</h3>", unsafe_allow_html=True)
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
        topic_perf["avg_score"] = topic_perf["avg_score"].round(1)
        topic_perf["short_label"] = topic_perf["topic_label"].apply(short_topic_label)

        hardest_topics = topic_perf.sort_values(["avg_score", "total_responses"], ascending=[True, False]).head(3)
        easiest_topics = topic_perf.sort_values(["avg_score", "total_responses"], ascending=[False, False]).head(3)

        dcol1, dcol2 = st.columns(2)

        with dcol1:
            st.markdown("<div class='align-panel-title'>Hardest Topics for AI</div>", unsafe_allow_html=True)
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
            st.markdown("<div class='align-panel-title'>Easiest Topics for AI</div>", unsafe_allow_html=True)
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

    st.markdown("<h3 class='section-subtitle'>Topic deep-dive</h3>", unsafe_allow_html=True)
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

        st.markdown(f"""
        <div class="msg-box msg-success">
            <strong>Topic:</strong> {html_escape_mod.escape(selected_topic)}<br>
            <strong>Fatwa Records:</strong> {len(selected_df)}&nbsp;&nbsp;
            <strong>States Covering:</strong> {len(covering_states)}&nbsp;&nbsp;
            <strong>States Missing:</strong> {len(missing_states)}
        </div>
        """, unsafe_allow_html=True)

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