"""
validate_fidelity.py — Technical Validation 4.1 (distributional fidelity).

Recomputes the synthetic conditional P(level | cell) over the released 1M enriched dataset and
compares it, cell by cell, against the survey anchor tables. Because attributes are *sampled from*
the anchor conditionals, the dataset matches national surveys by construction; this reports the
residual sampling deviation (Total Variation Distance per cell) and produces figure F2.

  --v3  validate the Route-B v3 dataset: FV & DL on age x education; AD & SI on age x sex x education
        (config/anchors/*_b1.csv); PV x RP on the KCVS observed joint (kcvs_joint_b2.csv, 3 outcomes).
  (default) validate the v2 base dataset (all anchors on age_band; DL on age x edu).

Usage
  python src/validate_fidelity.py --parts data/processed/enriched_1M_v3_parts --v3 --out results_v3
"""
from __future__ import annotations
import argparse, glob
from pathlib import Path
import numpy as np
import pandas as pd

ANCHORS = {
    "financial_vulnerability": ("financial_vulnerability", ["age_band"]),
    "digital_literacy":        ("digital_literacy",        ["age_band", "education_tier"]),
    "authority_deference":     ("authority_deference",     ["age_band"]),
    "social_isolation":        ("social_isolation",        ["age_band"]),
    "prior_victimization":     ("prior_victimization",     ["age_band"]),
    "reporting_propensity":    ("reporting_propensity",    ["age_band"]),
}
# v3: level-based anchors (FV/DL/AD/SI) + the PV x RP joint handled separately
ANCHORS_V3 = {
    "financial_vulnerability": ("financial_vulnerability_b1", ["age_band", "education_tier"]),
    "digital_literacy":        ("digital_literacy",           ["age_band", "education_tier"]),
    "authority_deference":     ("authority_deference_b1",     ["age_band", "sex_mf", "education_tier"]),
    "social_isolation":        ("social_isolation_b1",        ["age_band", "sex_mf", "education_tier"]),
}
JOINT_CELLS = ["age_band", "sex_mf", "education_tier"]
JOINT_OUTCOMES = ["nonvictim", "victim_unreported", "victim_reported"]
AGE_ORDER = ["19-29", "30-44", "45-59", "60-74", "75+"]


def load_parts(parts_dir):
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


def _level_report(df, attr, stem, cells, anchors_dir):
    col = "attr_" + attr
    anchor = pd.read_csv(Path(anchors_dir) / f"{stem}.csv")
    for c in cells:
        anchor[c] = anchor[c].astype(str)
    anchor["level"] = anchor["level"].astype(int)
    sub = df[cells + [col]].copy()
    for c in cells:
        sub[c] = sub[c].astype(str)
    sub["level"] = sub[col].astype(int)
    sub = sub[sub["level"] >= 0]                       # drop sentinels
    syn = sub.groupby(cells + ["level"]).size().rename("n").reset_index()
    denom = syn.groupby(cells)["n"].transform("sum")
    syn["syn"] = syn["n"] / denom
    cell_n = syn.groupby(cells)["n"].sum().rename("cell_n").reset_index()
    m = anchor.merge(syn[cells + ["level", "syn"]], on=cells + ["level"], how="left").fillna({"syn": 0.0})
    m = m.merge(cell_n, on=cells, how="left")
    m["attr"] = attr
    m["abs_dev"] = (m["prob"] - m["syn"]).abs()
    return m, cells


