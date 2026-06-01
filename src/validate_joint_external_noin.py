"""
validate_joint_external_noin.py — external joint-distribution validation against 노인실태조사
(National Survey of Older Koreans, KIHASA/MOHW). Answers the reviewers' strongest point:
KVRB samples cross-survey attributes under (mostly) conditional independence, so it may
mis-estimate the JOINT of compounding vulnerabilities — exactly the tail prevention work reads.

This script computes, for the elderly population (age >= 65):
  (A) the REAL rate of "simultaneous extremes" — high financial vulnerability AND low digital
      literacy AND high social isolation — from 노인실태조사 microdata (weighted), and the REAL
      pairwise associations (Cramer's V) for FV x DL, FV x SI, DL x SI;
  (B) the SYNTHETIC counterparts from the KVRB v3 1M dataset, filtered to age >= 65;
  (C) the ERROR BOUND: how much KVRB under- or over-estimates each quantity (signed pp + ratio).

The §4.5 result is then a sentence of the form:
  "Against 노인실태조사 (N=...), KVRB under-estimates the simultaneous-extreme elderly rate by
   X.X pp (real R.R% vs synthetic S.S%, ratio K), and recovers the FV x SI association to within
    delta-V = ..., bounding the conditional-independence error."

------------------------------------------------------------------------------------------------
WHY THIS IS HONEST, NOT CIRCULAR: 노인실태조사 is NOT an anchor of KVRB. KVRB's FV/DL/SI come from
가계금융복지조사 / 디지털정보격차 / KGSS — different surveys. So comparing the realized KVRB joint
to the 노인실태조사 joint is a genuine out-of-sample test of the (cross-survey) joint, which no
KVRB anchor observed. A non-trivial error here is an informative finding, not a defect to hide.
------------------------------------------------------------------------------------------------

USAGE (Daniel, on PC with the microdata):
  # 0) one-time: discover the right column names in your 노인실태조사 file
  py src/validate_joint_external_noin.py --discover --noin path\to\노인실태조사_2023.sav
  # -> prints candidate columns by keyword; fill CONFIG below (NOIN_VARS + level rules)

  # 1) run the real-vs-synthetic comparison
  py src/validate_joint_external_noin.py ^
     --noin path\to\노인실태조사_2023.sav ^
     --kvrb data\processed\enriched_1M_v3_parts ^
     --out results

  # dry-run with no data (proves the pipeline; NOT a real result):
  py src/validate_joint_external_noin.py --mock --out results

Outputs (in --out):
  joint_external_noin.csv   one row per quantity: real, synthetic, diff_pp, ratio
  joint_external_noin.txt   human-readable report + the ready-to-paste §4.5 sentence
  joint_external_noin.png   real vs synthetic bars (simultaneous-extreme + 3 pairwise V)

Operational notes (repo rules):
  - Windows: use the `py` launcher, not the Store `python` stub.
  - .sav via pyreadstat; .csv via pandas (cp949). pyreadstat reads missing/IAP codes as real
    numbers, so MISSING_CODES below are dropped explicitly (B0 audit lesson).
  - All rates are survey-WEIGHTED (set NOIN_VARS['weight']).
"""
from __future__ import annotations
import argparse, glob, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

# ============================ CONFIG — FILL FROM THE CODEBOOK ============================
# 노인실태조사 variable codes differ by wave (2017 / 2020 / 2023). Run --discover first, then set
# the actual column names and the rule that maps each to a KVRB attribute level (1..5).
# Each rule is a callable: raw pandas Series -> integer level Series in {1..5} (NaN for missing).
#
# Defaults below are PLACEHOLDERS keyed to typical item meanings. VERIFY each against the codebook
# before trusting the output. Leave a rule as None to skip that attribute (the script will tell you
# which joints it can still compute).

NOIN_VARS = {
    # column name in the microdata  (None until you fill it)
    "age":    None,   # 만 나이 (continuous) or age-group code
    "weight": None,   # 가중치 (survey weight). If None, unweighted (NOT recommended).
    # raw columns feeding each attribute (can be one or several):
    "fv":     None,   # e.g. 경제상태 만족도 / 소득충분도 / 생활비 충당 어려움
    "dl":     None,   # e.g. 스마트폰·인터넷 이용 능력 / 정보화기기 활용
    "si":     None,   # e.g. 독거 + 연락빈도 + 사회적 지지망 (structural support deficit)
}

# Missing / inapplicable codes to drop BEFORE mapping (pyreadstat returns these as numbers).
MISSING_CODES = {-1, -9, 9, 99, 999, 8, 88}  # trim to your codebook's actual missing codes.

