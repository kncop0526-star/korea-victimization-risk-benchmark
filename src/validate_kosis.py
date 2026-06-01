"""
validate_kosis.py
------------------------------------------------------------------
Validate a cohort's distributional fidelity against KOSIS census microdata
using a chi-square goodness-of-fit test on the joint distribution of key
demographic columns.

Usage:
    python src/validate_kosis.py --cohort data/processed/module_01.parquet \
        --kosis data/reference/kosis_joint.csv --on age_band province sex

NOTE: KOSIS reference distributions are NOT shipped (licensing). Prepare a
reference table of expected joint proportions from KOSIS 인구총조사 마이크로데이터.
With large N, raw p-values are fragile — interpret effect size (Cramer's V).
------------------------------------------------------------------
한국어 주석: cohort의 joint 분포를 KOSIS 기준과 χ² 적합도 검정. 대표본에서는
p-value가 취약하므로 효과크기(Cramer's V)를 함께 해석한다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chisquare


def joint_proportions(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    counts = df.groupby(cols, observed=True).size()
    return counts / counts.sum()


def cramers_v(chi2: float, n: int, k: int) -> float:
    """k = number of categories (cells). Bias-uncorrected Cramer's V proxy."""
    return float(np.sqrt(chi2 / (n * max(k - 1, 1))))


def main() -> None:
    ap = argparse.ArgumentParser(description="KOSIS goodness-of-fit validation.")
    ap.add_argument("--cohort", required=True, help="Cohort parquet/csv path.")
    ap.add_argument("--kosis", required=True,
                    help="KOSIS reference CSV with the same join cols + 'proportion'.")
    ap.add_argument("--on", nargs="+", default=["age_band", "province", "sex"],
                    help="Join columns for the joint distribution.")
    args = ap.parse_args()

    cpath = Path(args.cohort)
    cohort = pd.read_parquet(cpath) if cpath.suffix == ".parquet" else pd.read_csv(cpath)
    ref = pd.read_csv(args.kosis)

    obs_prop = joint_proportions(cohort, args.on).rename("obs")
    ref_idx = ref.set_index(args.on)["proportion"].rename("exp")

    merged = pd.concat([obs_prop, ref_idx], axis=1).fillna(0.0)
    n = len(cohort)
    observed = (merged["obs"] * n).to_numpy()
    expected = (merged["exp"] * n).to_numpy()
    # Rescale expected to match observed total (chisquare requires equal sums).
    expected = expected * observed.sum() / expected.sum()

    chi2, p = chisquare(f_obs=observed, f_exp=expected)
    v = cramers_v(chi2, n, k=len(merged))

    print("=== KOSIS goodness-of-fit ===")
    print(f"cells={len(merged)}  N={n:,}")
    print(f"chi2={chi2:,.2f}  p={p:.4g}")
    print(f"Cramer's V={v:.4f}  "
          f"({'negligible' if v < 0.1 else 'small' if v < 0.3 else 'moderate+'} divergence)")
    print("NOTE: with large N, prefer effect size (V) over p-value for the accept/reject call.")

    worst = (merged["obs"] - merged["exp"]).abs().sort_values(ascending=False).head(10)
    print("\nLargest per-cell proportion gaps:")
    print(worst.to_string())


if __name__ == "__main__":
    main()
