# Module 05 — School Violence / 학교폭력

**Status:** template — **proxy-only; primary victims are out of data range.**

## 0. Critical caveat / 결정적 한계 (READ FIRST)
School-violence victims are predominantly **minors (under 19)**, who are **not present** in
Nemotron-Personas-Korea (19–99). This module therefore **cannot** model child/adolescent victims
directly. It instead supports **adjacent stakeholder cohorts**:
- **Guardians** (parents of school-age children — inferred via `family_type` containing
  미혼자녀 + appropriate parent age band).
- **Educators / youth-facing occupations** (via `occupation`).
- **Adult recall** (young adults 19–24 reflecting on recent school experience).

Do **not** present this module as minor-victim data. True school-violence victim research requires
separate, ethics-board-approved, minor-appropriate data sources. See [ETHICS.md §5](../../ETHICS.md).

## 1. Crime type & rationale
Prevention and response involve guardians, teachers, and school resource officers. Modeling these
*adult* stakeholders supports training and communication design without requiring minor data.

## 2. Risk dimensions → source columns
| Stakeholder cohort | Source column(s) | Notes |
|--------------------|------------------|-------|
| Guardian of school-age child | `family_type`, `age` | 미혼자녀 가구 + parent age band |
| Educator / youth-facing | `occupation` | teachers, counselors, youth workers |
| Adult recall (19–24) | `age` | reflective, not victim-of-record |

## 3. Abstracted predicate
`config/cohorts.example.yaml → module_05` (guardian / educator variants).

## 4. Expected cohort size
TBD; guardian cohort likely substantial, educator cohort small.

## 5. Validation plan
KOSIS joint for the guardian cohort: `age_band × family_type × province`.

## 6. Limitations
**Primary victims (minors) absent — structural limit, not fixable within this data.** All cohorts
are adult stakeholders. Synthetic origin.

## 7. Intended use
Guardian/teacher communication design; officer training for school-liaison roles; awareness
campaigns. **Not** a model of minor victims.
