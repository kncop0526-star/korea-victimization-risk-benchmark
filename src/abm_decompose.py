"""abm_decompose.py - identify whether the inter-attribute joint or the
demographic coupling drives the KVRB diffusion reach gap (reviewer C1), and
bound the conditional-independence assumption by sweeping the elderly
inter-attribute dependence (independence / released / observed) with marginals
held fixed (M1). numpy/pandas only, fixed seeds, reproducible."""
from __future__ import annotations
import argparse, glob, sys, json
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.parquet as pq

ATTRS=["attr_digital_literacy","attr_social_isolation","attr_authority_deference","attr_financial_vulnerability"]
AGE_RANK={"19-29":0,"30-44":1,"45-59":2,"60-74":3,"75+":4}

def load_sample(n,seed):
    parts=sorted(glob.glob("data/processed/enriched_1M_v4_parts/*.parquet"))
    cols=["age_band","sex","education_tier"]+ATTRS
    df=pq.read_table(parts[0],columns=cols).to_pandas()
    idx=np.random.default_rng(seed).choice(len(df),size=min(n,len(df)),replace=False)
    s=df.iloc[idx].reset_index(drop=True)
    for c in ATTRS: s[c]=s[c].astype(int)
    s["_cell"]=s["age_band"].astype(str)+"|"+s["sex"].astype(str)+"|"+s["education_tier"].astype(str)
    s["_eld"]=s["age_band"].isin(["60-74","75+"]).to_numpy()
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

_ADJ_CACHE={}
def build_base_adj(topo,n,seed,k=8,m=4):
    key=(topo,n,seed)
    if key in _ADJ_CACHE: return _ADJ_CACHE[key]
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
    _ADJ_CACHE[key]=adj; return adj

def build_net(topo,iso,seed,k=8,m=4):
    return _cut_flatten(build_base_adj(topo,len(iso),seed,k,m),iso,seed)

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

def cond_real(base,seed): return base.copy()

def cond_shuffle_full(base,seed):
    s=base.copy(); rg=np.random.default_rng(seed+99)
    for c in ATTRS: s[c]=rg.permutation(s[c].to_numpy())
    return s

def cond_within_cell(base,seed):
    s=base.copy(); rg=np.random.default_rng(seed+311)
    groups=s.groupby("_cell").indices
    for c in ATTRS:
        v=s[c].to_numpy().copy()
        for _,gi in groups.items():
            if gi.size>1: v[gi]=rg.permutation(v[gi])
        s[c]=v
    return s

def cond_block(base,seed):
    s=base.copy(); rg=np.random.default_rng(seed+733)
    perm=rg.permutation(len(s))
    for c in ATTRS: s[c]=s[c].to_numpy()[perm]
    return s

def cond_eld_indep(base,seed):
    s=base.copy(); rg=np.random.default_rng(seed+517); ei=np.where(s["_eld"].to_numpy())[0]
    for c in ATTRS:
        v=s[c].to_numpy().copy(); v[ei]=rg.permutation(v[ei]); s[c]=v
    return s

def induce_factor(base_frame,seed,rho,eld):
    s=base_frame.copy(); rng=np.random.default_rng(seed+881); ei=np.where(eld)[0]; ne=ei.size
    z=rng.standard_normal(ne)
    def reorder(col,sign):
        vals=np.sort(s[col].to_numpy()[ei])
        score=rho*z+np.sqrt(max(1-rho*rho,0))*rng.standard_normal(ne)
        rank=np.argsort(np.argsort(sign*score))
        v=s[col].to_numpy().copy(); v[ei]=vals[rank]; s[col]=v
    reorder("attr_financial_vulnerability",+1)
    reorder("attr_digital_literacy",-1)
    reorder("attr_social_isolation",+1)
    return s

def mult_eld(s,eld):
    e=s.loc[eld]
    fvhi=(e["attr_financial_vulnerability"]>=4); dllo=(e["attr_digital_literacy"]<=2); sihi=(e["attr_social_isolation"]>=4)
    ext=(fvhi&dllo&sihi).mean(); indep=fvhi.mean()*dllo.mean()*sihi.mean()
    return ext/indep if indep>0 else np.nan

