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
import hashlib
from code.schema import OutputSchema
from code.config import FALLBACK_ROW

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v3"
CACHE_FILE_PATH = os.path.join(os.path.dirname(__file__), "vlm_cache.json")

def load_vlm_cache():
    if os.path.exists(CACHE_FILE_PATH):
        try:
            with open(CACHE_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load VLM cache file: %s", e)
    return {}

def save_vlm_cache(cache):
    try:
        with open(CACHE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Failed to save VLM cache file: %s", e)

def compute_cache_key(user_claim, claim_object, image_paths, model_name, prompt_version):
    img_hashes = []
    for path in image_paths:
        if os.path.exists(path):
            hasher = hashlib.sha256()
            try:
                with open(path, "rb") as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)
                img_hashes.append(hasher.hexdigest())
            except Exception as e:
                img_hashes.append(f"error:{str(e)}")
        else:
            img_hashes.append("missing")
            
    paths_normalized = [os.path.normpath(p) for p in image_paths]
    
    key_str = f"{user_claim.strip()}||{claim_object.strip()}||{';'.join(img_hashes)}||{';'.join(paths_normalized)}||{model_name}||{prompt_version}"
    return hashlib.sha256(key_str.encode('utf-8')).hexdigest()


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


import time
from io import BytesIO
from PIL import Image

def resize_and_compress_image(path, max_dim=512, quality=70):
    """
    Resizes image to max_dim on the largest side while keeping aspect ratio.
    Compresses using JPEG format.
    Returns (bytes_data, len(bytes_data), original_dim, resized_dim)
    """
    img = Image.open(path)
    orig_dim = img.size
    
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        img = img.convert('RGB')
    
    w, h = orig_dim
    if max(w, h) > max_dim:
        if w > h:
            new_w = max_dim
            new_h = int(h * (max_dim / w))
        else:
            new_h = max_dim
            new_w = int(w * (max_dim / h))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    else:
        new_w, new_h = w, h

    out = BytesIO()
    img.save(out, format="JPEG", quality=quality)
    bytes_data = out.getvalue()
    return bytes_data, len(bytes_data), orig_dim, (new_w, new_h)


# ── Gemini ────────────────────────────────────────────────────────────────────
_last_request_time = 0.0

def process_with_gemini(prompt, image_paths, model_name="gemini-3.5-flash"):
    global _last_request_time
    start_time = time.time()
    
    # Respect rate limits: 5 RPM for 3.5-flash (12s interval), 15 RPM for 1.5-flash (4s interval)
    min_interval = 12.0 if "3.5" in model_name else 4.0
    elapsed = time.time() - _last_request_time
    if elapsed < min_interval:
        sleep_dur = min_interval - elapsed
        logger.info(f"Rate limiting active to prevent 429. Sleeping for {sleep_dur:.2f} seconds...")
        time.sleep(sleep_dur)
        start_time = time.time() # reset start time after sleeping
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Auth Error: GEMINI_API_KEY is not set.")
    
    logger.info(f"Using Gemini API Key (starts with): {api_key[:10]}...")
    client = genai.Client(api_key=api_key)

    contents = [prompt]
    total_size = 0
    valid_paths = 0
    dim_logs = []
    
    # Check if timeout occurs during preprocessing
    logger.info("Starting image preprocessing (resizing and compression)...")
    preprocess_start = time.time()
    
    for path in image_paths:
        if os.path.exists(path):
            try:
                data, size, orig_dim, new_dim = resize_and_compress_image(path)
                part = types.Part.from_bytes(data=data, mime_type="image/jpeg")
                contents.append(part)
                total_size += size
                valid_paths += 1
                dim_logs.append(f"{orig_dim} -> {new_dim} ({size} bytes)")
            except Exception as e:
                logger.error(f"Failed to process image {path}: {e}")

    preprocess_dur = time.time() - preprocess_start
    payload_size = len(prompt.encode('utf-8')) + total_size
    
    logger.info(f"Model: {model_name}")
    logger.info(f"Image Count: {valid_paths}")
    logger.info(f"Image Dimensions & Sizes: {dim_logs}")
    logger.info(f"Preprocessing Duration: {preprocess_dur:.2f}s")
    logger.info(f"Total Request Payload Size: {payload_size} bytes")
    logger.info(f"Request Start Time: {start_time}")
    logger.info("Dispatching API Request and waiting for response...")

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=OutputSchema,
                temperature=0.0,
            ),
        )
        end_time = time.time()
        _last_request_time = end_time
        latency = end_time - start_time
        logger.info(f"Request End Time: {end_time} | API Latency: {latency:.2f}s")
        
        raw_text = response.text
        logger.info(f"Raw API response (first 500 chars): {raw_text[:500]}")
        
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failure: {e}")
            raise

    except Exception as e:
        end_time = time.time()
        _last_request_time = end_time
        logger.info(f"Request End Time: {end_time} | Latency until failure: {end_time - start_time:.2f}s")
        error_str = str(e).lower()
        if "429" in error_str or "quota" in error_str or "exhausted" in error_str:
            logger.error("Quota/Rate-limit error detected.")
        elif "timeout" in error_str:
            logger.error("Timeout error detected during API generate_content execution.")
        elif "401" in error_str or "auth" in error_str:
            logger.error("Authentication error detected.")
        raise


