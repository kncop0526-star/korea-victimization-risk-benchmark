"""fig_external_joint.py - replot F7 (external joint validation) with English labels
from the precomputed results_v4/joint_external_noin2023_full.json. No survey re-run."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

d = json.load(open("results_v4/joint_external_noin2023_full.json", encoding="utf-8"))
r, s = d["real"], d["synth"]
out = Path("results_v4/F7_external_joint_noin2023.png")

fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
# Panel A: marginals & joint tail
catsA = ["FV high", "DL low", "SI high", "simul.\nextreme", "indep.\nimplied"]
realA = [r["share_FVhi"], r["share_DLlo"], r["share_SIhi"],
         r["simultaneous_extreme_rate"], r["independence_implied_rate"]]
synA = [s["share_FVhi"], s["share_DLlo"], s["share_SIhi"],
        s["simultaneous_extreme_rate"], s["independence_implied_rate"]]
x = np.arange(len(catsA)); w = 0.38
ax[0].bar(x - w/2, np.array(realA)*100, w, label="real (Survey of Older Koreans 2023)", color="#1b9e77")
ax[0].bar(x + w/2, np.array(synA)*100, w, label="synthetic (KVRB)", color="#7aa6d6")
ax[0].set_xticks(x); ax[0].set_xticklabels(catsA)
ax[0].set_ylabel("% of elderly (65+)")
ax[0].set_title("Marginals and joint tail (digital literacy recalibrated)")
ax[0].legend(fontsize=8)
ax[0].annotate("DL low: 35% (synthetic) vs 37% (real)\n(was 85% before recalibration)",
               xy=(1+ w/2, s["share_DLlo"]*100), xytext=(1.1, 60),
               fontsize=8, arrowprops=dict(arrowstyle="->", color="grey"))
# Panel B: inter-attribute dependence (Cramer's V)
catsB = ["FV x SI", "FV x DL", "DL x SI"]
realB = [r["V_fv_si"], r["V_fv_dl"], r["V_dl_si"]]
synB = [s["V_fv_si"], s["V_fv_dl"], s["V_dl_si"]]
xb = np.arange(len(catsB))
ax[1].bar(xb - w/2, realB, w, label="real", color="#1b9e77")
ax[1].bar(xb + w/2, synB, w, label="synthetic (KVRB)", color="#7aa6d6")
ax[1].set_xticks(xb); ax[1].set_xticklabels(catsB)
ax[1].set_ylabel("Cramer's V")
ax[1].set_title("Inter-attribute dependence (real > released)")
ax[1].legend(fontsize=8)
fig.suptitle("External joint validation: KVRB vs National Survey of Older Koreans (2023), aged 65+  |  "
             "compound-extreme dependence 2.30x (95% CI 2.12-2.49) real vs 1.29x released",
             fontsize=10.5, y=1.02)
fig.tight_layout()
fig.savefig(out, dpi=130, bbox_inches="tight")
print("[fig]", out)
