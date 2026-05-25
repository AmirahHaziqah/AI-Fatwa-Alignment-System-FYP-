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
# IMPORTANT FIX:
# History must not depend only on the folder where Streamlit is launched.
# If the app is copied, renamed, or opened from a different working directory,
# a local-only history file can make old records appear to disappear.
#
# Default location:
#   ~/.fyp_fatwa_dashboard/analysis_history.json
#
# Optional override:
#   set FYP_HISTORY_FILE=/full/path/analysis_history.json
#
# The loader below also migrates/merges any old local analysis_history.json
# found beside this file, so existing records are not lost.
MODULE_DIR = Path(__file__).resolve().parent
LOCAL_HISTORY_FILE = MODULE_DIR / "analysis_history.json"
_HISTORY_ENV = os.environ.get("FYP_HISTORY_FILE", "").strip()
if _HISTORY_ENV:
    HISTORY_FILE = Path(_HISTORY_ENV).expanduser().resolve()
else:
    try:
        HISTORY_FILE = Path.home() / ".fyp_fatwa_dashboard" / "analysis_history.json"
    except Exception:
        HISTORY_FILE = LOCAL_HISTORY_FILE

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
    """Return the path used for stable on-disk history storage."""
    return HISTORY_FILE


def _read_json_list(path: Path) -> List[dict]:
    """Read a JSON list safely. Returns [] if the file is missing/corrupt."""
    try:
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        return [x for x in data if isinstance(x, dict)]
    except Exception:
        return []


def _record_key(record: dict) -> str:
    """Stable key used only to prevent accidental duplicate writes."""
    if not isinstance(record, dict):
        return ""
    return "|".join([
        normalize_text(record.get("timestamp", "")),
        normalize_text(record.get("topic_label", record.get("detected_question_id", ""))),
        normalize_text(record.get("best_state", "")),
        str(record.get("final_match_score", record.get("alignment_score", ""))),
        str(record.get("semantic_similarity", "")),
        str(record.get("coverage", "")),
    ])


def _merge_history_records(*groups: Iterable[dict]) -> List[dict]:
    """Merge history lists, migrate schemas, and avoid exact duplicate records."""
    merged: List[dict] = []
    seen = set()
    for group in groups:
        for raw in group or []:
            if not isinstance(raw, dict):
                continue
            rec = _migrate_history_record(raw)
            key = _record_key(rec)
            # Empty timestamp records are still kept, but exact full duplicates are skipped.
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            merged.append(rec)
    return merged


def _ensure_history_parent(path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _migrate_local_history_if_needed() -> None:
    """
    Merge the old local history file into the stable history file.

    This fixes the "I did 130+ analyses but only 120 appear after reopening"
    problem when the app is launched from another folder or renamed copy.
    """
    stable = _history_path()
    local = LOCAL_HISTORY_FILE
    if stable == local:
        return

    stable_records = _read_json_list(stable)
    local_records = _read_json_list(local)
    if not local_records:
        return

    merged = _merge_history_records(stable_records, local_records)
    if len(merged) > len(stable_records):
        _save_history(merged)


def load_history_from_file() -> List[dict]:
    """
    Load analysis history from disk.

    Returns an empty list if the file does not exist or is corrupt.
    Old records using 'alignment_score' are migrated to 'final_match_score'.
    The function also merges older local history into the stable history path.
    """
    _migrate_local_history_if_needed()
    data = _read_json_list(_history_path())
    return _merge_history_records(data)


def _migrate_history_record(record: dict) -> dict:
    """
    Upgrade a single history record from the old schema to the current one.
    Also keeps newer records complete and fills missing optional fields.
    """
    if not isinstance(record, dict):
        return record

    # New or partially-new schema.
    if "final_match_score" in record:
        out = dict(record)
        try:
            out["final_match_score"] = round(float(out.get("final_match_score", 0.0)), 2)
        except Exception:
            out["final_match_score"] = 0.0
        out.setdefault("timestamp", "")
        out.setdefault("topic_label", out.get("detected_question_id", "Unknown"))
        out.setdefault("specific_issue", "")
        out.setdefault("detection_confidence", "Unknown")
        out.setdefault("best_state", "")
        out.setdefault("mean_alignment", out.get("final_match_score", 0.0))
        out.setdefault("lexical_similarity", 0.0)
        out.setdefault("semantic_similarity", 0.0)
        out.setdefault("coverage", 0.0)
        out.setdefault("compliance_level", "Unknown")
        out.setdefault("compliance_reason", "")
        out.setdefault("recommendation_label", "")
        out.setdefault("recommendation_reason", "")
        return out

    # Old schema migration.
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
        "mean_alignment":       score,
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
    A backup copy is also written so records can be recovered if the main
    file is interrupted during a Streamlit rerun or shutdown.
    """
    path = _history_path()
    _ensure_history_parent(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    backup = path.with_suffix(path.suffix + ".bak")
    records = _merge_history_records(history)
    payload = json.dumps(records, ensure_ascii=False, indent=2)

    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        if path.exists():
            try:
                backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass
        tmp.replace(path)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        # Last-resort fallback to the local file beside the app.
        fallback = LOCAL_HISTORY_FILE
        try:
            fallback.write_text(payload, encoding="utf-8")
        except Exception:
            pass


def add_to_history(record: dict) -> List[dict]:
    """
    Append one analysis record to the on-disk history and return fresh history.

    Returning the fresh list lets the Streamlit UI update the total and average
    immediately after a run instead of waiting for a manual refresh.
    """
    current = load_history_from_file()
    updated = _merge_history_records(current, [record])
    _save_history(updated)
    return load_history_from_file()


def clear_history() -> None:
    """Delete the on-disk history file and its backup if possible."""
    for path in {_history_path(), LOCAL_HISTORY_FILE, _history_path().with_suffix(_history_path().suffix + ".bak")}:
        try:
            if path.exists():
                path.unlink()
        except Exception:
            try:
                path.write_text("[]", encoding="utf-8")
            except Exception:
                pass


def history_file_location() -> str:
    """Expose the active history path for debugging inside the dashboard."""
    return str(_history_path())


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