"""
abm_demo.py - Illustrative agent-based simulation initialized from KVRB.

Methodological question (JASSS framing, application-neutral):
  Does initializing an ABM from a *behaviorally* enriched synthetic population
  (KVRB) change model outcomes relative to a population that carries the same
  attribute *marginals* but no demographic/joint structure ("demographics-only")?

Process: diffusion of a protective/advisory behavior through a social network
with two channels - (1) a broadcast (digital) channel reaching mainly digitally
literate agents, and (2) social contagion: an agent adopts when the share of
adopted neighbours exceeds a personal threshold lowered by authority_deference
and financial_vulnerability. Network exposure is modulated by social_isolation.

Two conditions, identical model and seed:
  A. KVRB     - agents keep their real (demographically structured) attributes.
  B. Shuffled - each behavioural attribute column is permuted across agents,
                preserving marginals but destroying demographic coupling and the
                inter-attribute joint.

Reproducible: fixed seed, no LLM, numpy only.
Usage:  py src/abm_demo.py [--n 3000] [--steps 25] [--seed 42]
"""
from __future__ import annotations
import argparse, glob, json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ATTRS = ["attr_digital_literacy", "attr_social_isolation",
         "attr_authority_deference", "attr_financial_vulnerability"]
AGE_RANK = {"19-29": 0, "30-44": 1, "45-59": 2, "60-74": 3, "75+": 4}


def load_sample(n: int, seed: int) -> pd.DataFrame:
    parts = sorted(glob.glob("data/processed/enriched_1M_v4_parts/*.parquet"))
    cols = ["age_band", "education_tier"] + ATTRS
    df = pq.read_table(parts[0], columns=cols).to_pandas()
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(df), size=min(n, len(df)), replace=False)
    s = df.iloc[idx].reset_index(drop=True)
    for c in ATTRS:
        s[c] = s[c].astype(int)
    return s


