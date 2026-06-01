"""
build_anchor_kcvs.py
------------------------------------------------------------------
Build REAL anchors from 전국범죄피해조사 (KCVS) 2018 (KICJ), person file:
  prior_victimization  P(level | age_band)  level 0=없음, 1=피해경험 (bct_1)         [N=13,144]
  reporting_propensity P(level | age_band)  level 0=미신고, 1=신고 (c24, victims only) [N~452 low]
Weighting: wt3 (가구원 가중치). Age: bh4_02 (raw) -> 5-band.

License: KICJ 공공저작물 제4유형 (출처표시 + 비영리 + 변경금지 / NON-COMMERCIAL, NO-DERIV) +
KOSSDA 회원공개. Only aggregate anchor tables published, with attribution.
------------------------------------------------------------------
한국어 주석: KCVS 2018에서 피해경험(bct_1)·신고여부(c24, 피해자만)의 가중 조건부 분포 산출.
신고성향은 피해자 표본만이라 저표본(플래그). 집계만 공개, 제4유형 NC/ND.
"""
from __future__ import annotations
import json, os
from pathlib import Path
import numpy as np, pandas as pd, pyreadstat

SAV = os.path.join(os.environ.get("KVRB_DATA_ROOT", "data/raw"), "KCVS_2018", "kcvs2018.sav")
AGE_BINS = [19, 30, 45, 60, 75, 200]
AGE_LABELS = ["19-29", "30-44", "45-59", "60-74", "75+"]


def weighted_p(df, level_col, wcol="wt3"):
    g = df.groupby(["age_band", level_col])[wcol].sum().reset_index()
    g["prob"] = g[wcol] / g.groupby("age_band")[wcol].transform("sum")
    out = g[["age_band", level_col, "prob"]].rename(columns={level_col: "level"})
    return out.sort_values(["age_band", "level"]).reset_index(drop=True).round({"prob": 4})


def write(out, name, src, od):
    out.to_csv(od / (name + ".csv"), index=False, encoding="utf-8")
    json.dump(src, open(od / (name + ".source.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def main():
    df, _ = pyreadstat.read_sav(SAV, usecols=["bct_1", "c24", "bh4_02", "wt3"])
    for c in ["bct_1", "c24", "bh4_02", "wt3"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[df.wt3.notna() & (df.wt3 > 0) & df.bh4_02.notna()]
    df["age_band"] = pd.cut(df.bh4_02, bins=AGE_BINS, labels=AGE_LABELS, right=False).astype(str)
    df = df[df.age_band != "nan"]
    od = Path("config/anchors"); od.mkdir(parents=True, exist_ok=True)

    base_src = {"survey": "전국범죄피해조사 KCVS 2018", "conducting_body": "한국형사·법무정책연구원",
                "access": "KOSSDA 회원공개 (KICJ 작성)", "reference_year": "2018",
                "weight_variable": "wt3", "conditioning": ["age_band (bh4_02 -> 5-band)"],
                "license": "KICJ 공공저작물 제4유형 (출처표시+비영리+변경금지 / NC, ND) + KOSSDA 회원공개. 집계만 공개."}

    # prior_victimization
    v = df[df.bct_1.isin([0, 1])].copy(); v["level"] = v.bct_1.astype(int)
    out = weighted_p(v, "level")
    write(out, "prior_victimization", {**base_src, "attribute": "prior_victimization",
          "operationalization": "level=bct_1 (0=없음,1=피해경험); P(level|age_band) weighted",
          "n_respondents": int(len(v)), "anchor_tier": 1}, od)
    print("[ok] prior_victimization.csv N=" + str(len(v)))
    print(out.pivot(index="age_band", columns="level", values="prob").to_string())

    # reporting_propensity (victims with c24 in {1,2})
    r = df[df.c24.isin([1, 2])].copy(); r["level"] = (r.c24 == 1).astype(int)  # 1=신고
    out2 = weighted_p(r, "level")
    write(out2, "reporting_propensity", {**base_src, "attribute": "reporting_propensity",
          "operationalization": "victims only; level=1 if c24==신고했다 else 0; P(level|age_band) weighted",
          "n_respondents": int(len(r)), "anchor_tier": 1, "low_n_flag": True,
          "notes": "Victim subsample only (~452) -> low N, sparse cells. Disposition applied to all personas in enrichment."}, od)
    print("\n[ok] reporting_propensity.csv N=" + str(len(r)) + " (victims only, low-N)")
    print(out2.pivot(index="age_band", columns="level", values="prob").to_string())


if __name__ == "__main__":
    main()
