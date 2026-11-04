"""Portable paths and provenance for the unchanged-model duration checks."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import sys

PACKAGE = Path(__file__).resolve().parent

def signature(path):
    path = Path(path)
    return {"bytes": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

def simulation_context(kind):
    parser = argparse.ArgumentParser(description="Run the original model over fixed observation horizons.")
    parser.add_argument("--repo-root", type=Path, default=PACKAGE.parent,
                        help="Repository containing src, results_v4, and reconstructed data.")
    parser.add_argument("--data-root", type=Path, default=None,
                        help="Optional root containing reconstructed data; defaults to --repo-root.")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="Output root; results are written in a model-specific subdirectory.")
    parser.add_argument("--baseline-only", action="store_true",
                        help="Run only the original 25-step diffusion or 20-step opinion horizon.")
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    data_root = args.data_root.resolve() if args.data_root is not None else repo
    output = (args.output_dir.resolve() / kind)
    if output.exists() and any(output.iterdir()):
        parser.error(f"Output directory must be new or empty: {output}")
    config = json.loads((PACKAGE / "config.json").read_text(encoding="utf-8"))
    if args.baseline_only:
        config["diffusion_steps"] = [25]
        config["opinion_steps"] = [20]
    part = data_root / "data/processed/enriched_1M_v4_parts/part_00.parquet"
    if not part.is_file():
        parser.error("Reconstruct the population first; data/processed/enriched_1M_v4_parts/part_00.parquet is required.")
    actual_input = signature(part)
    if actual_input["sha256"] != config["sample_part_sha256"]:
        parser.error("The first reconstructed population part differs from the published experiment input hash.")
    config["protected"] = {}
    for name, expected_hash in config["model_sha256"].items():
        path = repo / "src" / name
        normalized_hash = (hashlib.sha256(path.read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest()
                           if path.is_file() else None)
        if normalized_hash != expected_hash:
            parser.error(f"Original model source does not match its recorded hash: {name}")
        config["protected"][str(path)] = {"sha256": signature(path)["sha256"],
                                           "normalized_source_sha256": normalized_hash}
    import numpy, pandas, pyarrow
    config["versions"] = {"python": sys.version, "numpy": numpy.__version__,
                          "pandas": pandas.__version__, "pyarrow": pyarrow.__version__}
    config["repo"] = str(repo)
    config["data_root"] = str(data_root)
    config["input_data"] = {str(part): actual_input}
    output.mkdir(parents=True, exist_ok=True)
    return config, repo, output

def analysis_context():
    parser = argparse.ArgumentParser(description="Recompute paired-seed contrasts and bootstrap intervals.")
    parser.add_argument("--input-dir", type=Path, required=True,
                        help="Read-only result root containing discriminate, decompose, and opinion outputs.")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="Output root; analysis tables and plots are written in its analysis subdirectory.")
    args = parser.parse_args()
    input_dir = args.input_dir.resolve()
    output = args.output_dir.resolve() / "analysis"
    if output.exists() and any(output.iterdir()):
        parser.error(f"Output directory must be new or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    config = json.loads((PACKAGE / "config.json").read_text(encoding="utf-8"))
    return config, input_dir, output
