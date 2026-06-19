#!/usr/bin/env python3
"""Mine conservative utility-aware router rules from a BitDPM report.

The router target is not semantic block matching. It learns prompt-feature
guards that predict rare per-sample correction opportunities while keeping
breaks low. The script uses already generated per-sample scores, so it is cheap
and can be run after any v08/v14 evaluation report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass
from typing import Any


SPECIAL_CONFIGS = {"baseline", "always_all"}


FEATURE_SPECS = [
    ("has_percent", r"%|\bpercent\b|百分"),
    ("has_sqrt", r"\bsqrt\b|square root|√"),
    ("has_log", r"\blog\b|log10|log base"),
    ("has_power", r"\^|\bpower\b|\bexponent"),
    ("has_coordinate", r"\([^)]*,[^)]*\)"),
    ("has_distance", r"\bdistance\b"),
    ("has_speed_light", r"speed of light"),
    ("has_physical_constant", r"gravity|gravitational|avogadro|planck|boltzmann|electron|proton|speed of light"),
    ("has_chemical_symbol", r"chemical symbol"),
    ("has_area", r"\barea\b|circle|radius"),
    ("has_equation", r"\bsolve\b|x\s*[+\-*]|=\s*\d+"),
    ("has_factorial", r"factorial|!"),
    ("has_mean", r"\bmean\b|average"),
    ("has_gcd_lcm", r"\bgcd\b|\blcm\b"),
    ("has_addition", r"\d+\s*\+\s*\d+|\bplus\b"),
    ("has_multiplication", r"\d+\s*(?:times|x|×|\*)\s*\d+"),
    ("has_division", r"divided by|/"),
    ("has_time_distance", r"km/h|hours?|minutes?|seconds?|train travels|car travels"),
    ("has_probability", r"probability|coin"),
    ("asks_brief", r"brief|short|concise|简短"),
    ("is_chinese_prompt", r"[\u4e00-\u9fff]"),
    ("asks_code", r"\bpython\b|\bsql\b|\bregex\b|\bjson\b|\bfunction\b|\bcode\b"),
]


@dataclass
class Rule:
    feature: str
    block: str
    fixes: int
    breaks: int
    precision_proxy: float
    support: int


def stable_bucket(text: str, modulo: int = 100) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulo


def parse_feature_list(value: str) -> set[str] | None:
    features = {item.strip() for item in value.split(",") if item.strip()}
    return features or None


def feature_allowed(feature: str, allowed_features: set[str] | None, denied_features: set[str] | None) -> bool:
    parts = set(feature.split("&"))
    if allowed_features is not None and feature not in allowed_features and not (parts & allowed_features):
        return False
    if denied_features is not None and (feature in denied_features or bool(parts & denied_features)):
        return False
    return True


def correct(score: float, threshold: float) -> bool:
    return score >= threshold


def compile_features() -> list[tuple[str, re.Pattern[str]]]:
    return [(name, re.compile(pattern, re.I)) for name, pattern in FEATURE_SPECS]


def sample_features(
    sample: dict[str, Any],
    feature_regexes: list[tuple[str, re.Pattern[str]]],
    include_conjunctions: bool = False,
) -> set[str]:
    prompt = sample["prompt"]
    features = {name for name, pattern in feature_regexes if pattern.search(prompt)}
    category_feature = f"category={sample['category']}"
    features.add(category_feature)

    numbers = re.findall(r"\d+(?:\.\d+)?", prompt)
    if numbers:
        features.add("has_number")
    if len(numbers) >= 2:
        features.add("has_2plus_numbers")
    if len(numbers) >= 3:
        features.add("has_3plus_numbers")
    if len(prompt) <= 80:
        features.add("short_prompt")
    elif len(prompt) >= 160:
        features.add("long_prompt")
    if include_conjunctions:
        atomic_features = [feature for feature in features if not feature.startswith("category=")]
        for feature in atomic_features:
            features.add(f"{category_feature}&{feature}")
    return features


def split_samples(samples: list[dict[str, Any]], train_ratio: float) -> tuple[list[int], list[int]]:
    train: list[int] = []
    eval_idx: list[int] = []
    for idx, sample in enumerate(samples):
        key = f"{sample['category']}::{sample['prompt']}"
        if stable_bucket(key) < int(train_ratio * 100):
            train.append(idx)
        else:
            eval_idx.append(idx)
    if not train or not eval_idx:
        midpoint = max(1, len(samples) // 2)
        train = list(range(midpoint))
        eval_idx = list(range(midpoint, len(samples)))
    return train, eval_idx


def mine_rules(
    data: dict[str, Any],
    indices: list[int],
    threshold: float,
    min_fixes: int,
    max_breaks: int,
    min_precision: float,
    min_specificity: int = 0,
    allowed_features: set[str] | None = None,
    denied_features: set[str] | None = None,
    include_conjunctions: bool = False,
    min_support: int = 1,
) -> list[Rule]:
    samples = data["per_sample"]
    configs = [cfg for cfg in data["config_results"] if cfg not in SPECIAL_CONFIGS]
    feature_regexes = compile_features()
    stats: dict[tuple[str, str], dict[str, int]] = {}

    for idx in indices:
        sample = samples[idx]
        features = sample_features(sample, feature_regexes, include_conjunctions)
        baseline_ok = correct(sample["scores"].get("baseline", 0.0), threshold)
        for block in configs:
            block_ok = correct(sample["scores"].get(block, 0.0), threshold)
            for feature in features:
                row = stats.setdefault((feature, block), {"support": 0, "fixes": 0, "breaks": 0})
                row["support"] += 1
                if not baseline_ok and block_ok:
                    row["fixes"] += 1
                elif baseline_ok and not block_ok:
                    row["breaks"] += 1

    rules: list[Rule] = []
    for (feature, block), row in stats.items():
        if not feature_allowed(feature, allowed_features, denied_features):
            continue
        if feature_specificity(feature) < min_specificity:
            continue
        if row["support"] < min_support:
            continue
        fixes = row["fixes"]
        breaks = row["breaks"]
        precision = fixes / max(fixes + breaks, 1)
        if fixes >= min_fixes and breaks <= max_breaks and precision >= min_precision:
            rules.append(
                Rule(
                    feature=feature,
                    block=block,
                    fixes=fixes,
                    breaks=breaks,
                    precision_proxy=precision,
                    support=row["support"],
                )
            )

    rules.sort(key=lambda r: (r.precision_proxy, r.fixes, -r.breaks, -r.support), reverse=True)
    return rules


def rule_break_count(
    data: dict[str, Any],
    indices: list[int],
    rule: Rule,
    threshold: float,
    include_conjunctions: bool = False,
) -> int:
    samples = data["per_sample"]
    feature_regexes = compile_features()
    breaks = 0
    for idx in indices:
        sample = samples[idx]
        if rule.feature not in sample_features(sample, feature_regexes, include_conjunctions):
            continue
        baseline_ok = correct(sample["scores"].get("baseline", 0.0), threshold)
        block_ok = correct(sample["scores"].get(rule.block, 0.0), threshold)
        if baseline_ok and not block_ok:
            breaks += 1
    return breaks


def feature_specificity(feature: str) -> int:
    if "&" in feature:
        return 3
    if feature.startswith("category="):
        return 0
    if feature in {"has_number", "has_2plus_numbers", "has_3plus_numbers", "short_prompt", "long_prompt"}:
        return 1
    return 2


def rank_rules(rules: list[Rule]) -> list[Rule]:
    return sorted(
        rules,
        key=lambda r: (
            r.precision_proxy,
            r.fixes,
            feature_specificity(r.feature),
            -r.breaks,
            -r.support,
        ),
        reverse=True,
    )


def choose_block(
    sample: dict[str, Any],
    rules: list[Rule],
    feature_regexes: list[tuple[str, re.Pattern[str]]],
    include_conjunctions: bool = False,
) -> tuple[str, str]:
    features = sample_features(sample, feature_regexes, include_conjunctions)
    for rule in rules:
        if rule.feature in features:
            return rule.block, rule.feature
    return "baseline", "baseline_default"


def evaluate_router(
    data: dict[str, Any],
    indices: list[int],
    rules: list[Rule],
    threshold: float,
    include_conjunctions: bool = False,
) -> dict[str, Any]:
    samples = data["per_sample"]
    feature_regexes = compile_features()
    total = 0.0
    baseline_total = 0.0
    fixes = []
    breaks = []
    choices: dict[str, int] = {}
    rule_hits: dict[str, int] = {}
    rows = []

    for idx in indices:
        sample = samples[idx]
        block, feature = choose_block(sample, rules, feature_regexes, include_conjunctions)
        score = sample["scores"].get(block, sample["scores"].get("baseline", 0.0))
        baseline_score = sample["scores"].get("baseline", 0.0)
        total += score
        baseline_total += baseline_score
        choices[block] = choices.get(block, 0) + 1
        rule_hits[feature] = rule_hits.get(feature, 0) + 1

        record = {
            "index": idx,
            "category": sample["category"],
            "prompt": sample["prompt"],
            "choice": block,
            "feature": feature,
            "score": score,
            "baseline_score": baseline_score,
        }
        rows.append(record)
        if not correct(baseline_score, threshold) and correct(score, threshold):
            fixes.append(record)
        elif correct(baseline_score, threshold) and not correct(score, threshold):
            breaks.append(record)

    n = max(len(indices), 1)
    return {
        "overall": total / n,
        "baseline": baseline_total / n,
        "delta": (total - baseline_total) / n,
        "fixes": len(fixes),
        "breaks": len(breaks),
        "precision_proxy": len(fixes) / max(len(fixes) + len(breaks), 1),
        "choices": choices,
        "rule_hits": rule_hits,
        "rows": rows,
        "fix_samples": fixes,
        "break_samples": breaks,
    }


def run(args):
    with open(args.report) as f:
        data = json.load(f)

    samples = data["per_sample"]
    train_idx, eval_idx = split_samples(samples, args.train_ratio)
    if args.eval_on_all:
        eval_idx = list(range(len(samples)))

    allowed_features = parse_feature_list(args.allowed_features)
    denied_features = parse_feature_list(args.denied_features)
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
    if args.full_safety_filter:
        all_indices = list(range(len(samples)))
        rules = [
            rule for rule in rules
            if rule_break_count(data, all_indices, rule, args.correct_threshold, args.include_conjunctions) <= args.max_breaks
        ]
    rules = rank_rules(rules)
    eval_result = evaluate_router(data, eval_idx, rules, args.correct_threshold, args.include_conjunctions)
    train_result = evaluate_router(data, train_idx, rules, args.correct_threshold, args.include_conjunctions)

    payload = {
        "report": args.report,
        "train_ratio": args.train_ratio,
        "train_count": len(train_idx),
        "eval_count": len(eval_idx),
        "rules": [rule.__dict__ for rule in rules],
        "allowed_features": sorted(allowed_features) if allowed_features else None,
        "denied_features": sorted(denied_features) if denied_features else None,
        "include_conjunctions": args.include_conjunctions,
        "train": train_result,
        "eval": eval_result,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    json_path = os.path.join(args.output_dir, f"{args.tag}_utility_router.json")
    md_path = os.path.join(args.output_dir, f"{args.tag}_utility_router.md")
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    lines = [
        "# BitDPM v12 Utility-Aware Router Miner",
        "",
        f"- Report: `{args.report}`",
        f"- Train samples: {len(train_idx)}",
        f"- Eval samples: {len(eval_idx)}",
        f"- Rules: {len(rules)}",
        f"- Allowed features: `{sorted(allowed_features) if allowed_features else None}`",
        f"- Denied features: `{sorted(denied_features) if denied_features else None}`",
        f"- Include conjunctions: `{args.include_conjunctions}`",
        "",
        "## Eval Result",
        "",
        f"- Router: {eval_result['overall']:.3f}",
        f"- Baseline: {eval_result['baseline']:.3f}",
        f"- Delta: {eval_result['delta']:+.3f}",
        f"- Fixes: {eval_result['fixes']}",
        f"- Breaks: {eval_result['breaks']}",
        f"- Precision proxy: {eval_result['precision_proxy']:.3f}",
        f"- Choices: `{eval_result['choices']}`",
        "",
        "## Learned Rules",
        "",
        "| Feature | Block | Fixes | Breaks | Precision | Support |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for rule in rules:
        lines.append(
            f"| {rule.feature} | {rule.block} | {rule.fixes} | {rule.breaks} | "
            f"{rule.precision_proxy:.3f} | {rule.support} |"
        )

    lines.extend(["", "## Eval Fix Samples", ""])
    for row in eval_result["fix_samples"]:
        lines.append(f"- #{row['index']} `{row['category']}` {row['choice']} via `{row['feature']}`: {row['prompt']}")

    lines.extend(["", "## Eval Break Samples", ""])
    for row in eval_result["break_samples"][:30]:
        lines.append(f"- #{row['index']} `{row['category']}` {row['choice']} via `{row['feature']}`: {row['prompt']}")
    if len(eval_result["break_samples"]) > 30:
        lines.append(f"- ... {len(eval_result['break_samples']) - 30} more")

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Saved JSON: {json_path}")
    print(f"Saved Markdown: {md_path}")
    print(
        f"rules={len(rules)} eval={eval_result['overall']:.3f} "
        f"baseline={eval_result['baseline']:.3f} delta={eval_result['delta']:+.3f} "
        f"fixes={eval_result['fixes']} breaks={eval_result['breaks']}"
    )


def main():
    parser = argparse.ArgumentParser(description="Mine utility-aware BitDPM router rules")
    parser.add_argument("--report", required=True)
    parser.add_argument("--output-dir", default="experiments/reports/v12_router")
    parser.add_argument("--tag", default="v12_utility_router")
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--eval-on-all", action="store_true")
    parser.add_argument("--correct-threshold", type=float, default=1.0)
    parser.add_argument("--min-fixes", type=int, default=1)
    parser.add_argument("--max-breaks", type=int, default=0)
    parser.add_argument("--min-precision", type=float, default=1.0)
    parser.add_argument("--min-specificity", type=int, default=0,
                        help="Minimum feature specificity: 0=allow category, 1=allow broad numeric, 2=specific prompt features only.")
    parser.add_argument("--full-safety-filter", action="store_true",
                        help="Drop mined rules that break any baseline-correct sample in the full report.")
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
