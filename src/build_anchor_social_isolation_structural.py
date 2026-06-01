"""
build_anchor_social_isolation_structural.py
------------------------------------------------------------------
Build a REAL *structural* social_isolation anchor P(level | age_band) from KGSS, replacing
the earlier OTHREL (subjective loneliness) version per author decision.

Structural isolation = lack of actual support sources:
  personal_deficit = mean over {SICK1,BORROW1,DOWN1} of (helper == 0 '없음'), valid(>=0)
                     (아플때/돈빌릴때/우울할때 도움청할 사람이 '없음'인 영역 비율)
  neighbor_deficit = (5 - NGHASK)/4, NGHASK in 1..5 (1=0명 ... 5=10명+)  -> higher = fewer neighbors
  score = mean of available components (>=1 required)
  social_isolation level 1..5 = weighted quintile of score (5 = most isolated)

Conditioning: age_band (AGE -> 5-band). Weighting: FINALWT. CAVEAT: KGSS support battery is
single-wave -> low effective N; indicative anchor.
------------------------------------------------------------------
한국어 주석: 주관적 외로움(OTHREL) 대신 '지원 부재=구조적 고립'으로 재정의.
도움청할 사람 없음 + 이웃 수 적음을 결합, 가중 5분위로 ordinal화. 저표본 플래그.
"""
from __future__ import annotations
import json, os
from pathlib import Path
import numpy as np, pandas as pd, pyreadstat

SAV = os.path.join(os.environ.get("KVRB_DATA_ROOT", "data/raw"), "KGSS_2003_2021", "Korean_data_CUM0048.sav")
AGE_BINS = [19, 30, 45, 60, 75, 200]
AGE_LABELS = ["19-29", "30-44", "45-59", "60-74", "75+"]

def main():
    cols = ["SICK1","BORROW1","DOWN1","NGHASK","AGE","FINALWT"]
    df,_ = pyreadstat.read_sav(SAV, usecols=cols)
    for c in cols: df[c] = pd.to_numeric(df[c], errors="coerce")

    # personal support deficit: among valid(>=0) of the 3 domains, fraction == 0 (없음)
    dom = df[["SICK1","BORROW1","DOWN1"]].where(df[["SICK1","BORROW1","DOWN1"]] >= 0)
    pd_valid = dom.notna().sum(axis=1)
    p_def = (dom == 0).sum(axis=1) / pd_valid.replace(0, np.nan)
    # neighbor deficit from NGHASK 1..5
    ng = df["NGHASK"].where((df["NGHASK"] >= 1) & (df["NGHASK"] <= 5))
    n_def = (5 - ng) / 4.0
    score = pd.concat([p_def, n_def], axis=1).mean(axis=1, skipna=True)

    m = score.notna() & df["FINALWT"].notna() & (df["FINALWT"] > 0)
    d = pd.DataFrame({"score": score[m].values,
                      "age_band": pd.cut(df["AGE"][m], bins=AGE_BINS, labels=AGE_LABELS, right=False).astype(str),
                      "w": df["FINALWT"][m].values})
    d = d[d.age_band != "nan"]

    s = d.score.values; w = d.w.values
    o = np.argsort(s); cw = np.cumsum(w[o]) / w.sum()
    edges = [np.interp(q, cw, s[o]) for q in (0.2, 0.4, 0.6, 0.8)]
    d["level"] = [sum(v > e for e in edges) + 1 for v in s]

    g = d.groupby(["age_band","level"])["w"].sum().reset_index()
    g["prob"] = g["w"] / g.groupby("age_band")["w"].transform("sum")
    out = g[["age_band","level","prob"]].sort_values(["age_band","level"]).reset_index(drop=True)
    out["prob"] = out["prob"].round(4)

    od = Path("config/anchors"); od.mkdir(parents=True, exist_ok=True)
    out.to_csv(od / "social_isolation.csv", index=False, encoding="utf-8")
    src = {
        "attribute": "social_isolation",
        "operationalization_version": "structural (v2; replaces OTHREL subjective-loneliness v1)",
        "survey": "한국종합사회조사 KGSS (2003-2021 cumulative)",
        "conducting_body": "성균관대 서베이리서치센터",
        "access": "on-hand (KOSSDA-distributed)",
        "weight_variable": "FINALWT",
        "operationalization": "structural isolation = mean of [personal support deficit (SICK/BORROW/DOWN helper=='없음' fraction), neighbor deficit ((5-NGHASK)/4)]; weighted quintile 1..5 (5=most isolated)",
        "conditioning": ["age_band (AGE -> 5-band)"],
        "n_respondents": int(len(d)),
        "anchor_tier": 2,
        "low_n_flag": True,
        "notes": "Structural (support-availability) measure, not subjective loneliness. Single-wave support battery -> low N. 75+ cell may be sparse.",
    }
    json.dump(src, open(od / "social_isolation.source.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    out["wl"] = out.level * out.prob
    print("[ok] social_isolation.csv (STRUCTURAL) N=" + str(len(d)) + " (weighted, low-N)")
    print("[edges] quintile cuts: " + ", ".join(str(round(e,3)) for e in edges))
    print("[anchor] mean structural social_isolation level by age_band (5=most isolated):")
    print(out.groupby("age_band").wl.sum().round(2).to_string())

if __name__ == "__main__":
    main()
