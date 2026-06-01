"""
audit_microdata.py — Route B feasibility audit (run on Daniel's PC; needs raw microdata).

Answers the two questions that decide whether the joint-structure upgrade is buildable:
  (1) JOINT OBSERVABILITY — are the two attributes that share a survey actually answered by the
      SAME respondents? KGSS is a 2003-2021 cumulative file with item-specific waves, so authority
      (AUTHORT*) and isolation (SICK/BORROW/DOWN/NGHASK) items may sit on DIFFERENT respondents.
      We compute the overlap N where both are valid. KCVS reporting is victims-only, structurally
      nested in victimization, so PV x RP is observable by design — we confirm the Ns.
  (2) RICHER-CONDITIONING GRANULARITY (B1) — does each survey carry sex / education / region, and
      how small do cells get under age x sex x education? We list columns and flag candidates.

Set KVRB_DATA_ROOT to the folder holding the survey subfolders (e.g. Paper F 04_data). Requires
pyreadstat for .sav (pip install pyreadstat) and pandas. Nothing is written; it prints a report.

Usage (PowerShell):
  $env:KVRB_DATA_ROOT="C:\\...\\06_Paper_F_SSCI_BDS\\04_data"
  py src/audit_microdata.py
"""
from __future__ import annotations
import os, re
from pathlib import Path

ROOT = os.environ.get("KVRB_DATA_ROOT", "data/raw")
DEMO_PAT = re.compile(r"sex|gender|성별|educ|edu|degree|학력|학교|region|area|sido|지역|시도|province|도시",
                      re.I)


def banner(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def try_sav_meta(path):
    import pyreadstat
    df, meta = pyreadstat.read_sav(path, metadataonly=True)
    return meta.column_names


def audit_kgss():
    banner("KGSS  — authority_deference (AUTHORT2/4/5/6/7) x social_isolation (SICK1/BORROW1/DOWN1/NGHASK)")
    path = Path(ROOT) / "KGSS_2003_2021" / "Korean_data_CUM0048.sav"
    if not path.exists():
        print(f"[missing] {path}"); return
    try:
        import pyreadstat
        ad = ["AUTHORT2", "AUTHORT4", "AUTHORT5", "AUTHORT6", "AUTHORT7"]
        si = ["SICK1", "BORROW1", "DOWN1", "NGHASK"]
        demo = ["AGE", "SEX", "EDUC", "DEGREE", "REGION", "SIDO", "AREA", "FINALWT"]
        cols_all = try_sav_meta(path)
        want = [c for c in ad + si + demo if c in cols_all]
        df, _ = pyreadstat.read_sav(path, usecols=want)
        import pandas as pd
        ad_present = [c for c in ad if c in df.columns]
        si_present = [c for c in si if c in df.columns]
        ad_valid = (df[ad_present].apply(lambda s: (s >= 1) & (s <= 5)).sum(axis=1) >= 3) if ad_present else None
        si_valid = (df[si_present].notna().sum(axis=1) >= 1) if si_present else None
        print(f"total rows: {len(df):,}")
        print(f"AD items present: {ad_present}  valid-AD N: {int(ad_valid.sum()) if ad_valid is not None else 'NA'}")
        print(f"SI items present: {si_present}  valid-SI N: {int(si_valid.sum()) if si_valid is not None else 'NA'}")
        if ad_valid is not None and si_valid is not None:
            overlap = int((ad_valid & si_valid).sum())
            print(f"*** AD x SI JOINT-OBSERVABLE overlap N = {overlap:,} ***  "
                  f"-> {'B2 feasible for AD x SI' if overlap >= 300 else 'TOO SMALL — AD x SI joint NOT feasible (different waves)'}")
        demo_present = [c for c in cols_all if DEMO_PAT.search(c)]
        print(f"demographic-candidate columns: {demo_present[:20]}")
    except ImportError:
        print("[need] pip install pyreadstat")
    except Exception as e:
        print(f"[error] {e}")


def audit_kcvs():
    banner("KCVS 2018 — prior_victimization (bct_1) x reporting_propensity (victims-only)")
    path = Path(ROOT) / "KCVS_2018" / "kcvs2018.sav"
    if not path.exists():
        print(f"[missing] {path}"); return
    try:
        import pyreadstat, pandas as pd
        cols_all = try_sav_meta(path)
        want = [c for c in ["bct_1", "c24", "bh4_02", "wt3"] if c in cols_all]
        df, _ = pyreadstat.read_sav(path, usecols=want)
        print(f"total rows: {len(df):,}")
        if "bct_1" in df.columns:
            vic = pd.to_numeric(df["bct_1"], errors="coerce")
            nv = int((vic > 0).sum()) if vic.notna().any() else 0
            print(f"victims (bct_1>0): {nv:,}  -> PV x RP nested & observable (RP defined on victims)")
        demo_present = [c for c in cols_all if DEMO_PAT.search(c)]
        print(f"all columns: {len(cols_all)} | demographic-candidate: {demo_present[:25]}")
    except ImportError:
        print("[need] pip install pyreadstat")
    except Exception as e:
        print(f"[error] {e}")


def audit_csv(label, rel, enc="utf-8"):
    banner(label)
    path = Path(ROOT) / rel
    cands = list(Path(ROOT).glob(rel)) if any(ch in rel for ch in "*?") else ([path] if path.exists() else [])
    if not cands:
        print(f"[missing] {path}  (adjust filename; listing {Path(ROOT)} subdirs:)")
        for p in sorted(Path(ROOT).glob("*"))[:30]:
            print("   ", p.name)
        return
    try:
        import pandas as pd
        p = cands[0]
        df = pd.read_csv(p, encoding=enc, nrows=5000)
        print(f"file: {p.name}  cols: {len(df.columns)}")
        demo_present = [c for c in df.columns if DEMO_PAT.search(str(c))]
        print(f"demographic-candidate columns: {demo_present[:25]}")
        print(f"first 25 columns: {list(df.columns)[:25]}")
    except Exception as e:
        print(f"[error] {e} — try a different --encoding (cp949 for 가금복)")


def main():
    print(f"KVRB_DATA_ROOT = {ROOT}")
    if not Path(ROOT).exists():
        print(f"[fatal] data root not found: {ROOT}\nSet $env:KVRB_DATA_ROOT to the folder with the survey subfolders.")
        return
    audit_kgss()
    audit_kcvs()
    audit_csv("가계금융복지조사 (financial_vulnerability) — list columns (cp949)",
              "*가계금융*"  , enc="cp949")
    audit_csv("디지털정보격차 (digital_literacy) — list columns",
              "*디지털*")
    banner("VERDICT GUIDE")
    print("- AD x SI overlap >= ~300  -> B2 joint sampling feasible for that pair.")
    print("- KCVS victims N usable    -> PV x RP joint feasible.")
    print("- For B1: confirm sex + education columns exist in each survey; region optional.")
    print("- Paste this whole report back to Claude to finalize the B1/B2 plan.")


if __name__ == "__main__":
    main()