# --- level-mapping rules: raw Series -> level 1..5 (edit to match the codebook direction) ---
# FINANCIAL VULNERABILITY: higher level = MORE vulnerable.
def rule_fv(s: pd.Series) -> pd.Series:
    # PLACEHOLDER: assume a 1(매우 충분/만족)..5(매우 부족/불만) economic-hardship item already 1..5
    # where 5 = most vulnerable. If your item runs the other way, reverse with (6 - s).
    return pd.to_numeric(s, errors="coerce")

# DIGITAL LITERACY: higher level = MORE competent (KVRB convention; "low DL" = level 1-2).
def rule_dl(s: pd.Series) -> pd.Series:
    # PLACEHOLDER: assume a 1(전혀 못함)..5(매우 잘함) competency item already 1..5.
    return pd.to_numeric(s, errors="coerce")

# SOCIAL ISOLATION (structural): higher level = MORE isolated (support-network deficit).
def rule_si(s: pd.Series) -> pd.Series:
    # PLACEHOLDER: assume a 1(지지망 충분)..5(고립) item already 1..5. If you must build SI from
    # several items (독거 flag + 연락빈도 + 도움요청 가능 인원), combine them here and bin to 1..5.
    return pd.to_numeric(s, errors="coerce")

RULES = {"fv": rule_fv, "dl": rule_dl, "si": rule_si}

# "Extreme" thresholds — MUST match the manuscript cohort definition (§4.5 / §5.1).
EXTREME = {
    "fv": lambda lv: lv >= 4,   # high financial vulnerability
    "dl": lambda lv: lv <= 2,   # low digital literacy
    "si": lambda lv: lv >= 4,   # high social isolation
}
ELDERLY_MIN_AGE = 65
# ========================================================================================

KVRB_ATTR = {"fv": "attr_financial_vulnerability", "dl": "attr_digital_literacy",
             "si": "attr_social_isolation", "age": "age"}


def cramers_v(a: pd.Series, b: pd.Series, w: pd.Series | None = None) -> float:
    """Weighted Cramer's V between two categorical/ordinal series."""
    a, b = a.astype("Int64"), b.astype("Int64")
    m = a.notna() & b.notna()
    a, b = a[m], b[m]
    ww = (w[m] if w is not None else pd.Series(np.ones(m.sum()), index=a.index))
    tab = pd.crosstab(a, b, values=ww, aggfunc="sum").fillna(0.0)
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        return float("nan")
    obs = tab.values.astype(float)
    n = obs.sum()
    row = obs.sum(1, keepdims=True); col = obs.sum(0, keepdims=True)
    exp = row @ col / n
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.nansum((obs - exp) ** 2 / np.where(exp == 0, np.nan, exp))
    k = min(obs.shape) - 1
    return float(np.sqrt(chi2 / (n * k))) if k > 0 and n > 0 else float("nan")


def wmean(mask: pd.Series, w: pd.Series) -> float:
    w = w.fillna(0.0)
    tot = w.sum()
    return float((w[mask].sum() / tot)) if tot > 0 else float("nan")


