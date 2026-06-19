"""
vlm_client.py
─────────────────────────────────────────────────────────────────────────────
Configurable VLM client.

Priority order:
  1. Gemini (if GEMINI_API_KEY present and google-genai installed)
  2. OpenAI (if OPENAI_API_KEY present and openai installed)
  3. Deterministic fallback engine (always available, no API required)
"""
import os
import json
import base64
import logging
from code.schema import OutputSchema
from code.config import FALLBACK_ROW

logger = logging.getLogger(__name__)

# ── SDK availability probes ───────────────────────────────────────────────────
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def encode_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# ── Gemini ────────────────────────────────────────────────────────────────────
def process_with_gemini(prompt, image_paths):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    from PIL import Image
    contents = [prompt]
    for path in image_paths:
        if os.path.exists(path):
            img = Image.open(path)
            contents.append(img)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=OutputSchema,
            temperature=0.0,
        ),
    )
    return json.loads(response.text)


# ── OpenAI ────────────────────────────────────────────────────────────────────
def process_with_openai(prompt, image_paths):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    for path in image_paths:
        if os.path.exists(path):
            b64 = encode_image_base64(path)
            ext = path.split(".")[-1].lower()
            mime = f"image/{ext}" if ext in ["jpg", "jpeg", "png", "webp"] else "image/jpeg"
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            })

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        response_format=OutputSchema,
        temperature=0.0,
    )
    return json.loads(response.choices[0].message.content)


# ── Main dispatcher ───────────────────────────────────────────────────────────
def analyze_claim_vlm(prompt, image_paths, row=None, req_df=None):
    """
    Try VLM APIs in order; fall back to the deterministic engine when no key
    is configured or all API calls fail.

    Parameters
    ----------
    prompt      : str   – formatted prompt string
    image_paths : list  – absolute paths to submitted images
    row         : dict  – merged claim + history row (for deterministic engine)
    req_df      : DataFrame – evidence requirements (for deterministic engine)
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    # ── 1. Gemini ────────────────────────────────────────────────────────────
    if gemini_key and HAS_GEMINI:
        try:
            logger.info("Attempting Gemini VLM analysis.")
            return process_with_gemini(prompt, image_paths)
        except Exception as exc:
            logger.warning("Gemini failed: %s", exc)
            if openai_key and HAS_OPENAI:
                logger.info("Falling back to OpenAI.")
                try:
                    return process_with_openai(prompt, image_paths)
                except Exception as exc2:
                    logger.warning("OpenAI also failed: %s", exc2)

    # ── 2. OpenAI only ───────────────────────────────────────────────────────
    elif openai_key and HAS_OPENAI:
        try:
            logger.info("Attempting OpenAI VLM analysis.")
            return process_with_openai(prompt, image_paths)
        except Exception as exc:
            logger.warning("OpenAI failed: %s", exc)

    # ── 3. Deterministic fallback ─────────────────────────────────────────────
    logger.info("No VLM API available. Using deterministic fallback engine.")
    if row is not None:
        from code.deterministic_engine import analyze_claim_deterministic
        return analyze_claim_deterministic(row, image_paths, req_df)

    # Last-resort static fallback (should not normally be reached)
    logger.error("Deterministic engine unavailable (row not passed). Using static fallback.")
    return FALLBACK_ROW.copy()
