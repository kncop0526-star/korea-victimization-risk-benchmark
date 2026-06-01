# Data & Documentation License

## Derived data and documentation: CC-BY-4.0

All persona-derived data (cohort subsets) and documentation in this repository are licensed
under the **Creative Commons Attribution 4.0 International (CC-BY-4.0)** license,
inherited from the upstream dataset.

License text: https://creativecommons.org/licenses/by/4.0/

## Upstream attribution (REQUIRED)

This repository is a **derivative work** of:

> **NVIDIA. (2025). Nemotron-Personas-Korea** [Dataset]. Hugging Face.
> https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea — Licensed under CC-BY-4.0.

Under CC-BY-4.0 you **must**, in any use or redistribution:

1. Give appropriate credit to NVIDIA as the source of the underlying personas.
2. Provide a link to the license (CC-BY-4.0).
3. Indicate if changes were made (this repository derives cohorts via filtering and validation;
   it does not alter individual persona content).

## What this repository adds (the derivative contribution)

The maintainer's original contribution — released under the same CC-BY-4.0 for data/docs and
MIT for code — consists of:

- Victimization-risk **cohort construction methodology** (`docs/`)
- A **validation pipeline** against KOSIS census microdata (`src/validate_kosis.py`)
- **Abstracted cohort definitions** (`config/`)

The maintainer does **not** claim authorship or ownership of the underlying NVIDIA personas.

## BibTeX (upstream)

```bibtex
@dataset{nvidia_nemotron_personas_korea,
  author    = {NVIDIA},
  title     = {Nemotron-Personas-Korea},
  year      = {2025},
  publisher = {Hugging Face},
  url       = {https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea},
  license   = {CC-BY-4.0}
}
```
