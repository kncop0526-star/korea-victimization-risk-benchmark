# A survey-anchored synthetic persona dataset with crime-prevention behavioral attributes for Korean police-administration research

**Manuscript type:** Data Descriptor (target: *Scientific Data*; fallback: *Data in Brief*)
---

## 1. Background & Summary

Korean police-prevention research needs persona populations that are demographically faithful and
carry the behavioral variables prevention work turns on — digital-payment unfamiliarity, financial
strain, social isolation, prior victimization, willingness to report. Demographically realistic
synthetic populations already exist: NVIDIA's Nemotron-Personas-Korea [1] provides one million Korean
personas validated against KOSIS census margins [2]. The behavioral and victimization layer is missing.
A researcher assembling an elderly voice-phishing cohort can filter on age, household type, and
education, but cannot read off that cohort's digital literacy or authority deference — those fields
are not in the backbone.

This dataset adds that layer. The method is survey-conditioned enrichment. Each behavioral attribute
is sampled from the conditional distribution of a real Korean survey, and a pinned language model only
renders the sampled value into first-person narrative. The model expresses values; it does not
estimate them. Because attributes are drawn from survey conditionals, each attribute's marginal — conditional on its
anchor cell — matches the source survey by construction, not by assertion. §4.1 reports this cell by
cell (largest per-attribute deviation 0.0020 in total variation); it is mainly a claim about marginals.
The joint distribution is modeled only partially — §4.5 characterizes what is captured (shared-demographic
conditioning plus one observed survey joint) and what is left as stated conditional independence.

Four pieces make up the release: the enriched one-million-persona dataset, the construction code, the
anchor-table specifications with their survey provenance, and a technical validation covering
distributional fidelity, round-trip consistency, and a worked cohort demonstration. The contribution
is the anchoring procedure, not the backbone. Provenance is layered: NVIDIA supplies the
demographic spine (CC-BY-4.0), national surveys supply the conditional distributions, and this work
supplies the schema, the sampling, and the validation. Nothing here claims the personas are real
or that the attributes were measured on individuals.

A companion study (Paper F, in preparation) works the other side of the same data: whether synthetic
Korean personas are demographically and structurally faithful enough to stand in for a real
population. This dataset assumes that faithfulness and builds on top of it. The two share raw survey
inputs but separate cleanly — one validates the backbone, the other augments it — and cite each other
to keep the boundary visible. In practice this lets a researcher assemble a cohort,
inspect its risk profile, and test a prevention message in simulation before any contact with a real
population — none of which the demographic backbone alone supports. The cohorts this builds are
*susceptibility* segments, not realized-victim predictions: §5.1 shows that for voice-phishing, realized
loss tracks exposure and income, so the layer constructs who is vulnerable to an approach, not who loses
most. The inter-attribute joint is adjudicated out-of-sample against a same-respondent elderly survey (§4.6)
— quantifying the conditional-independence under-capture and flagging an elderly digital-literacy marginal
that needs recalibration — for the elderly cohort only; the non-elderly joint rests on stated conditional
independence. That validation also surfaced a policy-relevant victimology result reported separately.

## 2. Methods

### 2.1 Demographic backbone

NVIDIA Nemotron-Personas-Korea (1,000,000 personas, CC-BY-4.0) is the backbone, retained unmodified.
Enrichment is strictly additive: no backbone column is altered. Twelve demographic columns are used
for conditioning and selection (`sex, age, marital_status, military_status, family_type, housing_type,
education_level, bachelors_field, occupation, district, province, country`). Long-form persona text is
kept for downstream simulation but is never used as a selection or conditioning criterion, to avoid
encoding stereotype content into the filter logic. Coverage is ages 19–99, single country (대한민국);
there are no minors.

### 2.2 Attribute schema

Six behavioral attributes form the released layer. Four are ordinal Likert (1–5):
financial_vulnerability, digital_literacy, authority_deference, social_isolation. Two are binary:
prior_victimization, reporting_propensity. Each attribute names its anchor source and an
anchor-strength tier (Tier 1 = a national survey measures the attribute directly; Tier 2 = anchored on a
related survey item through a documented mapping; Tier 3 = no clean survey anchor, qualitative-only). One
further attribute, scam_susceptibility, is Tier 3 and is excluded from the quantitative release.

