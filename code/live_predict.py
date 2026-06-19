"""
live_predict.py
─────────────────────────────────────────────────────────────────────────────
Entry point for the "Try Your Own Claim" frontend feature.
Reads JSON from stdin, runs the existing pipeline validation on it,
and outputs the result JSON to stdout.

Requires an API key. Re-uses the existing pipeline to ensure exact parity.
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

from code.pipeline import process_single_claim
from code.data_loader import load_data, get_requirements_for_object
from code.vlm_client import HAS_GEMINI, HAS_OPENAI

def run():
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            print(json.dumps({"error": "Empty input payload"}))
            return

        payload = json.loads(input_data)
        
        # Check API keys as requested by the user
        gemini_key = os.environ.get("GEMINI_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")
        
        if not ((gemini_key and HAS_GEMINI) or (openai_key and HAS_OPENAI)):
            print(json.dumps({
                "error": "Vision API key not configured. Try Your Own Claim requires GEMINI_API_KEY or OPENAI_API_KEY."
            }))
            return

        # Construct a synthetic row that mimics claims.csv merged with user_history.csv
        row = pd.Series({
            "user_id": payload.get("user_id", "demo_user"),
            "image_paths": payload.get("image_paths", ""),
            "user_claim": payload.get("user_claim", ""),
            "claim_object": payload.get("claim_object", "car"),
            "past_claim_count": 0,
            "last_90_days_claim_count": 0,
            "rejected_claim": False,
            "history_flags": "none",
            "history_summary": "First time user.",
        })

        # Load evidence requirements
        _, req_df = load_data("claims.csv") # We just need req_df
        obj_req = get_requirements_for_object(req_df, row["claim_object"])

        # Run core pipeline
        result = process_single_claim(row, obj_req, ROOT_DIR)
        
        # Output clean JSON
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    run()
