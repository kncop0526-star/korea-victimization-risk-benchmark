"""Original-model opinion duration sensitivity with an explicit output directory."""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import sys, json, hashlib, time, csv, importlib.util, datetime, traceback
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from runtime import simulation_context
CFG, REPO, HERE = simulation_context("opinion")
os.chdir(CFG["data_root"])
sys.dont_write_bytecode = True
START = time.perf_counter()
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save_json(name, value):
    p = HERE / name
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")

def progress(message):
    msg = f"{datetime.datetime.now().isoformat(timespec='seconds')} {time.perf_counter()-START:.1f}s {message}"
    print(msg, flush=True)
    with (HERE / "progress.log").open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

def frame_sha(d):
    h = hashlib.sha256()
    h.update(json.dumps(list(d.columns)).encode())
    h.update(pd.util.hash_pandas_object(d, index=True).to_numpy().tobytes())
    return h.hexdigest()

def arrays_sha(*arrays):
    h = hashlib.sha256()
    for a in arrays:
        a = np.ascontiguousarray(a)
        h.update(str(a.dtype).encode()); h.update(str(a.shape).encode()); h.update(a.tobytes())
    return h.hexdigest()

def ci(x):
    x = np.asarray(x, dtype=float)
    return float(1.96 * np.nanstd(x, ddof=1) / np.sqrt(max(np.sum(~np.isnan(x)), 1)))

def safe(v):
    return None if not np.isfinite(v) else float(v)

def aggregate(raw, steps):
    rows = []
    exact = []
    for topo in CFG["topologies"]:
        for e in CFG["eps"]:
            sub = [r for r in raw if r["steps"] == steps and r["topology"] == topo and r["eps"] == e]
            nc = {c: np.array([r["noncons_pct"] for r in sub if r["condition"] == c]) for c in CONDS}
            st = {c: np.array([r["cohort_stranded_pct"] for r in sub if r["condition"] == c]) for c in CONDS}
            assert all(len(nc[c]) == 30 for c in CONDS)
            j = nc["within_cell"] - nc["real"]
            cp = nc["shuffle_full"] - nc["within_cell"]
            fl = nc["shuffle_full"] - nc["real"]
            bk = nc["block"] - nc["real"]
            row = dict(topology=topo, eps=e, noncons_real=round(nc["real"].mean(), 2),
                joint_pp=round(j.mean(), 2), joint_CI=round(ci(j), 2), coupling_pp=round(cp.mean(), 2), coupling_CI=round(ci(cp), 2),
                full_pp=round(fl.mean(), 2), full_CI=round(ci(fl), 2), blockVSreal_pp=round(bk.mean(), 2),
                cohort_strand_real=round(np.nanmean(st["real"]), 1), cohort_strand_shuf=round(np.nanmean(st["shuffle_full"]), 1))
            rows.append(row)
            detail = {"topology": topo, "eps": e, "steps": steps, "n_seeds": 30}
            for c in CONDS:
                detail[c + "_noncons_mean"] = float(nc[c].mean())
                detail[c + "_noncons_CI_halfwidth"] = ci(nc[c])
                detail[c + "_stranded_mean"] = float(np.nanmean(st[c]))
                detail[c + "_stranded_CI_halfwidth"] = ci(st[c])
            for key, val in [("joint", j), ("coupling", cp), ("full", fl), ("blockVSreal", bk)]:
                detail[key + "_pp"] = float(val.mean())
                detail[key + "_CI_halfwidth"] = ci(val)
            exact.append(detail)
    return rows, exact

