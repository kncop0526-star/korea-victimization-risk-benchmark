# A survey-anchored synthetic persona dataset with crime-prevention behavioral attributes for the Korean population (KVRB)

**Authors:** Chihwa Lee¹²*

¹ Korean National Police Agency, AI Policy Division, Republic of Korea
² KAIST, Daejeon, Republic of Korea

**\* Corresponding author:** Chihwa Lee — chi0526@kaist.ac.kr; ORCID 0009-0009-6959-1797

**Keywords:** synthetic population; data fusion; survey conditioning; behavioral attributes; crime prevention; Korea; large language models

---

## Specifications Table

| | |
|---|---|
| **Subject** | Social Sciences |
| **Specific subject area** | Computational social science; synthetic populations for crime-prevention and police-administration research; survey-based data fusion |
| **Type of data** | Table (Parquet, CSV); Text (JSONL narratives); Image (PNG validation figures); Code (Python) |
| **How the data were acquired** | A one-million-record demographic backbone (NVIDIA Nemotron-Personas-Korea, pinned Hugging Face revision `d0a9272116a2ebf139b964ca72b8b8f604616689`, released 2026-04-20) was augmented with six behavioral/victimization attributes. Each attribute was sampled from the conditional distribution of a Korean national survey given a demographic cell; a pinned large language model (gemini-2.5-flash) then rendered the sampled value into a first-person Korean narrative without inferring the value. |
| **Data format** | Analyzed (derived synthetic records); anchor tables are aggregate conditional distributions derived from national surveys |
| **Description of data collection** | Six attributes — financial vulnerability, digital literacy, authority deference, social isolation, prior victimization, reporting propensity — were each conditioned on age band (and, where a single survey records them on the same respondents, sex and education tier) and sampled from weighted survey conditionals `P(level\|cell)`. The prior-victimization × reporting-propensity pair was drawn from one observed survey joint; the remaining cross-survey pairs rest on conditional independence given the demographic vector. No real individual is represented. |
| **Data source location** | Republic of Korea. Anchor surveys: Survey of Household Finances and Living Conditions 2024 (Statistics Korea); Digital Divide Survey 2024 (NIA); Korean General Social Survey (KGSS) 2004/2012/2016; Korean Crime Victim Survey (KCVS) 2018; National Survey of Older Koreans (노인실태조사) 2023. Backbone: NVIDIA Nemotron-Personas-Korea (Hugging Face). |
| **Data accessibility** | Repository name: Zenodo and GitHub. Dataset DOI: 10.5281/zenodo.20500537. GitHub: https://github.com/kncop0526-star/korea-victimization-risk-benchmark. Licenses: MIT (code), CC-BY-4.0 (derived data and documentation). The demographic backbone is not redistributed; it is reproducible from the pinned upstream revision above. |
| **Related research article** | None. |

---

## Value of the Data

- The data add a crime-prevention behavioral layer (financial vulnerability, digital literacy, authority deference, social isolation, prior victimization, reporting propensity) to a demographically faithful one-million-record Korean synthetic population, which previously carried demographic fields only.
- Researchers in policing, fraud and voice-phishing prevention, cybercrime, and social policy can construct target cohorts (for example, elderly single-person low-education households) and read their behavioral risk profile without contacting real individuals.
- Each attribute names its survey anchor, conditioning cells, and the strength of evidence behind it, so reusers can decide how far to trust each field; every marginal is reproducible from the released anchor tables.
- The first-person narratives let each record be used directly as an agent persona in large-language-model agent-based simulation, prevention-message testing, and officer-training material, beyond use as a structured table.
- The release includes the construction code, the survey-provenance anchor tables, and a technical validation (distributional fidelity, model round-trip, and an out-of-sample joint check against an independent elderly survey), so the construction can be reproduced, audited, and extended.

---

## Abstract

