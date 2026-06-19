#!/usr/bin/env python3
"""Analyze unique-utility admission for BitDPM block pools.

The script compares a base pool against one or more candidate-pool reports.
It is designed for v0.10 admission decisions:

- fixes: baseline wrong, candidate block correct
- unique fixes: base pool oracle wrong, candidate block correct
- overlap fixes: base pool oracle already correct, candidate block correct
- breaks: baseline correct, candidate block wrong
- net unique utility: unique fixes - breaks
- admit recommendation

It also lists samples that remain uncorrected by the current best pool, so the
next targeted repair data can be constructed from concrete failure types.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Any


SPECIAL_CONFIGS = {"baseline", "always_all"}


@dataclass
class Report:
    label: str
    path: str
    data: dict[str, Any]
    configs: list[str]


def load_report(label_path: str) -> Report:
    if "=" in label_path:
        label, path = label_path.split("=", 1)
    else:
        path = label_path
        label = os.path.splitext(os.path.basename(path))[0]
    with open(path) as f:
        data = json.load(f)
    return Report(
        label=label,
        path=path,
        data=data,
        configs=list(data["config_results"]),
    )


def is_correct(score: float, threshold: float) -> bool:
    return score >= threshold


def best_config(sample: dict[str, Any], configs: list[str]) -> str:
    return max(
        configs,
        key=lambda cfg: (
            sample["scores"].get(cfg, 0.0),
            -sample["active_counts"].get(cfg, 0),
            -configs.index(cfg),
        ),
    )


def sample_key(sample: dict[str, Any]) -> tuple[str, str]:
    return sample["category"], sample["prompt"]


def build_sample_map(report: Report) -> dict[tuple[str, str], dict[str, Any]]:
    return {sample_key(sample): sample for sample in report.data["per_sample"]}


def oracle_correct(sample: dict[str, Any], configs: list[str], threshold: float) -> bool:
    cfg = best_config(sample, configs)
    return is_correct(sample["scores"].get(cfg, 0.0), threshold)


def analyze_candidate(
    base: Report,
    candidate: Report,
    threshold: float,
    admit_min_unique: int,
    admit_max_breaks_per_unique: float,
    candidate_blocks: set[str] | None = None,
) -> list[dict[str, Any]]:
    base_samples = build_sample_map(base)
    rows: list[dict[str, Any]] = []
    candidate_configs = [cfg for cfg in candidate.configs if cfg not in SPECIAL_CONFIGS]
    if candidate_blocks is not None:
        candidate_configs = [cfg for cfg in candidate_configs if cfg in candidate_blocks]

    for cfg in candidate_configs:
        fixes = []
        unique_fixes = []
        overlap_fixes = []
        breaks = []

        for sample in candidate.data["per_sample"]:
            key = sample_key(sample)
            base_sample = base_samples.get(key)
            if base_sample is None:
                continue

            baseline_score = sample["scores"].get("baseline", 0.0)
            block_score = sample["scores"].get(cfg, 0.0)
            base_oracle_ok = oracle_correct(base_sample, base.configs, threshold)
            block_ok = is_correct(block_score, threshold)
            baseline_ok = is_correct(baseline_score, threshold)

            record = {
                "category": sample["category"],
                "prompt": sample["prompt"],
                "baseline_score": baseline_score,
                "block_score": block_score,
            }

            if not baseline_ok and block_ok:
                fixes.append(record)
                if base_oracle_ok:
                    overlap_fixes.append(record)
                else:
                    unique_fixes.append(record)
            elif baseline_ok and not block_ok:
                breaks.append(record)

        unique_count = len(unique_fixes)
        break_count = len(breaks)
        breaks_per_unique = break_count / max(unique_count, 1)
        admit = (
            unique_count >= admit_min_unique
            and breaks_per_unique <= admit_max_breaks_per_unique
        )

        rows.append({
            "candidate_pool": candidate.label,
            "block": cfg,
            "fixed_score": candidate.data["config_results"][cfg]["overall"],
            "fixes": len(fixes),
            "unique_fixes": unique_count,
            "overlap_fixes": len(overlap_fixes),
            "breaks": break_count,
            "net_unique_utility": unique_count - break_count,
            "breaks_per_unique": breaks_per_unique,
            "admit": admit,
            "unique_fix_samples": unique_fixes,
            "overlap_fix_samples": overlap_fixes,
            "break_samples": breaks,
        })

    rows.sort(
        key=lambda row: (
            row["admit"],
            row["unique_fixes"],
            row["net_unique_utility"],
            -row["breaks"],
        ),
        reverse=True,
    )
    return rows


def remaining_failures(base: Report, threshold: float) -> list[dict[str, Any]]:
    rows = []
    for idx, sample in enumerate(base.data["per_sample"]):
        cfg = best_config(sample, base.configs)
        score = sample["scores"].get(cfg, 0.0)
        if not is_correct(score, threshold):
            rows.append({
                "index": idx,
                "category": sample["category"],
                "prompt": sample["prompt"],
                "best_config": cfg,
                "best_score": score,
                "baseline_score": sample["scores"].get("baseline", 0.0),
            })
    return rows


def write_outputs(
    base: Report,
    candidates: list[Report],
    rows: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    output_dir: str,
    tag: str,
):
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, f"{tag}_admission.json")
    md_path = os.path.join(output_dir, f"{tag}_admission.md")

    payload = {
        "base": {"label": base.label, "path": base.path},
        "candidates": [{"label": c.label, "path": c.path} for c in candidates],
        "rows": rows,
        "remaining_failures": failures,
    }
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    lines = [
        "# BitDPM v0.10 Unique Utility Admission",
        "",
        f"- Base pool: `{base.label}`",
        f"- Base report: `{base.path}`",
        "",
        "## Admission Table",
        "",
        "| Candidate Pool | Block | Fixed | Fixes | Unique | Overlap | Breaks | Net Unique | Breaks/Unique | Admit |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['candidate_pool']} | {row['block']} | {row['fixed_score']:.3f} | "
            f"{row['fixes']} | {row['unique_fixes']} | {row['overlap_fixes']} | "
            f"{row['breaks']} | {row['net_unique_utility']} | "
            f"{row['breaks_per_unique']:.1f} | {'yes' if row['admit'] else 'no'} |"
        )

    lines.extend(["", "## Unique Fix Samples", ""])
    for row in rows:
        if not row["unique_fix_samples"]:
            continue
        lines.append(f"### {row['candidate_pool']} / {row['block']}")
        for sample in row["unique_fix_samples"]:
            lines.append(f"- `{sample['category']}`: {sample['prompt']}")
        lines.append("")

    lines.extend(["", "## Remaining Failures in Base Pool", ""])
    for failure in failures:
        lines.append(
            f"- #{failure['index']} `{failure['category']}` "
            f"best=`{failure['best_config']}` score={failure['best_score']}: {failure['prompt']}"
        )

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Saved JSON: {json_path}")
    print(f"Saved Markdown: {md_path}")
    print("| pool | block | fixes | unique | overlap | breaks | net | admit |")
    print("|---|---|---:|---:|---:|---:|---:|---|")
    for row in rows:
        print(
            f"| {row['candidate_pool']} | {row['block']} | {row['fixes']} | "
            f"{row['unique_fixes']} | {row['overlap_fixes']} | {row['breaks']} | "
            f"{row['net_unique_utility']} | {'yes' if row['admit'] else 'no'} |"
        )
    print(f"Remaining failures: {len(failures)}")


def run(args):
    base = load_report(args.base)
    candidates = [load_report(item) for item in args.candidates]
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        rows.extend(
            analyze_candidate(
                base=base,
                candidate=candidate,
                threshold=args.correct_threshold,
                admit_min_unique=args.admit_min_unique,
                admit_max_breaks_per_unique=args.admit_max_breaks_per_unique,
                candidate_blocks=set(args.candidate_blocks) if args.candidate_blocks else None,
            )
        )
    failures = remaining_failures(base, args.correct_threshold)
    write_outputs(base, candidates, rows, failures, args.output_dir, args.tag)


def main():
    parser = argparse.ArgumentParser(description="Analyze unique utility block admission")
    parser.add_argument("--base", required=True, help="Base report, optionally label=path")
    parser.add_argument("--candidates", nargs="+", required=True, help="Candidate reports, optionally label=path")
    parser.add_argument("--output-dir", default="experiments/reports/v10_admission")
    parser.add_argument("--tag", default="v10_unique_utility")
    parser.add_argument("--correct-threshold", type=float, default=1.0)
    parser.add_argument("--admit-min-unique", type=int, default=1)
    parser.add_argument("--admit-max-breaks-per-unique", type=float, default=15.0)
    parser.add_argument("--candidate-blocks", nargs="*", default=None,
                        help="Optional block/config names to analyze from candidate reports.")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
