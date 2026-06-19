import re
from typing import Tuple

ISSUE_KEYWORDS = {
    "dent": ["dent", "dented", "dinting", "dab gaya", "hail dent"],
    "scratch": ["scratch", "scratched", "scrape", "scraped", "mark", "scrape lag", "paint issue", "scratched"],
    "crack": ["crack", "cracked", "crack pattern", "fracture"],
    "glass_shatter": ["shatter", "shattered", "glass shatter", "windshield shatter"],
    "broken_part": ["broken", "broke", "breakage", "damaged part", "snapped", "toot gaya", "broken part", "damaged"],
    "missing_part": ["missing", "lost", "fell off", "came off", "faltan", "keycaps came off"],
    "torn_packaging": ["torn", "tear", "ripped", "torn-open", "torn open", "phati hui", "open package"],
    "crushed_packaging": ["crush", "crushed", "crushing", "squashed", "dab gaya tha", "corner crushed"],
    "water_damage": ["water damage", "wet", "water", "moisture", "damp", "liquid", "spilled water", "liquid damage"],
    "stain": ["stain", "stained", "oily", "oil stain", "mark", "dark oily"],
}

CAR_PARTS = {
    "front_bumper": ["front bumper", "bumper front", "front bumper"],
    "rear_bumper": ["rear bumper", "back bumper", "bumper back", "back bumper", "parachoques trasero", "atras"],
    "door": ["door", "door panel", "left side door"],
    "hood": ["hood", "bonnet"],
    "windshield": ["windshield", "front glass", "windscreen", "front screen"],
    "side_mirror": ["side mirror", "mirror", "wing mirror", "side mirror"],
    "headlight": ["headlight", "head light", "front light", "left headlight"],
    "taillight": ["taillight", "tail light", "back light", "rear light"],
    "fender": ["fender"],
    "quarter_panel": ["quarter panel"],
    "body": ["body", "body panel", "car body", "panel", "car body"],
}

LAPTOP_PARTS = {
    "screen": ["screen", "display", "monitor", "pantalla", "display area", "display glass"],
    "keyboard": ["keyboard", "key", "keys", "teclas", "keycaps"],
    "trackpad": ["trackpad", "touchpad", "palm-rest", "palm rest"],
    "hinge": ["hinge"],
    "lid": ["lid", "outer lid", "cover"],
    "corner": ["corner", "laptop corner", "side edge"],
    "port": ["port", "usb port", "charging port"],
    "base": ["base", "bottom"],
    "body": ["body", "laptop body", "casing", "chassis", "outer body"],
}

PACKAGE_PARTS = {
    "box": ["box", "cardboard box", "shipping box", "delivery box"],
    "package_corner": ["corner", "package corner", "box corner"],
    "package_side": ["side", "surface", "package surface", "package side"],
    "seal": ["seal", "tape", "flap", "seal area", "seal wali side"],
    "label": ["label", "shipping label", "unreadable"],
    "contents": ["contents", "item inside", "inside item", "product inside", "missing item", "inside the package"],
    "item": ["item", "product", "broken item", "inside item"],
}

OBJECT_PARTS = {
    "car": CAR_PARTS,
    "laptop": LAPTOP_PARTS,
    "package": PACKAGE_PARTS,
}


def extract_claim(conversation: str, claim_object: str) -> Tuple[str, str]:
    conv_lower = conversation.lower()
    issue_type = _find_issue_type(conv_lower)
    if claim_object in OBJECT_PARTS:
        object_part = _find_object_part(conv_lower, claim_object)
    else:
        object_part = "unknown"
    return issue_type, object_part


def _find_issue_type(text: str) -> str:
    scores = {}
    for issue, keywords in ISSUE_KEYWORDS.items():
        base_score = 0
        for kw in keywords:
            if kw in text:
                # Score by keyword length (longer = more specific)
                base_score += len(kw)
        if base_score > 0:
            scores[issue] = base_score

    if not scores:
        if any(w in text for w in ["damage", "damaged", "issue", "problem"]):
            return "unknown"
        return "unknown"

    return max(scores, key=scores.get)


def _find_object_part(text: str, claim_object: str) -> str:
    parts_dict = OBJECT_PARTS.get(claim_object, {})
    scores = {}

    for part, keywords in parts_dict.items():
        score = 0
        for kw in keywords:
            if kw in text:
                score += len(kw)
        if score > 0:
            scores[part] = score

    if not scores:
        return "unknown"

    return max(scores, key=scores.get)
