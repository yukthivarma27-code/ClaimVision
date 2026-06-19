import os
import re
import pandas as pd
from typing import Dict, List
from tqdm import tqdm

from . import utils
from .claim_parser import extract_claim
from .history_analyzer import analyze_history
from .evidence_checker import check_evidence
from .image_analyzer import analyze_image
from .decision_engine import make_decision


def _has_text_instructions(conversation: str) -> bool:
    patterns = [
        r"(?i)\bapprove\b",
        r"(?i)mark this (row|claim) (as )?supported",
        r"(?i)(follow|use) the (note|instruction)",
        r"(?i)skip manual review",
        r"(?i)accept this claim",
        r"(?i)approve the claim",
        r"(?i)claim should be approved",
        r"(?i)ignore.*instruction",
        r"(?i)follow.*instruction",
        r"(?i)follow.*note",
    ]
    return any(re.search(p, conversation) for p in patterns)


def _detect_manipulation_attempt(conversation: str) -> bool:
    patterns = [
        r"(?i)ignore (all |any |the )?(previous|prior|above) (instructions|prompts|rules)",
        r"(?i)you are (now |)an ai (system|assistant) that",
        r"(?i)system prompt",
        r"(?i)you must (approve|accept|support) this claim",
        r"(?i)override",
    ]
    return any(re.search(p, conversation) for p in patterns)


def predict_row(row: Dict) -> Dict:
    user_id = row["user_id"]
    image_paths_str = row["image_paths"]
    conversation = row["user_claim"]
    claim_object = row["claim_object"]

    image_paths = utils.parse_image_paths(image_paths_str)
    claim_issue, claim_part = extract_claim(conversation, claim_object)
    history_flags, history_summary = analyze_history(user_id)

    has_instructions = _has_text_instructions(conversation)
    has_manipulation = _detect_manipulation_attempt(conversation)

    image_results = []
    for idx, img_rel_path in enumerate(image_paths):
        img_path = utils.get_image_path(img_rel_path)
        if not img_path.exists():
            utils.logger.warning(f"Image not found: {img_path}")
            continue
        result = analyze_image(
            img_path, claim_object, claim_issue, claim_part,
            conversation, image_idx=idx, total_images=len(image_paths)
        )
        image_results.append(result)

    evidence_met, evidence_reason = check_evidence(
        claim_object, claim_issue, len(image_paths),
        [{"usable": r.usable, "blurry": r.blurry} for r in image_results]
    )

    decision = make_decision(
        claim_object, claim_issue, claim_part, image_results, evidence_met,
        conversation=conversation
    )
    status, justification, supporting_ids, valid_image, severity, quality_flags = decision

    risk_flags = quality_flags.copy()
    for f in history_flags:
        if f.lower() != "none" and f not in risk_flags:
            risk_flags.append(f)

    if has_instructions and "text_instruction_present" not in risk_flags:
        risk_flags.append("text_instruction_present")
    if has_manipulation and "possible_manipulation" not in risk_flags:
        risk_flags.append("possible_manipulation")

    if not risk_flags:
        risk_flags = ["none"]

    risk_flags_str = ";".join(risk_flags)
    evidence_met_str = "true" if evidence_met else "false"

    issue_final = claim_issue
    part_final = claim_part

    return {
        "user_id": user_id,
        "image_paths": image_paths_str,
        "user_claim": conversation,
        "claim_object": claim_object,
        "evidence_standard_met": evidence_met_str,
        "evidence_standard_met_reason": evidence_reason,
        "risk_flags": risk_flags_str,
        "issue_type": issue_final,
        "object_part": part_final,
        "claim_status": status,
        "claim_status_justification": justification,
        "supporting_image_ids": supporting_ids,
        "valid_image": valid_image,
        "severity": severity,
    }


def predict_csv(input_path: str, output_path: str = "output.csv") -> pd.DataFrame:
    utils.logger.info(f"Reading input from {input_path}")
    df = pd.read_csv(input_path)
    results = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing claims"):
        try:
            result = predict_row(row.to_dict())
            results.append(result)
        except Exception as e:
            utils.logger.error(f"Error processing row: {e}")
            results.append({
                "user_id": row.get("user_id", "unknown"),
                "image_paths": row.get("image_paths", ""),
                "user_claim": row.get("user_claim", ""),
                "claim_object": row.get("claim_object", ""),
                "evidence_standard_met": "false",
                "evidence_standard_met_reason": f"Error: {str(e)[:100]}",
                "risk_flags": "manual_review_required",
                "issue_type": "unknown",
                "object_part": "unknown",
                "claim_status": "not_enough_information",
                "claim_status_justification": "Processing error occurred.",
                "supporting_image_ids": "none",
                "valid_image": "false",
                "severity": "unknown",
            })

    out_df = pd.DataFrame(results)
    out_df.to_csv(output_path, index=False)
    utils.logger.info(f"Written {len(results)} predictions to {output_path}")
    return out_df
