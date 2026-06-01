# -*- coding: utf-8 -*-
"""build_human_reread_sheet.py (reviewer M3) — break the all-synthetic round-trip loop with HUMAN raters.
Samples N narratives, strips any leaked '(속성 N)' parentheticals (only ~0.2% of narratives carry them),
and builds an xlsx where a human decodes FV/DL/AD/SI (1-5) from the narrative alone. --score reads the
filled sheet back and computes human-vs-sampled quadratic-weighted kappa — the missing evidence that a
*person* reads the same level the sampler set.

USAGE (Daniel):
  # build the blank rater sheet (sampled values hidden in a separate key file)
  py src/build_human_reread_sheet.py --build --in data/processed/enriched_stage23_N2000.jsonl --n 100 --out results
  #   -> results/human_reread_sheet.xlsx  (give to raters; they fill human_* columns 1-5)
  #   -> results/human_reread_key.csv     (KEEP PRIVATE: sampled values, persona_id)
  # after raters fill it:
  py src/build_human_reread_sheet.py --score --sheet results/human_reread_sheet_FILLED.xlsx \
        --key results/human_reread_key.csv --out results
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import numpy as np, pandas as pd

ATTRS=["financial_vulnerability","digital_literacy","authority_deference","social_isolation"]
KOR={"financial_vulnerability":"재정 취약성","digital_literacy":"디지털 활용",
     "authority_deference":"권위 순응","social_isolation":"사회적 고립"}
LEAK=re.compile(r'\s*\((재정 취약성|디지털 활용|권위 순응|사회적 고립)\s*[1-5]\)')

def qwk(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float); m=~(np.isnan(a)|np.isnan(b)); a,b=a[m],b[m]
    if len(a)<2: return float("nan")
    cats=sorted(set(a)|set(b)); idx={c:i for i,c in enumerate(cats)}; k=len(cats)
    if k<2: return float("nan")
    O=np.zeros((k,k));
    for x,y in zip(a,b): O[idx[x],idx[y]]+=1
    W=np.array([[((i-j)**2)/((k-1)**2) for j in range(k)] for i in range(k)])
    r=O.sum(1); c=O.sum(0); E=np.outer(r,c)/O.sum()
    num=(W*O).sum(); den=(W*E).sum()
    return float(1-num/den) if den>0 else float("nan")

def build(inp, n, out):
    rows=[json.loads(l) for l in open(inp, encoding="utf-8") if l.strip()]
    rng=np.random.default_rng(42); sel=rng.choice(len(rows), min(n,len(rows)), replace=False)
    sheet=[]; key=[]
    for k,i in enumerate(sel):
        d=rows[i]; narr=LEAK.sub("", d.get("attr_narrative","") or "").strip()
        pid=d.get("uuid", f"P{k:04d}")
        sheet.append({"persona_id":pid,"narrative":narr,
                      "human_financial_vulnerability":"","human_digital_literacy":"",
                      "human_authority_deference":"","human_social_isolation":""})
        a=d.get("attr",{}); key.append({"persona_id":pid, **{f"sampled_{x}":a.get(x) for x in ATTRS}})
    out=Path(out); out.mkdir(parents=True, exist_ok=True)
    import openpyxl
    wb=openpyxl.Workbook(); ws=wb.active; ws.title="rater"
    cols=["persona_id","narrative"]+[f"human_{x}" for x in ATTRS]
    ws.append(cols)
    ws.append(["","RATING GUIDE: read each narrative, score 1-5 (1=low, 5=high). FV higher=more vulnerable; "
               "DL higher=more competent; AD higher=more deferent; SI higher=more isolated.","","","",""])
    for r in sheet: ws.append([r[c] for c in cols])
    ws.column_dimensions["B"].width=90
    wb.save(out/"human_reread_sheet.xlsx")
    pd.DataFrame(key).to_csv(out/"human_reread_key.csv", index=False, encoding="utf-8-sig")
    print(f"[ok] results/human_reread_sheet.xlsx ({len(sheet)} personas; leak-stripped) + human_reread_key.csv (PRIVATE)")

def score(sheet, key, out):
    import openpyxl
    wb=openpyxl.load_workbook(sheet); ws=wb["rater"]; rows=list(ws.values)
    hdr=list(rows[0]); data=[dict(zip(hdr,r)) for r in rows[1:] if r[0] and r[0]!=""]
    H=pd.DataFrame(data); K=pd.read_csv(key)
    M=H.merge(K, on="persona_id")
    out=Path(out); res=[]
    for x in ATTRS:
        h=pd.to_numeric(M.get(f"human_{x}"), errors="coerce"); s=pd.to_numeric(M.get(f"sampled_{x}"), errors="coerce")
        v=qwk(h,s); within1=float((np.abs(h-s)<=1).mean()); exact=float((h==s).mean())
        res.append({"attr":x,"human_vs_sampled_qwk":round(v,3),"within1":round(within1,3),"exact":round(exact,3),"n":int(h.notna().sum())})
    cmp=pd.DataFrame(res); cmp.to_csv(out/"human_reread_results.csv", index=False, encoding="utf-8-sig")
    print(cmp.to_string(index=False)); print("\n[ok] results/human_reread_results.csv")
    print("READY §4.2 SENTENCE: a 100-narrative human re-read gives QWK "
          + " / ".join(f"{r['attr'].split('_')[0]} {r['human_vs_sampled_qwk']}" for r in res)
          + " (vs the synthetic round-trip), breaking the all-synthetic loop.")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true"); ap.add_argument("--score", action="store_true")
    ap.add_argument("--in", dest="inp", default="data/processed/enriched_stage23_N2000.jsonl")
    ap.add_argument("--n", type=int, default=100); ap.add_argument("--out", default="results")
    ap.add_argument("--sheet"); ap.add_argument("--key")
    a=ap.parse_args()
    if a.build: build(a.inp, a.n, a.out)
    elif a.score:
        if not (a.sheet and a.key): raise SystemExit("[fatal] --score needs --sheet and --key")
        score(a.sheet, a.key, a.out)
    else: raise SystemExit("[fatal] use --build or --score")

if __name__=="__main__": main()
