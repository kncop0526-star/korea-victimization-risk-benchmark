# Paper K (KVRB) — Daniel's next steps, sequenced (2026-06-01)

> What's left to get to a Scientific Data submission, in order. **Phase 1 = real blockers (must, before submit).** Phase 2 = strengthening runs (answer reviewer Majors; can be pre-submit or at revision). Phase 3 = submit. After each run, paste me the output and I patch the manuscript.

State now: manuscript at v0.8+ (37 KB), text fully addresses both external reviews; figures, References, statistics all verified. Remaining gaps are **deposit + author info + a few strengthening runs** — none are writing problems.

---

## PHASE 1 — submission blockers (must do)

**1. Data/code deposit (C1).** Follow `docs/C1_deposit_runbook.md`:
   - remove the corrupt `enriched_1M_v2.parquet` from the package; ship only `enriched_1M_v3_parts/`;
   - pin the NVIDIA Nemotron backbone revision/hash in the repo;
   - push GitHub public (scan for secrets first); tag a release;
   - fill `CITATION.cff` (name, ORCID);
   - publish to Zenodo → get the DOI.
   → **Send me the Zenodo DOI + GitHub URL** and I patch §6 of the manuscript, the Title page, the Cover letter, and CITATION.cff in one pass.

**2. Author information.** Fill the author block in `manuscript/Title_page.md` and `manuscript/Cover_letter.md`: name, affiliation, ORCID, email, funding. (I left placeholders.)

**3. Clean the 5 leaked narratives (minor data-quality).** Five of the 2000 round-trip narratives embed the level in text, e.g. "(재정 취약성 2)". uuids: `f14567f0…, a7658d80…, 047e1974…, 87df7be8…, cbc5aa92…`. Regenerate those 5 (or strip the parentheticals) before the public release so no narrative leaks its schema value. (Does not affect any reported statistic — 0.2% of narratives.)

---

## PHASE 2 — strengthening runs (answer reviewer Majors; raises accept odds)

**4. M2 — residual magnitude match (cheap; needs KGSS microdata you already have).**
   Proves the "measured, not introduced" claim for AD×sex (V=0.145) / SI×sex (0.084) by comparing to the source survey's own V + CI.
   ```
   py src/validate_residual_magnitude_match.py --kgss path\to\kgss_needcols.csv --out results
   ```
   (Edit `SI_ITEMS` in the script to match the released social_isolation anchor if the item names differ.)
   → paste me `results/residual_magnitude_match.txt`; I patch §4.3 with the side-by-side V (reproduces vs amplifies).

**5. M3a — cross-model round-trip on the full N=2000 (needs an OpenAI key).**
   Replaces the old n=120 cross-model probe with the real N=2000 set.
   ```
   $env:OPENAI_API_KEY="..."   # then immediately plan to revoke after
   py src/crossmodel_extract.py --in data\processed\enriched_stage23_N2000.jsonl --provider openai --model gpt-4o-2024-11-20 --out data\processed\enriched_stage23_N2000_xmodel.jsonl
   py src/validate_roundtrip.py --in data\processed\enriched_stage23_N2000_xmodel.jsonl --out results_xmodel_N2000
   ```
   → paste me `results_xmodel_N2000/roundtrip_summary.csv`; I patch §4.2.

**6. M3b — human re-read (breaks the all-synthetic loop; needs 1–3 people).**
   ```
   py src/build_human_reread_sheet.py --build --in data\processed\enriched_stage23_N2000.jsonl --n 100 --out results
   ```
   Give `results/human_reread_sheet.xlsx` to raters (they fill human_FV/DL/AD/SI 1–5; keep `human_reread_key.csv` private). After filling:
   ```
   py src/build_human_reread_sheet.py --score --sheet results\human_reread_sheet_FILLED.xlsx --key results\human_reread_key.csv --out results
   ```
   → paste me `results/human_reread_results.csv`; I patch §4.2 with human-vs-sampled QWK.

**7. C2-full — recalibrate the elderly DL anchor (larger; optional for v1).**
   The text now labels elderly digital_literacy as within-cohort-ordinal-only. A full fix re-derives the DL anchor so the elderly low-DL marginal (now 85%) matches the ~37% same-respondent level. If you want this in v1, we redesign the DL anchor; otherwise the labeling fix ships and recalibration is the v2 roadmap.

---

## PHASE 3 — submit

**8.** Assemble for Scientific Data's online system: manuscript, Title page, Cover letter, figures as separate files (F1–F7 from `results/`), data-availability + code-availability statements (with the live DOI/URL), reporting summary. Single-blind, so author info stays in. Submit.

---

## Parallel / separate tracks (not blockers for the descriptor)
- **Victimology paper** — outline ready (`_victimology_paper_outline_2026-06-01.md`); start when you choose. Empirical companion to Paper G.
- **AI-threat literacy scale** — design ready (`_ai_threat_literacy_scale_2026-06-01.md`); needs IRB + the 모두의 경찰관 110-panel to test Axis 2.
- **Paper G** — in review; when its decision lands, fold in the KVRB linkage (`_paperG_linkage_note_2026-06-01.md`).

## My side (tell me when ready)
- DOI/URL/author info → I sync §6 + Title + Cover + CITATION.
- Any Phase-2 output → I patch the matching section + re-run the AI-style + integrity gate.
- A delta external review on the next version, if you want one more loop before submit.

## Recommended minimal path to submit
Phase 1 (deposit + author + clean 5) → optionally M2 + M3a (both cheap, strong) → submit; handle M3b/C2-full at revision if reviewers ask.
