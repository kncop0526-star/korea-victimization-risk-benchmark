"""recompute_bootstrap_ci.py — 본문 §4.2 bootstrap CI 재산출 (v2, 정의 일치판).

v1 문제
  1차 실행에서 점추정 2.64가 나와 본문 2.30과 어긋났다. 원인은 극단 정의 재구성 오류:
  - SI: 원본은 "3개 지지 항목 중 충족 개수 <= 1"(99=무응답→NaN, 유효응답 >= 2 요구).
        v1은 "셋 다 0"으로 더 좁게 잡았고 99를 지지 있음으로 오처리했다.
  - FV: 원본은 소득 5분위 코드 반전(fv = 6 - 분위, fv >= 4 = 하위 2분위).
        v1은 가중 순위 백분위 40%로 잡았다.
  이 버전은 validate_joint_external_noin2023.py의 플래그 구성을 **그대로 복사**한다.

안전 게이트
  점추정이 커밋된 값 2.3026(= 0.047897/0.020802, joint_external_noin2023_full.json)과
  ±0.01 안에서 일치하지 않으면 본문용 문장을 출력하지 않고 실패로 종료한다.
  일치하는 경우에만 CI를 신뢰한다.

사용 (repo 루트에서)
  py src\\recompute_bootstrap_ci.py --boot 2000 --seed 42
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CSV = REPO / "data/raw/노인실태조사_2023/2023_총괄_20260601_13406.csv"

AGE = "노인 조사대상자 만연령"
W = "가중치 모수추정(사후층화 가중치)"
INC = "연가구소득"
SUP = ["도움받을 수 있는 사람 수_우울할 때",
       "도움받을 수 있는 사람 수_몸이 아플 때",
       "도움받을 수 있는 사람 수_돈을 빌려야 할 때"]

COMMITTED_POINT = 2.3026   # results_v4/joint_external_noin2023_full.json 에서 재계산된 값
TOL = 0.01


def build_frame() -> pd.DataFrame:
    """validate_joint_external_noin2023.py 의 REAL 블록을 그대로 재현."""
    df = pd.read_csv(CSV, encoding="cp949", dtype=str)
    n = lambda c: pd.to_numeric(df[c], errors="coerce")
    R = pd.DataFrame()
    R["age"] = n(AGE)
    R["w"] = n(W)
    # FV: 소득 5분위 반전 (1=최저소득 → FV5 최취약)
    R["fv"] = 6 - n(INC)
    # DL: '전자기기 활동여부_' 13개 중 '예'(==1) 개수 → 레벨 1..5
    dlcols = [c for c in df.columns if c.startswith("전자기기 활동여부_")]
    assert len(dlcols) == 13, f"전자기기 활동 컬럼 {len(dlcols)}개 (13개여야 함)"
    dlcount = sum((n(c) == 1).astype(int) for c in dlcols)
    R["dl"] = pd.cut(dlcount, [-1, 0, 2, 5, 9, 13], labels=[1, 2, 3, 4, 5]).astype("float")
    # SI: 지지 3항목 중 충족(>=1명) 개수. 99=무응답→NaN, 유효응답 >= 2 요구.
    sup = [n(c).where(n(c) < 99) for c in SUP]
    needs_valid = sum(s.notna().astype(int) for s in sup)
    needs_cov = sum((s > 0).astype(int) for s in sup)
    R["needs_cov"] = needs_cov.where(needs_valid >= 2)
    R["si"] = R["needs_cov"].map({0: 5, 1: 4, 2: 2, 3: 1})
    return R[R["age"] >= 65].reset_index(drop=True)


def ratio(R: pd.DataFrame, idx=None) -> float:
    d = R if idx is None else R.iloc[idx]
    w = d["w"].fillna(0.0)
    tot = w.sum()
    if tot <= 0:
        return np.nan
    def wrate(mask):
        m = mask.fillna(False).values
        return float(w[m].sum() / tot)
    p_fv = wrate(d["fv"] >= 4)
    p_dl = wrate(d["dl"] <= 2)
    p_si = wrate(d["si"] >= 4)
    ext = wrate((d["fv"] >= 4) & (d["dl"] <= 2) & (d["si"] >= 4))
    ind = p_fv * p_dl * p_si
    return ext / ind if ind > 0 else np.nan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="results_v4")
    a = ap.parse_args()

    if not CSV.exists():
        raise SystemExit(f"[ERR] 원자료 없음: {CSV}")

    R = build_frame()
    point = ratio(R)
    print(f"점추정: {point:.4f}  (커밋값 {COMMITTED_POINT}, 허용오차 ±{TOL})")

    if abs(point - COMMITTED_POINT) > TOL:
        raise SystemExit(
            "[FAIL] 점추정이 커밋값과 일치하지 않습니다. 정의가 아직 어긋나 있으므로 "
            "이 CI는 사용 금지입니다. 이 출력을 Claude에게 그대로 전달해 주세요.")

    print("[OK] 점추정 일치 — CI 산출 진행")
    rng = np.random.default_rng(a.seed)
    n = len(R)
    boots = np.empty(a.boot)
    for i in range(a.boot):
        boots[i] = ratio(R, rng.integers(0, n, n))
        if (i + 1) % 200 == 0:
            print(f"  ...{i+1}/{a.boot}")
    boots = boots[np.isfinite(boots)]
    lo, hi = np.percentile(boots, [2.5, 97.5])

    out = REPO / a.out
    out.mkdir(parents=True, exist_ok=True)
    txt = (f"Bootstrap CI for the elderly compound-extreme dependence ratio (v2, definitions matched)\n"
           f"source: {CSV.name}  (N={n:,}, aged 65+)\n"
           f"point estimate : {point:.4f}  (matches committed 2.3026)\n"
           f"95% percentile CI : {lo:.4f} - {hi:.4f}\n"
           f"resamples : {len(boots):,} (seed {a.seed})\n"
           f"method : respondent-level resampling with replacement; weighted marginals,\n"
           f"         simultaneous-extreme rate, and independence-implied rate recomputed\n"
           f"         within each resample; percentile interval of their ratio.\n"
           f"flag definitions identical to validate_joint_external_noin2023.py\n")
    (out / "bootstrap_ci_dependence.txt").write_text(txt, encoding="utf-8")
    print("\n" + txt)
    print("=" * 70)
    print("본문 §4.2 문장:")
    print(f"  **{point:.2f} times** the independence baseline (95% bootstrap CI {lo:.2f}–{hi:.2f})")
    print("=" * 70)
    print(f"[대조] 본문 현재 CI = 2.12–2.49")


if __name__ == "__main__":
    main()
