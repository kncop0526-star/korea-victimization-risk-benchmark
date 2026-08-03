"""
demo_cohort.py — Figure F4 (usage demonstration: elderly voice-phishing cohort).

Selects the elderly voice-phishing cohort (cohort_specs/01) from the enriched 1M dataset
and contrasts its crime-prevention attribute profile against the full population. The point
is a demonstration of *use*, not a finding: because attributes are sampled from survey
conditionals tied to demographics, the elderly-isolated-low-education segment carries an
elevated-risk profile by construction — which is exactly what a prevention researcher would
select on. The figure shows that the augmented layer yields a coherent, interpretable cohort.

Cohort (cohort_specs/01, abstracted): age >= 65 AND single-person household AND lower education.

Outputs
  results/cohort_profile.csv          per risk dimension: cohort vs population share-at-risk
  results/F4_elderly_phishing_cohort.png

Usage
  python src/demo_cohort.py --parts data/processed/enriched_1M_v2_parts --out results \
         --min-age 65
"""
from __future__ import annotations
import argparse, glob
from pathlib import Path
import numpy as np
import pandas as pd

# risk direction per attribute: (label, column, predicate on level, kind)
RISK = [
    ("High financial vulnerability", "attr_financial_vulnerability", lambda s: s >= 4, "likert"),
    ("Low digital literacy",         "attr_digital_literacy",        lambda s: s <= 2, "likert"),
    ("High authority deference",     "attr_authority_deference",     lambda s: s >= 4, "likert"),
    ("High social isolation",        "attr_social_isolation",        lambda s: s >= 4, "likert"),
    ("Prior victimization",          "attr_prior_victimization",     lambda s: s == 1, "binary"),
    ("Would not report",             "attr_reporting_propensity",    lambda s: s == 0, "binary"),
]
SINGLE_HH_TERMS = ["혼자 거주", "1인", "독거"]


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


def cohort_mask(df: pd.DataFrame, min_age: int) -> pd.Series:
    single = df["family_type"].astype(str).apply(lambda x: any(t in x for t in SINGLE_HH_TERMS))
    lower = df["education_tier"].astype(str).eq("lower") if "education_tier" in df.columns else True
    return (df["age"] >= min_age) & single & lower


def make_figure(df: pd.DataFrame, mask: pd.Series, out_png: Path, min_age: int) -> pd.DataFrame:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    coh = df[mask]; pop = df
    rows = []
    for label, col, pred, kind in RISK:
        if col not in df.columns:
            continue
        rows.append({
            "dimension": label,
            "cohort_share": round(float(pred(coh[col]).mean()), 4),
            "population_share": round(float(pred(pop[col]).mean()), 4),
        })
    prof = pd.DataFrame(rows)
    prof["lift"] = (prof["cohort_share"] / prof["population_share"].replace(0, np.nan)).round(2)

    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "figure.dpi": 150})
    fig = plt.figure(figsize=(12, 4.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.28)

    # Panel A: share-at-risk, cohort vs population
    axA = fig.add_subplot(gs[0, 0])
    y = np.arange(len(prof)); h = 0.38
    axA.barh(y + h / 2, prof["cohort_share"], h, color="#c0392b", edgecolor="0.3", lw=0.4,
             label=f"elderly cohort (n={len(coh):,})")
    axA.barh(y - h / 2, prof["population_share"], h, color="#95a5a6", edgecolor="0.3", lw=0.4,
             label=f"full population (n={len(pop):,})")
    axA.set_yticks(y); axA.set_yticklabels(prof["dimension"], fontsize=8)
    axA.invert_yaxis(); axA.set_xlim(0, 1.0); axA.set_xlabel("share in high-risk band")
    for k, (c, p, lift) in enumerate(zip(prof["cohort_share"], prof["population_share"], prof["lift"])):
        axA.text(c + 0.01, k + h / 2, f"{c:.2f}", va="center", fontsize=6.8, color="#c0392b")
        axA.text(p + 0.01, k - h / 2, f"{p:.2f}", va="center", fontsize=6.8, color="0.4")
        axA.text(0.985, k, f"x{lift:.1f}" if pd.notna(lift) else "", va="center", ha="right",
                 fontsize=7, color="0.2", style="italic")
    axA.set_title("(A) Behavioral risk profile (share-at-risk)")
    axA.legend(fontsize=7.5, loc="center right", bbox_to_anchor=(0.99, 0.34), framealpha=0.95)

    # Panel B: digital literacy distribution, cohort vs population
    axB = fig.add_subplot(gs[0, 1])
    levels = [1, 2, 3, 4, 5]
    cd = [float((coh["attr_digital_literacy"] == lv).mean()) for lv in levels]
    pd_ = [float((pop["attr_digital_literacy"] == lv).mean()) for lv in levels]
    x = np.arange(len(levels)); w = 0.4
    axB.bar(x - w / 2, cd, w, color="#c0392b", edgecolor="0.3", lw=0.4, label="elderly cohort")
    axB.bar(x + w / 2, pd_, w, color="#95a5a6", edgecolor="0.3", lw=0.4, label="population")
    axB.set_xticks(x); axB.set_xticklabels([f"L{lv}" for lv in levels])
    axB.set_xlabel("digital-literacy level (1=lowest)"); axB.set_ylabel("share")
    axB.set_title("(B) Digital literacy: cohort vs population")
    axB.legend(fontsize=7.5, framealpha=0.9)

    fig.suptitle(f"Cohort query: compound-vulnerability cohort (age >= {min_age}, "
                 f"single-person, lower-education)", fontsize=11, y=1.03)
    fig.text(0.5, -0.04, "Profile is by construction from survey conditionals tied to the cohort's "
             "demographics — a usage demo, not an independent finding.",
             ha="center", fontsize=7.5, style="italic", color="0.4")
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)
    return prof


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="data/processed/enriched_1M_v2_parts")
    ap.add_argument("--out", default="results")
    ap.add_argument("--min-age", type=int, default=65)
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    df = load_parts(args.parts)
    mask = cohort_mask(df, args.min_age)
    prof = make_figure(df, mask, out / "F4_elderly_phishing_cohort.png", args.min_age)
    prof.to_csv(out / "cohort_profile.csv", index=False, encoding="utf-8-sig")

    print(f"[ok] population={len(df):,}  cohort={int(mask.sum()):,}  ({100*mask.mean():.1f}% of 1M)")
    print("[profile] share-at-risk  cohort | population | lift")
    for _, r in prof.iterrows():
        print(f"   {r['dimension']:<28} {r['cohort_share']:.3f} | {r['population_share']:.3f} | x{r['lift']}")
    print(f"[fig] {out/'F4_elderly_phishing_cohort.png'}")


if __name__ == "__main__":
    main()
