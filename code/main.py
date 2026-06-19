"""
main.py — CLI entry point for the Multi-Modal Evidence Review pipeline.

Usage
-----
    py code/main.py                          # runs on claims.csv → outputs.csv
    py code/main.py --input claims.csv --output outputs.csv
    py code/main.py --input sample_claims.csv --output outputs.csv

Logging
-------
    Set LOG_LEVEL env var to DEBUG/INFO/WARNING/ERROR (default: INFO).
"""
import os
import sys
import logging
import argparse
import pandas as pd

# ── Path bootstrap ────────────────────────────────────────────────────────────
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from code.config import (
    ROOT_DIR as CFG_ROOT, REQUIRED_COLUMNS, CLAIM_STATUS_CHOICES,
    ISSUE_TYPE_CHOICES, SEVERITY_CHOICES, RISK_FLAGS_CHOICES,
    OBJECT_PART_CAR_CHOICES, OBJECT_PART_LAPTOP_CHOICES, OBJECT_PART_PACKAGE_CHOICES
)
from code.data_loader import load_data, get_requirements_for_object
from code.pipeline import process_single_claim

# ── Logging setup ─────────────────────────────────────────────────────────────
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


def validate_output_dataframe(df: pd.DataFrame, expected_count: int):
    """
    Strict validation of output data before saving to CSV.
    """
    assert len(df) == expected_count, f"Validation failed: expected {expected_count} rows, got {len(df)}"
    assert list(df.columns) == REQUIRED_COLUMNS, "Validation failed: column mismatch or incorrect order"
    
    allowed_parts = set(OBJECT_PART_CAR_CHOICES + OBJECT_PART_LAPTOP_CHOICES + OBJECT_PART_PACKAGE_CHOICES)

    for i, row in df.iterrows():
        # Blanks
        for col in REQUIRED_COLUMNS:
            assert pd.notna(row[col]), f"Row {i} has blank value in {col}"

        # Booleans
        assert isinstance(row["evidence_standard_met"], bool) or str(row["evidence_standard_met"]).lower() in ["true", "false"], f"Row {i} evidence_standard_met is not boolean"
        assert isinstance(row["valid_image"], bool) or str(row["valid_image"]).lower() in ["true", "false"], f"Row {i} valid_image is not boolean"

        # Categoricals
        assert row["claim_status"] in CLAIM_STATUS_CHOICES, f"Row {i} invalid claim_status: {row['claim_status']}"
        assert row["issue_type"] in ISSUE_TYPE_CHOICES, f"Row {i} invalid issue_type: {row['issue_type']}"
        assert row["severity"] in SEVERITY_CHOICES, f"Row {i} invalid severity: {row['severity']}"
        assert row["object_part"] in allowed_parts, f"Row {i} invalid object_part: {row['object_part']}"

        # Semicolon separated
        flags = str(row["risk_flags"])
        if flags != "none":
            for f in flags.split(";"):
                assert f.strip() in RISK_FLAGS_CHOICES, f"Row {i} invalid risk_flag: {f}"

        images = str(row["supporting_image_ids"])
        if images != "none":
            for img in images.split(";"):
                assert img.strip() != "", f"Row {i} empty image ID in list"

    logger.info("Validation passed: Schema and values are strictly valid.")

def run_prediction(input_file: str = "claims.csv", output_file: str = "output.csv"):
    """
    Load data, process every claim through the pipeline, and write outputs.csv.
    Preserves row order from claims.csv.
    """
    logger.info("Loading data from %s …", input_file)
    merged_df, req_df = load_data(input_file)
    n = len(merged_df)
    logger.info("Loaded %d claims. Starting pipeline …", n)

    results = []
    errors = 0

    for i, (idx, row) in enumerate(merged_df.iterrows(), start=1):
        logger.info("Processing %d/%d  user=%s", i, n, row["user_id"])
        try:
            claim_object = row["claim_object"]
            obj_req = get_requirements_for_object(req_df, claim_object)
            processed_row = process_single_claim(row, obj_req, CFG_ROOT)
            # Keep only required columns in exact order
            final_row = {col: processed_row.get(col, None) for col in REQUIRED_COLUMNS}
            results.append(final_row)
        except Exception as exc:
            errors += 1
            logger.error("Row %d (user=%s) failed: %s — using fallback.", i, row["user_id"], exc)
            from code.config import FALLBACK_ROW
            fallback = FALLBACK_ROW.copy()
            fallback.update({
                "user_id": row.get("user_id", "unknown"),
                "image_paths": row.get("image_paths", ""),
                "user_claim": row.get("user_claim", ""),
                "claim_object": row.get("claim_object", "unknown"),
            })
            results.append({col: fallback.get(col, None) for col in REQUIRED_COLUMNS})

    out_df = pd.DataFrame(results, columns=REQUIRED_COLUMNS)
    
    # Run strict validation before saving
    validate_output_dataframe(out_df, expected_count=n)
    
    out_path = os.path.join(CFG_ROOT, output_file)
    out_df.to_csv(out_path, index=False)

    logger.info("Output saved → %s  (%d rows, %d errors)", out_path, len(out_df), errors)
    print(f"\nDone. {len(out_df)} rows written to {out_path}")
    if errors:
        print(f"  WARNING: {errors} rows used fallback due to unexpected errors.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Multi-Modal Evidence Review — Prediction Pipeline"
    )
    parser.add_argument(
        "--input", type=str, default="claims.csv",
        help="Input CSV filename inside dataset/ (default: claims.csv)"
    )
    parser.add_argument(
        "--output", type=str, default="output.csv",
        help="Output CSV filename written to repo root (default: output.csv)"
    )
    args = parser.parse_args()
    run_prediction(args.input, args.output)
