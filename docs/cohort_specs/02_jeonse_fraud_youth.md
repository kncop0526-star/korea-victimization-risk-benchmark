# Module 02 — Jeonse Rental Fraud (Youth) / 전세사기·청년

**Status:** template (to be developed).

## 1. Crime type & rationale
Jeonse (lump-sum deposit) fraud disproportionately affects young, first-time tenants in
metropolitan rental markets who lack experience verifying landlord/title risk. High social
salience in Korea since 2022–2023.

## 2. Risk dimensions → source columns
| Risk dimension | Source column(s) | Direction |
|----------------|------------------|-----------|
| Young adult | `age` | 19–34 ↑ |
| First independent household | `family_type`, `marital_status` | single-person / unmarried ↑ |
| Metropolitan rental market | `province`, `district` | Seoul/Gyeonggi metro ↑ |
| Multi-unit rental housing | `housing_type` | 다세대/연립 ↑ |

## 3. Abstracted predicate
`config/cohorts.example.yaml → module_02` (tiers placeholder).

## 4. Expected cohort size
TBD after first draw.

## 5. Validation plan
KOSIS joint: `age_band × province × housing_type`.

## 6. Limitations
No tenure/deposit variables in source → housing_type + region is an indirect proxy. Synthetic origin.

## 7. Intended use
Prevention-message testing (deposit-verification nudges); policy-acceptance simulation
(e.g., mandatory title-check apps).