### 2.3 Survey anchoring

Each attribute is conditioned on demographic cells and sampled from a weighted survey conditional
`P(level | cell)`. Anchor tables and their provenance:

| Attribute | Anchor source | Survey N | Conditioning cell |
|---|---|---|---|
| financial_vulnerability | 가계금융복지조사 2024 [3] | 18,314 | age_band × education_tier (sex-invariant; household-head proxy) |
| digital_literacy | 디지털정보격차 실태조사 2024 (NIA) [4] | 7,000 | age_band × education_tier |
| authority_deference | KGSS (AUTHORT, 2016) [5] | 922 | age_band × sex × education_tier |
| social_isolation (structural v2) | KGSS (support battery, 2004+2012) | 2,686 | age_band × sex × education_tier |
| prior_victimization | KCVS 2018 [6] | 12,601 | age × sex × edu (observed joint with reporting) |
| reporting_propensity | KCVS 2018 | victims, joint | age × sex × edu, conditional on victimization |

Sampling is seed-fixed (`random_state=42`). The `reporting_propensity` cell among the oldest victims is
low-N (a survey subsample), flagged for interpretation in §5. Most attributes now condition on
age × sex × education where their survey records all three on the same respondents (KGSS, KCVS);
financial vulnerability conditions on age × education only and is held sex-invariant (§4.3, §4.5);
sparse cells fall back to a coarser demographic subset rather than to a fabricated value.
Education tier is higher = {4-year university, 2–3-year college, graduate school} and lower otherwise.
Attributes are not drawn fully independently, but the structure between them is deliberately modest and
we are explicit about its limits. Where two attributes come from the same survey and the same
respondents — victimization and reporting in KCVS — the dataset samples them from the observed joint,
so that pair carries the covariance the survey itself measured. For the rest, conditioning each
attribute on shared demographics (age, plus sex and education where a survey records them on the same
respondents) lets common demographic causes induce some cross-attribute association instead of forcing
independence. This is a partial, demographic-channel structure rather than a full joint model.
Associations that no single survey measures on the same people — most cross-survey pairs — still rest
on conditional independence given the demographic vector, which we state rather than conceal. How
closely this conditioning approximates the real Korean joint distribution is an open question, and one
we expect reusers to test further; the release labels throughout which associations are measured and
which are assumed.

### 2.4 LLM narrative realization (render-not-estimate)

Stage 2 hands each persona's *fixed* attribute vector to a pinned LLM and asks for a 4–6 sentence
first-person Korean narrative consistent with those values. The prompt states the values are fixed
inputs to express, not to estimate. The model snapshot is pinned (no floating alias) and the actual
responding model id is captured per record. The released code reads the key from the environment;
no key is embedded. A deterministic stub allows the pipeline to run without a key for plumbing tests.

### 2.5 Round-trip consistency audit

Stage 3 re-extracts each Likert attribute's level from the generated narrative and compares it to the
sampled value. Agreement measures whether the narrative faithfully encodes the fixed input. The audit
covers all four Likert attributes; each adds one extractor call per record in the real pass.

## 3. Data Records

This release comprises:

- **Enriched personas (v3, Route-B)** — 1,000,000 rows, backbone columns plus `attr_{financial_vulnerability,
  digital_literacy, authority_deference, social_isolation, prior_victimization, reporting_propensity}`,
  in partitioned parquet (`enriched_1M_v3_parts/`, 9 parts, footer-verified) and CSV samples. v3 is the
  validated artifact: B1 conditioning (age × sex × education where a survey records all three on the same
  respondents) plus the B2 observed PV × RP joint. **Schema note:** the elderly (65+) `attr_digital_literacy` is a within-cohort ordinal/relative measure, not a population prevalence (§4.6, §5.3) — do not read its elderly marginal as a prevalence.
- **Narratives** — JSONL (`enriched_stage23.jsonl` full release; `enriched_stage23_N2000.jsonl` the
  stratified round-trip probe of §4.2): per-record `attr`, `attr_narrative`,
  `roundtrip_<attr>`, mismatch flags, and `gen_meta` (actual model, provider, pinned model).
