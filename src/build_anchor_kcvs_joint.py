"""
build_anchor_kcvs_joint.py — Route-B step B2: observed within-survey joint for PV x RP (KCVS 2018).

PV (prior_victimization) and RP (reporting_propensity) are measured on the SAME KCVS respondents,
and RP is defined only for victims (the report-to-police item c24 is asked of victims). So the honest
joint is a nested 3-outcome distribution per demographic cell:
    nonvictim          : bct_1 == 0
    victim_unreported  : bct_1 == 1 & c24 == 2 (신고 안 함)
    victim_reported    : bct_1 == 1 & c24 == 1 (신고함)
This preserves the real covariance KCVS measured (victimization rate x conditional reporting rate)
and fixes a coherence bug in independent sampling, where reporting_propensity was assigned to
non-victims for whom the construct is undefined.

Conditioning: age_band x sex x education_tier with the same hierarchical N-floor backoff as B1.
Weighting: wt3. Victims with missing c24 are dropped from the joint estimation (cannot place them).

Output: config/anchors/kcvs_joint_b2.csv  (age_band,sex_mf,education_tier,outcome,prob,backoff,n_cell)
        config/anchors/kcvs_joint_b2.source.json

Usage:  $env:KVRB_DATA_ROOT=...04_data ; py src/build_anchor_kcvs_joint.py
"""
from __future__ import annotations
import json, os
from pathlib import Path
import numpy as np, pandas as pd, pyreadstat

ROOT = os.environ.get("KVRB_DATA_ROOT", "data/raw")
KCVS = os.path.join(ROOT, "KCVS_2018_전국범죄피해자조사", "kcvs2018.sav")
AGE_BINS = [19, 30, 45, 60, 75, 200]
AGE_LABELS = ["19-29", "30-44", "45-59", "60-74", "75+"]
SEX_LABELS = ["M", "F"]
EDU_TIERS = ["lower", "higher"]
OUTCOMES = ["nonvictim", "victim_unreported", "victim_reported"]
FLOOR = 30


def prep():
    cols = ["bct_1", "c24", "bh4_02", "bh3", "b21", "wt3"]
    df, _ = pyreadstat.read_sav(KCVS, usecols=cols)
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[df.wt3.notna() & (df.wt3 > 0)].copy()
    # outcome: drop victims with missing/invalid c24 (cannot place in joint)
    outcome = np.where(df.bct_1 == 0, "nonvictim",
              np.where((df.bct_1 == 1) & (df.c24 == 2), "victim_unreported",
              np.where((df.bct_1 == 1) & (df.c24 == 1), "victim_reported", None)))
    df["outcome"] = outcome
    df = df[df.outcome.notna()].copy()
    df["age_band"] = pd.cut(df.bh4_02, bins=AGE_BINS, labels=AGE_LABELS, right=False).astype("object")
    df["sex_mf"] = df.bh3.map({1: "M", 2: "F"})
    df["education_tier"] = np.where(df.b21.isin([5, 6, 7]), "higher",
                                    np.where(df.b21 >= 0, "lower", None))
    df = df.dropna(subset=["age_band", "sex_mf", "education_tier"])
    df = df[df.age_band != "nan"]
    return df[["age_band", "sex_mf", "education_tier", "outcome", "wt3"]].reset_index(drop=True)


def backoff_table(resp):
    rows = []
    grids = [(a, s, e) for a in AGE_LABELS for s in SEX_LABELS for e in EDU_TIERS]
    specs = [("age+sex+edu", ["age_band", "sex_mf", "education_tier"]),
             ("age+edu", ["age_band", "education_tier"]),
             ("age+sex", ["age_band", "sex_mf"]),
             ("age", ["age_band"]),
             ("global", [])]
    stats = {k: 0 for k, _ in specs}
    for (a, s, e) in grids:
        cv = {"age_band": a, "sex_mf": s, "education_tier": e}
        for name, keys in specs:
            mask = np.ones(len(resp), dtype=bool)
            for k in keys:
                mask &= (resp[k].values == cv[k])
            n = int(mask.sum())
            if n >= FLOOR or name == "global":
                sub = resp[mask]; chosen = (name, sub, n); break
        name, sub, n = chosen
        stats[name] += 1
        wsum = sub.wt3.sum()
        for oc in OUTCOMES:
            p = sub.loc[sub.outcome == oc, "wt3"].sum() / wsum if wsum > 0 else 0.0
            rows.append({"age_band": a, "sex_mf": s, "education_tier": e, "outcome": oc,
                         "prob": round(float(p), 4), "backoff": name, "n_cell": n})
    return pd.DataFrame(rows), stats


def main():
    if not Path(KCVS).exists():
        print(f"[fatal] KCVS not found: {KCVS}"); return
    resp = prep()
    table, stats = backoff_table(resp)
    od = Path("config/anchors"); od.mkdir(parents=True, exist_ok=True)
    table.to_csv(od / "kcvs_joint_b2.csv", index=False, encoding="utf-8")
    chk = table.groupby(["age_band", "sex_mf", "education_tier"]).prob.sum()
    # implied marginals for a sanity print
    vic = resp.groupby("outcome").wt3.sum(); tot = vic.sum()
    rep_rate = vic.get("victim_reported", 0) / (vic.get("victim_reported", 0) + vic.get("victim_unreported", 0))
    src = {"attributes": ["prior_victimization", "reporting_propensity"],
           "survey": "전국범죄피해조사 KCVS 2018 (KICJ) — same respondents",
           "weight_variable": "wt3", "conditioning": ["age_band", "sex_mf", "education_tier"],
           "outcomes": OUTCOMES, "n_floor": FLOOR, "n_respondents": int(len(resp)),
           "backoff_cell_counts": stats,
           "notes": "Observed nested joint P(PV,RP|cell). RP defined only for victims (c24). "
                    "Victims with missing c24 dropped. Fixes independent-sampling incoherence "
                    "(RP assigned to non-victims). No copula; the joint is the empirical conditional."}
    json.dump(src, open(od / "kcvs_joint_b2.source.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"[ok] kcvs_joint_b2.csv  N={len(resp)}  cells=20  backoff={stats}")
    print(f"     prob-sum range [{chk.min():.3f},{chk.max():.3f}]  overall report-rate(victims)={rep_rate:.3f}")
    print(f"     overall outcome shares: " + ", ".join(f"{k} {100*vic[k]/tot:.1f}%" for k in OUTCOMES if k in vic))


if __name__ == "__main__":
    main()