KVRB (Korea Victimization-Risk persona Benchmark) is a one-million-record synthetic Korean persona dataset that adds six crime-prevention behavioral attributes to NVIDIA's demographically faithful Nemotron-Personas-Korea backbone. Each behavioral attribute is sampled from the conditional distribution of a real Korean national survey given a demographic cell, and a pinned language model renders the sampled value into a first-person Korean narrative; the model expresses the supplied value rather than inferring it. Four attributes are ordinal Likert (1–5) — financial vulnerability, digital literacy, authority deference, social isolation — and two encode victimization history and reporting propensity from an observed survey joint. Marginal distributions reproduce their survey anchors cell by cell by construction; the inter-attribute joint is modeled partially, through shared-demographic conditioning plus one observed survey joint, with the remaining cross-survey pairs sampled under conditional independence. The release comprises the enriched dataset in partitioned Parquet, the first-person narratives in JSONL, the anchor tables with survey provenance, the construction and validation code, and the technical-validation outputs. The data accessibility section gives the repository, DOI, and licenses; the demographic backbone is reproducible from a pinned upstream revision. The data support cohort construction, agent-based simulation, and prevention-message testing for Korean police-administration research without contact with real individuals.

---

## 1. Data Description

The release contains the following files (Zenodo/GitHub):

- `data/processed/enriched_1M_v4_parts/` — the enriched one-million-record dataset in nine footer-verified Parquet parts. Each record carries the Nemotron backbone columns (uuid, sex, age, age_band, education_level, education_tier, province, occupation, family_type) plus six attribute columns `attr_{financial_vulnerability, digital_literacy, authority_deference, social_isolation, prior_victimization, reporting_propensity}`, a `life_course_valid` boolean, and `gen_meta`. The four Likert attributes take integer values 1–5; prior victimization and reporting propensity follow the observed survey joint.
- `data/processed/enriched_stage23.jsonl` — first-person Korean narratives per persona, with the sampled attribute values (`attr`), the narrative text, and per-record generation metadata. `data/processed/enriched_stage23_N2000.jsonl` is the stratified 2,000-record subset used for the round-trip check.
- `config/anchors/` — the survey-derived conditional distributions (`*_b1.csv` for the age × sex × education conditioning; `kcvs_joint_b2.csv` for the observed victimization × reporting joint) with `.source.json` provenance.
- `src/` — construction code (`build_anchor_*.py`, `enrich_stage1.py`, `enrich_stage2_3.py`) and validation code (`validate_fidelity.py`, `audit_stereotype.py`, `audit_joint.py`, `demo_cohort.py`, `validate_joint_external_noin2023.py`, `validate_nonelderly_joint.py`, `recalibrate_elderly_dl.py`, `crossmodel_extract.py`, `validate_roundtrip.py`).
- `results_v4/`, `results_N2000/`, `results_xmodel_N2000/` — the technical-validation outputs and figures (F1–F7) referenced in the Methods.

The `life_course_valid` flag marks the 117 records (0.01%) whose backbone education level is chronologically impossible for the persona's age; reusers can exclude them with `df = df[df.life_course_valid]` (pandas) or `WHERE life_course_valid` (SQL).

---

## 2. Experimental Design, Materials and Methods

### 2.1 Backbone and attributes
The demographic spine is NVIDIA Nemotron-Personas-Korea (1,000,000 personas validated against KOSIS census margins), used at the pinned revision recorded in the Specifications Table. Six behavioral attributes were added. Four are ordinal Likert (1–5): financial vulnerability, digital literacy, authority deference, social isolation. Two encode prior victimization and reporting propensity.

### 2.2 Survey anchoring (data fusion)
Each attribute is conditioned on demographic cells and sampled from a weighted survey conditional `P(level | cell)`:

