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

from code.config import ROOT_DIR as CFG_ROOT, REQUIRED_COLUMNS
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


def run_prediction(input_file: str = "claims.csv", output_file: str = "outputs.csv"):
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
        "--output", type=str, default="outputs.csv",
        help="Output CSV filename written to repo root (default: outputs.csv)"
    )
    args = parser.parse_args()
    run_prediction(args.input, args.output)
