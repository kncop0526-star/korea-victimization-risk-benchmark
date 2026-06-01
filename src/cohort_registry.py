"""
cohort_registry.py
------------------------------------------------------------------
Loads abstracted cohort definitions and resolves named tiers into
pandas filter masks. This module is the SAFEGUARD layer: the public
config ships placeholder/abstracted tiers, and operational cutoffs (if
any) live only in a git-ignored local config.

See: docs/methodology.md, ETHICS.md
------------------------------------------------------------------
한국어 주석: 추상화된 cohort 정의(YAML)를 읽어 pandas 마스크로 변환한다.
민감한 운영 임계값은 공개 config에 두지 않는다(.gitignore가 local config 차단).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    """YAML cohort 정의 로드. local override가 있으면 병합."""
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Optional local override (git-ignored) for operational thresholds.
    local = path.with_name("cohorts.local.yaml")
    if local.exists():
        with open(local, encoding="utf-8") as f:
            override = yaml.safe_load(f) or {}
        cfg = _deep_merge(cfg, override)
    return cfg


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _resolve_predicate(df: pd.DataFrame, key: str, val: Any, tiers: dict) -> pd.Series:
    """단일 술어를 pandas boolean mask로 변환."""
    if key == "age_tier":
        t = tiers["age_tier"][val]
        return df["age"].between(t["min"], t["max"])
    if key == "isolation":
        terms = tiers["isolation"][val]["family_type_contains"]
        return df["family_type"].apply(
            lambda x: any(term in str(x) for term in terms)
        )
    if key == "education_tier":
        allowed = tiers["education_tier"][val]["education_level_in"]
        return df["education_level"].isin(allowed)
    if key.endswith("_in"):
        col = key[:-3]
        return df[col].isin(val)
    if key.endswith("_contains"):
        col = key[:-9]
        terms = val if isinstance(val, list) else [val]
        return df[col].apply(lambda x: any(term in str(x) for term in terms))
    if key == "keep_coarse":
        return pd.Series(True, index=df.index)  # no-op flag, honored upstream
    raise ValueError(f"Unknown predicate key: {key}")


def build_mask(df: pd.DataFrame, module_cfg: dict, tiers: dict) -> pd.Series:
    """모듈의 모든 술어를 AND 결합한 mask 반환."""
    mask = pd.Series(True, index=df.index)
    for predicate in module_cfg.get("predicates", []):
        for key, val in predicate.items():
            mask &= _resolve_predicate(df, key, val, tiers)
    return mask
