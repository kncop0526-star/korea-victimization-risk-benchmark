# Zenodo DOI release — runbook (KVRB v0.3)

Prepared 2026-05-31. Everything except the final web steps is done; the steps below need Daniel's
Zenodo/GitHub login and so cannot be automated here.

## Package (ready)
- Upload archive: `KVRB_zenodo_upload_v0.3.zip` (in the Cowork outputs folder; 1.4 MB, 109 files).
  Contains: src/, config/anchors/ (aggregate tables + provenance), results/ (figures + CSV +
  validation notes), docs/, manuscript draft, README/LICENSE/LICENSE-DATA/ETHICS/CITATION, .zenodo.json,
  requirements.txt. EXCLUDES the 1M parquet, raw survey microdata, _archive/, internal review notes.
- `.zenodo.json` (repo root) — auto-fills the Zenodo deposit metadata (title, CC-BY-4.0, creators,
  keywords, isDerivedFrom Nemotron).
- `CITATION.cff` — updated with author Chihwa Lee (KNPA AI Policy Division; KAIST).

## Confirm before minting (Daniel)
1. Author name romanization / order ("Lee, Chihwa") in `.zenodo.json` and `CITATION.cff`.
2. Add ORCID in both files (placeholder lines marked TODO).
3. Decide whether to also deposit the 1M enriched parquet. Default: NO (it is reproducible from the
   code + anchors; keeping it out keeps the deposit small and avoids restating survey-derived rows).

## Two ways to mint the DOI
### A. GitHub-linked (recommended, gives versioned DOIs automatically)
1. Push the repo to GitHub (fill `[USER]` in CITATION.cff license-url / repository-code first).
2. zenodo.org -> log in with GitHub -> Settings -> GitHub -> flip the repo switch ON.
3. On GitHub, create a Release (tag `v0.3.0`). Zenodo captures it and mints a DOI; `.zenodo.json`
   populates the metadata. A concept DOI (all versions) + a version DOI are issued.

### B. Manual upload (no GitHub needed)
1. zenodo.org -> New upload. Drag in `KVRB_zenodo_upload_v0.3.zip`.
2. Zenodo will NOT read .zenodo.json on manual upload — paste metadata by hand: type = Dataset,
   license = CC-BY-4.0, title/creators/keywords/description from `.zenodo.json`, and add the
   related identifier "isDerivedFrom https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea".
3. Reserve a DOI (button) if you want it in the manuscript before publishing; then Publish.

## After minting
- Put the DOI in: manuscript Data-availability section, README badge, CITATION.cff (add `doi:`).
- For double-blind manuscript submission, use Zenodo's restricted/peer-review view-only link instead
  of the public DOI, or publish after acceptance (the deposit identifies the author).