# ----------------------------------- loaders -----------------------------------
def load_noin(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() == ".sav":
        try:
            import pyreadstat
        except ImportError:
            raise SystemExit("[fatal] pip install pyreadstat --break-system-packages  (for .sav)")
        df, _ = pyreadstat.read_sav(str(p))
    elif p.suffix.lower() in (".csv", ".txt"):
        try:
            df = pd.read_csv(p, encoding="cp949")
        except UnicodeDecodeError:
            df = pd.read_csv(p, encoding="utf-8")
    else:
        raise SystemExit(f"[fatal] unsupported file type: {p.suffix}")
    return df


def to_levels_noin(df: pd.DataFrame) -> pd.DataFrame:
    """Apply CONFIG to produce age, weight, and fv/dl/si levels (1..5)."""
    need = NOIN_VARS["age"]
    if need is None or need not in df.columns:
        raise SystemExit("[fatal] set NOIN_VARS['age'] to the age column (run --discover).")
    out = pd.DataFrame(index=df.index)
    out["age"] = pd.to_numeric(df[NOIN_VARS["age"]], errors="coerce")
    wv = NOIN_VARS["weight"]
    out["w"] = pd.to_numeric(df[wv], errors="coerce") if (wv and wv in df.columns) else 1.0
    if wv is None:
        print("[warn] NOIN_VARS['weight'] is None -> UNWEIGHTED rates (set it for a defensible result).")
    for a in ("fv", "dl", "si"):
        col = NOIN_VARS[a]
        if col is None or col not in df.columns or RULES[a] is None:
            out[a] = pd.NA
            print(f"[warn] {a}: no column/rule -> skipped.")
            continue
        raw = df[col].copy()
        raw = raw.where(~raw.isin(MISSING_CODES))   # drop missing codes
        lv = RULES[a](raw)
        lv = lv.where(lv.between(1, 5))
        out[a] = lv.round().astype("Int64")
    return out


def load_kvrb_elderly(parts_dir: str) -> pd.DataFrame:
    files = sorted(glob.glob(str(Path(parts_dir) / "part_*.parquet")))
    if not files:
        raise SystemExit(f"[fatal] no parquet parts under {parts_dir}")
    cols = list(KVRB_ATTR.values())
    frames = []
    for f in files:
        d = pd.read_parquet(f, columns=cols)
        d = d[pd.to_numeric(d["age"], errors="coerce") >= ELDERLY_MIN_AGE]
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    out = pd.DataFrame(index=df.index)
    out["age"] = pd.to_numeric(df["age"], errors="coerce")
    out["w"] = 1.0
    for a in ("fv", "dl", "si"):
        out[a] = pd.to_numeric(df[KVRB_ATTR[a]], errors="coerce").astype("Int64")
    return out


# ----------------------------------- compare -----------------------------------
def quantities(d: pd.DataFrame, label: str) -> dict:
    eld = d[d["age"] >= ELDERLY_MIN_AGE].copy()
    w = eld["w"]
    have = [a for a in ("fv", "dl", "si") if eld[a].notna().any()]
    res = {"label": label, "n": int(len(eld)), "n_eff_w": float(w.sum())}
    # simultaneous extremes (needs all three present)
    if set(("fv", "dl", "si")).issubset(have):
        ext = (eld["fv"].map(EXTREME["fv"]).fillna(False)
               & eld["dl"].map(EXTREME["dl"]).fillna(False)
               & eld["si"].map(EXTREME["si"]).fillna(False))
        res["simultaneous_extreme_rate"] = wmean(ext, w)
    else:
        res["simultaneous_extreme_rate"] = float("nan")
    # pairwise associations
    for x, y in (("fv", "si"), ("fv", "dl"), ("dl", "si")):
        res[f"V_{x}_{y}"] = (cramers_v(eld[x], eld[y], w)
                             if x in have and y in have else float("nan"))
    return res


def compare(real: dict, synth: dict) -> pd.DataFrame:
    keys = ["simultaneous_extreme_rate", "V_fv_si", "V_fv_dl", "V_dl_si"]
    rows = []
    for k in keys:
        r, s = real.get(k, float("nan")), synth.get(k, float("nan"))
        diff_pp = (s - r) * 100 if k.endswith("rate") else (s - r)
        ratio = (s / r) if (r and not np.isnan(r) and r != 0) else float("nan")
        rows.append({"quantity": k, "real_노인실태조사": r, "synthetic_KVRB": s,
                     "synth_minus_real": (diff_pp if k.endswith("rate") else (s - r)),
                     "unit": "pp" if k.endswith("rate") else "ΔV", "ratio_synth_real": ratio})
    return pd.DataFrame(rows)


def make_sentence(cmp: pd.DataFrame, real: dict, synth: dict) -> str:
    row = cmp[cmp.quantity == "simultaneous_extreme_rate"].iloc[0]
    r, s = row["real_노인실태조사"], row["synthetic_KVRB"]
    if np.isnan(r) or np.isnan(s):
        return "[fill once FV/DL/SI rules are set] simultaneous-extreme comparison unavailable."
    direction = "under-estimates" if s < r else "over-estimates"
    vfs = cmp[cmp.quantity == "V_fv_si"].iloc[0]
    return (f"Against 노인실태조사 (N={real['n']:,} aged {ELDERLY_MIN_AGE}+), KVRB {direction} the "
            f"simultaneous-extreme elderly rate (high financial vulnerability, low digital literacy, "
            f"high social isolation) by {abs(s-r)*100:.1f} pp (real {r*100:.1f}% vs synthetic "
            f"{s*100:.1f}%; ratio {s/r:.2f}). The strongest cross-survey pair, FV×SI, is recovered to "
            f"within ΔV = {abs(vfs['synth_minus_real']):.3f} (real {vfs['real_노인실태조사']:.3f} vs "
            f"synthetic {vfs['synthetic_KVRB']:.3f}). This bounds the conditional-independence error: "
            f"the dataset's joint tail is {'conservative' if s<r else 'inflated'} relative to a survey "
            f"that measured the three on the same elderly respondents.")


def plot(cmp: pd.DataFrame, out: Path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[warn] matplotlib missing -> no figure."); return
    d = cmp.dropna(subset=["real_노인실태조사", "synthetic_KVRB"])
    if d.empty:
        print("[warn] nothing to plot."); return
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(d)); wd = 0.38
    rv = [v*100 if u == "pp" else v for v, u in zip(d["real_노인실태조사"], d["unit"])]
    sv = [v*100 if u == "pp" else v for v, u in zip(d["synthetic_KVRB"], d["unit"])]
    ax.bar(x - wd/2, rv, wd, label="real (Survey of Older Koreans)")
    ax.bar(x + wd/2, sv, wd, label="synthetic (KVRB v3)")
    ax.set_xticks(x); ax.set_xticklabels(d["quantity"], rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("% (rate) or Cramér's V"); ax.legend()
    ax.set_title("External joint validation: KVRB vs Survey of Older Koreans (65+)")
    fig.tight_layout(); fig.savefig(out / "joint_external_noin.png", dpi=140)
    print(f"[fig] {out/'joint_external_noin.png'}")


def mock_frame() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 4000
    age = rng.integers(65, 90, n)
    # induce a real positive FV-SI dependence the synthetic CI model would miss
    base = rng.normal(0, 1, n)
    fv = np.clip(np.round(3 + base + rng.normal(0, .7, n)), 1, 5)
    si = np.clip(np.round(3 + .6*base + rng.normal(0, .8, n)), 1, 5)
    dl = np.clip(np.round(3 - .4*(age-77)/6 + rng.normal(0, .9, n)), 1, 5)
    return pd.DataFrame({"age": age, "w": rng.uniform(.5, 2, n),
                         "fv": fv.astype(int), "dl": dl.astype(int), "si": si.astype(int)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--noin", help="노인실태조사 microdata (.sav or .csv)")
    ap.add_argument("--kvrb", default="data/processed/enriched_1M_v3_parts")
    ap.add_argument("--out", default="results")
    ap.add_argument("--discover", action="store_true", help="print candidate column names and exit")
    ap.add_argument("--mock", action="store_true", help="dry-run on fabricated data (NOT a real result)")
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    if args.discover:
        if not args.noin:
            raise SystemExit("[fatal] --discover needs --noin path")
        df = load_noin(args.noin)
        kw = {"age": ["age", "나이", "연령"], "weight": ["weight", "가중", "wt"],
              "fv": ["경제", "소득", "생활비", "빈곤", "만족"],
              "dl": ["스마트", "인터넷", "정보", "디지털", "기기", "활용"],
              "si": ["독거", "혼자", "연락", "고립", "관계", "지지", "외출", "친구"]}
        print(f"[discover] {len(df.columns)} columns in {args.noin}\n")
        for tgt, ks in kw.items():
            hits = [c for c in df.columns if any(k in str(c) for k in ks)]
            print(f"  {tgt:7s} candidates: {hits[:25]}")
        print("\nFill NOIN_VARS + RULES in the CONFIG block, then re-run without --discover.")
        return

    if args.mock:
        print("[mock] fabricated data — pipeline check only, NOT a real validation result.")
        real_df = mock_frame()
        synth_df = mock_frame().assign(  # synthetic: break the FV-SI dependence (CI assumption)
            si=lambda d: np.clip(d["si"].sample(frac=1).values, 1, 5))
    else:
        if not args.noin:
            raise SystemExit("[fatal] need --noin (or use --mock). Run --discover first.")
        real_df = to_levels_noin(load_noin(args.noin))
        synth_df = load_kvrb_elderly(args.kvrb)

    real = quantities(real_df, "real_노인실태조사")
    synth = quantities(synth_df, "synthetic_KVRB")
    cmp = compare(real, synth)
    sentence = make_sentence(cmp, real, synth)

    cmp.to_csv(out / "joint_external_noin.csv", index=False, encoding="utf-8-sig")
    with open(out / "joint_external_noin.txt", "w", encoding="utf-8") as fh:
        fh.write("KVRB external joint validation vs 노인실태조사 (elderly 65+)\n")
        fh.write("=" * 70 + "\n")
        fh.write(f"real:      N={real['n']:,}  (weighted {real['n_eff_w']:.0f})\n")
        fh.write(f"synthetic: N={synth['n']:,}  (KVRB v3, age>={ELDERLY_MIN_AGE})\n\n")
        fh.write(cmp.to_string(index=False) + "\n\n")
        fh.write("READY-TO-PASTE §4.5 SENTENCE:\n" + sentence + "\n")
    plot(cmp, out)
    print(cmp.to_string(index=False))
    print("\n" + sentence)
    print(f"\n[ok] wrote {out/'joint_external_noin.csv'} / .txt / .png")


if __name__ == "__main__":
    main()
