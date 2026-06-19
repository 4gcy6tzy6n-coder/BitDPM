#!/usr/bin/env python3
"""Evaluate conservative deployable router rules from a BitDPM report.

This is an offline router simulator: it reads an evaluation report containing
baseline and candidate block outputs, applies prompt-only rules, and scores the
chosen config from the already generated per-sample scores. It is meant as the
first deployable-router sanity check before training a learned utility model.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from typing import Any


SPECIAL_CONFIGS = {"baseline", "always_all"}


@dataclass
class Rule:
    name: str
    config: str
    pattern: re.Pattern[str]


DEFAULT_RULE_SPECS = [
    (
        "coordinate_distance_to_power_log",
        "arithmetic_power_log",
        r"\bdistance\b.*\([^)]*\).*\([^)]*\)|\([^)]*\).*\([^)]*\).*\bdistance\b",
    ),
    ("log_power_to_power_log", "arithmetic_power_log", r"\blog\b|log10|\^|\bpower\b|\bexponent"),
    ("sqrt_to_commonsense", "commonsense_choice", r"\bsqrt\b|square root|√"),
    ("percent_to_format", "format_following", r"%|\bpercent\b|百分"),
    (
        "physical_constant_to_format",
        "format_following",
        r"speed of light|gravity|gravitational|electron|proton|avogadro|planck|boltzmann",
    ),
]


def correct(score: float, threshold: float) -> bool:
    return score >= threshold


def load_rules(configs: set[str], custom_rules: list[str] | None) -> list[Rule]:
    specs = list(DEFAULT_RULE_SPECS)
    for item in custom_rules or []:
        if "=" not in item:
            raise ValueError(f"Invalid rule '{item}'. Expected config=regex")
        config, pattern = item.split("=", 1)
        specs.append((f"custom_{config}", config, pattern))

    rules: list[Rule] = []
    for name, config, pattern in specs:
        if config in configs:
            rules.append(Rule(name=name, config=config, pattern=re.compile(pattern, re.I)))
    return rules


def choose_config(prompt: str, rules: list[Rule]) -> tuple[str, str]:
    for rule in rules:
        if rule.pattern.search(prompt):
            return rule.config, rule.name
    return "baseline", "baseline_default"


def best_config(sample: dict[str, Any], configs: list[str]) -> str:
    return max(
        configs,
        key=lambda cfg: (
            sample["scores"].get(cfg, 0.0),
            -sample["active_counts"].get(cfg, 0),
            -configs.index(cfg),
        ),
    )


def run(args):
    with open(args.report) as f:
        data = json.load(f)

    configs = list(data["config_results"])
    candidate_configs = [cfg for cfg in configs if cfg not in SPECIAL_CONFIGS]
    rules = load_rules(set(configs), args.rule)

    rows = []
    score_total = 0.0
    baseline_total = 0.0
    router_fixes = []
    router_breaks = []
    rule_counts: dict[str, int] = {}
    chosen_counts: dict[str, int] = {}

    for idx, sample in enumerate(data["per_sample"]):
        chosen, rule_name = choose_config(sample["prompt"], rules)
        score = sample["scores"].get(chosen, sample["scores"].get("baseline", 0.0))
        baseline_score = sample["scores"].get("baseline", 0.0)
        oracle_cfg = best_config(sample, configs)
        candidate_oracle_cfg = best_config(sample, ["baseline"] + candidate_configs)

        score_total += score
        baseline_total += baseline_score
        rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1
        chosen_counts[chosen] = chosen_counts.get(chosen, 0) + 1

        record = {
            "index": idx,
            "category": sample["category"],
            "prompt": sample["prompt"],
            "rule": rule_name,
            "chosen": chosen,
            "chosen_score": score,
            "baseline_score": baseline_score,
            "oracle_config": oracle_cfg,
            "candidate_oracle_config": candidate_oracle_cfg,
        }
        rows.append(record)
        if not correct(baseline_score, args.correct_threshold) and correct(score, args.correct_threshold):
            router_fixes.append(record)
        elif correct(baseline_score, args.correct_threshold) and not correct(score, args.correct_threshold):
            router_breaks.append(record)

    n = max(len(data["per_sample"]), 1)
    result = {
        "report": args.report,
        "router": args.tag,
        "overall": score_total / n,
        "baseline": baseline_total / n,
        "delta": (score_total - baseline_total) / n,
        "fixes": len(router_fixes),
        "breaks": len(router_breaks),
        "precision_proxy": len(router_fixes) / max(len(router_fixes) + len(router_breaks), 1),
        "rule_counts": rule_counts,
        "chosen_counts": chosen_counts,
        "rules": [{"name": r.name, "config": r.config, "pattern": r.pattern.pattern} for r in rules],
        "rows": rows,
        "fix_samples": router_fixes,
        "break_samples": router_breaks,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    json_path = os.path.join(args.output_dir, f"{args.tag}_rule_router.json")
    md_path = os.path.join(args.output_dir, f"{args.tag}_rule_router.md")
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    lines = [
        "# BitDPM v12 Rule Router",
        "",
        f"- Report: `{args.report}`",
        f"- Router overall: {result['overall']:.3f}",
        f"- Baseline: {result['baseline']:.3f}",
        f"- Delta: {result['delta']:+.3f}",
        f"- Fixes: {result['fixes']}",
        f"- Breaks: {result['breaks']}",
        f"- Precision proxy: {result['precision_proxy']:.3f}",
        f"- Chosen counts: `{chosen_counts}`",
        "",
        "## Rules",
        "",
    ]
    for rule in rules:
        lines.append(f"- `{rule.name}` -> `{rule.config}`: `{rule.pattern.pattern}`")

    lines.extend(["", "## Fix Samples", ""])
    for row in router_fixes:
        lines.append(f"- #{row['index']} `{row['category']}` {row['chosen']} via `{row['rule']}`: {row['prompt']}")

    lines.extend(["", "## Break Samples", ""])
    for row in router_breaks[:30]:
        lines.append(f"- #{row['index']} `{row['category']}` {row['chosen']} via `{row['rule']}`: {row['prompt']}")
    if len(router_breaks) > 30:
        lines.append(f"- ... {len(router_breaks) - 30} more")

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Saved JSON: {json_path}")
    print(f"Saved Markdown: {md_path}")
    print(
        f"router={result['overall']:.3f} baseline={result['baseline']:.3f} "
        f"delta={result['delta']:+.3f} fixes={result['fixes']} breaks={result['breaks']}"
    )


def main():
    parser = argparse.ArgumentParser(description="Evaluate prompt-rule BitDPM router from a report")
    parser.add_argument("--report", required=True)
    parser.add_argument("--output-dir", default="experiments/reports/v12_router")
    parser.add_argument("--tag", default="v12_rule_router")
    parser.add_argument("--correct-threshold", type=float, default=1.0)
    parser.add_argument("--rule", nargs="*", default=None, help="Optional extra rules: config=regex")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
