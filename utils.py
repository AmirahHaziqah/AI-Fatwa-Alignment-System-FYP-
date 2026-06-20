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
# FATWA SOURCE LABELS
# =========================================================
# Maps long-form fatwa source / state names found in the raw dataset to
# shorter, clearer labels for display on the dashboard.
#
# Added in response to expert validation feedback (Section 4.4.2): the
# second evaluator, Noor Munirah binti Isa (Senior Lecturer, Bioethics),
# suggested that the national-level fatwa body be referenced using the
# short name "Fatwa Jawatankuasa Muzakarah MKI" for clearer attribution.
# Reference: https://i-fiqh.islam.gov.my
# =========================================================

FATWA_SOURCE_SHORT_NAMES = {
    "muzakarah majlis kebangsaan": "Fatwa Jawatankuasa Muzakarah MKI",
    "majlis kebangsaan": "Fatwa Jawatankuasa Muzakarah MKI",
    "jawatankuasa muzakarah majlis kebangsaan": "Fatwa Jawatankuasa Muzakarah MKI",
    "jawatankuasa fatwa majlis kebangsaan": "Fatwa Jawatankuasa Muzakarah MKI",
    "majlis kebangsaan bagi hal ehwal ugama islam malaysia": "Fatwa Jawatankuasa Muzakarah MKI",
}


def format_state_label(value) -> str:
    """
    Return a shortened, display-friendly fatwa source name.

    Looks up the cleaned/lower-cased value against FATWA_SOURCE_SHORT_NAMES.
    Falls back to the original (normalised) value when no short name is
    defined, so unmapped state names are shown exactly as in the dataset.
    """
    text = normalize_text(value)
    if not text:
        return text
    key = re.sub(r"\s+", " ", text).strip().lower()
    return FATWA_SOURCE_SHORT_NAMES.get(key, text)


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

_HISTORY_ROW_ID = "default"
_DEFAULT_SUPABASE_TABLE = "analysis_history_store"


def _history_path() -> Path:
    """Return the primary local history path."""
    return HISTORY_FILE


def _secret_value(*names: str) -> str:
    """
    Read a setting from environment variables or Streamlit secrets.

    This function is intentionally defensive: missing secrets must not crash
    local development. If no secret is found, an empty string is returned.
    """
    for name in names:
        value = os.environ.get(name, "")
        if str(value).strip():
            return str(value).strip()

    try:
        import streamlit as _st  # imported lazily so utils.py stays usable in scripts

        for name in names:
            try:
                value = _st.secrets.get(name, "")
                if str(value).strip():
                    return str(value).strip()
            except Exception:
                pass

        try:
            supabase = _st.secrets.get("supabase", {})
            lowered = {str(k).lower(): v for k, v in dict(supabase).items()}
            for name in names:
                short_name = name.lower().replace("supabase_", "")
                value = lowered.get(short_name, "")
                if str(value).strip():
                    return str(value).strip()
        except Exception:
            pass
    except Exception:
        pass

    return ""


def _supabase_config() -> dict:
    """Return Supabase configuration, if available."""
    url = _secret_value("SUPABASE_URL", "supabase_url").rstrip("/")
    key = _secret_value(
        "SUPABASE_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_ANON_KEY",
        "supabase_key",
        "supabase_service_role_key",
        "supabase_anon_key",
    )
    table = _secret_value("SUPABASE_HISTORY_TABLE", "supabase_history_table") or _DEFAULT_SUPABASE_TABLE
    return {
        "enabled": bool(url and key),
        "url": url,
        "key": key,
        "table": table,
    }


def history_backend_name() -> str:
    """Return the active history backend name for debugging."""
    return "supabase" if _supabase_config()["enabled"] else "local_json"


def _supabase_headers(prefer: str = "") -> dict:
    cfg = _supabase_config()
    headers = {
        "apikey": cfg["key"],
        "Authorization": f"Bearer {cfg['key']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _supabase_request(method: str, endpoint: str, payload=None, prefer: str = ""):
    """Minimal Supabase REST request using only the Python standard library."""
    from urllib import request, error

    cfg = _supabase_config()
    if not cfg["enabled"]:
        raise RuntimeError("Supabase is not configured.")

    url = f"{cfg['url']}/rest/v1/{endpoint}"
    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = request.Request(
        url,
        data=body,
        method=method.upper(),
        headers=_supabase_headers(prefer=prefer),
    )

    try:
        with request.urlopen(req, timeout=12) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)
    except error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            pass
        raise RuntimeError(f"Supabase {method} failed with HTTP {exc.code}: {detail}") from exc


