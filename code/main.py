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
load_dotenv(os.path.join(ROOT_DIR, ".env"), override=True)

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
    Load data, process claims through the routing pipeline, and write output.csv.
    Preserves row order from claims.csv.
    """
    logger.info("Loading data from %s …", input_file)
    merged_df, req_df = load_data(input_file)
    n = len(merged_df)
    logger.info("Loaded %d claims. Starting pipeline …", n)

    # Initialize stats counters
    vlm_count = 0
    fallback_count = 0
    cache_hits = 0
    quota_errors = 0
    timeout_errors = 0

    from code.vlm_client import load_vlm_cache, compute_cache_key, PROMPT_VERSION
    from code.deterministic_engine import analyze_claim_deterministic, calculate_deterministic_confidence
    from code.prompts import build_prompt
    from code.pipeline import validate_and_format_row
    import code.vlm_client as vlm_client
    import traceback

    vlm_cache = load_vlm_cache()

    # Pre-analysis pass: Calculate cache keys, check cache hits, compute confidence and deterministic fallback
    rows_data = []
    for idx, row in merged_df.iterrows():
        user_id = row["user_id"]
        claim_object = row["claim_object"]
        user_claim = row["user_claim"]
        image_paths_raw = str(row["image_paths"]).split(";")
        image_paths = [
            os.path.join(CFG_ROOT, "dataset", p.strip()) if not os.path.isabs(p.strip()) else p.strip()
            for p in image_paths_raw
        ]

        # Compute cache key using the required variables
        cache_key = compute_cache_key(user_claim, claim_object, image_paths, "gemini-flash-latest", PROMPT_VERSION)

        # Check cache hit
        cache_hit_data = vlm_cache.get(cache_key, None)

        # Compute deterministic analysis
        obj_req = get_requirements_for_object(req_df, claim_object)
        det_result = analyze_claim_deterministic(row.to_dict(), image_paths, obj_req)
        det_confidence = calculate_deterministic_confidence(row.to_dict(), image_paths, obj_req)

        rows_data.append({
            "idx": idx, # preserve original row index
            "row": row,
            "image_paths": image_paths,
            "obj_req": obj_req,
            "cache_key": cache_key,
            "cache_hit_data": cache_hit_data,
            "det_result": det_result,
            "det_confidence": det_confidence,
            "result_row": None, # will be populated
            "processed_by": None # "cache_hit", "vlm", "fallback"
        })

    # Group 1: Cache hits (already solved by VLM, no API call or fallback needed)
    for rd in rows_data:
        if rd["cache_hit_data"] is not None:
            formatted = validate_and_format_row(rd["row"], rd["row"]["claim_object"], rd["cache_hit_data"])
            rd["result_row"] = formatted
            rd["processed_by"] = "cache_hit"
            cache_hits += 1
            vlm_count += 1
            logger.info("Row %d (user=%s) - Cache HIT.", rd["idx"] + 1, rd["row"]["user_id"])

    # Group 2: High confidence fallback (confidence >= 0.85, deterministic result is highly certain)
    for rd in rows_data:
        if rd["processed_by"] is None and rd["det_confidence"] >= 0.85:
            formatted = validate_and_format_row(rd["row"], rd["row"]["claim_object"], rd["det_result"])
            formatted["confidence"] = rd["det_confidence"]
            rd["result_row"] = formatted
            rd["processed_by"] = "fallback"
            fallback_count += 1
            logger.info("Row %d (user=%s) - High confidence fallback (confidence=%.2f).", rd["idx"] + 1, rd["row"]["user_id"], rd["det_confidence"])

    # Group 3: Low confidence candidates (confidence < 0.85, need VLM)
    vlm_candidates = [rd for rd in rows_data if rd["processed_by"] is None]
    # Rank candidates by uncertainty (lowest confidence first)
    vlm_candidates.sort(key=lambda x: x["det_confidence"])

    logger.info("Total VLM candidates: %d", len(vlm_candidates))

    # Initialize client error counts in case they are imported
    vlm_client.QUOTA_ERRORS_LOGGED = 0
    vlm_client.TIMEOUT_ERRORS_LOGGED = 0

    for rd in vlm_candidates:
        user_id = rd["row"]["user_id"]
        confidence = rd["det_confidence"]
        
        # If daily quota is already exhausted, bypass immediately
        if vlm_client.DAILY_QUOTA_EXHAUSTED:
            logger.info("Row %d (user=%s, conf=%.2f) - Quota exhausted bypass. Using fallback.", rd["idx"] + 1, user_id, confidence)
            formatted = validate_and_format_row(rd["row"], rd["row"]["claim_object"], rd["det_result"])
            formatted["confidence"] = confidence
            rd["result_row"] = formatted
            rd["processed_by"] = "fallback"
            fallback_count += 1
            continue

        logger.info("Row %d (user=%s, conf=%.2f) - Routing to VLM.", rd["idx"] + 1, user_id, confidence)
        prompt = build_prompt(rd["row"], rd["obj_req"])
        
        try:
            # Call analyze_claim_vlm
            raw_vlm = vlm_client.analyze_claim_vlm(prompt, rd["image_paths"], row=rd["row"].to_dict(), req_df=rd["obj_req"])
            
            fb_patterns = [
                'The conversation clearly describes', 'User history contains flags',
                'Evidence standard not met', 'A prompt injection attempt',
                'Possible contradiction signals', 'The conversation expresses',
                'Insufficient claim specificity', 'API Failure occurred'
            ]
            just = raw_vlm.get("claim_status_justification", "")
            is_fallback = any(pat in just for pat in fb_patterns)

            if is_fallback:
                logger.info("Row %d (user=%s) - VLM API failed or returned fallback. Using fallback.", rd["idx"] + 1, user_id)
                formatted = validate_and_format_row(rd["row"], rd["row"]["claim_object"], raw_vlm)
                formatted["confidence"] = confidence
                rd["result_row"] = formatted
                rd["processed_by"] = "fallback"
                fallback_count += 1
            else:
                logger.info("Row %d (user=%s) - VLM API Succeeded.", rd["idx"] + 1, user_id)
                formatted = validate_and_format_row(rd["row"], rd["row"]["claim_object"], raw_vlm)
                rd["result_row"] = formatted
                rd["processed_by"] = "vlm"
                vlm_count += 1

        except Exception as exc:
            logger.error("Row %d (user=%s) - Exception in VLM: %s", rd["idx"] + 1, user_id, exc)
            
            # Fall back to deterministic
            formatted = validate_and_format_row(rd["row"], rd["row"]["claim_object"], rd["det_result"])
            formatted["confidence"] = confidence
            rd["result_row"] = formatted
            rd["processed_by"] = "fallback"
            fallback_count += 1

    # Extract dynamic errors count from the VLM client wrapper
    quota_errors = vlm_client.QUOTA_ERRORS_LOGGED
    timeout_errors = vlm_client.TIMEOUT_ERRORS_LOGGED

    # Restore original row order by sorting by original index
    rows_data.sort(key=lambda x: x["idx"])

    # Assemble final results
    results = [rd["result_row"] for rd in rows_data]

    # Convert to DataFrame
    out_df = pd.DataFrame(results, columns=REQUIRED_COLUMNS)

    # Final output.csv validation
    validation_status = "Failed"
    try:
        validate_output_dataframe(out_df, expected_count=n)
        validation_status = "Passed"
    except Exception as val_err:
        logger.error("Final validation failed: %s", val_err)
        traceback.print_exc()

    # Save to file
    out_path = os.path.join(CFG_ROOT, output_file)
    out_df.to_csv(out_path, index=False)

    logger.info("Output saved → %s (%d rows)", out_path, len(out_df))

    # Print final audit report (Rule 8)
    print("\n" + "="*50)
    print("FINAL MULTIMODAL PIPELINE AUDIT REPORT")
    print("="*50)
    print(f"Total Rows Processed       : {n}")
    print(f"VLM-processed Rows (Total) : {vlm_count}")
    print(f"  - Active VLM Successes   : {vlm_count - cache_hits}")
    print(f"  - Permanent Cache Hits   : {cache_hits}")
    print(f"Fallback-processed Rows   : {fallback_count}")
    print(f"Quota/Rate-limit Errors    : {quota_errors}")
    print(f"Timeout Errors             : {timeout_errors}")
    print(f"Output Validation Status   : {validation_status}")
    print("="*50 + "\n")


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

