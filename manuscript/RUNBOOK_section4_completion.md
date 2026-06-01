# Runbook — completing §4.2 (real F3) and §4.4 (face validity)

Turnkey steps for the next session, once an LLM key is set. Everything below runs from the repo root
`korea-victimization-risk-benchmark/`. §4.1 (F2) and §4.3 (F5) are already done with real data.

## 0. Key handling (security rules)

- Set the key in the terminal env, never hard-coded. In PowerShell wrap the value in double quotes:
  `setx OPENAI_API_KEY "sk-..."`  (new shell after setx) — or `$env:OPENAI_API_KEY="sk-..."` for the
  current session only.
- Pin a dated model snapshot, no floating alias: `gpt-4o-2024-11-20` or `gemini-2.5-flash`.
- After the run, revoke/rotate the key if it was ever shown on screen. Set a billing cap beforehand.

## 0.5 Model preflight (do this before the run)

A pinned dated snapshot can still 404 as "no longer available to new users" (this happened with
`gemini-2.0-flash-001` on 2026-05-30). List what the key can actually call, then pick a flash model:

```
py -c "import google.generativeai as genai,os; genai.configure(api_key=os.environ['GEMINI_API_KEY']); [print(m.name) for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]"
```

Use `py` (not `python`) on Windows — bare `python` hits the Microsoft Store alias stub. The code now
guards Gemini empty-Part responses (finish_reason 1/2 with no content) so the run no longer crashes
mid-batch; such records are skipped, so a per-attribute n slightly below the requested N is expected.

## 1. §4.2 — real round-trip F3

Pick the sample size first. Round-trip cost ≈ N × (1 render + 4 extract) calls. N=200 is enough for
agreement rates; N=500 tightens the confusion matrix.

```
# 1a. Stage 2/3 real pass (pinned model, key from env)
python src/enrich_stage2_3.py --in data/processed/enriched_stage1.csv \
    --provider openai --model gpt-4o-2024-11-20 --n 200

# 1b. regenerate F3 from the real narratives
python src/validate_roundtrip.py --in data/processed/enriched_stage23.jsonl --out results
```

Check the console: `actual_model` should echo the pinned snapshot, and the agreement lines should NOT
say STUB. `results/F3_roundtrip_consistency.png` will lose its DEMO/STUB banner automatically.
Then fill §4.2 with the per-attribute exact / within-1 agreement and the `roundtrip_summary.csv`.

## 2. §4.4 — face validity

```
# build the blind review sheet from the REAL narratives (refuses stub input)
python src/build_face_validity_sheet.py --in data/processed/enriched_stage23.jsonl --n 50 --seed 7
```

This writes `results/face_validity_sheet.csv` (Excel) and `.md`. An expert scores each narrative:
`plausible_1to5` and `consistent_with_levels_Y_N`. Aggregate the returned sheet (mean plausibility,
percent consistent, inter-rater agreement if more than one reviewer) and write §4.4.

## 3. After §4 is complete

- Remove the `[AUTHOR]` markers left in §4.2 and §4.4; confirm none remain (`grep "\[AUTHOR" manuscript/*.md`).
- Re-run the AI-style v4 grep gate over the whole manuscript + the §6-A Reviewer Simulation (5–7 Q).
- Deposit dataset + code on Zenodo/OSF, mint the DOI, fill `CITATION.cff` ([YOUR NAME]).
- External-LLM adversarial review (Gemini / GPT-4o) before Editorial Manager upload.

## State at handoff (2026-05-30)

| Section | Status | Needs |
|---|---|---|
| §4.1 fidelity (F2) | DONE (real, 1M) | — |
| §4.2 round-trip (F3) | stub/demo | key → step 1 |
| §4.3 stereotype audit (F5) | DONE (real, 1M) | — |
| §4.4 face validity | not started | narratives → step 2 |
| §1, §5.4 | drafted | author review |
