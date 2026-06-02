# -*- coding: utf-8 -*-
"""validate_residual_magnitude_match.py (reviewer M2) — does the synthetic 'measured' residual
(e.g. AD×sex V=0.145, SI×sex V=0.084) MATCH the source survey's V, or AMPLIFY it?
Computes the source-survey Cramér's V (KGSS) with a bootstrap CI and prints it beside the synthetic V.
Verdict: within CI -> 'reproduces'; synthetic > CI upper -> 'amplifies'; below -> 'attenuates'.

USAGE (Daniel, KGSS microdata on PC):
  py src/validate_residual_magnitude_match.py --kgss path\to\kgss_needcols.csv --out results
  # dry-run (fabricated, NOT a result):
  py src/validate_residual_magnitude_match.py --mock --out results

KGSS needcols CSV must carry (same extract as build_anchor_kgss.py): AUTHORT2/4/5/6/7, SEX, AGE,
FINALWT, and the structural-isolation items used by the released SI anchor (set SI_ITEMS below to match
build_anchor_social_isolation_structural.py — e.g. the support battery). Synthetic residual V is read
from results/stereotype_audit_v3.csv.
"""
from __future__ import annotations
import argparse, csv
from pathlib import Path
import numpy as np, pandas as pd

AGE_BINS=[19,30,45,60,75,200]; AGE_LABELS=["19-29","30-44","45-59","60-74","75+"]
AD_ITEMS=["AUTHORT2","AUTHORT4","AUTHORT5","AUTHORT6","AUTHORT7"]
# set to match the RELEASED social_isolation anchor (structural support battery). Edit if names differ.
SI_ITEMS=["SICK1","BORROW1","DOWN1","NGHASK"]   # structural SI: support deficit + neighbor deficit (matches released anchor)
WEIGHT="FINALWT"; SEX="SEX"; AGE="AGE"

def cramers_v(a,b,w):
    a=pd.Series(a); b=pd.Series(b); w=pd.Series(w)
    m=a.notna()&b.notna()&w.notna(); a,b,w=a[m],b[m],w[m]
    if a.nunique()<2 or b.nunique()<2: return float("nan")
    tab=pd.crosstab(a,b,values=w,aggfunc="sum").fillna(0.0).values.astype(float)
    n=tab.sum(); r=tab.sum(1,keepdims=True); c=tab.sum(0,keepdims=True); exp=r@c/n
    with np.errstate(divide="ignore",invalid="ignore"):
        chi2=np.nansum((tab-exp)**2/np.where(exp==0,np.nan,exp))
    k=min(tab.shape)-1
    return float(np.sqrt(chi2/(n*k))) if k>0 and n>0 else float("nan")

