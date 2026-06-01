# Enrichment Attribute Schema / 증강 속성 스키마

The new attribute layer added on top of the Nemotron demographic backbone. Each attribute names
its **anchor source** and **anchor-strength tier** (see enrichment_design.md §3). Tier 3 attributes
are **qualitative-only** and must be excluded from quantitative claims.

> Values below are the *target design*. Actual ranges/scales must be set from the real survey once
> sourced. Conditioning column lists are illustrative, not final.

## Core attributes

| # | Attribute | Type / scale | Conditioned on (D + prior A) | Anchor source (verify) | Tier |
|---|-----------|--------------|------------------------------|------------------------|------|
| 1 | `digital_literacy` | ordinal 1–5 | age, education, region | national digital-divide survey | 1 |
| 2 | `smartphone_payment_use` | ordinal 1–5 | age, digital_literacy | digital-divide / 인터넷이용실태 | 1–2 |
| 3 | `financial_vulnerability` | ordinal 1–5 | age, occupation, housing_type | 가계금융복지조사 | 2 |
| 4 | `liquid_asset_band` | categorical (low/mid/high) | age, occupation | 가계금융복지조사 | 2 |
| 5 | `social_isolation` | ordinal 1–5 | family_type, age, marital_status | 통계청 사회조사 / 독거노인 | 1–2 |
| 6 | `authority_deference` | ordinal 1–5 | age, education | 사회조사 (신뢰·태도 문항) | 2–3 |
| 7 | `prior_victimization` | binary + type | age, sex, region | national crime victim survey (KCVS) | 1 |
| 8 | `reporting_propensity` | ordinal 1–5 | prior_victimization, age, sex | KCVS 신고율 | 1 |
| 9 | `risk_exposure_behavior` | composite 0–10 | digital_literacy, age | 보이스피싱 통계 + 추정 | 2–3 |
| 10 | `scam_susceptibility` | ordinal 1–5 | (derived) all above | **no direct survey** | **3 (weak)** |

### Notes
- **#10 `scam_susceptibility` is Tier 3** — there is no clean survey for individual susceptibility.
  It is generated as an LLM-prior composite and is **flagged low-confidence**; use it only as a
  qualitative simulation input, never as a measured outcome.
- Attributes are sampled **independently**, each from its own demographic conditioning cell (age, and
  age x education for digital literacy). The released dataset therefore carries **no inter-attribute
  correlation** beyond what shared conditioners induce; given the conditioning cell, attributes are
  mutually independent. (An earlier design envisaged sequential conditioning on prior attributes; the
  released sampler does not implement it. Users needing joint structure must impose it themselves.)

## Output record shape

Each enriched persona record =

```
{ ...all 26 Nemotron columns...,            # backbone (unchanged)
  "attr": { "digital_literacy": 2, ... },    # sampled values (Stage 1)
  "attr_narrative": "…",                     # LLM realization (Stage 2)
  "attr_roundtrip": { "digital_literacy": 2, ... },   # re-extracted (Stage 3)
  "attr_flags": { "roundtrip_mismatch": [],  # QA flags
                  "tier3_qualitative": ["scam_susceptibility"] },
  "gen_meta": { "actual_model": "...", "anchor_versions": {...}, "random_state": 42 } }
```

## Provenance & versioning
- Every attribute carries its anchor source + survey year in `gen_meta.anchor_versions`.
- Tier is fixed in this schema; if a better survey is found, tier may be upgraded with a version bump.
- Backbone columns are never modified — enrichment is strictly additive.
