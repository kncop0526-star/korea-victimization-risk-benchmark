"""
enrich_stage1.py — Stage-1 multi-attribute enrichment.
Combine REAL survey anchors with the Nemotron backbone; verify by-construction fidelity.
Stage 2/3 (LLM) run separately (enrich_stage2_3.py).
  --b1  Route-B richer conditioning: the 4 survey-direct anchors use age_band x sex x education_tier
        (config/anchors/*_b1.csv via build_anchor_b1.py).
  --b2  Route-B observed joint: prior_victimization & reporting_propensity drawn jointly from the
        KCVS nested joint (config/anchors/kcvs_joint_b2.csv); RP set only for victims (-1 = N/A).
        Implies --b1 for the other attrs.
education_level -> education_tier: higher = {4년제 대학교, 2~3년제 전문대학, 대학원}.
--backbone: a parquet file OR a dir/glob of Nemotron shards (train-*.parquet).
"""
from __future__ import annotations
import argparse, glob, json
from pathlib import Path
import numpy as np
import pandas as pd

BACKBONE_COLS = ["uuid", "sex", "age", "education_level", "province", "occupation", "family_type"]
AGE_BINS = [19, 30, 45, 60, 75, 200]
AGE_LABELS = ["19-29", "30-44", "45-59", "60-74", "75+"]
HIGHER_EDU = {"4년제 대학교", "2~3년제 전문대학", "대학원"}
ANCHORS = {
    "financial_vulnerability": ("config/anchors/financial_vulnerability.csv", ["age_band"]),
    "digital_literacy": ("config/anchors/digital_literacy.csv", ["age_band", "education_tier"]),
    "authority_deference": ("config/anchors/authority_deference.csv", ["age_band"]),
    "social_isolation": ("config/anchors/social_isolation.csv", ["age_band"]),
    "prior_victimization": ("config/anchors/prior_victimization.csv", ["age_band"]),
    "reporting_propensity": ("config/anchors/reporting_propensity.csv", ["age_band"]),
}
ANCHORS_B1 = {
    "financial_vulnerability": ("config/anchors/financial_vulnerability_b1.csv", ["age_band", "sex_mf", "education_tier"]),
    "digital_literacy": ("config/anchors/digital_literacy.csv", ["age_band", "education_tier"]),
    "authority_deference": ("config/anchors/authority_deference_b1.csv", ["age_band", "sex_mf", "education_tier"]),
    "social_isolation": ("config/anchors/social_isolation_b1.csv", ["age_band", "sex_mf", "education_tier"]),
    "prior_victimization": ("config/anchors/prior_victimization_b1.csv", ["age_band", "sex_mf", "education_tier"]),
    "reporting_propensity": ("config/anchors/reporting_propensity_b1.csv", ["age_band", "sex_mf", "education_tier"]),
}
JOINT_KCVS = ("config/anchors/kcvs_joint_b2.csv", ["age_band", "sex_mf", "education_tier"])
JOINT_OUTCOMES = ["nonvictim", "victim_unreported", "victim_reported"]
JOINT_MAP = {"nonvictim": (0, -1), "victim_unreported": (1, 0), "victim_reported": (1, 1)}

def load_backbone(path):
    if Path(path).is_dir():
        files = sorted(glob.glob(str(Path(path) / "train-*.parquet")))
    else:
        files = sorted(glob.glob(path)) or [path]
    parts = []
    for f in files:
        try:
            parts.append(pd.read_parquet(f, columns=BACKBONE_COLS, engine="fastparquet"))
        except Exception:
            parts.append(pd.read_parquet(f, engine="fastparquet"))
    return pd.concat(parts, ignore_index=True)

def add_cells(df):
    df = df.copy()
    df["age_band"] = pd.cut(df["age"], bins=AGE_BINS, labels=AGE_LABELS, right=False).astype(str)
    df["education_tier"] = np.where(df["education_level"].isin(HIGHER_EDU), "higher", "lower")
    df["sex_mf"] = df["sex"].map({"남자": "M", "여자": "F"})
    return df

def sample_attr(df, anchor, cells, rng):
    out = np.full(len(df), -1)
    for keys, sub in anchor.groupby(cells):
        sub = sub.sort_values("level")
        mask = np.ones(len(df), dtype=bool)
        keyvals = keys if isinstance(keys, tuple) else (keys,)
        for col, val in zip(cells, keyvals):
            mask &= (df[col].values == val)
        n = int(mask.sum())
        if n:
            p = (sub["prob"] / sub["prob"].sum()).to_numpy()
            out[mask] = rng.choice(sub["level"].to_numpy(), size=n, p=p)
    return out

