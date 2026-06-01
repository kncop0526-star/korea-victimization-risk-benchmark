"""
fig_pipeline.py — Figure F1 (construction pipeline diagram).

Renders the KVRB construction pipeline as a labelled box-and-arrow diagram:
  demographic backbone + survey anchors -> Stage 1 sample -> Stage 2 render
  -> Stage 3 round-trip -> released dataset, with the F2/F3 validation taps.
No data is read; this is a static schematic for the data descriptor.

Usage
  python src/fig_pipeline.py --out results
"""
from __future__ import annotations
import argparse
from pathlib import Path


def make(out_png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    plt.rcParams.update({"font.size": 9})
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.set_xlim(0, 100); ax.set_ylim(0, 58); ax.axis("off")

    def box(x, y, w, h, title, body, fc, ec):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=2",
                                    linewidth=1.3, edgecolor=ec, facecolor=fc, zorder=2))
        ax.text(x + w / 2, y + h - 3.2, title, ha="center", va="top", fontsize=9.5,
                fontweight="bold", zorder=3)
        ax.text(x + w / 2, y + h - 7.0, body, ha="center", va="top", fontsize=7.4,
                color="0.25", zorder=3)

    def arrow(x1, y1, x2, y2, color="0.35", style="-|>", lw=1.6, ls="-"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                     mutation_scale=14, lw=lw, color=color, ls=ls, zorder=1))

    blue, green, amber, purple, grey, red = (
        "#dbe6f3", "#dcefdc", "#fbecd2", "#e8def5", "#eeeeee", "#f6dada")
    eb, eg, ea, ep, er = "#3a6ea5", "#3f8a3f", "#c8941f", "#7a4fb0", "#c0392b"

    # Inputs (left column)
    box(2, 38, 22, 15, "Demographic backbone",
        "Nemotron-Personas-Korea\n1M personas · CC-BY-4.0\n(KOSIS-validated)", blue, eb)
    box(2, 6, 22, 18, "Survey anchors (6)",
        "Household Finance · Digital Divide\nKGSS · KCVS\nweighted P(level | cell)", green, eg)

    # Stage 1
    box(30, 22, 19, 16, "Stage 1 — Sample",
        "draw attribute level\nfrom P(level | cell)\nseed-fixed, no estimation", amber, ea)
    # Stage 2
    box(54, 22, 19, 16, "Stage 2 — Render",
        "pinned LLM writes\n1st-person narrative\nfrom FIXED levels", purple, ep)
    # Stage 3
    box(78, 22, 19, 16, "Stage 3 — Round-trip",
        "re-extract level\nfrom narrative\nagreement audit", red, er)

    # Output
    box(54, 1, 43, 14, "Released dataset",
        "enriched 1M (parquet/CSV) + narratives (JSONL)\nanchor-version metadata · Zenodo DOI · CC-BY-4.0", grey, "0.45")

    # Validation taps
    box(30, 44, 19, 11, "F2 fidelity",
        "synthetic vs survey\nP(level | cell)", "#eef4fb", eb)

    # Arrows: inputs -> stage1
    arrow(24, 45, 30, 33)
    arrow(24, 15, 30, 27)
    # stage1 -> stage2 -> stage3
    arrow(49, 30, 54, 30)
    arrow(73, 30, 78, 30)
    # stage1 -> F2 tap (dashed, validation)
    arrow(39.5, 38, 39.5, 44, color=eb, style="-|>", lw=1.4, ls=(0, (4, 2)))
    # stage3 -> released
    arrow(87, 22, 80, 15)
    # stage2 -> released (narrative)
    arrow(63, 22, 68, 15, color="0.5", ls=(0, (4, 2)))
    # stage3 round-trip feedback to stage2 (F3)
    arrow(82, 22, 70, 20.5, color=er, style="-|>", lw=1.3, ls=(0, (3, 2)))
    ax.text(74, 18.8, "F3 round-trip agreement", ha="center", fontsize=7, color=er)

    # render-not-estimate banner
    ax.text(63, 40.5, "render-not-estimate:  the LLM expresses values, it never invents them",
            ha="center", fontsize=8, style="italic", color="0.3")

    ax.text(50, 56.5, "F1  KVRB construction pipeline", ha="center", fontsize=12, fontweight="bold")
    fig.savefig(out_png, bbox_inches="tight", dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    p = out / "F1_pipeline.png"
    make(p)
    print(f"[fig] {p}")


if __name__ == "__main__":
    main()