- **Anchor tables** — base CSVs plus the v3 anchors (`config/anchors/*_b1.csv` for the age × sex × edu
  conditioning, `kcvs_joint_b2.csv` for the observed PV × RP joint) with `.source.json` provenance.
- **Code** — construction (`build_anchor_b1.py`, `build_anchor_kcvs_joint.py`, `build_anchor_fv_b1.py`,
  `enrich_stage1.py --b2`, `enrich_stage2_3.py`) and validation (`validate_fidelity.py --v3`,
  `validate_roundtrip.py`, `audit_joint.py`, `crossmodel_extract.py`, `demo_cohort.py`, `fig_pipeline.py`,
  `audit_stereotype.py`, `build_face_validity_sheet.py`).

The raw 1M backbone is not redistributed; users download it from the upstream source. Aggregate
anchor tables are public with source attribution. Code is MIT; derived data and docs are CC-BY-4.0.
A Zenodo deposit and DOI are pending (§6).

## 4. Technical Validation

### 4.1 Distributional fidelity to anchors (Figure 2)

Over the full one million records, the synthetic conditional `P(level | cell)` matches each anchor
closely. Weighted mean per-cell Total Variation Distance ranges from 0.0007 (prior_victimization ×
reporting joint) to 0.0034 (authority_deference); the largest single-cell TVD is 0.0163, in a small
authority-deference cell (n ≈ 2,556). The residual is sampling noise, not estimation error — attributes are drawn from the
anchors, so the match holds by construction and the deviation shrinks with cell size. Figure 2 plots
synthetic against anchor probability across all 80 cell-level pairs (points on the diagonal),
digital literacy by age band for the lower-education tier, and the per-attribute deviation. This
figure checks the sampler, not the world: because the levels were drawn from these anchors, agreement
is expected and the residual is Monte-Carlo noise. It establishes that the construction reproduces its
inputs faithfully. Whether the anchors themselves model the Korean population is a separate question,
carried by the choice of national-survey sources (§2.3) and, for the realized narratives, by §4.2 and
§4.4. One out-of-sample check now addresses this directly. The digital-literacy attribute is anchored
on the 디지털정보격차 실태조사 competency battery and never ingests internet-use rates; yet its
competency gradient by age rank-predicts the age gradient of internet use measured by a separate
national survey (인터넷이용실태조사) [7], across five age bands — Spearman ρ = 0.975 (n = 5; the p-value is uninformative at this n), with both series showing the same
elderly cliff (KVRB high-literacy share 28.9% → 5.3% across 45–59 → 75+; external use rate 98.5% →
≈52%). Two instruments from two surveys recover the same latent gradient. We report this as suggestive
only: with five age bands and both series declining monotonically with age, the rank agreement is close to
automatic and carries little independent information — consistent with the competency anchor not being far
off for one attribute, no more. (The synthetic digital-literacy marginal matches the NIA competency
distribution it samples but diverges sharply from activity-based prevalence — see §4.6.) The joint across
attributes is adjudicated more directly in §4.6. External
figures are approximate and the test is rank-based; convergent validity, not identity. (results/C1_external_validity.png.)

### 4.2 Round-trip agreement (Figure 3)

The round-trip ran on a stratified 2,000-persona sample (200 per age-band x sex cell) with
gemini-2.5-flash, after which the level extractor re-read each Likert value from the generated
narrative. On quadratic weighted kappa — the metric that fits an ordinal scale [11] — agreement is
substantial to almost perfect: 0.885 for social isolation, 0.879 for financial vulnerability, 0.875
for authority deference, and 0.730 for digital literacy. Agreement within one level runs from 91.7%
(digital literacy) to 96.6% (authority deference and social isolation); mean absolute error stays
between 0.33 and 0.59 of a level. Exact five-level recovery is lower, 58.1% to 73.4%, because
natural-language rendering blurs adjacent levels — a narrative written for level 4 ("재정적으로 빠듯")
is sometimes read back as 3 or 5. The confusion matrices in Figure 3 concentrate on the diagonal and
its neighbors. Digital literacy is the weakest, and for a closed-loop encode-decode a kappa of 0.730 with 58.1% exact recovery is mediocre rather than reassuring:
a single combined-extraction call recovers all four levels at once, and digital competence is the
attribute a reader most often places one step off. This reverses the smaller N=200 pilot, where digital
literacy round-tripped best — the larger stratified sample, which loads more sparse elderly and
low-education cells, is the more honest estimate.

