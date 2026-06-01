"""
build_anchor_digital_literacy.py
------------------------------------------------------------------
Build a REAL anchor P(digital_literacy | age_band x education_tier) from the
디지털정보격차 실태조사 (Digital Divide Survey, 과기정통부·NIA) public micro file
(일반국민 / general-population sample).

Construct (v1, transparent & revisable):
  competency       = mean of 활용역량 items Q8_1..Q8_9 (4-pt Likert, higher=more competent;
                     incl. online payment / kiosk / authentication — phishing-relevant skills)
  digital_literacy = weighted quintile of competency, 1 (lowest) .. 5 (highest)

Conditioning: age_band (ADQ1 = RAW age, binned to Nemotron's 5-band scheme)
              x education_tier (ADQ4: 1-3 = lower, 4 = higher).
Weighting: WT applied (required).

Input: the cached needed-columns CSV extracted from 일반국민.xlsx (ADQ1, ADQ4, WT, Q8_1..Q8_9).
       (The full xlsx is slow to parse; extract those columns once, then run this.)

License: source is 공공데이터포털 제2유형 (출처표시 + 상업적 이용금지 / NON-COMMERCIAL).
Only the aggregated anchor table is written, with attribution; see .source.json.
------------------------------------------------------------------
한국어 주석: 활용역량 9문항 평균을 디지털역량으로, 가중 5분위로 ordinal화.
연령대(원자료 나이→5밴드)×학력(ADQ4) 조건부 가중확률. 가중치(WT) 필수.
"""

from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

Q8 = [f"Q8_{i}" for i in range(1, 10)]
AGE_BINS = [19, 30, 45, 60, 75, 200]
AGE_LABELS = ["19-29", "30-44", "45-59", "60-74", "75+"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="cached needcols CSV (ADQ1,ADQ4,WT,Q8_1..9)")
    ap.add_argument("--year", default="2025")
    ap.add_argument("--out-dir", default="config/anchors")
    args = ap.parse_args()

    df = pd.read_csv(args.source)
    for c in ["ADQ1", "ADQ4", "WT"] + Q8:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["ADQ1", "ADQ4", "WT"])
    df = df[(df.WT > 0) & (df.ADQ4.isin([1, 2, 3, 4]))]

    comp_items = df[Q8].where((df[Q8] >= 1) & (df[Q8] <= 4))
    df = df[comp_items.notna().sum(axis=1) >= 5]
    competency = comp_items.loc[df.index].mean(axis=1).values

    band = pd.cut(df.ADQ1, bins=AGE_BINS, labels=AGE_LABELS, right=False).astype(str).values
    edu = np.where(df.ADQ4.isin([1, 2, 3]), "lower", "higher")
    w = df.WT.values

    # weighted quintile edges of competency
    order = np.argsort(competency)
    cw = np.cumsum(w[order]) / w.sum()
    edges = [np.interp(q, cw, competency[order]) for q in (0.2, 0.4, 0.6, 0.8)]
    level = np.array([sum(v > e for e in edges) + 1 for v in competency])

    t = pd.DataFrame({"age_band": band, "education_tier": edu, "level": level, "w": w})
    t = t[t.age_band != "nan"]
    g = t.groupby(["age_band", "education_tier", "level"])["w"].sum().reset_index()
    g["prob"] = g["w"] / g.groupby(["age_band", "education_tier"])["w"].transform("sum")
    out = g[["age_band", "education_tier", "level", "prob"]].sort_values(
        ["age_band", "education_tier", "level"]).reset_index(drop=True)
    out["prob"] = out["prob"].round(4)

    od = Path(args.out_dir); od.mkdir(parents=True, exist_ok=True)
    out.to_csv(od / "digital_literacy.csv", index=False, encoding="utf-8")
    src = {
        "attribute": "digital_literacy",
        "survey": "디지털정보격차 실태조사 (Digital Divide Survey)",
        "conducting_body": "과학기술정보통신부·한국지능정보사회진흥원(NIA)",
        "access": "공공데이터포털 dataset 15038422 (일반국민 micro file)",
        "reference_year": args.year,
        "weight_variable": "WT",
        "operationalization": "competency = mean(Q8_1..Q8_9 활용역량, 4pt Likert); digital_literacy = weighted quintile (1=low,5=high)",
        "conditioning": ["age_band (ADQ1 raw age -> 5-band)", "education_tier (ADQ4: 1-3=lower,4=higher)"],
        "n_respondents": int(len(df)),
        "anchor_tier": 1,
        "license": "공공데이터포털 제2유형 (출처표시 + 상업적 이용금지 / NON-COMMERCIAL). Aggregate table only; NC source flagged.",
        "notes": "활용역량 sub-index incl. online payment/kiosk/authentication (phishing-relevant). ADQ1 is raw age, binned to Nemotron's native 5-band scheme.",
    }
    json.dump(src, open(od / "digital_literacy.source.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    out["wl"] = out.level * out.prob
    print("[ok] digital_literacy.csv  N=" + str(len(df)) + " (weighted)")
    print("[edges] competency quintile cuts: " + ", ".join(str(round(e, 3)) for e in edges))
    print("[anchor] mean digital_literacy level by cell (5=most literate):")
    print(out.groupby(["age_band", "education_tier"]).wl.sum().round(2).to_string())


if __name__ == "__main__":
    main()
