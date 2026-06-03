"""Second ABM: Hegselmann-Krause bounded-confidence opinion dynamics on KVRB.
Same 4-population decomposition as the diffusion model (real / within-cell /
full-shuffle / block) to test whether 'demographic coupling drives the outcome,
inter-attribute joint barely moves it' replicates under a fundamentally
different mechanism (continuous opinion updating vs binary adoption).
Agent params from attributes: initial opinion x0 raised by authority deference
and financial vulnerability; confidence bound eps widened by digital literacy,
narrowed by authority deference; social isolation thins ties (fewer interlocutors).
Outcomes: non-consensus fraction (1 - largest final cluster) = aggregate
fragmentation; compound-cohort stranding = share of elderly low-DL high-SI agents
outside the largest cluster. numpy only, fixed seeds."""
import argparse, glob, sys, json
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.parquet as pq
ATTRS=["attr_digital_literacy","attr_social_isolation","attr_authority_deference","attr_financial_vulnerability"]
AGE_RANK={"19-29":0,"30-44":1,"45-59":2,"60-74":3,"75+":4}
def load_sample(n,seed):
    parts=sorted(glob.glob("data/processed/enriched_1M_v4_parts/*.parquet"))
    df=pq.read_table(parts[0],columns=["age_band","sex","education_tier"]+ATTRS).to_pandas()
    idx=np.random.default_rng(seed).choice(len(df),size=min(n,len(df)),replace=False)
    s=df.iloc[idx].reset_index(drop=True)
    for c in ATTRS: s[c]=s[c].astype(int)
    s["_cell"]=s["age_band"].astype(str)+"|"+s["sex"].astype(str)+"|"+s["education_tier"].astype(str)
    s["_eld"]=s["age_band"].isin(["60-74","75+"]).to_numpy()
    return s
def _cut(adj,iso,seed):
    rng=np.random.default_rng(seed+23); keep={1:1.0,2:0.85,3:0.7,4:0.5,5:0.3}; src=[];dst=[]
    for i in range(len(adj)):
        nb=np.fromiter(adj[i],dtype=np.int64); f=keep.get(int(iso[i]),0.7)
        if nb.size and f<1.0:
            mk=max(1,int(round(nb.size*f)))
            if mk<nb.size: nb=rng.choice(nb,size=mk,replace=False)
        if nb.size: src.append(np.full(nb.size,i)); dst.append(nb)
    return np.concatenate(src),np.concatenate(dst)
CA={}
def base_adj(topo,n,seed,k=8,m=4):
    key=(topo,n,seed)
    if key in CA: return CA[key]
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
        rng=np.random.default_rng(seed+11); adj=[set() for _ in range(n)]; rep=list(range(m)); targets=list(range(m))
        for i in range(m,n):
            for t in set(targets): adj[i].add(t); adj[t].add(i)
            rep.extend(targets); rep.extend([i]*m); ridx=rng.integers(0,len(rep),size=m); targets=[rep[j] for j in ridx]
    CA[key]=adj; return adj
def order_idx(df): return np.argsort(df["age_band"].map(AGE_RANK).to_numpy(),kind="stable")
def prep(df,topo,seed):
    o=order_idx(df); d=df.iloc[o].reset_index(drop=True)
    si=d.attr_social_isolation.to_numpy()
    src,dst=_cut(base_adj(topo,len(si),seed),si,seed)
    return d,src,dst
