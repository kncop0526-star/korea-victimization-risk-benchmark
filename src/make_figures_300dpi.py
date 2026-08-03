#!/usr/bin/env python3
"""Regenerate the five JASSS submission figures at 300 dpi with one shared style.

Referee 1 asked for two things: higher resolution and harmonized subpanels.
Content (data, panel structure, messages) is unchanged from the submitted figures.

Shared style:
- 300 dpi, width 6.5 in (print column width)
- Panel tags (A)(B)(C), bold, same size everywhere
- One color system across all figures:
    blue  #0072B2 = KVRB / synthetic / demographic coupling
    green #009E73 = real survey / external data
    verm  #D55E00 = inter-attribute joint / residual
    gray  #999999 = reference / marginal / population
- Okabe-Ito categorical set for the attribute palette in Figure 1
"""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

DATA = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

BLUE, GREEN, VERM, GRAY = "#0072B2", "#009E73", "#D55E00", "#999999"
# Okabe-Ito categorical (attributes, Figure 1)
CAT = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00"]

plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7,
    "axes.linewidth": 0.8, "figure.dpi": 300, "savefig.dpi": 300,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
    "axes.axisbelow": True,
})

def tag(ax, letter, title):
    ax.set_title(f"({letter}) {title}", loc="left", fontweight="bold", fontsize=8)

