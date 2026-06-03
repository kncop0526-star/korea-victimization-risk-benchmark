# M-1: rerun the discrimination (never-reached elderly vs elderly inter-attribute dependence)
# with the elderly social-isolation marginal DEFLATED from ~0.30 to the validation-survey ~0.14,
# to show the -46%/-24% distributional drops are not an artifact of the inflated isolation marginal.
import glob,sys,numpy as np,pandas as pd,pyarrow.parquet as pq
ATTRS=["attr_digital_literacy","attr_social_isolation","attr_authority_deference","attr_financial_vulnerability"]
AGE_RANK={"19-29":0,"30-44":1,"45-59":2,"60-74":3,"75+":4}
def load(n,seed=42):
    p=sorted(glob.glob("data/processed/enriched_1M_v4_parts/*.parquet"))
    df=pq.read_table(p[0],columns=["age_band","sex","education_tier"]+ATTRS).to_pandas()
    idx=np.random.default_rng(seed).choice(len(df),size=min(n,len(df)),replace=False)
    s=df.iloc[idx].reset_index(drop=True)
    for c in ATTRS: s[c]=s[c].astype(int)
    s["_eld"]=s.age_band.isin(["60-74","75+"]).to_numpy(); return s
def deflate_si(base,target=0.14,seed=42):
    s=base.copy(); eld=s["_eld"].to_numpy(); rng=np.random.default_rng(seed+5)
    hi=eld&(s.attr_social_isolation.to_numpy()>=4); idx=np.where(hi)[0]
    cur=hi.sum()/eld.sum(); demote_frac=max(0,1-target/cur)
    dem=rng.choice(idx,size=int(round(len(idx)*demote_frac)),replace=False)
    v=s.attr_social_isolation.to_numpy().copy(); v[dem]=3; s["attr_social_isolation"]=v
    return s,(eld&(v>=4)).sum()/eld.sum()
CA={}
def base_adj(n,seed,k=8):
    if (n,seed) in CA: return CA[(n,seed)]
    rng=np.random.default_rng(seed+7); half=k//2; adj=[set() for _ in range(n)]
    for i in range(n):
        for j in range(1,half+1): b=(i+j)%n; adj[i].add(b); adj[b].add(i)
    for i in range(n):
        for nb in list(adj[i]):
            if rng.random()<0.05:
                nw=int(rng.integers(0,n))
                if nw!=i and nw not in adj[i]: adj[i].discard(nb);adj[nb].discard(i);adj[i].add(nw);adj[nw].add(i)
    CA[(n,seed)]=adj; return adj
def thin(adj,iso,seed):
    rng=np.random.default_rng(seed+23); keep={1:1,2:0.85,3:0.7,4:0.5,5:0.3}; src=[];dst=[]
    for i in range(len(adj)):
        nb=np.fromiter(adj[i],dtype=np.int64); f=keep.get(int(iso[i]),0.7)
        if nb.size and f<1.0:
            mk=max(1,int(round(nb.size*f)))
            if mk<nb.size: nb=rng.choice(nb,size=mk,replace=False)
        if nb.size: src.append(np.full(nb.size,i)); dst.append(nb)
    s=np.concatenate(src);d=np.concatenate(dst);deg=np.bincount(d,minlength=len(adj)).astype(float);deg[deg==0]=np.nan; return s,d,deg
def order(df): return np.argsort(df.age_band.map(AGE_RANK).to_numpy(),kind="stable")
def induce(b,seed,rho,eld):
    s=b.copy(); rng=np.random.default_rng(seed+881); ei=np.where(eld)[0]; ne=ei.size; z=rng.standard_normal(ne)
    def ro(col,sign):
        vals=np.sort(s[col].to_numpy()[ei]); sc=rho*z+np.sqrt(max(1-rho*rho,0))*rng.standard_normal(ne)
        rk=np.argsort(np.argsort(sign*sc)); v=s[col].to_numpy().copy(); v[ei]=vals[rk]; s[col]=v
    ro("attr_financial_vulnerability",1); ro("attr_digital_literacy",-1); ro("attr_social_isolation",1); return s
def mult(s,eld):
    e=s.loc[eld]; fv=(e.attr_financial_vulnerability>=4);dl=(e.attr_digital_literacy<=2);si=(e.attr_social_isolation>=4)
    ind=fv.mean()*dl.mean()*si.mean(); return (fv&dl&si).mean()/ind if ind>0 else np.nan
def calib(base,target,eld):
    lo,hi=0,0.99
    for _ in range(22):
        m=(lo+hi)/2
        if mult(induce(base,42,m,eld),eld)<target: lo=m
        else: hi=m
    return (lo+hi)/2
def diffuse(net,dl,si,ad,fv,thr,steps,seed):
    src,dst,deg=net;n=len(dl);rng=np.random.default_rng(seed+13)
    pb=np.array([0,0,0.015,0.08,0.18])[dl-1];th=np.clip(thr-0.05*(ad-3)-0.03*(fv-3),0.2,0.95);A=np.zeros(n,bool)
    for _ in range(steps):
        new=(~A)&(rng.random(n)<pb);cnt=np.bincount(dst[A[src]],minlength=n).astype(float)
        fr=np.divide(cnt,deg,out=np.zeros(n),where=~np.isnan(deg));new|=(~A)&(fr>=th);A|=new
    return A
def run():
    n=3000;seeds=30;base0=load(n)
    base,ach=deflate_si(base0,0.14)
    eld=base["_eld"].to_numpy()
    print("elderly SI-high prevalence after deflation: %.3f (target 0.14; original ~0.30)"%ach)
    targets={"indep":calib(base,1.0,eld) if False else 0.0,"observed":calib(base,2.30,eld)}
    for thr in [0.55,0.65]:
        out={"indep":[],"observed":[]}
        for sd in range(1,seeds+1):
            for lab,rho in [("indep",0.0),("observed",targets["observed"])]:
                pop=induce(base,sd,rho,eld); o=order(pop); d=pop.iloc[o].reset_index(drop=True)
                net=thin(base_adj(n,sd),d.attr_social_isolation.to_numpy(),sd)
                A=diffuse(net,d.attr_digital_literacy.to_numpy(),d.attr_social_isolation.to_numpy(),
                          d.attr_authority_deference.to_numpy(),d.attr_financial_vulnerability.to_numpy(),thr,25,sd)
                eo=d["_eld"].to_numpy(); lb=float((eo&~A).sum())/n*1000; out[lab].append(lb)
        ci=lambda x:1.96*np.std(x,ddof=1)/np.sqrt(len(x))
        i=np.array(out["indep"]);o=np.array(out["observed"]);drop=round((i.mean()-o.mean())/i.mean()*100)
        sep=(i.mean()-ci(i))>(o.mean()+ci(o))
        print(f"thr {thr}: left-behind indep {i.mean():.1f}±{ci(i):.1f} -> observed {o.mean():.1f}±{ci(o):.1f} = -{drop}%  CIs disjoint: {sep}")
run()
