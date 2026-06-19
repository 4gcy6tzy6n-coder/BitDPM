#!/usr/bin/env python3
"""Generate BitDPM v0.8 rank/capacity scan commands.

The generated commands focus on the strongest v0.7 structure:

- error-type datasets
- l22_l24_down structure
- rank scan: 8 / 16 / 32 / 64 by default
- scale scan: 0.45 / 0.60 / 0.75 by default
"""

from __future__ import annotations

import argparse
import os


DATASETS = [
    "calculation_error",
    "commonsense_choice",
    "format_following",
    "chinese_semantic",
    "short_reasoning",
]


def command_block(lines: list[str]) -> str:
    return " \\\n  ".join(lines)


def train_command(model: str, output_dir: str, rank: int, epochs: int, lr: float, max_length: int) -> str:
    return command_block([
        "BITDPM_FORCE_CPU=1 python scripts/train_v07_blocks.py",
        f"--model {model}",
        f"--output-dir {output_dir}",
        f"--datasets {' '.join(DATASETS)}",
        "--structure l22_l24_down",
        f"--rank {rank}",
        f"--epochs {epochs}",
        "--batch-size 1",
        f"--lr {lr}",
        f"--max-length {max_length}",
    ])


def eval_command(
    model: str,
    block_dir: str,
    scale: float,
    benchmark_set: str,
    tag: str,
    deterministic: bool,
) -> str:
    parts = [
        "BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py",
        f"--model {model}",
        f"--load-blocks {block_dir}",
        f"--benchmark-set {benchmark_set}",
        "--save-outputs",
        f"--block-scale {scale:.2f}",
        f"--tag {tag}",
    ]
    if deterministic:
        parts.append("--deterministic")
    else:
        parts.extend(["--seed 0", "--stable-sampling-seeds"])
    return command_block(parts)


def run(args):
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    ranks = [int(x) for x in args.ranks]
    scales = [float(x) for x in args.scales]

    lines: list[str] = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# BitDPM v0.8 capacity scan commands.",
        "# Run this whole file or copy individual blocks.",
        "",
    ]
    md: list[str] = [
        "# BitDPM v0.8 Capacity Scan",
        "",
        "Focus: error-type `l22_l24_down` with rank/capacity scan.",
        "",
        f"- Ranks: `{ranks}`",
        f"- Scales: `{scales}`",
        f"- Benchmark set: `{args.benchmark_set}`",
        "",
    ]

    for rank in ranks:
        block_dir = f"{args.output_root}/blocks_v08_error_l22_l24_down_rank{rank}"
        lines.extend([
            f"echo '=== Train rank {rank} ==='",
            train_command(args.model, block_dir, rank, args.epochs, args.lr, args.max_length),
            "",
        ])
        md.extend([
            f"## Rank {rank}",
            "",
            "Training:",
            "",
            "```bash",
            train_command(args.model, block_dir, rank, args.epochs, args.lr, args.max_length),
            "```",
            "",
        ])
        for scale in scales:
            scale_tag = str(scale).replace(".", "")
            det_tag = f"v08_rank{rank}_scale{scale_tag}_{args.benchmark_set}_det"
            sampling_tag = f"v08_rank{rank}_scale{scale_tag}_{args.benchmark_set}_stable_sampling"
            lines.extend([
                f"echo '=== Eval rank {rank} scale {scale:.2f} deterministic ==='",
                eval_command(args.model, block_dir, scale, args.benchmark_set, det_tag, deterministic=True),
                "",
                f"echo '=== Eval rank {rank} scale {scale:.2f} stable sampling ==='",
                eval_command(args.model, block_dir, scale, args.benchmark_set, sampling_tag, deterministic=False),
                "",
            ])
            md.extend([
                f"Scale `{scale:.2f}` deterministic:",
                "",
                "```bash",
                eval_command(args.model, block_dir, scale, args.benchmark_set, det_tag, deterministic=True),
                "```",
                "",
                f"Scale `{scale:.2f}` stable sampling:",
                "",
                "```bash",
                eval_command(args.model, block_dir, scale, args.benchmark_set, sampling_tag, deterministic=False),
                "```",
                "",
            ])

    with open(args.output, "w") as f:
        f.write("\n".join(lines))
    os.chmod(args.output, 0o755)

    md_path = os.path.splitext(args.output)[0] + ".md"
    with open(md_path, "w") as f:
        f.write("\n".join(md) + "\n")

    print(f"Saved shell commands: {args.output}")
    print(f"Saved markdown commands: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate v0.8 rank/capacity scan commands")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--output-root", default="experiments/outputs")
    parser.add_argument("--output", default="experiments/reports/v08_capacity_scan_commands.sh")
    parser.add_argument("--benchmark-set", default="v08", choices=["core", "v08"])
    parser.add_argument("--ranks", nargs="+", default=["8", "16", "32", "64"])
    parser.add_argument("--scales", nargs="+", default=["0.45", "0.60", "0.75"])
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-length", type=int, default=96)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
