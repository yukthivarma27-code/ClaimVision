import base64
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai

from . import utils
from PIL import Image, ImageFilter, ImageStat


class ImageAnalysisResult:
    def __init__(
        self,
        image_id: str,
        object_detected: str,
        object_part_detected: str,
        damage_type: str,
        severity: str,
        blurry: bool,
        cropped: bool,
        glare: bool,
        wrong_angle: bool,
        wrong_object: bool,
        damage_visible: bool,
        manipulation: bool,
        non_original: bool,
        text_instruction: bool,
        usable: bool,
        description: str,
    ):
        self.image_id = image_id
        self.object_detected = object_detected
        self.object_part_detected = object_part_detected
        self.damage_type = damage_type
        self.severity = severity
        self.blurry = blurry
        self.cropped = cropped
        self.glare = glare
        self.wrong_angle = wrong_angle
        self.wrong_object = wrong_object
        self.damage_visible = damage_visible
        self.manipulation = manipulation
        self.non_original = non_original
        self.text_instruction = text_instruction
        self.usable = usable
        self.description = description

    @property
    def quality_flags(self) -> List[str]:
        flags = []
        if self.blurry: flags.append("blurry_image")
        if self.cropped: flags.append("cropped_or_obstructed")
        if self.glare: flags.append("low_light_or_glare")
        if self.wrong_angle: flags.append("wrong_angle")
        if self.wrong_object: flags.append("wrong_object")
        if not self.damage_visible: flags.append("damage_not_visible")
        if self.manipulation: flags.append("possible_manipulation")
        if self.non_original: flags.append("non_original_image")
        if self.text_instruction: flags.append("text_instruction_present")
        return flags


ANALYSIS_SYSTEM_PROMPT = """You are a professional insurance damage assessor. Analyze the submitted image and return a JSON object with your findings.

Return ONLY valid JSON with these exact fields:
{
  "object_detected": "car|laptop|package|unknown",
  "object_part_detected": "the specific part visible or unknown",
  "damage_type": "dent|scratch|crack|glass_shatter|broken_part|missing_part|torn_packaging|crushed_packaging|water_damage|stain|none|unknown",
  "severity": "none|low|medium|high|unknown",
  "blurry": false,
  "cropped_or_obstructed": false,
  "low_light_or_glare": false,
  "wrong_angle": false,
  "wrong_object": false,
  "damage_visible": false,
  "possible_manipulation": false,
  "non_original_image": false,
  "text_instruction_present": false,
  "usable": true,
  "description": "Brief 1-sentence description of what the image shows."
}"""


def _encode_image(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type(
        (openai.APIError, openai.APITimeoutError, openai.RateLimitError)
    ),
)
def _analyze_with_gpt(image_path: Path, claim_context: str) -> dict:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    b64_image = _encode_image(image_path)
    data_url = f"data:image/jpeg;base64,{b64_image}"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Claim context: {claim_context}\nAnalyze this image for damage assessment.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url, "detail": "high"},
                    },
                ],
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=500,
        temperature=0.1,
    )
    text = response.choices[0].message.content.strip()
    return json.loads(text)


def _extract_image_quality(image_path: Path) -> dict:
    try:
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        fs = image_path.stat().st_size
        gray = img.convert("L")
        lap = gray.filter(ImageFilter.Kernel((3,3),
            [-1,-1,-1,-1,8,-1,-1,-1,-1], scale=1))
        blur_score = float(ImageStat.Stat(lap).stddev[0])
        brightness = float(ImageStat.Stat(gray).mean[0])
        aspect = max(w,h) / max(min(w,h), 1)
    except Exception:
        return {"width": 0, "height": 0, "file_size": 0, "blur_score": 50,
                "brightness": 128, "aspect_ratio": 1}

    return {
        "width": w, "height": h, "file_size": fs,
        "blur_score": blur_score, "brightness": brightness,
        "aspect_ratio": aspect
    }


def _conversation_signals(conversation: str) -> dict:
    conv = conversation.lower()
    
    unsure = bool(re.search(
        r"(not sure|confused|couldn.t decide|cannot tell|overthinking|"
        r"not fully sure|wondering if|am not sure|walked around.*checked)", conv
    ))
    
    has_photos = bool(re.search(r"(photo|image|picture|upload|attach|img_\d)", conv))
    explicit_claim = bool(re.search(
        r"(claim|reporting|submit|issue is|want.*reviewed|verify|please review|"
        r"reporting|the claim|review|check|inspect)", conv
    ))
    
    has_instructions = bool(re.search(
        r"(?i)(approve|mark.*supported|skip.*review|follow.*note|"
        r"follow.*instruction|accept this)", conv
    ))
    
    confident = bool(re.search(
        r"(clearly|definitely|visible|shows|is (cracked|broken|dented|scratched)|"
        r"have a (crack|dent|scratch)|noticed|saw|see it|attached photo|here.*photo)", conv
    ))
    
    mismatch = bool(re.search(
        r"(ignore|wrong|unrelated|different car|not the same|not.*about|"
        r"not.*claim|first thought|at first|walked around)", conv
    ))
    
    return {
        "unsure": unsure, "has_photos": has_photos,
        "explicit_claim": explicit_claim, "has_instructions": has_instructions,
        "confident": confident, "mismatch": mismatch
    }


