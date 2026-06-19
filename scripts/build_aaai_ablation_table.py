#!/usr/bin/env python3
"""Build consolidated BitDPM ablation tables from current paper results.

This is report-only. It reads `paper_tables/bitdpm_current_results.json` and
extracts the scattered rank/scale/admission/router/transfer evidence into a
single paper-facing ablation report.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def row_by_label(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("label")): row for row in rows}


def md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return lines


def block_row(label: str, row: dict[str, Any], factor: str) -> list[Any]:
    return [
        factor,
        label,
        row.get("benchmark"),
        row.get("n"),
        fmt(row.get("baseline")),
        fmt(row.get("best_fixed")),
        row.get("best_fixed_config"),
        fmt(row.get("oracle")),
        fmt(row.get("oracle_gain")),
        f"{row.get('coverage')}/{row.get('n')}",
        fmt(row.get("always_all")),
    ]


def router_row(row: dict[str, Any], factor: str) -> list[Any]:
    return [
        factor,
        row.get("label"),
        row.get("kind"),
        fmt(row.get("router")),
        fmt(row.get("baseline")),
        fmt(row.get("gain")),
        row.get("fixes"),
        row.get("breaks"),
        row.get("notes"),
    ]


def build_report(data: dict[str, Any]) -> str:
    block_rows = data.get("block_pool_results", [])
    router_rows = data.get("router_results", [])
    blocks = row_by_label(block_rows)

    lines = [
        "# BitDPM AAAI Ablation Tables",
        "",
        "This report consolidates existing ablation evidence from generated paper",
        "tables. It does not run model inference.",
        "",
        "## Block Capacity and Scale Ablations",
        "",
    ]

    capacity_labels = [
        ("rank/scale", "v08 rank8 det"),
        ("rank/scale", "v08 rank16 det"),
        ("rank/scale", "v08 rank8 stable"),
        ("rank/scale", "v08 rank16 stable"),
        ("hybrid scale", "v08 hybrid det"),
        ("hybrid scale", "v08 hybrid stable"),
    ]
    lines.extend(
        md_table(
            ["Factor", "Setting", "Benchmark", "N", "Baseline", "Best Fixed", "Best Config", "Oracle", "Gain", "Coverage", "Always-All"],
            [block_row(label, blocks[label], factor) for factor, label in capacity_labels if label in blocks],
        )
    )

    lines.extend(
        [
            "",
            "Takeaway: rank16 strengthens fixed-block utility in deterministic v08",
            "(`0.830` best fixed versus `0.800` for rank8), while hybrid scale",
            "improves stable-sampling oracle to `0.880` and exposes strong",
            "Always-All interference.",
            "",
            "## Admission and Repair-Block Ablations",
            "",
        ]
    )
    admission_labels = [
        ("repair-only pool", "v09 repair stable"),
        ("unique repair direction", "v09b + power_log"),
        ("overlap repair direction", "v09b + factual"),
        ("combined repair directions", "v09b + both"),
        ("admitted pool", "v10 admitted"),
        ("merged candidates", "v11 merged candidates"),
    ]
    lines.extend(
        md_table(
            ["Factor", "Setting", "Benchmark", "N", "Baseline", "Best Fixed", "Best Config", "Oracle", "Gain", "Coverage", "Always-All"],
            [block_row(label, blocks[label], factor) for factor, label in admission_labels if label in blocks],
        )
    )
    lines.extend(
        [
            "",
            "Takeaway: admitting the unique `arithmetic_power_log` direction improves",
            "v08 oracle from `0.880` to `0.890`; v11 candidates further increase",
            "oracle to `0.900`, but best fixed remains baseline, reinforcing sparse",
            "rather than always-on utility.",
            "",
            "## Benchmark Transfer Ablations",
            "",
        ]
    )
    transfer_labels = [
        ("v08 continuity", "v11 merged candidates"),
        ("v14 pilot", "v14 pilot v11 admitted"),
        ("v14 full", "v14 full v11 admitted"),
        ("v15 targeted", "v15 router validation v11 admitted"),
    ]
    lines.extend(
        md_table(
            ["Factor", "Setting", "Benchmark", "N", "Baseline", "Best Fixed", "Best Config", "Oracle", "Gain", "Coverage", "Always-All"],
            [block_row(label, blocks[label], factor) for factor, label in transfer_labels if label in blocks],
        )
    )
    lines.extend(
        [
            "",
            "Takeaway: sparse oracle utility persists beyond v08. The broad v14 full",
            "benchmark gives oracle `0.903` over baseline `0.840` with `19/300`",
            "coverage, while v15 targeted validation shows larger correction surface",
            "but is not a broad capability benchmark.",
            "",
            "## Router Safety Ablations",
            "",
        ]
    )
    interesting_router = [
        ("strict CV", "v14 full v11 utility strict CV"),
        ("allow-core strict CV", "v14 full v11 allow-core utility strict CV"),
        ("allow-core-no-log strict CV", "v14 full v11 allow-core-no-log utility strict CV"),
        ("v15 allow-core strict CV", "v15 allow-core utility strict CV"),
        ("v15 allow-core-no-log strict CV", "v15 allow-core-no-log utility strict CV"),
        ("v15 conjunction strict CV", "v15 conjunction utility strict CV"),
        ("full-report prototype", "v14 full v11 utility full-report"),
        ("full-report prototype", "v15 conjunction utility full-report"),
    ]
    router_by_label = row_by_label(router_rows)
    lines.extend(
        md_table(
            ["Factor", "Setting", "Kind", "Router", "Baseline", "Gain", "Fixes", "Breaks", "Evidence"],
            [router_row(router_by_label[label], factor) for factor, label in interesting_router if label in router_by_label],
        )
    )
    lines.extend(
        [
            "",
            "Takeaway: full-report routers recover more fixes, but strict held-out CV",
            "reveals break risk. Conservative allow-core-no-log routing is currently",
            "the safest deployable claim: v14 strict CV `0.857` over `0.840` with",
            "`5` fixes and `0` breaks; v15 strict CV `0.500` over `0.442` with",
            "`7` fixes and `0` breaks.",
            "",
            "## Paper Claim Boundary",
            "",
            "- These ablations support mechanism claims about sparse utility, admission,",
            "  scale, and interference.",
            "- They do not by themselves prove a high-confidence AAAI main result.",
            "- The missing next evidence remains v1k held-out validation plus completed",
            "  prompt-only and LoRA external baselines.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build consolidated BitDPM ablation tables.")
    parser.add_argument("--paper-tables", type=Path, default=Path("experiments/reports/paper_tables/bitdpm_current_results.json"))
    parser.add_argument("--out", type=Path, default=Path("experiments/reports/bitdpm_aaai_ablation_table.md"))
    parser.add_argument("--json-out", type=Path, default=Path("experiments/reports/bitdpm_aaai_ablation_table.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = load_json(args.paper_tables)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build_report(data), encoding="utf-8")
    args.json_out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.json_out}")


if __name__ == "__main__":
    main()