A separate check addresses whether agreement is merely a model agreeing with itself. On the earlier
200-narrative pass, a different provider — OpenAI gpt-4o-2024-11-20 — re-extracted each level from the
same Gemini narratives (n = 120 after parse-rate exclusion). Between-model agreement held: weighted
kappa 0.88 (authority deference), 0.89 (digital literacy), 0.84 (financial vulnerability), 0.77 (social
isolation), within-one 0.89 to 1.00. The encoded level therefore survives a model boundary; it is in
the text, not an artifact of one model reading its own output. Two cautions remain. The round-trip is
synthetic throughout — no human re-read — so it measures whether the narrative faithfully encodes the
fixed input, not whether a person would read it the same way. And N = 2,000 is a 0.2% probe of the
million, stratified to span the cell range rather than to be representative. Summaries: within-model
`results_N2000/roundtrip_summary.csv`, cross-model `results_xmodel/roundtrip_summary.csv`.

### 4.3 Stereotype audit (Figure 5)

The attributes are sampled on age band, and digital literacy also on education tier. A
protected-attribute audit asks whether the released attributes carry association with sex or province
that the conditioning does not justify. Two patterns matter. First, digital literacy by sex: its
marginal association (Cramér's V [9] = 0.078) shrinks to 0.005 within the justified age × education cells —
the marginal link runs through education tier, a justified conditioner, not through sex itself. Second,
and the largest residual in the set under v3 conditioning, authority deference by sex (Cramér's V =
0.145). This is not an artifact the pipeline introduced: authority deference is anchored on KGSS, which
records a real individual-level sex difference in deference, so conditioning on age × sex × education
reproduces that measured relationship rather than fabricating one. Social isolation by sex (0.084) and
the two KCVS attributes by sex (≈0.04) are measured KGSS/KCVS relationships in the same way; province
residuals stay ≤ 0.021 across all attributes. These residuals inherit their anchors' sampling uncertainty — the deference anchor (KGSS, N = 922) and the isolation anchor (N = 2,686) are small — so the projected sex associations should be read with the source survey's confidence interval in mind, not as exact population values. The audit also caught one association the pipeline *did*
introduce, and we removed it: an earlier financial-vulnerability-by-sex link of 0.245, traced to
household-head sex (heads are 71% male, which does not proxy persona sex). We cut it by making financial
vulnerability sex-invariant, after which its residual falls to 0.033. The distinction the audit enforces
— measured-and-surfaced versus introduced-and-removed — is the point: Figure 5 reports the full table
for the reuser to weigh, flagging authority-deference × sex as a KGSS-grounded relationship to interpret,
not a defect to discount. Audit code: `src/audit_stereotype.py`; full table:
`results/stereotype_audit_v3.csv`.

### 4.4 Face validity

Two raters — one author and one independent domain expert — scored the same blind 50-persona sample on
two axes: demographic plausibility (1–5) and whether the narrative carried all four codes in the right
direction. Mean plausibility was 4.54 and 4.68; the two raters placed 42 and 47 of 50 personas at 4 or 5. Both
recorded directional consistency on every narrative for all four attributes (100% / 100%), including
the reversed coding of financial vulnerability (higher = more vulnerable) — complete agreement on that
axis. The strongest reliability signal is that the two raters independently flagged the *same*
personas: the below-4 cases are demographic, not attribute, failures, and both raters named them — two
life-course timing errors (a 20-year-old described as a junior-college graduate already in work, which
leaves no room for study plus military service; a 23-year-old four-year graduate working as a
professional), elderly personas paired with high digital literacy, and family-cohabiting personas
sampled at maximum isolation. That convergence both supports inter-rater reliability and confirms these
are real limitations (§5.3), not one rater's idiosyncrasy. The family-cohabiting maximum-isolation
cases remain consistent under the structural definition of social_isolation (support-network deficit,
not physical aloneness; §2.3). Attribute intensity sometimes softened — an extreme code such as
authority-deference 1 ("rarely defers") occasionally read as a moderate "tends not to" — but never
flipped. Inter-rater reliability on the ordinal plausibility is substantial: quadratic-weighted Cohen's kappa [10] = 0.63 (exact 78%, within-one-level 92%, mean absolute difference 0.30) — a kappa deflated by restriction of range, since both raters placed most personas at 4–5, so the 78% raw agreement is the fairer read, computed by
`src/face_validity_kappa.py` from the two released score sheets
(`results/face_validity_rater_A.xlsx`, `results/face_validity_rater_B.xlsx`).

### 4.5 Inter-attribute structure (Figure 6)

A reuser running a multi-attribute simulation needs to know what joint structure the dataset carries,
and how far to trust it. There is some structure, from two routes, and it is bounded. Figure 6 reports pairwise
correlations both marginally and within age band. Conditioning each survey-direct attribute on shared
demographics — age, plus sex and education where a survey records them on the same respondents — lifts
the within-age correlations off zero; the largest is financial vulnerability with digital literacy at
|r| ≈ 0.09, both tied to education. These stay small because the demographic channel only carries part
of the real covariance. One pair is sampled from a genuine observed joint rather than two independent marginals: victimization and reporting (KCVS, same respondents). The released pair matches that survey joint to within a per-cell total variation distance of 0.002 — but by construction, since it is drawn from it, so the number confirms faithful sampling, not that the survey's joint transfers to any other population. Every other cross-survey pair rests on conditional independence given the demographic vector — an assumption we state plainly and have not verified.

Two cautions bound the gain. The conditioning induces correlation but not a within-cell joint, so the
simultaneous-extreme combinations a tighter model would suppress fall only modestly — personas at once
maximally financially vulnerable and maximally digitally literate move from 4.81% to 4.72%. And
conditioning on real survey demographics also reproduces real demographic associations: authority
deference varies with sex in KGSS (residual Cramér V ≈ 0.15), which the stereotype audit (§4.3) flags
for the reuser to weigh — a measured relationship rather than one the pipeline introduced. We did
remove one that was introduced: an earlier financial-vulnerability-by-sex association traced to
household-head conditioning, which we cut by making that attribute sex-invariant. Whether these anchors
and this conditioning represent the Korean population well enough for a given use remains open to the
further, and likely adversarial, validation a dataset like this should invite. Audit code:
`src/audit_joint.py`, `src/audit_stereotype.py`; table: `results/joint_audit.csv`.

### 4.6 External validation of joint structure (Figure 7)

The fidelity and round-trip checks above stay inside the construction: they confirm the sampler reproduces
its anchors and the narrative encodes the sampled value. Neither reaches the one thing a multi-attribute
reuser most needs and the anchors never observed — the joint across attributes drawn from different
surveys. We test it against a survey that was not an anchor and that measures three of the attributes on
the same elders: the 2023 National Survey of Older Koreans (노인실태조사 [8]; N = 10,078 aged 65+). Financial
vulnerability maps to its household-income quintile (inverted), digital literacy to a count of thirteen
device activities, and social isolation to the support-availability battery — people to turn to when
depressed, ill, or short of money — the same structural-support construct the KGSS anchor uses. The survey
shares no respondents and no instrument with the anchors, so for the joint the comparison is genuinely
out-of-sample.

Two results follow, and they cut in opposite directions. The real attributes are positively dependent:
the share of elders who are at once high financial vulnerability, low digital literacy, and high social
isolation is 2.36 times what their marginals give under independence (95% bootstrap CI 2.20–2.55 [12]), and the
real pairwise associations (Cramér's V: financial × digital 0.21, digital × isolation 0.13, financial ×
isolation 0.11) run two to six times the released dataset's (0.09, 0.03, 0.02). The conditional-independence
structure the fusion rests on [13,14] under-states real compounding — a limitation §4.5 stated and we can now
quantify rather than assert. The larger gap, though, is in a marginal, not the joint: the dataset places
85% of elders at low digital literacy against 37% in the survey. Part of this is instrument difference — a
competency battery versus a count of basic activities — but a 48-point gap is too large for that alone, and
our own §4.1 external series (75+ internet use ≈52%) makes an 85% low-literacy elderly share implausibly
pessimistic. We therefore do not treat the elderly digital-literacy marginal as a trustworthy prevalence:
we compare the dependence structure (instrument-robust) for the joint claim, and we restrict the elderly
digital-literacy attribute to within-cohort ordinal use, not population prevalence (§5.3). Recalibrating that
anchor is a release blocker, not a deferred nicety.

| Quantity (elderly 65+) | Real (노인실태조사 2023) | KVRB v3 |
|---|---|---|
| High financial-vulnerability share | 0.40 | 0.42 |
| Low digital-literacy share | 0.37 | 0.85 |
| High social-isolation share | 0.14 | 0.30 |
| Simultaneous-extreme rate | 0.048 | 0.116 |
| Independence-implied rate | 0.021 | 0.106 |
| **Dependence ratio (extreme ÷ independence)** | **2.36** | **1.09** |
| Pairwise V (FV×SI / FV×DL / DL×SI) | 0.11 / 0.21 / 0.13 | 0.02 / 0.09 / 0.03 |

The reading is that the dataset is a faithful sampler of its anchors (§4.1) whose realized joint is partial
and conservative in dependence yet pessimistic in the elderly digital-literacy marginal. A reuser building
compound-vulnerability cohorts should treat the co-occurrence of extremes as under-modelled and the
absolute elderly digital-exclusion rate as over-stated, and should validate against a same-respondent
source where one exists, as we did here. This external check is elderly-scoped (65+); the joint for the
non-elderly majority of the release is not externally validated and rests on the stated conditional
independence of §4.5, which a future release should test on a non-elderly band. Code:
`src/validate_joint_external_noin2023.py`; table `results/joint_external_noin2023.csv`.

## 5. Usage Notes

### 5.1 Demonstration — elderly voice-phishing cohort (Figure 4)

Selecting the cohort prevention work targets (age ≥ 65, single-person household, lower education)
returns 44,362 personas, 4.4% of the million — slightly below the 5–8% the cohort spec anticipated.
The cohort's risk profile separates from the population on the dimensions voice-phishing exploits:
low digital literacy at 0.92 versus 0.42 (×2.2), high authority deference at 0.61 versus 0.41 (×1.5).
Financial vulnerability barely moves (0.47 versus 0.46, ×1.0) and social isolation does not rise (0.31
versus 0.32, ×1.0). Isolation stays flat even though it now conditions on education, because the cohort's
defining axis — single-person household — is not a conditioner for social_isolation, and the age ×
education channel nets flat for this group (§2.3); a household-type-conditioned anchor would change this.
The profile is a usage demonstration of how to query the layer, not an independent finding and not a
targeting recommendation: it builds a high-*susceptibility* cohort, which — as the voice-phishing caveat
below shows — is not the same as a high realized-*loss* cohort, so an analyst directing real interventions
must intersect this susceptibility profile with an exposure/income variable. The attribute draw is driven by age, sex, and education — the v3
conditioners; selecting on occupation, region, or household type does not shift the attribute
distributions, so reusers should read a cohort's attribute profile as demographic-driven along those three axes.

Applying the same external survey to this use case adds a caution worth stating. Among the 10,078 elders,
voice-phishing financial loss does not fall on the most digitally excluded; it rises with digital engagement
(smartphone users 1.75% vs non-users 0.34%; odds ratio 3.0) and, holding income, with both income and
engagement, reaching about 4% among higher-income digital elders. Realized loss tracks exposure and
transaction capacity, which run opposite to the digital illiteracy that susceptibility-based accounts
emphasize. The cohort selected here — low digital literacy, single-person household, lower education — is
therefore high in *susceptibility* but not necessarily in realized *loss*, a distinction prevention
targeting should keep; the full income × engagement × loss analysis is developed separately (in preparation).
The cohort remains a valid demonstration of how to query the layer, not a victimization prevalence claim.

### 5.2 Other uses

Cohort selection for GABM/agent simulation, prevention-message A/B testing, and officer-training
victim interviews. The shared persona pool also serves robustness substrates for related tracks.

### 5.3 Limitations

Personas are synthetic; behavioral attributes are proxies, not measured traits. Conditioning uses
age, sex, and education but not every relevant variable — family type, for one, is not a conditioner —
so an attribute and a non-conditioned selection variable can still move independently: a
family-cohabiting persona can draw maximum structural isolation.
Narrative realization also produces occasional life-course timing that does not cohere with the
sampled demographics — a 20-year-old already holding a college degree and a job — which both
face-validity raters independently flagged (§4.4) but the pipeline does not yet prevent. Inter-attribute
structure is partial and runs mainly through shared demographics: conditioning induces only modest
within-age correlation (§4.5), one pair (victimization–reporting) comes from an observed joint, and most
cross-survey correlations among vulnerabilities — financial strain and isolation, say — are not directly
modeled but rest on stated conditional independence, so simulation users needing fuller covariance should
add it and validate against their own target. The `reporting_propensity` 75+ cell is low-N. `scam_susceptibility` is Tier-3 qualitative-only and excluded from quantitative
claims. Two limits are now quantified rather than asserted: the cross-survey conditional-independence
assumption under-states the elderly compound-vulnerability tail by about 2.4× (§4.6, elderly-scoped; the
non-elderly joint is unvalidated), and the elderly digital-literacy marginal runs implausibly pessimistic
against a same-respondent survey (85% vs 37%). Until that anchor is recalibrated, the elderly
digital-literacy attribute must be used as a within-cohort ordinal/relative measure only — not as a
population prevalence, and not for real-world budget or resource allocation (e.g., physical-outreach vs
digital-campaign sizing); valid use is correlational and structural testing. Results should be replicated on
real population data before any operational use.

### 5.4 Ethics & dual-use

No record corresponds to a real person. Every persona is synthetic, carries no personally identifying
information, and cannot be traced to an individual; the attribute layer is sampled from aggregate
survey distributions, never from microdata about a person. Coverage stops at adults — ages 19 to 99 —
so no minor is represented; the backbone fixes every age at 19 or above, and the face-validity screen
(§4.4) checks that the narrative does not misstate it.

The attributes exist to direct protection, not to describe individuals. A cohort names a population
segment a prevention program might prioritize, such as isolated older adults with low digital literacy;
it is not a list of people and must not be used as one. Targeting real individuals, offender profiling,
and presenting synthetic personas as real victims are out of scope and prohibited.

A profile built to direct prevention could also point an offender toward softer targets. The release
limits that exposure. Operational cohort thresholds are abstracted and kept in a
git-ignored local config, so the public repository ships the method rather than the cutoffs.
scam_susceptibility, the one attribute with no survey anchor, stays Tier-3 qualitative-only and out of
the quantitative release. Published anchors are aggregate conditional tables; the underlying survey
microdata is not.

Two anchor sources carry use restrictions that the release honors. The NIA digital-divide survey is
classified 제2유형 (non-commercial) and the KCVS is 제4유형 (non-commercial, no-derivatives). For both,
only aggregate conditional probabilities appear in the anchor tables, with source attribution, and the
raw microdata is not redistributed. Full statements are in ETHICS.md and LICENSE-DATA.md.

## 6. Code & Data Availability

- **Code:** MIT, `korea-victimization-risk-benchmark/` (GitHub; public at submission).
- **Derived data & docs:** CC-BY-4.0; archived at Zenodo (DOI finalized at submission).
- **Backbone:** NVIDIA Nemotron-Personas-Korea (release 2026-04-20), CC-BY-4.0; reproduce from the pinned
  upstream version (exact snapshot id/hash recorded in the repo to guard against upstream drift); not redistributed here.
- **Author / citation:** `CITATION.cff` (name, ORCID) completed before deposit.

---

## References

1. NVIDIA. (2026). Nemotron-Personas-Korea [Data set]. Hugging Face. Released 2026-04-20.
2. Statistics Korea. (2021). 2020 Population and Housing Census. Korean Statistical Information Service (KOSIS).
3. Statistics Korea. (2024). Survey of Household Finances and Living Conditions (가계금융복지조사).
4. National Information Society Agency. (2024). The Report on the Digital Divide (디지털정보격차 실태조사). Ministry of Science and ICT.
5. Korean General Social Survey (KGSS). Survey Research Center, Sungkyunkwan University (AUTHORT module 2016; social-support battery 2004, 2012).
6. Korean Crime Victim Survey (KCVS) 2018. Korean Institute of Criminology and Justice.
7. National Information Society Agency. Survey on Internet Use (인터넷이용실태조사). Ministry of Science and ICT.
8. Korea Institute for Health and Social Affairs. (2023). National Survey of Older Koreans (노인실태조사). Ministry of Health and Welfare.
9. Cramér, H. (1946). Mathematical Methods of Statistics. Princeton University Press.
10. Cohen, J. (1960). A coefficient of agreement for nominal scales. Educational and Psychological Measurement, 20(1), 37–46.
11. Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. Biometrics, 33(1), 159–174.
12. Efron, B. (1979). Bootstrap methods: Another look at the jackknife. The Annals of Statistics, 7(1), 1–26.
13. D'Orazio, M., Di Zio, M., & Scanu, M. (2006). Statistical Matching: Theory and Practice. Wiley.
14. Rässler, S. (2002). Statistical Matching: A Frequentist Theory, Practical Applications, and Alternative Bayesian Approaches. Springer.

(Survey years are those cited in §2.3; DOIs/URLs and access dates to be finalized at journal formatting.)

## Appendix A. Generation prompt and model

Stage-2 narrative realization used the verbatim Korean prompt below, with the persona's demographics
and fixed attribute levels interpolated. The instruction states the levels are fixed inputs to express,
not to estimate.

```
다음은 합성 페르소나의 인구통계와, 실제 조사 분포에서 '이미 정해진' 속성값(1~5)이다.
이 값들은 고정 입력이다. 추정하거나 바꾸지 말고, 값과 모순되지 않는 1인칭 한국어 서술(4~6문장)만 작성하라.
네 속성(재정 취약성/디지털 활용/권위 순응/사회적 고립) 각각이 서술에서 드러나야 한다.
인구통계: {demographics JSON}
고정 속성값(1=낮음~5=높음): {attribute levels JSON}
서술:
```

Stage-3 re-extraction asked the model for a single integer 1–5 per attribute, no explanation. The
generation and extraction model was requested as `gemini-2.5-flash`; this is a stable pointer, not a
dated snapshot, because the dated `gemini-2.0-flash-001` was retired for new accounts at the time of
the run. The exact responding model id is captured per record in `gen_meta.actual_model`. Temperature
was 0.7 for generation. For full reproducibility a dated snapshot should be pinned once available.

### Figures (in `results/`)
- **F1** `F1_pipeline.png` — construction pipeline (sample → render → round-trip).
- **F2** `F2_distributional_fidelity_v3.png` — by-construction fidelity to survey anchors (v3, 1M; weighted per-cell TVD <= 0.0034).
- **F3** `results_N2000/F3_roundtrip_consistency.png` — round-trip reliability (gemini-2.5-flash, stratified N=2000; qwk 0.73-0.89, within-1 0.92-0.97). Cross-model confirmation (gpt-4o-2024-11-20, n=120; qwk 0.77-0.89) in `results_xmodel/`.
- **F4** `F4_elderly_phishing_cohort_v3.png` — elderly voice-phishing cohort (usage example, not validation; v3, 1M).
- **F5** `F5_stereotype_audit_v3.png` — protected-attribute audit (v3; max residual Cramer V = 0.145, AD x sex, a measured KGSS relationship).
- **F6** `F6_joint_b1b2.png` — inter-attribute structure under Route-B (within-age |r| up to 0.093); `F6prime_pvrp_joint_b2.png` — observed PV x RP joint (per-cell TVD <= 0.002); `C1_external_validity.png` — out-of-sample convergent validity (Spearman rho 0.975).
- **F7** `F7_external_joint_noin2023.png` — external joint validation vs 노인실태조사 2023 (elderly 65+): real dependence 2.36x independence (95% CI 2.20-2.55) vs KVRB near-independent (1.09x); pairwise Cramér's V real > KVRB on all three pairs.
