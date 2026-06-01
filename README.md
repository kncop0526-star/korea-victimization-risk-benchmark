# Korea Victimization-Risk Persona Benchmark (KVRB)

**A synthetic persona benchmark for crime-prevention research in Korean police administration.**

> ⚠️ This repository contains **synthetic personas only**. It does not contain, describe, or
> represent any real victims, suspects, or identifiable individuals. It is intended for
> **prevention research, education, and simulation** — not for targeting. See [ETHICS.md](ETHICS.md).

[![License: MIT](https://img.shields.io/badge/Code-MIT-blue.svg)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/Data-CC%20BY%204.0-lightgrey.svg)](LICENSE-DATA.md)
<!-- [![DOI](https://zenodo.org/badge/DOI/PLACEHOLDER.svg)](https://doi.org/PLACEHOLDER) -->

---

## 1. Overview / 개요

**EN.** KVRB **enriches** the
[NVIDIA Nemotron-Personas-Korea](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea)
dataset (1,000,000 synthetic Korean personas, CC-BY-4.0) with a new layer of
**crime-prevention-relevant behavioral and vulnerability attributes** that the source data lacks
(digital/financial literacy, social isolation, prior victimization, reporting propensity, risk
exposure, etc.). The core contribution is a **survey-conditioned enrichment method**: attribute
values are *sampled from real Korean survey distributions*, the LLM only *renders* them into
narrative, and both are then *validated* — defusing the "synthetic-data hallucination" objection by
design. Cohort filtering (below) is a secondary selection step on top of the enriched dataset.
Methodology: [docs/enrichment_design.md](docs/enrichment_design.md).

**KO.** KVRB는 NVIDIA Nemotron-Personas-Korea(100만 한국인 합성 페르소나, CC-BY-4.0)에 원천 데이터에
**없는** 범죄예방용 행동·취약성 변수 레이어(디지털·금융 이해도, 사회적 고립, 과거 피해경험, 신고성향,
위험노출 등)를 **증강(enrichment)**합니다. 핵심 기여는 **조사 기반 조건부 증강 방법론**입니다 —
속성값은 *실제 한국 조사 분포에서 샘플링*하고, LLM은 그것을 *서술로 렌더링*만 하며, 양쪽을 *검증*합니다.
이로써 "합성 데이터 환각" 비판을 설계 차원에서 차단합니다. cohort 필터링은 증강된 데이터셋 위에서의
2차 선택 단계입니다. 방법론: [docs/enrichment_design.md](docs/enrichment_design.md).

## 2. What this is / is NOT

| ✅ This repository provides | ❌ This repository does NOT provide |
|---|---|
| Cohort construction methodology (documented) | Real victim or offender data |
| Validation pipeline (KOSIS goodness-of-fit) | Pre-extracted "vulnerable target" lists |
| Abstracted, configurable cohort definitions | Raw sensitive thresholds for targeting |
| Reproducible scaffolding for prevention research | Any personally identifiable information (PII) |
| Officer-training / interview-simulation persona pools | Suspect/offender profiling tools |

## 3. Crime-type modules / 범죄유형 모듈

| ID | Module | Cohort basis | Status |
|----|--------|--------------|--------|
| 01 | Voice phishing (elderly) / 보이스피싱·노인 | age 70+ · single-person household · lower education | worked example |
| 02 | Jeonse rental fraud (youth) / 전세사기·청년 | youth · single-person · metropolitan tenants | template |
| 03 | Romance / investment scam / 로맨스스캠·투자리딩방 | 40–60s · widowed/divorced · select occupations | template |
| 04 | Digital sex crime / 디지털 성범죄 | youngest available cohort (19+) — see caveat | template |
| 05 | School violence / 학교폭력 | **proxy only** — dataset has no minors (19–99) | template + limitation note |

> Module 04 and 05 involve minors or near-minors. Nemotron-Personas-Korea contains **no one
> under 19**, so these modules use adjacent-age proxies (e.g., 19-year-olds, guardians, adult
> recall) and explicitly document the limitation. Do not interpret them as minor-victim data.

## 4. Repository structure

```
korea-victimization-risk-benchmark/
├── README.md                  ← this file (EN-primary + KO)
├── LICENSE                    ← code license (MIT)
├── LICENSE-DATA.md            ← derived-data license (CC-BY-4.0 + NVIDIA attribution)
├── ETHICS.md                  ← responsible-use & dual-use statement (EN + KO)
├── CITATION.cff               ← machine-readable citation (Zenodo-ready)
├── requirements.txt
├── docs/
│   ├── enrichment_design.md   ← ★ PRIMARY: survey-conditioned enrichment methodology
│   ├── attribute_schema.md    ← ★ new attribute layer (variables, anchors, tiers)
│   ├── methodology.md         ← cohort construction method (secondary selection step)
│   ├── data_card.md           ← datasheet (Gebru et al. 2021 format)
│   └── cohort_specs/          ← one spec per crime-type module
├── src/
│   ├── enrich_personas.py     ← ★ PoC: sample attr → LLM render → round-trip audit
│   ├── build_cohorts.py       ← load Nemotron → apply config → export subset
│   ├── validate_kosis.py      ← KOSIS χ² goodness-of-fit validation
│   └── cohort_registry.py     ← abstract cohort-definition loader (safeguard layer)
├── config/
│   ├── cohorts.example.yaml   ← abstracted cohort definitions (sensitive thresholds redacted)
│   └── anchors/               ← survey conditional-distribution tables (PLACEHOLDER examples)
└── data/                      ← raw dataset NOT committed (see data/README.md)
```

## 5. Responsible release / 책임있는 공개

This project follows a **methodology-centric** release model to mitigate dual-use risk:

1. **Raw vulnerability thresholds are not published.** `config/cohorts.example.yaml` ships
   abstracted/placeholder values; the operational thresholds are kept by the maintainer.
2. **Framing is prevention, not exposure.** Cohorts describe *who to protect*, not *who to target*.
3. **Synthetic-data disclaimer** appears in every artifact.
4. Full statement: [ETHICS.md](ETHICS.md).

## 6. Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 0) See the enrichment pipeline run with NO dataset and NO API key (demo mode):
python src/enrich_personas.py --demo --n 6

# 1) Download Nemotron-Personas-Korea into data/ (see data/README.md)
# 2) Enrich personas (sample attr from survey anchor -> LLM render -> round-trip audit)
python src/enrich_personas.py --source data/raw/nemotron_korea.parquet --n 1000
# 3) (optional) Select a crime-type cohort from the enriched set
python src/build_cohorts.py --config config/cohorts.example.yaml --module module_01
# 4) Validate distributional fidelity against KOSIS
python src/validate_kosis.py --cohort data/processed/module_01.parquet
```

> The demo step works offline because the LLM render and round-trip extractor are stubs and the
> anchor table is a placeholder. Wire a pinned LLM and real survey anchors for research use
> (see [docs/enrichment_design.md](docs/enrichment_design.md)).

## 7. Attribution / 출처 (required)

This work derives from **NVIDIA Nemotron-Personas-Korea** (CC-BY-4.0). You must retain this
attribution in any redistribution. See [LICENSE-DATA.md](LICENSE-DATA.md) and [CITATION.cff](CITATION.cff).

## 8. License

- **Code** (`src/`, scripts): [MIT](LICENSE)
- **Derived data & docs**: [CC-BY-4.0](LICENSE-DATA.md), inherited from the upstream dataset.

## 9. Citation

If you use this benchmark, please cite both this repository and the upstream dataset
(see [CITATION.cff](CITATION.cff)).
