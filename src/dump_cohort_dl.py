"""dump_cohort_dl.py — Figure 4 panel B data dump (one-time, run on the data PC).

demo_cohort.py computed the digital-literacy level distribution (cohort vs population)
in memory but never saved it. This script saves exactly that, nothing else.
Cohort definition is copied verbatim from demo_cohort.py (cohort_specs/01):
age >= 65 AND single-person household AND lower education.

Usage (repo root):
  py src\\dump_cohort_dl.py --parts data\\processed\\enriched_1M_v4_parts --out results_v4

Output: results_v4/cohort_dl_distribution.csv  (columns: level, cohort, population)
"""
from __future__ import annotations
import argparse, glob
from pathlib import Path
import pandas as pd

SINGLE_HH_TERMS = ["혼자 거주", "1인", "독거"]


def load_parts(parts_dir: str) -> pd.DataFrame:
    files = sorted(glob.glob(str(Path(parts_dir) / "part_*.parquet")))
    if not files:
        raise SystemExit(f"no parquet parts under {parts_dir}")
    frames = []
    for f in files:
        try:
            frames.append(pd.read_parquet(f, engine="fastparquet"))
        except Exception:
            frames.append(pd.read_parquet(f))
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="data/processed/enriched_1M_v4_parts")
    ap.add_argument("--out", default="results_v4")
    ap.add_argument("--min-age", type=int, default=65)
    a = ap.parse_args()

    df = load_parts(a.parts)
    single = df["family_type"].astype(str).apply(lambda x: any(t in x for t in SINGLE_HH_TERMS))
    lower = df["education_tier"].astype(str).eq("lower") if "education_tier" in df.columns else True
    mask = (df["age"] >= a.min_age) & single & lower
    coh, pop = df[mask], df

    rows = []
    for lv in [1, 2, 3, 4, 5]:
        rows.append({
            "level": lv,
            "cohort": float((coh["attr_digital_literacy"] == lv).mean()),
            "population": float((pop["attr_digital_literacy"] == lv).mean()),
        })
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    dst = out / "cohort_dl_distribution.csv"
    pd.DataFrame(rows).to_csv(dst, index=False, encoding="utf-8-sig")
    print(f"[ok] cohort n={int(mask.sum()):,} / population n={len(df):,}")
    print(f"[ok] wrote {dst}")


if __name__ == "__main__":
    main()