def sample_joint_kcvs(df, joint, cells, rng):
    """Draw (PV, RP) jointly from the KCVS nested joint; RP = -1 (N/A) for non-victims."""
    pv = np.full(len(df), -1); rp = np.full(len(df), -1)
    for keys, sub in joint.groupby(cells):
        mask = np.ones(len(df), dtype=bool)
        keyvals = keys if isinstance(keys, tuple) else (keys,)
        for col, val in zip(cells, keyvals):
            mask &= (df[col].values == val)
        n = int(mask.sum())
        if n:
            sub = sub.set_index("outcome").reindex(JOINT_OUTCOMES).fillna(0.0)
            p = sub["prob"].to_numpy(); p = p / p.sum()
            draws = rng.choice(JOINT_OUTCOMES, size=n, p=p)
            pv[mask] = np.array([JOINT_MAP[d][0] for d in draws])
            rp[mask] = np.array([JOINT_MAP[d][1] for d in draws])
    return pv, rp

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", required=True)
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--out", default="data/processed/enriched_stage1")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--b1", action="store_true")
    ap.add_argument("--b2", action="store_true", help="observed PV x RP joint (implies --b1)")
    args = ap.parse_args()

    use_b1 = args.b1 or args.b2
    anchor_set = dict(ANCHORS_B1 if use_b1 else ANCHORS)
    joint_attrs = ["prior_victimization", "reporting_propensity"] if args.b2 else []
    for a in joint_attrs:
        anchor_set.pop(a, None)

    rng = np.random.default_rng(args.seed)
    df = load_backbone(args.backbone)
    if args.n and args.n < len(df):
        df = df.sample(args.n, random_state=args.seed).reset_index(drop=True)
    df = add_cells(df)

    fidelity = {}
    for attr, (path, cells) in anchor_set.items():
        anchor = pd.read_csv(path)
        for c in cells:
            anchor[c] = anchor[c].astype(str)
        df["attr_" + attr] = sample_attr(df, anchor, cells, rng)
        syn = df.groupby(cells + ["attr_" + attr]).size()
        syn = (syn / syn.groupby(level=list(range(len(cells)))).transform("sum")).rename("syn").reset_index()
        syn.columns = cells + ["level", "syn"]
        m = anchor.merge(syn, on=cells + ["level"], how="left").fillna(0)
        fidelity[attr] = round(float((m["prob"] - m["syn"]).abs().max()), 4)

    if args.b2:
        jpath, jcells = JOINT_KCVS
        joint = pd.read_csv(jpath)
        for c in jcells:
            joint[c] = joint[c].astype(str)
        pv, rp = sample_joint_kcvs(df, joint, jcells, rng)
        df["attr_prior_victimization"] = pv
        df["attr_reporting_propensity"] = rp
        vrate = float((pv == 1).mean())
        rrate = float((rp == 1).sum() / max((pv == 1).sum(), 1))
        fidelity["prior_victimization(joint)"] = round(vrate, 4)
        fidelity["reporting_propensity(joint|victim)"] = round(rrate, 4)

    all_attrs = list(anchor_set) + (["prior_victimization", "reporting_propensity"] if args.b2 else [])
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    keep = ["uuid", "sex", "age", "age_band", "education_level", "education_tier", "sex_mf",
            "province", "occupation", "family_type"] + ["attr_" + a for a in all_attrs]
    keep = [c for c in keep if c in df.columns]
    enriched = df[keep].copy()
    cond = "B2" if args.b2 else ("B1" if use_b1 else "base")
    meta = {"stage": 1, "random_state": args.seed, "conditioning": cond,
            "llm_stage2_3": "pending (needs API key)"}
    enriched["gen_meta"] = json.dumps(meta, ensure_ascii=False)
    enriched.to_parquet(outp.with_suffix(".parquet"), index=False, engine="fastparquet")
    enriched.head(2000).to_csv(str(outp) + "_sample.csv", index=False, encoding="utf-8-sig")
    print("[ok] enriched " + format(len(enriched), ",") + " personas (" + cond + ") -> " + str(outp) + ".parquet")
    print("[fidelity] max |anchor - synthetic| (joint rows = realized rate):")
    for a, g in fidelity.items():
        print("   " + a.ljust(36) + " " + str(g))

if __name__ == "__main__":
    main()
