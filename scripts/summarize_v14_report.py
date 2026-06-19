#!/usr/bin/env python3
"""Summarize BitDPM v14 benchmark reports for paper-facing analysis."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any


def best_config(sample: dict[str, Any], configs: list[str]) -> str:
    return max(
        configs,
        key=lambda cfg: (
            sample["scores"].get(cfg, 0.0),
            -sample["active_counts"].get(cfg, 0),
            -configs.index(cfg),
        ),
    )


def correct(score: float, threshold: float) -> bool:
    return score >= threshold


def run(args):
    with open(args.report) as f:
        data = json.load(f)

    configs = list(data["config_results"])
    baseline = data["config_results"]["baseline"]["overall"]
    always_all = data["config_results"].get("always_all", {}).get("overall")
    oracle = data["oracle"]["overall"]
    selection_frequency = data.get("selection_frequency", {})

    non_baseline_samples = []
    by_category: dict[str, int] = {}
    for idx, sample in enumerate(data["per_sample"]):
        chosen = best_config(sample, configs)
        if chosen != "baseline" and correct(sample["scores"].get(chosen, 0.0), args.correct_threshold):
            record = {
                "index": idx,
                "category": sample["category"],
                "prompt": sample["prompt"],
                "chosen": chosen,
                "score": sample["scores"].get(chosen, 0.0),
                "baseline_score": sample["scores"].get("baseline", 0.0),
            }
            non_baseline_samples.append(record)
            by_category[sample["category"]] = by_category.get(sample["category"], 0) + 1

    fixed_rows = []
    for cfg, agg in data["config_results"].items():
        if cfg in ("baseline", "always_all"):
            continue
        fixed_rows.append({
            "config": cfg,
            "overall": agg["overall"],
            "delta": agg["overall"] - baseline,
            "active": agg["active_blocks"],
        })
    fixed_rows.sort(key=lambda row: row["overall"], reverse=True)

    result = {
        "report": args.report,
        "benchmark_set": data.get("benchmark_set"),
        "total_prompts": data.get("total_prompts"),
        "baseline": baseline,
        "oracle": oracle,
        "oracle_gain": oracle - baseline,
        "coverage": len(non_baseline_samples),
        "coverage_rate": len(non_baseline_samples) / max(data.get("total_prompts", 0), 1),
        "always_all": always_all,
        "selection_frequency": selection_frequency,
        "coverage_by_category": by_category,
        "fixed_rows": fixed_rows,
        "non_baseline_samples": non_baseline_samples,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    tag = args.tag or os.path.splitext(os.path.basename(args.report))[0]
    json_path = os.path.join(args.output_dir, f"{tag}_summary.json")
    md_path = os.path.join(args.output_dir, f"{tag}_summary.md")

    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    lines = [
        "# BitDPM v14 Report Summary",
        "",
        f"- Report: `{args.report}`",
        f"- Benchmark: `{result['benchmark_set']}`",
        f"- Total prompts: {result['total_prompts']}",
        f"- Baseline: {baseline:.3f}",
        f"- Oracle: {oracle:.3f}",
        f"- Oracle gain: {oracle - baseline:+.3f}",
        f"- Non-baseline oracle coverage: {len(non_baseline_samples)}/{result['total_prompts']} ({result['coverage_rate']:.3f})",
        f"- Always-All: {always_all:.3f}" if always_all is not None else "- Always-All: n/a",
        f"- Selection frequency: `{selection_frequency}`",
        f"- Coverage by category: `{by_category}`",
        "",
        "## Fixed Blocks",
        "",
        "| Config | Overall | Delta | Active |",
        "|---|---:|---:|---:|",
    ]
    for row in fixed_rows:
        lines.append(f"| {row['config']} | {row['overall']:.3f} | {row['delta']:+.3f} | {row['active']:.2f} |")

    lines.extend(["", "## Non-Baseline Oracle Samples", ""])
    for sample in non_baseline_samples:
        lines.append(
            f"- #{sample['index']} `{sample['category']}` `{sample['chosen']}` "
            f"baseline={sample['baseline_score']} score={sample['score']}: {sample['prompt']}"
        )

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Saved JSON: {json_path}")
    print(f"Saved Markdown: {md_path}")
    print(
        f"baseline={baseline:.3f} oracle={oracle:.3f} "
        f"coverage={len(non_baseline_samples)}/{result['total_prompts']} always_all={always_all}"
    )


def main():
    parser = argparse.ArgumentParser(description="Summarize BitDPM v14 report")
    parser.add_argument("--report", required=True)
    parser.add_argument("--output-dir", default="experiments/reports/v14_summary")
    parser.add_argument("--tag", default="")
    parser.add_argument("--correct-threshold", type=float, default=1.0)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
