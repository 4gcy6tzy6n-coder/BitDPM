#!/usr/bin/env python3
"""Generate external baseline commands for BitDPM paper experiments."""

from __future__ import annotations

import argparse
import os


def join_cmd(parts: list[str]) -> str:
    return " \\\n  ".join(parts)


def prompt_only_cmd(model: str, benchmark: str, policy: str) -> str:
    tag = f"prompt_only_{policy}_{benchmark}"
    return join_cmd(
        [
            "python scripts/run_prompt_only_baseline.py",
            f"--model {model}",
            f"--benchmark-set {benchmark}",
            f"--prompt-policy {policy}",
            "--deterministic",
            "--save-outputs",
            f"--tag {tag}",
        ]
    )


def run(args: argparse.Namespace) -> None:
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# BitDPM external baseline commands.",
        "# These commands evaluate prompt-only baselines. Standard LoRA remains a",
        "# required pending baseline and should be added once a LoRA training/eval",
        "# recipe is finalized.",
        "",
    ]
    for benchmark in args.benchmarks:
        lines.extend(
            [
                f"# Prompt-only baseline on {benchmark}.",
                prompt_only_cmd(args.model, benchmark, args.prompt_policy),
                "",
            ]
        )
    lines.extend(
        [
            "python scripts/build_aaai_baseline_gap_table.py",
            "python scripts/build_paper_package.py",
            "",
            "echo 'External baseline commands complete.'",
        ]
    )
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(args.output, 0o755)
    print(f"Saved: {args.output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate BitDPM external baseline commands.")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--prompt-policy", default="category_aware", choices=["short_answer", "category_aware", "math_direct"])
    parser.add_argument("--benchmarks", nargs="+", default=["v14", "v15", "v1k_clean"])
    parser.add_argument("--output", default="experiments/reports/external_baseline_commands.sh")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
