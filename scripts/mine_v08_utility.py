#!/usr/bin/env python3
"""Mine per-sample block utility from BitDPM evaluation reports.

This script turns router-calibration JSON files into actionable utility mining
artifacts for v0.8:

- baseline correct / block wrong
- baseline wrong / block correct
- baseline wrong / all blocks wrong
- near miss samples
- unique utility samples per block

The output is intended to guide data construction and rank/capacity scans.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def is_correct(score: float, threshold: float) -> bool:
    return score >= threshold


def sample_record(sample: dict[str, Any], config: str | None = None) -> dict[str, Any]:
    record = {
        "category": sample["category"],
        "prompt": sample["prompt"],
        "scores": sample["scores"],
    }
    if config is not None:
        record["config"] = config
        outputs = sample.get("outputs") or {}
        if config in outputs:
            record["output"] = outputs[config]
        if "baseline" in outputs:
            record["baseline_output"] = outputs["baseline"]
    return record


def mine_report(data: dict[str, Any], correct_threshold: float, near_miss_threshold: float) -> dict[str, Any]:
    configs = list(data["config_results"])
    block_configs = [c for c in configs if c not in ("baseline", "always_all")]

    buckets: dict[str, list[dict[str, Any]]] = {
        "baseline_correct_block_wrong": [],
        "baseline_wrong_block_correct": [],
        "baseline_wrong_all_wrong": [],
        "near_miss": [],
    }
    unique_by_block: dict[str, list[dict[str, Any]]] = defaultdict(list)
    best_by_sample: list[dict[str, Any]] = []

    for idx, sample in enumerate(data["per_sample"]):
        scores = sample["scores"]
        baseline_score = scores.get("baseline", 0.0)
        block_scores = {cfg: scores[cfg] for cfg in block_configs if cfg in scores}
        correct_blocks = [
            cfg for cfg, score in block_scores.items()
            if is_correct(score, correct_threshold)
        ]
        wrong_blocks = [
            cfg for cfg, score in block_scores.items()
            if not is_correct(score, correct_threshold)
        ]

        best_config = max(
            configs,
            key=lambda cfg: (
                scores[cfg],
                -sample["active_counts"].get(cfg, 0),
                -configs.index(cfg),
            ),
        )
        best_by_sample.append({
            "index": idx,
            "category": sample["category"],
            "prompt": sample["prompt"],
            "best_config": best_config,
            "best_score": scores[best_config],
            "baseline_score": baseline_score,
            "delta": scores[best_config] - baseline_score,
        })

        if is_correct(baseline_score, correct_threshold):
            for cfg in wrong_blocks:
                buckets["baseline_correct_block_wrong"].append(sample_record(sample, cfg))
            continue

        if correct_blocks:
            for cfg in correct_blocks:
                buckets["baseline_wrong_block_correct"].append(sample_record(sample, cfg))
            if len(correct_blocks) == 1:
                unique_by_block[correct_blocks[0]].append(sample_record(sample, correct_blocks[0]))
            continue

        buckets["baseline_wrong_all_wrong"].append(sample_record(sample))
        for cfg, score in block_scores.items():
            if score > baseline_score and score >= near_miss_threshold:
                buckets["near_miss"].append(sample_record(sample, cfg))

    summary = {
        "report_model": data.get("model"),
        "benchmark_set": data.get("benchmark_set", "unknown"),
        "total_prompts": data.get("total_prompts", len(data.get("per_sample", []))),
        "block_scale": data.get("block_scale"),
        "configs": configs,
        "oracle": data.get("oracle"),
        "selection_frequency": data.get("selection_frequency"),
        "bucket_counts": {name: len(rows) for name, rows in buckets.items()},
        "unique_utility_counts": {cfg: len(rows) for cfg, rows in unique_by_block.items()},
        "positive_delta_samples": [
            row for row in best_by_sample
            if row["best_config"] != "baseline" and row["delta"] > 0
        ],
    }
    return {
        "summary": summary,
        "buckets": buckets,
        "unique_by_block": dict(unique_by_block),
        "best_by_sample": best_by_sample,
    }


def build_training_texts(mined: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for row in mined["buckets"]["baseline_wrong_block_correct"]:
        cfg = row["config"]
        prompt = row["prompt"]
        output = row.get("output", "").strip()
        if output:
            texts.append(f"Utility block: {cfg}\nQuestion: {prompt}\nPreferred answer:\n{output}")
        else:
            texts.append(f"Utility block: {cfg}\nQuestion: {prompt}\nAnswer:")
    for row in mined["buckets"]["near_miss"]:
        cfg = row["config"]
        prompt = row["prompt"]
        output = row.get("output", "").strip()
        texts.append(f"Near-miss utility block: {cfg}\nQuestion: {prompt}\nImprove this answer:\n{output}")
    return texts


def run(args):
    with open(args.report) as f:
        data = json.load(f)

    mined = mine_report(data, args.correct_threshold, args.near_miss_threshold)
    os.makedirs(args.output_dir, exist_ok=True)

    base = args.tag or os.path.splitext(os.path.basename(args.report))[0]
    json_path = os.path.join(args.output_dir, f"{base}_utility_mining.json")
    texts_path = os.path.join(args.output_dir, f"{base}_training_texts.json")
    md_path = os.path.join(args.output_dir, f"{base}_utility_mining.md")

    with open(json_path, "w") as f:
        json.dump(mined, f, indent=2, ensure_ascii=False)

    texts = build_training_texts(mined)
    with open(texts_path, "w") as f:
        json.dump(texts, f, indent=2, ensure_ascii=False)

    summary = mined["summary"]
    lines = [
        f"# Utility Mining: {base}",
        "",
        f"- Report: `{args.report}`",
        f"- Benchmark: `{summary['benchmark_set']}`",
        f"- Total prompts: `{summary['total_prompts']}`",
        f"- Block scale: `{summary['block_scale']}`",
        f"- Oracle overall: `{summary['oracle']['overall']:.3f}`",
        f"- Selection frequency: `{summary['selection_frequency']}`",
        "",
        "## Bucket Counts",
        "",
    ]
    for name, count in summary["bucket_counts"].items():
        lines.append(f"- `{name}`: {count}")
    lines.extend(["", "## Unique Utility Counts", ""])
    if summary["unique_utility_counts"]:
        for cfg, count in summary["unique_utility_counts"].items():
            lines.append(f"- `{cfg}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Positive Delta Samples", ""])
    for row in summary["positive_delta_samples"]:
        lines.append(
            f"- #{row['index']} `{row['category']}` `{row['best_config']}` "
            f"{row['baseline_score']} -> {row['best_score']}: {row['prompt']}"
        )
    lines.extend(["", "## Outputs", "", f"- JSON: `{json_path}`", f"- Training texts: `{texts_path}`"])
    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Saved mining JSON: {json_path}")
    print(f"Saved training texts: {texts_path}")
    print(f"Saved summary: {md_path}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Mine BitDPM per-sample block utility")
    parser.add_argument("--report", required=True, help="Evaluation JSON report to mine")
    parser.add_argument("--output-dir", default="experiments/reports/v08_utility_mining")
    parser.add_argument("--tag", default="")
    parser.add_argument("--correct-threshold", type=float, default=1.0)
    parser.add_argument("--near-miss-threshold", type=float, default=0.5)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
