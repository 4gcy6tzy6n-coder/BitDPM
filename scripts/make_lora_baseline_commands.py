#!/usr/bin/env python3
"""Generate standard LoRA baseline commands for BitDPM paper experiments."""

from __future__ import annotations

import argparse
import os


def join_cmd(parts: list[str]) -> str:
    return " \\\n  ".join(parts)


def lora_cmd(model: str, benchmark: str, train_samples: int, epochs: int) -> str:
    tag = f"lora_r16_{benchmark}"
    return join_cmd(
        [
            "python scripts/run_lora_baseline.py",
            f"--model {model}",
            f"--benchmark-set {benchmark}",
            "--rank 16",
            "--alpha 32",
            f"--train-samples {train_samples}",
            f"--epochs {epochs}",
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
        "# BitDPM standard LoRA baseline commands.",
        "# Requires PEFT: pip install -e '.[peft]'",
        "",
    ]
    for benchmark in args.benchmarks:
        lines.extend(
            [
                f"# Standard LoRA baseline on {benchmark}.",
                lora_cmd(args.model, benchmark, args.train_samples, args.epochs),
                "",
            ]
        )
    lines.extend(
        [
            "python scripts/build_aaai_baseline_gap_table.py",
            "python scripts/build_paper_package.py",
            "",
            "echo 'LoRA baseline commands complete.'",
        ]
    )
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(args.output, 0o755)
    print(f"Saved: {args.output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate BitDPM LoRA baseline commands.")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--benchmarks", nargs="+", default=["v14", "v15", "v1k_clean"])
    parser.add_argument("--train-samples", type=int, default=120)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--output", default="experiments/reports/lora_baseline_commands.sh")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
