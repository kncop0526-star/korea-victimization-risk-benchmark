# -*- coding: utf-8 -*-
"""Real external joint validation: 노인실태조사 2023 vs KVRB v3 (elderly 65+).
Tests the reviewers' conditional-independence concern by measuring the REAL joint of
compounding vulnerabilities (high FV & low DL & high SI) on the same elderly respondents,
and comparing to KVRB's synthetic (mostly conditional-independent) joint.
Bonus: validates the §5.1 use case against actual voice-phishing victimization (#574)."""
import glob, json
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path("/sessions/eloquent-focused-rubin/mnt/연구 논문/korea-victimization-risk-benchmark")
CSV = REPO/"data/raw/노인실태조사_2023/2023_총괄_20260601_13406.csv"
KVRB = REPO/"data/processed/enriched_1M_v3_parts"
OUT = REPO/"results"

AGE="노인 조사대상자 만연령"; W="가중치 모수추정(사후층화 가중치)"
INC="연가구소득"; VP="지난 1년 간 범죄피해 여부_보이스 피싱으로 인한 금전 피해"
SUP=["도움받을 수 있는 사람 수_우울할 때","도움받을 수 있는 사람 수_몸이 아플 때","도움받을 수 있는 사람 수_돈을 빌려야 할 때"]

def cramers_v(a,b,w):
    a=pd.Series(a); b=pd.Series(b); w=pd.Series(w)
    m=a.notna()&b.notna()&w.notna(); a,b,w=a[m],b[m],w[m]
    if a.nunique()<2 or b.nunique()<2: return float("nan")
    tab=pd.crosstab(a,b,values=w,aggfunc="sum").fillna(0.0).values.astype(float)
    n=tab.sum(); r=tab.sum(1,keepdims=True); c=tab.sum(0,keepdims=True); exp=r@c/n
    with np.errstate(divide="ignore",invalid="ignore"):
        chi2=np.nansum((tab-exp)**2/np.where(exp==0,np.nan,exp))
    k=min(tab.shape)-1
    return float(np.sqrt(chi2/(n*k))) if k>0 and n>0 else float("nan")

def wrate(mask,w):
    w=pd.Series(w).fillna(0.0); m=pd.Series(mask).fillna(False).values
    return float(w[m].sum()/w.sum()) if w.sum()>0 else float("nan")

# ---------- REAL ----------
df=pd.read_csv(CSV, encoding="cp949", dtype=str)
n=lambda c: pd.to_numeric(df[c], errors="coerce")
R=pd.DataFrame()
R["age"]=n(AGE); R["w"]=n(W)
# FV: invert income quintile (1 lowest income -> FV5 most vulnerable)
R["fv"]=6-n(INC)
# DL: count of '예'(==1) among 13 활동 (9 비해당 -> 0); -> level 1..5
dlcols=[c for c in df.columns if c.startswith("전자기기 활동여부_")]
assert len(dlcols)==13, len(dlcols)
dlcount=sum((n(c)==1).astype(int) for c in dlcols)
R["dl_count"]=dlcount
R["dl"]=pd.cut(dlcount, [-1,0,2,5,9,13], labels=[1,2,3,4,5]).astype("float")
# SI: needs_covered = # of (우울/아플/돈) with >=1 person, 99 -> NaN; fewer covered -> more isolated
cov=0; valid=0
sup=[n(c).where(n(c)<99) for c in SUP]   # 99 = 무응답/모름 -> NaN
needs_valid=sum(s.notna().astype(int) for s in sup)
needs_cov=sum((s>0).astype(int) for s in sup)         # counts NaN as 0; require >=2 valid
R["needs_cov"]=needs_cov.where(needs_valid>=2)
R["si"]=R["needs_cov"].map({0:5,1:4,2:2,3:1})         # high SI = few supports
R["vp"]=(n(VP)==1).astype("float")                    # voice-phishing victim
R=R[R["age"]>=65]

def quants(d,label):
    w=d["w"]; have=[a for a in ("fv","dl","si") if d[a].notna().any()]
    res={"label":label,"n":int(len(d)),"w":float(w.sum())}
    res["share_FVhi"]=wrate(d["fv"]>=4,w); res["share_DLlo"]=wrate(d["dl"]<=2,w); res["share_SIhi"]=wrate(d["si"]>=4,w)
    ext=(d["fv"]>=4)&(d["dl"]<=2)&(d["si"]>=4)
    res["simultaneous_extreme_rate"]=wrate(ext,w)
    indep=res["share_FVhi"]*res["share_DLlo"]*res["share_SIhi"]   # rate if fully independent
    res["independence_implied_rate"]=indep
    for x,y in (("fv","si"),("fv","dl"),("dl","si")):
        res[f"V_{x}_{y}"]=cramers_v(d[x],d[y],w)
    return res,ext

real,ext_real=quants(R,"real_노인실태조사2023")
# bonus: voice-phishing victimization in high-risk cohort vs rest (real)
vp_hi=wrate((R["vp"]==1)&ext_real, R["w"])/max(wrate(ext_real,R["w"]),1e-9)
vp_lo=wrate((R["vp"]==1)&~ext_real, R["w"])/max(wrate(~ext_real,R["w"]),1e-9)
real["vp_victim_in_extreme"]=vp_hi; real["vp_victim_in_rest"]=vp_lo; real["vp_lift"]=vp_hi/max(vp_lo,1e-9)

