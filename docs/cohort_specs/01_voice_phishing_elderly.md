# Module 01 — Voice Phishing (Elderly) / 보이스피싱·노인

**Status:** worked example. Directly connects to the existing elderly-phishing GABM track.

## 1. Crime type & rationale
Voice phishing targeting older adults exploits social isolation, unfamiliarity with digital
payment/authentication, and authority-deference. Korean prevention research and KNPA reporting
consistently identify older single-person households as an elevated-exposure segment.

## 2. Risk dimensions → source columns
| Risk dimension | Source column(s) | Direction |
|----------------|------------------|-----------|
| Advanced age | `age` | older ↑ |
| Social isolation | `family_type` | single-person household ↑ |
| Lower formal education | `education_level` | lower tiers ↑ |
| Digital-payment unfamiliarity (proxy) | `occupation`, `age` | non-digital / retired ↑ |

## 3. Abstracted predicate
See `config/cohorts.example.yaml → module_01`. Tiers (`age_tier: senior`, `isolation: high`,
`education_tier: lower`) are placeholders; operational cutoffs are kept in the maintainer's
local config.

## 4. Expected cohort size
~5–8% of 1M when restricted to the core senior-isolated segment (aligns with the upstream
`elderly_75plus` subset in the nemotron skill catalog).

## 5. Validation plan
KOSIS joint distribution: `age_band × province × sex`. Compare cohort proportions to census
microdata; report χ², Cramér's V, per-cell residuals. Accept if no material divergence.

## 6. Limitations
Synthetic personas (NVIDIA Nemotron); digital-unfamiliarity is a proxy, not a measured trait;
results should be replicated on real victimization data (e.g., KNPA case statistics) in follow-up.

## 7. Intended use
- Robustness check / Appendix B for the elderly-phishing GABM paper.
- Prevention-message A/B testing (which warning framing reduces simulated susceptibility).
- Officer training: simulated victim interviews.