def hk_run(d,src,dst,eps_base,steps,seed):
    dl=d.attr_digital_literacy.to_numpy(); si=d.attr_social_isolation.to_numpy()
    ad=d.attr_authority_deference.to_numpy(); fv=d.attr_financial_vulnerability.to_numpy()
    eld=d["_eld"].to_numpy(); n=len(dl); rng=np.random.default_rng(seed+13)
    x=np.clip(0.5+0.10*(ad-3)+0.05*(fv-3)+0.05*rng.standard_normal(n),0,1)   # initial opinion
    eps=np.clip(eps_base+0.04*(dl-3)-0.03*(ad-3),0.04,0.6)                    # confidence bound
    for _ in range(steps):
        diff=np.abs(x[src]-x[dst]); mask=diff<eps[src]
        ssum=np.bincount(src[mask],weights=x[dst][mask],minlength=n)
        scnt=np.bincount(src[mask],minlength=n).astype(float)
        x=(ssum+x)/(scnt+1.0)                                                # include self
    # cluster: bin to 0.02, largest cluster mass
    b=np.round(x/0.02).astype(int); vals,cnts=np.unique(b,return_counts=True)
    big=vals[np.argmax(cnts)]; inbig=np.abs(b-big)<=2                        # within 0.04 of mode = majority cluster
    noncons=1.0-inbig.mean()
    cohort=eld&(dl<=2)&(si>=4)
    stranded=(~inbig)[cohort].mean() if cohort.sum()>0 else np.nan
    return noncons*100, (stranded*100 if cohort.sum()>0 else np.nan)
# conditions
def c_real(b,s): return b.copy()
def c_shuffle(b,seed):
    s=b.copy(); rg=np.random.default_rng(seed+99)
    for c in ATTRS: s[c]=rg.permutation(s[c].to_numpy())
    return s
def c_within(b,seed):
    s=b.copy(); rg=np.random.default_rng(seed+311); g=s.groupby("_cell").indices
    for c in ATTRS:
        v=s[c].to_numpy().copy()
        for _,gi in g.items():
            if gi.size>1: v[gi]=rg.permutation(v[gi])
        s[c]=v
    return s
def c_block(b,seed):
    s=b.copy(); rg=np.random.default_rng(seed+733); p=rg.permutation(len(s))
    for c in ATTRS: s[c]=s[c].to_numpy()[p]
    return s
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--n",type=int,default=3000); ap.add_argument("--steps",type=int,default=20)
    ap.add_argument("--seeds",type=int,default=30); ap.add_argument("--out",default="/tmp/op_out")
    ap.add_argument("--eps",default="0.10,0.16"); ap.add_argument("--topo",default="smallworld"); a=ap.parse_args()
    epss=[float(x) for x in a.eps.split(",")]; base=load_sample(a.n,42)
    bld={"real":c_real,"within_cell":c_within,"shuffle_full":c_shuffle,"block":c_block}
    DEC=["real","within_cell","shuffle_full","block"]
    nc={c:{} for c in DEC}; st={c:{} for c in DEC}
    for sd in range(1,a.seeds+1):
        for c in DEC:
            d,src,dst=prep(bld[c](base,sd),a.topo,sd)
            for e in epss:
                v,stv=hk_run(d,src,dst,e,a.steps,sd)
                nc[c].setdefault(e,[]).append(v); st[c].setdefault(e,[]).append(stv)
        sys.stdout.write("."); sys.stdout.flush()
    ci=lambda x:1.96*np.nanstd(x,ddof=1)/np.sqrt(max(np.sum(~np.isnan(x)),1)); rows=[]
    for e in epss:
        R={c:np.array(nc[c][e]) for c in DEC}
        j=R["within_cell"]-R["real"]; cp=R["shuffle_full"]-R["within_cell"]; fl=R["shuffle_full"]-R["real"]; bk=R["block"]-R["real"]
        rows.append(dict(topology=a.topo,eps=e,noncons_real=round(R["real"].mean(),2),
            joint_pp=round(j.mean(),2),joint_CI=round(ci(j),2),coupling_pp=round(cp.mean(),2),coupling_CI=round(ci(cp),2),
            full_pp=round(fl.mean(),2),full_CI=round(ci(fl),2),blockVSreal_pp=round(bk.mean(),2),
            cohort_strand_real=round(np.nanmean(st["real"][e]),1),cohort_strand_shuf=round(np.nanmean(st["shuffle_full"][e]),1)))
    df=pd.DataFrame(rows); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    df.to_csv(out/("opinion_%s.csv"%a.topo),index=False); print(df.to_string(index=False))
main()
