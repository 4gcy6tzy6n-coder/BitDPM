#!/usr/bin/env python3
"""Analyze pairwise BitDPM block incompatibility from combo eval reports."""

from __future__ import annotations

import argparse
import itertools
import json
import os
from typing import Any


SPECIAL_CONFIGS = {"baseline", "always_all"}


def combo_parts(config: str) -> list[str]:
    return config.split("+") if "+" in config else [config]


def correct(score: float, threshold: float) -> bool:
    return score >= threshold


def run(args):
    with open(args.report) as f:
        data = json.load(f)

    configs = list(data["config_results"])
    singles = [cfg for cfg in configs if cfg not in SPECIAL_CONFIGS and "+" not in cfg]
    pairs = [cfg for cfg in configs if "+" in cfg]

    rows = []
    for pair in pairs:
        a, b, *_ = combo_parts(pair)
        if a not in data["config_results"] or b not in data["config_results"]:
            continue
        pair_score = data["config_results"][pair]["overall"]
        a_score = data["config_results"][a]["overall"]
        b_score = data["config_results"][b]["overall"]
        best_single = max(a_score, b_score)
        mean_single = (a_score + b_score) / 2

        pair_fixes = []
        pair_breaks = []
        synergy_samples = []
        conflict_samples = []
        for idx, sample in enumerate(data["per_sample"]):
            baseline = sample["scores"].get("baseline", 0.0)
            sa = sample["scores"].get(a, 0.0)
            sb = sample["scores"].get(b, 0.0)
            sp = sample["scores"].get(pair, 0.0)

            record = {
                "index": idx,
                "category": sample["category"],
                "prompt": sample["prompt"],
                "baseline": baseline,
                a: sa,
                b: sb,
                pair: sp,
            }
            if not correct(baseline, args.correct_threshold) and correct(sp, args.correct_threshold):
                pair_fixes.append(record)
            if correct(baseline, args.correct_threshold) and not correct(sp, args.correct_threshold):
                pair_breaks.append(record)
            if not correct(sa, args.correct_threshold) and not correct(sb, args.correct_threshold) and correct(sp, args.correct_threshold):
                synergy_samples.append(record)
            if (correct(sa, args.correct_threshold) or correct(sb, args.correct_threshold)) and not correct(sp, args.correct_threshold):
                conflict_samples.append(record)

        rows.append({
            "pair": pair,
            "a": a,
            "b": b,
            "pair_score": pair_score,
            "a_score": a_score,
            "b_score": b_score,
            "delta_vs_best_single": pair_score - best_single,
            "delta_vs_mean_single": pair_score - mean_single,
            "pair_fixes": len(pair_fixes),
            "pair_breaks": len(pair_breaks),
            "synergy_samples": len(synergy_samples),
            "conflict_samples": len(conflict_samples),
            "compatible": pair_score >= best_single - args.compatibility_margin and len(conflict_samples) <= args.max_conflict_samples,
            "synergy_sample_records": synergy_samples,
            "conflict_sample_records": conflict_samples,
        })

    rows.sort(key=lambda r: (r["compatible"], r["delta_vs_best_single"], -r["conflict_samples"]), reverse=True)
    matrix = {a: {b: "" for b in singles} for a in singles}
    for a in singles:
        matrix[a][a] = "self"
    for row in rows:
        value = "ok" if row["compatible"] else "conflict"
        matrix[row["a"]][row["b"]] = value
        matrix[row["b"]][row["a"]] = value

    os.makedirs(args.output_dir, exist_ok=True)
    json_path = os.path.join(args.output_dir, f"{args.tag}_incompatibility.json")
    md_path = os.path.join(args.output_dir, f"{args.tag}_incompatibility.md")
    with open(json_path, "w") as f:
        json.dump({"rows": rows, "matrix": matrix}, f, indent=2, ensure_ascii=False)

    lines = [
        "# BitDPM v13 Pairwise Incompatibility",
        "",
        f"- Report: `{args.report}`",
        f"- Compatibility margin: {args.compatibility_margin}",
        "",
        "| Pair | Pair Score | A | B | Delta vs Best | Fixes | Breaks | Synergy | Conflict | Compatible |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['pair']} | {row['pair_score']:.3f} | {row['a_score']:.3f} | "
            f"{row['b_score']:.3f} | {row['delta_vs_best_single']:+.3f} | "
            f"{row['pair_fixes']} | {row['pair_breaks']} | {row['synergy_samples']} | "
            f"{row['conflict_samples']} | {'yes' if row['compatible'] else 'no'} |"
        )

    lines.extend(["", "## Matrix", ""])
    header = "| Block | " + " | ".join(singles) + " |"
    sep = "|---|" + "|".join(["---" for _ in singles]) + "|"
    lines.extend([header, sep])
    for a in singles:
        lines.append("| " + a + " | " + " | ".join(matrix[a][b] for b in singles) + " |")

    lines.extend(["", "## Conflict Samples", ""])
    for row in rows:
        if not row["conflict_sample_records"]:
            continue
        lines.append(f"### {row['pair']}")
        for sample in row["conflict_sample_records"][:20]:
            lines.append(f"- #{sample['index']} `{sample['category']}`: {sample['prompt']}")
        if len(row["conflict_sample_records"]) > 20:
            lines.append(f"- ... {len(row['conflict_sample_records']) - 20} more")
        lines.append("")

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Saved JSON: {json_path}")
    print(f"Saved Markdown: {md_path}")
    print("| pair | score | delta_best | synergy | conflict | compatible |")
    print("|---|---:|---:|---:|---:|---|")
    for row in rows:
        print(
            f"| {row['pair']} | {row['pair_score']:.3f} | {row['delta_vs_best_single']:+.3f} | "
            f"{row['synergy_samples']} | {row['conflict_samples']} | "
            f"{'yes' if row['compatible'] else 'no'} |"
        )


def main():
    parser = argparse.ArgumentParser(description="Analyze BitDPM pairwise incompatibility")
    parser.add_argument("--report", required=True)
    parser.add_argument("--output-dir", default="experiments/reports/v13_safety")
    parser.add_argument("--tag", default="v13")
    parser.add_argument("--correct-threshold", type=float, default=1.0)
    parser.add_argument("--compatibility-margin", type=float, default=0.01)
    parser.add_argument("--max-conflict-samples", type=int, default=2)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
