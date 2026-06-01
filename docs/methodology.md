# Cohort Construction Methodology / cohort 구성 방법론

This document describes *how* victimization-risk cohorts are constructed and validated. It is the
public, methodology-centric core of the benchmark. Operational threshold values are intentionally
abstracted (see [ETHICS.md §3](../ETHICS.md)).

## 1. Source variables / 원천 변수

Cohorts are defined over the 12 demographic columns of Nemotron-Personas-Korea:

`sex, age, marital_status, military_status, family_type, housing_type, education_level,
bachelors_field, occupation, district, province, country`

Long-form persona fields (`professional_persona`, `family_persona`, etc.) are retained for
simulation/training but are **not** used as selection criteria, to avoid encoding stereotype
content into the filter logic.

## 2. Construction pipeline / 구성 파이프라인

```
Nemotron 1M  ──►  (a) define risk dimensions  ──►  (b) abstracted filter (config)
             ──►  (c) draw cohort (random_state fixed)
             ──►  (d) KOSIS goodness-of-fit validation
             ──►  (e) document limitations  ──►  cohort subset (parquet + CSV)
```

**(a) Risk dimensions.** For each crime type, we identify demographic dimensions that the
*prevention literature* associates with elevated exposure (e.g., social isolation, digital-payment
unfamiliarity, housing tenure). Each dimension maps to one or more source columns. The mapping —
not the cutoff values — is what this repository publishes.

**(b) Abstracted filter.** Dimensions are expressed in `config/cohorts.example.yaml` as named
predicates with **placeholder** parameters. The maintainer keeps operational parameters in a
local, git-ignored config.

**(c) Cohort draw.** `src/build_cohorts.py` applies the predicates and draws the cohort with a
fixed `random_state` for reproducibility.

**(d) Validation.** `src/validate_kosis.py` runs a χ² goodness-of-fit test comparing the cohort's
joint distribution (age × region × sex × occupation) against KOSIS census microdata, to confirm
the synthetic cohort is not distorted relative to the real population it stands in for.

**(e) Limitations.** Every cohort spec documents synthetic-data limitations, proxy variables, and
out-of-scope populations (notably minors).

## 3. Reproducibility / 재현성

- Fixed `random_state` (default 42) on all draws.
- `parquet` + `CSV` dual export (Excel/Cowork compatible).
- Validation report (χ², p-value, per-cell residuals) saved alongside each cohort.

## 4. Validation acceptance criteria / 검증 통과 기준

A cohort is considered usable when:

1. Joint-distribution χ² goodness-of-fit does not reveal *material* divergence from KOSIS
   (report p-value and Cramér's V; large samples make raw p-values fragile — interpret effect size).
2. A manual review of ~50 sampled personas finds no systematic stereotype artifacts.
3. Limitations are documented in the cohort spec.

## 5. Caveats for peer review / peer review 대비 유의

When using a cohort in a KCI/SSCI paper, the Discussion must state: synthetic origin (NVIDIA
Nemotron), KOSIS validation outcome, proxy-variable limits, and a recommendation to replicate on
real population data (e.g., KLIPS/KSDC) in follow-up work.
