# Human re-read coding protocol (M3b) — turnkey

**Why:** four independent SSCI reviewers asked for human validation. The round-trip in §4.2 is LLM→LLM; a blind human re-read of a stratified sample is the evidence that a *person* reads the level the sampler set. This is the single highest-leverage item for a *Scientific Data* decision (reviewers estimate SD ~60% without it, ~higher with it).

## What is already prepared (by Claude)
- `results/human_reread_rater1.xlsx`, `_rater2.xlsx`, `_rater3.xlsx` — three identical blank sheets, **200 personas stratified** over age_band × sex (≈20 per cell, 10 cells), narratives **leak-stripped** (no `(속성 N)` parentheticals).
- `results/human_reread_key.csv` — the sampler's values. **PRIVATE — keep out of git/Zenodo** (it is the answer key; `.gitignore` already excludes it).

## Steps (Daniel + 2 colleagues = 3 independent coders)
1. Give each coder **one** sheet (rater1/2/3). They read each `narrative` and fill the four `human_*` columns with **1–5** (1=low, 5=high):
   - FV higher = more financially vulnerable
   - DL higher = more digitally engaged
   - AD higher = more deferent to authority
   - SI higher = more socially isolated
2. Coders work **independently, blind to each other and to the sampled values**. No conferring.
3. Save the filled files as `..._rater1_FILLED.xlsx` etc.
4. Score:
   ```
   py src/build_human_reread_sheet.py --score \
       --sheets results/human_reread_rater1_FILLED.xlsx results/human_reread_rater2_FILLED.xlsx results/human_reread_rater3_FILLED.xlsx \
       --key results/human_reread_key.csv --out results
   ```
   → `results/human_reread_results.csv` with, per attribute:
   - **inter-rater** reliability: mean pairwise quadratic-weighted κ **and** ordinal **Krippendorff α**
   - **consensus-vs-sampled** QWK (the headline: do humans recover the sampler's level?)
5. Send Claude `human_reread_results.csv`; Claude patches §4.2 with the human numbers and reports them against the synthetic round-trip.

## Interpreting the result
- High consensus-vs-sampled QWK (≈0.7+) → the narrative genuinely encodes the level; the all-synthetic loop is broken.
- A gap between human and the GPT-4o cross-model number would temper the §4.2 "the level is in the text" claim — report it honestly either way.
- Krippendorff α < 0.667 on any attribute → flag that attribute's narrative as ambiguous for humans (especially digital literacy, the weakest in the synthetic round-trip).

## Effort
200 narratives × 3 coders ≈ 1.5–2 hours per coder. Korean-fluent coders required (narratives are Korean).
