"""Build an AAAI-readiness report from current BitDPM evidence.

The report is intentionally conservative: it separates paper-usable evidence
from frozen or unrecovered claims, then lists concrete experiments required for
a high-level AAAI submission.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def best_oracle_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            float(row.get("oracle_gain", 0.0)),
            int(row.get("coverage", 0)),
            int(row.get("n") or 0),
        ),
        reverse=True,
    )


def zero_break_router_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row for row in rows
        if int(row.get("breaks", 10**9)) == 0 and float(row.get("gain", 0.0)) > 0
    ]


def router_evidence_rank(row: dict[str, Any]) -> tuple[int, float, int]:
    notes = str(row.get("notes", ""))
    if "held-out cross-validation" in notes:
        tier = 2
    elif "hand-authored" in notes:
        tier = 1
    else:
        tier = 0
    return (tier, float(row.get("gain", 0.0)), int(row.get("fixes", 0)))


def markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return lines


def build_report(
    paper_tables_path: Path,
    provenance_audit_path: Path,
    crash_analysis_path: Path,
) -> str:
    data = load_json(paper_tables_path)
    block_rows = data.get("block_pool_results", [])
    router_rows = data.get("router_results", [])
    provenance_text = load_text(provenance_audit_path)
    crash_text = load_text(crash_analysis_path)

    oracle_top = best_oracle_rows(block_rows)[:6]
    zero_break_top = sorted(zero_break_router_rows(router_rows), key=router_evidence_rank, reverse=True)[:8]
    v31_unrecovered = "Status: **UNRECOVERED**" in provenance_text
    crash_doc_has_six = all(
        token in crash_text
        for token in ["维度不匹配", "设备不匹配", "FP16 NaN", "Rank32", "Gating 无声失效", "MPS"]
    )

    lines: list[str] = [
        "# BitDPM AAAI Readiness Report",
        "",
        "## Bottom Line",
        "",
    ]
    lines.extend(
        [
            "BitDPM is not yet at a high-confidence AAAI main-result state. The current",
            "evidence is strong enough for a mechanism-oriented technical report and a",
            "paper draft, but a competitive AAAI submission still needs reproducible",
            "main results on larger benchmarks, stronger external baselines, and a",
            "non-oracle deployable router with stable held-out gains.",
            "",
            "The v31 `allow_math@0.85 -> fixes=6, breaks=0` record is explicitly frozen:",
            "it remains historical evidence until exact block/backbone provenance is",
            "recovered or a compatible block is retrained and replayed.",
            "",
        ]
    )

    lines.extend(
        [
            "## Current Paper-Usable Evidence",
            "",
            "### Sparse Correction Oracle",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Setting", "Benchmark", "N", "Baseline", "Oracle", "Gain", "Coverage", "Always-All"],
            [
                [
                    row.get("label"),
                    row.get("benchmark"),
                    row.get("n"),
                    fmt(row.get("baseline")),
                    fmt(row.get("oracle")),
                    fmt(row.get("oracle_gain")),
                    f"{row.get('coverage')}/{row.get('n')}",
                    fmt(row.get("always_all")),
                ]
                for row in oracle_top
            ],
        )
    )

    lines.extend(
        [
            "",
            "Interpretation: sparse correction opportunities are real, measurable, and",
            "persist beyond core-45. The strongest broad-scale evidence is v14 full",
            "300-sample validation: oracle `0.903` over baseline `0.840`, coverage",
            "`19/300`, and Always-All `0.000`.",
            "",
            "### Deployable Router Evidence",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Setting", "Router", "Baseline", "Gain", "Fixes", "Breaks", "Evidence Type"],
            [
                [
                    row.get("label"),
                    fmt(row.get("router")),
                    fmt(row.get("baseline")),
                    fmt(row.get("gain")),
                    row.get("fixes"),
                    row.get("breaks"),
                    row.get("notes"),
                ]
                for row in zero_break_top
            ],
        )
    )
    lines.extend(
        [
            "",
            "Interpretation: zero-break routing exists, but the gains are still modest",
            "under strict held-out validation. The table prioritizes held-out CV over",
            "full-report prototypes. The safest current deployable claim is conservative",
            "allow-core-no-log routing, not broad learned routing.",
            "",
            "## Claims That Are Safe Today",
            "",
            "1. BitDPM parameter blocks can create sparse per-sample correction opportunities.",
            "2. All-block activation is a negative control and often collapses for high-scale pools.",
            "3. Unique-utility block admission is better supported than semantic-label admission.",
            "4. Conservative safety routing can preserve zero-break gains on v14/v15 validation.",
            "5. Engineering reproducibility now requires block/backbone dimension auditing.",
            "",
            "## Claims That Must Not Be Made Yet",
            "",
            "1. Do not claim v31 is a confirmed 1.5B result.",
            "2. Do not claim the v31 `0.956` score as current reproducible main evidence.",
            "3. Do not claim broad deployable router generalization.",
            "4. Do not claim BitDPM improves most samples; current utility is sparse.",
            "5. Do not claim Always-All or adapter merging is the intended deployment mode.",
            "",
            "## AAAI-Level Gaps",
            "",
        ]
    )
    gap_rows = [
        [
            "Main result provenance",
            "v31 is unrecovered" if v31_unrecovered else "v31 recovered",
            "Recover exact block or retrain compatible 1.5B block with full metadata",
        ],
        [
            "Scale",
            "300-sample v14; 120-sample targeted v15; v1k_clean code exists for overlap-audited validation",
            "Run v1k_clean and report confidence intervals",
        ],
        [
            "External baselines",
            "Random/fixed/oracle covered; prompt-only and LoRA runnable",
            "Run prompt-only and LoRA outputs; add task-adapter comparison if needed",
        ],
        [
            "Router generalization",
            "Zero-break but modest strict-CV gains",
            "Train/evaluate a preregistered router on train/dev/test splits",
        ],
        [
            "Ablations",
            "Consolidated rank/scale/admission/router table exists",
            "Refresh ablation table after v1k and external-baseline runs",
        ],
        [
            "Reproducibility",
            "Crash doc covers six failure modes" if crash_doc_has_six else "Crash doc incomplete",
            "Use `scripts/build_paper_package.py` as the one-command paper-evidence rebuild entry",
        ],
    ]
    lines.extend(markdown_table(["Dimension", "Current State", "AAAI Requirement"], gap_rows))

    lines.extend(
        [
            "",
            "## Required Main Experiment Plan",
            "",
            "### Stage A: Reproducible Main Path",
            "",
            "- Freeze model, block registry, benchmark split, decoding, evaluator, and random seed.",
            "- If pursuing 1.5B, train fresh 1.5B-compatible down-proj blocks; do not reuse 0.5B blocks.",
            "- Run `audit_v31_provenance.py` and block manifest generation before any migration claim.",
            "",
            "### Stage B: Paper-Scale Validation",
            "",
            "- v14 full 300: rerun current best pool and safest router from a clean manifest.",
            "- Use `v1k_clean`, a 1k mixed benchmark with balanced arithmetic, factual, commonsense, Chinese, code, and reasoning slices.",
            "- Treat the benchmark as held-out only after `bitdpm_benchmark_manifest` shows zero exact prompt overlap with prior validation sets.",
            "- Report baseline, best fixed, oracle, deployable router, Always-All, fixes, breaks, net, active ratio.",
            "",
            "### Stage C: Baselines and Ablations",
            "",
            "- Baselines: frozen backbone, standard LoRA adapter, always-on best adapter, random router, full-report oracle, prompt-only rules.",
            "- Ablations: rank, scale, layer/module placement, unique-utility admission, router features, and device/dtype safety.",
            "- Statistical reporting: bootstrap confidence intervals over prompts and per-category breakdowns.",
            "",
            "## AAAI Submission Gate",
            "",
            "A high-level AAAI claim should wait until all of the following are true:",
            "",
            "- A reproducible, provenance-complete main result exists.",
            "- Deployable router improves held-out accuracy with zero or very low breaks on at least two benchmarks.",
            "- Oracle coverage remains meaningful on 1k+ prompts.",
            "- External baselines are included and BitDPM wins on correction safety or parameter efficiency.",
            "- All paper tables are generated from scripts, not hand-edited summaries.",
            "",
            "## Recommended Current Positioning",
            "",
            "Current best positioning is a rigorous mechanism paper draft:",
            "",
            "> BitDPM is a runtime-selective sparse parameter correction framework. It",
            "> shows that useful correction directions exist, that indiscriminate block",
            "> composition is unsafe, and that block admission and routing must be",
            "> governed by unique per-sample utility and break control. The method is",
            "> promising but still needs provenance-complete large-scale validation for",
            "> a strong AAAI main-result claim.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build BitDPM AAAI readiness report.")
    parser.add_argument("--paper-tables", type=Path, default=Path("experiments/reports/paper_tables/bitdpm_current_results.json"))
    parser.add_argument("--provenance-audit", type=Path, default=Path("experiments/reports/bitdpm_v31_provenance_audit.md"))
    parser.add_argument("--crash-analysis", type=Path, default=Path("experiments/reports/bitdpm_crash_analysis.md"))
    parser.add_argument("--out", type=Path, default=Path("experiments/reports/bitdpm_aaai_readiness_report.md"))
    args = parser.parse_args()

    report = build_report(args.paper_tables, args.provenance_audit, args.crash_analysis)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
