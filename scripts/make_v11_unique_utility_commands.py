#!/usr/bin/env python3
"""Generate v11 unique-utility repair mining commands.

The generated shell trains candidate repair blocks for the remaining failures
of the v10 admitted pool, evaluates each candidate as an add-on to the current
pool, and runs admission analysis against the v10 base report.
"""

from __future__ import annotations

import argparse
import os


V11_DATASETS = [
    "v11_linear_equation",
    "v11_percent_time_distance",
    "v11_circle_area",
    "v11_stats_number_theory",
    "v11_factorial_derivative",
]

BASE_CONFIGS = [
    "baseline",
    "commonsense_choice",
    "format_following",
    "chinese_semantic",
    "calculation_error",
    "short_reasoning",
    "arithmetic_power_log",
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


def eval_command(
    model: str,
    base_dirs: list[str],
    repair_dir: str,
    candidate: str,
    tag: str,
    scale: float,
) -> str:
    scales = dict(BASE_SCALES)
    scales[candidate] = scale
    configs = BASE_CONFIGS + [candidate, "always_all"]
    parts = [
        "BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py",
        f"--model {model}",
        f"--load-blocks {' '.join(base_dirs)} {repair_dir}",
        "--benchmark-set v08",
        "--seed 0",
        "--stable-sampling-seeds",
        "--save-outputs",
        "--block-scale 0.75",
        "--block-scales",
        *[f"{name}={value}" for name, value in scales.items()],
        "--configs",
        *configs,
        f"--tag {tag}",
    ]
    return join_cmd(parts)


def safety_and_mining(tag: str) -> str:
    report = f"$(ls -t experiments/reports/{tag}_*.json | head -1)"
    return "\n".join([
        "python scripts/analyze_v08_block_safety.py \\",
        f"  --report \"{report}\" \\",
        f"  --tag {tag}",
        "python scripts/mine_v08_utility.py \\",
        f"  --report \"{report}\" \\",
        f"  --tag {tag}",
    ])


def run(args):
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    repair_dir = args.repair_dir

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# BitDPM v11 Unique-Utility Repair Mining",
        "",
        "echo '=== Train v11 candidate repair blocks ==='",
        f"if [ -f {repair_dir}/training_summary.json ]; then",
        f"  echo 'Skip training: {repair_dir}/training_summary.json exists'",
        "else",
        join_cmd([
            "  BITDPM_FORCE_CPU=1 python scripts/train_v07_blocks.py",
            f"--model {args.model}",
            f"--output-dir {repair_dir}",
            f"--datasets {' '.join(V11_DATASETS)}",
            "--structure l22_l24_down",
            "--rank 16",
            "--epochs 5",
            "--batch-size 1",
            "--lr 2e-4",
            "--max-length 96",
        ]),
        "fi",
        "",
    ]

    candidate_reports: list[str] = []
    for candidate in V11_DATASETS:
        tag = f"v11_add_{candidate}_stable_sampling"
        candidate_reports.append(f"{candidate}=experiments/reports/{tag}_LATEST.json")
        lines.extend([
            f"echo '=== Eval candidate {candidate} ==='",
            f"if [ -f experiments/reports/{tag}_LATEST.json ]; then",
            f"  echo 'Skip eval: experiments/reports/{tag}_LATEST.json exists'",
            "else",
            eval_command(args.model, args.base_dirs, repair_dir, candidate, tag, args.candidate_scale).replace(
                "BITDPM_FORCE_CPU=1", "  BITDPM_FORCE_CPU=1", 1
            ),
            "",
            safety_and_mining(tag).replace("\n", "\n  "),
            "",
            f"  latest=$(ls -t experiments/reports/{tag}_*.json | head -1)",
            f"  cp \"$latest\" experiments/reports/{tag}_LATEST.json",
            "fi",
            "",
        ])

    lines.extend([
        "echo '=== v11 admission analysis ==='",
        "python scripts/analyze_v10_admission.py \\",
        f"  --base v10=experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json \\",
        "  --candidates \\",
    ])
    for idx, candidate in enumerate(V11_DATASETS):
        lines.append(f"  {candidate}=experiments/reports/v11_add_{candidate}_stable_sampling_LATEST.json \\")
    lines.extend([
        "  --tag v11_unique_utility_admission",
        "",
        "echo 'v11 commands complete.'",
    ])

    with open(args.output, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(args.output, 0o755)

    print(f"Saved: {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Generate v11 unique-utility commands")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument(
        "--base-dirs",
        nargs="+",
        default=[
            "experiments/outputs/blocks_v08_error_l22_l24_down_rank16",
            "experiments/outputs/blocks_v09_repair_l22_l24_down_rank16",
        ],
    )
    parser.add_argument("--repair-dir", default="experiments/outputs/blocks_v11_unique_repair_l22_l24_down_rank16")
    parser.add_argument("--candidate-scale", type=float, default=0.75)
    parser.add_argument("--output", default="experiments/reports/v11_unique_utility_commands.sh")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
