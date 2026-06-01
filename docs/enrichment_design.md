# Persona Enrichment Methodology / 페르소나 증강 방법론

This is the **primary intellectual contribution** of the project: a method for adding
crime-prevention-relevant behavioral attributes to the Nemotron demographic backbone, in a way
that survives peer review.

> One-line claim: *Survey-conditioned synthetic enrichment — attribute values are sampled from
> real Korean survey distributions; the LLM only renders them into coherent narrative; both the
> distribution and the narrative are then validated.*

---

## 1. Why enrichment, not generation-from-scratch

Nemotron-Personas-Korea provides demographically realistic (KOSIS-validated) personas but carries
**no behavioral or victimization variables**. Police-administration research needs exactly those.
We therefore keep Nemotron's demographic backbone D and add a new attribute layer A.

The naive approach — "ask an LLM to estimate each persona's scam susceptibility" — fails review:
the resulting distribution reflects the LLM's prior, not Korean reality, and has no ground truth.
We avoid this by separating **where the numbers come from** (real surveys) from **how they are
expressed** (LLM narrative).

## 2. The three-stage pipeline

```
Nemotron persona (D) ─► [1] SAMPLE A from P(A | D)  (real survey conditionals)
                     ─► [2] RENDER narrative from (D, A)  (LLM as writer, not estimator)
                     ─► [3] ROUND-TRIP extract A' from narrative; check A' ≈ A
                     ─► enriched persona (D, A, narrative)  +  per-record validation flags
```

### Stage 1 — Survey-conditioned sampling (the rigor)
For each new attribute we obtain a **conditional distribution** `P(attribute | subset of D)` from a
real Korean survey and **sample** the persona's value from the matching cell (plus calibrated
noise). Because values are drawn from real distributions, the enriched dataset matches the survey
**by construction** — fidelity is guaranteed at sampling time, not hoped for afterward.

- Example: `digital_literacy` is sampled from a `score | age_band × region × education` table
  derived from the national digital-divide survey, so the synthetic age gradient equals the real
  one.

Joint dependence between attributes is handled by **sequential conditioning** (sample attribute
*k* conditioned on D and on already-sampled attributes 1…*k*−1) where a survey supports it; where
it does not, attributes are sampled independently and this limitation is recorded.

### Stage 2 — LLM narrative realization (the texture)
The LLM receives `(D, sampled A)` and writes a short persona narrative **consistent with the given
values**. It is explicitly instructed that the numeric/categorical attributes are fixed inputs, not
things to estimate. The LLM adds plausible texture (daily routine, reasoning) but cannot move the
distribution. Model version is pinned and `actual_model` is captured per record.

### Stage 3 — Round-trip consistency check (the audit)
A second pass (LLM or lightweight classifier) reads the generated narrative and **re-extracts** the
attributes `A'`. We flag any record where `A'` materially disagrees with the sampled `A` (e.g., a
"low digital literacy" persona narrated as a software engineer). Agreement rate is a headline
quality metric and supports a clean reliability statistic for the paper.

## 3. Anchor sources / 앵커 출처

Each attribute must name a real Korean source for its conditional distribution. Candidate sources
(exact instrument names, conducting bodies, and years **must be verified before citation** — do not
hard-cite from this design doc):

| Attribute family | Candidate anchor source (verify before citing) |
|------------------|-----------------------------------------------|
| Digital / device / online literacy | National digital-divide survey (과기정통부·NIA) |
| General victimization rate, reporting rate | National crime victim survey / KCVS (KIC·KICJ) |
| Phishing/voice-phishing exposure & loss | 금융감독원 · 경찰청 보이스피싱 통계 |
| Social isolation / living-alone | 통계청 사회조사 · 독거노인 통계 |
| Financial vulnerability / assets | 가계금융복지조사 (통계청·한국은행·금감원) |

**Anchor-strength tiers** (recorded per attribute in the schema):
- **Tier 1 (strong):** direct survey conditional exists → sample from it.
- **Tier 2 (partial):** survey gives marginals only → sample from marginal, condition narrative.
- **Tier 3 (weak / LLM-prior):** no survey → value is an LLM-prior estimate; **flagged low-confidence**
  and excluded from any quantitative claim. Susceptibility-type constructs usually fall here.

## 4. Validation plan / 검증

1. **Distributional fidelity** — compare enriched marginals/conditionals to the anchor (Tier 1/2);
   report deviation. By-construction match is expected; this confirms sampling correctness.
2. **Round-trip agreement** — % of records where re-extracted A' matches sampled A (Stage 3).
3. **Internal consistency** — rule checks for impossible combinations (occupation vs literacy, etc.).
4. **Face validity** — manual review of ~50 enriched personas by a domain expert.
5. **Stereotype audit** — verify attribute–demographic correlations do not exceed what the anchoring
   survey justifies (no spurious protected-attribute effects introduced by the LLM).

## 5. Honest limitations / 한계 (must appear in any paper)

- Surveys give low-dimensional conditionals; full joint dependence among attributes is
  approximated, not measured.
- Tier 3 attributes reflect model priors, not Korean ground truth → qualitative use only.
- The dataset remains **synthetic**; it complements but does not replace real victimization
  microdata. Replication on real data (KCVS/KLIPS) is recommended follow-up.
- LLM rendering can inject subtle stereotype texture → Stage 3 + stereotype audit are mandatory,
  not optional.

## 6. Why this is publishable

The method is a concrete, reusable recipe (survey-conditioned sampling + LLM realization +
round-trip audit), specialized to the Korean police-prevention domain with a named attribute set
and named anchors. It yields a citable dataset/resource and a methods contribution, while
defusing the standard "synthetic-data hallucination" objection by design rather than by argument.
