from pathlib import Path
import json,hashlib,sys,itertools
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from runtime import analysis_context
C,T,A=analysis_context()
bp=json.loads((T/'discriminate/baseline.json').read_text(encoding='utf-8'));assert bp['passed'] and not bp['mismatches']
bd=json.loads((T/'decompose/baseline_check.json').read_text(encoding='utf-8'));assert bd['pass'] and all(not x['mismatches'] for x in bd['checks'])
bo=json.loads((T/'opinion/baseline_reproduction.json').read_text(encoding='utf-8'));assert bo['pass'] and not bo['mismatches']
def exact_grid(d,columns,values,numeric):
 actual=list(d[columns].itertuples(index=False,name=None));expected=set(itertools.product(*values))
 assert len(actual)==len(set(actual))==len(expected) and set(actual)==expected,(len(actual),len(set(actual)),len(expected))
 assert np.isfinite(d[numeric].to_numpy(dtype=float)).all(),numeric
raw=pd.read_csv(T/'discriminate/raw.csv');assert len(raw)==2700
exact_grid(raw,['topology','threshold','target_mult','steps','seed'],[C['topologies'],C['thresholds'],C['targets'],C['diffusion_steps'],C['simulation_seeds']],['overall','leftbehind_per1k','realized_multiplier'])
assert raw.groupby(['steps','topology','threshold','target_mult']).size().eq(30).all()
keys=['topology','threshold','target_mult','seed'];monotonic=[]
for k,g in raw.groupby(keys):
 g=g.sort_values('steps')
 if (np.diff(g.overall)<-1e-10).any() or (np.diff(g.leftbehind_per1k)>1e-10).any():monotonic.append(k)
assert not monotonic
indices=np.random.default_rng(C['bootstrap_seed']).integers(0,30,size=(C['bootstrap_replicates'],30))
def vals(g,col):
 g=g.sort_values('seed');assert list(g.seed)==list(range(1,31));return g[col].to_numpy(dtype=float)
def ci_half(x):return 1.96*np.std(x,ddof=1)/np.sqrt(len(x))
def boot_ci(x):return np.percentile(x,[2.5,97.5]).tolist()
def diffsummary(d):
 b=d[indices].mean(1);lo,hi=boot_ci(b)
 return float(d.mean()),float(lo),float(hi),float(ci_half(d))
rows=[];means=[]
for (topo,thr,step),g in raw.groupby(['topology','threshold','steps']):
 obs=g[g.target_mult==2.3];oyo=vals(obs,'overall');oyl=vals(obs,'leftbehind_per1k')
 for target,gg in g.groupby('target_mult'):
  means.append({'topology':topo,'threshold':thr,'steps':step,'target':target,'overall_mean':gg.overall.mean(),'overall_CI_half':ci_half(gg.overall.to_numpy()),'older_unadopted_per1k_mean':gg.leftbehind_per1k.mean(),'older_CI_half':ci_half(gg.leftbehind_per1k.to_numpy()),'realized_multiplier_mean':gg.realized_multiplier.mean()})
 for ref in [1.0,1.29]:
  base=g[g.target_mult==ref];bov=vals(base,'overall');blb=vals(base,'leftbehind_per1k');dagg=oyo-bov;dlb=blb-oyl
  am,alo,ahi,ah=diffsummary(dagg);dm,dlo,dhi,dh=diffsummary(dlb)
  bb=blb[indices].mean(1);bo=oyl[indices].mean(1);valid=bb>0;ratios=100*(bb[valid]-bo[valid])/bb[valid]
  rel=100*dm/blb.mean() if blb.mean()>0 else np.nan
  rlo,rhi=boot_ci(ratios) if valid.all() else (np.nan,np.nan)
  gb=raw[(raw.topology==topo)&(raw.threshold==thr)&(raw.steps==25)]
  b0=vals(gb[gb.target_mult==ref],'leftbehind_per1k');o0=vals(gb[gb.target_mult==2.3],'leftbehind_per1k');timechange=diffsummary(dlb-(b0-o0))
  rows.append(dict(topology=topo,threshold=thr,steps=step,reference_target=ref,observed_target=2.3,reference_reach_mean=bov.mean(),observed_reach_mean=oyo.mean(),reach_difference_pp=am,reach_difference_boot_low=alo,reach_difference_boot_high=ahi,reach_difference_normal_half=ah,reference_older_per1k=blb.mean(),observed_older_per1k=oyl.mean(),older_absolute_reduction_per1k=dm,older_reduction_boot_low=dlo,older_reduction_boot_high=dhi,older_reduction_normal_half=dh,older_relative_reduction_pct=rel,relative_reduction_boot_low=rlo,relative_reduction_boot_high=rhi,relative_bootstrap_valid=int(valid.sum()),seed_lower_older_count=int((dlb>1e-10).sum()),seed_equal_older_count=int((np.abs(dlb)<=1e-10).sum()),seed_higher_older_count=int((dlb<-1e-10).sum()),separate_original_CI_nonoverlap=bool(blb.mean()-ci_half(blb)>oyl.mean()+ci_half(oyl)),paired_bootstrap_CI_excludes_zero=bool(dlo>0 or dhi<0),both_reach_at_least99=bool(min(bov.mean(),oyo.mean())>=99),reference_older_below1per1k=bool(blb.mean()<1),absolute_effect_change_vs25=timechange[0],change_vs25_boot_low=timechange[1],change_vs25_boot_high=timechange[2]))
