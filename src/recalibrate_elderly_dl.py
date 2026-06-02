# -*- coding: utf-8 -*-
"""Elderly DL recalibration (reviewer A1), anchor-faithful + vectorized.
Re-derives the elderly DL bands (60-74,75+) of config/anchors/digital_literacy.csv from
노인실태조사 2023 (activity instrument, P(level|age_band x education_tier)), rewrites the anchor,
and RE-SAMPLES v4 DL for those bands from the new anchor (cell-vectorized, deterministic seed)."""
import glob, os, hashlib
import numpy as np, pandas as pd
CSV="data/raw/노인실태조사_2023/2023_총괄_20260601_13406.csv"
AGE="노인 조사대상자 만연령"; W="가중치 모수추정(사후층화 가중치)"; EDU="노인 조사대상자 교육수준"
ANCHOR="config/anchors/digital_literacy.csv"; ELDER=["60-74","75+"]
def band(a): return "60-74" if a<75 else "75+"
def tier(e): return "lower" if e<=5 else "higher"

def noin_anchor():
    df=pd.read_csv(CSV,encoding="cp949",dtype=str); n=lambda c: pd.to_numeric(df[c],errors="coerce")
    dlc=sum((n(c)==1).astype(int) for c in [c for c in df.columns if c.startswith("전자기기 활동여부_")])
    R=pd.DataFrame({"age":n(AGE),"w":n(W),"edu":n(EDU),
        "lvl":pd.cut(dlc,[-1,0,2,5,9,13],labels=[1,2,3,4,5]).astype("float")})
    R=R[(R.age>=65)&R.lvl.notna()&R.w.notna()&(R.w>0)&R.edu.notna()].copy()
    R["age_band"]=R.age.apply(band); R["education_tier"]=R.edu.apply(tier)
    rows=[]
    for (bd,tr),g in R.groupby(["age_band","education_tier"]):
        p=g.groupby("lvl")["w"].sum(); p=(p/p.sum()).reindex([1,2,3,4,5],fill_value=0.0)
        for lv in [1,2,3,4,5]: rows.append({"age_band":bd,"education_tier":tr,"level":lv,"prob":round(float(p[lv]),4)})
    return pd.DataFrame(rows)

ne=noin_anchor()
print("[anchor] new elderly rows:\n"+ne.to_string(index=False))
a=pd.read_csv(ANCHOR); keep=a[~a.age_band.isin(ELDER)]
out=pd.concat([keep,ne],ignore_index=True)
o={"19-29":0,"30-44":1,"45-59":2,"60-74":3,"75+":4}; t={"lower":0,"higher":1}
out=out.assign(_a=out.age_band.map(o),_t=out.education_tier.map(t)).sort_values(["_a","_t","level"]).drop(columns=["_a","_t"])
out.to_csv(ANCHOR,index=False)
cell={(r.age_band,r.education_tier):(np.array([1,2,3,4,5]),None) for _,r in ne.iterrows()}
for (bd,tr),g in ne.groupby(["age_band","education_tier"]):
    cell[(bd,tr)]=(g.level.values.astype(int), (g.prob.values/g.prob.values.sum()))

src=sorted(glob.glob("data/processed/enriched_1M_v3_parts/*.parquet")); outdir="data/processed/enriched_1M_v4_parts"
os.makedirs(outdir,exist_ok=True); eld_lo=eld_n=0
for pi,p in enumerate(src):
    d=pd.read_parquet(p); ab=d.age_band.astype(str).values; et=d.education_tier.astype(str).values
    dl=d.attr_digital_literacy.astype(int).values.copy()
    for (bd,tr),(lv,pr) in cell.items():
        mask=(ab==bd)&(et==tr); k=int(mask.sum())
        if k==0: continue
        rng=np.random.default_rng(int(hashlib.md5(f"{pi}|{bd}|{tr}".encode()).hexdigest()[:8],16))
        dl[mask]=rng.choice(lv,size=k,p=pr)
    d["attr_digital_literacy"]=dl; d.to_parquet(os.path.join(outdir,os.path.basename(p)),index=False)
    age=pd.to_numeric(d.age,errors="coerce").values; e=age>=65
    eld_lo+=int((dl[e]<=2).sum()); eld_n+=int(e.sum())
msg=f"[v4] elderly(65+) DL low(<=2) = {eld_lo/eld_n:.3f} (n={eld_n}); real target 0.365"
open("results/elderly_dl_recalibration.txt","w",encoding="utf-8").write(
 "Elderly DL recalibration: anchor bands 60-74/75+ rebuilt from 노인실태조사 2023 "
 "(65-74->60-74 proxy, 75+) x education_tier; v4 DL resampled from new anchor.\n"+msg+"\n")
print(msg)