| Attribute | Anchor source | Survey N | Conditioning cell |
|---|---|---|---|
| financial_vulnerability | Survey of Household Finances and Living Conditions 2024 | 18,314 | age_band × education_tier (sex-invariant; household-head proxy) |
| digital_literacy | Digital Divide Survey 2024, NIA (ages 19–59); National Survey of Older Koreans 2023, activity instrument (ages 60+) | 7,000; 10,078 | age_band × education_tier |
| authority_deference | KGSS (AUTHORT module, 2016) | 922 | age_band × sex × education_tier |
| social_isolation | KGSS (support-availability battery, 2004+2012) | 2,686 | age_band × sex × education_tier |
| prior_victimization | KCVS 2018 | 12,601 | age × sex × education (observed joint with reporting) |
| reporting_propensity | KCVS 2018 | victims | age × sex × education, conditional on victimization |

Where a single survey records several attributes on the same respondents, conditioning on shared demographics induces realistic cross-attribute association; the prior-victimization × reporting-propensity pair is sampled from an observed survey joint. Cross-survey pairs that no single survey measures on the same respondents are sampled under conditional independence given the demographic vector.

### 2.3 Narrative rendering
A pinned language model (requested as `gemini-2.5-flash`; the responding model id is captured per record in `gen_meta.actual_model`, uniformly `gemini-2.5-flash` across the release; temperature 0.7) renders each sampled value into a first-person Korean narrative. The model is given the value and writes the narrative around it; it does not infer the value.

### 2.4 Technical validation
**Distributional fidelity (Figure 2).** Because attributes are sampled from the anchors, the released marginals reproduce the survey conditionals by construction. The recomputed per-cell total variation distance over the full million is small (weighted per-cell TVD ≤ 0.0034 across attributes; 0.0019 for digital literacy against its recalibrated anchor); this confirms the sampler reproduces its anchors, not that the anchors transfer to any other population.

**Model round-trip (Figure 3).** On a stratified 2,000-persona sample, a level extractor re-read each Likert value from the generated narrative. Quadratic-weighted kappa was 0.73–0.89 (within-one agreement 0.92–0.97). A second provider (gpt-4o-2024-11-20) re-extracting the same 2,000 narratives gave quadratic-weighted kappa 0.88–0.93 (within-one 0.99–1.00); the encoded level survives a model boundary. The round-trip is model-based throughout; it measures whether the narrative faithfully encodes the fixed input, not whether a human reads it the same way.