# ── OpenAI ────────────────────────────────────────────────────────────────────
def process_with_openai(prompt, image_paths):
    start_time = time.time()
    model_name = "gpt-4o"
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Auth Error: OPENAI_API_KEY is not set.")
        
    logger.info(f"Using OpenAI API Key (starts with): {api_key[:10]}...")
    client = OpenAI(api_key=api_key, timeout=60.0, max_retries=1)

    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    total_size = 0
    valid_paths = []
    
    for path in image_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            total_size += size
            valid_paths.append(path)
            b64 = encode_image_base64(path)
            ext = path.split(".")[-1].lower()
            mime = f"image/{ext}" if ext in ["jpg", "jpeg", "png", "webp"] else "image/jpeg"
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            })

    payload_size = len(prompt.encode('utf-8')) + total_size
    logger.info(f"Model: {model_name} | Image Count: {len(valid_paths)} | Total Image Size: {total_size} bytes | Payload: {payload_size} bytes")
    logger.info(f"Request Start Time: {start_time}")

    try:
        response = client.beta.chat.completions.parse(
            model=model_name,
            messages=messages,
            response_format=OutputSchema,
            temperature=0.0,
        )
        end_time = time.time()
        logger.info(f"Request End Time: {end_time} | Duration: {end_time - start_time:.2f}s")
        
        raw_text = response.choices[0].message.content
        logger.info(f"Raw API response (first 500 chars): {raw_text[:500]}")
        
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failure: {e}")
            raise
            
    except Exception as e:
        end_time = time.time()
        logger.info(f"Request End Time: {end_time} | Duration: {end_time - start_time:.2f}s")
        error_str = str(e).lower()
        if "429" in error_str or "quota" in error_str or "rate_limit" in error_str:
            logger.error("Quota/Rate-limit error detected.")
        elif "timeout" in error_str:
            logger.error("Timeout error detected.")
        elif "401" in error_str or "auth" in error_str:
            logger.error("Authentication error detected.")
        raise

DAILY_QUOTA_EXHAUSTED = False
QUOTA_ERRORS_LOGGED = 0
TIMEOUT_ERRORS_LOGGED = 0