def build_network(n: int, isolation: np.ndarray, k: int, seed: int):
    """Ring lattice on the caller's (age-sorted) order + small rewire, then drop
    ties for isolated agents. isolation in 1..5 (5 = most isolated)."""
    rng = np.random.default_rng(seed + 7)
    half = max(1, k // 2)
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(1, half + 1):
            a, b = i, (i + j) % n
            adj[a].add(b); adj[b].add(a)
    beta = 0.05
    for i in range(n):
        for nb in list(adj[i]):
            if rng.random() < beta:
                new = int(rng.integers(0, n))
                if new != i and new not in adj[i]:
                    adj[i].discard(nb); adj[nb].discard(i)
                    adj[i].add(new); adj[new].add(i)
    keep_frac = {1: 1.0, 2: 0.85, 3: 0.7, 4: 0.5, 5: 0.3}
    neigh = []
    for i in range(n):
        nbrs = np.array(sorted(adj[i]), dtype=np.int64)
        f = keep_frac.get(int(isolation[i]), 0.7)
        if len(nbrs) and f < 1.0:
            m = max(1, int(round(len(nbrs) * f)))
            if m < len(nbrs):
                nbrs = rng.choice(nbrs, size=m, replace=False)
        neigh.append(nbrs)
    return neigh


def run_diffusion(df: pd.DataFrame, steps: int, seed: int, k: int = 8):
    n = len(df)
    order = np.argsort(df["age_band"].map(AGE_RANK).to_numpy(), kind="stable")
    d = df.iloc[order].reset_index(drop=True)
    dl = d["attr_digital_literacy"].to_numpy()
    si = d["attr_social_isolation"].to_numpy()
    ad = d["attr_authority_deference"].to_numpy()
    fv = d["attr_financial_vulnerability"].to_numpy()
    neigh = build_network(n, si, k, seed)
    rng = np.random.default_rng(seed + 13)

    bcast_by_level = np.array([0.0, 0.0, 0.015, 0.08, 0.18])  # DL 1..5
    p_bcast = bcast_by_level[dl - 1]
    thr = 0.55 - 0.05 * (ad - 3) - 0.03 * (fv - 3)
    thr = np.clip(thr, 0.2, 0.9)

    adopted = np.zeros(n, dtype=bool)
    curve = []
    for _ in range(steps):
        new = np.zeros(n, dtype=bool)
        hit = (~adopted) & (rng.random(n) < p_bcast)
        new |= hit
        for i in range(n):
            if adopted[i] or new[i]:
                continue
            nb = neigh[i]
            if len(nb) == 0:
                continue
            if adopted[nb].mean() >= thr[i]:
                new[i] = True
        adopted |= new
        curve.append(adopted.mean())
    adopted_orig = np.empty(n, dtype=bool)
    adopted_orig[order] = adopted
    return np.array(curve), adopted_orig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="results_v4")
    args = ap.parse_args()

    base = load_sample(args.n, args.seed)
    curveA, adoptedA = run_diffusion(base, args.steps, args.seed)

    rng = np.random.default_rng(args.seed + 99)
    shuf = base.copy()
    for c in ATTRS:
        shuf[c] = rng.permutation(shuf[c].to_numpy())
    curveB, adoptedB = run_diffusion(shuf, args.steps, args.seed)

    elderly = base["age_band"].isin(["60-74", "75+"]).to_numpy()
    lowdl = (base["attr_digital_literacy"] <= 2).to_numpy()
    iso = (base["attr_social_isolation"] >= 4).to_numpy()
    cohort = elderly & lowdl & iso
    cohort_share = float(cohort.mean())
    reachA_cohort = float(adoptedA[cohort].mean()) if cohort.any() else float("nan")
    reachA_rest = float(adoptedA[~cohort].mean())

    out = Path(args.out); out.mkdir(exist_ok=True)
    summary = {
        "n": int(args.n), "steps": int(args.steps), "seed": int(args.seed),
        "final_reach_KVRB": round(float(curveA[-1]), 4),
        "final_reach_shuffled": round(float(curveB[-1]), 4),
        "reach_gap_pp": round(float((curveB[-1] - curveA[-1]) * 100), 2),
        "compound_cohort_share": round(cohort_share, 4),
        "compound_cohort_n": int(cohort.sum()),
        "cohort_reach_KVRB": round(reachA_cohort, 4),
        "rest_reach_KVRB": round(reachA_rest, 4),
        "cohort_reach_ratio": round(reachA_cohort / reachA_rest, 3) if reachA_rest else None,
    }
    (out / "abm_demo_summary.json").write_text(json.dumps(summary, indent=2))
    with open(out / "abm_demo_summary.txt", "w", encoding="utf-8") as f:
        f.write("KVRB ABM demonstration - behavioural structure changes ABM outcomes\n")
        f.write("=" * 66 + "\n")
        for kk, vv in summary.items():
            f.write(f"{kk}: {vv}\n")
        f.write("\nIdentical model/seed; the only difference is whether agents carry\n")
        f.write("KVRB's demographically structured behavioural attributes (A) or the\n")
        f.write("same marginals with the joint shuffled out (B).\n")
    pd.DataFrame({"step": np.arange(1, args.steps + 1),
                  "reach_KVRB": curveA, "reach_shuffled": curveB}
                 ).to_csv(out / "abm_demo_curves.csv", index=False)

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    xs = np.arange(1, args.steps + 1)
    ax[0].plot(xs, curveA * 100, "-o", ms=3, label="KVRB (structured)")
    ax[0].plot(xs, curveB * 100, "--s", ms=3, label="Shuffled (marginals only)")
    ax[0].set_xlabel("step"); ax[0].set_ylabel("cumulative reach (%)")
    ax[0].set_title("(A) Diffusion under identical model"); ax[0].legend(); ax[0].grid(alpha=.3)
    labels = ["compound-vulnerability\ncohort", "rest of population"]
    vals = [reachA_cohort * 100, reachA_rest * 100]
    ax[1].bar(labels, vals, color=["#c0392b", "#7f8c8d"])
    for i, v in enumerate(vals):
        ax[1].text(i, v + 1, f"{v:.0f}%", ha="center")
    ax[1].set_ylabel("final reach (%)"); ax[1].set_ylim(0, 100)
    ax[1].set_title("(B) KVRB run: under-reach of compound cohort\n(n=%d, %.1f%%)" % (int(cohort.sum()), cohort_share * 100))
    fig.suptitle("KVRB-initialized diffusion: behavioural joint structure shifts model outcomes")
    fig.tight_layout()
    fig.savefig(out / "F8_abm_demo.png", dpi=130)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
