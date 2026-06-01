# Cohort Spec Template / cohort 스펙 템플릿

> Copy this file to create a new crime-type module. Keep threshold values **abstracted**
> (named tiers, not raw cutoffs) per the responsible-release policy.

## Module: `<ID>_<name>`

### 1. Crime type & rationale / 범죄유형·근거
Brief description of the crime type and why specific demographic segments face elevated exposure.
Cite prevention literature where possible.

### 2. Risk dimensions → source columns / 위험차원 → 원천 컬럼
| Risk dimension | Source column(s) | Direction |
|----------------|------------------|-----------|
| (e.g., social isolation) | `family_type` | single-person ↑ |

### 3. Abstracted predicate / 추상 술어
Reference the named predicate in `config/cohorts.example.yaml`. **Do not** write raw cutoffs here.

### 4. Expected cohort size / 예상 규모
Approximate % of 1M, before validation.

### 5. Validation plan / 검증 계획
KOSIS joint-distribution columns to test; acceptance criteria.

### 6. Limitations / 한계
Synthetic origin, proxy variables, out-of-scope populations.

### 7. Intended use / 의도된 사용
Simulation? prevention-message test? officer training? State explicitly.
