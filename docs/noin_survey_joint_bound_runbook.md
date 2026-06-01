# Runbook — External joint validation against 노인실태조사 (for Scientific Data revision)

**Goal.** Convert the reviewers' strongest objection (cross-survey **conditional-independence** may
mis-estimate the JOINT of compounding vulnerabilities) into a **quantified error bound**, by comparing
KVRB's realized elderly joint against a single survey that measured financial vulnerability, digital
literacy, and social isolation **on the same elderly respondents** — 노인실태조사 (National Survey of
Older Koreans, KIHASA/MOHW).

This is a genuine out-of-sample test: 노인실태조사 is **not** a KVRB anchor (KVRB uses 가계금융복지조사 /
디지털정보격차 / KGSS), so the comparison is not circular.

Why 노인실태조사 and not the others reviewers suggested:
- **노인실태조사 — use this.** 65+ only, carries FV + DL + SI + scam victimization on the same person.
  Matches the §5.1 elderly voice-phishing use case exactly.
- 한국복지패널(KoWePS) — good *secondary* (FV × SI + CES-D), general population. Optional add.
- 통계청 사회조사 — SI × crime-fear × income, but **weak on digital literacy**. Skip unless needed.
- **KGSS internal AD × SI — DO NOT.** Our own B0 audit (`results/b0_microdata_audit.txt`) already
  proved AUTHORT (2016 only) and the SI battery (2004/2012) were never co-fielded → overlap N = 0.
  Gemini suggested this without knowing; it is foreclosed.

---

## Step 0 — get the microdata (Daniel)

노인실태조사 raw microdata is distributed through **KOSIS MDIS** (mdis.kostat.go.kr) and/or the KIHASA
data archive. Pick the latest wave you can access (2023 preferred; 2020 fine). Download the SPSS `.sav`
(or CSV). Note the wave — variable codes differ by year.

## Step 1 — discover the column names

```
py src/validate_joint_external_noin.py --discover --noin "path\to\노인실태조사_2023.sav"
```

This prints candidate columns grouped by keyword (age / weight / 경제·소득 / 디지털·기기 / 독거·관계).
Open the official codebook alongside and pick the exact items.

## Step 2 — fill the CONFIG block

In `src/validate_joint_external_noin.py`, edit:
- `NOIN_VARS` — set `age`, `weight`, and the raw column(s) for `fv`, `dl`, `si`.
- `RULES` (rule_fv / rule_dl / rule_si) — map each raw item to a **1..5 level in KVRB's direction**:
  - FV: 5 = most financially vulnerable (reverse a satisfaction item with `6 - s`).
  - DL: 5 = most digitally competent (KVRB convention; "low DL" = level 1–2).
  - SI: 5 = most isolated (support-network deficit). If SI must be built from several items
    (독거 flag + 연락빈도 + 도움요청 가능 인원), combine and bin to 1..5 inside `rule_si`.
- `MISSING_CODES` — trim to the codebook's actual missing/IAP codes (pyreadstat returns them as
  numbers, not NaN — the B0-audit lesson).
- `EXTREME` — already set to match the manuscript (FV≥4, DL≤2, SI≥4). Leave unless the manuscript
  cohort definition changes.

## Step 3 — run the comparison

```
py src/validate_joint_external_noin.py ^
   --noin "path\to\노인실태조사_2023.sav" ^
   --kvrb data\processed\enriched_1M_v3_parts ^
   --out results
```

Outputs in `results/`:
- `joint_external_noin.csv` — real vs synthetic, signed diff (pp / ΔV), ratio.
- `joint_external_noin.txt` — report **plus a ready-to-paste §4.5 sentence**.
- `joint_external_noin.png` — bars (simultaneous-extreme rate + 3 pairwise Cramér's V).

Sanity dry-run with no data (proves the pipeline, NOT a result):
```
py src/validate_joint_external_noin.py --mock --out results
```
The mock deliberately shows the expected pattern: when the real FV–SI association (V≈0.245) is replaced
by conditional independence (V≈0.03), the simultaneous-extreme elderly rate is **under-estimated** by a
few pp — exactly the bound the manuscript will report.

## Step 4 — write it into the manuscript (Claude, once you paste the numbers back)

Planned edits to `manuscript/KVRB_data_descriptor_submission.md`:
1. **§4.5** — add one paragraph: the paste-ready sentence (real vs synthetic simultaneous-extreme rate,
   signed bound, FV×SI ΔV), framed as *bounding* the conditional-independence error, not erasing it.
2. **New Table** (Table in §4.5 or §4): `quantity | real (노인실태조사) | synthetic (KVRB) | Δ | ratio`
   for the four rows in the CSV.
3. **§5.3** — move the "external joint validation" bullet from "planned" to "done", keep the residual
   caveat (one elderly survey, one wave; general-population joint still partly assumed).
4. **§1 / Abstract** — one clause: the joint is partially validated out-of-sample for the elderly cohort.
5. Re-run the AI-style v4 grep + Reviewer Simulation gate after the patch; md5-verify (mount rule).

## Interpretation guide (how to frame whatever number comes out)

- **KVRB under-estimates the tail (synthetic < real):** the honest, expected result. Report it as a
  *conservative* bound — the dataset will under-count co-occurring extremes, so reusers targeting the
  highest-risk segment should treat KVRB cohort sizes as a **floor**, and the manuscript says so. This
  is a strength: the limitation is now quantified, which is exactly what Scientific Data's Technical
  Validation asks for.
- **KVRB matches closely (small Δ):** even better — the demographic conditioning recovers most of the
  real joint; report the small residual.
- **KVRB over-estimates:** less likely under pure CI, but if it happens, report it plainly and flag the
  tail as inflated. Either direction, a measured bound beats an unmeasured assumption.