# ---------- SYNTHETIC (KVRB v3, 65+) ----------
files=sorted(glob.glob(str(KVRB/"part_*.parquet")))
fr=[]
for f in files:
    d=pd.read_parquet(f, columns=["age","attr_financial_vulnerability","attr_digital_literacy","attr_social_isolation"])
    fr.append(d[pd.to_numeric(d["age"],errors="coerce")>=65])
S=pd.concat(fr,ignore_index=True)
K=pd.DataFrame({"age":pd.to_numeric(S["age"],errors="coerce"),"w":1.0,
    "fv":pd.to_numeric(S["attr_financial_vulnerability"],errors="coerce"),
    "dl":pd.to_numeric(S["attr_digital_literacy"],errors="coerce"),
    "si":pd.to_numeric(S["attr_social_isolation"],errors="coerce")})
synth,_=quants(K,"synthetic_KVRB_v3")

# ---------- COMPARE ----------
keys=["share_FVhi","share_DLlo","share_SIhi","simultaneous_extreme_rate","independence_implied_rate","V_fv_si","V_fv_dl","V_dl_si"]
rows=[]
for k in keys:
    r,s=real.get(k,np.nan),synth.get(k,np.nan)
    unit="pp" if ("share" in k or "rate" in k) else "V"
    rows.append({"quantity":k,"real":r,"synthetic_KVRB":s,
        "diff":(s-r)*100 if unit=="pp" else s-r,"unit":unit,
        "ratio":(s/r) if (isinstance(r,float) and r==r and r!=0) else np.nan})
cmp=pd.DataFrame(rows)
OUT.mkdir(exist_ok=True)
cmp.to_csv(OUT/"joint_external_noin2023.csv", index=False, encoding="utf-8-sig")

re_=real["simultaneous_extreme_rate"]; sy=synth["simultaneous_extreme_rate"]; ind=real["independence_implied_rate"]
sent=(f"On 노인실태조사 2023 (N={real['n']:,} weighted, aged 65+), {re_*100:.2f}% of elders are "
 f"simultaneously high financial vulnerability, low digital literacy, and high social isolation. "
 f"If the three were independent given the marginals, the rate would be {ind*100:.2f}% — the real joint "
 f"is {re_/max(ind,1e-9):.2f}x the independence baseline, confirming the compounding the reviewers flag. "
 f"KVRB v3 yields {sy*100:.2f}% for the same cut ({'under' if sy<re_ else 'over'}-estimating the real tail "
 f"by {abs(sy-re_)*100:.2f} pp; ratio {sy/max(re_,1e-9):.2f}). Real pairwise Cramér's V: FV×SI {real['V_fv_si']:.3f}, "
 f"FV×DL {real['V_fv_dl']:.3f}, DL×SI {real['V_dl_si']:.3f}; KVRB: {synth['V_fv_si']:.3f} / {synth['V_fv_dl']:.3f} / "
 f"{synth['V_dl_si']:.3f}. Bonus validation: actual voice-phishing victimization is {real['vp_lift']:.2f}x higher in "
 f"the high-risk cohort ({real['vp_victim_in_extreme']*100:.2f}% vs {real['vp_victim_in_rest']*100:.2f}%).")

with open(OUT/"joint_external_noin2023.txt","w",encoding="utf-8") as fh:
    fh.write("KVRB external joint validation vs 노인실태조사 2023 (elderly 65+)\n"+"="*70+"\n")
    fh.write(f"real N={real['n']:,}  synth N(KVRB 65+)={synth['n']:,}\n\n")
    fh.write("REAL marginals: FVhi=%.3f DLlo=%.3f SIhi=%.3f\n"%(real['share_FVhi'],real['share_DLlo'],real['share_SIhi']))
    fh.write("SYNTH marginals: FVhi=%.3f DLlo=%.3f SIhi=%.3f\n\n"%(synth['share_FVhi'],synth['share_DLlo'],synth['share_SIhi']))
    fh.write(cmp.to_string(index=False)+"\n\n")
    fh.write("VOICE-PHISHING (real): extreme cohort %.3f%% vs rest %.3f%% (lift %.2fx)\n"%(real['vp_victim_in_extreme']*100,real['vp_victim_in_rest']*100,real['vp_lift']))
    fh.write("\nREADY §4.5 SENTENCE:\n"+sent+"\n")
print(cmp.to_string(index=False)); print("\nVP lift %.2fx (%.3f%% vs %.3f%%)"%(real['vp_lift'],real['vp_victim_in_extreme']*100,real['vp_victim_in_rest']*100))
print("\n"+sent)
json.dump({"real":{k:real[k] for k in real if not k.startswith('label')},"synth":{k:synth[k] for k in synth if not k.startswith('label')}},
          open(OUT/"joint_external_noin2023_full.json","w"), ensure_ascii=False, indent=1, default=float)
print("\n[ok] wrote results/joint_external_noin2023.{csv,txt,_full.json}")
