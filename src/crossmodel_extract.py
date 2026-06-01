"""
crossmodel_extract.py — independent round-trip extraction (reviewer C2/C3, unanimous critical).

The round-trip in §4.2 had the same model write and read the narrative. This script re-extracts
each Likert level from the *already-generated* Gemini narratives using a DIFFERENT model (ideally a
different provider, e.g. OpenAI gpt-4o), so agreement becomes a between-model reliability coefficient
rather than within-model self-consistency. Narratives are reused, so this costs only the extraction
calls, not regeneration.

Output JSONL has the same shape validate_roundtrip.py consumes (attr + roundtrip_<attr>), so:
  python src/crossmodel_extract.py --in data/processed/enriched_stage23.jsonl \
      --provider openai --model gpt-4o-2024-11-20 --out data/processed/enriched_stage23_xmodel.jsonl
  python src/validate_roundtrip.py --in data/processed/enriched_stage23_xmodel.jsonl --out results_xmodel

A different provider gives the strongest evidence. A different model in the same family
(e.g. gemini-2.5-pro vs the gemini-2.5-flash generator) is weaker but still partly independent —
state which you used in §4.2.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from enrich_stage2_3 import ATTRS, extract_roundtrip  # reuse the same extraction logic


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/processed/enriched_stage23.jsonl")
    ap.add_argument("--out", default="data/processed/enriched_stage23_xmodel.jsonl")
    ap.add_argument("--provider", required=True, choices=["openai", "gemini"],
                    help="use a DIFFERENT provider/model than the generator")
    ap.add_argument("--model", required=True, help="pinned extractor model (e.g. gpt-4o-2024-11-20)")
    ap.add_argument("--n", type=int, default=0, help="0 = all records in the input")
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
    mism = {a: 0 for a in ATTRS}; n_eval = {a: 0 for a in ATTRS}
    with open(outp, "w", encoding="utf-8") as f:
        for i, rec in enumerate(recs, 1):
            narr = rec.get("attr_narrative", "")
            attr = rec.get("attr", {})
            rt = {}
            for a in ATTRS:
                got = extract_roundtrip(narr, a, args.provider, args.model, dry=False)
                time.sleep(0.1)
                rt[a] = got
                sampled = attr.get(a)
                if got is not None and sampled is not None:
                    n_eval[a] += 1
                    if got != sampled:
                        mism[a] += 1
            row = {"uuid": rec.get("uuid"), "attr": attr, "attr_narrative": narr,
                   "gen_meta": {"actual_model": (rec.get("gen_meta") or {}).get("actual_model"),
                                "extractor_model": args.model, "extractor_provider": args.provider}}
            for a in ATTRS:
                row[f"roundtrip_{a}"] = rt[a]
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            if i % 50 == 0:
                print(f"  ... {i}/{len(recs)}")

    print(f"[ok] cross-model extraction ({args.model}) on {len(recs)} records -> {outp}")
    print("[qa] cross-model exact agreement by attribute (vs sampled level):")
    for a in ATTRS:
        agree = 100 * (1 - mism[a] / n_eval[a]) if n_eval[a] else float("nan")
        print(f"   {a:<26} {agree:5.1f}%  (n={n_eval[a]})")
    print("[next] python src/validate_roundtrip.py --in", outp, "--out results_xmodel")


if __name__ == "__main__":
    main()
