# R3 observation-horizon sensitivity

These scripts reproduce the duration checks in Sections 5.3 and 5.5. They call the existing model functions in `src/` without changing their bodies or random-number sequence. `original_module.py` suppresses an unconditional top-level `main()` call when importing two original scripts and records function AST hashes before and after import preparation.

## Environment and population input

The checks were run with Python 3.14.3, NumPy 2.4.4, pandas 3.0.2 and PyArrow 24.0.0; plotting also needs Matplotlib. Install the repository dependencies and these packages in your environment. Reconstruct the population using the repository's released construction code and anchor tables plus the pinned upstream demographic backbone before running these scripts. The million-record population file is not included here. The expected first part is `data/processed/enriched_1M_v4_parts/part_00.parquet`; `config.json` records its SHA-256 and the three original model hashes. Model-source hashes use UTF-8 text with line endings normalized to LF, so Windows CRLF checkouts and Unix LF checkouts use the same source identity; runtime provenance separately records and rechecks actual source bytes. A mismatch stops execution instead of silently using a different experiment input.

The fixed sample has 3,000 agents, sampled with seed 42. Simulation seeds are 1 through 30. Diffusion horizons are 25, 50, 100, 200 and 400; opinion horizons are 20, 40, 80, 160 and 320. All other settings and the order of random draws follow the original models. The target multipliers 1.00, 1.29 and 2.30 are calibration targets, not the realized values in each simulation seed.

## Run from the repository root

Choose a new output directory; the runners refuse a nonempty model-specific output directory. The commands are also portable from another current directory when given `--repo-root ../repository` and absolute script paths. If reconstructed data are stored under a different root, pass `--data-root ../population-root`; only the data root changes, while model sources and reference CSVs still come from `--repo-root`.

```sh
python -B analysis_r3_horizon/discriminate/run_original.py --output-dir horizon_output
python -B analysis_r3_horizon/decompose/run_decompose_horizons.py --output-dir horizon_output
python -B analysis_r3_horizon/opinion/run_opinion_horizon.py --output-dir horizon_output
python -B analysis_r3_horizon/analysis/analyse.py --input-dir horizon_output --output-dir horizon_summary
```

Each runner first checks its original 25- or 20-step results against the canonical `results_v4` CSVs and stops on a mismatch. For only these original-horizon gates, add `--baseline-only` to each of the first three commands and use a separate output directory. The full analysis requires all horizons, so do not pass baseline-only outputs to `analyse.py`.

The analysis uses the same paired-seed bootstrap indices for all contrasts: 10,000 resamples generated with seed 20261104. Intervals are pointwise and conditional on the fixed sample; they are not simultaneous or population-sampling intervals. An undefined relative-effect interval is left empty when any resampled reference mean is zero. `analysis/headline.csv`, `diffusion_target_contrasts.csv` and `opinion_decomposition_contrasts.csv` contain the values reported in Sections 5.3 and 5.5. Additional tables and diagnostic plots preserve the full calculation. Runtime provenance may include the local paths supplied by the person running the code; the distributed configuration contains no machine-specific paths.
