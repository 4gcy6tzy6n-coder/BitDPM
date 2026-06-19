#!/usr/bin/env python3
"""Generate v14 registry-based validation commands for v10/v11 pools."""

from __future__ import annotations

import argparse
import os


def run(args):
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# BitDPM v14 registry-based validation",
        "# Pilot commands run 10 prompts/category (60 total) before expensive full v14.",
        "",
        "echo '=== v14 pilot: v10 admitted pool ==='",
        "python scripts/run_v10_registry_eval.py \\",
        "  --registry configs/bitdpm_v10_admitted_pool.json \\",
        "  --benchmark-set v14 \\",
        "  --max-prompts-per-category 10 \\",
        "  --tag v14_pilot_v10_admitted",
        "",
        "echo '=== v14 pilot: v11 admitted pool ==='",
        "python scripts/run_v10_registry_eval.py \\",
        "  --registry configs/bitdpm_v11_admitted_pool.json \\",
        "  --benchmark-set v14 \\",
        "  --max-prompts-per-category 10 \\",
        "  --tag v14_pilot_v11_admitted",
        "",
        "python scripts/summarize_v14_report.py \\",
        "  --report \"$(ls -t experiments/reports/v14_pilot_v10_admitted_*.json | head -1)\" \\",
        "  --tag v14_pilot_v10_admitted",
        "",
        "python scripts/summarize_v14_report.py \\",
        "  --report \"$(ls -t experiments/reports/v14_pilot_v11_admitted_*.json | head -1)\" \\",
        "  --tag v14_pilot_v11_admitted",
        "",
        "echo '=== Optional full v14 commands ==='",
        "echo 'Run these manually after inspecting pilot results:'",
        "echo 'python scripts/run_v10_registry_eval.py --registry configs/bitdpm_v10_admitted_pool.json --benchmark-set v14 --tag v14_full_v10_admitted'",
        "echo 'python scripts/run_v10_registry_eval.py --registry configs/bitdpm_v11_admitted_pool.json --benchmark-set v14 --tag v14_full_v11_admitted'",
    ]
    with open(args.output, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(args.output, 0o755)
    print(f"Saved: {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Generate v14 registry eval commands")
    parser.add_argument("--output", default="experiments/reports/v14_registry_eval_commands.sh")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
