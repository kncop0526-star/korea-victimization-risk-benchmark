# Module 04 — Digital Sex Crime / 디지털 성범죄

**Status:** template — **handle with elevated ethical caution.**

## 0. Critical caveat / 결정적 한계 (READ FIRST)
The upstream dataset contains **only ages 19–99**. The primary at-risk population for many
digital sex crimes includes minors, who are **entirely absent** from the source data. This module
therefore covers **only the youngest available adult cohort (19+)** and must never be presented as
minor-victim data. Research on minor victimization requires separate, ethics-board-approved data
and is out of scope. See [ETHICS.md §5](../../ETHICS.md).

## 1. Crime type & rationale
Among young adults, exposure to image-based abuse, sextortion, and grooming-adjacent fraud is a
prevention priority. This module supports *adult* (19+) prevention and training only.

## 2. Risk dimensions → source columns
| Risk dimension | Source column(s) | Direction |
|----------------|------------------|-----------|
| Youngest adult cohort | `age` | 19–24 |
| Living arrangement | `family_type` | (analyze, do not over-narrow) |

## 3. Abstracted predicate
`config/cohorts.example.yaml → module_04` (intentionally minimal; avoid over-specific targeting).

## 4. Expected cohort size
Small (19–24 slice of adults).

## 5. Validation plan
KOSIS joint: `age_band × sex × province` for the 19–24 band only.

## 6. Limitations
**No minors in data (hard limit).** Adult-only proxy. High dual-use sensitivity → keep predicate
coarse; do not publish fine-grained targeting attributes. Synthetic origin.

## 7. Intended use
Adult digital-safety education; awareness-message testing. **Not** for any targeting or for
minor-related research.
