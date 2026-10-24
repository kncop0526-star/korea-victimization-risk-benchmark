#!/usr/bin/env python3
"""Regenerate the five JASSS figures at 300 dpi with one shared style (R2 revision).

R2 changes (JASSS 2026:161:2):
- One colour rule across all five figures, stated in the Figure 1 caption:
    blue   #0072B2 = released KVRB population (and the demographic coupling it carries)
    green  #009E73 = real survey / anchor table
    verm.  #D55E00 = inter-attribute joint
    grey   #999999 = reference series (full population, marginal V)
- Figure 1A pooled in one colour (per-attribute deviation is shown in 1C); shared legend removed.
- Figure 1B: in-plot text box replaced by a compact legend; wider panel so tick labels do not collide.
- Figure 2: one shared legend above the panels; nothing overlaps the bars.
- Figure 3: residual V drawn in blue (a property of the released population), marginal V in grey.
- Figure 4: panel B uses horizontal bars like panel A; one shared legend.
- Figure 5C: drawn from the same runs as Table 5 (abm_discriminate_grid.csv), in vermilion.
- Data paths point at the released result folders, so the script runs from a clone.
- After drawing, every legend is tested against bars, points, and labels; overlaps are printed.

Run from anywhere:  python src/make_figures_300dpi.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.transforms import blended_transform_factory

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "results_v4"           # released population (Zenodo v4)
OUT = ROOT / "submission_R2" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

BLUE, GREEN, VERM, GRAY = "#0072B2", "#009E73", "#D55E00", "#999999"

plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.linewidth": 0.8, "figure.dpi": 300, "savefig.dpi": 300,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
    "axes.axisbelow": True,
})

REPORT = []


def tag(ax, letter, title):
    ax.set_title(f"({letter}) {title}", loc="left", fontweight="bold", fontsize=8)


def _artist_boxes(ax, r):
    boxes = []
    for p in ax.patches:
        bb = p.get_window_extent(r)
        if bb.width > 0.5 and bb.height > 0.5:
            boxes.append(("bar", bb))
    for c in ax.collections:
        offs = c.get_offsets()
        if len(offs):
            pts = c.get_offset_transform().transform(offs)
            for x, y in pts:
                from matplotlib.transforms import Bbox
                boxes.append(("point", Bbox([[x - 2, y - 2], [x + 2, y + 2]])))
    for t in ax.texts:
        if t.get_text().strip():
            boxes.append(("text", t.get_window_extent(r)))
    return boxes


def check_layout(fig, name):
    """Legend-vs-data overlap and tick-label collision test (pixel boxes at 300 dpi)."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    legends = [lg for lg in fig.legends]
    legends += [ax.get_legend() for ax in fig.axes if ax.get_legend() is not None]
    hits = 0
    for lg in legends:
        lb = lg.get_window_extent(r)
        for ax in fig.axes:
            for kind, bb in _artist_boxes(ax, r):
                if lb.overlaps(bb):
                    hits += 1
        fs = min(t.get_fontsize() for t in lg.get_texts())
        if fs < 7:
            REPORT.append(f"{name}: legend font {fs}pt < 7pt")
    tick_hits = 0
    for ax in fig.axes:
        labs = [t for t in ax.get_xticklabels() if t.get_text()]
        bbs = [t.get_window_extent(r) for t in labs]
        for i in range(len(bbs) - 1):
            if bbs[i].overlaps(bbs[i + 1]):
                tick_hits += 1
    REPORT.append(f"{name}: legends={len(legends)} legend-overlaps={hits} xtick-collisions={tick_hits}")


