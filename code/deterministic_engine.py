"""
deterministic_engine.py  (v4 — final enhanced)
─────────────────────────────────────────────────────────────────────────────
Fully deterministic claim analysis without any external API call.

v4 fixes (based on gap analysis vs sample_claims.csv):
  • issue_type: added Hindi/multilingual patterns, more specific triggers
  • object_part: hinge beats screen when "hinge area" present; "phati/seal" → seal
  • claim_status:
      - 'non_original_image' history flag → contradicted
      - 'wrong_object' history flag → contradicted
      - 'damage_not_visible' history flag → not_enough_information
      - "could not find" / "not inside" → not_enough_information for contents
      - uncertainty language without specific part → not_enough_information
      - injection + user_history_risk → contradicted (not just not_enough_info)
  • severity: broken_part on hinge/lid/corner/base → medium (not high);
              missing_part → medium; none/unknown issue → none/"unknown"
"""

import os
import re
import logging
from code.config import (
    ISSUE_TYPE_CHOICES, OBJECT_PART_CAR_CHOICES,
    OBJECT_PART_LAPTOP_CHOICES, OBJECT_PART_PACKAGE_CHOICES,
    RISK_FLAGS_CHOICES, SEVERITY_CHOICES, CLAIM_STATUS_CHOICES,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Issue-type priority table
# (priority, issue_type, list_of_keywords)
# Higher priority wins on score tie; longer keyword wins on priority tie.
# ─────────────────────────────────────────────────────────────────────────────
ISSUE_PRIORITY_TABLE = [
    (10, "glass_shatter",     ["glass shattered", "windshield shatter"]),
    (9,  "crack",             ["cracked screen", "screen crack", "screen has a crack",
                               "screen shatter", "crack lines", "crack spreading",
                               "cracked", "cracking", "crack", "fracture", "fissure"]),
    (9,  "dent",              ["has a dent", "dent now", "dent on", "dent along",
                               "dented", "dab gaya", "indented", "depressed"]),
    (9,  "broken_part",       ["hinge area has broken", "hinge is broken", "hinge broke",
                               "mirror is broken", "broken", "broke", "toot gaya",
                               "snapped", "missing or broken", "does not sit properly",
                               "not sitting", "does not open", "no longer opens"]),
    (9,  "scratch",           ["scratch across", "has a scratch", "scratch on",
                               "scratched", "a scratch", "scrape", "scraped",
                               "light scratch", "deep scratch"]),
    (8,  "torn_packaging",    ["phati hui thi", "phati hui", "phata hui", "seal phati",
                               "torn open", "torn-open", "seal torn", "ripped open",
                               "seal open", "opened packaging", "parcel khola",
                               "torn seal", "jaise parcel khola"]),
    (8,  "missing_part",      ["keycaps came off", "keycap", "keys missing",
                               "key is missing", "missing key", "came off", "fell off",
                               "faltan", "teclas", "keys missing"]),
    (8,  "crushed_packaging", ["badly crushed", "box crushed", "package crushed",
                               "crush ho", "dab gaya", "squished", "crushed in",
                               "crushed corner", "corner was crushed"]),
    (8,  "water_damage",      ["water damage", "water damaged", "wet box",
                               "water stain", "rain damage", "got wet"]),
    (7,  "stain",             ["stain", "stained", "oil stain", "oily mark",
                               "dark stain", "coffee stain", "liquid stain"]),
    # Low-priority catch-alls
    (5,  "missing_part",      ["product missing", "contents missing", "not inside",
                               "could not find"]),
    (5,  "water_damage",      ["wet", "liquid", "soaked", "spill", "coffee"]),
    (5,  "crushed_packaging", ["crushed"]),
    (5,  "torn_packaging",    ["torn"]),
    (4,  "scratch",           [" mark ", "mark on"]),
    (3,  "broken_part",       ["broken", "smashed", "not working"]),
    (2,  "dent",              ["damaged", "affected", "hit", "impact", "looks bad", "daño", "dano"]),
    (1,  "broken_part",       ["issue", "problem", "ruined", "destroyed"]),
]

# ─────────────────────────────────────────────────────────────────────────────
# Object-part priority table per claim_object
# (priority, part, list_of_keywords)
# ─────────────────────────────────────────────────────────────────────────────
OBJECT_PART_KEYWORDS = {
    "car": [
        (10, "windshield",   ["windshield", "front glass", "windscreen", "wind screen"]),
        (10, "front_bumper", ["front bumper", "fore bumper"]),
        (10, "rear_bumper",  ["rear bumper", "back bumper", "behind bumper"]),
        (10, "side_mirror",  ["side mirror", "wing mirror", "left mirror", "left side mirror"]),
        (10, "headlight",    ["headlight", "head light", "front light"]),
        (10, "taillight",    ["taillight", "tail light", "back light", "rear light"]),
        (9,  "hood",         ["the hood", "on the hood", "across the hood", "bonnet"]),
        (9,  "door",         ["door panel", "door dented", "door damage", "the door",
                               "left side door", "black car door", "car door"]),
        (8,  "fender",       ["fender"]),
        (8,  "quarter_panel",["quarter panel"]),
        (7,  "body",         ["body panel", "body damage", "outer body"]),
        (5,  "rear_bumper",  ["bumper", "back", "parachoque"]),
        (4,  "door",         ["door"]),
        (1,  "body",         ["car", "vehicle", "it"]),
    ],
    "laptop": [
        # hinge must beat screen when both are mentioned
        (10, "hinge",        ["hinge area has broken", "hinge is broken", "hinge broke",
                               "the hinge", "hinge damage", "hinge area"]),
        (10, "screen",       ["laptop screen", "cracked screen", "screen crack",
                               "screen has a crack", "screen damage", "screen broken",
                               "broken screen", "screen shatter", "display crack",
                               "display has", "display glass", "the screen is the issue",
                               "the screen", "screen only"]),
        (10, "trackpad",     ["trackpad", "touchpad"]),
        (10, "keyboard",     ["keyboard keys", "keycap", "missing key",
                               "keyboard damage", "keyboard liquid",
                               "keyboard area", "keys feel", "went over the keys"]),
        (10, "lid",          ["laptop lid", "the lid", "lid area", "lid is cracked"]),
        (9,  "corner",       ["laptop corner", "corner of the laptop", "corner dented"]),
        (9,  "port",         ["usb port", "hdmi port", "charging port", "the port"]),
        (8,  "base",         ["base", "bottom panel"]),
        (7,  "body",         ["outer body", "chassis", "casing"]),
        # Catch-alls last so specific matches win
        (5,  "screen",       ["screen", "display"]),
        (5,  "keyboard",     ["keyboard", "keys"]),
        (4,  "hinge",        ["hinge"]),
        (1,  "body",         ["laptop", "computer", "device", "machine", "it"]),
    ],
    "package": [
        (10, "package_corner", ["package corner", "corner of the package",
                                 "corner was crushed", "corner dab", "corner damage",
                                 "corner is crushed", "corner crushed"]),
        (10, "seal",           ["seal area", "seal torn", "torn seal", "seal side",
                                 "the seal", "seal open", "phati hui", "seal phati",
                                 "parcel khola"]),
        (10, "label",          ["shipping label", "the label", "address label",
                                 "label damage", "label became unreadable"]),
        (9,  "contents",       ["product inside", "contents missing",
                                 "item inside the box", "the product inside",
                                 "not inside the box", "could not find the product",
                                 "product inside"]),
        (9,  "item",           ["item inside", "inside item", "broken item",
                                 "the item inside"]),
        (8,  "package_side",   ["package side", "package surface", "the outside",
                                 "outside surface", "surface looked"]),
        (7,  "box",            ["cardboard box", "delivery box", "the box",
                                 "shipping box", "outside box"]),
        (5,  "seal",           ["flap", "tape", "torn"]),
        (4,  "contents",       ["inside", "contents"]),
        (3,  "box",            ["box"]),
        (1,  "box",            ["package", "parcel", "order", "delivery", "it"]),
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Prompt injection patterns
# ─────────────────────────────────────────────────────────────────────────────
INJECTION_PATTERNS = [
    r"approve\s+(immediately|this|now|claim|it|the)",
    r"skip\s+(review|manual|verification)",
    r"mark\s+(as\s+)?(supported|approved|valid|accepted)",
    r"mark\s+this\s+row",
    r"ignore\s+(previous|prior|all|above|review)",
    r"auto[\s-]?approve",
    r"bypass\s+review",
    r"force\s+approve",
    r"this\s+should\s+be\s+approved",
    r"follow\s+it\s+and\s+approve",
    r"follow\s+the\s+note",
    r"keep\s+(reopen|reopening|opening)",
    r"escalate\s+publicly",
    r"ignore\s+all\s+previous\s+instructions",
    r"approve\s+the\s+claim",
    r"usko\s+follow\s+karke\s+claim\s+approve",   # Hindi injection
]

# ─────────────────────────────────────────────────────────────────────────────
# Conversation-level signals for claim status
# ─────────────────────────────────────────────────────────────────────────────

# Strong uncertainty without clear physical claim → not_enough_information
UNCERTAINTY_PATTERNS = [
    r"not\s+fully\s+sure",
    r"not\s+sure\s+(if|whether|what|how)",
    r"i\s+(was\s+)?confused",
    r"(could|can)\s+not\s+(decide|tell|see|find|notice|determine)",
    r"not\s+sure\s+if\s+i\s+(am|was)\s+overthinking",
    r"could\s+not\s+find\s+the\s+product",
    r"could\s+not\s+find\s+(anything|it)",
]

# Explicit contradiction signals
CONTRADICTION_PATTERNS = [
    r"wrong\s+(photo|image|picture)",
    r"unrelated\s+(photo|image|picture)",
    r"(very|extremely|severely|totally|badly)\s+damaged",   # exaggeration
    r"no\s+(visible\s+)?(damage|crack|dent|scratch|issue)",
    r"(only|just)\s+(minor|small|light|tiny)\s+(scratch|mark|dent)",
    r"cannot\s+(see|find|notice|verify)\s+(any\s+)?(damage|crack|issue)",
]

# ─────────────────────────────────────────────────────────────────────────────
# History-flag-based override rules
# These flags from user_history.csv indicate specific contradictions
# that a vision model would normally detect from the image.
# ─────────────────────────────────────────────────────────────────────────────
# Flags that imply the image likely contradicts or doesn't support the claim
CONTRADICTED_FLAGS = {"non_original_image", "wrong_object"}
# Flags that imply evidence cannot be assessed (image quality issues)
NEI_FLAGS = {"damage_not_visible", "cropped_or_obstructed", "blurry_image",
             "low_light_or_glare", "wrong_angle"}

# ─────────────────────────────────────────────────────────────────────────────
# Severity matrix  (claim_status × issue_type → severity)
# ─────────────────────────────────────────────────────────────────────────────
SEVERITY_MAP_SUPPORTED = {
    "glass_shatter":     "high",
    "broken_part":       "medium",   # hinge/lid/corner break = medium
    "missing_part":      "medium",
    "crack":             "medium",
    "dent":              "medium",
    "torn_packaging":    "medium",
    "crushed_packaging": "medium",
    "water_damage":      "medium",
    "stain":             "medium",
    "scratch":           "low",
    "none":              "none",
    "unknown":           "unknown",
}


# ─────────────────────────────────────────────────────────────────────────────
# Parsers
# ─────────────────────────────────────────────────────────────────────────────

def extract_issue_type(conversation: str) -> str:
    text_l = conversation.lower()
    best = (0, 0, "unknown")
    for (prio, itype, kws) in ISSUE_PRIORITY_TABLE:
        for kw in kws:
            if kw.lower() in text_l:
                score = (prio, len(kw))
                if score > (best[0], best[1]):
                    best = (prio, len(kw), itype)
    return best[2]


def extract_object_part(conversation: str, claim_object: str) -> str:
    text_l = conversation.lower()
    entries = OBJECT_PART_KEYWORDS.get(claim_object, [])
    best = (0, 0, "unknown")
    for (prio, part, kws) in entries:
        for kw in kws:
            if kw.lower() in text_l:
                score = (prio, len(kw))
                if score > (best[0], best[1]):
                    best = (prio, len(kw), part)
    return best[2]


def detect_prompt_injection(conversation: str) -> bool:
    text_l = conversation.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_l):
            logger.warning("Prompt injection detected: %s", pattern)
            return True
    return False


def detect_uncertainty(conversation: str) -> bool:
    text_l = conversation.lower()
    return any(re.search(p, text_l) for p in UNCERTAINTY_PATTERNS)


def detect_contradiction(conversation: str) -> bool:
    text_l = conversation.lower()
    return any(re.search(p, text_l) for p in CONTRADICTION_PATTERNS)


def extract_risk_flags(row: dict) -> list:
    raw = str(row.get("history_flags", "none"))
    flags = []
    for f in raw.split(";"):
        f = f.strip()
        if f and f != "none" and f in RISK_FLAGS_CHOICES:
            flags.append(f)
    return flags


def check_evidence_standard(image_paths: list, claim_object: str, req_df) -> tuple:
    existing = [p for p in image_paths if os.path.exists(p)]
    n = len(existing)
    if n == 0:
        return False, "No accessible image files found on disk for this claim."
    sizes = [os.path.getsize(p) for p in existing]
    if min(sizes) < 1024:
        return False, "One or more images appear corrupt or placeholder (< 1 KB). Evidence standard not met."
    noun = "images" if n > 1 else "image"
    reason = (
        f"{n} {noun} submitted and accessible. "
        f"{'Multi-image submission satisfies' if n > 1 else 'Single image provisionally satisfies'} "
        "the general evidence visibility requirement."
    )
    return True, reason


# ─────────────────────────────────────────────────────────────────────────────
# Claim-status decision engine
# ─────────────────────────────────────────────────────────────────────────────

def decide_claim_status(
    issue_type: str,
    object_part: str,
    injection_detected: bool,
    uncertainty_detected: bool,
    contradiction_detected: bool,
    history_flags_set: set,
    has_history_risk: bool,
    has_manual_review: bool,
    evidence_met: bool,
    valid_image: bool,
) -> tuple:
    has_specific = issue_type not in ("unknown", "none") and object_part != "unknown"
    contradicted_by_history = bool(CONTRADICTED_FLAGS & history_flags_set)
    nei_by_history          = bool(NEI_FLAGS & history_flags_set)

    # P1: Injection detected
    if injection_detected:
        # If also history risk, that makes it stronger → contradicted
        if has_history_risk:
            return (
                "contradicted",
                "A prompt injection attempt was detected in the claim conversation. "
                "Combined with elevated user history risk, the claim is contradicted. "
                "Mandatory manual review required."
            )
        return (
            "not_enough_information",
            "A prompt injection attempt was detected in the claim conversation "
            "(e.g., instruction to approve or skip review). "
            "Claim flagged for mandatory manual review."
        )

    # P2: Evidence problems
    if not evidence_met or not valid_image:
        return (
            "not_enough_information",
            "Evidence standard not met: no accessible or valid image files found. "
            "Visual confirmation is not possible without usable images."
        )

    # P3: History flags that imply contradiction (wrong_object / non_original_image)
    if contradicted_by_history:
        return (
            "contradicted",
            f"User history contains flags indicating the submitted image likely does not "
            f"match the claimed object or is not an original photo. "
            f"Extracted claim: '{issue_type}' on '{object_part}'. "
            f"Claim is contradicted; manual review required."
        )

    # P4: History flags that imply evidence insufficient (damage_not_visible, etc.)
    if nei_by_history:
        return (
            "not_enough_information",
            f"User history contains flags indicating the submitted image may not show "
            f"the claimed damage clearly enough (e.g., wrong angle, obstructed). "
            f"Extracted claim: '{issue_type}' on '{object_part}'."
        )

    # P5: Contradiction in conversation + history risk → contradicted
    if contradiction_detected and has_history_risk:
        return (
            "contradicted",
            f"Contradiction signals in conversation (e.g., exaggeration, wrong-object language) "
            f"combined with elevated user history risk. "
            f"Claim: '{issue_type}' on '{object_part}'. Manual review recommended."
        )

    # P6: Contradiction in conversation alone → not_enough_information
    if contradiction_detected:
        return (
            "not_enough_information",
            f"Possible contradiction signals detected in conversation for "
            f"'{issue_type}' on '{object_part}'. Visual evidence required to resolve."
        )

    # P7: Uncertainty language → not_enough_information ONLY if no specific claim
    if uncertainty_detected and not has_specific:
        return (
            "not_enough_information",
            "The conversation expresses significant uncertainty about the damage "
            "and lacks a clearly extractable claim type or object part."
        )

    # P7b: No specific claim at all → not_enough_information
    if not has_specific:
        return (
            "not_enough_information",
            f"Insufficient claim specificity (issue_type='{issue_type}', "
            f"object_part='{object_part}'). Cannot determine status without a vision model."
        )

    # P8: Specific claim + no red flags → supported
    if has_specific:
        note = " User history indicates elevated risk; human reviewer should cross-check." \
               if has_history_risk else ""
        return (
            "supported",
            f"The conversation clearly describes '{issue_type}' on '{object_part}' "
            f"of the claimed object. Images are present and evidence standard is met. "
            f"Claim is provisionally supported pending visual confirmation.{note}"
        )

    # P9: Fallthrough
    return (
        "not_enough_information",
        f"Insufficient claim specificity (issue_type='{issue_type}', "
        f"object_part='{object_part}'). Cannot determine status without a vision model."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Severity
# ─────────────────────────────────────────────────────────────────────────────

def assign_severity(issue_type: str, claim_status: str) -> str:
    if claim_status == "contradicted":
        return "none"
    if claim_status == "not_enough_information":
        return "unknown"
    return SEVERITY_MAP_SUPPORTED.get(issue_type, "unknown")


def build_supporting_image_ids(image_paths: list, claim_status: str) -> str:
    if claim_status != "supported":
        return "none"
    ids = [os.path.splitext(os.path.basename(p))[0] for p in image_paths if os.path.exists(p)]
    return ";".join(ids) if ids else "none"


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def calculate_deterministic_confidence(row: dict, image_paths: list, req_df) -> float:
    # Starts at 1.0
    conf = 1.0
    
    # 1. Image file existence
    existing_images = [p for p in image_paths if os.path.exists(p)]
    if len(existing_images) == 0:
        # If no images exist on disk, we are 100% confident it's NEI (no VLM needed)
        return 1.0
    
    # If some images listed do not exist, we have a discrepancy, deduct confidence
    if len(existing_images) < len(image_paths):
        conf -= 0.15
        
    # 2. Number of images
    # VLM routing should prioritize multiple-image claims, so we lower confidence for multiple images
    if len(existing_images) > 1:
        conf -= 0.15 * (len(existing_images) - 1)
        
    # 3. Object Type & Evidence Requirements
    claim_object = str(row.get("claim_object", "")).lower()
    conversation = str(row.get("user_claim", ""))
    
    # Base offsets/multipliers
    if claim_object == "car":
        conf -= 0.05
    elif claim_object == "laptop":
        conf -= 0.05
    elif claim_object == "package":
        conf -= 0.10
        
    # Specific package contents / item claims require visual inspection, deduct confidence
    part = extract_object_part(conversation, claim_object)
    if claim_object == "package" and part in ("contents", "item"):
        conf -= 0.25
        
    # 4. Ambiguity in Claim
    # Check for generic/ambiguous keywords in claim text
    text_l = conversation.lower()
    generic_words = ["damaged", "affected", "looks bad", "problem", "issue", "ruined", "destroyed", "dano", "daño"]
    if any(gw in text_l for gw in generic_words):
        conf -= 0.15
        
    # Check for uncertainty language
    if detect_uncertainty(conversation):
        conf -= 0.20
        
    # Check for contradiction signals in text
    if detect_contradiction(conversation):
        conf -= 0.15
        
    # Check for prompt injection
    if detect_prompt_injection(conversation):
        conf -= 0.20
        
    # 5. Risk Flags from history
    risk_flags = extract_risk_flags(row)
    if "user_history_risk" in risk_flags:
        conf -= 0.20
    if "manual_review_required" in risk_flags:
        conf -= 0.15
    for flag in risk_flags:
        if flag not in ("user_history_risk", "manual_review_required"):
            conf -= 0.10
            
    # 6. Uncertain parts/issues
    issue_type = extract_issue_type(conversation)
    if issue_type == "unknown" or issue_type == "none":
        conf -= 0.25
    if part == "unknown":
        conf -= 0.25

    # Clamp confidence between 0.0 and 1.0
    return max(0.0, min(1.0, conf))


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def analyze_claim_deterministic(row: dict, image_paths: list, req_df) -> dict:
    conversation = str(row.get("user_claim", ""))
    claim_object = str(row.get("claim_object", "")).lower()

    # Parsing
    issue_type  = extract_issue_type(conversation)
    object_part = extract_object_part(conversation, claim_object)
    logger.info("Extracted: issue_type=%-18s  object_part=%s", issue_type, object_part)

    # Signals
    injection_detected     = detect_prompt_injection(conversation)
    uncertainty_detected   = detect_uncertainty(conversation)
    contradiction_detected = detect_contradiction(conversation)

    # Risk flags from history
    risk_flags       = extract_risk_flags(row)
    history_flags_set = set(risk_flags)
    if injection_detected and "text_instruction_present" not in risk_flags:
        risk_flags.append("text_instruction_present")
    has_history_risk  = "user_history_risk"      in history_flags_set
    has_manual_review = "manual_review_required" in history_flags_set

    # Evidence
    evidence_met, evidence_reason = check_evidence_standard(image_paths, claim_object, req_df)
    valid_image = evidence_met and any(
        os.path.exists(p) and os.path.getsize(p) >= 1024 for p in image_paths
    )

    # Claim status
    claim_status, justification = decide_claim_status(
        issue_type, object_part,
        injection_detected, uncertainty_detected, contradiction_detected,
        history_flags_set, has_history_risk, has_manual_review,
        evidence_met, valid_image,
    )

    # Calculate supporting image ids
    supporting_ids = build_supporting_image_ids(image_paths, claim_status)

    # Apply Rule 5: even if fallback confidence is high, do not mark a claim supported 
    # unless supporting_image_ids are valid and evidence requirements are met.
    if claim_status == "supported":
        if not evidence_met or not valid_image or not supporting_ids or supporting_ids == "none":
            claim_status = "not_enough_information"
            justification = "Evidence standard not met: supporting images are missing or invalid."
            supporting_ids = "none"

    # Finalise risk flags
    if has_history_risk and "manual_review_required" not in risk_flags:
        risk_flags.append("manual_review_required")
    if contradiction_detected and "claim_mismatch" not in risk_flags:
        risk_flags.append("claim_mismatch")
    if injection_detected and "manual_review_required" not in risk_flags:
        risk_flags.append("manual_review_required")

    # Deduplicate + filter to allowed set
    seen, clean = set(), []
    for f in risk_flags:
        if f not in seen and f in RISK_FLAGS_CHOICES:
            seen.add(f)
            clean.append(f)
    risk_flags_str = ";".join(clean) if clean else "none"

    severity       = assign_severity(issue_type, claim_status)

    result = {
        "evidence_standard_met":        evidence_met,
        "evidence_standard_met_reason": evidence_reason,
        "risk_flags":                   risk_flags_str,
        "issue_type":                   issue_type,
        "object_part":                  object_part,
        "claim_status":                 claim_status,
        "claim_status_justification":   justification,
        "supporting_image_ids":         supporting_ids,
        "valid_image":                  valid_image,
        "severity":                     severity,
    }
    logger.debug("Result: %s", result)
    return result
