from pathlib import Path
import sys,json,hashlib,time,os
import numpy as np,pandas as pd
T=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(T))
from original_module import load_original
from runtime import simulation_context
C,R,D=simulation_context('discriminate');os.chdir(C['data_root'])
start=time.perf_counter();m,loader=load_original(R/'src/abm_discriminate.py')
base=m.load_sample(C['n'],C['sample_seed']);eld=base['_eld'].to_numpy();assert len(base)==3000
rhos={t:(0.0 if t<=1.001 else m.calib(base,t,eld)) for t in C['targets']}
achieved={t:round(m.mult(m.induce(base,42,rhos[t],eld),eld),3) for t in C['targets']}
pops={(t,sd):m.induce(base,sd,rhos[t],eld) for t in C['targets'] for sd in C['simulation_seeds']}
def frame_hash(df):return hashlib.sha256(pd.util.hash_pandas_object(df,index=True).values.tobytes()).hexdigest()
def net_hash(net):
 h=hashlib.sha256()
 for a in net:h.update(np.asarray(a).tobytes())
 return h.hexdigest()
fingerprints=[]
for topo in C['topologies']:
 for (t,sd),p in pops.items():
  ordered=p.iloc[m.order_idx(p)].reset_index(drop=True);network=m.build_net(topo,ordered.attr_social_isolation.to_numpy(),sd)
  fingerprints.append({'topology':topo,'target':t,'seed':sd,'population_sha256':frame_hash(p),'network_sha256':net_hash(network),'realized_multiplier':float(m.mult(p,eld))})
def aggregate(df):
 rows=[]
 ci=lambda x:1.96*np.nanstd(x,ddof=1)/np.sqrt(max(np.sum(~np.isnan(x)),1))
 for (step,topo,t,thr),g in df.groupby(['steps','topology','target_mult','threshold'],sort=True):
  ov=g.overall.to_numpy();cr=g.coh_reach.to_numpy();dbr=g.db_reach.to_numpy();gap=ov-dbr
  rows.append(dict(steps=step,topology=topo,target_mult=t,achieved_mult=achieved[t],threshold=thr,overall_reach=round(np.mean(ov),2),overall_CI=round(ci(ov),2),coh_n=round(g.coh_n.mean(),1),coh_reach=round(np.nanmean(cr),2),db_n=round(g.db_n.mean(),1),db_reach=round(np.nanmean(dbr),2),db_reach_CI=round(ci(dbr),2),db_gap_pp=round(np.nanmean(gap),2),db_gap_CI=round(ci(gap),2),leftbehind_per1k=round(g.leftbehind_per1k.mean(),2),lb_CI=round(ci(g.leftbehind_per1k.to_numpy()),2)))
 return pd.DataFrame(rows)
rows=[];baseline=None
for step in C['diffusion_steps']:
 for topo in C['topologies']:
  for target in C['targets']:
   for sd in C['simulation_seeds']:
    pop=pops[(target,sd)]
    for thr in C['thresholds']:
     result=m.run(pop,topo,thr,step,sd)
     rows.append(dict(steps=step,topology=topo,target_mult=target,threshold=thr,seed=sd,elderly_n=int(eld.sum()),n=len(base),realized_multiplier=float(m.mult(pop,eld)),**result))
   print(json.dumps({'steps':step,'topology':topo,'target':target,'rows':len(rows),'elapsed_seconds':round(time.perf_counter()-start,2)}),flush=True)
 df=pd.DataFrame(rows);df.to_csv(D/'raw.csv',index=False,float_format='%.17g');agg=aggregate(df);agg.to_csv(D/'aggregate.csv',index=False)
 if step==25:
  ref=pd.read_csv(R/'results_v4/abm_discriminate_grid.csv');cur=agg.loc[agg.steps==25];errors=[];checks=0
  for _,r in ref.iterrows():
   hit=cur[(cur.topology==r.topology)&(cur.threshold==r.threshold)&(cur.target_mult==r.target_mult)];assert len(hit)==1
   for col in ref.columns:
    if col=='topology':continue
    a=float(hit.iloc[0][col]);b=float(r[col]);checks+=1
    if not np.isclose(a,b,rtol=0,atol=1e-10,equal_nan=True):errors.append({'key':[r.topology,r.threshold,r.target_mult],'column':col,'new':a,'original':b})
  baseline={'rows':len(ref),'numeric_checks':checks,'mismatches':errors,'passed':not errors}
  (D/'baseline.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8');assert not errors,errors
  print('BASELINE PASS '+str(checks),flush=True)
fingerprint_fail=[]
for f in fingerprints:
 p=pops[(f['target'],f['seed'])];ordered=p.iloc[m.order_idx(p)].reset_index(drop=True)
 if frame_hash(p)!=f['population_sha256'] or net_hash(m.build_net(f['topology'],ordered.attr_social_isolation.to_numpy(),f['seed']))!=f['network_sha256']:fingerprint_fail.append(f)
assert not fingerprint_fail
assert len(rows)==len(C['diffusion_steps'])*len(C['topologies'])*len(C['targets'])*len(C['simulation_seeds'])*len(C['thresholds'])
meta={'loader':loader,'config':{k:v for k,v in C.items() if k not in ['protected']},'rhos':rhos,'seed42_achieved':achieved,'sample_sha256':frame_hash(base),'elderly_n':int(eld.sum()),'fingerprints':fingerprints,'fingerprints_unchanged':True,'raw_rows':len(rows),'baseline':baseline,'elapsed_seconds':time.perf_counter()-start,'source_unchanged':hashlib.sha256((R/'src/abm_discriminate.py').read_bytes()).hexdigest()==loader['sha256']}
assert meta['source_unchanged']
(D/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print('COMPLETE '+json.dumps({'rows':len(rows),'elapsed_seconds':meta['elapsed_seconds']}),flush=True)
