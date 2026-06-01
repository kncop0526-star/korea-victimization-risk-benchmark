# Data / Resource Paper Outline / 데이터·리소스 논문 개요

A plan to publish KVRB as a citable **data descriptor / resource paper**. This positions the dataset
(not just a study) as the contribution, which fits the "make it, put my name on it" goal and yields
a clean citation for the rest of the portfolio.

---

## 1. Working title

> *A survey-anchored synthetic persona dataset with crime-prevention behavioral attributes for
> Korean police-administration research.*

(KO) *경찰행정 연구를 위한, 조사 기반 앵커링 합성 페르소나 데이터셋 — 범죄예방 행동·취약성 속성 증강.*

## 2. One-paragraph contribution claim

We release a synthetic persona dataset that augments the demographically realistic
Nemotron-Personas-Korea backbone with a layer of crime-prevention behavioral attributes
(digital/financial literacy, social isolation, prior victimization, reporting propensity, …). The
methodological contribution is **survey-conditioned enrichment**: attribute values are sampled from
real Korean survey conditional distributions and an LLM only renders them into narrative, so the
dataset's attribute distributions match national surveys *by construction* rather than by assertion.
We provide the dataset, the construction code, the anchor-table specifications, and a technical
validation (distributional fidelity, round-trip consistency, stereotype audit), with explicit ethics
and dual-use safeguards.

## 3. Target venues (decide before writing)

| Venue | Type | Fit | Notes |
|-------|------|-----|-------|
| **Scientific Data** (Nature) | data descriptor (SCIE) | high | Strong for open synthetic datasets; strict on data availability + technical validation. Prestige. |
| **Data in Brief** (Elsevier) | data article | high, lighter | Fast, companion-data style; lower bar; pairs well with a separate methods/application paper. |
| **Crime Science** (open access) | domain | medium | If framed as a crime-prevention resource + demonstration. |
| A computational-social-science / CSS venue | methods | medium | If the enrichment method is the headline over the data. |

Recommended: **Scientific Data** if technical validation is thorough; **Data in Brief** as the
fast-track fallback. Both require the dataset to be openly deposited (Zenodo/OSF) with a DOI.

## 4. Section structure (data-descriptor format)

1. **Background & Summary** — gap: KOSIS-realistic personas exist but lack behavioral/victimization
   variables that Korean police-prevention research needs; introduce survey-anchored enrichment.
2. **Methods**
   - 2.1 Demographic backbone (Nemotron, CC-BY-4.0, KOSIS validation recap).
   - 2.2 Attribute schema (the new layer; tiers).
   - 2.3 Survey anchoring (sources, weighting, crosswalks, `P(level|cell)`).
   - 2.4 LLM narrative realization (pinned model, prompt design, "render-not-estimate").
   - 2.5 Round-trip consistency audit.
3. **Data Records** — files, formats (parquet/CSV/JSONL), schema dictionary, record counts,
   repository/Zenodo DOI, anchor-version metadata.
4. **Technical Validation**
   - 4.1 Distributional fidelity to anchors (by-construction match + deviation report).
   - 4.2 Round-trip agreement rate (reliability).
   - 4.3 Stereotype audit (no spurious protected-attribute effects beyond survey-justified).
   - 4.4 Face validity (expert review of N samples).
5. **Usage Notes** — cohort selection, GABM/simulation use, prevention-message testing, officer
   training; **Limitations** (synthetic, low-dim conditionals, Tier-3 caveats); **Ethics & dual-use**.
6. **Code Availability** (MIT repo) / **Data Availability** (CC-BY-4.0, Zenodo DOI).

## 5. Figures & tables to produce

- T1: attribute schema with anchor source + tier (from `attribute_schema.md`).
- T2: data records — files, formats, counts.
- F1: pipeline diagram (sample → render → round-trip).
- F2: distributional fidelity — synthetic vs survey for 2–3 Tier-1 attributes (e.g., digital
  literacy by age band).
- F3: round-trip agreement by attribute.
- F4 (optional): a demonstration — elderly voice-phishing cohort vulnerability profile.

## 6. What must be done before submission (gating)

1. Source **≥2 Tier-1 anchors** for real (digital literacy; victimization/reporting) — see
   `anchor_sourcing_plan.md`. Placeholder anchors cannot appear in a submission.
2. Wire a **pinned LLM** for Stage 2 + a real extractor for Stage 3; report model + version.
3. Generate a released dataset version (decide N: full 1M vs a documented stratified sample).
4. Run the **technical validation** suite and produce F2–F3.
5. Deposit on **Zenodo/OSF** → mint DOI; fill `CITATION.cff`.
6. Ethics statement + dual-use section finalized; confirm institutional clearance for release.
7. AI-writing-style pass on the manuscript (portfolio TYPE-B rule) before EM submission.

## 7. Portfolio linkage / 기존 트랙 연계

- **Companion to the elderly-phishing GABM paper** — this dataset can be cited as the persona source
  / robustness substrate (Appendix B), and the GABM paper can be cited as a demonstration of use.
- Reusable substrate for the cognitive-warfare / Delphi tracks (shared persona pool).
- Could register as a new portfolio track ("KVRB resource paper") with its own status row.

## 8. Authorship & credit framing

- You are the author of the **enrichment method, attribute schema, anchoring, and validation**.
- NVIDIA Nemotron is cited as the **backbone source** (CC-BY-4.0); national surveys are cited as
  **anchor sources**. The paper makes this layered provenance explicit (no over-claiming).