def _joint_report(df, anchors_dir):
    """PV x RP observed joint: derive 3-outcome per persona, compare to kcvs_joint_b2."""
    anchor = pd.read_csv(Path(anchors_dir) / "kcvs_joint_b2.csv")
    for c in JOINT_CELLS:
        anchor[c] = anchor[c].astype(str)
    pv = df["attr_prior_victimization"].to_numpy()
    rp = df["attr_reporting_propensity"].to_numpy()
    outcome = np.where(pv == 0, "nonvictim",
              np.where(rp == 0, "victim_unreported", "victim_reported"))
    sub = df[JOINT_CELLS].copy()
    for c in JOINT_CELLS:
        sub[c] = sub[c].astype(str)
    sub["outcome"] = outcome
    syn = sub.groupby(JOINT_CELLS + ["outcome"]).size().rename("n").reset_index()
    denom = syn.groupby(JOINT_CELLS)["n"].transform("sum")
    syn["syn"] = syn["n"] / denom
    cell_n = syn.groupby(JOINT_CELLS)["n"].sum().rename("cell_n").reset_index()
    m = anchor.merge(syn[JOINT_CELLS + ["outcome", "syn"]], on=JOINT_CELLS + ["outcome"], how="left").fillna({"syn": 0.0})
    m = m.merge(cell_n, on=JOINT_CELLS, how="left")
    m["attr"] = "prior_victimization x reporting_propensity (joint)"
    m["abs_dev"] = (m["prob"] - m["syn"]).abs()
    m["level"] = m["outcome"]
    return m


def fidelity_report(df, anchors_dir, v3=False):
    rows, summ = [], []
    anchset = ANCHORS_V3 if v3 else ANCHORS
    for attr, (stem, cells) in anchset.items():
        if "attr_" + attr not in df.columns:
            continue
        m, cells = _level_report(df, attr, stem, cells, anchors_dir)
        rows.append(m)
        tvd = m.groupby(cells).apply(lambda g: 0.5 * g["abs_dev"].sum(), include_groups=False).rename("tvd").reset_index()
        cn = m.groupby(cells)["cell_n"].first().reset_index()
        tvd = tvd.merge(cn, on=cells, how="left")
        w = tvd["cell_n"] / tvd["cell_n"].sum()
        summ.append({"attr": attr, "n_cells": int(len(tvd)),
                     "mean_TVD": round(float(tvd["tvd"].mean()), 5), "max_TVD": round(float(tvd["tvd"].max()), 5),
                     "weighted_TVD": round(float((tvd["tvd"] * w).sum()), 5),
                     "max_abs_dev": round(float(m["abs_dev"].max()), 5), "min_cell_n": int(tvd["cell_n"].min())})
    if v3 and "attr_prior_victimization" in df.columns:
        mj = _joint_report(df, anchors_dir)
        rows.append(mj)
        tvd = mj.groupby(JOINT_CELLS).apply(lambda g: 0.5 * g["abs_dev"].sum(), include_groups=False).rename("tvd").reset_index()
        cn = mj.groupby(JOINT_CELLS)["cell_n"].first().reset_index()
        tvd = tvd.merge(cn, on=JOINT_CELLS, how="left")
        w = tvd["cell_n"] / tvd["cell_n"].sum()
        summ.append({"attr": "PVxRP (joint)", "n_cells": int(len(tvd)),
                     "mean_TVD": round(float(tvd["tvd"].mean()), 5), "max_TVD": round(float(tvd["tvd"].max()), 5),
                     "weighted_TVD": round(float((tvd["tvd"] * w).sum()), 5),
                     "max_abs_dev": round(float(mj["abs_dev"].max()), 5), "min_cell_n": int(tvd["cell_n"].min())})
    cols = ["attr", "age_band", "education_tier", "level", "prob", "syn", "abs_dev", "cell_n"]
    rep = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    for c in cols:
        if c not in rep.columns:
            rep[c] = np.nan
    return rep[cols], pd.DataFrame(summ)