def to_level(df, items):
    sc=df[items].where((df[items]>=1)&(df[items]<=5))
    keep=sc.notna().sum(axis=1)>=max(1,len(items)//2)
    d=df[keep & df[WEIGHT].notna() & (df[WEIGHT]>0)].copy()
    scale=sc.loc[d.index].mean(axis=1).values; w=d[WEIGHT].values
    order=np.argsort(scale); cw=np.cumsum(w[order])/w.sum()
    edges=[np.interp(q,cw,scale[order]) for q in (0.2,0.4,0.6,0.8)]
    lvl=np.array([sum(v>e for e in edges)+1 for v in scale])
    return d, lvl, w

def structural_si_level(df):
    """Mirror build_anchor_social_isolation_structural: SI = weighted quintile of
    mean[personal-support deficit (SICK1/BORROW1/DOWN1 helper==0 '없음' fraction), neighbor deficit (5-NGHASK)/4]."""
    for c in ["SICK1","BORROW1","DOWN1","NGHASK",WEIGHT,SEX,AGE]:
        if c in df.columns: df[c]=pd.to_numeric(df[c], errors="coerce")
    dom=df[["SICK1","BORROW1","DOWN1"]].where(df[["SICK1","BORROW1","DOWN1"]]>=0)
    pdv=dom.notna().sum(axis=1)
    personal=(dom==0).sum(axis=1)/pdv.replace(0,np.nan)   # frac of VALID needs with no helper; NaN if none valid
    ng=df["NGHASK"].where((df["NGHASK"]>=1)&(df["NGHASK"]<=5))
    neighbor=(5-ng)/4.0
    score=pd.concat([personal,neighbor],axis=1).mean(axis=1,skipna=True)
    d=df[score.notna() & df[WEIGHT].notna() & (df[WEIGHT]>0)].copy()
    s=score.loc[d.index].values; w=d[WEIGHT].values
    order=np.argsort(s); cw=np.cumsum(w[order])/w.sum()
    edges=[np.interp(q,cw,s[order]) for q in (0.2,0.4,0.6,0.8)]
    lvl=np.array([sum(v>e for e in edges)+1 for v in s])
    sex=d[SEX].values
    V=cramers_v(lvl,sex,w)
    rng=np.random.default_rng(42); idx=np.arange(len(lvl)); boots=[]
    for _ in range(400):
        b=rng.choice(idx,len(idx),replace=True); boots.append(cramers_v(lvl[b],sex[b],w[b]))
    return V,(np.nanpercentile(boots,2.5),np.nanpercentile(boots,97.5)),len(lvl)


def source_V(df, items, label):
    have=[c for c in items if c in df.columns]
    if len(have)<2: return float("nan"), (float("nan"),float("nan")), 0
    for c in have+[WEIGHT,SEX,AGE]:
        df[c]=pd.to_numeric(df[c], errors="coerce")
    d,lvl,w=to_level(df, have)
    sex=d[SEX].values
    V=cramers_v(lvl, sex, w)
    rng=np.random.default_rng(42); idx=np.arange(len(lvl)); boots=[]
    for _ in range(400):
        s=rng.choice(idx,len(idx),replace=True)
        boots.append(cramers_v(lvl[s], sex[s], w[s]))
    lo,hi=np.nanpercentile(boots,2.5),np.nanpercentile(boots,97.5)
    return V,(lo,hi),len(lvl)

def synth_residual(attr):
    f=Path("results/stereotype_audit_v3.csv")
    if not f.exists(): return float("nan")
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r["attr"]==attr and r["protected"]=="sex":
            return float(r["residual_V"])
    return float("nan")

def verdict(syn, lo, hi):
    if any(np.isnan(x) for x in (syn,lo,hi)): return "n/a"
    if syn>hi: return "AMPLIFIES (synthetic > source CI)"
    if syn<lo: return "attenuates (synthetic < source CI)"
    return "reproduces (within source CI)"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--kgss", help="cached KGSS needcols CSV")
    ap.add_argument("--out", default="results"); ap.add_argument("--mock", action="store_true")
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rows=[]
    if a.mock:
        print("[mock] fabricated KGSS — pipeline check only, NOT a result.")
        rng=np.random.default_rng(1); n=900
        base=rng.normal(0,1,n); df=pd.DataFrame({
            "AUTHORT2":np.clip(np.round(3+0.4*base+rng.normal(0,1,n)),1,5),
            "AUTHORT4":np.clip(np.round(3+0.4*base+rng.normal(0,1,n)),1,5),
            "AUTHORT5":np.clip(np.round(3+0.4*base+rng.normal(0,1,n)),1,5),
            "SICK1":np.clip(np.round(3+rng.normal(0,1,n)),1,5),"BORROW1":np.clip(np.round(3+rng.normal(0,1,n)),1,5),
            "DOWN1":np.clip(np.round(3+rng.normal(0,1,n)),1,5),
            "SEX":rng.integers(1,3,n),"AGE":rng.integers(40,85,n),"FINALWT":rng.uniform(.5,2,n)})
        global AD_ITEMS,SI_ITEMS; AD_ITEMS=["AUTHORT2","AUTHORT4","AUTHORT5"]
    else:
        if not a.kgss: raise SystemExit("[fatal] --kgss path required (or --mock)")
        df=pd.read_csv(a.kgss)
    for attr,items in (("authority_deference",AD_ITEMS),("social_isolation",SI_ITEMS)):
        if attr=="social_isolation" and all(c in df.columns for c in ["SICK1","BORROW1","DOWN1","NGHASK"]):
            V,(lo,hi),nn=structural_si_level(df.copy())
        else:
            V,(lo,hi),nn=source_V(df.copy(), items, attr)
        syn=synth_residual(attr)
        rows.append({"attr":attr,"synthetic_residual_V":round(syn,3) if syn==syn else syn,
                     "source_survey_V":round(V,3) if V==V else V,
                     "source_CI95":f"[{lo:.3f},{hi:.3f}]" if lo==lo else "n/a","n":nn,
                     "verdict":verdict(syn,lo,hi)})
    cmp=pd.DataFrame(rows); cmp.to_csv(out/"residual_magnitude_match.csv", index=False, encoding="utf-8-sig")
    with open(out/"residual_magnitude_match.txt","w",encoding="utf-8") as fh:
        fh.write("Residual magnitude match — synthetic vs source-survey Cramér's V (reviewer M2)\n"+"="*70+"\n")
        fh.write(cmp.to_string(index=False)+"\n\n")
        fh.write("READY §4.3 SENTENCE (fill from row):\n")
        for r in rows:
            fh.write(f"  {r['attr']}×sex: synthetic V {r['synthetic_residual_V']} vs source survey V "
                     f"{r['source_survey_V']} {r['source_CI95']} -> {r['verdict']}.\n")
    print(cmp.to_string(index=False)); print("\n[ok] results/residual_magnitude_match.{csv,txt}")

if __name__=="__main__": main()
