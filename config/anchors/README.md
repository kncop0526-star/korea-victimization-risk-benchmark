# Anchor tables / 앵커 테이블

Each CSV here encodes a **conditional distribution** `P(attribute level | conditioning cell)`
derived from a real Korean survey. The enrichment pipeline samples attribute values from these
tables (enrichment_design.md §2, Stage 1).

> ⚠️ **All `*.example.csv` files contain PLACEHOLDER probabilities** for illustration only.
> They are NOT real survey values. Before any research use, replace them with conditionals
> computed from the actual survey microdata named in `docs/attribute_schema.md`, and record the
> survey year in `gen_meta.anchor_versions`. Do not publish results based on placeholder anchors.

## Format

Long format, one row per (cell × level):

```
age_band,education_tier,level,prob
60-74,lower,1,0.45
60-74,lower,2,0.30
...
```

- Conditioning columns (e.g., `age_band`, `education_tier`) must match the keys used in
  `enrich_personas.py`.
- `level` = ordinal attribute value; `prob` = P(level | cell). Probabilities within a cell sum to 1.
- Cells not present fall back to the marginal (Tier 2 behavior) with a flag.

## Status

| Anchor file | Status | Source |
|-------------|--------|--------|
| `financial_vulnerability.csv` | ✅ **REAL** (weighted, N=18,314) | 가계금융복지조사 2024 (MDIS) — `.source.json` |
| `digital_literacy.csv` | ✅ **REAL** (weighted, N=7,000) | 디지털정보격차 실태조사 2024 (NIA, 일반국민) — **제2유형 NC** license |
| `authority_deference.csv` | ✅ **REAL** (weighted, **low-N=927**) | KGSS 2003–2021 (AUTHORT battery) — `src/build_anchor_kgss.py` |
| `social_isolation.csv` | ✅ **REAL** (weighted, **low-N=2,686**) | KGSS 2003–2021 — **structural v2** (SICK/BORROW/DOWN + NGHASK) |
| `prior_victimization.csv` | ✅ **REAL** (weighted, N=12,623) | 전국범죄피해조사 KCVS 2018 (bct_1) — **제4유형 NC/ND** |
| `reporting_propensity.csv` | ✅ **REAL** (weighted, **low-N=439 victims**) | KCVS 2018 (c24, victims only) — **제4유형 NC/ND** |
| `digital_literacy.example.csv` | ⛔ SUPERSEDED placeholder (Windows file lock prevented deletion; ignore) | — |

**KCVS anchors (prior_victimization, reporting_propensity):** from 전국범죄피해조사 2018 (KICJ, via
KOSSDA member access). Victimization rate declines with age (19-29 ≈ 4.7% → 75+ ≈ 2.3%).
`reporting_propensity` is built on the **victim subsample only (~439)** → low-N and sparse;
the 75+ cell (very few elderly victims) is noisy (≈1.8% report) — treat as indicative, not precise.
**License:** KICJ 공공저작물 **제4유형 (출처표시 + 비영리 + 변경금지)** — more restrictive than the
others; aggregate-only release with attribution, flagged NC/ND in `.source.json`.

**All 6 attributes now have REAL anchors** (the schema's full set except Tier-3 `scam_susceptibility`).
The complete 6-attribute enriched 1M dataset is at `data/processed/enriched_1M_v2_parts/` (9 parts).

**KGSS anchors (authority_deference, social_isolation):** the item batteries appear only in
specific KGSS waves, so effective N is small (~900 / ~2,700) — **indicative, low-N** anchors
conditioned on `age_band` only. **`social_isolation` v2 = structural** (lack of actual support:
도움청할 사람 '없음' + few neighbors to ask), replacing the v1 OTHREL subjective-loneliness measure.
The structural version correctly puts **75+ as most isolated** (phishing-relevant), unlike v1.
Caveat: the deficit score is zero-inflated (isolation is rare), so levels 1–2 are weakly separated.

Both real anchors are weighted and built from public-use micro files, year-aligned to **2024**:
- `financial_vulnerability.csv` — `src/build_anchor_financial_vulnerability.py`; passes by-construction
  fidelity (synthetic resample reproduces survey conditional, max cell gap ≈ 0.009).
- `digital_literacy.csv` — `src/build_anchor_digital_literacy.py`; face-valid age×education gradient
  (19-29 ≈ 4.0 / 75+ lower-edu ≈ 1.16 on a 1–5 scale). **Note:** the `75+ × higher` cell is sparse
  (few highly-educated 75+) → low-N, treat with caution. **License:** derives from a 공공데이터포털
  제2유형 source (출처표시 + **상업적 이용금지**); only the aggregate table is published, with
  attribution, and this anchor is flagged non-commercial in its `.source.json`.

## Real-data workflow

1. Obtain survey microdata (e.g., via KOSIS MDIS, KIC, NIA data portals — access per each
   provider's terms).
2. Compute `P(level | cell)` per attribute.
3. Save as `<attribute>.csv` (drop `.example`) and reference it in the run config.
4. Record source + year for citation.