def top_legend(fig, handles, suptitle, top=0.84, ncol=2):
    """Lay out panels below `top`, the shared legend just above them, the title above the legend."""
    fig.tight_layout(rect=(0, 0, 1, top))
    lg = fig.legend(handles=handles, loc="lower center", ncol=ncol, frameon=False,
                    bbox_to_anchor=(0.5, top), borderaxespad=0.1)
    fig.canvas.draw()
    bb = lg.get_window_extent(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
    fig.suptitle(suptitle, fontsize=9, y=bb.y1 + 0.01, va="bottom")


def save(fig, name):
    check_layout(fig, name)
    fig.savefig(OUT / name, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    from PIL import Image
    im = Image.open(OUT / name)
    print(f"{name:32} {im.width}x{im.height}px")


ATTR_LABEL = {
    "financial_vulnerability": "financial vulnerability",
    "digital_literacy": "digital literacy",
    "authority_deference": "authority deference",
    "social_isolation": "social isolation",
    "PVxRP (joint)": "victimization x reporting (joint)",
}


# ── Figure 1: distributional fidelity ────────────────────────────────
def figure1():
    rep = pd.read_csv(V4 / "fidelity_report.csv", encoding="utf-8-sig")
    summ = pd.read_csv(V4 / "fidelity_summary.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.7),
                           gridspec_kw={"width_ratios": [1.0, 1.4, 1.15]})

    # (A) anchor vs released P(level|cell), all attributes pooled
    ax[0].scatter(rep["prob"], rep["syn"], s=5, color=BLUE, alpha=0.7, linewidths=0)
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
    ax[1].set_ylim(0, 0.56)
    ax[1].legend(handles=[Patch(color=greens[2], label="anchor"),
                          Line2D([], [], marker="o", ls="", color=BLUE, markersize=3.5,
                                 label="released")],
                 loc="upper center", ncol=2, frameon=False, handlelength=1.0,
                 columnspacing=0.8, handletextpad=0.4, borderaxespad=0.2)
    tag(ax[1], "B", "Digital literacy by age\n(lower education)")

    # (C) weighted per-cell TVD by attribute
    s2 = summ.sort_values("weighted_TVD")
    labels = [ATTR_LABEL.get(a, a) for a in s2["attr"]]
    labels = [l.replace(" x reporting (joint)", " x\nreporting (joint)").replace(" ", "\n", 1)
              if " x" not in l else l.replace(" x reporting (joint)", " x\nreporting (joint)")
              for l in labels]
    ax[2].barh(labels, s2["weighted_TVD"], color=BLUE, height=0.6)
    for y, v in enumerate(s2["weighted_TVD"]):
        ax[2].text(v + 0.00008, y, f"{v:.4f}", va="center", fontsize=6.5)
    ax[2].tick_params(axis="y", labelsize=7)
    ax[2].set_xlabel("weighted mean per-cell TVD")
    ax[2].set_xlim(0, 0.0048)
    ax[2].set_xticks([0, 0.002, 0.004]); ax[2].set_xticklabels(["0", "0.002", "0.004"])
    tag(ax[2], "C", "Residual sampling deviation\n(lower = tighter match)")

    fig.suptitle("Distributional fidelity of the released attributes against their anchor tables",
                 fontsize=9, y=1.02)
    fig.tight_layout()
    save(fig, "Figure1_fidelity.png")


# ── Figure 2: external joint validation ──────────────────────────────
def figure2():
    d = json.load(open(V4 / "joint_external_noin2023_full.json", encoding="utf-8"))
    r, s = d["real"], d["synth"]
    fig, ax = plt.subplots(1, 2, figsize=(6.8, 2.6))

    catsA = ["FV high", "DL low", "SI high", "all three\nat once", "expected if\nindependent"]
    keys = ["share_FVhi", "share_DLlo", "share_SIhi",
            "simultaneous_extreme_rate", "independence_implied_rate"]
    x = np.arange(len(catsA)); w = 0.38
    ax[0].bar(x - w/2, [r[k] * 100 for k in keys], w, color=GREEN)
    ax[0].bar(x + w/2, [s[k] * 100 for k in keys], w, color=BLUE)
    ax[0].set_xticks(x); ax[0].set_xticklabels(catsA, fontsize=6.5)
    ax[0].set_ylabel("% of elderly (65+)")
    ax[0].set_ylim(0, 62)
    ax[0].annotate("DL low: 35% released vs 37% real\n(85% before recalibration)",
                   xy=(1 + w/2, s["share_DLlo"] * 100 + 0.8), xytext=(1.75, 49),
                   fontsize=6.5, arrowprops=dict(arrowstyle="->", color="gray", lw=0.7))
    tag(ax[0], "A", "Marginals and joint tail")

    catsB = ["FV x SI", "FV x DL", "DL x SI"]
    rb = [r["V_fv_si"], r["V_fv_dl"], r["V_dl_si"]]
    sb = [s["V_fv_si"], s["V_fv_dl"], s["V_dl_si"]]
    xb = np.arange(len(catsB))
    ax[1].bar(xb - w/2, rb, w, color=GREEN)
    ax[1].bar(xb + w/2, sb, w, color=BLUE)
    for xi, v in zip(xb - w/2, rb):
        ax[1].text(xi, v + 0.004, f"{v:.2f}", ha="center", fontsize=6.5)
    for xi, v in zip(xb + w/2, sb):
        ax[1].text(xi, v + 0.004, f"{v:.2f}", ha="center", fontsize=6.5)
    ax[1].set_xticks(xb); ax[1].set_xticklabels(catsB)
    ax[1].set_ylabel("Cramer's V"); ax[1].set_ylim(0, 0.25)
    tag(ax[1], "B", "Inter-attribute dependence (real > released)")

    top_legend(fig, [Patch(color=GREEN, label="real survey (National Survey of Older Koreans 2023)"),
                     Patch(color=BLUE, label="released population (KVRB)")],
               "External joint validation against the 2023 National Survey of Older Koreans (65+):\n"
               "compound-extreme dependence 2.30x real (95% CI 2.12-2.49) vs 1.29x released")
    save(fig, "Figure2_external_joint.png")


# ── Figure 3: protected-attribute audit ──────────────────────────────
def figure3():
    d = pd.read_csv(V4 / "stereotype_audit.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(1, 2, figsize=(6.5, 2.6), sharey=True)
    for k, (prot, letter) in enumerate([("sex", "A"), ("province", "B")]):
        sub = d[d["protected"] == prot]
        labels = [a.replace("_", " ") for a in sub["attr"]]
        y = np.arange(len(labels)); h = 0.38
        ax[k].barh(y - h/2, sub["marginal_V"], h, color=GRAY)
        ax[k].barh(y + h/2, sub["residual_V"], h, color=BLUE)
        for yi, v in zip(y + h/2, sub["residual_V"]):
            ax[k].text(v + 0.002, yi, f"{v:.3f}", va="center", fontsize=6.5)
        ax[k].set_yticks(y); ax[k].set_yticklabels(labels)
        ax[k].invert_yaxis()
        ax[k].set_xlim(0, 0.17)
        ax[k].set_xlabel("Cramer's V")
        tag(ax[k], letter, f"attribute x {prot}")
    top_legend(fig, [Patch(color=GRAY, label="marginal V (before conditioning)"),
                     Patch(color=BLUE, label="residual V in the released population (within justified cells)")],
               "Protected-attribute audit: residual association after conditioning on survey-justified cells",
               top=0.88)
    save(fig, "Figure3_protected_audit.png")


# ── Figure 4: cohort query ───────────────────────────────────────────
def figure4():
    prof = pd.read_csv(V4 / "cohort_profile.csv", encoding="utf-8-sig")
    dl = pd.read_csv(V4 / "cohort_dl_distribution.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(1, 2, figsize=(6.8, 2.7),
                           gridspec_kw={"width_ratios": [1.55, 1]})
    h = 0.38

    y = np.arange(len(prof))
    ax[0].barh(y - h/2, prof["cohort_share"], h, color=BLUE)
    ax[0].barh(y + h/2, prof["population_share"], h, color=GRAY)
    for yi, v in zip(y, prof["cohort_share"]):
        ax[0].text(v + 0.01, yi - h/2, f"{v:.2f}", va="center", fontsize=6.5)
    tr = blended_transform_factory(ax[0].transAxes, ax[0].transData)
    ax[0].text(1.03, -0.45, "lift", transform=tr, ha="left", va="bottom",
               fontsize=6.5, color="#444444", fontweight="bold")
    for yi, lift in enumerate(prof["lift"]):
        ax[0].text(1.03, yi, f"x{lift:g}", transform=tr, ha="left", va="center",
                   fontsize=6.5, color="#444444")
    ax[0].set_yticks(y); ax[0].set_yticklabels(prof["dimension"], fontsize=7)
    ax[0].invert_yaxis()
    ax[0].set_xlim(0, 1.0)
    ax[0].set_xlabel("share in high-risk band")
    tag(ax[0], "A", "Behavioral risk profile (share at risk)")

    yb = np.arange(len(dl))
    ax[1].barh(yb - h/2, dl["cohort"], h, color=BLUE)
    ax[1].barh(yb + h/2, dl["population"], h, color=GRAY)
    ax[1].set_yticks(yb)
    lv = [f"L{int(v)}" for v in dl["level"]]
    lv[0] += " (lowest)"; lv[-1] += " (highest)"
    ax[1].set_yticklabels(lv, fontsize=7)
    ax[1].invert_yaxis()
    ax[1].set_xlim(0, 0.35)
    ax[1].set_xlabel("share at each level")
    tag(ax[1], "B", "Digital literacy: cohort vs population")

    top_legend(fig, [Patch(color=BLUE, label="elderly cohort (n = 44,362)"),
                     Patch(color=GRAY, label="full population (n = 1,000,000)")],
               "Cohort query: compound-vulnerability cohort (age >= 65, single-person, lower education)",
               top=0.88)
    fig.subplots_adjust(wspace=0.55)
    fig.text(0.5, -0.03,
             "The profile follows by construction from survey conditionals tied to the cohort's demographics"
             " - a usage demonstration, not an independent finding.",
             ha="center", fontsize=6.5, style="italic", color="#555555")
    save(fig, "Figure4_cohort.png")


# ── Figure 5: decomposition ──────────────────────────────────────────
def figure5():
    dec = pd.read_csv(V4 / "abm_decompose.csv")
    grid = pd.read_csv(V4 / "abm_discriminate_grid.csv")
    fig, ax = plt.subplots(1, 3, figsize=(6.8, 2.4))

    for k, (topo, letter, title) in enumerate([
            ("smallworld", "A", "Small-world:\ncoupling drives the gap"),
            ("scalefree", "B", "Scale-free:\nthe gap vanishes")]):
        sub = dec[dec["topology"] == topo]
        x = np.arange(len(sub)); w = 0.38
        ax[k].bar(x - w/2, sub["coupling_pp"], w, yerr=sub["coupling_CI"],
                  color=BLUE, error_kw={"lw": 0.7})
        ax[k].bar(x + w/2, sub["joint_pp"], w, yerr=sub["joint_CI"],
                  color=VERM, error_kw={"lw": 0.7})
        ax[k].axhline(0, lw=0.7, color="black")
        ax[k].set_xticks(x); ax[k].set_xticklabels(sub["threshold"])
        ax[k].set_xlabel("contagion threshold")
        ax[k].set_ylim(-8.5, 8.5)
        if k == 0:
            ax[k].set_ylabel("reach-gap component (pp)")
        tag(ax[k], letter, title)

    # (C) same runs as Table 5: overall reach at the observed joint minus at independence
    rows = []
    for topo in ["scalefree", "smallworld"]:
        for th in [0.45, 0.55, 0.65]:
            g = grid[(grid["topology"] == topo) & (np.isclose(grid["threshold"], th))]
            ind = g[np.isclose(g["target_mult"], 1.0)]["overall_reach"].iloc[0]
            obs = g[np.isclose(g["target_mult"], 2.3)]["overall_reach"].iloc[0]
            rows.append((("sf" if topo == "scalefree" else "sw") + f"\n{th:.2f}", obs - ind))
    labels = [r_[0] for r_ in rows]; vals = [r_[1] for r_ in rows]
    ax[2].bar(np.arange(len(vals)), vals, 0.6, color=VERM)
    ax[2].axhline(0, lw=0.7, color="black")
    ax[2].set_xticks(np.arange(len(vals))); ax[2].set_xticklabels(labels, fontsize=6.5)
    ax[2].set_ylabel("aggregate reach change (pp)")
    ax[2].set_ylim(-0.2, 1.5)
    tag(ax[2], "C", f"Injected 2.30x joint:\nreach moves <= {max(vals):.1f} pp")
    REPORT.append("Figure5C values (pp): " + ", ".join(f"{l.replace(chr(10),' ')}={v:+.2f}" for l, v in rows))

    top_legend(fig, [Patch(color=BLUE, label="demographic coupling"),
                     Patch(color=VERM, label="inter-attribute joint")],
               "Decomposition of the fused structure under threshold contagion (30 seeds per cell, 95% CI)",
               top=0.86)
    save(fig, "Figure5_decomposition.png")


if __name__ == "__main__":
    figure1(); figure2(); figure3(); figure4(); figure5()
    print("\n".join(REPORT))
    print("done ->", OUT)
