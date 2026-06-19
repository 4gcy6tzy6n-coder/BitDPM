#!/usr/bin/env python3
"""Check whether current BitDPM artifacts satisfy the AAAI submission gate.

This is a conservative artifact audit. It does not run inference and it does
not infer success from plans or command files. A gate is marked passed only when
current generated artifacts prove it.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Gate:
    name: str
    status: str
    evidence: str
    requirement: str


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def has_text(path: Path, needle: str) -> bool:
    return path.exists() and needle in path.read_text(encoding="utf-8")


def latest_json(directory: Path, pattern: str) -> Path | None:
    if not directory.exists():
        return None
    matches = sorted(directory.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def gate_status(passed: bool, partial: bool = False) -> str:
    if passed:
        return "PASS"
    if partial:
        return "PARTIAL"
    return "FAIL"


def check_v31(root: Path) -> Gate:
    audit = root / "experiments/reports/bitdpm_v31_provenance_audit.md"
    unrecovered = has_text(audit, "Status: **UNRECOVERED**")
    recovered = has_text(audit, "Status: **RECOVERED**")
    return Gate(
        "Provenance-complete main result",
        gate_status(recovered),
        f"{audit.relative_to(root)}: {'RECOVERED' if recovered else 'UNRECOVERED' if unrecovered else 'missing/unknown'}",
        "Recover exact v31 provenance or train/replay a compatible main block with model, block path, SHA256, benchmark, decoding, and max-token metadata.",
    )


def check_v1k(root: Path) -> Gate:
    report = latest_json(root / "experiments/reports", "aaai_v1k_clean_current_pool_*.json")
    if report is None:
        return Gate(
            "1k-clean main validation",
            "FAIL",
            "No `experiments/reports/aaai_v1k_clean_current_pool_*.json` report found.",
            "Run `bash experiments/reports/aaai_main_experiment_commands.sh` and produce v1k_clean baseline/fixed/oracle/router/Always-All results.",
        )
    data = load_json(report)
    n = int(data.get("total_prompts", 0))
    baseline = float(data.get("config_results", {}).get("baseline", {}).get("overall", 0.0))
    oracle = float(data.get("oracle", {}).get("overall", 0.0))
    passed = n >= 1000 and oracle > baseline
    return Gate(
        "1k-clean main validation",
        gate_status(passed, partial=n >= 1000),
        f"{report.relative_to(root)}: n={n}, baseline={baseline:.3f}, oracle={oracle:.3f}",
        "Need n>=1000 and oracle above baseline; router result should also be evaluated on v1k_clean.",
    )


def check_benchmark_overlap(root: Path) -> Gate:
    manifest = root / "experiments/reports/bitdpm_benchmark_manifest.json"
    if not manifest.exists():
        return Gate(
            "Benchmark held-out audit",
            "FAIL",
            "No `experiments/reports/bitdpm_benchmark_manifest.json` report found.",
            "Run `python scripts/build_benchmark_manifest.py` and verify v1k exact prompt overlap is zero against prior validation sets.",
        )
    data = load_json(manifest)
    matrix = data.get("overlap_matrix", {})
    benchmark = "v1k_clean"
    overlaps = {
        prior: int(matrix.get(benchmark, {}).get(prior, 0))
        for prior in ["core", "v08", "v14", "v15"]
    }
    passed = all(count == 0 for count in overlaps.values())
    evidence = ", ".join(f"{benchmark}∩{name}={count}" for name, count in overlaps.items())
    return Gate(
        "Benchmark held-out audit",
        gate_status(passed),
        f"{manifest.relative_to(root)}: {evidence}",
        "Need zero exact normalized prompt overlap between the paper-scale v1k_clean benchmark and earlier core/v08/v14/v15 validation sets before calling it held-out.",
    )


def check_router(root: Path) -> Gate:
    v14 = root / "experiments/reports/v12_router/v14_full_v11_utility_router_allow_core_nolog_cv_crossval.json"
    v15 = root / "experiments/reports/v12_router/v15_router_validation_v11_admitted_allow_core_nolog_cv_crossval.json"
    if not v14.exists() or not v15.exists():
        return Gate(
            "Held-out conservative router",
            "FAIL",
            "Missing v14 or v15 allow-core-no-log strict-CV report.",
            "Need held-out router reports with positive or non-negative net and low breaks.",
        )
    rows = []
    passed = True
    for path in [v14, v15]:
        summary = load_json(path)["summary"]
        delta = float(summary.get("delta", 0.0))
        fixes = int(summary.get("fixes", 0))
        breaks = int(summary.get("breaks", 0))
        rows.append(f"{path.relative_to(root)}: delta={delta:+.3f}, fixes={fixes}, breaks={breaks}")
        passed = passed and delta > 0 and breaks == 0 and fixes > 0
    return Gate(
        "Held-out conservative router",
        gate_status(passed),
        "; ".join(rows),
        "Need positive held-out router net with zero or very low breaks on at least two benchmarks.",
    )


def check_external_baselines(root: Path) -> Gate:
    benchmarks = ["v14", "v15", "v1k_clean"]
    parts = []
    completed = 0
    required = len(benchmarks) * 2
    for benchmark in benchmarks:
        prompt = latest_json(root / "experiments/reports/prompt_only", f"prompt_only_*_{benchmark}_*.json")
        lora = latest_json(root / "experiments/reports/lora_baseline", f"lora_*_{benchmark}_*.json")
        if prompt:
            completed += 1
            prompt_status = prompt.relative_to(root)
        else:
            prompt_status = "missing"
        if lora:
            completed += 1
            lora_status = lora.relative_to(root)
        else:
            lora_status = "missing"
        parts.append(f"{benchmark}: prompt-only={prompt_status}, lora={lora_status}")
    passed = completed == required
    partial = 0 < completed < required
    return Gate(
        "External baselines",
        gate_status(passed, partial=partial),
        "; ".join(parts),
        "Need completed prompt-only and standard LoRA/always-on adapter results on v14, v15, and v1k_clean.",
    )


def check_ablation(root: Path) -> Gate:
    path = root / "experiments/reports/bitdpm_aaai_ablation_table.md"
    tokens = ["Block Capacity", "Admission", "Benchmark Transfer", "Router Safety"]
    passed = path.exists() and all(token in path.read_text(encoding="utf-8") for token in tokens)
    return Gate(
        "Consolidated ablations",
        gate_status(passed),
        f"{path.relative_to(root)}: {'present' if path.exists() else 'missing'}",
        "Need consolidated rank/scale/admission/transfer/router ablation table generated from artifacts.",
    )


def check_statistics(root: Path) -> Gate:
    paths = [
        root / "experiments/reports/bitdpm_v14_full_bootstrap_ci.md",
        root / "experiments/reports/bitdpm_v14_allow_core_nolog_cv_bootstrap_ci.md",
    ]
    passed = all(path.exists() and "95% CI" in path.read_text(encoding="utf-8") for path in paths)
    return Gate(
        "Statistical reporting",
        gate_status(passed),
        "; ".join(f"{path.relative_to(root)}={'present' if path.exists() else 'missing'}" for path in paths),
        "Need bootstrap confidence intervals for main benchmark and deployable router deltas.",
    )


def check_paper_package(root: Path) -> Gate:
    required = [
        root / "paper/bitdpm_aaai_draft.md",
        root / "paper/claim_to_evidence.md",
        root / "paper/aaai_main_experiment_protocol.md",
        root / "experiments/reports/bitdpm_paper_artifact_index.md",
    ]
    passed = all(path.exists() for path in required)
    return Gate(
        "Paper package and claim discipline",
        gate_status(passed),
        "; ".join(f"{path.relative_to(root)}={'present' if path.exists() else 'missing'}" for path in required),
        "Need paper draft, claim-to-evidence map, experiment protocol, and artifact index.",
    )


def make_report(gates: list[Gate]) -> str:
    overall = "PASS" if all(g.status == "PASS" for g in gates) else "NOT READY"
    lines = [
        "# BitDPM AAAI Submission Gate Check",
        "",
        f"Overall status: **{overall}**",
        "",
        "| Gate | Status | Evidence | Requirement |",
        "|---|---|---|---|",
    ]
    for gate in gates:
        lines.append(f"| {gate.name} | **{gate.status}** | {gate.evidence} | {gate.requirement} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `PASS` means current artifacts directly support the gate.",
            "- `PARTIAL` means infrastructure or partial results exist, but final evidence is incomplete.",
            "- `FAIL` means the required evidence is missing or contradicted.",
            "",
            "Do not claim high-confidence AAAI readiness while overall status is `NOT READY`.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check BitDPM AAAI submission gate.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=Path("experiments/reports/bitdpm_aaai_submission_gate.md"))
    parser.add_argument("--json-out", type=Path, default=Path("experiments/reports/bitdpm_aaai_submission_gate.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    gates = [
        check_v31(root),
        check_benchmark_overlap(root),
        check_v1k(root),
        check_router(root),
        check_external_baselines(root),
        check_ablation(root),
        check_statistics(root),
        check_paper_package(root),
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(make_report(gates), encoding="utf-8")
    args.json_out.write_text(json.dumps([gate.__dict__ for gate in gates], indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.json_out}")


if __name__ == "__main__":
    main()
