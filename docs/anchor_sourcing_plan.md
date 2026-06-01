# Anchor Data Sourcing Plan / 앵커 데이터 소싱 계획

How to obtain real Korean survey data and turn it into the conditional-distribution tables
(`P(level | cell)`) that drive Stage-1 sampling (enrichment_design.md §2). This is the work that
converts the PoC into a real, publishable dataset.

> **Redistribution rule.** We commit **only aggregated conditional tables** (the anchors), never the
> raw survey microdata. Each provider's terms govern the microdata; aggregates derived for research
> are publishable, but verify each source's redistribution clause before release.

---

## 1. Attribute → survey map

| Attribute | Survey (conducting body) | Cadence | Access portal | Public / Authorized | Anchor tier |
|-----------|--------------------------|---------|---------------|---------------------|-------------|
| `digital_literacy`, `smartphone_payment_use` | 디지털정보격차 실태조사 (과기정통부·NIA) | annual | NIA site · data.go.kr | public raw data + codebook | 1 |
| `prior_victimization`, `reporting_propensity` | 전국범죄피해조사 / 국민생활안전실태조사 (한국형사·법무정책연구원) | biennial | KICJ CCJS · KOSSDA · data.go.kr | public-use file | 1 |
| `financial_vulnerability`, `liquid_asset_band` | 가계금융복지조사 (통계청·한국은행·금감원) | annual | 통계청 MDIS | public + authorized | 2 |
| `social_isolation` | 사회조사 (통계청) | biennial (해당 부문) | 통계청 MDIS | public + authorized | 1–2 |
| `authority_deference` | 사회조사 / 한국종합사회조사 KGSS | annual/biennial | MDIS / KOSSDA | public | 2–3 |
| `risk_exposure_behavior` | 인터넷이용실태조사 (NIA) + 보이스피싱 통계 (금감원·경찰청) | annual | NIA · FSS/KNPA releases | public report + raw | 2–3 |
| `scam_susceptibility` | — none — | — | — | — | **3 (LLM-prior, qualitative only)** |

Exact survey years/waves, variable names, and conducting-body names **must be re-verified against
the codebook at sourcing time** and cited with their year. Surveys are not synchronized
(victim survey is biennial; digital-divide is annual) — pick reference years and document them in
`gen_meta.anchor_versions`.

## 2. Access routes (verified May 2026)

- **통계청 MDIS** — `mdis.kostat.go.kr`. ONE-ID login. **Public-use** files: free download + online
  analysis. **Authorized** (more detailed cells): remote-access / RDC center service. Use authorized
  version only if fine cells (e.g., region × age × education) are too sparse in the public file.
- **NIA** — digital-divide & internet-use surveys: raw data + codebook on the NIA stats pages and
  on `data.go.kr` (e.g., dataset 15038422). Public.
- **KICJ CCJS** — 범죄와 형사사법 통계정보 portal hosts the victim-survey DB; **KOSSDA** hosts
  several waves as cleaned files; `data.go.kr` lists file data. Public-use.

## 3. The processing recipe (per attribute)

For each attribute, produce `config/anchors/<attribute>.csv` with columns
`<conditioning cols…>, level, prob`:

1. **Download** the public-use microdata + codebook. Record survey name, body, year.
2. **Locate variables.** Identify (a) the *attribute variable* (the survey item that operationalizes
   the construct) and (b) the *conditioning variables* (age, sex, region, education).
3. **Harmonize to the Nemotron schema** via an explicit crosswalk:
   - `age` → `age_band` (19-29 / 30-44 / 45-59 / 60-74 / 75+)
   - region code → `province` (17 시·도)
   - education code → `education_tier` (lower / higher) — document the cut
   - Recode the attribute item onto the schema's ordinal scale (e.g., 1–5); document the mapping.
4. **Apply survey weights.** Compute **weighted** counts per `(cell, level)` using the survey's
   sampling weight variable — never raw unweighted counts (this is a common reviewer catch).
5. **Normalize within cell** → `P(level | cell)` (probabilities sum to 1 per cell).
6. **Handle sparse cells.** If a cell has too few (weighted) respondents, either (a) collapse a
   conditioning dimension, or (b) fall back to the marginal and set the Tier-2 `marginal_fallback`
   flag. Apply light smoothing (e.g., add-α) to avoid zero-probability levels.
7. **Save aggregate only.** Write the CSV (drop `.example`); store source + year in a sidecar
   `<attribute>.source.json`. Do **not** commit microdata.
8. **Sanity-check** against the published report's headline numbers (e.g., the survey's reported
   elderly digital-literacy gap) to confirm the harmonization is correct.

## 4. Cross-survey integration cautions / 통합 시 유의

- **Year mismatch.** Anchor each attribute to its own reference year; report the set of years.
- **Population frame differences.** Some surveys are household-based (가계금융복지) vs individual-based
  (디지털격차). Define the unit (individual persona) and convert household variables consistently.
- **Weighting bases differ** across surveys — apply each survey's own weight; do not pool weights.
- **Sequential conditioning needs a shared survey** to capture attribute–attribute dependence; where
  attributes come from *different* surveys, sample them independently and record the independence
  assumption (enrichment_design.md §5).

## 5. Deliverables of this phase

- `config/anchors/*.csv` — real conditional tables (replacing the `.example` placeholders).
- `config/anchors/*.source.json` — provenance (survey, body, year, weight var, crosswalk version).
- `docs/crosswalks.md` — the age/region/education recode tables (for reproducibility & review).
- A short validation note confirming each anchor reproduces its source's published marginals.

## 6. Effort & sequencing

Start with the **two Tier-1, highest-value anchors**: `digital_literacy` (NIA, public, easy) and
`prior_victimization`/`reporting_propensity` (KICJ victim survey). These alone enable a credible
first dataset version and directly support the elderly-phishing use case. Add 가계금융복지 and
사회조사 anchors in a second pass. Leave Tier-3 `scam_susceptibility` as a flagged qualitative field.
