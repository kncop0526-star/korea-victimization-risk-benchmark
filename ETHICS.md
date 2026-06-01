# Responsible Use & Dual-Use Statement / 책임있는 사용·이중용도 성명

## 1. Purpose / 목적

**EN.** This benchmark exists to support **crime prevention, victim protection, public education,
and police-officer training**. Cohorts describe population segments that prevention efforts
should *protect*, in order to design better warnings, interventions, and training scenarios.

**KO.** 본 벤치마크는 **범죄 예방·피해자 보호·시민 교육·경찰 교육**을 목적으로 합니다.
cohort는 예방 노력이 *보호해야 할* 인구집단을 기술하며, 더 나은 경고·개입·교육 시나리오 설계를
위한 것입니다.

## 2. Synthetic data — no real people / 합성 데이터 — 실재 인물 없음

**EN.** All personas are **synthetically generated** by NVIDIA's Nemotron model. They do not
correspond to any real victim, suspect, or identifiable individual, and contain no PII. Any
resemblance to a real person is coincidental and not evidentiary.

**KO.** 모든 페르소나는 NVIDIA Nemotron 모델이 **합성 생성**한 것입니다. 실재하는 피해자·피의자·
식별 가능한 개인과 무관하며 개인정보를 포함하지 않습니다. 실존 인물과의 유사성은 우연이며 증거가
되지 않습니다.

## 3. Dual-use risk and mitigations / 이중용도 위험과 완화

A benchmark of *victimization-risk cohorts* could, if misused, inform targeting. We mitigate this:

| Risk | Mitigation |
|------|-----------|
| Raw thresholds reused as a targeting recipe | Operational thresholds are **not published**; `config/` ships abstracted/placeholder values only |
| "Vulnerable list" extraction | No pre-extracted target lists are committed; `.gitignore` blocks derived data |
| Re-framing for offense | Documentation consistently frames cohorts as *protection targets*, with this statement in every artifact |
| Misreading synthetic as real | Synthetic-data disclaimer in README, data card, and each cohort spec |

## 4. Prohibited uses / 금지된 사용

You may **not** use this repository or its outputs to:

- Identify, target, contact, or solicit real individuals for fraud, harassment, or any crime.
- Build offender/suspect-profiling systems that assign criminality based on demographics.
- Represent synthetic personas as real victims in any legal, investigative, or news context.
- Train models intended to facilitate any of the above.

## 5. Special caution: minors / 미성년자 특별 주의

The upstream dataset contains **only ages 19–99**. Modules touching minors (digital sex crime,
school violence) therefore use **adjacent-age proxies** and must not be presented as
minor-victim data. Research on minor victimization requires separate, ethics-board-approved
data sources and is out of scope here.

## 6. Institutional & legal note / 기관·법적 유의

Contributors employed by public institutions should confirm that releasing work-related
artifacts under a personal account complies with their organization's policies on outside
activity and ownership of work product. This is the contributor's responsibility.

## 6.5 LLM-generated attributes / LLM 생성 속성

This dataset adds attributes generated with an LLM (see `docs/enrichment_design.md`). To keep this
honest:

- **Values come from real surveys, not the LLM.** Attribute *values* are sampled from real Korean
  survey conditional distributions; the LLM only renders them into narrative. The LLM does not
  estimate or invent the distribution.
- **Weakly-anchored (Tier 3) attributes are flagged.** Constructs with no survey anchor (e.g.,
  `scam_susceptibility`) are LLM-prior estimates, marked low-confidence, and must be used
  qualitatively only — never as a measured outcome or quantitative claim.
- **Stereotype audit is mandatory.** LLM rendering can inject stereotype texture; the round-trip
  check and a stereotype audit (attribute–demographic correlations must not exceed survey-justified
  levels) are required before release.
- **No real-person inference.** Generated attributes describe synthetic personas; they must never
  be applied to infer traits of any real individual.

## 7. Reporting concerns / 우려 신고

If you identify a misuse pathway or an ethical concern, please open an issue or contact the
maintainer. We will respond and, where warranted, restrict or revise the release.
