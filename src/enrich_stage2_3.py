"""
enrich_stage2_3.py
------------------------------------------------------------------
Stage 2 (LLM narrative realization) + Stage 3 (round-trip audit) on a Stage-1 enriched dataset.

Design guarantees:
  * The LLM is told the attribute values are FIXED inputs to express, NOT estimated.
  * Model snapshot is PINNED; the actual responding model id is captured per record.
  * No API key is hard-coded — read from an environment variable.
  * --dry-run uses a deterministic stub so the pipeline runs with no key.

Robustness (added 2026-05-31, for N=2000 runs):
  * ONE combined extraction call recovers all four Likert levels per narrative (2 API calls/record
    instead of 5) — large quota saving.
  * Retry with exponential backoff on any API error (rate limit / transient).
  * RESUME: re-running with the same --out skips records already written (append mode), so a run that
    dies on a daily/RPM limit can be continued later without redoing work.
  * Per-record error tolerance: a record that still fails after retries is logged to stdout and skipped,
    not fatal. The [qa] summary is recomputed from the whole output file (resume-safe).

Providers: set ONE of
  OPENAI_API_KEY   (+ --provider openai  --model gpt-4o-2024-11-20)
  GEMINI_API_KEY   (+ --provider gemini  --model gemini-2.5-flash)

Usage:
  py src/enrich_stage2_3.py --in data/processed/roundtrip_input_stratified_2000.csv \
     --provider gemini --model gemini-2.5-flash --n 2000 --out data/processed/enriched_stage23_N2000.jsonl
  py src/enrich_stage2_3.py --in ... --dry-run        # no key needed
------------------------------------------------------------------
"""

from __future__ import annotations
import argparse, json, os, re, time
from pathlib import Path
import pandas as pd

ATTRS = ["financial_vulnerability", "digital_literacy", "authority_deference", "social_isolation"]

LEVEL_WORDS = {
    "financial_vulnerability": {
        1: "재정적으로 안정", 2: "재정에 여유가 있는 편", 3: "재정 상태는 보통",
        4: "재정적으로 빠듯", 5: "재정적으로 매우 취약"},
    "digital_literacy": {
        1: "디지털 기기 사용에 큰 어려움", 2: "디지털 사용이 익숙하지 않",
        3: "기본적 디지털 사용", 4: "디지털을 무리 없이", 5: "디지털에 매우 능숙"},
    "authority_deference": {
        1: "권위에 거의 순응하지 않", 2: "권위에 잘 따르지 않는 편",
        3: "권위에 보통 수준으로 순응", 4: "권위에 잘 따르는 편", 5: "권위에 매우 순응적"},
    "social_isolation": {
        1: "사회적으로 거의 고립되지 않", 2: "사회적 교류가 있는 편",
        3: "사회적 고립은 보통", 4: "사회적으로 다소 고립", 5: "사회적으로 매우 고립"},
}
ATTR_KO = {
    "financial_vulnerability": "재정 취약성", "digital_literacy": "디지털 활용 수준",
    "authority_deference": "권위 순응 정도", "social_isolation": "사회적 고립 정도",
}


def _vals(rec):
    return {a: int(rec["attr_" + a]) for a in ATTRS
            if ("attr_" + a) in rec and pd.notna(rec["attr_" + a])}


def build_prompt(rec):
    vals = _vals(rec)
    demo = {k: rec[k] for k in ["sex", "age", "education_level", "province", "occupation", "family_type"]
            if k in rec}
    return (
        "다음은 합성 페르소나의 인구통계와, 실제 조사 분포에서 '이미 정해진' 속성값(1~5)이다.\n"
        "이 값들은 고정 입력이다. 추정하거나 바꾸지 말고, 값과 모순되지 않는 1인칭 한국어 서술(4~6문장)만 작성하라.\n"
        "네 속성(재정 취약성/디지털 활용/권위 순응/사회적 고립) 각각이 서술에서 드러나야 한다.\n"
        f"인구통계: {json.dumps(demo, ensure_ascii=False)}\n"
        f"고정 속성값(1=낮음~5=높음): {json.dumps(vals, ensure_ascii=False)}\n"
        "서술:"
    )


def _gemini_text(r):
    try:
        cands = getattr(r, "candidates", None) or []
        for c in cands:
            content = getattr(c, "content", None)
            parts = getattr(content, "parts", None) if content else None
            if parts:
                txt = "".join(getattr(p, "text", "") or "" for p in parts)
                if txt.strip():
                    return txt.strip()
        return ""
    except Exception:
        return ""


_OPENAI_CLI = None
_GEMINI_READY = False


def call_llm(prompt, provider, model):
    global _OPENAI_CLI, _GEMINI_READY
    if provider == "openai":
        from openai import OpenAI
        if _OPENAI_CLI is None:
            key = os.environ.get("OPENAI_API_KEY")
            if not key:
                raise RuntimeError("OPENAI_API_KEY not set")
            _OPENAI_CLI = OpenAI(api_key=key)
        r = _OPENAI_CLI.chat.completions.create(model=model, temperature=0.7,
                                                messages=[{"role": "user", "content": prompt}])
        return r.choices[0].message.content.strip(), getattr(r, "model", model)
    if provider == "gemini":
        import google.generativeai as genai
        if not _GEMINI_READY:
            key = os.environ.get("GEMINI_API_KEY")
            if not key:
                raise RuntimeError("GEMINI_API_KEY not set")
            genai.configure(api_key=key)
            _GEMINI_READY = True
        r = genai.GenerativeModel(model).generate_content(prompt)
        return _gemini_text(r), model
    raise ValueError("unknown provider: " + provider)


