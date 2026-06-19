#!/usr/bin/env python3
"""Generate v12/v13 systemization commands for BitDPM.

The generated shell assumes v10 is the current best pool and optionally consumes
v11 admission outputs if the user has already run v11 mining.
"""

from __future__ import annotations

import argparse
import itertools
import os


BASE_REPORT = "experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json"
BASE_SAFETY = "experiments/reports/v08_block_safety/v10_admitted_powerlog_stable_sampling_block_safety.json"
BASE_ADMISSION = "experiments/reports/v10_admission/v10_v09b_admission_admission.json"
REGISTRY = "configs/bitdpm_v10_admitted_pool.json"

BASE_DIRS = [
    "experiments/outputs/blocks_v08_error_l22_l24_down_rank16",
    "experiments/outputs/blocks_v09_repair_l22_l24_down_rank16",
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


def run(args):
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    pair_configs = [f"{a}+{b}" for a, b in itertools.combinations(BASE_CONFIGS[1:], 2)]
    configs = BASE_CONFIGS + pair_configs + ["always_all"]

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# BitDPM v12/v13 systemization commands",
        "",
        "echo '=== v12 offline conservative rule router on current best report ==='",
        "python scripts/analyze_v12_rule_router.py \\",
        f"  --report {BASE_REPORT} \\",
        "  --tag v12_v10_conservative_rule_router",
        "",
        "echo '=== v12 mined utility-aware router on current best report ==='",
        "python scripts/train_v12_utility_router.py \\",
        f"  --report {BASE_REPORT} \\",
        "  --tag v12_v10_utility_router_safe \\",
        "  --eval-on-all \\",
        "  --min-fixes 1 \\",
        "  --max-breaks 0 \\",
        "  --min-precision 1.0 \\",
        "  --min-specificity 2 \\",
        "  --full-safety-filter",
        "",
        "echo '=== v12 strict cross-validation for utility-aware router ==='",
        "python scripts/crossval_v12_utility_router.py \\",
        f"  --report {BASE_REPORT} \\",
        "  --tag v12_v10_utility_router_strict_cv \\",
        "  --folds 5 \\",
        "  --min-fixes 1 \\",
        "  --max-breaks 0 \\",
        "  --min-precision 1.0 \\",
        "  --min-specificity 2",
        "",
        "echo '=== v13 safety cards for current best pool ==='",
        "python scripts/build_v13_safety_cards.py \\",
        f"  --safety-report {BASE_SAFETY} \\",
        f"  --admission-report {BASE_ADMISSION} \\",
        f"  --registry {REGISTRY} \\",
        "  --tag v13_v10_best_pool",
        "",
        "echo '=== v13 pairwise incompatibility eval for current best pool ==='",
        "if [ -f experiments/reports/v13_v10_pairwise_stable_sampling_LATEST.json ]; then",
        "  echo 'Skip pairwise eval: experiments/reports/v13_v10_pairwise_stable_sampling_LATEST.json exists'",
        "else",
        join_cmd([
            "  BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py",
            f"--model {args.model}",
            f"--load-blocks {' '.join(BASE_DIRS)}",
            "--benchmark-set v08",
            "--seed 0",
            "--stable-sampling-seeds",
            "--save-outputs",
            "--block-scale 0.75",
            "--block-scales",
            *[f"{name}={scale}" for name, scale in BASE_SCALES.items()],
            "--configs",
            *configs,
            "--tag v13_v10_pairwise_stable_sampling",
        ]),
        "  latest=$(ls -t experiments/reports/v13_v10_pairwise_stable_sampling_*.json | head -1)",
        "  cp \"$latest\" experiments/reports/v13_v10_pairwise_stable_sampling_LATEST.json",
        "fi",
        "",
        "python scripts/analyze_v13_incompatibility.py \\",
        "  --report experiments/reports/v13_v10_pairwise_stable_sampling_LATEST.json \\",
        "  --tag v13_v10_pairwise",
        "",
        "echo 'v12/v13 commands complete.'",
    ]

    with open(args.output, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(args.output, 0o755)
    print(f"Saved: {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Generate BitDPM v12/v13 command script")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--output", default="experiments/reports/v12_v13_system_commands.sh")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
