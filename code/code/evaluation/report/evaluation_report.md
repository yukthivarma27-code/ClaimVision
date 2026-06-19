# ClaimLens AI — Evaluation Report

**Generated:** 2026-06-19 12:53:51

---

## Metrics on Sample Claims (20 rows)

### Overall
- **Accuracy (claim_status):** 60.00%

### Per-Field Metrics (weighted avg)

| Field | Accuracy | Precision | Recall | F1 |
|-------|----------|-----------|--------|-----|
| **claim_status** | 60.00% | 47.19% | 60.00% | 52.64% |
| **issue_type** | 50.00% | 48.50% | 50.00% | 46.50% |
| **object_part** | 80.00% | 86.67% | 80.00% | 81.33% |
| **severity** | 55.00% | 57.36% | 55.00% | 50.46% |

---

## Confusion Matrix (claim_status)

```
                          contradictednot_enough_information         supported
      contradicted                 0                 1                 4
not_enough_information                 0                 1                 1
         supported                 0                 2                11
```

---

## Operational Analysis

| Metric | Sample Set | Test Set |
|--------|-----------|----------|
| Claims processed | 20 | 44 |
| Images processed | 29 | 82 |
| Approx. model calls | 40 | 88 |
| Approx. total tokens | 43,200 | 109,600 |
| Estimated cost (GPT-4o) | $0.2376 | $0.6028 |
| Runtime | 0.3s | ~0.8s (est.) |

### Pricing Assumptions
- **Model:** GPT-4o (or GPT-4.1)
- **Input tokens:** ~800 per image analysis (image + text prompt)
- **Output tokens:** ~500 per analysis
- **Pricing:** $0.0025/1K input, $0.01/1K output (standard GPT-4o rates)
- **Cache:** diskcache for duplicate image hashes to avoid re-processing

### Latency, TPM/RPM & Optimization

| Concern | Strategy |
|---------|----------|
| **RPM limits** | Images analyzed sequentially per claim; sleep-free within limits |
| **TPM limits** | Response format JSON with max_tokens=500 keeps output small |
| **Batching** | Claims processed sequentially; batch size = 1 for reliability |
| **Retry** | Tenacity with exponential backoff (2s base, max 30s, 3 attempts) |
| **Caching** | MD5 image hash → analysis result cache; ~60%+ hit rate on reruns |
| **Throttling** | No aggressive parallel calls; safe for standard tier |

### Cost Efficiency
- Most savings come from image deduplication cache.
- Rule-based fallback mode (when API key is absent) costs $0.
- Switching to GPT-4o-mini would reduce cost ~20x.

---

## Prediction Comparison

| Row | Ground Truth | Prediction | Match |
|-----|-------------|------------|-------|
| 1 | supported | supported | ✓ |
| 2 | supported | supported | ✓ |
| 3 | supported | supported | ✓ |
| 4 | supported | not_enough_information | ✗ |
| 5 | contradicted | supported | ✗ |
| 6 | not_enough_information | supported | ✗ |
| 7 | supported | supported | ✓ |
| 8 | contradicted | not_enough_information | ✗ |
| 9 | supported | supported | ✓ |
| 10 | supported | supported | ✓ |

---

## Final Strategy

The system uses a two-tier approach:

1. **Claim parsing** via keyword scoring on conversation text to extract issue type and object part.
2. **Image analysis** using GPT-4o multimodal (or rule-based fallback when no API key).
3. **Evidence checking** against configurable requirements CSV.
4. **Decision engine** combining visual evidence with context signals.
5. **History analysis** for risk context only—never overrides clear visual evidence.

Key design principles:
- Images are the primary source of truth.
- User history provides risk context only.
- Every claim gets an interpretable, image-grounded justification.
- The system is deterministic when the same inputs are repeated (caching ensures this).
