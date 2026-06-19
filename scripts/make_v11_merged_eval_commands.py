#!/usr/bin/env python3
"""Generate a faster merged v11 candidate evaluation command.

The original v11 command evaluates each candidate in a separate model run. This
merged version evaluates all v11 candidates in one run, avoiding repeated
baseline/base-pool generations.
"""

from __future__ import annotations

import argparse
import os


BASE_DIRS = [
    "experiments/outputs/blocks_v08_error_l22_l24_down_rank16",
    "experiments/outputs/blocks_v09_repair_l22_l24_down_rank16",
]

V11_DIR = "experiments/outputs/blocks_v11_unique_repair_l22_l24_down_rank16"

BASE_CONFIGS = [
    "baseline",
    "commonsense_choice",
    "format_following",
    "chinese_semantic",
    "calculation_error",
    "short_reasoning",
    "arithmetic_power_log",
]

V11_CANDIDATES = [
    "v11_linear_equation",
    "v11_percent_time_distance",
    "v11_circle_area",
    "v11_stats_number_theory",
    "v11_factorial_derivative",
]

BASE_SCALES = {
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
    tag = "v11_merged_candidates_stable_sampling"
    configs = BASE_CONFIGS + V11_CANDIDATES + ["always_all"]
    scales = dict(BASE_SCALES)
    for candidate in V11_CANDIDATES:
        scales[candidate] = args.candidate_scale

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# BitDPM v11 merged unique-utility candidate evaluation",
        "",
        "if [ ! -f experiments/outputs/blocks_v11_unique_repair_l22_l24_down_rank16/training_summary.json ]; then",
        "  echo 'Missing v11 training outputs. Run experiments/reports/v11_unique_utility_commands.sh first.'",
        "  exit 1",
        "fi",
        "",
        f"if [ -f experiments/reports/{tag}_LATEST.json ]; then",
        f"  echo 'Skip merged eval: experiments/reports/{tag}_LATEST.json exists'",
        "else",
        join_cmd([
            "  BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py",
            f"--model {args.model}",
            f"--load-blocks {' '.join(BASE_DIRS)} {V11_DIR}",
            "--benchmark-set v08",
            "--seed 0",
            "--stable-sampling-seeds",
            "--save-outputs",
            "--block-scale 0.75",
            "--block-scales",
            *[f"{name}={scale}" for name, scale in scales.items()],
            "--configs",
            *configs,
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
        "python scripts/analyze_v10_admission.py \\",
        "  --base v10=experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json \\",
        f"  --candidates v11_merged=experiments/reports/{tag}_LATEST.json \\",
        "  --candidate-blocks \\",
        *[f"  {candidate} \\" for candidate in V11_CANDIDATES],
        "  --tag v11_merged_unique_utility_admission",
        "",
        "python scripts/summarize_v14_report.py \\",
        f"  --report experiments/reports/{tag}_LATEST.json \\",
        "  --tag v11_merged_candidates",
        "",
        "echo 'v11 merged eval complete.'",
    ]

    with open(args.output, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(args.output, 0o755)
    print(f"Saved: {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Generate merged v11 eval commands")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--candidate-scale", type=float, default=0.75)
    parser.add_argument("--output", default="experiments/reports/v11_merged_eval_commands.sh")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
