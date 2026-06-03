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
    s=np.concatenate(src); d=np.concatenate(dst); deg=np.bincount(d,minlength=len(adj)).astype(float); deg[deg==0]=np.nan
    return s,d,deg
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
def build_net(topo,iso,seed): return _cut(base_adj(topo,len(iso),seed),iso,seed)
def order_idx(df): return np.argsort(df["age_band"].map(AGE_RANK).to_numpy(),kind="stable")
def diffuse(net,dl,si,ad,fv,thr_base,steps,seed):
    src,dst,deg=net; n=len(dl); rng=np.random.default_rng(seed+13)
    pb=np.array([0.0,0.0,0.015,0.08,0.18])[dl-1]; thr=np.clip(thr_base-0.05*(ad-3)-0.03*(fv-3),0.2,0.95)
    adopted=np.zeros(n,bool)
    for _ in range(steps):
        new=(~adopted)&(rng.random(n)<pb); cnt=np.bincount(dst[adopted[src]],minlength=n).astype(float)
        frac=np.divide(cnt,deg,out=np.zeros(n),where=~np.isnan(deg)); new|=(~adopted)&(frac>=thr); adopted|=new
    return adopted
def induce(b,seed,rho,eld):
    s=b.copy(); rng=np.random.default_rng(seed+881); ei=np.where(eld)[0]; ne=ei.size; z=rng.standard_normal(ne)
    def ro(col,sign):
        vals=np.sort(s[col].to_numpy()[ei]); score=rho*z+np.sqrt(max(1-rho*rho,0))*rng.standard_normal(ne)
        rank=np.argsort(np.argsort(sign*score)); v=s[col].to_numpy().copy(); v[ei]=vals[rank]; s[col]=v
    ro("attr_financial_vulnerability",1); ro("attr_digital_literacy",-1); ro("attr_social_isolation",1); return s
def mult(s,eld):
    e=s.loc[eld]; fv=(e.attr_financial_vulnerability>=4); dl=(e.attr_digital_literacy<=2); si=(e.attr_social_isolation>=4)
    ext=(fv&dl&si).mean(); ind=fv.mean()*dl.mean()*si.mean(); return ext/ind if ind>0 else np.nan
def calib(base,target,eld):
    lo,hi=0.0,0.99
    for _ in range(24):
        mid=(lo+hi)/2
        if mult(induce(base,42,mid,eld),eld)<target: lo=mid
        else: hi=mid
    return (lo+hi)/2
def run(pop,topo,thr,steps,seed):
    o=order_idx(pop); d=pop.iloc[o].reset_index(drop=True)
    dl=d.attr_digital_literacy.to_numpy(); si=d.attr_social_isolation.to_numpy()
    ad=d.attr_authority_deference.to_numpy(); fv=d.attr_financial_vulnerability.to_numpy()
    eld=d["_eld"].to_numpy()
    net=build_net(topo,si,seed); adopt=diffuse(net,dl,si,ad,fv,thr,steps,seed)
    overall=adopt.mean()
    # outcome 1: triply-vulnerable cohort (defined on THIS pop)
    coh=eld&(dl<=2)&(si>=4)&(fv>=4); cn=int(coh.sum())
    cr=adopt[coh].mean() if cn>0 else np.nan
    # outcome 2: doubly channel-blocked elderly (low DL AND high SI): no broadcast AND few ties
    db=eld&(dl<=2)&(si>=4); dbn=int(db.sum())
    dbr=adopt[db].mean() if dbn>0 else np.nan
    # outcome 3: left-behind = unreached elderly count (per 1000 agents, size-normalized)
    lb=float((eld&~adopt).sum())/len(adopt)*1000
    return dict(overall=overall*100, coh_n=cn, coh_reach=(cr*100 if cn>0 else np.nan),
                db_n=dbn, db_reach=(dbr*100 if dbn>0 else np.nan), leftbehind_per1k=lb)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--n",type=int,default=6000); ap.add_argument("--steps",type=int,default=25)
    ap.add_argument("--seeds",type=int,default=30); ap.add_argument("--out",default="/tmp/disc_out")
    ap.add_argument("--thr",default="0.55,0.65"); ap.add_argument("--topo",default="smallworld")
    ap.add_argument("--targets",default="1.0,1.29,2.30"); a=ap.parse_args()
    thrs=[float(x) for x in a.thr.split(",")]; targets=[float(x) for x in a.targets.split(",")]
    base=load_sample(a.n,42); eld=base["_eld"].to_numpy()
    rhos={t:(0.0 if t<=1.001 else calib(base,t,eld)) for t in targets}
    achieved={t:round(mult(induce(base,42,rhos[t],eld),eld),3) for t in targets}
    ci=lambda x:1.96*np.nanstd(x,ddof=1)/np.sqrt(max(np.sum(~np.isnan(x)),1))
    rows=[]
    for t in targets:
        for thr in thrs:
            R=[run(induce(base,sd,rhos[t],eld),a.topo,thr,a.steps,sd) for sd in range(1,a.seeds+1)]
            g=lambda k:np.array([r[k] for r in R],dtype=float)
            ov=g("overall"); cr=g("coh_reach"); dbr=g("db_reach")
            dbgap=ov-dbr   # overall minus doubly-blocked reach = equity gap
            rows.append(dict(target_mult=t,achieved_mult=achieved[t],threshold=thr,
                overall_reach=round(np.mean(ov),2),overall_CI=round(ci(ov),2),
                coh_n=round(np.mean(g("coh_n")),1), coh_reach=round(np.nanmean(cr),2),
                db_n=round(np.mean(g("db_n")),1), db_reach=round(np.nanmean(dbr),2),db_reach_CI=round(ci(dbr),2),
                db_gap_pp=round(np.nanmean(dbgap),2),db_gap_CI=round(ci(dbgap),2),
                leftbehind_per1k=round(np.mean(g("leftbehind_per1k")),2),lb_CI=round(ci(g("leftbehind_per1k")),2)))
    df=pd.DataFrame(rows); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    df.to_csv(out/"abm_discriminate.csv",index=False)
    (out/"abm_discriminate.txt").write_text(
        "KVRB diffusion: does the inter-attribute JOINT discriminate by OUTCOME? (n=%d, %s, %d seeds, 95%% CI)\n"%(a.n,a.topo,a.seeds)+
        "Elderly joint swept independence->observed, marginals fixed. achieved_mult = realized P(all3 extreme)/independence.\n"+
        "overall_reach: aggregate adoption %% ; protection_gap_pp = overall - compound-cohort reach.\n\n"+df.to_string(index=False)+"\n")
    print(df.to_string(index=False)); print("\nachieved multipliers:",json.dumps(achieved))
main()