def _read_supabase_history() -> tuple:
    """
    Return (enabled, ok, row_exists, records).

    row_exists matters. If Supabase has an explicit empty row, that empty row is
    the source of truth and old local JSON must not be merged back in after a
    cloud redeploy.
    """
    cfg = _supabase_config()
    if not cfg["enabled"]:
        return False, False, False, []

    try:
        table = cfg["table"]
        endpoint = f"{table}?id=eq.{_HISTORY_ROW_ID}&select=history"
        data = _supabase_request("GET", endpoint)
        if not isinstance(data, list) or len(data) == 0:
            return True, True, False, []

        history = data[0].get("history", [])
        if not isinstance(history, list):
            history = []
        return True, True, True, [_migrate_history_record(r) for r in history if isinstance(r, dict)]
    except Exception as exc:
        print(
            f"[FYP Dashboard] Could not read Supabase history: {exc}",
            file=_sys.stderr,
            flush=True,
        )
        return True, False, False, []


def _write_supabase_history(records: Iterable[dict]) -> bool:
    """Write the complete history list to Supabase. Returns True on success."""
    cfg = _supabase_config()
    if not cfg["enabled"]:
        return False

    try:
        table = cfg["table"]
        payload = {
            "id": _HISTORY_ROW_ID,
            "history": _dedupe_history(records),
            "updated_at": pd.Timestamp.utcnow().isoformat(),
        }
        _supabase_request(
            "POST",
            f"{table}?on_conflict=id",
            payload=payload,
            prefer="resolution=merge-duplicates,return=minimal",
        )
        print(
            f"[FYP Dashboard] Saved {len(payload['history'])} history record(s) to Supabase table {table}",
            file=_sys.stderr,
            flush=True,
        )
        return True
    except Exception as exc:
        print(
            f"[FYP Dashboard] Could not save Supabase history: {exc}",
            file=_sys.stderr,
            flush=True,
        )
        return False


def _read_history_file(path: Path) -> List[dict]:
    """Read one local history JSON file and return migrated records. Never raises."""
    try:
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return []
        return [_migrate_history_record(r) for r in raw if isinstance(r, dict)]
    except Exception as exc:
        print(
            f"[FYP Dashboard] Could not read local history file {path}: {exc}",
            file=_sys.stderr,
            flush=True,
        )
        return []


def _read_local_history() -> List[dict]:
    all_records: List[dict] = []
    for candidate in _HISTORY_CANDIDATES:
        all_records.extend(_read_history_file(candidate))
    return _dedupe_history(all_records)


def load_history_from_file() -> List[dict]:
    """
    Load analysis history from persistent storage.

    Supabase mode:
        If the Supabase row exists, Supabase is treated as the source of truth.
        This prevents old committed analysis_history.json files from reappearing
        after redeploy or after clearing history.

    Local mode:
        Reads and merges all known candidate JSON files to prevent path mismatch.
    """
    enabled, ok, row_exists, remote_records = _read_supabase_history()
    if enabled and ok and row_exists:
        return _dedupe_history(remote_records)

    local_records = _read_local_history()

    # First-time Supabase setup: if the row does not exist yet, allow migration
    # from the local JSON file. The startup merge function will write it back.
    if enabled and ok and not row_exists:
        return _dedupe_history(local_records + remote_records)

    # Supabase configured but temporarily unavailable: fall back to local JSON
    # so the app still opens instead of losing the UI.
    return local_records


def _migrate_history_record(record: dict) -> dict:
    """
    Upgrade a single history record from the old schema to the current one.
    """
    if not isinstance(record, dict):
        return record

    if "final_match_score" in record:
        return record

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


