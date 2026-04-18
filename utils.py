import json
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Iterable, List

import pandas as pd

HISTORY_FILE = Path("analysis_history.json")

try:
    import openpyxl  # noqa: F401
    EXCEL_AVAILABLE = True
except Exception:
    EXCEL_AVAILABLE = False


def normalize_text(text) -> str:
    if text is None:
        return ""
    text = str(text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def safe_read_csv(path: str) -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
    last_error = None
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception as exc:
            last_error = exc
    raise last_error


def get_score_tier(score) -> str:
    try:
        score = float(score)
    except Exception:
        score = 0.0
    if score >= 70:
        return "good"
    if score >= 50:
        return "moderate"
    return "weak"


def get_score_css_class(value) -> str:
    tier = value if isinstance(value, str) else get_score_tier(value)
    mapping = {"good": "good", "moderate": "mid", "weak": "low"}
    return mapping.get(tier, "low")


def get_score_tier_colors(value):
    tier = value if isinstance(value, str) else get_score_tier(value)
    if tier == "good":
        return ("#06A77D", "#E6F7F1", "#06A77D")
    if tier == "moderate":
        return ("#F1A208", "#FFF4D9", "#C27D06")
    return ("#A31621", "#FBEAEC", "#A31621")


def get_score_color(score) -> str:
    return get_score_tier_colors(score)[2]


def get_score_band_label(score) -> str:
    tier = get_score_tier(score)
    if tier == "good":
        return "Good"
    if tier == "moderate":
        return "Moderate"
    return "Weak"


def format_percent(value, digits: int = 1) -> str:
    try:
        if pd.isna(value):
            return "-"
        return f"{float(value):.{digits}f}%"
    except Exception:
        return "-"


def _history_path() -> Path:
    return HISTORY_FILE



def load_history_from_file() -> List[dict]:
    path = _history_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_history(history: Iterable[dict]) -> None:
    path = _history_path()
    try:
        path.write_text(json.dumps(list(history), ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def add_to_history(record: dict) -> None:
    history = load_history_from_file()
    history.append(record)
    _save_history(history)


def clear_history() -> None:
    path = _history_path()
    if path.exists():
        try:
            path.unlink()
        except Exception:
            path.write_text("[]", encoding="utf-8")


def recent_topics_summary(history: List[dict], max_items: int = 4) -> List[str]:
    topics = []
    for row in reversed(history or []):
        topic = normalize_text(row.get("topic_label", ""))
        if topic and topic not in topics:
            topics.append(topic)
        if len(topics) >= max_items:
            break
    return topics


def build_light_table_html(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "<div class='small-note'>No data available.</div>"

    safe_df = df.fillna("-").copy()
    headers = "".join(f"<th>{_escape(col)}</th>" for col in safe_df.columns)
    body_rows = []
    for _, row in safe_df.iterrows():
        cells = []
        for col in safe_df.columns:
            value = _escape(row[col])
            cells.append(f"<td data-label='{_escape(col)}'><span class='light-table-cell'>{value}</span></td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    body = "".join(body_rows)
    return (
        "<div class='light-table-wrap'>"
        "<table class='light-table light-table-compact'>"
        f"<thead><tr>{headers}</tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table>"
        "</div>"
    )


def _escape(value) -> str:
    text = normalize_text(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def export_to_excel(df: pd.DataFrame) -> bytes:
    if not EXCEL_AVAILABLE:
        raise RuntimeError("Excel export is unavailable because openpyxl is not installed.")
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="analysis_history")
    output.seek(0)
    return output.getvalue()