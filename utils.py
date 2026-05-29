import json
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import pandas as pd
import sys as _sys

# =========================================================
# HISTORY FILE LOCATION
# =========================================================
# IMPORTANT:
# A Streamlit app must read and write the SAME physical file every run.
# Your old screenshots show the classic failure: yesterday's file existed in
# one runtime/path, then today's app started from another runtime/path and saw
# an empty history.
#
# Priority:
#   1. FYP_HISTORY_FILE environment variable, if you set one.
#   2. analysis_history.json beside this utils.py file.
#
# For local work, keep analysis_history.json in the same folder as utils.py.
# For Streamlit Cloud, local files are NOT durable after the app restarts. Use
# an external database/storage if you need permanent multi-day persistence.
_env_path = os.environ.get("FYP_HISTORY_FILE", "").strip()
if _env_path:
    HISTORY_FILE = Path(_env_path).expanduser().resolve()
else:
    HISTORY_FILE = Path(__file__).resolve().parent / "analysis_history.json"


def _unique_paths(paths: Iterable[Path]) -> List[Path]:
    seen = set()
    out: List[Path] = []
    for p in paths:
        try:
            rp = p.expanduser().resolve()
        except Exception:
            rp = Path(p)
        key = str(rp)
        if key not in seen:
            seen.add(key)
            out.append(rp)
    return out


_HISTORY_CANDIDATES: List[Path] = _unique_paths([
    HISTORY_FILE,
    Path(__file__).resolve().parent / "analysis_history.json",
    Path.cwd() / "analysis_history.json",
    Path.cwd().parent / "analysis_history.json",
])

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

    Reads all known candidate paths and merges them. This fixes the common
    problem where yesterday's records were saved in ./analysis_history.json but
    today's Streamlit process reads project_folder/analysis_history.json.
    """
    all_records: List[dict] = []
    for candidate in _HISTORY_CANDIDATES:
        all_records.extend(_read_history_file(candidate))
    return _dedupe_history(all_records)


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


def _read_history_file(path: Path) -> List[dict]:
    """Read one history JSON file and return migrated records. Never raises."""
    try:
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return []
        return [_migrate_history_record(r) for r in raw if isinstance(r, dict)]
    except Exception as exc:
        print(
            f"[FYP Dashboard] Could not read history file {path}: {exc}",
            file=_sys.stderr,
            flush=True,
        )
        return []


def _record_identity(record: dict) -> Tuple[str, str]:
    """
    Stable identity for deduplication.

    Batch runs may include batch_key. Single runs usually do not, so timestamp
    is used. If neither exists, fall back to the meaningful fields.
    """
    if not isinstance(record, dict):
        return ("invalid", "")
    batch_key = normalize_text(record.get("batch_key", ""))
    if batch_key:
        return ("batch", batch_key)
    timestamp = normalize_text(record.get("timestamp", ""))
    if timestamp:
        return ("timestamp", timestamp)
    return (
        "content",
        "|".join([
            normalize_text(record.get("topic_label", "")),
            normalize_text(record.get("specific_issue", "")),
            normalize_text(record.get("best_state", "")),
            normalize_text(record.get("final_match_score", "")),
        ]),
    )


def _dedupe_history(records: Iterable[dict]) -> List[dict]:
    """
    Deduplicate records while keeping the newest version of repeated batch runs.
    """
    merged = {}
    order: List[Tuple[str, str]] = []
    for rec in records or []:
        if not isinstance(rec, dict):
            continue
        migrated = _migrate_history_record(rec)
        key = _record_identity(migrated)
        if key not in merged:
            order.append(key)
        merged[key] = migrated
    out = [merged[k] for k in order]
    out.sort(key=lambda r: normalize_text(r.get("timestamp", "")))
    return out


def _atomic_write_json(path: Path, records: Iterable[dict]) -> None:
    """Write JSON safely using tmp file, fsync, then atomic replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    payload = json.dumps(list(records), ensure_ascii=False, indent=2)
    with tmp.open("w", encoding="utf-8") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def _save_history(history: Iterable[dict]) -> None:
    """
    Persist history to disk.

    The primary file is HISTORY_FILE. A backup copy is also written to other
    candidate locations that are writable. This protects you from launching
    Streamlit from a different working directory later.
    """
    records = _dedupe_history(history)
    write_errors = []

    for path in _HISTORY_CANDIDATES:
        try:
            _atomic_write_json(path, records)
            print(
                f"[FYP Dashboard] Saved {len(records)} history record(s) to {path}",
                file=_sys.stderr,
                flush=True,
            )
        except Exception as exc:
            write_errors.append(f"{path}: {exc}")
            try:
                path.with_name(path.name + ".tmp").unlink(missing_ok=True)
            except Exception:
                pass

    if len(write_errors) == len(_HISTORY_CANDIDATES):
        raise RuntimeError("Could not save analysis history. " + " | ".join(write_errors))


def add_to_history(record: dict) -> None:
    """
    Append or update one analysis record, then persist it.

    If record has batch_key, an old record with the same batch_key is replaced
    instead of duplicated. Single-review records are appended by timestamp.
    """
    if not isinstance(record, dict):
        return

    history = load_history_from_file()
    new_record = _migrate_history_record(record)
    new_key = _record_identity(new_record)

    replaced = False
    updated: List[dict] = []
    for old in history:
        if _record_identity(old) == new_key:
            updated.append(new_record)
            replaced = True
        else:
            updated.append(old)
    if not replaced:
        updated.append(new_record)

    _save_history(updated)


def merge_history_candidates() -> int:
    """
    Merge records found in any candidate history file into the primary file.
    Returns how many records were recovered compared with the primary file.
    """
    primary_before = _read_history_file(HISTORY_FILE)
    primary_keys = {_record_identity(r) for r in primary_before}

    merged = load_history_from_file()
    recovered = [r for r in merged if _record_identity(r) not in primary_keys]

    if merged:
        _save_history(merged)

    if recovered:
        print(
            f"[FYP Dashboard] Recovered {len(recovered)} missing history record(s).",
            file=_sys.stderr,
            flush=True,
        )
    return len(recovered)


def get_history_debug_info() -> dict:
    """Return paths and record counts for troubleshooting in Streamlit."""
    return {
        "primary": str(HISTORY_FILE),
        "candidates": [
            {"path": str(p), "exists": p.exists(), "records": len(_read_history_file(p))}
            for p in _HISTORY_CANDIDATES
        ],
        "merged_records": len(load_history_from_file()),
    }


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