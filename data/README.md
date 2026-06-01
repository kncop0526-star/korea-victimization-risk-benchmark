# data/ — not committed

The raw NVIDIA Nemotron-Personas-Korea dataset (1M rows) and all derived cohort outputs are
**deliberately excluded** from version control (see `.gitignore`). Reasons: file size, and the
responsible-release policy (no derived vulnerable-target data in the repo).

## Expected layout (local only)

```
data/
├── raw/                    # downloaded upstream dataset
│   └── nemotron_korea.parquet
├── reference/              # KOSIS joint-distribution reference (you prepare this)
│   └── kosis_joint.csv
└── processed/              # cohort outputs from build_cohorts.py (git-ignored)
```

## Download the upstream dataset

```python
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="nvidia/Nemotron-Personas-Korea",
    repo_type="dataset",
    local_dir="data/raw",
)
```

Then consolidate to a single parquet at `data/raw/nemotron_korea.parquet` (or pass `--source`).

## License reminder

The upstream dataset is **CC-BY-4.0**. Attribution to NVIDIA is required in any use or
redistribution. See `../LICENSE-DATA.md`.
