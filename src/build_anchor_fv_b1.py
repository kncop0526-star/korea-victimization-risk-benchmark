"""
build_anchor_fv_b1.py — Route-B step B1 for financial_vulnerability (가계금융복지조사 가구마스터).

Extends FV from age_band-only to age_band x sex x education_tier, resolving the previously deferred
교육 통합코드(G1-G4) mapping. financial_vulnerability = inverted net-worth quintile (순자산5분위코드:
Q1 lowest networth -> level 5 most vulnerable ... Q5 -> level 1). Weighted by 가중값.

Conditioners come from the HOUSEHOLD HEAD (가구주_성별코드 1남/2여, 가구주_만연령, 가구주_교육정도_통합코드
G4=대학이상 -> higher, G1-G3 -> lower). FV is a household-level attribute; the age-only anchor already
applied head age to the persona, so applying head sex/education is the same head-as-proxy assumption,
now stated. Hierarchical N-floor backoff (FLOOR=30), dense over the 20 cells.

Output: config/anchors/financial_vulnerability_b1.csv (age_band,sex_mf,education_tier,level,prob,backoff,n_cell)
        config/anchors/financial_vulnerability_b1.source.json

Usage: $env:KVRB_DATA_ROOT=...04_data ; py src/build_anchor_fv_b1.py [--year 2024]
"""
from __future__ import annotations
import argparse, glob, json, os
from pathlib import Path
import numpy as np, pandas as pd

ROOT = os.environ.get("KVRB_DATA_ROOT", "data/raw")
AGE_BINS = [19, 30, 45, 60, 75, 200]
AGE_LABELS = ["19-29", "30-44", "45-59", "60-74", "75+"]
SEX_LABELS = ["M", "F"]
EDU_TIERS = ["lower", "higher"]
FLOOR = 30
Q_TO_LEVEL = {"Q1": 5, "Q2": 4, "Q3": 3, "Q4": 2, "Q5": 1}
COLS = ["가구주_성별코드", "가구주_만연령", "가구주_교육정도_통합코드", "순자산5분위코드", "가중값"]


def find_master(year):
    pats = [os.path.join(ROOT, "MDIS_가금복_2024_가구마스터", "*.csv"),
            os.path.join(ROOT, "MDIS_가금복_2024_가구마스터", "**", "*.csv")]
    cands = []
    for p in pats:
        cands += glob.glob(p, recursive=True)
    cands = [c for c in cands if str(year) in os.path.basename(c)] or cands
    return cands[0] if cands else None


def prep(year):
    path = find_master(year)
    if not path:
        raise SystemExit(f"[fatal] 가구마스터 CSV not found under {ROOT}/MDIS_가금복_2024_가구마스터")
    df = pd.read_csv(path, encoding="cp949", usecols=COLS)
    df = df[df["가중값"].notna() & (df["가중값"] > 0)].copy()
    df["level"] = df["순자산5분위코드"].map(Q_TO_LEVEL)
    df["age_band"] = pd.cut(pd.to_numeric(df["가구주_만연령"], errors="coerce"),
                            bins=AGE_BINS, labels=AGE_LABELS, right=False).astype("object")
    df["sex_mf"] = pd.to_numeric(df["가구주_성별코드"], errors="coerce").map({1: "M", 2: "F"})
    df["education_tier"] = np.where(df["가구주_교육정도_통합코드"] == "G4", "higher",
                            np.where(df["가구주_교육정도_통합코드"].isin(["G1", "G2", "G3"]), "lower", None))
    df = df.rename(columns={"가중값": "w"})
    df = df.dropna(subset=["age_band", "sex_mf", "education_tier", "level"])
    df = df[df.age_band != "nan"]
    return df[["age_band", "sex_mf", "education_tier", "level", "w"]].reset_index(drop=True), path


def backoff_table(resp):
    levels = sorted(resp.level.unique())
    rows = []
    grids = [(a, s, e) for a in AGE_LABELS for s in SEX_LABELS for e in EDU_TIERS]
    # FV is a HOUSEHOLD attribute keyed to the head; head sex (71% male) does NOT proxy the persona's
    # sex, and conditioning on it manufactures a spurious FV x sex association (stereotype audit flagged
    # residual V=0.245). Education head-proxy is defensible and carries the FV-DL signal, so FV conditions
    # on age x education only; the same distribution is written for both sexes (sex-invariant).
    specs = [("age+edu", ["age_band", "education_tier"]),
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
        wsum = sub.w.sum()
        for lv in levels:
            p = sub.loc[sub.level == lv, "w"].sum() / wsum if wsum > 0 else 0.0
            rows.append({"age_band": a, "sex_mf": s, "education_tier": e, "level": int(lv),
                         "prob": round(float(p), 4), "backoff": name, "n_cell": n})
    return pd.DataFrame(rows), stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", default="2024")
    args = ap.parse_args()
    resp, path = prep(args.year)
    table, stats = backoff_table(resp)
    od = Path("config/anchors"); od.mkdir(parents=True, exist_ok=True)
    table.to_csv(od / "financial_vulnerability_b1.csv", index=False, encoding="utf-8")
    chk = table.groupby(["age_band", "sex_mf", "education_tier"]).prob.sum()
    src = {"attribute": "financial_vulnerability",
           "survey": "가계금융복지조사 (통계청·한은·금감원) MDIS 가구마스터 " + str(args.year),
           "source_file": os.path.basename(path), "weight_variable": "가중값",
           "conditioning": ["age_band", "education_tier"], "sex_handling": "sex-invariant (dropped: household head sex does not proxy persona sex; manufactured spurious FV x sex assoc V=0.245)", "n_floor": FLOOR,
           "operationalization": "inverted 순자산5분위 (Q1->5 most vulnerable ... Q5->1)",
           "education_map": "통합코드 G4=대학이상->higher, G1-G3->lower (resolves deferred G1-G4 mapping)",
           "n_respondents": int(len(resp)), "backoff_cell_counts": stats,
           "caveat": "Household-level attribute keyed to the head; head age/education applied to the persona "
                     "under the same head-as-proxy assumption the age-only anchor used. SEX dropped after the "
                     "stereotype audit showed head-sex conditioning manufactured a spurious FV x sex association "
                     "(residual V 0.245 -> 0.033); FV is now sex-invariant, conditioned on age x education only."}
    json.dump(src, open(od / "financial_vulnerability_b1.source.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"[ok] financial_vulnerability_b1.csv  N={len(resp)}  src={os.path.basename(path)}")
    print(f"     backoff={stats}  prob-sum range [{chk.min():.3f},{chk.max():.3f}]")


if __name__ == "__main__":
    main()
