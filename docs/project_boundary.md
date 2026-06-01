# Project boundary & shared-data note / 프로젝트 경계·공유 데이터

## KVRB vs Paper F — distinct contributions
This benchmark (KVRB) and the "Paper F" track share **raw survey microdata** but are **separate
research contributions**:

| | Paper F | KVRB (this repo) |
|---|---|---|
| Question | Do synthetic personas (Nemotron) *match reality*? | Can we *add* survey-anchored behavioral attributes to them? |
| Method | 4-pillar **validation** (distributional fidelity, stereotype, generative, …) | **Enrichment** — sample attributes from real survey conditionals + LLM realization |
| Output | Validation paper | Data/resource paper + public dataset |

They legitimately reuse the same national surveys. To avoid any salami-slicing concern, the two
papers should **cite each other** and state the role split explicitly (validation vs. enrichment).

## Shared raw data — where it lives
Raw survey microdata (가계금융복지조사, 디지털정보격차, KGSS, KCVS, Nemotron) is **not committed**
to this repo (see `.gitignore`, `config/anchors/README.md`). Locally it lives in the Paper F
data folder, which both tracks reference. This repo ships only **aggregate anchor tables** + code.

## Decoupling — KVRB_DATA_ROOT
Builder scripts that read raw microdata resolve the data folder from the env var **`KVRB_DATA_ROOT`**
(or `config/local_paths.json`, git-ignored), defaulting to `data/raw`. No absolute/Paper-F paths are
hard-coded in committed source. To rebuild anchors locally:

```bash
export KVRB_DATA_ROOT="/path/to/shared/04_data"   # Windows: set KVRB_DATA_ROOT=...
python src/build_anchor_kcvs.py
python src/build_anchor_social_isolation_structural.py
```

Where to obtain each survey is documented in `docs/data_inventory.md` and `docs/anchor_sourcing_plan.md`.
