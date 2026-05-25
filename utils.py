# =========================================================
# utils.py  —  Shared helpers for the FYP Dashboard
# =========================================================
# All functions here are pure helpers: no Streamlit calls,
# no side-effects.  Keep imports minimal so this module loads
# fast in every context.
# =========================================================

import json
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd

# ── Where analysis history is persisted on disk ──────────
# PRIMARY store  : analysis_history.json   (full fidelity, next to this file)
# BACKUP  store  : analysis_history_persistent.csv  (same folder)
#
# On every save BOTH files are written.
# On every load, BOTH files are read and merged by timestamp so that
# records are never silently lost even if one file is missing, empty,
# or out of date (e.g. after a re-deploy that copies only .py files).
#
# IMPORTANT: Paths are anchored to this module's own directory so they
# resolve correctly regardless of the working directory Streamlit uses.
_BASE_DIR    = Path(__file__).resolve().parent
HISTORY_FILE = _BASE_DIR / "analysis_history.json"
_CSV_BACKUP  = _BASE_DIR / "analysis_history_persistent.csv"

# Columns that must be present in the CSV backup (in this order)
_CSV_COLUMNS = [
    "timestamp", "topic_label", "specific_issue", "detection_confidence",
    "best_state", "final_match_score", "mean_alignment",
    "lexical_similarity", "semantic_similarity", "coverage",
    "compliance_level", "compliance_reason",
    "recommendation_label", "recommendation_reason",
]

# ── Optional Excel export (needs openpyxl installed) ─────
try:
    import openpyxl  # noqa: F401
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


# =========================================================
# TEXT UTILITIES
# =========================================================

def normalize_text(text) -> str:
    """
    Return a clean, single-line string from any input.

    - Converts None / non-string values to ''
    - Strips non-breaking spaces (U+00A0)
    - Removes HTML tags
    - Collapses consecutive whitespace
    """
    if text is None:
        return ""
    text = str(text)
    text = text.replace("\u00a0", " ")          # non-breaking space → regular space
    text = re.sub(r"<[^>]+>", " ", text)        # strip HTML tags
    text = re.sub(r"\s+", " ", text)            # collapse whitespace
    return text.strip()


def _escape(value) -> str:
    """HTML-escape a value after normalising it to a string."""
    text = normalize_text(value)
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


# =========================================================
# FILE I/O
# =========================================================

def safe_read_csv(path: str) -> pd.DataFrame:
    """
    Read a CSV file, trying multiple encodings so that files
    saved by Excel (cp1252, latin1) are also handled gracefully.

    Raises the last exception if all encodings fail.
    """
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
    last_error: Optional[Exception] = None
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception as exc:
            last_error = exc
    raise last_error  # type: ignore[misc]


# =========================================================
# SCORE TIER LOGIC
# =========================================================
# Thresholds (consistent across ALL files):
#   High Alignment     ≥ 70 %   → "good"     (green)
#   Moderate Alignment ≥ 50 %   → "moderate" (yellow)
#   Low Alignment       < 50 %  → "weak"     (red)
#
# NOTE: The score is rounded to the nearest integer before
# comparison so that the displayed circle value (which is
# already rounded) stays consistent with the tier label —
# e.g. 69.7 rounds to 70 = High Alignment.
# =========================================================

def get_score_tier(score) -> str:
    """
    Return 'good', 'moderate', or 'weak' for a numeric score.

    Thresholds (after rounding):
        good     (High Alignment)      >= 70
        moderate (Moderate Alignment)  >= 50
        weak     (Low Alignment)        < 50
    """
    try:
        score = round(float(score))
    except Exception:
        score = 0

    if score >= 70:
        return "good"
    if score >= 50:
        return "moderate"
    return "weak"


def get_score_css_class(value) -> str:
    """
    Map a score (float) or tier string to its CSS utility class.
    Returns one of: 'good', 'mid', 'low'.
    """
    tier = value if isinstance(value, str) else get_score_tier(value)
    return {"good": "good", "moderate": "mid", "weak": "low"}.get(tier, "low")