def make_figure(report, summary, out_png, v3=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "figure.dpi": 150})
    fig = plt.figure(figsize=(12, 4.2))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1.25, 1.0], wspace=0.32)
    axA = fig.add_subplot(gs[0, 0])
    cmap = plt.get_cmap("tab10")
    for i, a in enumerate(report["attr"].unique()):
        g = report[report["attr"] == a]
        axA.scatter(g["prob"], g["syn"], s=10, alpha=0.55, color=cmap(i % 10), label=a.replace("_", " ")[:22])
    axA.plot([0, 1], [0, 1], color="0.4", lw=1, ls="--")
    axA.set_xlim(0, 1); axA.set_ylim(0, 1)
    axA.set_xlabel("Survey anchor  P(level | cell)"); axA.set_ylabel("Synthetic  P(level | cell)")
    axA.set_title("(A) By-construction fidelity\nall cells x levels (n=%d)" % len(report))
    axA.legend(fontsize=5.5, loc="upper left", framealpha=0.9)
    axB = fig.add_subplot(gs[0, 1])
    dl = report[(report["attr"] == "digital_literacy") & (report["education_tier"] == "lower")].copy()
    dl["age_band"] = pd.Categorical(dl["age_band"], categories=AGE_ORDER, ordered=True)
    dl = dl.sort_values(["age_band", "level"])
    bands = [b for b in AGE_ORDER if b in dl["age_band"].astype(str).unique()]
    x = np.arange(len(bands)); width = 0.11
    levels = sorted([int(v) for v in dl["level"].unique()])
    blues = plt.get_cmap("Blues")
    for j, lv in enumerate(levels):
        sv = [dl[(dl["age_band"].astype(str) == b) & (dl["level"].astype(str) == str(lv))]["prob"].sum() for b in bands]
        sy = [dl[(dl["age_band"].astype(str) == b) & (dl["level"].astype(str) == str(lv))]["syn"].sum() for b in bands]
        off = (j - (len(levels) - 1) / 2) * width
        axB.bar(x + off, sv, width * 0.9, color=blues(0.35 + 0.13 * j), edgecolor="0.3", lw=0.3, label=f"L{lv} survey")
        axB.scatter(x + off, sy, s=14, color="crimson", zorder=5, label="synthetic" if j == 0 else None)
    axB.set_xticks(x); axB.set_xticklabels(bands); axB.set_ylim(0, 1.18)
    axB.set_xlabel("age band"); axB.set_ylabel("P(digital-literacy level)")
    axB.set_title("(B) Digital literacy by age (lower-edu)\nbars = survey, dots = synthetic")
    axB.legend(fontsize=5.5, ncol=3, loc="upper center", framealpha=0.9, bbox_to_anchor=(0.5, 1.0))
    axC = fig.add_subplot(gs[0, 2])
    s = summary.sort_values("weighted_TVD"); ypos = np.arange(len(s))
    axC.barh(ypos, s["weighted_TVD"], color="#4C72B0", edgecolor="0.3", lw=0.4)
    axC.set_yticks(ypos); axC.set_yticklabels([a.replace("_", " ")[:20] for a in s["attr"]], fontsize=6.5)
    axC.set_xlabel("weighted mean per-cell TVD"); axC.set_title("(C) Residual sampling deviation\n(lower = tighter match)")
    for k, v in enumerate(s["weighted_TVD"]):
        axC.text(v + max(s["weighted_TVD"]) * 0.02 + 1e-5, k, f"{v:.4f}", va="center", fontsize=6.5)
    axC.margins(x=0.20)
    fig.suptitle("F2  Distributional fidelity of KVRB %s synthetic attributes to Korean survey anchors"
                 % ("v3 (Route-B)" if v3 else ""), fontsize=11, y=1.02)
    fig.savefig(out_png, bbox_inches="tight"); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="data/processed/enriched_1M_v2_parts")
    ap.add_argument("--anchors", default="config/anchors")
    ap.add_argument("--out", default="results")
    ap.add_argument("--v3", action="store_true", help="validate the Route-B v3 dataset")
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    df = load_parts(args.parts)
    report, summary = fidelity_report(df, args.anchors, v3=args.v3)
    report.to_csv(out / "fidelity_report.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(out / "fidelity_summary.csv", index=False, encoding="utf-8-sig")
    make_figure(report, summary, out / "F2_distributional_fidelity.png", v3=args.v3)
    print(f"[ok] dataset rows: {len(df):,}  (v3={args.v3})")
    for _, r in summary.sort_values("weighted_TVD").iterrows():
        print(f"   {r['attr']:<40} wTVD={r['weighted_TVD']:.4f}  maxTVD={r['max_TVD']:.4f}  "
              f"maxAbsDev={r['max_abs_dev']:.4f}  cells={r['n_cells']}  minCellN={r['min_cell_n']:,}")
    print(f"[fig] {out/'F2_distributional_fidelity.png'}")


if __name__ == "__main__":
    main()
