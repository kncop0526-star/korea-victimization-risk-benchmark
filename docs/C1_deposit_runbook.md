# C1 — Data/code availability deposit runbook (the genre blocker, Daniel)

> Both reviewers: a *Data Descriptor* cannot advance while data/code are "pending." Make availability real **before submission**. All steps need your accounts/credentials.

## 1. Clean the release first (no broken artifacts)
- **Remove the corrupt single-file parquet** from the public package: `data/processed/enriched_1M_v2.parquet` (footer-damaged). Ship only `enriched_1M_v3_parts/` (9 parts, footer-verified). The manuscript already points reusers to the parts.
- Confirm the v3 release contents: `enriched_1M_v3_parts/`, `enriched_stage23.jsonl` (+ `enriched_stage23_N2000.jsonl` validation probe), `config/anchors/*` (+ `*_b1.csv`, `kcvs_joint_b2.csv`), `src/` (incl. `validate_joint_external_noin2023.py`), `results/` (incl. `F7_external_joint_noin2023.png`, `joint_external_noin2023.*`).

## 2. Pin the backbone (guard against upstream drift)
- Record the **exact** NVIDIA Nemotron-Personas-Korea version used (release 2026-04-20) — its Hugging Face commit hash / revision id — in the repo (e.g., `docs/backbone_version.txt` and the README).
- If license permits, archive a frozen copy (or the precise download manifest + checksums) so the 1M backbone is reproducible even if upstream changes. The descriptor's §6 already states this intent — make the hash concrete.

## 3. GitHub — make the repo public
- Push `korea-victimization-risk-benchmark/` public (code MIT). Ensure no API keys / personal data in history (scan before pushing). Tag a release (e.g., `v1.0-submission`).

## 4. CITATION.cff — fill placeholders
- Replace `[YOUR NAME]` with author name; add ORCID, affiliation, the dataset title, version, and the Zenodo DOI (once issued). Validate the CFF (cffinit or `cffconvert`).

## 5. Zenodo — deposit + DOI
- Upload the release package (`outputs/KVRB_zenodo_upload_v0.3.zip`, refreshed to include the new §4.6 artifacts: `validate_joint_external_noin2023.py`, `F7`, `joint_external_noin2023.*`; exclude raw survey microdata and the corrupt v2 file).
- Set license (CC-BY-4.0 derived data/docs; MIT code), add metadata (authors, ORCID, title, description), **Publish** to mint the DOI.
- For double-anonymized review if the journal uses it, also create a **view-only** link; otherwise the public DOI suffices (Scientific Data is single-blind).

## 6. Sync the manuscript §6 once DOI exists
- Replace the §6 "DOI finalized at submission" placeholder with the live Zenodo DOI; replace the GitHub "public at submission" with the live URL. (I can patch §6 once you give me the DOI + URL.)

## Checklist before hitting submit
- [ ] corrupt v2 parquet removed from package
- [ ] NVIDIA backbone hash/revision recorded
- [ ] GitHub public, no secrets in history, tagged release
- [ ] CITATION.cff filled (name, ORCID, DOI)
- [ ] Zenodo published, DOI minted, package includes §4.6 artifacts
- [ ] §6 of the manuscript updated with live DOI + URL
