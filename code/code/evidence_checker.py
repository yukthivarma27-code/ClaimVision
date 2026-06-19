import pandas as pd
from typing import Tuple, List

from . import utils

REQUIREMENTS_CACHE = None

def _load_requirements() -> pd.DataFrame:
    global REQUIREMENTS_CACHE
    if REQUIREMENTS_CACHE is not None:
        return REQUIREMENTS_CACHE
    path = utils.DATASET_DIR / "evidence_requirements.csv"
    REQUIREMENTS_CACHE = pd.read_csv(path)
    return REQUIREMENTS_CACHE

def check_evidence(
    claim_object: str,
    issue_type: str,
    image_count: int,
    image_qualities: List[dict],
) -> Tuple[bool, str]:
    reqs = _load_requirements()
    relevant = reqs[
        (reqs["claim_object"] == claim_object) | (reqs["claim_object"] == "all")
    ]

    min_evidence_met = True
    reasons = []

    has_clear = any(q.get("usable", False) for q in image_qualities)
    has_blurry = any(q.get("blurry", False) for q in image_qualities)

    if image_count == 0:
        return False, "No images submitted."

    for _, req in relevant.iterrows():
        applies = str(req.get("applies_to", "")).lower()
        evidence_text = str(req.get("minimum_image_evidence", ""))

        if "general" in applies or "all" in applies or "reviewability" in applies:
            if not has_clear:
                min_evidence_met = False
                reasons.append("No clear usable image found.")

        if "dent or scratch" in applies or claim_object == "car":
            if issue_type in ("dent", "scratch") and not has_clear:
                min_evidence_met = False
                reasons.append("Surface damage cannot be assessed without a clear image.")
            else:
                reasons.append("Relevant object part visible for surface assessment.")

        if issue_type in ("crack", "broken_part", "missing_part", "glass_shatter"):
            if not has_clear:
                min_evidence_met = False
                reasons.append("Cannot inspect cracks or breakage without clear visibility.")
            else:
                reasons.append("Damage region visible for crack/breakage inspection.")

        if claim_object == "package" and issue_type in ("crushed_packaging", "torn_packaging"):
            if not has_clear:
                min_evidence_met = False
                reasons.append("Package exterior not clearly visible.")
            else:
                reasons.append("Package exterior visible for damage inspection.")

    if has_blurry and has_clear:
        reasons.insert(0, "Some images are blurry, but at least one clear image exists.")

    if min_evidence_met:
        return True, "; ".join(reasons) if reasons else "Evidence requirements satisfied."
    else:
        return False, "; ".join(reasons) if reasons else "Evidence requirements not met."
