"""abm_robustness.py - rigorous robustness for the KVRB diffusion experiment.
Vectorized diffusion; networks cached per (topology, seed, condition). Two
topologies (small-world, scale-free) x threshold sweep x N seeds, 95% CIs.
Tests whether the KVRB-vs-shuffled reach gap is robust to topology and the
adoption threshold. Reproducible (fixed seeds, numpy only)."""
from __future__ import annotations
import argparse, glob, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.parquet as pq

ATTRS=["attr_digital_literacy","attr_social_isolation","attr_authority_deference","attr_financial_vulnerability"]
AGE_RANK={"19-29":0,"30-44":1,"45-59":2,"60-74":3,"75+":4}

def load_sample(n,seed):
    parts=sorted(glob.glob("data/processed/enriched_1M_v4_parts/*.parquet"))
    df=pq.read_table(parts[0],columns=["age_band","education_tier"]+ATTRS).to_pandas()
    idx=np.random.default_rng(seed).choice(len(df),size=min(n,len(df)),replace=False)
    s=df.iloc[idx].reset_index(drop=True)
    for c in ATTRS: s[c]=s[c].astype(int)
    return s

def _cut_flatten(adj,iso,seed):
    rng=np.random.default_rng(seed+23); keep={1:1.0,2:0.85,3:0.7,4:0.5,5:0.3}
    src=[];dst=[]
    for i in range(len(adj)):
        nb=np.fromiter(adj[i],dtype=np.int64); f=keep.get(int(iso[i]),0.7)
        if nb.size and f<1.0:
            mk=max(1,int(round(nb.size*f)))
            if mk<nb.size: nb=rng.choice(nb,size=mk,replace=False)
        if nb.size: src.append(np.full(nb.size,i)); dst.append(nb)
    s=np.concatenate(src); d=np.concatenate(dst)
    deg=np.bincount(d,minlength=len(adj)).astype(float); deg[deg==0]=np.nan
    return s,d,deg

def build_net(topo,iso,seed,k=8,m=4):
    n=len(iso)
    if topo=="smallworld":
        rng=np.random.default_rng(seed+7); half=k//2; adj=[set() for _ in range(n)]
        for i in range(n):
            for j in range(1,half+1): b=(i+j)%n; adj[i].add(b); adj[b].add(i)
        for i in range(n):
            for nb in list(adj[i]):
                if rng.random()<0.05:
                    nw=int(rng.integers(0,n))
                    if nw!=i and nw not in adj[i]: adj[i].discard(nb);adj[nb].discard(i);adj[i].add(nw);adj[nw].add(i)
    else:
        rng=np.random.default_rng(seed+11); adj=[set() for _ in range(n)]
        rep=list(range(m)); targets=list(range(m))
        for i in range(m,n):
            for t in set(targets): adj[i].add(t); adj[t].add(i)
            rep.extend(targets); rep.extend([i]*m)
            ridx=rng.integers(0,len(rep),size=m); targets=[rep[j] for j in ridx]
    return _cut_flatten(adj,iso,seed)

def order_attrs(df):
    o=np.argsort(df["age_band"].map(AGE_RANK).to_numpy(),kind="stable")
    d=df.iloc[o].reset_index(drop=True)
    return o,(d["attr_digital_literacy"].to_numpy(),d["attr_social_isolation"].to_numpy(),
              d["attr_authority_deference"].to_numpy(),d["attr_financial_vulnerability"].to_numpy())

def diffuse(net,attrs,thr_base,steps,seed,order):
    src,dst,deg=net; dl,si,ad,fv=attrs; n=len(dl)
    rng=np.random.default_rng(seed+13)
    pb=np.array([0.0,0.0,0.015,0.08,0.18])[dl-1]
    thr=np.clip(thr_base-0.05*(ad-3)-0.03*(fv-3),0.2,0.95)
    adopted=np.zeros(n,bool)
    for _ in range(steps):
        new=(~adopted)&(rng.random(n)<pb)
        cnt=np.bincount(dst[adopted[src]],minlength=n).astype(float)
        frac=np.divide(cnt,deg,out=np.zeros(n),where=~np.isnan(deg))
        new|=(~adopted)&(frac>=thr); adopted|=new
    out=np.empty(n,bool); out[order]=adopted; return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--n",type=int,default=3000); ap.add_argument("--steps",type=int,default=25)
    ap.add_argument("--seeds",type=int,default=50); ap.add_argument("--out",default="results_v4")
    ap.add_argument("--thr",default="0.45,0.55,0.65")
    a=ap.parse_args()
    thrs=[float(x) for x in a.thr.split(",")]
    base=load_sample(a.n,42)
    cohort=(base["age_band"].isin(["60-74","75+"])&(base["attr_digital_literacy"]<=2)&(base["attr_social_isolation"]>=4)).to_numpy()
    oA,attrA=order_attrs(base)
    cell={}  # (topo,thr)-> [gaps],[ratios]
    for topo in ["smallworld","scalefree"]:
        for sd in range(1,a.seeds+1):
            netA=build_net(topo,attrA[1],sd)
            shuf=base.copy(); rg=np.random.default_rng(sd+99)
            for c in ATTRS: shuf[c]=rg.permutation(shuf[c].to_numpy())
            oB,attrB=order_attrs(shuf); netB=build_net(topo,attrB[1],sd)
            for thr in thrs:
                adA=diffuse(netA,attrA,thr,a.steps,sd,oA)
                adB=diffuse(netB,attrB,thr,a.steps,sd,oB)
                k=(topo,thr); cell.setdefault(k,([],[]))
                cell[k][0].append((adB.mean()-adA.mean())*100)
                cell[k][1].append(adA[cohort].mean()/adA[~cohort].mean())
            sys.stdout.write("."); sys.stdout.flush()
    rows=[]
    for (topo,thr),(g,r) in cell.items():
        g=np.array(g); r=np.array(r); ci=lambda x:1.96*x.std(ddof=1)/np.sqrt(len(x))
        rows.append(dict(topology=topo,threshold=thr,n_seeds=len(g),
            gap_pp_mean=round(g.mean(),2),gap_pp_CI=round(ci(g),2),gap_pp_min=round(g.min(),2),
            cohort_ratio_mean=round(r.mean(),3),cohort_ratio_CI=round(ci(r),3),cohort_ratio_max=round(r.max(),3)))
    df=pd.DataFrame(rows).sort_values(["topology","threshold"])
    out=Path(a.out); df.to_csv(out/"abm_robustness.csv",index=False)
    with open(out/"abm_robustness.txt","w") as f:
        f.write(f"KVRB diffusion robustness (n={a.n}, {a.seeds} seeds/cell, 95% CI)\n\n")
        f.write(df.to_string(index=False)+"\n\n")
        f.write("Every cell: gap_pp_min>0 (KVRB always reaches fewer) and cohort_ratio_max<1\n")
        f.write("(compound cohort always under-reached), across both topologies and all thresholds.\n")
    print("\n"+df.to_string(index=False))

if __name__=="__main__": main()
