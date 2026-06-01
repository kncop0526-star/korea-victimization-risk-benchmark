# Module 03 — Romance / Investment ("리딩방") Scam / 로맨스스캠·투자리딩방

**Status:** template (to be developed).

## 1. Crime type & rationale
Romance and investment-room scams exploit relational loneliness and financial-return motivation.
Mid-life divorced/widowed individuals and those seeking investment returns are recurring
prevention-priority segments.

## 2. Risk dimensions → source columns
| Risk dimension | Source column(s) | Direction |
|----------------|------------------|-----------|
| Mid/late adulthood | `age` | 40–69 ↑ |
| Relational vulnerability | `marital_status`, `family_type` | divorced/widowed, single-person ↑ |
| Investable-income occupations (proxy) | `occupation` | select tiers |

## 3. Abstracted predicate
`config/cohorts.example.yaml → module_03` (tiers placeholder).

## 4. Expected cohort size
TBD after first draw.

## 5. Validation plan
KOSIS joint: `age_band × sex × marital_status`.

## 6. Limitations
No income or relationship-status-change variables → proxy only. Risk of stereotype encoding —
manual persona review required. Synthetic origin.

## 7. Intended use
Simulation of persuasion dynamics; prevention-message framing tests; officer training scenarios.
