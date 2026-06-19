"""
metrics.py
─────────────────────────────────────────────────────────────────────────────
Evaluation metrics for the Multi-Modal Evidence Review pipeline.

Computes:
  • Exact-match accuracy for all categorical output fields
  • Per-class confusion detail for claim_status
  • Per-field miss analysis
  • Overall weighted score
"""
import pandas as pd
import os


CATEGORICAL_FIELDS = [
    "evidence_standard_met",
    "issue_type",
    "object_part",
    "claim_status",
    "valid_image",
    "severity",
]

# Weights for the composite score (reflects field importance)
FIELD_WEIGHTS = {
    "claim_status":           0.35,
    "issue_type":             0.20,
    "object_part":            0.20,
    "severity":               0.10,
    "evidence_standard_met":  0.10,
    "valid_image":            0.05,
}


def calculate_metrics(predicted_df: pd.DataFrame, ground_truth_df: pd.DataFrame) -> dict:
    metrics = {}

    merged = pd.merge(
        predicted_df, ground_truth_df,
        on=["user_id", "image_paths", "claim_object"],
        suffixes=("_pred", "_gt"),
    )
    total = len(merged)
    if total == 0:
        return {"error": "No matching rows found between predictions and ground truth."}

    metrics["total_evaluated"] = total

    per_field = {}
    for field in CATEGORICAL_FIELDS:
        pred_col = f"{field}_pred"
        gt_col   = f"{field}_gt"

        if field in ("evidence_standard_met", "valid_image"):
            p = merged[pred_col].astype(str).str.strip().str.lower().map(
                {"true": True, "1": True, "yes": True, "false": False, "0": False, "no": False}
            ).fillna(False)
            g = merged[gt_col].astype(str).str.strip().str.lower().map(
                {"true": True, "1": True, "yes": True, "false": False, "0": False, "no": False}
            ).fillna(False)
        else:
            p = merged[pred_col].astype(str).str.lower().str.strip()
            g = merged[gt_col].astype(str).str.lower().str.strip()

        correct = (p == g).sum()
        accuracy = correct / total
        metrics[field + "_accuracy"] = accuracy
        per_field[field] = {"correct": int(correct), "total": total,
                            "pred": p.tolist(), "gt": g.tolist(),
                            "user_ids": merged["user_id"].tolist()}

    # Composite weighted score
    composite = sum(
        FIELD_WEIGHTS.get(f, 0) * metrics[f + "_accuracy"]
        for f in CATEGORICAL_FIELDS
    )
    metrics["composite_weighted_score"] = composite
    metrics["_per_field_detail"] = per_field
    return metrics


def generate_report(metrics: dict, report_path: str):
    """Write a rich evaluation report in Markdown."""
    pf = metrics.pop("_per_field_detail", {})

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Evaluation Report — Multi-Modal Evidence Review\n\n")
        f.write("> Generated automatically by `code/evaluation/main.py`\n\n")

        if "error" in metrics:
            f.write(f"**Error**: {metrics['error']}\n")
            return

        total = metrics.get("total_evaluated", 0)
        composite = metrics.get("composite_weighted_score", 0)

        f.write("## Summary\n\n")
        f.write(f"| Metric | Value |\n|---|---|\n")
        f.write(f"| Total Evaluated | {total} |\n")
        f.write(f"| Composite Weighted Score | **{composite:.1%}** |\n\n")

        f.write("## Exact-Match Accuracy by Field\n\n")
        f.write("| Field | Accuracy | Correct/Total | Weight |\n")
        f.write("|---|---|---|---|\n")
        for field in CATEGORICAL_FIELDS:
            acc = metrics.get(field + "_accuracy", 0)
            detail = pf.get(field, {})
            c = detail.get("correct", 0)
            w = FIELD_WEIGHTS.get(field, 0)
            bar = "#" * int(acc * 20)
            f.write(f"| {field} | {acc:.1%} `{bar:<20}` | {c}/{total} | {w:.0%} |\n")

        f.write("\n## Per-Field Miss Analysis\n\n")
        for field in CATEGORICAL_FIELDS:
            detail = pf.get(field, {})
            preds   = detail.get("pred", [])
            gts     = detail.get("gt", [])
            uids    = detail.get("user_ids", [])
            misses  = [(uids[i], gts[i], preds[i])
                       for i in range(len(gts)) if gts[i] != preds[i]]
            if not misses:
                f.write(f"### {field} — All Correct\n\n")
                continue
            f.write(f"### {field} — {len(misses)} miss(es)\n\n")
            f.write("| user_id | ground_truth | predicted |\n|---|---|---|\n")
            for uid, gt, pr in misses:
                f.write(f"| {uid} | {gt} | {pr} |\n")
            f.write("\n")

        f.write("## claim_status Confusion Matrix\n\n")
        cs = pf.get("claim_status", {})
        if cs:
            labels = ["supported", "contradicted", "not_enough_information"]
            matrix = {r: {c: 0 for c in labels} for r in labels}
            for gt, pr in zip(cs.get("gt", []), cs.get("pred", [])):
                if gt in matrix and pr in matrix:
                    matrix[gt][pr] += 1
            header = "| GT \\ Pred | " + " | ".join(labels) + " |"
            sep    = "|---|" + "---|" * len(labels)
            f.write(header + "\n" + sep + "\n")
            for gt in labels:
                row = f"| **{gt}** | " + " | ".join(str(matrix[gt][pr]) for pr in labels) + " |"
                f.write(row + "\n")

        f.write("\n## System Architecture\n\n")
        f.write("| Component | Detail |\n|---|---|\n")
        f.write("| **Inference** | Deterministic engine (no API required) |\n")
        f.write("| **Claim parsing** | Priority-ordered keyword tables (multilingual) |\n")
        f.write("| **Prompt injection** | Regex-based detection, 14+ patterns |\n")
        f.write("| **User history** | Risk-flag override rules (history_flags field) |\n")
        f.write("| **Evidence check** | File-system validation (existence + size) |\n")
        f.write("| **Fallback** | Per-row deterministic fallback, pipeline never crashes |\n")
        f.write("| **VLM upgrade path** | Set GEMINI_API_KEY or OPENAI_API_KEY to enable |\n")
        f.write("\n## Limitations\n\n")
        f.write("- Without a vision model, `claim_status` is conservative: we cannot confirm "
                "damage is actually visible in the image, so borderline cases stay "
                "`not_enough_information`.\n")
        f.write("- `evidence_standard_met=false` ground-truth rows that still have accessible "
                "image files on disk cannot be distinguished from valid submissions without "
                "image inspection.\n")
        f.write("- Multilingual conversations (Hindi, Spanish, Chinese) are partially handled "
                "via specific keyword expansions; coverage is limited to seen patterns.\n")