def main():
    global CONDS
    source = REPO / "src/abm_opinion.py"
    expected = CFG["protected"][str(source)]
    assert SHA(source) == expected["sha256"]
    spec = importlib.util.spec_from_file_location("read_only_original_loader", ROOT / "original_module.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    mod, provenance = helper.load_original(source)
    assert provenance["removed_top_level_main_calls"] == 1
    base = mod.load_sample(CFG["n"], CFG["sample_seed"])
    assert len(base) == 3000
    base_fp = frame_sha(base)
    CONDS = {"real":mod.c_real, "within_cell":mod.c_within, "shuffle_full":mod.c_shuffle, "block":mod.c_block}
    input_manifest = {p:{"bytes":Path(p).stat().st_size,"mtime_ns":Path(p).stat().st_mtime_ns,"sha256":SHA(p)} for p in CFG["input_data"]}
    assert input_manifest == CFG["input_data"]
    metadata = {"started_at":datetime.datetime.now().isoformat(),"config_sha256":SHA(ROOT/"config.json"),
        "runner_sha256":SHA(__file__),"helper_sha256":SHA(ROOT/"original_module.py"),"source_provenance":provenance,
        "input_data":input_manifest,"versions":CFG["versions"],"sample_seed":42,"n_sample":len(base),
        "n_elderly":int(base["_eld"].sum()),"sample_frame_sha256":base_fp,
        "steps":CFG["opinion_steps"],"seeds":CFG["simulation_seeds"],"conditions":list(CONDS),
        "initialization":"Each untouched hk_run call initializes its own default_rng(seed+13), with the same sorted population and ordered edge arrays.",
        "CI_formula":"1.96 * nanstd(x, ddof=1) / sqrt(max(sum(~isnan(x)),1)); original paired decomposition arrays."}
    save_json("provenance_start.json", metadata)
    jobs = []
    fingerprints = []
    raw = []
    progress("PREP start; fixed sample N=3000, seed=42, elderly=" + str(metadata["n_elderly"]))
    for topo in CFG["topologies"]:
        for sd in CFG["simulation_seeds"]:
            for condition, builder in CONDS.items():
                d, src, dst = mod.prep(builder(base, sd), topo, sd)
                data_fp = frame_sha(d); net_fp = arrays_sha(src, dst)
                ad = d.attr_authority_deference.to_numpy(); fv = d.attr_financial_vulnerability.to_numpy()
                x0 = np.clip(0.5+0.10*(ad-3)+0.05*(fv-3)+0.05*np.random.default_rng(sd+13).standard_normal(len(d)),0,1)
                fingerprint = dict(topology=topo, seed=sd, condition=condition, sample_frame_sha256=base_fp,
                    sorted_frame_sha256=data_fp, ordered_edges_sha256=net_fp, initial_opinion_sha256=arrays_sha(x0),
                    directed_edge_count=len(src), n_elderly=int(d["_eld"].sum()),
                    cohort_n=int((d["_eld"] & (d.attr_digital_literacy<=2) & (d.attr_social_isolation>=4)).sum()))
                fingerprints.append(fingerprint)
                jobs.append((d,src,dst,fingerprint))
    assert frame_sha(base) == base_fp
    save_json("network_and_initial_fingerprints.json", fingerprints)
    progress(f"PREP complete; {len(jobs)} immutable prepared inputs")
    aggregate_rows = []; exact_rows = []
    fieldnames = ["topology","eps","steps","seed","condition","noncons_pct","cohort_stranded_pct","cohort_n","sample_frame_sha256","sorted_frame_sha256","ordered_edges_sha256","initial_opinion_sha256"]
    with (HERE/"raw_seed_metrics.csv").open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames);writer.writeheader();f.flush()
        for steps in CFG["opinion_steps"]:
            progress(f"T={steps} start")
            for index,(d,src,dst,fp) in enumerate(jobs):
                assert arrays_sha(src,dst) == fp["ordered_edges_sha256"]
                assert frame_sha(d) == fp["sorted_frame_sha256"]
                for eps in CFG["eps"]:
                    noncons,stranded = mod.hk_run(d,src,dst,eps,steps,fp["seed"])
                    row={k:fp[k] for k in ["topology","seed","condition","cohort_n","sample_frame_sha256","sorted_frame_sha256","ordered_edges_sha256","initial_opinion_sha256"]}
                    row.update(eps=eps,steps=steps,noncons_pct=float(noncons),cohort_stranded_pct=float(stranded))
                    raw.append(row);writer.writerow(row)
                assert arrays_sha(src,dst) == fp["ordered_edges_sha256"]
                assert frame_sha(d) == fp["sorted_frame_sha256"]
                if (index+1)%20==0:
                    f.flush();progress(f"T={steps} {index+1}/{len(jobs)} prepared inputs complete")
            rounded,exact=aggregate(raw,steps)
            aggregate_rows.extend([dict(steps=steps,**r) for r in rounded]);exact_rows.extend(exact)
            pd.DataFrame(aggregate_rows).to_csv(HERE/"aggregate_original_rounded.csv",index=False)
            pd.DataFrame(exact_rows).to_csv(HERE/"aggregate_unrounded.csv",index=False)
            if steps==20:
                reference=list(csv.DictReader((REPO/"results_v4/abm_opinion_decompose.csv").open(encoding="utf-8-sig")))
                checks=[]
                for expected_row in reference:
                    actual=next(r for r in rounded if r["topology"]==expected_row["topology"] and r["eps"]==float(expected_row["eps"]))
                    for field,expected_value in expected_row.items():
                        if field=="topology":continue
                        checks.append(dict(topology=actual["topology"],eps=actual["eps"],field=field,
                            expected=float(expected_value),actual=float(actual[field]),match=float(expected_value)==float(actual[field])))
                result={"pass":all(c["match"] for c in checks),"numeric_comparisons":len(checks),"mismatches":[c for c in checks if not c["match"]],"checks":checks,"elapsed_seconds":time.perf_counter()-START}
                save_json("baseline_reproduction.json",result)
                progress(f"BASELINE {'PASS' if result['pass'] else 'FAIL'} {sum(c['match'] for c in checks)}/{len(checks)}")
                if not result["pass"]:
                    save_json("status.json",{"status":"stopped_baseline_mismatch","elapsed_seconds":time.perf_counter()-START})
                    return 2
            f.flush();progress(f"T={steps} complete; {len(raw)} cumulative raw rows")
    assert frame_sha(base)==base_fp
    assert SHA(source)==metadata["source_provenance"]["sha256"]
    input_after={p:{"bytes":Path(p).stat().st_size,"mtime_ns":Path(p).stat().st_mtime_ns,"sha256":SHA(p)} for p in CFG["input_data"]}
    assert input_after==input_manifest
    metadata.update(finished_at=datetime.datetime.now().isoformat(),elapsed_seconds=time.perf_counter()-START,raw_rows=len(raw),
        aggregate_rows=len(aggregate_rows),source_hash_unchanged=True,input_data_unchanged=True,sample_unchanged=True,
        prepared_input_integrity_checks=2*len(jobs)*len(CFG["opinion_steps"]),network_and_population_integrity_failures=0)
    save_json("provenance_complete.json",metadata)
    save_json("status.json",{"status":"complete","elapsed_seconds":time.perf_counter()-START,"raw_rows":len(raw),"baseline_pass":True})
    progress(f"DONE {len(raw)} raw rows, {len(aggregate_rows)} aggregate rows")
    return 0

if __name__=="__main__":
    try:
        raise SystemExit(main())
    except Exception:
        save_json("error.json",{"traceback":traceback.format_exc(),"elapsed_seconds":time.perf_counter()-START})
        raise
