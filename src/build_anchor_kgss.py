"""
build_anchor_kgss.py
------------------------------------------------------------------
Build a REAL anchor P(attribute | age_band) from KGSS (한국종합사회조사, 2003-2021
cumulative). Generic over a Likert item set.

Used for two attributes (both on-hand, download-0):
  authority_deference : AUTHORT2,4,5,6,7  (권위 순종·법질서·질서정연 권위주의 척도; higher=more deferent)
  social_isolation    : OTHREL3,4,5,6,7   (외로움·기댈 사람 없음·신뢰관계 부재; higher=more isolated)

Construct (v1): scale = mean of valid (1-5) items (>=3 answered); weighted quintile -> level 1..5.
Conditioning (v1): age_band (AGE binned to Nemotron's 5-band scheme).
Weighting: FINALWT applied.

CAVEAT: these item batteries appear only in specific KGSS waves, so the effective N is small
(authority ~900, isolation ~1,400). Flagged low-N; treat as indicative. Add education/region
conditioning only if cell sizes allow.

Input: cached needcols CSV extracted from the KGSS .sav (pyreadstat).
------------------------------------------------------------------
한국어 주석: KGSS 리커트 문항 평균을 가중 5분위로 ordinal화, 연령대 조건부 P(level|age_band).
문항이 특정 wave에만 있어 표본이 작음(저표본 플래그). FINALWT 적용.
"""

from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

AGE_BINS = [19, 30, 45, 60, 75, 200]
AGE_LABELS = ["19-29", "30-44", "45-59", "60-74", "75+"]

PRESETS = {
    "authority_deference": ["AUTHORT2", "AUTHORT4", "AUTHORT5", "AUTHORT6", "AUTHORT7"],
    "social_isolation": ["OTHREL3", "OTHREL4", "OTHREL5", "OTHREL6", "OTHREL7"],
}
DESC = {
    "authority_deference": "AUTHORT2/4/5/6/7 (권위주의·법질서·질서 순응; higher=more deferent)",
    "social_isolation": "OTHREL3/4/5/6/7 (외로움·기댈 사람 없음·신뢰관계 부재; higher=more isolated)",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="cached KGSS needcols CSV")
    ap.add_argument("--attr", required=True, choices=list(PRESETS))
    ap.add_argument("--year", default="2003-2021 (item-specific waves)")
    ap.add_argument("--out-dir", default="config/anchors")
    args = ap.parse_args()

    items = PRESETS[args.attr]
    df = pd.read_csv(args.source)
    for c in items + ["AGE", "FINALWT"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    scale_items = df[items].where((df[items] >= 1) & (df[items] <= 5))
    keep = scale_items.notna().sum(axis=1) >= 3
    df = df[keep & df.FINALWT.notna() & (df.FINALWT > 0)]
    scale = scale_items.loc[df.index].mean(axis=1).values

    band = pd.cut(df.AGE, bins=AGE_BINS, labels=AGE_LABELS, right=False).astype(str).values
    w = df.FINALWT.values

    order = np.argsort(scale)
    cw = np.cumsum(w[order]) / w.sum()
    edges = [np.interp(q, cw, scale[order]) for q in (0.2, 0.4, 0.6, 0.8)]
    level = np.array([sum(v > e for e in edges) + 1 for v in scale])

    t = pd.DataFrame({"age_band": band, "level": level, "w": w})
    t = t[t.age_band != "nan"]
    g = t.groupby(["age_band", "level"])["w"].sum().reset_index()
    g["prob"] = g["w"] / g.groupby("age_band")["w"].transform("sum")
    out = g[["age_band", "level", "prob"]].sort_values(["age_band", "level"]).reset_index(drop=True)
    out["prob"] = out["prob"].round(4)

    od = Path(args.out_dir); od.mkdir(parents=True, exist_ok=True)
    out.to_csv(od / f"{args.attr}.csv", index=False, encoding="utf-8")
    src = {
        "attribute": args.attr,
        "survey": "한국종합사회조사 KGSS (2003-2021 cumulative)",
        "conducting_body": "성균관대 서베이리서치센터 (KGSS)",
        "access": "on-hand (KOSSDA-distributed cumulative file)",
        "reference_year": args.year,
        "weight_variable": "FINALWT",
        "operationalization": "scale = mean of valid(1-5) items (>=3 answered); weighted quintile 1..5. " + DESC[args.attr],
        "conditioning": ["age_band (AGE -> 5-band)"],
        "n_respondents": int(len(df)),
        "anchor_tier": 2,
        "low_n_flag": True,
        "notes": "Item battery present only in specific KGSS waves -> low effective N; indicative anchor. Education/region conditioning omitted (cell-size). 75+ cell may be sparse.",
    }
    json.dump(src, open(od / f"{args.attr}.source.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    out["wl"] = out.level * out.prob
    print("[ok] " + args.attr + ".csv  N=" + str(len(df)) + " (weighted, low-N)")
    print("[edges] quintile cuts: " + ", ".join(str(round(e, 3)) for e in edges))
    print("[anchor] mean " + args.attr + " level by age_band (5=high):")
    print(out.groupby("age_band").wl.sum().round(2).to_string())


if __name__ == "__main__":
    main()