contrasts=pd.DataFrame(rows);means=pd.DataFrame(means)
contrasts.to_csv(A/'diffusion_target_contrasts.csv',index=False,float_format='%.12g');means.to_csv(A/'diffusion_target_means.csv',index=False,float_format='%.12g')
headline=[]
for step in C['diffusion_steps']:
 g=contrasts[(contrasts.steps==step)&(contrasts.reference_target==1.)]
 row={'steps':step,'max_abs_aggregate_effect_pp_all6':g.reach_difference_pp.abs().max()}
 for thr in [.55,.65]:
  x=g[(g.topology=='smallworld')&(g.threshold==thr)].iloc[0];pre=f'sw_{str(thr).replace(".","")}_'
  for col in ['reference_older_per1k','observed_older_per1k','older_absolute_reduction_per1k','older_relative_reduction_pct','older_reduction_boot_low','older_reduction_boot_high','both_reach_at_least99','reference_reach_mean','observed_reach_mean']:row[pre+col]=x[col]
 headline.append(row)
pd.DataFrame(headline).to_csv(A/'headline.csv',index=False,float_format='%.12g')
def decomposition(rawfile,outfile,value,levelcol):
 d=pd.read_csv(rawfile);effects=[]
 conditions=['real','within_cell','shuffle_full','block']+(['eld_indep','eld_inject'] if levelcol=='threshold' else [])
 exact_grid(d,['topology',levelcol,'steps','condition','seed'],[C['topologies'],C['thresholds'] if levelcol=='threshold' else C['eps'],C['diffusion_steps'] if levelcol=='threshold' else C['opinion_steps'],conditions,C['simulation_seeds']],[value])
 for (topo,level,step),g in d.groupby(['topology',levelcol,'steps']):
  arr={c:vals(q,value) for c,q in g.groupby('condition')}
  ds={'joint':arr['within_cell']-arr['real'],'coupling':arr['shuffle_full']-arr['within_cell'],'full':arr['shuffle_full']-arr['real'],'blockVSreal':arr['block']-arr['real']}
  row={'topology':topo,levelcol:level,'steps':step,'real_mean':arr['real'].mean()}
  for effect,x in ds.items():
   mean,lo,hi,half=diffsummary(x);row.update({effect+'_pp':mean,effect+'_boot_low':lo,effect+'_boot_high':hi,effect+'_normal_half':half})
  row['coupling_abs_larger_than_joint']=abs(row['coupling_pp'])>abs(row['joint_pp']);effects.append(row)
 out=pd.DataFrame(effects);out.to_csv(A/outfile,index=False,float_format='%.12g');return out
