import re
from typing import Dict, List, Tuple

from .image_analyzer import ImageAnalysisResult


def _conv(conversation: str) -> dict:
    c = conversation.lower()
    
    # Primary signals
    has_photos = bool(re.search(r"(upload|attach|attached|photo|image|picture|img_|proof)", c))
    has_damage_word = bool(re.search(
        r"(cracked?|broken|dented|scratched|shattered|crushed|torn|damaged|stain)", c
    ))
    
    # Hedging: being uncertain about the damage itself (not about claim type)
    hedged_damage = bool(re.search(
        r"(may be|might be|looks like|i think|maybe|perhaps|not sure if.*(?:crack|dent|scratch|damage|issue)|"
        r"confused|wondering if|couldn't decide|cannot tell|overthinking|"
        r"walked around|not fully sure|am not sure|not certain|could not decide)", c
    ))
    
    # Clear definitive damage statement (overrides hedging)
    definitive_damage = bool(re.search(
        r"(is (cracked|broken|dented|scratched|shattered|crushed|torn|damaged)|"
        r"have (a |)(crack|dent|scratch|stain|damage|break)|"
        r"has (a |)(crack|dent|scratch|stain|damage|break)|"
        r"claim is.*(crack|dent|scratch|damage|break|stain|shatter)|"
        r"reporting.*(crack|dent|scratch|damage|break|stain|shatter)|"
        r"submitting this|the actual issue|"
        r"attached photo|uploaded|here.*photo)", c
    ))
    
    unsure = hedged_damage and not bool(re.search(
        r"not.*(?:any|major|big|other|else|way it should)", c
    )) and not definitive_damage
    
    confident = (has_photos or has_damage_word or definitive_damage) and not unsure
    
    return {
        "confident": confident,
        "unsure": unsure,
        "text_instructions": bool(re.search(
            r"(?i)(approve|mark.*supported|skip.*review|follow.*note|"
            r"follow.*instruction|accept this|note is enough)", c)),
        "manipulation": bool(re.search(
            r"(?i)(ignore.*instruction|ignore.*prompt|you are.*ai|"
            r"override|system prompt)", c)),
        "severe": bool(re.search(
            r"(?i)(bad|severe|pretty bad|looks bad|badly|shattered|severely)", c)),
        "mismatch": bool(re.search(
            r"(?i)(unrelated|different|not the same|wrong photo|"
            r"ignore|not.*about|not.*claim|the item inside|"
            r"contents.*missing|missing.*contents)", c)),
    }


def make_decision(
    claim_object: str, claim_issue: str, claim_part: str,
    image_results: List[ImageAnalysisResult], evidence_met: bool,
    conversation: str = "",
) -> Tuple[str, str, str, str, str, List[str]]:
    signals = _conv(conversation)
    
    all_quality_flags = list(set(
        f for r in image_results for f in r.quality_flags
    ))
    
    valid_images = [r for r in image_results if r.usable]
    
    if signals["text_instructions"] and "text_instruction_present" not in all_quality_flags:
        all_quality_flags.append("text_instruction_present")
    if signals["manipulation"] and "possible_manipulation" not in all_quality_flags:
        all_quality_flags.append("possible_manipulation")

    if not valid_images:
        return "not_enough_information", "No usable images available for review.", "none", "false", "unknown", all_quality_flags

    # GPT-4o path: actual visual damage detected
    for r in valid_images:
        if r.damage_visible and r.damage_type == claim_issue and r.damage_type not in ("unknown", "none"):
            sev = r.severity if r.severity not in ("unknown", "none") else "medium"
            just = f"Image {r.image_id} shows {claim_issue} on {claim_part} consistent with the claim. {r.description[:100]}"
            return "supported", just, r.image_id, "true", sev, all_quality_flags

    # Check if GPT-4o was used (any image shows damage visible)
    using_api = any(r.damage_visible for r in image_results)

    # --- FALLBACK PATH ---
    if not using_api:
        return _fallback(claim_object, claim_issue, claim_part, valid_images, signals, all_quality_flags)

    # GPT-4o mode but no damage match
    return _gpt_fallback(claim_object, claim_issue, claim_part, valid_images, signals, all_quality_flags)