def calibrate_rho(base,target,seed=42):
    eld=base["_eld"].to_numpy(); lo,hi=0.0,0.99
    for _ in range(22):
        mid=(lo+hi)/2
        if mult_eld(induce_factor(base,seed,mid,eld),eld)<target: lo=mid
        else: hi=mid
    return (lo+hi)/2

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--n",type=int,default=3000); ap.add_argument("--steps",type=int,default=25)
    ap.add_argument("--seeds",type=int,default=30); ap.add_argument("--out",default="results_v4")
    ap.add_argument("--thr",default="0.45,0.55,0.65"); ap.add_argument("--topos",default="smallworld,scalefree")
    ap.add_argument("--target",type=float,default=2.30)
    a=ap.parse_args()
    thrs=[float(x) for x in a.thr.split(",")]; topos=a.topos.split(",")
    base=load_sample(a.n,42); eld=base["_eld"].to_numpy()
    cohort=(base["_eld"]&(base["attr_digital_literacy"]<=2)&(base["attr_social_isolation"]>=4)).to_numpy()
    rho=calibrate_rho(base,a.target)
    mults={"real":round(mult_eld(base,eld),3),
           "within_cell":round(mult_eld(cond_within_cell(base,1),eld),3),
           "eld_indep":round(mult_eld(cond_eld_indep(base,1),eld),3),
           "eld_inject":round(mult_eld(induce_factor(base,42,rho,eld),eld),3),
           "rho":round(rho,3),"target":a.target}
    DECOMP=["real","within_cell","shuffle_full","block"]; SWEEP=["eld_indep","eld_inject"]
    builders={"real":cond_real,"within_cell":cond_within_cell,"shuffle_full":cond_shuffle_full,
              "block":cond_block,"eld_indep":cond_eld_indep,
              "eld_inject":lambda b,sd:induce_factor(b,sd,rho,eld)}
    allconds=list(dict.fromkeys(DECOMP+SWEEP))
    reach={c:{} for c in allconds}; cratio={c:{} for c in allconds}
    for topo in topos:
        for sd in range(1,a.seeds+1):
            for c in allconds:
                o,attr=order_attrs(builders[c](base,sd)); net=build_net(topo,attr[1],sd)
                for thr in thrs:
                    ad=diffuse(net,attr,thr,a.steps,sd,o)
                    reach[c].setdefault((topo,thr),[]).append(ad.mean()*100)
                    cratio[c].setdefault((topo,thr),[]).append(ad[cohort].mean()/ad[~cohort].mean())
            sys.stdout.write("."); sys.stdout.flush()
    ci=lambda x:1.96*np.std(x,ddof=1)/np.sqrt(len(x))
    drows=[]
    for topo in topos:
        for thr in thrs:
            R={c:np.array(reach[c][(topo,thr)]) for c in DECOMP}
            joint=R["within_cell"]-R["real"]; coup=R["shuffle_full"]-R["within_cell"]
            full=R["shuffle_full"]-R["real"]; blk=R["block"]-R["real"]
            cr_real=np.array(cratio["real"][(topo,thr)])
            drows.append(dict(topology=topo,threshold=thr,reach_real=round(R["real"].mean(),2),
                joint_pp=round(joint.mean(),2),joint_CI=round(ci(joint),2),
                coupling_pp=round(coup.mean(),2),coupling_CI=round(ci(coup),2),
                full_pp=round(full.mean(),2),full_CI=round(ci(full),2),
                blockVSreal_pp=round(blk.mean(),2),cohort_real=round(cr_real.mean(),3)))
    ddf=pd.DataFrame(drows)
    srows=[]
    for topo in topos:
        for thr in thrs:
            row=dict(topology=topo,threshold=thr)
            for c in SWEEP:
                rc=np.array(reach[c][(topo,thr)])
                row[f"reach_{c}"]=round(rc.mean(),2); row[f"reach_{c}_CI"]=round(ci(rc),2)
            row["inject_minus_indep_pp"]=round(np.array(reach["eld_inject"][(topo,thr)]).mean()-np.array(reach["eld_indep"][(topo,thr)]).mean(),2)
            srows.append(row)
    sdf=pd.DataFrame(srows)
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    ddf.to_csv(out/"abm_decompose.csv",index=False); sdf.to_csv(out/"abm_sweep.csv",index=False)
    lines=[f"KVRB diffusion DECOMPOSITION (n={a.n}, {a.seeds} seeds/cell, 95% CI)",
        "joint_pp = within_cell - real (inter-attribute joint BEYOND demographic coupling)",
        "coupling_pp = shuffle_full - within_cell (demographic coupling of attributes)",
        "full_pp = shuffle_full - real ; blockVSreal_pp = block - real (joint preserved, coupling destroyed)","",
        ddf.to_string(index=False),"",
        f"Elderly dependence multipliers: {json.dumps(mults)}","",
        "ELDERLY JOINT-STRENGTH SWEEP (marginals fixed; only dependence varies; inject vs indep)",
        sdf.to_string(index=False)]
    (out/"abm_decompose.txt").write_text("\n".join(lines)+"\n")
    print("\n"+ddf.to_string(index=False)); print("\nmults:",json.dumps(mults)); print("\n"+sdf.to_string(index=False))

if __name__=="__main__": main()
