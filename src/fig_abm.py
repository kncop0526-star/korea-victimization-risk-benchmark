"""Comprehensive ABM figure: (A) illustrative diffusion curves (small-world),
(B) reach gap vs adoption threshold by topology (95% CI), (C) compound-cohort
reach ratio vs threshold by topology. Reads results_v4/abm_demo_curves.csv and
results_v4/abm_robustness.csv. No re-run."""
from pathlib import Path
import pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

cur=pd.read_csv("results_v4/abm_demo_curves.csv")
rob=pd.read_csv("results_v4/abm_robustness.csv")
out=Path("results_v4/F8_abm_demo.png")
col={"smallworld":"#c0392b","scalefree":"#2c7fb8"}
nm={"smallworld":"small-world (clustered)","scalefree":"scale-free (hubs)"}

fig,ax=plt.subplots(1,3,figsize=(15,4.3))
# A: diffusion curves
xs=cur["step"]
ax[0].plot(xs,cur["reach_KVRB"]*100,"-o",ms=3,color="#c0392b",label="KVRB (structured)")
ax[0].plot(xs,cur["reach_shuffled"]*100,"--s",ms=3,color="#7f8c8d",label="shuffled (marginals only)")
ax[0].set_xlabel("step"); ax[0].set_ylabel("cumulative reach (%)")
ax[0].set_title("(A) Diffusion, small-world (one run)"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
# B: gap vs threshold
for topo,g in rob.groupby("topology"):
    g=g.sort_values("threshold")
    ax[1].errorbar(g["threshold"],g["gap_pp_mean"],yerr=g["gap_pp_CI"],marker="o",capsize=3,color=col[topo],label=nm[topo])
ax[1].axhline(0,color="grey",lw=.8); ax[1].set_xlabel("adoption threshold")
ax[1].set_ylabel("reach gap KVRB - shuffled (pp)")
ax[1].set_title("(B) Reach gap by topology (30 seeds, 95% CI)"); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
# C: cohort ratio vs threshold
for topo,g in rob.groupby("topology"):
    g=g.sort_values("threshold")
    ax[2].errorbar(g["threshold"],g["cohort_ratio_mean"],yerr=g["cohort_ratio_CI"],marker="s",capsize=3,color=col[topo],label=nm[topo])
ax[2].axhline(1,color="grey",lw=.8); ax[2].set_xlabel("adoption threshold")
ax[2].set_ylabel("compound-cohort reach ratio")
ax[2].set_title("(C) Compound-cohort under-reach by topology"); ax[2].legend(fontsize=8); ax[2].grid(alpha=.3)
fig.suptitle("KVRB-initialized diffusion: behavioural joint structure shifts reach only in clustered networks above a contagion threshold",fontsize=10.5,y=1.02)
fig.tight_layout(); fig.savefig(out,dpi=125,bbox_inches="tight"); print("[fig]",out)
