# Evaluation Report — Multi-Modal Evidence Review

> Generated automatically by `code/evaluation/main.py`

## Summary

| Metric | Value |
|---|---|
| Total Evaluated | 20 |
| Composite Weighted Score | **68.0%** |

## Exact-Match Accuracy by Field

| Field | Accuracy | Correct/Total | Weight |
|---|---|---|---|
| evidence_standard_met | 90.0% `##################  ` | 18/20 | 10% |
| issue_type | 55.0% `###########         ` | 11/20 | 20% |
| object_part | 85.0% `#################   ` | 17/20 | 20% |
| claim_status | 60.0% `############        ` | 12/20 | 35% |
| valid_image | 90.0% `##################  ` | 18/20 | 5% |
| severity | 55.0% `###########         ` | 11/20 | 10% |

## Per-Field Miss Analysis

### evidence_standard_met — 2 miss(es)

| user_id | ground_truth | predicted |
|---|---|---|
| user_006 | False | True |
| user_032 | False | True |

### issue_type — 9 miss(es)

| user_id | ground_truth | predicted |
|---|---|---|
| user_005 | scratch | unknown |
| user_006 | unknown | crack |
| user_008 | broken_part | scratch |
| user_018 | crack | unknown |
| user_020 | none | unknown |
| user_030 | torn_packaging | broken_part |
| user_032 | unknown | missing_part |
| user_033 | unknown | crushed_packaging |
| user_034 | none | crushed_packaging |

### object_part — 3 miss(es)

| user_id | ground_truth | predicted |
|---|---|---|
| user_008 | front_bumper | hood |
| user_031 | package_side | item |
| user_033 | unknown | contents |

### claim_status — 8 miss(es)

| user_id | ground_truth | predicted |
|---|---|---|
| user_005 | contradicted | not_enough_information |
| user_006 | not_enough_information | supported |
| user_008 | contradicted | supported |
| user_018 | supported | not_enough_information |
| user_020 | contradicted | not_enough_information |
| user_032 | not_enough_information | supported |
| user_033 | contradicted | supported |
| user_034 | contradicted | supported |

### valid_image — 2 miss(es)

| user_id | ground_truth | predicted |
|---|---|---|
| user_008 | False | True |
| user_032 | False | True |

### severity — 9 miss(es)

| user_id | ground_truth | predicted |
|---|---|---|
| user_005 | low | unknown |
| user_006 | unknown | medium |
| user_008 | high | low |
| user_012 | low | medium |
| user_018 | medium | unknown |
| user_020 | none | unknown |
| user_032 | unknown | medium |
| user_033 | low | medium |
| user_034 | none | medium |

## claim_status Confusion Matrix

| GT \ Pred | supported | contradicted | not_enough_information |
|---|---|---|---|
| **supported** | 12 | 0 | 1 |
| **contradicted** | 3 | 0 | 2 |
| **not_enough_information** | 2 | 0 | 0 |

## System Architecture

| Component | Detail |
|---|---|
| **Inference** | Deterministic engine (no API required) |
| **Claim parsing** | Priority-ordered keyword tables (multilingual) |
| **Prompt injection** | Regex-based detection, 14+ patterns |
| **User history** | Risk-flag override rules (history_flags field) |
| **Evidence check** | File-system validation (existence + size) |
| **Fallback** | Per-row deterministic fallback, pipeline never crashes |
| **VLM upgrade path** | Set GEMINI_API_KEY or OPENAI_API_KEY to enable |

## Limitations

- Without a vision model, `claim_status` is conservative: we cannot confirm damage is actually visible in the image, so borderline cases stay `not_enough_information`.
- `evidence_standard_met=false` ground-truth rows that still have accessible image files on disk cannot be distinguished from valid submissions without image inspection.
- Multilingual conversations (Hindi, Spanish, Chinese) are partially handled via specific keyword expansions; coverage is limited to seen patterns.
