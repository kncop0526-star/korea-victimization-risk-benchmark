# Behavioral Attributes for Synthetic Populations (KVRB)

Code and data for Lee, C. (2027). *"Behavioral Attributes for Synthetic Populations: Which Fused Structure an Agent-Based Model Needs."* Journal of Artificial Societies and Social Simulation, 30(1), 6. https://doi.org/10.18564/jasss.6437

> All personas are **synthetic**. No record corresponds to a real person; no real victims, suspects, or identifiable individuals are contained or described. See `ETHICS.md`.

## What this is

KVRB adds six survey-anchored behavioral attributes (financial vulnerability, digital literacy, authority deference, social isolation, prior victimization, reporting propensity) to NVIDIA Nemotron-Personas-Korea, a one-million-record demographically faithful backbone. Each attribute is **sampled from a real Korean national-survey conditional** given a demographic cell; a language model only renders the sampled value into narrative, it does not estimate it. Every inter-attribute pair is labeled **measured** (observed on shared respondents) or **assumed** (combined under conditional independence).

The paper's contribution is a diagnostic, not a new sampler: it (1) labels measured-vs-assumed joints, (2) validates the assumed joint **out-of-sample** against an independent same-respondent survey (real elderly co-occurrence 2.30× the independence baseline vs the released 1.29×), and (3) **decomposes**, with controlled agent-based experiments, which part of the fused structure changes a simulation outcome. Finding: under threshold contagion at step 25, demographic coupling drives aggregate reach; raising the inter-attribute dependence from none to the observed level changes aggregate reach by at most 1.3 percentage points but changes how many older agents are left behind (tested under threshold contagion only).

## Reproducing the paper

```
pip install -r requirements.txt          # numpy, pandas, pyarrow, matplotlib
# 1. build the enriched population (needs the Nemotron backbone, see data/README.md)
python src/enrich_stage1.py ; python src/enrich_stage2_3.py
# 2. validation
python src/validate_fidelity.py            # Figure 1 (distributional fidelity)
python src/validate_joint_external_noin2023.py  # Figure 2 (external joint, elderly)
python src/audit_stereotype.py             # Figure 3 (protected-attribute audit)
# 3. simulation experiments (fixed seeds, numpy only)
python src/abm_decompose.py                # Table 4 + Figure 5 (decomposition; injection sweep)
python src/abm_discriminate.py             # Table 5 (outcome discrimination)
python src/abm_opinion.py                  # Table 6 (opinion-dynamics replication)
python src/abm_robustness.py               # topology robustness
python src/abm_community.py                # community-network robustness (§6)
python src/abm_sidef.py                    # social-isolation-deflation robustness (§6)
# 4. observation-horizon (duration) sensitivity added in revision
#    see analysis_r3_horizon/README.md for the four commands
```

The two agent-based models are documented in ODD-protocol form in Appendix C of the paper. All anchor tables in `config/anchors/` are aggregate conditional distributions derived from public national surveys (no microdata).

## Layout

```
src/                 construction, validation, and ABM scripts (above)
config/anchors/      survey-derived conditional tables (measured/assumed labeled)
results_v4/          validation outputs and figures referenced in the paper
manuscript/          manuscript and submission materials
data/                backbone reproduced from pinned upstream revision (not redistributed)
```

## License & citation

Code MIT; derived data and documentation CC-BY-4.0 (inherits NVIDIA Nemotron-Personas-Korea attribution). Cite this repository and the upstream dataset; see `CITATION.cff`.