def save(fig, name):
    fig.savefig(OUT / name, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    from PIL import Image
    im = Image.open(OUT / name)
    print(f"{name:32} {im.width}x{im.height}px  (6.5in 기준 {round(im.width/6.5)}dpi)")

ATTR_LABEL = {
    "financial_vulnerability": "financial vulnerability",
    "digital_literacy": "digital literacy",
    "authority_deference": "authority deference",
    "social_isolation": "social isolation",
    "PVxRP (joint)": "victimization x reporting (joint)",
    "prior_victimization x reporting_propensity (joint)": "victimization x reporting (joint)",
}

# ── Figure 1: distributional fidelity ────────────────────────────────
def figure1():
    rep = pd.read_csv(DATA / "fidelity_report.csv", encoding="utf-8-sig")
    summ = pd.read_csv(DATA / "fidelity_summary.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(1, 3, figsize=(6.8, 2.5),
                           gridspec_kw={"width_ratios": [1.0, 1.15, 1.0]})

    # (A) anchor vs released P(level|cell) — 범례는 그림 하단 공동 범례로
    handles = []
    for i, (attr, g) in enumerate(rep.groupby("attr", sort=False)):
        h = ax[0].scatter(g["prob"], g["syn"], s=5, color=CAT[i % 6], alpha=0.8,
                          label=ATTR_LABEL.get(attr, attr), linewidths=0)
        handles.append(h)
    ax[0].plot([0, 1], [0, 1], ls="--", lw=0.7, color="black", zorder=0)
    ax[0].set_xlabel("anchor table  P(level | cell)")
    ax[0].set_ylabel("released  P(level | cell)")
    ax[0].set_xlim(0, 1); ax[0].set_ylim(0, 1)
    tag(ax[0], "A", f"By-construction fidelity\n(all cells x levels, n={len(rep)})")

    # (B) digital literacy by age band (lower education): bars = anchor, dots = released
    dl = rep[(rep["attr"] == "digital_literacy") & (rep["education_tier"] == "lower")]
    bands = list(dict.fromkeys(dl["age_band"]))
    x = np.arange(len(bands)); nlev = 5; w = 0.15
    greens = [plt.cm.Greens(0.3 + 0.14 * k) for k in range(nlev)]
    for k, lv in enumerate(range(1, nlev + 1)):
        sub = dl[dl["level"].astype(str) == str(lv)].set_index("age_band")
        ax[1].bar(x + (k - 2) * w, [sub.loc[b, "prob"] for b in bands], w, color=greens[k])
        ax[1].scatter(x + (k - 2) * w, [sub.loc[b, "syn"] for b in bands],
                      s=6, color=BLUE, zorder=3)
    ax[1].set_xticks(x); ax[1].set_xticklabels(bands, fontsize=6.5)
    ax[1].set_xlabel("age band"); ax[1].set_ylabel("P(level)")
    ax[1].set_ylim(0, 0.5)
    ax[1].text(0.02, 0.97, "bars = anchor (L1\u2192L5, light\u2192dark)\ndots = released",
               transform=ax[1].transAxes, va="top", fontsize=6.2,
               bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#cccccc", lw=0.5))
    tag(ax[1], "B", "Digital literacy by age\n(lower education)")

    # (C) weighted per-cell TVD by attribute
    s2 = summ.sort_values("weighted_TVD")
    labels = [ATTR_LABEL.get(a, a) for a in s2["attr"]]
    labels = [l.replace(" x reporting (joint)", " x reporting\n(joint)") for l in labels]
    ax[2].barh(labels, s2["weighted_TVD"], color=BLUE, height=0.6)
    for y, v in enumerate(s2["weighted_TVD"]):
        ax[2].text(v + 0.00008, y, f"{v:.4f}", va="center", fontsize=6)
    ax[2].tick_params(axis="y", labelsize=6.5)
    ax[2].set_xlabel("weighted mean per-cell TVD")
    ax[2].set_xlim(0, 0.0046)
    ax[2].set_xticks([0, 0.002, 0.004])
    ax[2].set_xticklabels(["0", "0.002", "0.004"])
    tag(ax[2], "C", "Residual sampling deviation\n(lower = tighter match)")

    fig.suptitle("Distributional fidelity of the released attributes against their anchor tables",
                 fontsize=9, y=1.02)
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=6,
               bbox_to_anchor=(0.5, -0.06), frameon=False, columnspacing=1.0,
               handletextpad=0.2, markerscale=1.6)
    fig.tight_layout()
    save(fig, "Figure1_fidelity.png")

# ── Figure 2: external joint validation ──────────────────────────────
def figure2():
    d = json.load(open(DATA / "joint_external_noin2023_full.json", encoding="utf-8"))
    r, s = d["real"], d["synth"]
    fig, ax = plt.subplots(1, 2, figsize=(6.5, 2.5))

    catsA = ["FV high", "DL low", "SI high", "simult.\nextreme", "indep.\nimplied"]
    keys = ["share_FVhi", "share_DLlo", "share_SIhi",
            "simultaneous_extreme_rate", "independence_implied_rate"]
    x = np.arange(len(catsA)); w = 0.38
    ax[0].bar(x - w/2, [r[k] * 100 for k in keys], w, color=GREEN,
              label="real (Survey of Older Koreans 2023)")
    ax[0].bar(x + w/2, [s[k] * 100 for k in keys], w, color=BLUE,
              label="released (KVRB)")
    ax[0].set_xticks(x); ax[0].set_xticklabels(catsA)
    ax[0].set_ylabel("% of elderly (65+)")
    ax[0].legend(loc="upper right")
    ax[0].annotate("DL low: 35% released vs 37% real\n(was 85% before recalibration)",
                   xy=(1 + w/2, s["share_DLlo"] * 100), xytext=(1.5, 52),
                   fontsize=6.5, arrowprops=dict(arrowstyle="->", color="gray", lw=0.7))
    tag(ax[0], "A", "Marginals and joint tail")

    catsB = ["FV x SI", "FV x DL", "DL x SI"]
    rb = [r["V_fv_si"], r["V_fv_dl"], r["V_dl_si"]]
    sb = [s["V_fv_si"], s["V_fv_dl"], s["V_dl_si"]]
    xb = np.arange(len(catsB))
    ax[1].bar(xb - w/2, rb, w, color=GREEN, label="real")
    ax[1].bar(xb + w/2, sb, w, color=BLUE, label="released (KVRB)")
    for xi, v in zip(xb - w/2, rb):
        ax[1].text(xi, v + 0.004, f"{v:.2f}", ha="center", fontsize=6.5)
    for xi, v in zip(xb + w/2, sb):
        ax[1].text(xi, v + 0.004, f"{v:.2f}", ha="center", fontsize=6.5)
    ax[1].set_xticks(xb); ax[1].set_xticklabels(catsB)
    ax[1].set_ylabel("Cramer's V"); ax[1].set_ylim(0, 0.25)
    ax[1].legend(loc="upper right")
    tag(ax[1], "B", "Inter-attribute dependence (real > released)")

    fig.suptitle("External joint validation against the 2023 National Survey of Older Koreans (65+):\n"
                 "compound-extreme dependence 2.30x real (95% CI 2.12-2.49) vs 1.29x released",
                 fontsize=9, y=1.10)
    fig.tight_layout()
    save(fig, "Figure2_external_joint.png")

# ── Figure 3: protected-attribute audit ──────────────────────────────
def figure3():
    d = pd.read_csv(DATA / "stereotype_audit_v3.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(1, 2, figsize=(6.5, 2.5), sharey=True)
    for k, (prot, letter) in enumerate([("sex", "A"), ("province", "B")]):
        sub = d[d["protected"] == prot]
        labels = [a.replace("_", " ") for a in sub["attr"]]
        y = np.arange(len(labels)); h = 0.38
        ax[k].barh(y - h/2, sub["marginal_V"], h, color=GRAY, label="marginal V")
        ax[k].barh(y + h/2, sub["residual_V"], h, color=VERM,
                   label="residual V (within justified cells)")
        for yi, v in zip(y + h/2, sub["residual_V"]):
            ax[k].text(v + 0.002, yi, f"{v:.3f}", va="center", fontsize=6)
        ax[k].set_yticks(y); ax[k].set_yticklabels(labels)
        ax[k].invert_yaxis()
        ax[k].set_xlim(0, 0.165)
        ax[k].set_xlabel("Cramer's V")
        tag(ax[k], letter, f"attribute x {prot}")
        if k == 1:
            ax[k].legend(loc="upper right", framealpha=0.95)
    fig.suptitle("Protected-attribute audit: residual association after conditioning on survey-justified cells",
                 fontsize=9, y=1.04)
    fig.tight_layout()
    save(fig, "Figure3_protected_audit.png")

# ── Figure 4: cohort query ───────────────────────────────────────────
def figure4():
    prof = pd.read_csv(DATA / "cohort_profile.csv", encoding="utf-8-sig")
    dl_path = DATA / "cohort_dl_distribution.csv"
    has_b = dl_path.exists()
    fig, ax = plt.subplots(1, 2, figsize=(6.5, 2.6),
                           gridspec_kw={"width_ratios": [1.5, 1]})

    y = np.arange(len(prof)); h = 0.38
    ax[0].barh(y - h/2, prof["cohort_share"], h, color=BLUE,
               label="elderly cohort (n=44,362)")
    ax[0].barh(y + h/2, prof["population_share"], h, color=GRAY,
               label="full population (n=1,000,000)")
    for yi, (v, lift) in enumerate(zip(prof["cohort_share"], prof["lift"])):
        ax[0].text(v + 0.01, yi - h/2, f"{v:.2f}", va="center", fontsize=6)
        ax[0].text(0.99, yi, f"x{lift:g}", va="center", ha="right", fontsize=6.5, color="#444444")
    ax[0].set_yticks(y); ax[0].set_yticklabels(prof["dimension"], fontsize=7)
    ax[0].invert_yaxis()
    ax[0].set_xlim(0, 1.0)
    ax[0].set_xlabel("share in high-risk band")
    ax[0].legend(loc="lower center")
    tag(ax[0], "A", "Behavioral risk profile (share at risk)")

    if has_b:
        dl = pd.read_csv(dl_path, encoding="utf-8-sig")
        xb = np.arange(len(dl)); w = 0.38
        ax[1].bar(xb - w/2, dl["cohort"], w, color=BLUE, label="elderly cohort")
        ax[1].bar(xb + w/2, dl["population"], w, color=GRAY, label="population")
        ax[1].set_xticks(xb)
        ax[1].set_xticklabels([f"L{int(v)}" for v in dl["level"]])
        ax[1].set_xlabel("digital-literacy level (1 = lowest)")
        ax[1].set_ylabel("share")
        ax[1].legend(loc="upper right")
    else:
        ax[1].text(0.5, 0.5, "PANEL B PENDING\nrun dump_cohort_dl.py on the data PC\nto produce cohort_dl_distribution.csv",
                   ha="center", va="center", fontsize=8, color="red",
                   transform=ax[1].transAxes)
        ax[1].set_xticks([]); ax[1].set_yticks([])
    tag(ax[1], "B", "Digital literacy: cohort vs population")

    fig.suptitle("Cohort query: compound-vulnerability cohort (age >= 65, single-person, lower education)",
                 fontsize=9, y=1.04)
    fig.text(0.5, -0.04,
             "The profile follows by construction from survey conditionals tied to the cohort's demographics"
             " - a usage demonstration, not an independent finding.",
             ha="center", fontsize=6.5, style="italic", color="#555555")
    fig.tight_layout()
    save(fig, "Figure4_cohort.png" if has_b else "Figure4_cohort_DRAFT_panelB_pending.png")

# ── Figure 5: decomposition ──────────────────────────────────────────
def figure5():
    dec = pd.read_csv(DATA / "abm_decompose.csv")
    swp = pd.read_csv(DATA / "abm_sweep.csv")
    fig, ax = plt.subplots(1, 3, figsize=(6.5, 2.2))

    for k, (topo, letter, title) in enumerate([
            ("smallworld", "A", "Small-world:\ncoupling drives the gap"),
            ("scalefree", "B", "Scale-free:\nthe gap vanishes")]):
        sub = dec[dec["topology"] == topo]
        x = np.arange(len(sub)); w = 0.38
        ax[k].bar(x - w/2, sub["coupling_pp"], w, yerr=sub["coupling_CI"],
                  color=BLUE, error_kw={"lw": 0.7}, label="demographic coupling")
        ax[k].bar(x + w/2, sub["joint_pp"], w, yerr=sub["joint_CI"],
                  color=VERM, error_kw={"lw": 0.7}, label="inter-attribute joint")
        ax[k].axhline(0, lw=0.7, color="black")
        ax[k].set_xticks(x); ax[k].set_xticklabels(sub["threshold"])
        ax[k].set_xlabel("contagion threshold")
        ax[k].set_ylim(-8.5, 8.5)
        if k == 0:
            ax[k].set_ylabel("reach-gap component (pp)")
            ax[k].legend(loc="lower left")
        tag(ax[k], letter, title)

    labels = [f"{'sf' if t == 'scalefree' else 'sw'}\n{th}"
              for t, th in zip(swp["topology"], swp["threshold"])]
    order = np.argsort([l.startswith("sw") for l in labels], kind="stable")
    swp2 = swp.iloc[order]; labels2 = [labels[i] for i in order]
    ax[2].bar(np.arange(len(swp2)), swp2["inject_minus_indep_pp"], 0.6, color=GREEN)
    ax[2].axhline(0, lw=0.7, color="black")
    ax[2].set_xticks(np.arange(len(swp2))); ax[2].set_xticklabels(labels2, fontsize=6.5)
    ax[2].set_ylabel("reach change (pp)")
    ax[2].set_ylim(0, 1.4)
    tag(ax[2], "C", "Injected 2.30x joint:\nreach moves <= 1.2 pp")

    fig.suptitle("Decomposition of the fused structure under threshold contagion (30 seeds per cell, 95% CI)",
                 fontsize=9, y=1.06)
    fig.tight_layout()
    save(fig, "Figure5_decomposition.png")

if __name__ == "__main__":
    figure1(); figure2(); figure3(); figure4(); figure5()
    print("done")