dec=decomposition(T/'decompose/per_seed_all_horizons.csv','diffusion_decomposition_contrasts.csv','reach_pct','threshold')
op=decomposition(T/'opinion/raw_seed_metrics.csv','opinion_decomposition_contrasts.csv','noncons_pct','eps')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18})
colors={1.0:'#0072B2',1.29:'#888888',2.3:'#D55E00'}
fig,ax=plt.subplots(2,2,figsize=(11,7.4),layout='constrained')
for i,thr in enumerate([.55,.65]):
 g=contrasts[(contrasts.topology=='smallworld')&(contrasts.threshold==thr)&(contrasts.reference_target==1.)].sort_values('steps');x=g.steps.to_numpy()
 a=ax[i,0];a.plot(x,g.reach_difference_pp,'o-',color='#0072B2');a.fill_between(x,g.reach_difference_boot_low,g.reach_difference_boot_high,color='#0072B2',alpha=.16);a.axhline(0,color='black',lw=.8);a.set_title(f'Small-world, threshold {thr:.2f}: aggregate contrast');a.set_ylabel('Reach change (percentage points)')
 a=ax[i,1]
 for target in [1.0,1.29,2.3]:
  q=means[(means.topology=='smallworld')&(means.threshold==thr)&(means.target==target)].sort_values('steps');a.plot(q.steps,q.older_unadopted_per1k_mean,'o-',color=colors[target],label=f'Target {target:.2f}');a.fill_between(q.steps,np.maximum(0,q.older_unadopted_per1k_mean-q.older_CI_half),q.older_unadopted_per1k_mean+q.older_CI_half,color=colors[target],alpha=.1)
 a.set_title(f'Small-world, threshold {thr:.2f}: older non-adopters');a.set_ylabel('Older non-adopters per 1,000 total agents');a.legend(frameon=False,fontsize=9)
for a in ax.flat:a.set_xscale('log',base=2);a.set_xticks(C['diffusion_steps'],labels=C['diffusion_steps']);a.set_xlabel('Simulation steps')
fig.suptitle('Duration sensitivity of the unchanged diffusion model\n30 paired seeds; fixed 3,000-agent sample',fontsize=13)
fig.savefig(A/'diffusion_duration.png',dpi=220);fig.savefig(A/'diffusion_duration.pdf');plt.close(fig)
def plot_decomp(df,levelcol,levels,steps,name,title):
 fig,axes=plt.subplots(2,len(levels),figsize=(4*len(levels),6.8),layout='constrained',squeeze=False)
 for i,topo in enumerate(['smallworld','scalefree']):
  for j,level in enumerate(levels):
   g=df[(df.topology==topo)&(df[levelcol]==level)].sort_values('steps');a=axes[i,j]
   for effect,color in [('joint','#0072B2'),('coupling','#D55E00')]:
    a.plot(g.steps,g[effect+'_pp'],'o-',label=effect,color=color);a.fill_between(g.steps,g[effect+'_boot_low'],g[effect+'_boot_high'],alpha=.13,color=color)
   a.axhline(0,color='black',lw=.8);a.set_xscale('log',base=2);a.set_xticks(steps,labels=steps);a.set_title(f'{topo}; {levelcol}={level:.2f}');a.set_xlabel('Simulation steps');a.set_ylabel('Effect (percentage points)');a.legend(frameon=False)
 fig.suptitle(title+'\n30 paired seeds; pointwise paired-bootstrap 95% intervals',fontsize=12);fig.savefig(A/(name+'.png'),dpi=200);fig.savefig(A/(name+'.pdf'));plt.close(fig)
plot_decomp(dec,'threshold',C['thresholds'],C['diffusion_steps'],'diffusion_decomposition_duration','Diffusion decomposition over time')
plot_decomp(op,'eps',C['eps'],C['opinion_steps'],'opinion_duration','Opinion decomposition over time')
checks={'primary_rows':len(raw),'primary_cells':len(raw.groupby(['steps','topology','threshold','target_mult'])),'primary_monotonicity_failures':monotonic,'contrast_rows':len(contrasts),'decomposition_cells':len(dec),'opinion_cells':len(op),'paired_bootstrap_indices_sha256':hashlib.sha256(indices.tobytes()).hexdigest(),'bootstrap_replicates':len(indices),'pointwise_not_simultaneous':True,'conditional_on_sample_seed42':True,'all_three_baseline_gates_passed':True,'exact_full_cartesian_grids_verified':True,'relative_bootstrap_CI_rule':'NA if any resampled reference mean is zero; point estimate NA if observed reference mean is zero','coupling_larger_flag':'descriptive abs(mean) only, not a significance test'}
(A/'analysis_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(pd.DataFrame(headline).to_string(index=False));print('\nOPINION\n'+op[['topology','eps','steps','real_mean','joint_pp','coupling_pp','coupling_abs_larger_than_joint']].to_string(index=False));print('\nDECOMPOSITION\n'+dec[['topology','threshold','steps','real_mean','joint_pp','coupling_pp','coupling_abs_larger_than_joint']].to_string(index=False))
