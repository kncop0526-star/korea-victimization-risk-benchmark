"""
build_cohorts.py
------------------------------------------------------------------
Load Nemotron-Personas-Korea, apply an abstracted cohort config, draw the
cohort with a fixed random_state, and export parquet + CSV.

Usage:
    python src/build_cohorts.py --config config/cohorts.example.yaml --module module_01

NOTE: The raw 1M dataset is NOT shipped. Download it from the upstream source
(see data/README.md) before running. This script performs filtering only; it
does not alter individual persona content.
------------------------------------------------------------------
한국어 주석: 네모트론 1M 로드 → 추상 config 적용 → random_state 고정 추출 →
parquet+CSV 동시 export. 원천 데이터는 저장소에 포함되지 않는다.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from cohort_registry import load_config, build_mask

# Default location of the downloaded upstream dataset (adjust as needed).
DEFAULT_SOURCE = Path("data/raw/nemotron_korea.parquet")
OUT_DIR = Path("data/processed")


def add_age_band(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["age_band"] = pd.cut(
        df["age"],
        bins=[18, 30, 45, 60, 75, 100],
        labels=["19-29", "30-44", "45-59", "60-74", "75+"],
        right=False,
    )
    return df


def sanity_check(df: pd.DataFrame) -> None:
    """업스트림 데이터 무결성 점검."""
    assert df["age"].between(19, 99).all(), "age out of [19,99]"
    assert df["uuid"].is_unique, "uuid not unique"
    assert (df["country"] == "대한민국").all(), "unexpected country value"


def main() -> None:
    ap = argparse.ArgumentParser(description="Build an abstracted victimization-risk cohort.")
    ap.add_argument("--config", required=True, help="Path to cohort YAML config.")
    ap.add_argument("--module", required=True, help="Module key, e.g. module_01.")
    ap.add_argument("--source", default=str(DEFAULT_SOURCE), help="Path to upstream parquet.")
    ap.add_argument("--frac", type=float, default=1.0, help="Optional subsample fraction of cohort.")
    args = ap.parse_args()

    cfg = load_config(args.config)
    tiers = cfg["tiers"]
    rs = cfg.get("defaults", {}).get("random_state", 42)

    if args.module not in cfg["modules"]:
        raise SystemExit(f"Module '{args.module}' not found in config.")
    module_cfg = cfg["modules"][args.module]

    src = Path(args.source)
    if not src.exists():
        raise SystemExit(
            f"Upstream dataset not found at {src}. See data/README.md for download steps."
        )

    print(f"[load] {src}")
    df = pd.read_parquet(src)
    sanity_check(df)
    df = add_age_band(df)

    mask = build_mask(df, module_cfg, tiers)
    cohort = df[mask]
    if args.frac < 1.0:
        cohort = cohort.sample(frac=args.frac, random_state=rs)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = OUT_DIR / args.module
    cohort.to_parquet(base.with_suffix(".parquet"), index=False)
    cohort.to_csv(base.with_suffix(".csv"), index=False, encoding="utf-8-sig")

    meta = {
        "module": args.module,
        "description": module_cfg.get("description", ""),
        "n_rows": int(len(cohort)),
        "share_of_total": round(len(cohort) / len(df), 4),
        "random_state": rs,
        "validate_on": module_cfg.get("validate_on", []),
        "source": "NVIDIA Nemotron-Personas-Korea (CC-BY-4.0)",
    }
    with open(base.with_suffix(".meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[done] {args.module}: {len(cohort):,} rows "
          f"({meta['share_of_total']*100:.1f}% of source) -> {base}.parquet/.csv")
    print(f"[next] validate: python src/validate_kosis.py --cohort {base}.parquet")


if __name__ == "__main__":
    main()
