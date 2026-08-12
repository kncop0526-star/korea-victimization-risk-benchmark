#!/usr/bin/env python3
"""check_prose.py — prose checks used while revising manuscript 2026:161:1.

Flags, in a plain-text or Markdown file:
  1. long sentences        (> --max-words, default 45; warn at >35)
  2. stacked clauses       (>2 subordinate/relative/participial joins in one
                            sentence, warn)
  3. unclear referents     (sentence-initial This/That/These/Those + verb;
                            a bare quantifier such as "the six" or "the other
                            one" standing in for an unnamed noun)
  4. undefined acronyms    (repeated ALL-CAPS tokens never expanded, warn)
  5. vocabulary check      (--glossary: JSON mapping a canonical term to
                            banned near-synonyms, e.g. enforcing the
                            anchor-survey / anchor-table distinction)

Usage:
  python check_prose.py MANUSCRIPT.md [--max-words 45] [--glossary terms.json]

Exit code 0 = no failures (warnings allowed), 1 = failures found.
Standard library only.
"""
import argparse, json, re, sys

CLAUSE_MARKERS = re.compile(
    r"\b(which|that|who|whose|whom|where|when|while|although|though|because|"
    r"since|unless|whereas|so that)\b|;|—", re.I)
# a quantifier acting as the noun itself: "The six are...", "the other one."
BARE_QUANT = re.compile(
    r"(?<!between )(?<!of )(?<!among )"
    r"\b[Tt]he (one|two|three|four|five|six|seven|eight|nine|ten|former|"
    r"latter|other one)(?=\s*[,.;:)]|\s+(is|are|was|were|has|have|had|does|"
    r"do|did|carries|carry|holds|hold|comes|come|goes|go|matters|matter|"
    r"gives|give|remains|remain)\b)")
THIS_VERB = re.compile(
    r"^(This|That|These|Those)\s+(is|are|was|were|has|have|had|does|do|did|"
    r"reads|shows|means|matters|holds|makes|gives|comes|goes|leaves|leads)\b")
KNOWN = {"USA", "III", "II", "DOI", "URL", "ISBN", "MIT", "AND", "NOT", "CC",
         "BY", "CI", "SD", "API", "CSV", "JSON", "PDF", "SVG", "PNG", "DPI",
         "NVIDIA", "RQ1", "RQ2", "RQ3"}


def sentences(text):
    text = re.sub(r"^\|.*$", "", text, flags=re.M)          # tables
    text = re.sub(r"^#+ .*$", "", text, flags=re.M)         # headings
    text = re.sub(r"`[^`]*`", "", text)                     # code spans
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)          # bold markers
    text = re.sub(r"\*([^*\n]+)\*", r"\1", text)            # italic markers
    out = []
    for block in re.split(r"\n\s*\n|\n(?=[-*] )", text):    # paragraph bounds
        block = " ".join(block.split())
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z“(])", block):
            if len(s.split()) >= 4:
                out.append(s.strip())
    return list(enumerate(out, 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--max-words", type=int, default=45)
    ap.add_argument("--glossary", help='JSON: {"canonical": ["banned", ...]}')
    a = ap.parse_args()
    text = open(a.file, encoding="utf-8").read()
    fails = warns = 0

    for i, s in sentences(text):
        n = len(s.split())
        if n > a.max_words:
            fails += 1
            print(f"[FAIL] long-sentence  #{i:4d} {n}w: {s[:90]}...")
        elif n > 35:
            warns += 1
            print(f"[warn] long-sentence  #{i:4d} {n}w: {s[:90]}...")
        if len(CLAUSE_MARKERS.findall(s)) > 2 and n > 25:
            warns += 1
            print(f"[warn] stacked-clause #{i:4d}: {s[:90]}...")
        m = THIS_VERB.match(s)
        if m:
            fails += 1
            print(f"[FAIL] bare-referent  #{i:4d} '{m.group(0)}...': {s[:90]}...")
        m = BARE_QUANT.search(s)
        if m:
            fails += 1
            print(f"[FAIL] bare-quant     #{i:4d} '{m.group(0)}': {s[:90]}...")

    # an acronym counts as expanded if it appears as "(ACRO)" after its
    # expansion, or is itself followed by a parenthesized expansion.
    acronyms = set(re.findall(r"\b[A-Z]{2,6}\b", text))
    expanded = set(re.findall(r"\(([A-Z]{2,6})\)", text))
    expanded |= set(re.findall(r"\b([A-Z]{2,6})\s*\((?=[A-Z][a-z])", text))
    for ac in sorted(acronyms - expanded - KNOWN):
        uses = len(re.findall(r"\b" + ac + r"\b", text))
        if uses >= 3:
            warns += 1
            print(f"[warn] acronym        '{ac}' used {uses}x, never expanded")

    if a.glossary:
        gl = json.load(open(a.glossary, encoding="utf-8"))
        for canon, banned in gl.items():
            for b in banned:
                hits = len(re.findall(r"\b" + re.escape(b) + r"\b", text, re.I))
                if hits:
                    fails += 1
                    print(f"[FAIL] vocabulary     '{b}' x{hits} (use '{canon}')")

    print(f"\n{fails} failure(s), {warns} warning(s).")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
