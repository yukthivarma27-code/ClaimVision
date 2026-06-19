import os

# Paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(ROOT_DIR, 'dataset')
OUTPUT_CSV_PATH = os.path.join(ROOT_DIR, 'output.csv')

# Allowed Values
CLAIM_STATUS_CHOICES = ["supported", "contradicted", "not_enough_information"]
ISSUE_TYPE_CHOICES = ["dent", "scratch", "crack", "glass_shatter", "broken_part", "missing_part", "torn_packaging", "crushed_packaging", "water_damage", "stain", "none", "unknown"]
OBJECT_PART_CAR_CHOICES = ["front_bumper", "rear_bumper", "door", "hood", "windshield", "side_mirror", "headlight", "taillight", "fender", "quarter_panel", "body", "unknown"]
OBJECT_PART_LAPTOP_CHOICES = ["screen", "keyboard", "trackpad", "hinge", "lid", "corner", "port", "base", "body", "unknown"]
OBJECT_PART_PACKAGE_CHOICES = ["box", "package_corner", "package_side", "seal", "label", "contents", "item", "unknown"]
RISK_FLAGS_CHOICES = ["none", "blurry_image", "cropped_or_obstructed", "low_light_or_glare", "wrong_angle", "wrong_object", "wrong_object_part", "damage_not_visible", "claim_mismatch", "possible_manipulation", "non_original_image", "text_instruction_present", "user_history_risk", "manual_review_required"]
SEVERITY_CHOICES = ["none", "low", "medium", "high", "unknown"]

REQUIRED_COLUMNS = [
    "user_id", "image_paths", "user_claim", "claim_object",
    "evidence_standard_met", "evidence_standard_met_reason", "risk_flags",
    "issue_type", "object_part", "claim_status", "claim_status_justification",
    "supporting_image_ids", "valid_image", "severity"
]

FALLBACK_ROW = {
    "evidence_standard_met": False,
    "evidence_standard_met_reason": "API Failure or parsing error",
    "risk_flags": "manual_review_required",
    "issue_type": "unknown",
    "object_part": "unknown",
    "claim_status": "not_enough_information",
    "claim_status_justification": "API Failure occurred during processing.",
    "supporting_image_ids": "none",
    "valid_image": False,
    "severity": "unknown"
}
