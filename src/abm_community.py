# C-2: 4-population decomposition on a planted-community network (demographic-homophily
# communities by age x education), to test whether the demographic-coupling effect survives
# realistic community structure (reviewer: Watts-Strogatz/Barabasi-Albert too stylized).
import glob, sys, numpy as np, pandas as pd, pyarrow.parquet as pq
ATTRS=["attr_digital_literacy","attr_social_isolation","attr_authority_deference","attr_financial_vulnerability"]
AGE_RANK={"19-29":0,"30-44":1,"45-59":2,"60-74":3,"75+":4}
def load(n,seed=42):
    p=sorted(glob.glob("data/processed/enriched_1M_v4_parts/*.parquet"))
    df=pq.read_table(p[0],columns=["age_band","sex","education_tier"]+ATTRS).to_pandas()
    idx=np.random.default_rng(seed).choice(len(df),size=min(n,len(df)),replace=False)
    s=df.iloc[idx].reset_index(drop=True)
    for c in ATTRS: s[c]=s[c].astype(int)
    s["_cell"]=s.age_band.astype(str)+"|"+s.sex.astype(str)+"|"+s.education_tier.astype(str)
    s["_comm"]=(s.age_band.astype(str)+"|"+s.education_tier.astype(str))
    return s
CACHE={}
def comm_adj(comm_ids,seed,m_in=4,m_out=1):
    key=(seed,len(comm_ids)); 
    if key in CACHE: return CACHE[key]
    rng=np.random.default_rng(seed+7); n=len(comm_ids)
    by={}
    for i,c in enumerate(comm_ids): by.setdefault(c,[]).append(i)
    by={k:np.array(v) for k,v in by.items()}
    adj=[set() for _ in range(n)]
    allnodes=np.arange(n)
    for i in range(n):
        same=by[comm_ids[i]]
        if same.size>1:
            pick=rng.choice(same,size=min(m_in,same.size),replace=False)
            for j in pick:
                if j!=i: adj[i].add(int(j)); adj[int(j)].add(i)
        gl=rng.choice(allnodes,size=m_out,replace=False)
        for j in gl:
            if j!=i: adj[i].add(int(j)); adj[int(j)].add(i)
    CACHE[key]=adj; return adj
def thin(adj,iso,seed):
    rng=np.random.default_rng(seed+23); keep={1:1.0,2:0.85,3:0.7,4:0.5,5:0.3}; src=[];dst=[]
    for i in range(len(adj)):
        nb=np.fromiter(adj[i],dtype=np.int64); f=keep.get(int(iso[i]),0.7)
        if nb.size and f<1.0:
            mk=max(1,int(round(nb.size*f)));
            if mk<nb.size: nb=rng.choice(nb,size=mk,replace=False)
        if nb.size: src.append(np.full(nb.size,i)); dst.append(nb)
    s=np.concatenate(src); d=np.concatenate(dst); deg=np.bincount(d,minlength=len(adj)).astype(float); deg[deg==0]=np.nan
    return s,d,deg
def order(df): return np.argsort(df.age_band.map(AGE_RANK).to_numpy(),kind="stable")
def diffuse(net,dl,si,ad,fv,thr,steps,seed):
    src,dst,deg=net; n=len(dl); rng=np.random.default_rng(seed+13)
    pb=np.array([0,0,0.015,0.08,0.18])[dl-1]; th=np.clip(thr-0.05*(ad-3)-0.03*(fv-3),0.2,0.95); ad_=np.zeros(n,bool)
    for _ in range(steps):
        new=(~ad_)&(rng.random(n)<pb); cnt=np.bincount(dst[ad_[src]],minlength=n).astype(float)
        fr=np.divide(cnt,deg,out=np.zeros(n),where=~np.isnan(deg)); new|=(~ad_)&(fr>=th); ad_|=new
    return ad_
def cond(base,kind,seed):
    s=base.copy()
    if kind=="real": return s
    rg=np.random.default_rng(seed+ {"shuffle":99,"within":311,"block":733}[kind])
    if kind=="shuffle":
        for c in ATTRS: s[c]=rg.permutation(s[c].to_numpy())
    elif kind=="within":
        g=s.groupby("_cell").indices
        for c in ATTRS:
            v=s[c].to_numpy().copy()
            for _,gi in g.items():
                if gi.size>1: v[gi]=rg.permutation(v[gi])
            s[c]=v
    elif kind=="block":
        p=rg.permutation(len(s))
        for c in ATTRS: s[c]=s[c].to_numpy()[p]
    return s
def run():
    n=3000; seeds=30; thrs=[0.65]; base=load(n)
    comm=base["_comm"].to_numpy()
    reach={k:{t:[] for t in thrs} for k in ["real","within","shuffle","block"]}
    # avg degree report
    degs=[]
    for sd in range(1,seeds+1):
        adjc=comm_adj(comm,sd)
        for k in ["real","within","shuffle","block"]:
            fr=cond(base,k,sd); o=order(fr); d=fr.iloc[o].reset_index(drop=True)
            net=thin(adjc,d.attr_social_isolation.to_numpy(),sd)
            if k=="real" and sd==1: degs.append(np.nanmean(net[2]))
            for t in thrs:
                a=diffuse(net,d.attr_digital_literacy.to_numpy(),d.attr_social_isolation.to_numpy(),
                          d.attr_authority_deference.to_numpy(),d.attr_financial_vulnerability.to_numpy(),t,25,sd)
                reach[k][t].append(a.mean()*100)
        sys.stdout.write("."); sys.stdout.flush()
    ci=lambda x:1.96*np.std(x,ddof=1)/np.sqrt(len(x))
    print("\n=== COMMUNITY NETWORK decomposition (planted age x education communities, n=%d, %d seeds) ==="%(n,seeds))
    print("mean degree ~%.1f"%(degs[0] if degs else 0))
    for t in thrs:
        R={k:np.array(reach[k][t]) for k in reach}
        joint=R["within"]-R["real"]; coup=R["shuffle"]-R["within"]; full=R["shuffle"]-R["real"]; blk=R["block"]-R["real"]
        print(f"thr {t}: joint {joint.mean():+.2f}±{ci(joint):.2f} | coupling {coup.mean():+.2f}±{ci(coup):.2f} | full {full.mean():+.2f}±{ci(full):.2f} | block-real {blk.mean():+.2f}")
run()
