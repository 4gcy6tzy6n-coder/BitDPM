#!/usr/bin/env python3
"""Rebuild the current BitDPM paper-evidence package.

This script is intentionally report-only: it does not run model inference.
It refreshes manifests, consolidated result tables, provenance audits,
bootstrap confidence intervals, the AAAI-readiness report, and a compact
artifact index from saved experiment outputs.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "experiments" / "reports"


@dataclass(frozen=True)
class Artifact:
    path: Path
    status: str
    role: str


def run_step(label: str, command: list[str]) -> None:
    print(f"\n== {label} ==")
    print(" ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def exists_mark(path: Path) -> str:
    return "present" if path.exists() else "missing"


def build_artifact_index(out: Path) -> None:
    artifacts = [
        Artifact(
            REPORTS / "paper_tables" / "bitdpm_current_results.md",
            "paper-facing",
            "Consolidated block-pool and router tables generated from saved JSON reports.",
        ),
        Artifact(
            REPORTS / "paper_tables" / "bitdpm_current_results.json",
            "paper-facing",
            "Machine-readable source for current paper tables.",
        ),
        Artifact(
            REPORTS / "paper_tables" / "bitdpm_aaai_main_results.md",
            "paper-facing",
            "AAAI main-result matrix for v14/v15/v1k current-pool, router, prompt-only, and LoRA results.",
        ),
        Artifact(
            REPORTS / "paper_tables" / "bitdpm_aaai_main_results.json",
            "paper-facing",
            "Machine-readable source for the AAAI main-result matrix.",
        ),
        Artifact(
            REPORTS / "bitdpm_v31_provenance_audit.md",
            "frozen audit",
            "Explains why the historical v31 strong result is unrecovered and cannot be used as a current main result.",
        ),
        Artifact(
            REPORTS / "block_manifest.md",
            "provenance",
            "Inventory of saved parameter blocks, shapes, hashes, and inferred backbone compatibility.",
        ),
        Artifact(
            REPORTS / "bitdpm_benchmark_manifest.md",
            "benchmark audit",
            "Static audit of core/v08/v14/v15/v1k prompt counts, answer coverage, overlap, and fingerprints.",
        ),
        Artifact(
            REPORTS / "bitdpm_aaai_readiness_report.md",
            "readiness gate",
            "Conservative assessment of what is paper-usable and what still blocks a high-confidence AAAI claim.",
        ),
        Artifact(
            REPORTS / "bitdpm_aaai_submission_gate.md",
            "submission gate",
            "Machine-checkable AAAI readiness gate over current artifacts.",
        ),
        Artifact(
            REPORTS / "bitdpm_aaai_experiment_status.md",
            "experiment status",
            "Execution dashboard for v14/v15/v1k current-pool, router, prompt-only, and LoRA artifacts.",
        ),
        Artifact(
            REPORTS / "bitdpm_aaai_main_experiment_plan.md",
            "next experiment plan",
            "Main-result validation plan after v31 provenance failure.",
        ),
        Artifact(
            REPORTS / "bitdpm_crash_analysis.md",
            "engineering evidence",
            "Crash/failure-mode analysis and implementation handoff notes.",
        ),
        Artifact(
            REPORTS / "bitdpm_reproducibility_checklist.md",
            "reproducibility",
            "Checklist for rerunning and validating current evidence.",
        ),
        Artifact(
            ROOT / "paper" / "bitdpm_aaai_draft.md",
            "paper draft",
            "Mechanism-oriented AAAI-style manuscript draft using only current paper-safe evidence.",
        ),
        Artifact(
            ROOT / "paper" / "claim_to_evidence.md",
            "claim audit",
            "Maps allowed, caveated, and unsafe claims to generated evidence.",
        ),
        Artifact(
            ROOT / "paper" / "aaai_main_experiment_protocol.md",
            "main experiment protocol",
            "Defines the v14/v15/v1k validation path and external-baseline table required for AAAI-level claims.",
        ),
        Artifact(
            REPORTS / "aaai_main_experiment_commands.sh",
            "main experiment commands",
            "Generated shell script for current-pool v14/v15/v1k validation.",
        ),
        Artifact(
            REPORTS / "bitdpm_aaai_baseline_gap_table.md",
            "baseline gap table",
            "Computable frozen/backbone/fixed/oracle/random baselines and pending external baselines.",
        ),
        Artifact(
            REPORTS / "bitdpm_aaai_ablation_table.md",
            "ablation table",
            "Consolidated rank/scale/admission/transfer/router ablation evidence.",
        ),
        Artifact(
            REPORTS / "external_baseline_commands.sh",
            "external baseline commands",
            "Generated prompt-only baseline commands.",
        ),
        Artifact(
            REPORTS / "lora_baseline_commands.sh",
            "LoRA baseline commands",
            "Generated standard LoRA baseline commands; requires optional PEFT dependency.",
        ),
        Artifact(
            REPORTS / "bitdpm_v14_full_bootstrap_ci.md",
            "statistics",
            "Bootstrap confidence intervals for v14 full 300-sample block-pool results.",
        ),
        Artifact(
            REPORTS / "bitdpm_v14_allow_core_nolog_cv_bootstrap_ci.md",
            "statistics",
            "Bootstrap confidence intervals for v14 allow-core-no-log strict-CV router results.",
        ),
    ]

    lines = [
        "# BitDPM Paper Artifact Index",
        "",
        "This index is generated by `scripts/build_paper_package.py`. It separates",
        "paper-facing evidence from frozen historical claims and next-step plans.",
        "",
        "## Current Position",
        "",
        "BitDPM is currently supported as a mechanism-oriented sparse correction",
        "framework. The historical v31 strong result remains unrecovered and should",
        "not be cited as the current main result. The paper path should use v14/v15",
        "evidence until a provenance-complete main result is retrained or recovered.",
        "",
        "## Artifacts",
        "",
        "| Artifact | Exists | Status | Role |",
        "|---|---|---|---|",
    ]
    for item in artifacts:
        rel = item.path.relative_to(ROOT)
        lines.append(f"| `{rel}` | {exists_mark(item.path)} | {item.status} | {item.role} |")

    lines.extend(
        [
            "",
            "## Citation Discipline",
            "",
            "- Use v14/v15 results as current broad evidence.",
            "- Treat v31 `0.956 / fixes=6 / breaks=0` as frozen historical evidence only.",
            "- Do not claim a confirmed Qwen2.5-1.5B main result until block/backbone provenance is complete.",
            "- Report confidence intervals and fixes/breaks/net for any deployable router claim.",
            "- Keep Always-All as a negative control, not as a deployment mode.",
            "",
            "## Rebuild Command",
            "",
            "```bash",
            "python scripts/build_paper_package.py",
            "```",
            "",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild BitDPM paper-evidence package.")
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=2000,
        help="Bootstrap resamples for confidence interval reports.",
    )
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument(
        "--skip-manifest",
        action="store_true",
        help="Skip block manifest rebuild when torch loading is not available.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    py = sys.executable

    if not args.skip_manifest:
        run_step("Block manifest", [py, "scripts/build_block_manifest.py"])

    run_step("Benchmark manifest", [py, "scripts/build_benchmark_manifest.py"])
    run_step("Paper result tables", [py, "scripts/build_paper_result_tables.py"])
    run_step("AAAI main result table", [py, "scripts/build_aaai_main_result_table.py"])
    run_step("AAAI main experiment commands", [py, "scripts/make_aaai_main_experiment_commands.py"])
    run_step("External baseline commands", [py, "scripts/make_external_baseline_commands.py"])
    run_step("LoRA baseline commands", [py, "scripts/make_lora_baseline_commands.py"])
    run_step("AAAI baseline gap table", [py, "scripts/build_aaai_baseline_gap_table.py"])
    run_step("AAAI ablation table", [py, "scripts/build_aaai_ablation_table.py"])
    run_step("v31 provenance audit", [py, "scripts/audit_v31_provenance.py"])
    run_step(
        "v14 full bootstrap CI",
        [
            py,
            "scripts/bootstrap_result_ci.py",
            "experiments/reports/v14_full_v11_admitted_20260608_093845.json",
            "--samples",
            str(args.bootstrap_samples),
            "--seed",
            str(args.seed),
            "--out",
            "experiments/reports/bitdpm_v14_full_bootstrap_ci.md",
        ],
    )
    run_step(
        "v14 allow-core-no-log strict-CV bootstrap CI",
        [
            py,
            "scripts/bootstrap_result_ci.py",
            "experiments/reports/v12_router/v14_full_v11_utility_router_allow_core_nolog_cv_crossval.json",
            "--samples",
            str(args.bootstrap_samples),
            "--seed",
            str(args.seed),
            "--out",
            "experiments/reports/bitdpm_v14_allow_core_nolog_cv_bootstrap_ci.md",
        ],
    )
    run_step("AAAI readiness report", [py, "scripts/build_aaai_readiness_report.py"])
    run_step("AAAI submission gate", [py, "scripts/check_aaai_submission_gate.py"])
    run_step("AAAI experiment status", [py, "scripts/summarize_aaai_experiment_status.py"])
    build_artifact_index(REPORTS / "bitdpm_paper_artifact_index.md")


if __name__ == "__main__":
    main()
