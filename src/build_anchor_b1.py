"""
build_anchor_b1.py — Route-B step B1: richer demographic conditioning.

Re-estimate each survey-direct anchor on age_band x sex x education_tier instead of age_band
alone, with a hierarchical N-floor backoff so sparse cells fall back to a coarser, still
data-grounded estimate (never fabricated). Conditioning on shared demographics induces realistic
cross-attribute correlation through common causes (a low-education older person is jointly more
financially strained, less digital, more isolated) — fully data-grounded, no assumed correlation.

Covered anchors (direct .sav access; KVRB_DATA_ROOT must point at Paper F 04_data):
  authority_deference   KGSS  AUTHORT2/4/5/6/7   (2016 wave)         Likert -> weighted-quintile 1..5
  social_isolation      KGSS  SICK1/BORROW1/DOWN1 + NGHASK (2004,2012) structural -> w-quintile 1..5
  prior_victimization   KCVS  bct_1                                   binary 0/1
  reporting_propensity  KCVS  c24 (victims only, 신고=1/미신고=0)       binary 0/1

NOT covered here (need raw MDIS/NIA re-extract + deferred edu-code mapping): financial_vulnerability
(가금복), digital_literacy (디지털격차). Those keep their current conditioning until extracted.

Output (originals untouched):
  config/anchors/<attr>_b1.csv          dense over age_band x sex x education_tier:
        age_band,sex,education_tier,level,prob,backoff,n_cell
  config/anchors/<attr>_b1.source.json  provenance + backoff stats

Levels use GLOBAL weighted quintile edges (Likert) so levels are comparable across cells; the
conditional table is P(level | cell). Backoff order (most to least specific):
  (age,sex,edu) -> (age,edu) -> (age,sex) -> (age,) -> ()  ; first subset with n>=FLOOR wins.

Usage (PowerShell):
  $env:KVRB_DATA_ROOT="C:\\...\\06_Paper_F_SSCI_BDS\\04_data"
  py src/build_anchor_b1.py            # all four
  py src/build_anchor_b1.py --attr prior_victimization
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
import numpy as np
import pandas as pd
import pyreadstat

ROOT = os.environ.get("KVRB_DATA_ROOT", "data/raw")
AGE_BINS = [19, 30, 45, 60, 75, 200]
AGE_LABELS = ["19-29", "30-44", "45-59", "60-74", "75+"]
SEX_LABELS = ["M", "F"]
EDU_TIERS = ["lower", "higher"]
FLOOR = 30  # minimum respondents in a cell before backing off to a coarser conditioner

KGSS = lambda: os.path.join(ROOT, "KGSS_2003_2021", "Korean_data_CUM0048.sav")
KCVS = lambda: os.path.join(ROOT, "KCVS_2018_전국범죄피해자조사", "kcvs2018.sav")


def age_band(age):
    return pd.cut(pd.to_numeric(age, errors="coerce"), bins=AGE_BINS, labels=AGE_LABELS,
                  right=False).astype("object")


# ---------- per-attribute respondent-level builders -> DataFrame[age_band,sex,education_tier,level,w] ----------

def prep_kgss_authority():
    items = ["AUTHORT2", "AUTHORT4", "AUTHORT5", "AUTHORT6", "AUTHORT7"]
    cols = items + ["AGE", "SEX", "EDUC", "FINALWT"]
    df, _ = pyreadstat.read_sav(KGSS(), usecols=cols)
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    scale_items = df[items].where((df[items] >= 1) & (df[items] <= 5))
    keep = (scale_items.notna().sum(axis=1) >= 3) & df.FINALWT.notna() & (df.FINALWT > 0)
    df = df[keep].copy()
    scale = scale_items.loc[df.index].mean(axis=1).values
    level = weighted_quintile_levels(scale, df.FINALWT.values)
    return assemble(df, level, df.FINALWT.values, sex_col="SEX", edu_col="EDUC",
                    higher_set={4, 5, 6, 7}), 5


def prep_kgss_isolation():
    cols = ["SICK1", "BORROW1", "DOWN1", "NGHASK", "AGE", "SEX", "EDUC", "FINALWT"]
    df, _ = pyreadstat.read_sav(KGSS(), usecols=cols)
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    dom = df[["SICK1", "BORROW1", "DOWN1"]].where(df[["SICK1", "BORROW1", "DOWN1"]] >= 0)
    pd_valid = dom.notna().sum(axis=1)
    p_def = (dom == 0).sum(axis=1) / pd_valid.replace(0, np.nan)
    ng = df["NGHASK"].where((df["NGHASK"] >= 1) & (df["NGHASK"] <= 5))
    n_def = (5 - ng) / 4.0
    comp = pd.concat([p_def, n_def], axis=1)
    score = comp.mean(axis=1, skipna=True)
    keep = comp.notna().sum(axis=1) >= 1
    keep &= df.FINALWT.notna() & (df.FINALWT > 0)
    df = df[keep].copy()
    score = score[keep].values
    level = weighted_quintile_levels(score, df.FINALWT.values)
    return assemble(df, level, df.FINALWT.values, sex_col="SEX", edu_col="EDUC",
                    higher_set={4, 5, 6, 7}), 5


def prep_kcvs_prior():
    cols = ["bct_1", "bh4_02", "bh3", "b21", "wt3"]
    df, _ = pyreadstat.read_sav(KCVS(), usecols=cols)
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    keep = df.bct_1.isin([0, 1]) & df.wt3.notna() & (df.wt3 > 0)
    df = df[keep].copy()
    level = df.bct_1.astype(int).values
    return assemble(df, level, df.wt3.values, sex_col="bh3", edu_col="b21",
                    higher_set={5, 6, 7}, age_col="bh4_02"), 2


def prep_kcvs_reporting():
    cols = ["c24", "bh4_02", "bh3", "b21", "wt3"]
    df, _ = pyreadstat.read_sav(KCVS(), usecols=cols)
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    keep = df.c24.isin([1, 2]) & df.wt3.notna() & (df.wt3 > 0)   # victims who answered reporting
    df = df[keep].copy()
    level = (df.c24 == 1).astype(int).values                      # 신고=1, 미신고=0
    return assemble(df, level, df.wt3.values, sex_col="bh3", edu_col="b21",
                    higher_set={5, 6, 7}, age_col="bh4_02"), 2


def weighted_quintile_levels(scale, w):
    order = np.argsort(scale)
    cw = np.cumsum(w[order]) / w.sum()
    edges = [np.interp(q, cw, scale[order]) for q in (0.2, 0.4, 0.6, 0.8)]
    return np.array([sum(v > e for e in edges) + 1 for v in scale])


def assemble(df, level, w, sex_col, edu_col, higher_set, age_col="AGE"):
    ab = age_band(df[age_col])
    sex = df[sex_col].map({1: "M", 2: "F"})
    edu = np.where(df[edu_col].isin(list(higher_set)), "higher",
                   np.where(df[edu_col] >= 0, "lower", None))
    out = pd.DataFrame({"age_band": ab.values, "sex_mf": sex.values, "education_tier": edu,
                        "level": level, "w": w})
    out = out.dropna(subset=["age_band", "sex_mf", "education_tier"])
    out = out[out.age_band != "nan"]
    return out.reset_index(drop=True)


# ---------- backoff estimator over the full grid ----------

def backoff_table(resp, n_levels):
    levels = sorted(resp.level.unique())
    rows = []
    grids = [(a, s, e) for a in AGE_LABELS for s in SEX_LABELS for e in EDU_TIERS]
    backoff_specs = [
        ("age+sex+edu", ["age_band", "sex_mf", "education_tier"]),
        ("age+edu", ["age_band", "education_tier"]),
        ("age+sex", ["age_band", "sex_mf"]),
        ("age", ["age_band"]),
        ("global", []),
    ]
    stats = {k: 0 for k, _ in backoff_specs}
    for (a, s, e) in grids:
        cellvals = {"age_band": a, "sex_mf": s, "education_tier": e}
        chosen = None
        for name, keys in backoff_specs:
            mask = np.ones(len(resp), dtype=bool)
            for k in keys:
                mask &= (resp[k].values == cellvals[k])
            n = int(mask.sum())
            if n >= FLOOR or name == "global":
                sub = resp[mask]
                chosen = (name, sub, n)
                break
        name, sub, n = chosen
        stats[name] += 1
        wsum = sub.w.sum()
        for lv in levels:
            p = sub.loc[sub.level == lv, "w"].sum() / wsum if wsum > 0 else 0.0
            rows.append({"age_band": a, "sex_mf": s, "education_tier": e, "level": int(lv),
                         "prob": round(float(p), 4), "backoff": name, "n_cell": n})
    return pd.DataFrame(rows), stats


PREP = {
    "authority_deference": (prep_kgss_authority, "한국종합사회조사 KGSS (AUTHORT, 2016 wave)", "FINALWT", 2),
    "social_isolation": (prep_kgss_isolation, "한국종합사회조사 KGSS (support battery, 2004+2012)", "FINALWT", 2),
    "prior_victimization": (prep_kcvs_prior, "전국범죄피해조사 KCVS 2018 (KICJ)", "wt3", 4),
    "reporting_propensity": (prep_kcvs_reporting, "전국범죄피해조사 KCVS 2018 (KICJ, victims only)", "wt3", 4),
}


def build(attr):
    prep_fn, survey, wcol, tier = PREP[attr]
    resp, n_levels = prep_fn()
    table, stats = backoff_table(resp, n_levels)
    od = Path("config/anchors"); od.mkdir(parents=True, exist_ok=True)
    table.to_csv(od / f"{attr}_b1.csv", index=False, encoding="utf-8")
    # sanity: each cell's probs sum to ~1
    chk = table.groupby(["age_band", "sex_mf", "education_tier"]).prob.sum()
    src = {
        "attribute": attr, "survey": survey, "weight_variable": wcol, "anchor_tier": tier,
        "conditioning": ["age_band", "sex_mf", "education_tier"],
        "backoff_order": ["age+sex+edu", "age+edu", "age+sex", "age", "global"],
        "n_floor": FLOOR, "n_respondents": int(len(resp)),
        "backoff_cell_counts": stats,
        "notes": "B1 richer conditioning. Dense over 5 age x 2 sex x 2 edu = 20 cells; each cell "
                 "uses the most specific demographic subset with n>=floor, else backs off. "
                 "Probabilities are weighted P(level|cell). No correlation assumed; cross-attribute "
                 "structure arises through shared demographic conditioning (common causes).",
    }
    json.dump(src, open(od / f"{attr}_b1.source.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"[ok] {attr}_b1.csv  N={len(resp)}  cells=20  backoff={stats}  "
          f"prob-sum range [{chk.min():.3f},{chk.max():.3f}]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attr", choices=list(PREP), default=None)
    args = ap.parse_args()
    if not Path(ROOT).exists():
        print(f"[fatal] KVRB_DATA_ROOT not found: {ROOT}"); return
    attrs = [args.attr] if args.attr else list(PREP)
    for a in attrs:
        build(a)


if __name__ == "__main__":
    main()