def get_score_tier_colors(value) -> tuple:
    """
    Return a (fill_color, bg_color, text_color) triple for a score tier.

    Usage:
        fill, bg, text = get_score_tier_colors(72.5)
    """
    tier = value if isinstance(value, str) else get_score_tier(value)
    if tier == "good":
        return ("#06A77D", "#E6F7F1", "#06A77D")
    if tier == "moderate":
        return ("#F1A208", "#FFF4D9", "#C27D06")
    return ("#A31621", "#FBEAEC", "#A31621")


def get_score_color(score) -> str:
    """Return the text colour for a given score (uses tier mapping)."""
    return get_score_tier_colors(score)[2]


def get_score_band_label(score) -> str:
    """Return a human-friendly tier label: 'High Alignment', 'Moderate Alignment', or 'Low Alignment'."""
    tier = get_score_tier(score)
    return {"good": "High Alignment", "moderate": "Moderate Alignment", "weak": "Low Alignment"}.get(tier, "Low Alignment")


# =========================================================
# FORMATTING HELPERS
# =========================================================

def format_percent(value, digits: int = 1) -> str:
    """
    Format a float as a percentage string.

    Returns '-' for NaN or non-numeric values.

    Examples:
        format_percent(72.456)   → '72.5%'
        format_percent(None)     → '-'
    """
    try:
        if pd.isna(value):
            return "-"
        return f"{float(value):.{digits}f}%"
    except Exception:
        return "-"


# =========================================================
# HISTORY — PERSISTENCE
# =========================================================

def _history_path() -> Path:
    """Return the path used for on-disk history storage."""
    return HISTORY_FILE


def load_history_from_file() -> List[dict]:
    """
    Load analysis history from disk.

    Reads BOTH the JSON primary store and the CSV backup, merges them
    by timestamp (deduplicating), and returns a single unified list
    sorted oldest to newest.

    This means history is never lost even if one of the two files is
    missing, empty, or out of date after a re-deploy.

    Schema migration: old records that used 'alignment_score' instead of
    'final_match_score' are transparently upgraded on read.
    """
    records_by_ts: dict = {}

    # 1. Load JSON primary
    json_path = _history_path()
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for r in data:
                    r = _migrate_history_record(r)
                    ts = r.get("timestamp", "")
                    if ts:
                        records_by_ts[ts] = r
        except Exception:
            pass

    # 2. Load CSV backup — adds any records missing from the JSON
    if _CSV_BACKUP.exists():
        try:
            df = pd.read_csv(_CSV_BACKUP, encoding="utf-8")
            for _, row in df.iterrows():
                r = _migrate_history_record(row.to_dict())
                ts = r.get("timestamp", "")
                if ts and ts not in records_by_ts:
                    records_by_ts[ts] = r
        except Exception:
            pass

    if not records_by_ts:
        return []

    # Sort ascending by timestamp (oldest first)
    try:
        merged = sorted(records_by_ts.values(), key=lambda x: x.get("timestamp", ""))
    except Exception:
        merged = list(records_by_ts.values())

    return merged


def _migrate_history_record(record: dict) -> dict:
    """
    Upgrade a single history record from the old schema to the current one.

    Old schema (pre-April 2026) used 'alignment_score' as the primary score
    key and did not include topic_label, compliance_level, or recommendation.
    This function normalises those records so the rest of the codebase can
    treat all history entries identically.
    """
    if not isinstance(record, dict):
        return record

    # Already new schema — nothing to do
    if "final_match_score" in record:
        return record

    # Old schema migration
    raw_score = record.get("alignment_score", 0.0)
    try:
        score = round(float(raw_score), 2)
    except Exception:
        score = 0.0

    return {
        "timestamp":            record.get("timestamp", ""),
        "topic_label":          record.get("detected_question_id", "Unknown"),
        "specific_issue":       "",
        "detection_confidence": "Unknown",
        "best_state":           record.get("best_state", ""),
        "final_match_score":    score,
        "mean_alignment":       score,   # no multi-state mean was stored; best is the only value
        "lexical_similarity":   round(float(record.get("lexical_similarity",  0.0)), 2),
        "semantic_similarity":  round(float(record.get("semantic_similarity", 0.0)), 2),
        "coverage":             round(float(record.get("coverage",            0.0)), 2),
        "compliance_level":     "Unknown",
        "compliance_reason":    "Migrated from old schema — compliance not recorded.",
        "recommendation_label": "",
        "recommendation_reason": "",
    }


