#!/usr/bin/env python3
"""Analyze fixed-block safety from BitDPM evaluation reports.

For each non-baseline config, this script reports:

- fixed score
- fixes: baseline wrong, block correct
- breaks: baseline correct, block wrong
- net gain: sum(block_score - baseline_score)
- unique fixes: samples only this block fixes
- damaged categories
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict
from typing import Any


def correct(score: float, threshold: float) -> bool:
    return score >= threshold


def analyze(data: dict[str, Any], threshold: float) -> dict[str, Any]:
    configs = [c for c in data["config_results"] if c not in ("baseline", "always_all")]
    rows = []
    samples = data["per_sample"]

    correct_by_sample: list[set[str]] = []
    for sample in samples:
        correct_by_sample.append({
            cfg for cfg in configs
            if correct(sample["scores"].get(cfg, 0.0), threshold)
        })

    for cfg in configs:
        fixes = []
        breaks = []
        unique_fixes = []
        damaged_categories: dict[str, int] = defaultdict(int)
        fixed_total = 0.0
        baseline_total = 0.0

        for idx, sample in enumerate(samples):
            scores = sample["scores"]
            baseline_score = scores.get("baseline", 0.0)
            block_score = scores.get(cfg, 0.0)
            fixed_total += block_score
            baseline_total += baseline_score

            baseline_ok = correct(baseline_score, threshold)
            block_ok = correct(block_score, threshold)

            if not baseline_ok and block_ok:
                record = {
                    "index": idx,
                    "category": sample["category"],
                    "prompt": sample["prompt"],
                    "baseline_score": baseline_score,
                    "block_score": block_score,
                }
                fixes.append(record)
                if correct_by_sample[idx] == {cfg}:
                    unique_fixes.append(record)
            elif baseline_ok and not block_ok:
                breaks.append({
                    "index": idx,
                    "category": sample["category"],
                    "prompt": sample["prompt"],
                    "baseline_score": baseline_score,
                    "block_score": block_score,
                })
                damaged_categories[sample["category"]] += 1

        n = max(len(samples), 1)
        rows.append({
            "block": cfg,
            "fixed_score": fixed_total / n,
            "baseline_score": baseline_total / n,
            "score_delta": (fixed_total - baseline_total) / n,
            "fixes": len(fixes),
            "breaks": len(breaks),
            "net_fix_count": len(fixes) - len(breaks),
            "unique_fixes": len(unique_fixes),
            "damaged_categories": dict(sorted(damaged_categories.items())),
            "fix_samples": fixes,
            "break_samples": breaks,
            "unique_fix_samples": unique_fixes,
        })

    rows.sort(key=lambda r: (r["score_delta"], r["net_fix_count"], r["unique_fixes"]), reverse=True)
    return {
        "report": {
            "model": data.get("model"),
            "benchmark_set": data.get("benchmark_set", "unknown"),
            "total_prompts": data.get("total_prompts", len(samples)),
            "block_scale": data.get("block_scale"),
            "block_scales": data.get("block_scales", {}),
        },
        "rows": rows,
    }


def write_markdown(result: dict[str, Any], path: str):
    report = result["report"]
    lines = [
        "# BitDPM Block Safety Analysis",
        "",
        f"- Benchmark: `{report['benchmark_set']}`",
        f"- Total prompts: `{report['total_prompts']}`",
        f"- Global block scale: `{report['block_scale']}`",
        f"- Block-specific scales: `{report.get('block_scales', {})}`",
        "",
        "| Block | Fixed | Delta | Fixes | Breaks | Net | Unique Fixes | Damaged Categories |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row['block']} | {row['fixed_score']:.3f} | {row['score_delta']:+.3f} | "
            f"{row['fixes']} | {row['breaks']} | {row['net_fix_count']} | "
            f"{row['unique_fixes']} | `{row['damaged_categories']}` |"
        )

    lines.extend(["", "## Unique Fix Samples", ""])
    for row in result["rows"]:
        if not row["unique_fix_samples"]:
            continue
        lines.append(f"### {row['block']}")
        for sample in row["unique_fix_samples"]:
            lines.append(f"- #{sample['index']} `{sample['category']}`: {sample['prompt']}")
        lines.append("")

    lines.extend(["", "## Break Samples", ""])
    for row in result["rows"]:
        if not row["break_samples"]:
            continue
        lines.append(f"### {row['block']}")
        for sample in row["break_samples"][:20]:
            lines.append(f"- #{sample['index']} `{sample['category']}`: {sample['prompt']}")
        if len(row["break_samples"]) > 20:
            lines.append(f"- ... {len(row['break_samples']) - 20} more")
        lines.append("")

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_csv(result: dict[str, Any], path: str):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "block",
                "fixed_score",
                "baseline_score",
                "score_delta",
                "fixes",
                "breaks",
                "net_fix_count",
                "unique_fixes",
                "damaged_categories",
            ],
        )
        writer.writeheader()
        for row in result["rows"]:
            writer.writerow({
                key: row[key]
                for key in writer.fieldnames
            })


def run(args):
    with open(args.report) as f:
        data = json.load(f)
    result = analyze(data, args.correct_threshold)

    os.makedirs(args.output_dir, exist_ok=True)
    base = args.tag or os.path.splitext(os.path.basename(args.report))[0]
    json_path = os.path.join(args.output_dir, f"{base}_block_safety.json")
    md_path = os.path.join(args.output_dir, f"{base}_block_safety.md")
    csv_path = os.path.join(args.output_dir, f"{base}_block_safety.csv")

    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    write_markdown(result, md_path)
    write_csv(result, csv_path)

    print(f"Saved JSON: {json_path}")
    print(f"Saved Markdown: {md_path}")
    print(f"Saved CSV: {csv_path}")
    print("| block | fixed | delta | fixes | breaks | net | unique |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for row in result["rows"]:
        print(
            f"| {row['block']} | {row['fixed_score']:.3f} | {row['score_delta']:+.3f} | "
            f"{row['fixes']} | {row['breaks']} | {row['net_fix_count']} | {row['unique_fixes']} |"
        )


def main():
    parser = argparse.ArgumentParser(description="Analyze BitDPM block safety from an eval report")
    parser.add_argument("--report", required=True)
    parser.add_argument("--output-dir", default="experiments/reports/v08_block_safety")
    parser.add_argument("--tag", default="")
    parser.add_argument("--correct-threshold", type=float, default=1.0)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
