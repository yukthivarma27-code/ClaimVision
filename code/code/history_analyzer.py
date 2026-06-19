import pandas as pd
from typing import Dict, List, Tuple

from . import utils

HISTORY_CACHE = None

def _load_history() -> pd.DataFrame:
    global HISTORY_CACHE
    if HISTORY_CACHE is not None:
        return HISTORY_CACHE
    path = utils.DATASET_DIR / "user_history.csv"
    HISTORY_CACHE = pd.read_csv(path)
    return HISTORY_CACHE

def analyze_history(user_id: str) -> Tuple[List[str], str]:
    df = _load_history()
    row = df[df["user_id"] == user_id]
    if row.empty:
        return ["none"], "No user history found."

    row = row.iloc[0]
    flags = []
    history_flags_raw = str(row.get("history_flags", "none"))
    if history_flags_raw and history_flags_raw.lower() != "none":
        for f in history_flags_raw.split(";"):
            f = f.strip()
            if f and f.lower() != "none":
                flags.append(f)

    past_count = int(row.get("past_claim_count", 0))
    reject_count = int(row.get("rejected_claim", 0))
    manual_count = int(row.get("manual_review_claim", 0))
    recent_count = int(row.get("last_90_days_claim_count", 0))

    if reject_count >= 3 or (reject_count / max(past_count, 1)) >= 0.4:
        if "user_history_risk" not in flags:
            flags.append("user_history_risk")
    if manual_count >= 2:
        if "manual_review_required" not in flags:
            flags.append("manual_review_required")
    if recent_count >= 4:
        if "user_history_risk" not in flags:
            flags.append("user_history_risk")
    if recent_count >= 6:
        if "manual_review_required" not in flags:
            flags.append("manual_review_required")

    summary = str(row.get("history_summary", "No summary available."))
    if not flags:
        flags = ["none"]

    return flags, summary
