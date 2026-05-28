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
# Priority order for the history file location:
#   1. FYP_HISTORY_FILE environment variable (set this in your shell or .env
#      to pin the path permanently, e.g.  export FYP_HISTORY_FILE=/home/you/project/analysis_history.json)
#   2. A path anchored to THIS file's own directory (same folder as utils.py)
#
# Using an env-var as the primary source means the path never changes even if
# Streamlit is launched from a different working directory, a virtualenv, or a
# hot-reload cycle resolves __file__ differently.
import sys as _sys

_env_path = os.environ.get("FYP_HISTORY_FILE", "").strip()
if _env_path:
    HISTORY_FILE = Path(_env_path).resolve()
else:
    HISTORY_FILE = Path(__file__).resolve().parent / "analysis_history.json"

# ── Candidate locations to check during startup recovery ─
# If Streamlit was ever launched from the CWD, a stale file may exist there too.
_HISTORY_CANDIDATES: list = [
    HISTORY_FILE,
    Path.cwd() / "analysis_history.json",
    Path.cwd().parent / "analysis_history.json",
]

print(
    f"[FYP Dashboard] History file → {HISTORY_FILE}",
    file=_sys.stderr,
    flush=True,
)

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

    Returns an empty list if the file does not exist or is corrupt —
    never raises.

    Schema migration: old records that used 'alignment_score' instead of
    'final_match_score' are transparently upgraded on read so the rest of
    the codebase never sees the old key.
    """
    path = _history_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        return [_migrate_history_record(r) for r in data]
    except Exception:
        return []


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

    Why atomic?  A plain write_text() call can be interrupted mid-write
    (Streamlit hot-reload, OS flush timing, unexpected crash), leaving a
    truncated or empty file.  Writing to a .tmp file first and then calling
    Path.replace() is atomic on all major OSes: the old file is never
    touched until the new content is fully written and flushed.

    If anything goes wrong the original file is left intact, so history
    is never silently lost.
    """
    path = _history_path()
    tmp  = path.with_suffix(".tmp")
    try:
        tmp.write_text(
            json.dumps(list(history), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(path)   # atomic rename — safe on Windows and POSIX
    except Exception:
        # Remove the partial temp file so it does not interfere next time
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass


def add_to_history(record: dict) -> None:
    """Append one analysis record to the on-disk history."""
    history = load_history_from_file()
    history.append(record)
    _save_history(history)


def merge_history_candidates() -> int:
    """
    Scan all known candidate paths, merge any records not already in the
    primary HISTORY_FILE, save back to HISTORY_FILE, and return how many
    new records were recovered.

    Call this ONCE at app startup (guarded by a session-state flag so it
    only runs on the very first load, not on every Streamlit rerun).

    Returns the number of newly merged records (0 if nothing was recovered).
    """
    primary = load_history_from_file()
    primary_ts = {r.get("timestamp", ""): True for r in primary}

    recovered: list = []
    for candidate in _HISTORY_CANDIDATES:
        try:
            if candidate.resolve() == HISTORY_FILE.resolve():
                continue                        # skip the primary file itself
        except Exception:
            continue
        if not candidate.exists():
            continue
        try:
            raw = json.loads(candidate.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                continue
            for rec in raw:
                ts = rec.get("timestamp", "")
                if ts and ts not in primary_ts:
                    recovered.append(_migrate_history_record(rec))
                    primary_ts[ts] = True       # prevent duplicates across candidates
            print(
                f"[FYP Dashboard] Recovery: found {len(raw)} records in {candidate}",
                file=_sys.stderr, flush=True,
            )
        except Exception:
            pass

    if recovered:
        merged = primary + recovered
        merged.sort(key=lambda r: r.get("timestamp", ""))
        _save_history(merged)
        print(
            f"[FYP Dashboard] Merged {len(recovered)} recovered record(s) into {HISTORY_FILE}",
            file=_sys.stderr, flush=True,
        )

    return len(recovered)


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