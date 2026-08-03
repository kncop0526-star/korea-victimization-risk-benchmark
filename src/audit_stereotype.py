"""
audit_stereotype.py — Technical Validation 4.3 (stereotype / protected-attribute audit).

Attributes are sampled from survey conditionals on age band (digital_literacy also on education
tier). The survey justifies those conditioners. This audit asks the complementary question: do the
released attributes carry association with PROTECTED attributes (sex, province) beyond what the
conditioning justifies? Because sampling ignores sex and province entirely, any attribute-by-sex or
attribute-by-province association should survive only through demographic composition (e.g., age mix)
and must vanish once we condition on the justified cells.

Method. For each attribute and each protected attribute we report Cramér's V twice:
  * marginal V — over the whole population (may be non-zero via composition);
  * residual V — computed within each justified cell, then pooled by cell size (should be ≈ 0).
A residual V near zero is the pass condition: no spurious protected-attribute effect beyond the
survey-justified conditioners. Chi-square and Cramér's V are computed from contingency tables with
NumPy only (no SciPy dependency).

Outputs
  results/stereotype_audit.csv          attr × protected: marginal_V, residual_V, n_cells
  results/F5_stereotype_audit.png       marginal vs residual V, grouped by protected attribute

Usage
  python src/audit_stereotype.py --parts data/processed/enriched_1M_v2_parts --out results
"""
from __future__ import annotations
import argparse, glob
from pathlib import Path
import numpy as np
import pandas as pd

ATTRS = ["financial_vulnerability", "digital_literacy", "authority_deference",
         "social_isolation", "prior_victimization", "reporting_propensity"]
# justified conditioners per attribute (what the survey anchors actually condition on)
JUSTIFIED = {a: ["age_band"] for a in ATTRS}
JUSTIFIED["digital_literacy"] = ["age_band", "education_tier"]
PROTECTED = ["sex", "province"]


def load_parts(parts_dir: str) -> pd.DataFrame:
    files = sorted(glob.glob(str(Path(parts_dir) / "part_*.parquet")))
    if not files:
        raise SystemExit(f"no parquet parts under {parts_dir}")
    frames = []
    for f in files:
        try:
            frames.append(pd.read_parquet(f, engine="fastparquet"))
        except Exception:
            frames.append(pd.read_parquet(f))
    return pd.concat(frames, ignore_index=True)


def cramers_v(a: pd.Series, b: pd.Series) -> tuple[float, int]:
    """Plain Cramér's V from a contingency table (NumPy only). Returns (V, n)."""
    ct = pd.crosstab(a, b).to_numpy(dtype=float)
    n = ct.sum()
    if n < 2 or ct.shape[0] < 2 or ct.shape[1] < 2:
        return 0.0, int(n)
    row = ct.sum(1, keepdims=True)
    col = ct.sum(0, keepdims=True)
    exp = row @ col / n
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.nansum(np.where(exp > 0, (ct - exp) ** 2 / exp, 0.0))
    k = min(ct.shape) - 1
    return float(np.sqrt(chi2 / (n * k))) if k > 0 else 0.0, int(n)


def residual_v(df: pd.DataFrame, attr_col: str, prot: str, cells: list[str]) -> tuple[float, int]:
    """Cramér's V(attr, protected) within each justified cell, pooled by cell size."""
    num, den, ncells = 0.0, 0, 0
    for _, sub in df.groupby(cells, observed=True):
        if len(sub) < 50:
            continue
        v, n = cramers_v(sub[attr_col], sub[prot])
        num += v * n
        den += n
        ncells += 1
    return (num / den if den else 0.0), ncells


def run(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for a in ATTRS:
        col = "attr_" + a
        if col not in df.columns:
            continue
        for prot in PROTECTED:
            mv, _ = cramers_v(df[col], df[prot])
            rv, nc = residual_v(df, col, prot, JUSTIFIED[a])
            rows.append({"attr": a, "protected": prot,
                         "marginal_V": round(mv, 4), "residual_V": round(rv, 4),
                         "n_cells": nc, "justified_on": "+".join(JUSTIFIED[a])})
    return pd.DataFrame(rows)


def make_figure(res: pd.DataFrame, out_png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "figure.dpi": 150})
    fig, axes = plt.subplots(1, len(PROTECTED), figsize=(11, 4.2), sharex=True)
    for ax, prot in zip(np.atleast_1d(axes), PROTECTED):
        sub = res[res["protected"] == prot].set_index("attr").reindex(ATTRS)
        y = np.arange(len(sub)); h = 0.38
        ax.barh(y + h / 2, sub["marginal_V"], h, color="#bdbdbd", edgecolor="0.3", lw=0.4,
                label="marginal V")
        ax.barh(y - h / 2, sub["residual_V"], h, color="#c0392b", edgecolor="0.3", lw=0.4,
                label="residual V (within justified cells)")
        ax.set_yticks(y); ax.set_yticklabels([a.replace("_", " ") for a in sub.index], fontsize=7.5)
        ax.invert_yaxis()
        ax.axvline(0.1, color="0.5", ls=":", lw=1)  # 0.1 = negligible-association guide
        ax.set_xlabel("Cramér's V"); ax.set_title(f"attribute × {prot}")
        for k, (m, r) in enumerate(zip(sub["marginal_V"], sub["residual_V"])):
            ax.text(m + 0.004, k + h / 2, f"{m:.3f}", va="center", fontsize=6.3, color="0.35")
            ax.text(r + 0.004, k - h / 2, f"{r:.3f}", va="center", fontsize=6.3, color="#c0392b")
        ax.legend(fontsize=6.8, loc="lower right", framealpha=0.9)
    fig.suptitle("Stereotype audit: protected-attribute association is negligible after "
                 "conditioning on survey-justified cells", fontsize=10.5, y=1.02)
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="data/processed/enriched_1M_v2_parts")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    df = load_parts(args.parts)
    res = run(df)
    res.to_csv(out / "stereotype_audit.csv", index=False, encoding="utf-8-sig")
    make_figure(res, out / "F5_stereotype_audit.png")

    print(f"[ok] rows: {len(df):,}")
    print("[audit] Cramér's V — marginal vs residual (within justified cells):")
    for _, r in res.iterrows():
        print(f"   {r['attr']:<24} x {r['protected']:<9} marginal={r['marginal_V']:.3f}  "
              f"residual={r['residual_V']:.3f}  (cells={r['n_cells']}, on {r['justified_on']})")
    mx = res["residual_V"].max()
    print(f"[result] max residual V = {mx:.3f}  -> {'PASS (<0.1)' if mx < 0.1 else 'REVIEW'}")
    print(f"[fig] {out/'F5_stereotype_audit.png'}")


if __name__ == "__main__":
    main()
