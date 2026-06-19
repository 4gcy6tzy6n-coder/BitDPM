#!/usr/bin/env python3
"""Generate BitDPM v14 300-sample benchmark commands."""

from __future__ import annotations

import argparse
import os


BASE_DIRS = [
    "experiments/outputs/blocks_v08_error_l22_l24_down_rank16",
    "experiments/outputs/blocks_v09_repair_l22_l24_down_rank16",
]

CONFIGS = [
    "baseline",
    "commonsense_choice",
    "format_following",
    "chinese_semantic",
    "calculation_error",
    "short_reasoning",
    "arithmetic_power_log",
    "always_all",
]

SCALES = {
    "commonsense_choice": 0.60,
    "format_following": 0.75,
    "chinese_semantic": 0.75,
    "calculation_error": 0.30,
    "short_reasoning": 0.45,
    "arithmetic_power_log": 0.75,
}


def join_cmd(parts: list[str]) -> str:
    return " \\\n  ".join(parts)


def run(args):
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    tag = "v14_v10_best_pool_stable_sampling"
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# BitDPM v14 300-sample stratified benchmark",
        "",
        f"if [ -f experiments/reports/{tag}_LATEST.json ]; then",
        f"  echo 'Skip v14 eval: experiments/reports/{tag}_LATEST.json exists'",
        "else",
        join_cmd([
            "  BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py",
            f"--model {args.model}",
            f"--load-blocks {' '.join(BASE_DIRS)}",
            "--benchmark-set v14",
            "--seed 0",
            "--stable-sampling-seeds",
            "--save-outputs",
            "--block-scale 0.75",
            "--block-scales",
            *[f"{name}={scale}" for name, scale in SCALES.items()],
            "--configs",
            *CONFIGS,
            f"--tag {tag}",
        ]),
        f"  latest=$(ls -t experiments/reports/{tag}_*.json | head -1)",
        f"  cp \"$latest\" experiments/reports/{tag}_LATEST.json",
        "fi",
        "",
        "python scripts/analyze_v08_block_safety.py \\",
        f"  --report experiments/reports/{tag}_LATEST.json \\",
        f"  --tag {tag}",
        "",
        "python scripts/mine_v08_utility.py \\",
        f"  --report experiments/reports/{tag}_LATEST.json \\",
        f"  --tag {tag}",
        "",
        "python scripts/analyze_v12_rule_router.py \\",
        f"  --report experiments/reports/{tag}_LATEST.json \\",
        "  --tag v14_v10_rule_router",
        "",
        "python scripts/train_v12_utility_router.py \\",
        f"  --report experiments/reports/{tag}_LATEST.json \\",
        "  --tag v14_v10_utility_router_safe \\",
        "  --eval-on-all \\",
        "  --min-fixes 1 \\",
        "  --max-breaks 0 \\",
        "  --min-precision 1.0 \\",
        "  --min-specificity 2 \\",
        "  --full-safety-filter",
        "",
        "python scripts/crossval_v12_utility_router.py \\",
        f"  --report experiments/reports/{tag}_LATEST.json \\",
        "  --tag v14_v10_utility_router_strict_cv \\",
        "  --folds 5 \\",
        "  --min-fixes 1 \\",
        "  --max-breaks 0 \\",
        "  --min-precision 1.0 \\",
        "  --min-specificity 2",
        "",
        "python scripts/summarize_v14_report.py \\",
        f"  --report experiments/reports/{tag}_LATEST.json \\",
        "  --tag v14_v10_best_pool",
        "",
        "echo 'v14 benchmark commands complete.'",
    ]

    with open(args.output, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(args.output, 0o755)
    print(f"Saved: {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Generate BitDPM v14 benchmark commands")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--output", default="experiments/reports/v14_benchmark_commands.sh")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
