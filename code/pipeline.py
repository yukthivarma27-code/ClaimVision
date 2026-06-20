"""
pipeline.py
─────────────────────────────────────────────────────────────────────────────
Orchestrates per-claim processing:
  1. Build the prompt
  2. Resolve image paths
  3. Call VLM (or deterministic fallback)
  4. Validate and format output against the schema
"""
import os
import logging
from code.vlm_client import analyze_claim_vlm
from code.prompts import build_prompt
from code.config import (
    FALLBACK_ROW, CLAIM_STATUS_CHOICES, ISSUE_TYPE_CHOICES,
    OBJECT_PART_CAR_CHOICES, OBJECT_PART_LAPTOP_CHOICES, OBJECT_PART_PACKAGE_CHOICES,
    RISK_FLAGS_CHOICES, SEVERITY_CHOICES
)

logger = logging.getLogger(__name__)


def validate_and_format_row(row_input, claim_object, raw_vlm_output):
    """
    Ensure raw_vlm_output strictly matches allowed values.
    Falls back to FALLBACK_ROW defaults for any invalid field.
    """
    validated = FALLBACK_ROW.copy()
    if not isinstance(raw_vlm_output, dict):
        logger.error("VLM output is not a dict; using fallback row.")
        return validated

    def to_bool(val):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.strip().lower() in ("true", "1", "yes")
        return bool(val)

    validated["evidence_standard_met"] = to_bool(raw_vlm_output.get("evidence_standard_met", False))
    validated["evidence_standard_met_reason"] = (
        str(raw_vlm_output.get("evidence_standard_met_reason", "unknown")).replace("\n", " ")
    )
    validated["claim_status_justification"] = (
        str(raw_vlm_output.get("claim_status_justification", "unknown")).replace("\n", " ")
    )
    validated["supporting_image_ids"] = str(raw_vlm_output.get("supporting_image_ids", "none"))
    validated["valid_image"] = to_bool(raw_vlm_output.get("valid_image", False))

    issue = str(raw_vlm_output.get("issue_type", "unknown"))
    validated["issue_type"] = issue if issue in ISSUE_TYPE_CHOICES else "unknown"

    claim_stat = str(raw_vlm_output.get("claim_status", "not_enough_information"))
    validated["claim_status"] = (
        claim_stat if claim_stat in CLAIM_STATUS_CHOICES else "not_enough_information"
    )

    sev = str(raw_vlm_output.get("severity", "unknown"))
    validated["severity"] = sev if sev in SEVERITY_CHOICES else "unknown"

    part = str(raw_vlm_output.get("object_part", "unknown"))
    if claim_object == "car":
        validated["object_part"] = part if part in OBJECT_PART_CAR_CHOICES else "unknown"
    elif claim_object == "laptop":
        validated["object_part"] = part if part in OBJECT_PART_LAPTOP_CHOICES else "unknown"
    elif claim_object == "package":
        validated["object_part"] = part if part in OBJECT_PART_PACKAGE_CHOICES else "unknown"
    else:
        validated["object_part"] = "unknown"

    flags_raw = str(raw_vlm_output.get("risk_flags", "none"))
    if flags_raw == "none":
        validated["risk_flags"] = "none"
    else:
        flags = [f.strip() for f in flags_raw.split(";") if f.strip() in RISK_FLAGS_CHOICES]
        validated["risk_flags"] = ";".join(flags) if flags else "none"

    # Preserve input columns (row order guaranteed by main.py)
    validated["user_id"] = row_input["user_id"]
    validated["image_paths"] = row_input["image_paths"]
    validated["user_claim"] = row_input["user_claim"]
    validated["claim_object"] = claim_object
    validated["confidence"] = float(raw_vlm_output.get("confidence", 1.0))

    return validated


def process_single_claim(row, evidence_requirements, root_dir):
    """
    Process one claim row end-to-end.

    Parameters
    ----------
    row                  : pd.Series  – merged claim + user-history row
    evidence_requirements: pd.DataFrame
    root_dir             : str        – repo root for resolving image paths
    """
    claim_object = row["claim_object"]
    prompt = build_prompt(row, evidence_requirements)

    image_paths_raw = str(row["image_paths"]).split(";")
    image_paths = [
        os.path.join(root_dir, "dataset", p.strip()) if not os.path.isabs(p.strip()) else p.strip()
        for p in image_paths_raw
    ]

    logger.debug("Processing user=%s  object=%s  images=%s", row["user_id"], claim_object, image_paths)

    # Pass row + req_df so the deterministic engine has everything it needs
    raw_vlm_output = analyze_claim_vlm(
        prompt,
        image_paths,
        row=row.to_dict() if hasattr(row, "to_dict") else dict(row),
        req_df=evidence_requirements,
    )

    return validate_and_format_row(row, claim_object, raw_vlm_output)
