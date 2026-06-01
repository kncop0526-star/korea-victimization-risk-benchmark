# Round-trip scale-up to stratified N≈2000 — runbook (Daniel PC, needs API key)

Goal: replace the N=200 round-trip (F3) with a stratified N=2000 so the reliability estimate spans
the demographic range rather than the common cells. Prepared 2026-05-31.

## Input (ready)
`data/processed/roundtrip_input_stratified_2000.csv` — 2,000 v3 personas, 200 per age_band × sex cell
(all 10 cells full, shuffled). `enrich_stage2_3.py` reads the file head, so the stratification is
preserved by running with `--n 2000`.

## Run (PowerShell)
```powershell
cd "C:\Users\user\Desktop\연구 논문\korea-victimization-risk-benchmark"
$env:GEMINI_API_KEY="..."            # 큰따옴표 필수; revoke after the run
# Stage 2 (narrative) + Stage 3 (within-model round-trip), pinned snapshot:
py src\enrich_stage2_3.py --in data\processed\roundtrip_input_stratified_2000.csv `
   --provider gemini --model gemini-2.5-flash --n 2000 `
   --out data\processed\enriched_stage23_N2000.jsonl
py src\validate_roundtrip.py --in data\processed\enriched_stage23_N2000.jsonl --out results_N2000
```
Optional — cross-model confirmation on the same 2000 narratives (different provider, OpenAI key):
```powershell
$env:OPENAI_API_KEY="..."
py src\crossmodel_extract.py --in data\processed\enriched_stage23_N2000.jsonl `
   --provider openai --model gpt-4o-2024-11-20 --out data\processed\enriched_stage23_N2000_xmodel.jsonl
py src\validate_roundtrip.py --in data\processed\enriched_stage23_N2000_xmodel.jsonl --out results_N2000_xmodel
```

## Budget / time
~2,000 generation calls + 4 Likert × 2,000 extraction calls ≈ 10,000 Gemini calls (the binary PV/RP
are not narrative-rendered). With the built-in 0.2s pacing expect ~35–60 min plus API latency.
Pre-flight: run once with `--n 10` first and confirm parse-rate ≥ 90% before the full 2000
(gabm-checklist N=10 pilot rule). The script resumes nothing, so run in one session or shard by editing
the input.

## After the run — paste back
`results_N2000\roundtrip_summary.csv` (and the cross-model one if run). I will update §4.2 and Figure 3
to the N=2000 numbers, keeping the N=200 line as the pilot, and refresh the gates block.

## Model-pinning note
gemini-2.5-flash is a stable pointer, not a dated snapshot; `gen_meta.actual_model` captures the exact
responding id per record. If a dated Gemini snapshot is available at run time, prefer it and record it.
