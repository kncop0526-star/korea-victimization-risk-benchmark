import os,sys,pathlib,json,hashlib,time,datetime,platform,csv
for env_name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[env_name]='1'
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8',line_buffering=True)
TASK=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(TASK))
from original_module import load_original
from runtime import simulation_context
config,REPO,OUT=simulation_context('decompose')
import numpy as np,pandas as pd,pyarrow
os.chdir(config['data_root'])
start=time.perf_counter();started=datetime.datetime.now().isoformat()
def write_json(name,value):
    with (OUT/name).open('w',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
def file_sig(path):
    p=pathlib.Path(path);raw=p.read_bytes();return {'bytes':len(raw),'mtime_ns':p.stat().st_mtime_ns,'sha256':hashlib.sha256(raw).hexdigest()}
def arr_sig(arr):
    a=np.asarray(arr);h=hashlib.sha256();h.update(str(a.dtype).encode());h.update(str(a.shape).encode());h.update(a.tobytes(order='C'));return h.hexdigest()
def bundle_sig(arrays):
    return hashlib.sha256('|'.join(arr_sig(a) for a in arrays).encode()).hexdigest()
def frame_sig(df):return hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()
source=REPO/'src/abm_decompose.py';prior_source=file_sig(source)
assert prior_source['sha256']==config['protected'][str(source)]['sha256']
mod,loader=load_original(source)
assert loader['function_bodies_unchanged']
base=mod.load_sample(config['n'],config['sample_seed']);eld=base['_eld'].to_numpy()
cohort=(base['_eld']&(base['attr_digital_literacy']<=2)&(base['attr_social_isolation']>=4)).to_numpy()
rho=mod.calibrate_rho(base,2.30)
DECOMP=['real','within_cell','shuffle_full','block'];SWEEP=['eld_indep','eld_inject'];CONDS=DECOMP+SWEEP
builders={'real':mod.cond_real,'within_cell':mod.cond_within_cell,'shuffle_full':mod.cond_shuffle_full,'block':mod.cond_block,'eld_indep':mod.cond_eld_indep,'eld_inject':lambda b,sd:mod.induce_factor(b,sd,rho,eld)}
metadata={'started':started,'source':prior_source,'loader':loader,'runner':file_sig(__file__),'helper':file_sig(TASK/'original_module.py'),'configuration':{k:config[k] for k in ['n','sample_seed','simulation_seeds','diffusion_steps','topologies','thresholds']},'versions':{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'pyarrow':pyarrow.__version__},'threads':{k:os.environ[k] for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']},'baseline_sources':{name:file_sig(REPO/'results_v4'/name) for name in ['abm_decompose.csv','abm_sweep.csv']},'input_data':{p:file_sig(p) for p in config['input_data']},'base_frame_sha256':frame_sig(base),'elderly_mask_sha256':arr_sig(eld),'cohort_mask_sha256':arr_sig(cohort),'n_actual':len(base),'elderly_n':int(eld.sum()),'cohort_n':int(cohort.sum()),'calibration_target':2.30,'calibration_seed':42,'rho':rho,'seed42_realized_injected_multiplier':float(mod.mult_eld(mod.induce_factor(base,42,rho,eld),eld)),'real_multiplier':float(mod.mult_eld(base,eld)),'function_body_changes':0,'only_horizon_varies':True}
write_json('metadata_initial.json',metadata)
print(json.dumps({'stage':'loaded','n':len(base),'rho':rho,'elderly_n':int(eld.sum()),'cohort_n':int(cohort.sum())}))
prepared={};prep_rows=[]
for topo in config['topologies']:
    for sd in config['simulation_seeds']:
        for c in CONDS:
            frame=builders[c](base,sd);order,attrs=mod.order_attrs(frame);net=mod.build_net(topo,attrs[1],sd)
            prepared[(topo,sd,c)]=(order,attrs,net)
            prep_rows.append({'topology':topo,'seed':sd,'condition':c,'population_sha256':frame_sig(frame),'ordered_attributes_sha256':bundle_sig(attrs),'ordering_sha256':arr_sig(order),'transmission_network_sha256':bundle_sig(net),'network_edge_entries':len(net[0]),'realized_elderly_multiplier':float(mod.mult_eld(frame,eld))})
        if sd%10==0: print(json.dumps({'stage':'prepare','topology':topo,'seed':sd,'elapsed_seconds':round(time.perf_counter()-start,2)}))
pd.DataFrame(prep_rows).to_csv(OUT/'prepared_hashes.csv',index=False)
base_networks=[]
for (topo,n,sd),adj in mod._ADJ_CACHE.items():
    canonical=json.dumps([sorted(v) for v in adj],separators=(',',':')).encode()
    base_networks.append({'topology':topo,'n':n,'seed':sd,'base_adjacency_sha256':hashlib.sha256(canonical).hexdigest()})
write_json('base_network_hashes.json',base_networks)
ci=lambda x:1.96*np.std(x,ddof=1)/np.sqrt(len(x))
def aggregate(reach,cratio):
    drows=[];srows=[]
    for topo in config['topologies']:
        for thr in config['thresholds']:
            R={c:np.array(reach[c][(topo,thr)]) for c in DECOMP}
            joint=R['within_cell']-R['real'];coup=R['shuffle_full']-R['within_cell'];full=R['shuffle_full']-R['real'];blk=R['block']-R['real'];cr_real=np.array(cratio['real'][(topo,thr)])
            drows.append(dict(topology=topo,threshold=thr,reach_real=round(R['real'].mean(),2),joint_pp=round(joint.mean(),2),joint_CI=round(ci(joint),2),coupling_pp=round(coup.mean(),2),coupling_CI=round(ci(coup),2),full_pp=round(full.mean(),2),full_CI=round(ci(full),2),blockVSreal_pp=round(blk.mean(),2),cohort_real=round(cr_real.mean(),3)))
            row=dict(topology=topo,threshold=thr)
            for c in SWEEP:
                rc=np.array(reach[c][(topo,thr)]);row[f'reach_{c}']=round(rc.mean(),2);row[f'reach_{c}_CI']=round(ci(rc),2)
            row['inject_minus_indep_pp']=round(np.array(reach['eld_inject'][(topo,thr)]).mean()-np.array(reach['eld_indep'][(topo,thr)]).mean(),2);srows.append(row)
    return pd.DataFrame(drows),pd.DataFrame(srows)
def compare_baseline(ddf,sdf):
    checks=[]
    for name,actual in [('abm_decompose.csv',ddf),('abm_sweep.csv',sdf)]:
        expected=pd.read_csv(REPO/'results_v4'/name);expected=expected.sort_values(['topology','threshold']).reset_index(drop=True);actual=actual.sort_values(['topology','threshold']).reset_index(drop=True)
        mismatches=[]
        assert list(expected.columns)==list(actual.columns)
        for r in range(len(expected)):
            for col in expected.columns:
                x=expected.iloc[r][col];y=actual.iloc[r][col]
                if x!=y:mismatches.append({'row':r,'column':col,'expected':str(x),'actual':str(y)})
        checks.append({'file':name,'rows':len(expected),'columns':list(expected.columns),'numeric_cells':len(expected)*(len(expected.columns)-1),'exact_numeric_match':not mismatches,'mismatches':mismatches})
    result={'pass':all(c['exact_numeric_match'] for c in checks),'checks':checks,'checked_at':datetime.datetime.now().isoformat()}
    write_json('baseline_check.json',result)
    print(json.dumps({'stage':'baseline','pass':result['pass'],'checks':checks}))
    return result['pass']
all_raw=[];all_d=[];all_s=[];timings=[]
for steps in config['diffusion_steps']:
    t0=time.perf_counter();reach={c:{} for c in CONDS};cratio={c:{} for c in CONDS};raw=[]
    for topo in config['topologies']:
        for sd in config['simulation_seeds']:
            for c in CONDS:
                order,attrs,net=prepared[(topo,sd,c)]
                for thr in config['thresholds']:
                    adopted=mod.diffuse(net,attrs,thr,steps,sd,order)
                    r=adopted.mean()*100;cr=adopted[cohort].mean()/adopted[~cohort].mean()
                    reach[c].setdefault((topo,thr),[]).append(r);cratio[c].setdefault((topo,thr),[]).append(cr)
                    raw.append({'steps':steps,'topology':topo,'seed':sd,'condition':c,'threshold':thr,'n':len(base),'adopted_n':int(adopted.sum()),'reach_pct':float(r),'cohort_reach_ratio':float(cr),'elderly_n':int(eld.sum()),'elderly_unadopted_n':int((eld&~adopted).sum()),'elderly_unadopted_per1000_population':float((eld&~adopted).sum()/len(base)*1000),'cohort_n':int(cohort.sum()),'cohort_adopted_n':int((cohort&adopted).sum()),'noncohort_adopted_n':int((~cohort&adopted).sum()),'adopted_state_sha256':arr_sig(adopted)})
            if sd%10==0:print(json.dumps({'stage':'diffuse','steps':steps,'topology':topo,'seed':sd,'elapsed_seconds':round(time.perf_counter()-start,2)}))
    ddf,sdf=aggregate(reach,cratio)
    pd.DataFrame(raw).to_csv(OUT/f'per_seed_T{steps}.csv',index=False,float_format='%.17g')
    ddf.to_csv(OUT/f'abm_decompose_T{steps}.csv',index=False);sdf.to_csv(OUT/f'abm_sweep_T{steps}.csv',index=False)
    all_raw.extend(raw);all_d.extend(ddf.assign(steps=steps).to_dict('records'));all_s.extend(sdf.assign(steps=steps).to_dict('records'))
    timings.append({'steps':steps,'seconds':time.perf_counter()-t0,'runs':len(raw)})
    write_json('progress.json',{'completed_horizons':[v['steps'] for v in timings],'elapsed_seconds':time.perf_counter()-start,'timings':timings})
    if steps==25 and not compare_baseline(ddf,sdf):
        print('BASELINE MISMATCH: EXTENSIONS STOPPED');sys.exit(2)
    print(json.dumps({'stage':'horizon_complete','steps':steps,'runs':len(raw),'seconds':round(time.perf_counter()-t0,2)}))
pd.DataFrame(all_raw).to_csv(OUT/'per_seed_all_horizons.csv',index=False,float_format='%.17g')
pd.DataFrame(all_d).to_csv(OUT/'abm_decompose_all_horizons.csv',index=False);pd.DataFrame(all_s).to_csv(OUT/'abm_sweep_all_horizons.csv',index=False)
for row in prep_rows:
    order,attrs,net=prepared[(row['topology'],row['seed'],row['condition'])]
    assert row['ordered_attributes_sha256']==bundle_sig(attrs);assert row['ordering_sha256']==arr_sig(order);assert row['transmission_network_sha256']==bundle_sig(net)
assert file_sig(source)==prior_source
for name,signature in metadata['baseline_sources'].items():assert file_sig(REPO/'results_v4'/name)==signature
for p,signature in metadata['input_data'].items():assert file_sig(p)==signature
metadata.update({'finished':datetime.datetime.now().isoformat(),'runtime_seconds':time.perf_counter()-start,'timings':timings,'per_seed_rows':len(all_raw),'horizon_count':len(timings),'prepared_populations_and_networks':len(prepared),'base_networks':len(base_networks),'in_memory_network_attrs_unchanged_after_runs':True,'original_source_baseline_csv_input_files_unchanged':True,'baseline_check':json.loads((OUT/'baseline_check.json').read_text(encoding='utf-8'))})
write_json('metadata_final.json',metadata)
print(json.dumps({'stage':'complete','per_seed_rows':len(all_raw),'elapsed_seconds':round(time.perf_counter()-start,2)}))