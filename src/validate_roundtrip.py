"""
validate_roundtrip.py — Technical Validation 4.2 (round-trip consistency / reliability).

Consumes the Stage-2/3 output (enrich_stage2_3.py -> JSONL) and measures how often the
LLM narrative, when read back by the Stage-3 extractor, recovers the *sampled* attribute
level. High agreement = the narrative faithfully encodes the fixed input (render-not-estimate
held). It produces figure F3 (agreement by attribute + a confusion matrix) and a summary CSV.

This script is ready to run NOW; the inputs it needs come from the pinned-LLM Stage-2/3 pass
(API-key gated, run by the user). On the --dry-run stub JSONL it executes end-to-end but the
agreement is trivially ~100% (deterministic keyword stub) — clearly labelled DEMO, not a result.

JSONL record shape (per enrich_stage2_3.py):
  {"uuid", "attr": {attr: level, ...}, "attr_narrative",
   "roundtrip_<attr>": level, "roundtrip_mismatch": bool, "gen_meta": {...}}
Any number of "roundtrip_<attr>" fields are picked up automatically.

Usage
  python src/validate_roundtrip.py --in data/processed/enriched_stage23.jsonl --out results
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

LIKERT = {"financial_vulnerability", "digital_literacy", "authority_deference", "social_isolation"}
BINARY = {"prior_victimization", "reporting_propensity"}
RT_PREFIX = "roundtrip_"


def load_jsonl(path: str) -> tuple[pd.DataFrame, bool, set[str]]:
    recs, models = [], set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            models.add((r.get("gen_meta") or {}).get("actual_model", "?"))
            recs.append(r)
    df = pd.json_normalize(recs)
    is_stub = any("STUB" in str(m) for m in models)
    rt_attrs = sorted({c[len(RT_PREFIX):] for c in df.columns
                       if c.startswith(RT_PREFIX) and c[len(RT_PREFIX):] in (LIKERT | BINARY)})
    return df, is_stub, set(rt_attrs)


def _quadratic_weighted_kappa(s, r):
    """Quadratic weighted Cohen's kappa for ordinal ratings (NumPy only).
    Credits near-misses; 1.0 = perfect, 0 = chance-level. Likert only."""
    import numpy as np
    levels = sorted(set(int(x) for x in list(s) + list(r)))
    idx = {v: i for i, v in enumerate(levels)}
    k = len(levels)
    if k < 2:
        return 1.0
    O = np.zeros((k, k))
    for a_, b_ in zip(s, r):
        O[idx[int(a_)], idx[int(b_)]] += 1
    O /= O.sum()
    row = O.sum(1, keepdims=True)
    col = O.sum(0, keepdims=True)
    E = row @ col
    W = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            W[i, j] = (levels[i] - levels[j]) ** 2
    W /= (levels[-1] - levels[0]) ** 2
    denom = float((W * E).sum())
    return float(1 - (W * O).sum() / denom) if denom > 0 else 1.0


def per_attr_stats(df: pd.DataFrame, rt_attrs: set[str]) -> tuple[pd.DataFrame, dict]:
    rows, confus = [], {}
    for a in sorted(rt_attrs):
        s_col, r_col = f"attr.{a}", f"{RT_PREFIX}{a}"
        if s_col not in df.columns or r_col not in df.columns:
            continue
        sub = df[[s_col, r_col]].dropna()
        if sub.empty:
            continue
        s = sub[s_col].astype(int).to_numpy()
        r = sub[r_col].astype(int).to_numpy()
        exact = float(np.mean(s == r))
        within1 = float(np.mean(np.abs(s - r) <= 1)) if a in LIKERT else exact
        rows.append({
            "attr": a, "n": int(len(sub)),
            "exact_agreement": round(exact, 4),
            "within1_agreement": round(within1, 4),
            "mean_abs_err": round(float(np.mean(np.abs(s - r))), 4),
            "weighted_kappa": round(_quadratic_weighted_kappa(s, r), 4) if a in LIKERT else None,
            "type": "likert" if a in LIKERT else "binary",
        })
        levels = sorted(set(s) | set(r))
        cm = pd.crosstab(pd.Series(s, name="sampled"),
                         pd.Series(r, name="roundtrip"),
                         dropna=False).reindex(index=levels, columns=levels, fill_value=0)
        confus[a] = cm
    return pd.DataFrame(rows), confus


def make_figure(summ: pd.DataFrame, confus: dict, out_png: Path, is_stub: bool) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "figure.dpi": 150})
    primary = "digital_literacy" if "digital_literacy" in confus else (
        next(iter(confus)) if confus else None)
    ncol = 2 if primary else 1
    fig = plt.figure(figsize=(5.6 * ncol, 4.2))
    gs = fig.add_gridspec(1, ncol, wspace=0.3)

    # Panel A: agreement by attribute
    axA = fig.add_subplot(gs[0, 0])
    s = summ.sort_values("exact_agreement")
    y = np.arange(len(s)); h = 0.38
    axA.barh(y + h / 2, s["within1_agreement"], h, color="#9ecae1",
             edgecolor="0.3", lw=0.4, label="within +/-1 level")
    axA.barh(y - h / 2, s["exact_agreement"], h, color="#3182bd",
             edgecolor="0.3", lw=0.4, label="exact")
    axA.set_yticks(y); axA.set_yticklabels([a.replace("_", " ") for a in s["attr"]], fontsize=8)
    axA.set_xlim(0, 1.0); axA.set_xlabel("agreement rate")
    axA.axvline(0.8, color="0.5", ls=":", lw=1)
    for k, (e, w) in enumerate(zip(s["exact_agreement"], s["within1_agreement"])):
        axA.text(e + 0.01, k - h / 2, f"{e:.2f}", va="center", fontsize=6.5)
        if w > e:
            axA.text(w + 0.01, k + h / 2, f"{w:.2f}", va="center", fontsize=6.5, color="0.35")
    axA.set_title("(A) Round-trip agreement by attribute")
    axA.legend(fontsize=7, loc="lower right", framealpha=0.9)

    # Panel B: confusion matrix for the primary Likert attribute
    if primary:
        axB = fig.add_subplot(gs[0, 1])
        cm = confus[primary]
        cmn = cm.div(cm.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
        im = axB.imshow(cmn.to_numpy(), cmap="Blues", vmin=0, vmax=1, aspect="auto")
        axB.set_xticks(range(len(cm.columns))); axB.set_xticklabels(cm.columns)
        axB.set_yticks(range(len(cm.index))); axB.set_yticklabels(cm.index)
        axB.set_xlabel("round-trip level"); axB.set_ylabel("sampled level")
        for i in range(cmn.shape[0]):
            for j in range(cmn.shape[1]):
                v = cmn.to_numpy()[i, j]
                if v > 0.005:
                    axB.text(j, i, f"{v:.2f}", ha="center", va="center",
                             fontsize=6.5, color="white" if v > 0.5 else "0.2")
        axB.set_title(f"(B) Confusion: {primary.replace('_',' ')}\n(row-normalised)")
        fig.colorbar(im, ax=axB, fraction=0.046, pad=0.04)

    tag = "  [DEMO / STUB — replace with pinned-LLM pass]" if is_stub else ""
    fig.suptitle("Round-trip consistency of KVRB narrative realization" + tag,
                 fontsize=11, y=1.03)
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/processed/enriched_stage23.jsonl")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    df, is_stub, rt_attrs = load_jsonl(args.inp)
    if not rt_attrs:
        raise SystemExit("no roundtrip_<attr> fields found — run enrich_stage2_3.py first")
    summ, confus = per_attr_stats(df, rt_attrs)
    summ.to_csv(out / "roundtrip_summary.csv", index=False, encoding="utf-8-sig")
    make_figure(summ, confus, out / "F3_roundtrip_consistency.png", is_stub)

    print(f"[ok] records: {len(df):,}  | round-tripped attributes: {', '.join(sorted(rt_attrs))}")
    if is_stub:
        print("[warn] STUB input detected — agreement is deterministic, NOT a validation result.")
    print("[roundtrip] agreement by attribute:")
    for _, r in summ.sort_values("exact_agreement").iterrows():
        qwk = r['weighted_kappa']
        qwk_s = f"  qwk={qwk:.3f}" if qwk is not None else ""
        print(f"   {r['attr']:<26} exact={r['exact_agreement']:.3f}  "
              f"within1={r['within1_agreement']:.3f}  MAE={r['mean_abs_err']:.3f}{qwk_s}  n={r['n']}")
    print(f"[fig] {out/'F3_roundtrip_consistency.png'}")


if __name__ == "__main__":
    main()
