#!/usr/bin/env python3
"""Cross-validate the BitDPM v12 utility-aware router miner.

This script is deliberately stricter than the full-report safety-filter
prototype. Each fold mines rules only from its training split and evaluates on
held-out prompts. It estimates whether sparse correction rules generalize beyond
the exact samples used to admit them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from typing import Any

from train_v12_utility_router import evaluate_router, mine_rules, parse_feature_list, rank_rules


def fold_for_sample(sample: dict[str, Any], folds: int) -> int:
    key = f"{sample['category']}::{sample['prompt']}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % folds


def run(args):
    with open(args.report) as f:
        data = json.load(f)

    samples = data["per_sample"]
    fold_rows = []
    all_eval_rows = []
    total_score = 0.0
    total_baseline = 0.0
    total_count = 0
    total_fixes = 0
    total_breaks = 0
    allowed_features = parse_feature_list(args.allowed_features)
    denied_features = parse_feature_list(args.denied_features)

    for fold in range(args.folds):
        train_idx = [
            idx for idx, sample in enumerate(samples)
            if fold_for_sample(sample, args.folds) != fold
        ]
        eval_idx = [
            idx for idx, sample in enumerate(samples)
            if fold_for_sample(sample, args.folds) == fold
        ]
        rules = mine_rules(
            data=data,
            indices=train_idx,
            threshold=args.correct_threshold,
            min_fixes=args.min_fixes,
            max_breaks=args.max_breaks,
            min_precision=args.min_precision,
            min_specificity=args.min_specificity,
            allowed_features=allowed_features,
            denied_features=denied_features,
            include_conjunctions=args.include_conjunctions,
            min_support=args.min_support,
        )
        rules = rank_rules(rules)
        eval_result = evaluate_router(data, eval_idx, rules, args.correct_threshold, args.include_conjunctions)

        fold_rows.append({
            "fold": fold,
            "train_count": len(train_idx),
            "eval_count": len(eval_idx),
            "rules": [rule.__dict__ for rule in rules],
            "result": eval_result,
        })
        all_eval_rows.extend(eval_result["rows"])
        total_score += eval_result["overall"] * len(eval_idx)
        total_baseline += eval_result["baseline"] * len(eval_idx)
        total_count += len(eval_idx)
        total_fixes += eval_result["fixes"]
        total_breaks += eval_result["breaks"]

    overall = total_score / max(total_count, 1)
    baseline = total_baseline / max(total_count, 1)
    summary = {
        "report": args.report,
        "folds": args.folds,
        "total_eval_count": total_count,
        "overall": overall,
        "baseline": baseline,
        "delta": overall - baseline,
        "fixes": total_fixes,
        "breaks": total_breaks,
        "precision_proxy": total_fixes / max(total_fixes + total_breaks, 1),
    }
    payload = {
        "summary": summary,
        "allowed_features": sorted(allowed_features) if allowed_features else None,
        "denied_features": sorted(denied_features) if denied_features else None,
        "include_conjunctions": args.include_conjunctions,
        "min_support": args.min_support,
        "folds": fold_rows,
        "eval_rows": all_eval_rows,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    json_path = os.path.join(args.output_dir, f"{args.tag}_crossval.json")
    md_path = os.path.join(args.output_dir, f"{args.tag}_crossval.md")
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    lines = [
        "# BitDPM v12 Utility Router Cross-Validation",
        "",
        f"- Report: `{args.report}`",
        f"- Folds: {args.folds}",
        f"- Overall: {overall:.3f}",
        f"- Baseline: {baseline:.3f}",
        f"- Delta: {overall - baseline:+.3f}",
        f"- Fixes: {total_fixes}",
        f"- Breaks: {total_breaks}",
        f"- Precision proxy: {summary['precision_proxy']:.3f}",
        f"- Allowed features: `{sorted(allowed_features) if allowed_features else None}`",
        f"- Denied features: `{sorted(denied_features) if denied_features else None}`",
        f"- Include conjunctions: `{args.include_conjunctions}`",
        f"- Min support: {args.min_support}",
        "",
        "## Folds",
        "",
        "| Fold | Eval N | Rules | Router | Baseline | Delta | Fixes | Breaks |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in fold_rows:
        result = row["result"]
        lines.append(
            f"| {row['fold']} | {row['eval_count']} | {len(row['rules'])} | "
            f"{result['overall']:.3f} | {result['baseline']:.3f} | "
            f"{result['delta']:+.3f} | {result['fixes']} | {result['breaks']} |"
        )

    lines.extend(["", "## Held-Out Fix Samples", ""])
    for row in fold_rows:
        for sample in row["result"]["fix_samples"]:
            lines.append(
                f"- fold={row['fold']} #{sample['index']} `{sample['category']}` "
                f"{sample['choice']} via `{sample['feature']}`: {sample['prompt']}"
            )

    lines.extend(["", "## Held-Out Break Samples", ""])
    for row in fold_rows:
        for sample in row["result"]["break_samples"][:20]:
            lines.append(
                f"- fold={row['fold']} #{sample['index']} `{sample['category']}` "
                f"{sample['choice']} via `{sample['feature']}`: {sample['prompt']}"
            )

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Saved JSON: {json_path}")
    print(f"Saved Markdown: {md_path}")
    print(
        f"cv={overall:.3f} baseline={baseline:.3f} delta={overall - baseline:+.3f} "
        f"fixes={total_fixes} breaks={total_breaks}"
    )


def main():
    parser = argparse.ArgumentParser(description="Cross-validate BitDPM utility router rules")
    parser.add_argument("--report", required=True)
    parser.add_argument("--output-dir", default="experiments/reports/v12_router")
    parser.add_argument("--tag", default="v12_utility_router")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--correct-threshold", type=float, default=1.0)
    parser.add_argument("--min-fixes", type=int, default=1)
    parser.add_argument("--max-breaks", type=int, default=0)
    parser.add_argument("--min-precision", type=float, default=1.0)
    parser.add_argument("--min-specificity", type=int, default=0,
                        help="Minimum feature specificity: 0=allow category, 1=allow broad numeric, 2=specific prompt features only.")
    parser.add_argument("--allowed-features", default="",
                        help="Comma-separated feature allowlist. Empty means all features are allowed.")
    parser.add_argument("--denied-features", default="",
                        help="Comma-separated feature denylist applied after mining.")
    parser.add_argument("--include-conjunctions", action="store_true",
                        help="Include category-feature conjunctions such as category=arithmetic&has_log.")
    parser.add_argument("--min-support", type=int, default=1,
                        help="Minimum number of training samples matching a feature-block rule.")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