def _save_history(history: Iterable[dict]) -> None:
    """
    Persist history to disk using an atomic write-then-rename pattern.

    Writes BOTH:
      - analysis_history.json        (primary, full fidelity)
      - analysis_history_persistent.csv  (backup, survives re-deploys)

    The atomic write-then-rename pattern means the original file is never
    touched until the new content is fully written, so history is never
    silently truncated or lost on hot-reload / unexpected crash.
    """
    history_list = list(history)

    # ── 1. JSON primary (atomic) ──────────────────────────
    path = _history_path()
    tmp  = path.with_suffix(".tmp")
    try:
        tmp.write_text(
            json.dumps(history_list, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(path)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass

    # ── 2. CSV backup ─────────────────────────────────────
    try:
        rows = []
        for r in history_list:
            row = {col: r.get(col, "") for col in _CSV_COLUMNS}
            rows.append(row)
        df = pd.DataFrame(rows, columns=_CSV_COLUMNS)
        csv_tmp = _CSV_BACKUP.with_suffix(".tmp")
        df.to_csv(csv_tmp, index=False, encoding="utf-8")
        csv_tmp.replace(_CSV_BACKUP)
    except Exception:
        try:
            csv_tmp.unlink(missing_ok=True)  # type: ignore[possibly-undefined]
        except Exception:
            pass


def add_to_history(record: dict) -> None:
    """Append one analysis record to the on-disk history."""
    history = load_history_from_file()
    history.append(record)
    _save_history(history)


def clear_history() -> None:
    """Delete the on-disk history file (or empty it if deletion fails)."""
    path = _history_path()
    if not path.exists():
        return
    try:
        path.unlink()
    except Exception:
        # Fall back to emptying the file instead of deleting
        try:
            path.write_text("[]", encoding="utf-8")
        except Exception:
            pass


# =========================================================
# HISTORY — DISPLAY HELPERS
# =========================================================

def recent_topics_summary(history: List[dict], max_items: int = 4) -> List[str]:
    """
    Return the most-recent unique topic labels from a history list.

    Iterates from newest to oldest so that the first item is always
    the most recent topic the user analysed.
    """
    topics: List[str] = []
    for row in reversed(history or []):
        topic = normalize_text(row.get("topic_label", ""))
        if topic and topic not in topics:
            topics.append(topic)
        if len(topics) >= max_items:
            break
    return topics


# =========================================================
# HTML TABLE BUILDER
# =========================================================

def build_light_table_html(df: pd.DataFrame) -> str:
    """
    Build a styled HTML table from a DataFrame.

    - Missing values are replaced with '-' so the table always renders
    - Column headers and cell values are HTML-escaped
    - Adds a data-label attribute to each cell for mobile CSS tricks
    """
    if df is None or df.empty:
        return "<div class='small-note'>No data available.</div>"

    # Replace NaN with '-' to avoid displaying 'nan' in cells
    safe_df = df.fillna("-").copy()

    headers = "".join(
        f"<th>{_escape(col)}</th>" for col in safe_df.columns
    )

    body_rows = []
    for _, row in safe_df.iterrows():
        cells = "".join(
            f"<td data-label='{_escape(col)}'>"
            f"<span class='light-table-cell'>{_escape(row[col])}</span>"
            f"</td>"
            for col in safe_df.columns
        )
        body_rows.append(f"<tr>{cells}</tr>")

    return (
        "<div class='light-table-wrap'>"
        "<table class='light-table light-table-compact'>"
        f"<thead><tr>{headers}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
        "</div>"
    )


# =========================================================
# EXCEL EXPORT
# =========================================================

def export_to_excel(df: pd.DataFrame) -> bytes:
    """
    Serialise a DataFrame to an in-memory Excel (.xlsx) file.

    Raises RuntimeError if openpyxl is not installed.
    """
    if not EXCEL_AVAILABLE:
        raise RuntimeError(
            "Excel export is unavailable because 'openpyxl' is not installed. "
            "Run:  pip install openpyxl"
        )
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="analysis_history")
    output.seek(0)
    return output.getvalue()