def process_with_retry(func, prompt, image_paths, max_retries=3):
    global DAILY_QUOTA_EXHAUSTED, QUOTA_ERRORS_LOGGED, TIMEOUT_ERRORS_LOGGED
    for attempt in range(1, max_retries + 1):
        try:
            return func(prompt, image_paths)
        except Exception as e:
            error_str = str(e).lower()
            if "quota exceeded" in error_str or "exceeded your current quota" in error_str or "billing details" in error_str:
                logger.error("Daily API quota limit exhausted. Switching to fail-fast mode.")
                DAILY_QUOTA_EXHAUSTED = True
                QUOTA_ERRORS_LOGGED += 1
                raise e
            if "429" in error_str or "quota" in error_str or "exhausted" in error_str:
                QUOTA_ERRORS_LOGGED += 1
                if attempt < max_retries:
                    wait_time = 15 * attempt
                    logger.warning(f"Rate limit hit. Retrying in {wait_time}s (Attempt {attempt}/{max_retries})")
                    time.sleep(wait_time)
                    continue
            if "timeout" in error_str:
                TIMEOUT_ERRORS_LOGGED += 1
                if attempt < max_retries:
                    logger.warning(f"Timeout occurred. Retrying in 5s (Attempt {attempt}/{max_retries})")
                    time.sleep(5)
                    continue
            if attempt < max_retries and "401" not in error_str:
                logger.warning(f"API Error: {e}. Retrying in 5s (Attempt {attempt}/{max_retries})")
                time.sleep(5)
                continue
            raise


# ── Main dispatcher ───────────────────────────────────────────────────────────
def analyze_claim_vlm(prompt, image_paths, row=None, req_df=None):
    global DAILY_QUOTA_EXHAUSTED
    
    # 1. Cache lookup if row is present
    cache_key = None
    if row is not None:
        user_claim = row.get("user_claim", "")
        claim_object = row.get("claim_object", "")
        cache_key = compute_cache_key(user_claim, claim_object, image_paths, "gemini-flash-latest", PROMPT_VERSION)
        cache = load_vlm_cache()
        if cache_key in cache:
            logger.info("Cache HIT for key %s", cache_key)
            return cache[cache_key]

    if DAILY_QUOTA_EXHAUSTED:
        logger.warning("Daily quota already exhausted. Falling back to deterministic engine immediately.")
        if row is not None:
            from code.deterministic_engine import analyze_claim_deterministic
            return analyze_claim_deterministic(row, image_paths, req_df)
        return FALLBACK_ROW.copy()

    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    result = None

    if gemini_key and gemini_key != "PASTE_YOUR_GEMINI_API_KEY_HERE" and HAS_GEMINI:
        try:
            logger.info("Attempting Gemini 1.5 Flash (gemini-flash-latest) VLM analysis with retry logic.")
            result = process_with_retry(lambda p, i: process_with_gemini(p, i, "gemini-flash-latest"), prompt, image_paths)
        except Exception as exc:
            logger.error("Gemini 1.5 Flash (gemini-flash-latest) permanently failed after retries: %s", exc)
            logger.info("Attempting Gemini 2.0 Flash (gemini-2.0-flash) VLM model...")
            try:
                result = process_with_retry(lambda p, i: process_with_gemini(p, i, "gemini-2.0-flash"), prompt, image_paths)
            except Exception as exc_light:
                logger.error("Gemini 2.0 Flash also permanently failed: %s", exc_light)
                if openai_key and openai_key != "PASTE_YOUR_OPENAI_API_KEY_HERE" and HAS_OPENAI:
                    logger.info("Falling back to OpenAI.")
                    try:
                        result = process_with_retry(process_with_openai, prompt, image_paths)
                    except Exception as exc2:
                        logger.error("OpenAI also permanently failed: %s", exc2)

    elif openai_key and openai_key != "PASTE_YOUR_OPENAI_API_KEY_HERE" and HAS_OPENAI:
        try:
            logger.info("Attempting OpenAI VLM analysis with retry logic.")
            result = process_with_retry(process_with_openai, prompt, image_paths)
        except Exception as exc:
            logger.error("OpenAI permanently failed after retries: %s", exc)

    if result is not None:
        # Cache the successful result
        if cache_key is not None:
            cache = load_vlm_cache()
            cache[cache_key] = result
            save_vlm_cache(cache)
            logger.info("Saved VLM response to cache under key %s", cache_key)
        return result

    logger.warning("No valid VLM API succeeded. Falling back to deterministic engine gracefully.")
    if row is not None:
        from code.deterministic_engine import analyze_claim_deterministic
        return analyze_claim_deterministic(row, image_paths, req_df)

    logger.error("Deterministic engine unavailable (row not passed). Using static fallback.")
    return FALLBACK_ROW.copy()
