# Multimodal Verification Pipeline Optimization Walkthrough

We have successfully optimized the multi-modal evidence review pipeline under strict rate/quota limits and fully addressed all 8 corrections requested.

## Key Changes Made

### 1. Robust API Quota Attribution
- Modified error handling in [vlm_client.py](file:///c:/Users/yukth/OneDrive/Desktop/orchestrate/code/vlm_client.py) to explicitly track `429 Too Many Requests` (`RESOURCE_EXHAUSTED`) exceptions.
- Quota errors are only reported when they are proven and logged directly from the API endpoint.

### 2. Multi-Variable Cache Key Implementation
- Implemented a secure JSON cache layer stored in [vlm_cache.json](file:///c:/Users/yukth/OneDrive/Desktop/orchestrate/code/vlm_cache.json).
- The cache key uniquely hashes a combination of:
  - `user_claim`
  - `claim_object`
  - SHA-256 content hashes of all referenced image files
  - Resolved image file paths
  - `model_name`
  - `prompt_version`
- Migrated prior successful VLM runs from the previous `output.csv` using this precise hashing method, avoiding any user ID collision bugs.

### 3. Comprehensive Deterministic Confidence Metric
- Added `calculate_deterministic_confidence` in [deterministic_engine.py](file:///c:/Users/yukth/OneDrive/Desktop/orchestrate/code/deterministic_engine.py).
- The confidence score is calculated mathematically by evaluating:
  - Image file existence on disk (deducts if missing)
  - Image quantity (reduces score for multiple images to route them to VLM)
  - Base complexity of the object type (car, laptop, package)
  - Package contents/item requirements (highly complex, reduces confidence)
  - Claims ambiguity (generic words like "damaged", "issue", "ruined")
  - Conversation uncertainty and contradictions
  - History risk flags (`user_history_risk`, `manual_review_required`)

### 4. Sorted VLM Candidate Routing
- Centralized candidate evaluation in [main.py](file:///c:/Users/yukth/OneDrive/Desktop/orchestrate/code/main.py).
- Grouped rows into cache hits, high-confidence fallback (`>= 0.85`), and low-confidence VLM candidates.
- Sorted VLM candidates by confidence ascending to prioritize routing to VLM for the most ambiguous/critical claims first.
- Bypassed VLM immediately once the API key's daily limit was exhausted.

### 5. String Boolean Fix & Supported Claim Enforcements
- Wrote robust boolean string conversions in [pipeline.py](file:///c:/Users/yukth/OneDrive/Desktop/orchestrate/code/pipeline.py) (preventing `bool("false")` from parsing as `True`).
- Added strict checks in [deterministic_engine.py](file:///c:/Users/yukth/OneDrive/Desktop/orchestrate/code/deterministic_engine.py) to never mark a claim supported unless evidence standards are met and `supporting_image_ids` are valid.

### 6. Validation and Ordering Pass
- Re-aligned all processed rows to match the original index order from `claims.csv`.
- Validated all 44 rows against allowed choices, schema types, non-blank constraints, and column order before saving.

---

## Validation and Verification

Both the main pipeline and evaluation test suite run successfully:

```powershell
# Execute main prediction pipeline
py code/main.py

# Execute sample evaluation main script
py code/evaluation/main.py
```

### Final Multi-Modal Pipeline Audit Report

```text
==================================================
FINAL MULTIMODAL PIPELINE AUDIT REPORT
==================================================
Total Rows Processed       : 44
VLM-processed Rows (Total) : 5
  - Active VLM Successes   : 0
  - Permanent Cache Hits   : 5
Fallback-processed Rows   : 39
Quota/Rate-limit Errors    : 2
Timeout Errors             : 0
Output Validation Status   : Passed
==================================================
```

Validation of the final `output.csv` has successfully **Passed** all check passes.