def _retry(fn, *a, tries=6, base=4.0, **k):
    """Call fn with exponential backoff on any exception (rate-limit/transient)."""
    last = None
    for i in range(tries):
        try:
            return fn(*a, **k)
        except Exception as e:
            last = e
            wait = base * (2 ** i)
            print(f"   [retry {i+1}/{tries}] {type(e).__name__}: {str(e)[:120]} -> wait {wait:.0f}s", flush=True)
            time.sleep(wait)
    raise last


def stub_llm(rec):
    vals = _vals(rec)
    sents = [f"{rec.get('age','')}세 {rec.get('sex','')}."]
    for a in ATTRS:
        if a in vals:
            sents.append(f"{LEVEL_WORDS[a][vals[a]]} 상태다.")
    sents.append("(STUB narrative — replace with pinned LLM output.)")
    return " ".join(sents), "STUB-not-a-real-model"


def extract_all(narrative, provider, model, dry):
    """Recover ALL four Likert levels from one narrative. Real pass = ONE combined call."""
    if dry or provider == "stub":
        out = {}
        for a in ATTRS:
            out[a] = next((lv for lv, ph in LEVEL_WORDS[a].items() if ph in narrative), None)
        return out
    q = ("다음 1인칭 서술을 읽고, 글쓴이의 네 속성을 각각 1~5 정수로 평가하라.\n"
         "재정 취약성/디지털 활용 수준/권위 순응 정도/사회적 고립 정도.\n"
         "오직 아래 JSON 형식으로만 답하라(설명 금지):\n"
         '{"financial_vulnerability":n,"digital_literacy":n,"authority_deference":n,"social_isolation":n}\n\n'
         + narrative)
    txt, _ = call_llm(q, provider, model)
    out = {}
    try:
        m = re.search(r"\{.*\}", txt, re.S)
        obj = json.loads(m.group()) if m else {}
        for a in ATTRS:
            v = obj.get(a)
            out[a] = int(v) if v is not None and 1 <= int(v) <= 5 else None
    except Exception:
        for a in ATTRS:
            out[a] = None
    return out


def load_done(outp):
    done = set()
    if outp.exists():
        with open(outp, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    done.add(json.loads(line).get("uuid"))
                except Exception:
                    pass
    return done


def qa_from_file(outp):
    mism = {a: 0 for a in ATTRS}; n_eval = {a: 0 for a in ATTRS}; n = 0
    with open(outp, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line); n += 1
            for a in ATTRS:
                got = r.get(f"roundtrip_{a}"); samp = (r.get("attr") or {}).get(a)
                if got is not None and samp is not None:
                    n_eval[a] += 1
                    if int(got) != int(samp):
                        mism[a] += 1
    return mism, n_eval, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", default="data/processed/enriched_stage23.jsonl")
    ap.add_argument("--provider", default="stub", choices=["stub", "openai", "gemini"])
    ap.add_argument("--model", default="", help="PINNED dated snapshot (no floating alias)")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--sleep", type=float, default=1.0, help="seconds between records (pace API)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    dry = args.dry_run or args.provider == "stub"
    if not dry and not args.model:
        raise SystemExit("Pass a pinned --model snapshot (e.g., gemini-2.5-flash).")

    df = pd.read_csv(args.inp).head(args.n)
    outp = Path(args.out); outp.parent.mkdir(parents=True, exist_ok=True)
    done = load_done(outp)
    if done:
        print(f"[resume] {len(done)} records already in {outp.name}; skipping those.", flush=True)

    written = 0; errors = 0; processed = 0
    with open(outp, "a", encoding="utf-8") as f:
        for _, rec in df.iterrows():
            processed += 1
            uid = rec.get("uuid")
            if uid in done:
                continue
            try:
                if dry:
                    narr, actual = stub_llm(rec)
                else:
                    narr, actual = _retry(call_llm, build_prompt(rec), args.provider, args.model)
                    if not narr:
                        raise RuntimeError("empty narrative")
                    time.sleep(args.sleep)
                    rt = _retry(extract_all, narr, args.provider, args.model, dry)
                if dry:
                    rt = extract_all(narr, args.provider, args.model, dry)
                flags = []
                for a in ATTRS:
                    samp = int(rec["attr_" + a]) if pd.notna(rec.get("attr_" + a)) else None
                    if rt.get(a) is not None and samp is not None and rt[a] != samp:
                        flags.append(a)
                row = {
                    "uuid": uid,
                    "attr": {a: (int(rec["attr_" + a]) if pd.notna(rec.get("attr_" + a)) else None) for a in ATTRS},
                    "attr_narrative": narr,
                    "roundtrip_mismatch_any": bool(flags),
                    "roundtrip_mismatch_attrs": flags,
                    "gen_meta": {"actual_model": actual, "provider": args.provider, "pinned_model": args.model or None},
                }
                for a in ATTRS:
                    row[f"roundtrip_{a}"] = rt.get(a)
                f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush()
                written += 1
            except Exception as e:
                errors += 1
                print(f"   [err] record {processed} uuid={uid}: {type(e).__name__}: {str(e)[:160]}", flush=True)
            if processed % 25 == 0:
                print(f"[..] {processed}/{len(df)}  written={written} err={errors}", flush=True)

    mism, n_eval, ntot = qa_from_file(outp)
    print(f"[ok] Stage2/3 wrote {written} new (err {errors}); output now holds {ntot} records -> {outp}", flush=True)
    print("[qa] round-trip agreement by attribute (whole file):")
    for a in ATTRS:
        agree = 100 * (1 - mism[a] / n_eval[a]) if n_eval[a] else float("nan")
        print(f"   {a:<26} {agree:5.1f}%  (n={n_eval[a]})")
    if dry:
        print("[note] DRY/STUB run — wire a pinned LLM (provider+key+model) for the real pass.")


if __name__ == "__main__":
    main()
