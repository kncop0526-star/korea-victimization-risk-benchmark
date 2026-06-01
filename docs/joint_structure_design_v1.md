# Joint-Structure Design (Route B — toward a Nemotron-tier behavioral dataset)

Goal: replace the current per-attribute independence (F6) with realistic inter-attribute structure,
**without fabricating dependence**. The honest constraint that shapes everything below: attributes
come from different surveys with different respondents, so not every joint is observable.

## 0. What is and is not observable

| Block | Attributes | Survey | Joint within block? |
|---|---|---|---|
| Finance | financial_vulnerability | 가계금융복지조사 | (single attribute) |
| Digital | digital_literacy | 디지털정보격차 (NIA) | (single attribute) |
| **KGSS** | **authority_deference, social_isolation** | KGSS | **YES — same respondents** |
| **KCVS** | **prior_victimization, reporting_propensity** | KCVS | **YES — same respondents** |

- **Observable joints (use directly, no assumption):** AD×SI (KGSS), PV×RP (KCVS).
- **Unobservable cross-block joints** (FV↔DL↔KGSS↔KCVS): no survey measures them on the same people.
  These must be handled by *shared demographic conditioning* (defensible) and, only where a target
  estimate exists, a *calibrated copula* (assumption — flag it). Do NOT invent cross-block correlation.

The methodological contribution becomes **survey data fusion for behavioral persona enrichment** — a
real, citable method, not a hack.

## 1. The three honest upgrades (in priority order)

### B1. Richer demographic conditioning (biggest honest win, no assumptions)
Re-estimate every anchor on the largest demographic cell its survey N supports — target
`age_band × sex × education_tier` (add `region` only where N per cell stays usable). Today most
anchors condition on `age_band` alone, which is exactly why F6 shows within-age independence.
Conditioning on shared demographics induces realistic cross-attribute correlation *through common
causes* (a low-education older person is jointly more financially strained, less digital, more
isolated) — and it is fully data-grounded. This alone should move the F6 within-cell correlations off
zero in the right direction. **Requires:** raw microdata (KVRB_DATA_ROOT / Paper F 04_data) + re-run
of `build_anchor_*.py` with added conditioners + N-floor guard per cell (collapse sparse cells).

### B2. Within-survey joint sampling (use the observed joints)
For KGSS sample the **pair** (AD, SI) jointly from the survey's empirical joint `P(AD, SI | cell)`
instead of two independent marginals; likewise (PV, RP) from KCVS. This preserves the real covariance
those surveys actually measured. **Requires:** new `build_anchor_kgss_joint.py`,
`build_anchor_kcvs_joint.py` emitting joint cells; Stage-1 sampler change to draw blocks jointly.

### B3. Cross-block dependence (the residual — assumption-bounded)
After B1+B2, cross-block pairs (e.g., FV↔SI) still rely on shared-demographic correlation only. Two
honest options:
- **(default) Conditional independence given the rich demographic vector** — state it plainly; it is
  far weaker than today's "given age only," and B1 makes it defensible.
- **(optional) Gaussian copula calibrated to an external estimate** — only if a credible source gives
  a target correlation (e.g., a single survey or KOSIS table carrying two of the blocks). Calibrate,
  cite the target, report the imposed correlation. Never a free parameter.

## 2. New validation (what replaces / augments F6)

- **F6′ joint fidelity:** synthetic AD×SI joint vs KGSS observed joint (and PV×RP vs KCVS) — TVD on
  the 2-D joint, not just marginals. This is the headline "we preserved real covariance" evidence.
- **F6 update:** within-cell cross-attribute correlation should now be non-zero and *match* the
  survey-implied values where observable; report match, not just "near zero."
- **Extreme-combo rate:** the 4.81% incoherent FV5+DL5 share should drop measurably after B1.
- Keep F2 (marginals still match), F3 (round-trip), F5 (stereotype), F4 (cohort demo).

## 3. External validity (answers reviewer C1, parallel track)
Independent of joint structure: pick ONE statistic the dataset never ingested and predict it —
e.g., use the digital-literacy anchor to predict an internet-use rate from a *different* survey/year,
or compare the elderly cohort's profile to a KNPA voice-phishing victim statistic. One out-of-sample
hit converts §4.1 from sampler-check to validation.

## 4. Work phases (rough)
1. **Audit raw microdata** — confirm KGSS carries AD+SI jointly + demographics (SEX/EDUC/region);
   confirm KCVS carries PV+RP jointly; confirm 가금복/디지털격차 demographic granularity. (Daniel's PC.)
2. **B1 richer conditioning** — re-run anchor builders with age×sex×edu; N-floor guard; regen 1M; re-run F6.
3. **B2 joint blocks** — KGSS/KCVS joint anchors + sampler change; F6′ joint-fidelity figure.
4. **B3 decide** cross-block: conditional-independence statement (default) vs calibrated copula.
5. **External check** (C1) + cross-model round-trip (C2/C3) + 2nd rater (face validity).
6. Rewrite §2–§4 around data fusion; re-run adversarial review; target Scientific Data.

## 5. Honest ceiling note
B1+B2 make the dataset genuinely covariance-aware where surveys support it, and explicit where they
don't — that is the Nemotron-analogue bar (Nemotron validated demographics against census; KVRB would
validate behavioral marginals AND observed joints against national surveys, with fusion assumptions
stated). It does not magically make every cross-block correlation real; it makes the dataset honest
about which correlations are measured vs assumed. That distinction is itself the contribution.
