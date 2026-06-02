# -*- coding: utf-8 -*-
"""Non-elderly inter-attribute joint: feasibility of external validation + synthetic dependence
(reviewers: the 19-64 core joint rests on conditional independence). Finding: KGSS administers the
authority-deference battery (2016) and the social-isolation support battery (2004,2012) to DISJOINT
respondents, so AD x SI is never jointly observed -> the non-elderly joint cannot be validated, only
assumed (statistical matching; D'Orazio 2006, Rassler 2002). Reports per-age-group synthetic
dependence (near-independence by construction) for the released 1M. Writes results/nonelderly_joint_bound.txt."""
import glob, numpy as np, pandas as pd, pyreadstat, sys
def cramers_v(a,b,w=None):
    a,b=pd.Series(a),pd.Series(b); w=pd.Series(np.ones(len(a)) if w is None else w)
    m=a.notna()&b.notna(); a,b,w=a[m],b[m],w[m]
    if a.nunique()<2 or b.nunique()<2: return float("nan")
    tab=pd.crosstab(a,b,values=w,aggfunc="sum").fillna(0.0).values.astype(float)
    n=tab.sum(); r=tab.sum(1,keepdims=True); c=tab.sum(0,keepdims=True); exp=r@c/n
    chi2=np.nansum((tab-exp)**2/np.where(exp==0,np.nan,exp)); k=min(tab.shape)-1
    return float(np.sqrt(chi2/(n*k)))
def dep_ratio(x,y,thr=4):
    aH=x>=thr; sH=y>=thr; pa=aH.mean(); ps=sH.mean(); pj=(aH&sH).mean()
    return pj/(pa*ps) if pa>0 and ps>0 else float("nan")
def synth(parts):
    s=pd.concat([pd.read_parquet(p,columns=["age","attr_authority_deference","attr_social_isolation",
        "attr_financial_vulnerability","attr_digital_literacy"]) for p in parts],ignore_index=True)
    s["age"]=pd.to_numeric(s.age,errors="coerce"); return s
if __name__=="__main__":
    parts=sorted(glob.glob(sys.argv[1] if len(sys.argv)>1 else "data/processed/enriched_1M_v4_parts/*.parquet"))
    s=synth(parts); lines=["Non-elderly inter-attribute joint (synthetic dependence, near-independence by construction):"]
    for lab,lo,hi in [("non-elderly <65",0,64),("elderly 65+",65,200)]:
        d=s[(s.age>=lo)&(s.age<=hi)]
        for x,y in [("attr_authority_deference","attr_social_isolation"),
                    ("attr_financial_vulnerability","attr_social_isolation"),
                    ("attr_digital_literacy","attr_financial_vulnerability")]:
            lines.append(f"  {lab:16} {x.replace('attr_','')[:6]} x {y.replace('attr_','')[:6]:6} "
                         f"V={cramers_v(d[x],d[y]):.3f} dep-ratio(>=4)={dep_ratio(d[x].values,d[y].values):.2f}")
    print("\n".join(lines))
