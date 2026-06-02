"""
crossmodel_extract.py — independent round-trip extraction (reviewer C2/C3).

Re-extracts each Likert level from the *already-generated* narratives using a DIFFERENT model
(e.g. OpenAI gpt-4o), so agreement becomes a between-model reliability coefficient rather than
within-model self-consistency. Narratives are reused, so this costs only the extraction calls.

  py src/crossmodel_extract.py --in data/processed/enriched_stage23_N2000.jsonl \
      --provider openai --model gpt-4o-2024-11-20 --out data/processed/enriched_stage23_N2000_xmodel.jsonl
  py src/validate_roundtrip.py --in data/processed/enriched_stage23_N2000_xmodel.jsonl --out results_xmodel_N2000

Resumable: re-running the same command skips records already written to --out.
Key is read from the environment (OPENAI_API_KEY / GEMINI_API_KEY); never hard-code it.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from enrich_stage2_3 import ATTRS, extract_all, _retry   # combined extractor (all 4 attrs / record)


def load_done(outp):
    done = {}
    if outp.exists():
        for line in open(outp, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                if r.get("uuid") is not None:
                    done[r["uuid"]] = r
            except Exception:
                pass
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/processed/enriched_stage23.jsonl")
    ap.add_argument("--out", default="data/processed/enriched_stage23_xmodel.jsonl")
    ap.add_argument("--provider", required=True, choices=["openai", "gemini"])
    ap.add_argument("--model", required=True, help="pinned extractor model (e.g. gpt-4o-2024-11-20)")
    ap.add_argument("--n", type=int, default=0, help="0 = all records")
    args = ap.parse_args()

    recs = []
    with open(args.inp, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    if args.n:
        recs = recs[:args.n]

    gen_models = {(r.get("gen_meta") or {}).get("actual_model", "?") for r in recs}
    if args.model in gen_models:
        print(f"[warn] extractor model {args.model} equals a generator model — this is NOT cross-model.")

    outp = Path(args.out); outp.parent.mkdir(parents=True, exist_ok=True)
    done = load_done(outp)
    if done:
        print(f"[resume] {len(done)} records already extracted in {outp} -> skipping those")

    mism = {a: 0 for a in ATTRS}; n_eval = {a: 0 for a in ATTRS}
    written = 0
    with open(outp, "a", encoding="utf-8") as f:
        for i, rec in enumerate(recs, 1):
            uuid = rec.get("uuid")
            if uuid in done:
                rt = {a: done[uuid].get(f"roundtrip_{a}") for a in ATTRS}
            else:
                narr = rec.get("attr_narrative", "")
                rt = _retry(extract_all, narr, args.provider, args.model, False)  # {attr: level}, all 4
                row = {"uuid": uuid, "attr": rec.get("attr", {}), "attr_narrative": narr,
                       "gen_meta": {"actual_model": (rec.get("gen_meta") or {}).get("actual_model"),
                                    "extractor_model": args.model, "extractor_provider": args.provider}}
                for a in ATTRS:
                    row[f"roundtrip_{a}"] = (rt or {}).get(a)
                f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush()
                written += 1
            attr = rec.get("attr", {})
            for a in ATTRS:
                got = (rt or {}).get(a); samp = attr.get(a)
                if got is not None and samp is not None:
                    n_eval[a] += 1
                    if got != samp:
                        mism[a] += 1
            if i % 50 == 0:
                print(f"  ... {i}/{len(recs)} (new this run: {written})")

    print(f"[ok] cross-model extraction ({args.model}) on {len(recs)} records -> {outp}  (new this run: {written})")
    print("[qa] cross-model exact agreement by attribute (vs sampled level):")
    for a in ATTRS:
        agree = 100 * (1 - mism[a] / n_eval[a]) if n_eval[a] else float("nan")
        print(f"   {a:<26} {agree:5.1f}%  (n={n_eval[a]})")
    print(f"[next] py src/validate_roundtrip.py --in {outp} --out results_xmodel_N2000")


if __name__ == "__main__":
    main()
