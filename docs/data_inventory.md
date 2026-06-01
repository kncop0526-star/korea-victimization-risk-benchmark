# Anchor Data Inventory & Gaps / 보유 데이터 인벤토리·갭

Status of real survey data **already on hand** (collected during Paper F) vs. what still needs
downloading, mapped to the enrichment attributes (attribute_schema.md). Local paths are under the
Paper F data folder:

`…/01_활성연구중/치안 AI 정책 논문 시리즈/06_Paper_F_SSCI_BDS/04_data/`

> Only aggregated anchor tables go into `config/anchors/` of this repo; the raw microdata below
> stays in the Paper F folder and is never committed (see ETHICS.md, .gitignore).

## On hand ✅

| Attribute(s) | Survey | Local file(s) | Note |
|--------------|--------|---------------|------|
| `financial_vulnerability`, `liquid_asset_band` | 가계금융복지조사 (통계청·한은·금감원) | `MDIS_가금복_2024_가구마스터/2021–2025_가구마스터_*.csv`, `…_가구원/*.csv` | household + person files; apply survey weight |
| `social_isolation`, fear/safety perception | 사회조사 2024 범죄와안전 모듈 | `MDIS_사회조사_2024/MDIS_safety_2024.csv` (N=38,489, **cp949 encoding**), `mdis_2024_safety_marginals.csv` | raw is EUC-KR; decode with cp949. Fear ≠ victimization (see gap) |
| `authority_deference`, political/trust | KGSS 2003–2021 | `KGSS_2003_2021/Korean_data_CUM0048.{dta,sav}`, `kgss_2003_2021_marginals.csv` | PARTYLR + trust items |
| occupation / income (conditioning) | KLIPS 27차 | `klips_27_extract/*.{csv,dta}`, `klips_27_marginals.csv` | KSCO 1-digit, employed N=12,856 |
| occupation (cross-check) | 경제활동인구조사 2024 | `MDIS_경활_2024/2024_경제활동인구조사*.csv` | |
| stereotype audit (Pillar 2) | KoBBQ | `KoBBQ_real/kobbq_full.csv` | for the stereotype-audit validation step |
| region/demographic marginals | KOSIS 2024 | `kosis_marginals_2024_PaperF.csv` | already harmonized to province etc. |
| demographic backbone | Nemotron full 1M | `…/Nemotron-Personas-Korea/data/train-0000*-of-00009.parquet` (9 files) | + processed/ |

## Gaps — must download ❌

| Attribute(s) | Survey | Why not substitutable |
|--------------|--------|------------------------|
| `digital_literacy`, `smartphone_payment_use` | **디지털정보격차 실태조사 (과기정통부·NIA)** | No equivalent on hand; this is *the* digital-competency anchor |
| `prior_victimization`, `reporting_propensity` | **전국범죄피해조사 (KCVS / 한국형사·법무정책연구원)** | 사회조사 범죄와안전 has *fear/perception* only, not actual victimization rate or reporting rate |

`risk_exposure_behavior` (Tier 2–3) can be partially built from NIA 인터넷이용실태조사 + 금감원/경찰청
보이스피싱 통계; `scam_susceptibility` stays Tier-3 (no survey).

---

## Download guide A — 디지털정보격차 실태조사 (NIA)

**Goal:** respondent-level raw data (원자료, 공개용) + codebook, with sampling weights.

1. Primary: NIA stats page → 지식정보 → 통계·실태조사 → **디지털정보격차 실태조사**
   (`nia.or.kr` board `cbIdx=81623`). Open the latest year → download **원자료(공개용)** + **코드북**.
2. Mirror: 공공데이터포털 `data.go.kr` dataset **15038422**
   (한국지능정보사회진흥원_디지털정보격차실태조사 통계자료) — file data.
   ⚠️ Confirm the file is **respondent-level microdata with weights**, not just aggregated report
   tables. If only aggregate tables are offered, use the NIA 원자료 (step 1).
3. Save to `…/06_Paper_F_SSCI_BDS/04_data/NIA_디지털정보격차_<year>/`.
4. Target variables: digital access/competency/utilization scores; conditioning by age, region,
   education, vulnerable-group flag. Map score → ordinal 1–5 (document the cut).

**Access:** public, no application expected (verify the year's license note).

## Download guide B — 전국범죄피해조사 (KCVS)

**Goal:** respondent-level microdata with victimization experience + reporting + weights.

1. **KOSSDA** (한국사회과학자료원, `kossda.snu.ac.kr`) — hosts cleaned KCVS waves (e.g., 2008–2014+).
   Requires member login + a data-use request; download the wave's data + codebook.
2. **KICJ CCJS** (범죄와 형사사법 통계정보, 한국형사·법무정책연구원) — hosts the victim-survey DB
   (2008/2010/2012/2014/2016 in the public DB). Check for newer waves.
3. Mirror: `data.go.kr` dataset **15095483** (한국형사법무정책연구원_전국범죄피해조사) — file data.
4. Also check 통계청 **MDIS** for 국민생활안전실태조사 (KCVS is the approved-statistic form) — you
   already have an MDIS account from the 가금복/사회조사 pulls.
5. Save to `…/06_Paper_F_SSCI_BDS/04_data/KCVS_<wave>/`.
6. Target variables: victimization (binary + type), report-to-police (binary), weights;
   conditioning by age, sex, region. Map → `prior_victimization`, `reporting_propensity`.

**Access:** KOSSDA/KICJ may require a short data-use application → can take days; start early.
KCVS is **biennial** — pick a reference wave and record the year.

---

## Recommended sequencing

1. **Now (no download needed):** build the first *real* anchor from on-hand data —
   `financial_vulnerability` (가계금융복지) or `social_isolation`/fear (사회조사). Proves the pipeline
   on real Korean data and replaces a placeholder.
2. **Quick download:** NIA 디지털정보격차 (public, fast) → `digital_literacy` anchor.
3. **Application-gated:** KCVS via KOSSDA/KICJ → `prior_victimization`, `reporting_propensity`.
4. Backfill `risk_exposure_behavior`; leave `scam_susceptibility` Tier-3.