def _record_identity(record: dict) -> Tuple[str, str]:
    """
    Stable identity for deduplication.

    Batch records use batch_key so rerunning a batch updates the same question
    and model slot instead of inflating the run count. Single reviews use
    record_id when available, then timestamp for older saved records.
    """
    if not isinstance(record, dict):
        return ("invalid", "")

    batch_key = normalize_text(record.get("batch_key", ""))
    if batch_key:
        return ("batch", batch_key)

    record_id = normalize_text(record.get("record_id", ""))
    if record_id:
        return ("record", record_id)

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
    """Deduplicate records and sort by timestamp ascending."""
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
    """Write JSON safely using a tmp file, fsync, then atomic replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    payload = json.dumps(list(records), ensure_ascii=False, indent=2)
    with tmp.open("w", encoding="utf-8") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def _write_local_history(records: Iterable[dict]) -> bool:
    """Write history to every known local candidate path."""
    records = _dedupe_history(records)
    ok_count = 0
    for path in _HISTORY_CANDIDATES:
        try:
            _atomic_write_json(path, records)
            ok_count += 1
            print(
                f"[FYP Dashboard] Saved {len(records)} history record(s) to {path}",
                file=_sys.stderr,
                flush=True,
            )
        except Exception as exc:
            print(
                f"[FYP Dashboard] Could not save local history {path}: {exc}",
                file=_sys.stderr,
                flush=True,
            )
            try:
                path.with_name(path.name + ".tmp").unlink(missing_ok=True)
            except Exception:
                pass
    return ok_count > 0


def _save_history(history: Iterable[dict]) -> List[dict]:
    """Persist history to active storage and local fallback, then return records."""
    records = _dedupe_history(history)

    remote_ok = _write_supabase_history(records)
    local_ok = _write_local_history(records)

    if not remote_ok and not local_ok:
        raise RuntimeError("Could not save analysis history to Supabase or local JSON.")

    return records


def add_to_history(record: dict) -> List[dict]:
    """
    Append or update one analysis record, persist it, and return fresh history.

    Returning the updated list lets Streamlit update Saved Runs and Average
    immediately after analysis without waiting for a browser refresh.
    """
    if not isinstance(record, dict):
        return load_history_from_file()

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
    return load_history_from_file()


def merge_history_candidates() -> int:
    """
    Merge recovered local records into persistent storage at startup.

    If Supabase already has a row, Supabase remains the source of truth and old
    committed local JSON is not merged back in. If the Supabase row does not
    exist yet, local history is migrated into Supabase automatically.
    """
    enabled, ok, row_exists, remote_records = _read_supabase_history()
    local_records = _read_local_history()

    if enabled and ok and row_exists:
        # Remote source of truth. Keep the local cache aligned with remote.
        _write_local_history(remote_records)
        return 0

    merged = _dedupe_history(remote_records + local_records)
    if merged:
        _save_history(merged)

    before_keys = {_record_identity(r) for r in remote_records}
    recovered = [r for r in merged if _record_identity(r) not in before_keys]
    return len(recovered)


def get_history_debug_info() -> dict:
    """Return storage paths, backend status, and record counts for debugging."""
    enabled, ok, row_exists, remote_records = _read_supabase_history()
    return {
        "backend": history_backend_name(),
        "supabase_enabled": enabled,
        "supabase_ok": ok,
        "supabase_row_exists": row_exists,
        "supabase_records": len(_dedupe_history(remote_records)),
        "primary_local_path": str(HISTORY_FILE),
        "local_candidates": [
            {"path": str(p), "exists": p.exists(), "records": len(_read_history_file(p))}
            for p in _HISTORY_CANDIDATES
        ],
        "loaded_records": len(load_history_from_file()),
    }


def clear_history() -> List[dict]:
    """
    Clear saved history from Supabase and every local candidate file.

    A local backup is written first. The backup filename is not included in
    _HISTORY_CANDIDATES, so it will not be automatically reloaded.
    """
    existing_records = load_history_from_file()

    if existing_records:
        try:
            backup_path = HISTORY_FILE.with_name(
                f"analysis_history_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            _atomic_write_json(backup_path, existing_records)
            print(
                f"[FYP Dashboard] History backup written to {backup_path}",
                file=_sys.stderr,
                flush=True,
            )
        except Exception as exc:
            print(
                f"[FYP Dashboard] Could not create history backup: {exc}",
                file=_sys.stderr,
                flush=True,
            )

    # Empty remote first. If Supabase row exists with [], future cloud redeploys
    # will not resurrect a committed analysis_history.json file.
    _write_supabase_history([])

    for path in _HISTORY_CANDIDATES:
        try:
            _atomic_write_json(path, [])
        except Exception:
            try:
                path.write_text("[]", encoding="utf-8")
            except Exception:
                pass

    return []


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