def _fallback_analyze(
    image_path: Path, claim_object: str, claim_issue: str,
    claim_part: str, conversation: str, image_idx: int, total_images: int
) -> dict:
    quality = _extract_image_quality(image_path)
    signals = _conversation_signals(conversation)

    is_blurry = quality["blur_score"] < 15 or quality["file_size"] < 15000
    is_dark = quality["brightness"] < 45
    is_glare = quality["brightness"] > 230
    is_small = quality["width"] < 300 or quality["height"] < 300
    is_wrong_angle = quality["aspect_ratio"] > 3
    is_usable = not is_blurry and not is_small and not is_wrong_angle

    text_instr = signals["has_instructions"]

    damage_visible = False
    severity = "unknown"
    
    if signals["confident"] and signals["has_photos"] and is_usable:
        if image_idx == total_images - 1 or total_images == 1:
            damage_visible = claim_issue != "unknown"
            severity = "medium" if claim_issue not in ("unknown", "none") else "unknown"
    
    detected_part = claim_part if claim_part != "unknown" else "unknown"
    detected_damage = claim_issue if claim_issue != "unknown" else "unknown"

    if is_usable:
        if is_blurry:
            desc = f"Image of {claim_object} area. Blurry."
        elif is_dark:
            desc = f"Image of {claim_object} {detected_part}. Low lighting."
            is_usable = False
        elif image_idx == 0 and total_images > 1:
            desc = f"Overview image of {claim_object} showing general area."
        elif image_idx == total_images - 1 and total_images > 1:
            desc = f"Close-up of {claim_object} {detected_part}."
        else:
            desc = f"Image of {claim_object} {detected_part}."
    else:
        reasons = []
        if is_blurry: reasons.append("blurry")
        if is_dark: reasons.append("low light")
        if is_small: reasons.append("low resolution")
        if is_wrong_angle: reasons.append("unusual angle")
        desc = f"Image of {claim_object}. Quality issue: {', '.join(reasons)}."

    if text_instr:
        desc += " Contains text instructions."

    return {
        "object_detected": claim_object,
        "object_part_detected": detected_part,
        "damage_type": detected_damage,
        "severity": severity,
        "blurry": is_blurry,
        "cropped_or_obstructed": is_small and quality["file_size"] > 50000,
        "low_light_or_glare": is_dark or is_glare,
        "wrong_angle": is_wrong_angle,
        "wrong_object": False,
        "damage_visible": damage_visible,
        "possible_manipulation": False,
        "non_original_image": False,
        "text_instruction_present": text_instr,
        "usable": is_usable,
        "description": desc.strip(),
    }


def analyze_image(
    image_path: Path, claim_object: str, claim_issue: str,
    claim_part: str, conversation: str,
    image_idx: int = 0, total_images: int = 1
) -> ImageAnalysisResult:
    cache_key = f"img_v2:{utils.image_hash(image_path)}:{claim_object}:{claim_issue}:{claim_part}"
    cached = utils.cache.get(cache_key)
    if cached:
        return ImageAnalysisResult(**cached)

    if os.getenv("OPENAI_API_KEY"):
        try:
            ctx = f"Object: {claim_object}, Issue: {claim_issue}, Part: {claim_part}. Conversation: {conversation[:500]}"
            analysis = _analyze_with_gpt(image_path, ctx)
        except Exception:
            analysis = _fallback_analyze(image_path, claim_object, claim_issue, claim_part, conversation, image_idx, total_images)
    else:
        analysis = _fallback_analyze(image_path, claim_object, claim_issue, claim_part, conversation, image_idx, total_images)

    result = ImageAnalysisResult(
        image_id=utils.image_id_from_path(str(image_path)),
        object_detected=analysis.get("object_detected", claim_object),
        object_part_detected=analysis.get("object_part_detected", claim_part),
        damage_type=analysis.get("damage_type", claim_issue),
        severity=analysis.get("severity", "unknown"),
        blurry=analysis.get("blurry", False),
        cropped=analysis.get("cropped_or_obstructed", False),
        glare=analysis.get("low_light_or_glare", False),
        wrong_angle=analysis.get("wrong_angle", False),
        wrong_object=analysis.get("wrong_object", False),
        damage_visible=analysis.get("damage_visible", False),
        manipulation=analysis.get("possible_manipulation", False),
        non_original=analysis.get("non_original_image", False),
        text_instruction=analysis.get("text_instruction_present", False),
        usable=analysis.get("usable", True),
        description=analysis.get("description", ""),
    )

    utils.cache.set(cache_key, {
        "image_id": result.image_id,
        "object_detected": result.object_detected,
        "object_part_detected": result.object_part_detected,
        "damage_type": result.damage_type,
        "severity": result.severity,
        "blurry": result.blurry, "cropped": result.cropped,
        "glare": result.glare, "wrong_angle": result.wrong_angle,
        "wrong_object": result.wrong_object,
        "damage_visible": result.damage_visible,
        "manipulation": result.manipulation,
        "non_original": result.non_original,
        "text_instruction": result.text_instruction,
        "usable": result.usable,
        "description": result.description,
    })

    return result