**Protected-attribute audit (Figure 5).** After conditioning, residual association with sex and province is small; the largest residual is authority deference by sex (Cramér's V = 0.145), a real KGSS individual-level sex difference reproduced by conditioning rather than introduced. An earlier financial-vulnerability-by-sex association (V = 0.245), an artifact of a household-head proxy, was removed by making financial vulnerability sex-invariant (V = 0.033).

**External joint check against an independent survey (Figure 7).** The inter-attribute joint was adjudicated out-of-sample against the 2023 National Survey of Older Koreans (노인실태조사; N = 10,078 aged 65+), which records financial vulnerability, digital literacy, and social isolation on the same elderly respondents and is not an anchor. Real elderly attributes are positively dependent: the share simultaneously high in all three is 2.36 times the independence baseline (95% bootstrap CI 2.20–2.55); the released dataset reaches 1.29 times. After recalibrating the elderly digital-literacy anchor to this survey's activity instrument, the released elderly low-digital-literacy share (35%) matches the survey (37%). The released joint therefore reproduces calibrated single-attribute marginals while under-stating the co-occurrence of extremes; reusers building compound-vulnerability cohorts should treat such cohorts as lower bounds.

**Cohort demonstration (Figure 4).** Selecting age ≥ 65, single-person household, lower education returns 44,362 personas (4.4% of the million); the cohort separates from the population on low digital literacy (×1.8) and high authority deference (×1.5). This is a query demonstration of how to read the layer, not a targeting recommendation.

---

## 3. Limitations

- **Inter-attribute joint.** The cross-survey conditional-independence assumption under-states the real co-occurrence of vulnerabilities; against an independent elderly survey, the released dataset reproduces 1.29× dependence where the real value is 2.36× (§2.4). Multi-attribute extreme cohorts should be read as lower bounds.
- **External validation is elderly-scoped.** The only same-respondent multi-attribute Korean survey available covers the elderly; the non-elderly joint cannot be validated the same way, because the relevant attributes (authority deference, the social-isolation battery) are administered to disjoint KGSS waves and are never jointly observed — the defining condition of statistical matching. One non-elderly inter-attribute joint is observed rather than assumed (prior victimization × reporting propensity, from KCVS).
- **Validation is model-based.** Distributional fidelity is a by-construction check of the sampler; the narrative round-trip is conducted by language models, not human readers, so it measures faithful encoding rather than human legibility.
- **Digital-literacy construct.** The non-elderly digital-literacy marginal reflects a competency instrument; the elderly marginal is recalibrated to an activity-use instrument. The two constructs differ and should be read accordingly.
- **No real individuals.** No record corresponds to a real person; the data describe synthetic populations and must not be presented as observations of real victims.

---

## Ethics Statement

The work uses no human or animal subjects and no personally identifying data. All records are synthetic; no record corresponds to a real person. Anchor tables are aggregate conditional distributions derived from publicly documented national surveys, not microdata records. To limit dual-use exposure, no real-person re-identification is possible, the demographic intersections the data expose are already public at the marginal level in official statistics, and the single attribute that would convert vulnerability description into operational targeting (scam susceptibility) has no survey anchor and is excluded from the quantitative release.

## CRediT Author Statement

**Chihwa Lee:** Conceptualization, Methodology, Software, Validation, Data curation, Writing – original draft, Writing – review & editing.

## Declaration of Competing Interests

The author declares no known competing financial interests or personal relationships that could have appeared to influence the work reported in this article.

## Data Availability

The dataset, anchor tables, construction and validation code, and technical-validation outputs are openly available on Zenodo (DOI 10.5281/zenodo.20500537) and GitHub (https://github.com/kncop0526-star/korea-victimization-risk-benchmark), under MIT (code) and CC-BY-4.0 (derived data and documentation). The demographic backbone (NVIDIA Nemotron-Personas-Korea) is not redistributed and is reproducible from the pinned upstream revision recorded in the Specifications Table.

## Declaration of Generative AI and AI-assisted Technologies in the Writing Process

During the preparation of this manuscript, the author used Claude (Anthropic) to assist with drafting and editing the text under the author's direction. The author reviewed and edited the content as needed and takes full responsibility for the content of the published article.

## References

1. NVIDIA. (2026). Nemotron-Personas-Korea [Data set]. Hugging Face. Released 2026-04-20.
2. Statistics Korea. (2021). 2020 Population and Housing Census. Korean Statistical Information Service (KOSIS).
3. Statistics Korea. (2024). Survey of Household Finances and Living Conditions.
4. National Information Society Agency (NIA). (2024). The Report on the Digital Divide.
5. Survey Research Center, Sungkyunkwan University. Korean General Social Survey (KGSS), 2004/2012/2016 cumulative file.
6. Korean Institute of Criminology and Justice. (2018). Korean Crime Victim Survey (KCVS).
7. Korea Internet & Security Agency (KISA) / NIA. Survey on Internet Use.
8. Korea Institute for Health and Social Affairs. (2023). National Survey of Older Koreans (노인실태조사). Ministry of Health and Welfare.
9. Cramér, H. (1946). Mathematical Methods of Statistics. Princeton University Press.
10. Cohen, J. (1960). A coefficient of agreement for nominal scales. Educational and Psychological Measurement, 20(1), 37–46.
11. Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. Biometrics, 33(1), 159–174.
12. Efron, B. (1979). Bootstrap methods: Another look at the jackknife. The Annals of Statistics, 7(1), 1–26.
13. D'Orazio, M., Di Zio, M., & Scanu, M. (2006). Statistical Matching: Theory and Practice. Wiley.
14. Rässler, S. (2002). Statistical Matching: A Frequentist Theory, Practical Applications, and Alternative Bayesian Approaches. Springer.
