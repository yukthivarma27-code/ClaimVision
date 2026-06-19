"""
live_predict.py
─────────────────────────────────────────────────────────────────────────────
Entry point for the "Try Your Own Claim" frontend feature.
Reads JSON from stdin, runs the strict multi-stage validation logic,
and outputs the result JSON to stdout.

Requires an API key. Uses strict object matching.
"""
import sys
import os
import json
import logging
import pandas as pd

# Suppress existing logs to stdout to not break JSON parsing
logging.getLogger().setLevel(logging.CRITICAL)

# ── Path bootstrap ────────────────────────────────────────────────────────────
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from code.vlm_client import HAS_GEMINI, HAS_OPENAI, analyze_claim_vlm
from code.data_loader import load_data, get_requirements_for_object
from code.prompts import build_prompt
from code.pipeline import validate_and_format_row

STRICT_LIVE_RULES = """

==================================================
STRICT OBJECT VALIDATION RULES FOR LIVE UPLOADS (MANDATORY):
==================================================
1. DETECT THE PRIMARY OBJECT: Identify the primary object in the image.
2. SUPPORTED OBJECTS ONLY: The Try Your Own Claim feature ONLY supports: car, laptop, package.
3. REJECT UNSUPPORTED OBJECTS: If the image contains a person, face, animal, pet, motorcycle, bicycle, furniture, television, mobile phone, screenshot, document, meme, landscape, or ANY other random object NOT listed in step 2:
   - You MUST immediately reject it.
   - Return exactly: issue_type=unknown, object_part=unknown, claim_status=not_enough_information, risk_flags=wrong_object, valid_image=false.
4. CLAIM OBJECT CROSS-CHECK: Verify that the claimed object matches the visible image object.
   - Example: If the claim is "car" but the image shows a "laptop" or a "dog", reject it.
   - Return exactly: claim_status=not_enough_information, risk_flags=wrong_object, valid_image=false.
   
==================================================
MULTI-STAGE VERIFICATION:
==================================================
Images remain the primary source of truth. Do NOT blindly trust the claim text.
Cross-check image findings against the claim.
If damage is not visible: issue_type=unknown, claim_status=not_enough_information.
If the relevant area is clearly visible and healthy: issue_type=none, claim_status=contradicted, severity=none.
If the claim mentions "dent" but the image only shows a "scratch", return issue_type=scratch, claim_status=contradicted. Never invent damage.
"""

def run():
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            sys.stderr.write("Empty input payload\n")
            print(json.dumps({"error": "Empty input payload"}))
            return

        payload = json.loads(input_data)
        
        # Check API keys as requested by the user
        gemini_key = os.environ.get("GEMINI_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")
        
        if not ((gemini_key and HAS_GEMINI) or (openai_key and HAS_OPENAI)):
            sys.stderr.write("API Key missing.\n")
            print(json.dumps({
                "error": "Vision API key not configured. Try Your Own Claim requires GEMINI_API_KEY or OPENAI_API_KEY."
            }))
            return

        claim_object = payload.get("claim_object", "unknown")

        # Construct a synthetic row that mimics claims.csv merged with user_history.csv
        row = pd.Series({
            "user_id": payload.get("user_id", "demo_user"),
            "image_paths": payload.get("image_paths", ""),
            "user_claim": payload.get("user_claim", ""),
            "claim_object": claim_object,
            "past_claim_count": 0,
            "last_90_days_claim_count": 0,
            "rejected_claim": False,
            "history_flags": "none",
            "history_summary": "First time user.",
        })

        # Load evidence requirements
        try:
            _, req_df = load_data("claims.csv")
            obj_req = get_requirements_for_object(req_df, claim_object)
        except Exception as e:
            sys.stderr.write(f"Failed to load req_df: {e}\n")
            # fallback empty df if dataset isn't fully available
            obj_req = pd.DataFrame()

        # Build original prompt and append strict live rules
        base_prompt = build_prompt(row, obj_req)
        strict_prompt = base_prompt + STRICT_LIVE_RULES

        image_paths = [p.strip() for p in str(row["image_paths"]).split(";") if p.strip()]

        # Run core pipeline directly via VLM client
        sys.stderr.write(f"Running VLM analysis for object: {claim_object} with images: {image_paths}\n")
        raw_vlm_output = analyze_claim_vlm(
            prompt=strict_prompt,
            image_paths=image_paths,
            row=row.to_dict(),
            req_df=obj_req,
        )

        result = validate_and_format_row(row, claim_object, raw_vlm_output)
        
        # Output clean JSON to stdout
        sys.stdout.write(json.dumps(result))
        sys.stdout.write("\n")
        
    except Exception as e:
        sys.stderr.write(f"Unhandled Python exception: {e}\n")
        print(json.dumps({"error": f"Internal python exception: {str(e)}"}))

if __name__ == "__main__":
    run()