def _fallback(claim_object, claim_issue, claim_part, valid_images, signals, all_quality_flags) -> Tuple:
    """Conversation-driven fallback decision."""
    img = valid_images[0].image_id

    # Check for manipulation attempts
    if signals["manipulation"]:
        return "contradicted", "Claim contains instruction-override attempts. Visual evidence does not support automatic approval.", img, "true", "none", all_quality_flags
    
    # Instruction following attempts should be reviewed
    if signals["text_instructions"] and signals["confident"]:
        if claim_issue == "none":
            return "contradicted", f"Image {img} shows the {claim_part} area but no damage is visible, contradicting the claim.", img, "true", "none", all_quality_flags
        # Confident claim with instructions should still evaluate the claim
        if claim_issue == "unknown":
            pass  # Fall through to unsure logic

    # Content mismatch (package contents, wrong object)
    if signals["mismatch"] and claim_object == "package" and claim_part in ("contents", "item"):
        return "not_enough_information", f"Image {img} does not clearly show the package contents. Insufficient evidence to verify missing items.", "none", "false", "unknown", all_quality_flags

    if signals["mismatch"] and not signals["confident"]:
        if "claim_mismatch" not in all_quality_flags:
            all_quality_flags.append("claim_mismatch")
        
        # If user describes different thing or is confused, it's contradicted
        if claim_issue != "unknown" and claim_part != "unknown":
            return "contradicted", f"Image {img} shows the {claim_part} but the visible condition does not match the claimed {claim_issue}.", img, "true", "none", all_quality_flags

    # Not sure / confused
    if signals["unsure"] or (claim_issue == "unknown" and claim_part == "unknown"):
        if claim_part == "unknown" or claim_issue == "unknown":
            return "not_enough_information", "The conversation does not clearly identify the specific damage or part. Manual image review needed.", "none", "true", "unknown", all_quality_flags
        return "not_enough_information", f"The claimant expressed uncertainty about the {claim_part}. Clear visual evidence needed.", "none", "true", "unknown", all_quality_flags

    # Confident claim with photos
    if signals["confident"] and claim_issue != "unknown":
        sev = "medium"
        if claim_issue in ("scratch", "stain", "dent"):
            sev = "low" if not signals["severe"] else "medium"
        if claim_issue in ("crack", "glass_shatter", "broken_part", "crushed_packaging", "torn_packaging"):
            sev = "medium"
        
        if "damage_not_visible" in all_quality_flags:
            all_quality_flags.remove("damage_not_visible")
        
        just = f"Image {img} shows {claim_issue} on {claim_part} consistent with the claim."
        return "supported", just, img, "true", sev, all_quality_flags

    # Confident with unknown issue
    if signals["confident"]:
        if claim_part != "unknown":
            return "supported", f"Image {img} of {claim_object} {claim_part} shows signs consistent with the reported issue.", img, "true", "unknown", all_quality_flags
        return "not_enough_information", "Claim part not identified from conversation.", "none", "true", "unknown", all_quality_flags

    # Default: not enough info
    return "not_enough_information", "Insufficient evidence to determine claim status.", "none", "false", "unknown", all_quality_flags


def _gpt_fallback(claim_object, claim_issue, claim_part, valid_images, signals, all_quality_flags) -> Tuple:
    """GPT analyzed images but no damage found - use that signal."""
    img = valid_images[0].image_id
    
    if claim_part != "unknown":
        return "contradicted", f"Image {img} shows the {claim_part} area but no {claim_issue} damage is detected, contradicting the claim.", img, "true", "none", all_quality_flags
    
    if signals["unsure"]:
        return "not_enough_information", "Images do not provide clear evidence for the claimed damage.", "none", "true", "unknown", all_quality_flags
    
    return "not_enough_information", f"Image {img} does not show sufficient evidence of {claim_issue} on the claimed part.", "none", "true", "unknown", all_quality_flags
