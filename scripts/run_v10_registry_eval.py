#!/usr/bin/env python3
"""Run a BitDPM evaluation from a block-pool registry JSON.

The registry fixes the current admitted pool, scales, configs, and benchmark
protocol so the v10 best setting can be reproduced without hand-copying a long
command.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys


def shell_join(parts: list[str]) -> str:
    return " ".join(parts)


def run_cmd(cmd: list[str], dry_run: bool):
    print(shell_join(cmd))
    if not dry_run:
        subprocess.run(cmd, check=True)


def latest_report(tag: str, reports_dir: str) -> str:
    matches = [
        os.path.join(reports_dir, name)
        for name in os.listdir(reports_dir)
        if name.startswith(tag + "_") and name.endswith(".json")
    ]
    if not matches:
        raise FileNotFoundError(f"No report found for tag {tag} in {reports_dir}")
    return max(matches, key=os.path.getmtime)


def run(args):
    with open(args.registry) as f:
        registry = json.load(f)

    tag = args.tag or registry["name"]
    reports_dir = args.output
    os.makedirs(reports_dir, exist_ok=True)

    benchmark_set = args.benchmark_set or registry.get("benchmark_set", "v08")
    eval_cmd = [
        sys.executable,
        "scripts/run_v05_router_calibration.py",
        "--model",
        args.model,
        "--load-blocks",
        *registry["load_blocks"],
        "--benchmark-set",
        benchmark_set,
        "--save-outputs",
        "--block-scale",
        str(registry.get("global_block_scale", 0.75)),
        "--configs",
        *registry["configs"],
        "--tag",
        tag,
        "--output",
        reports_dir,
    ]
    if args.max_prompts_per_category:
        eval_cmd.extend(["--max-prompts-per-category", str(args.max_prompts_per_category)])
    if args.resume:
        eval_cmd.append("--resume")

    if registry.get("protocol") == "deterministic":
        eval_cmd.append("--deterministic")
    else:
        eval_cmd.extend(["--seed", str(registry.get("seed", 0))])
        if registry.get("stable_sampling_seeds", False):
            eval_cmd.append("--stable-sampling-seeds")

    block_scales = registry.get("block_scales", {})
    if block_scales:
        eval_cmd.append("--block-scales")
        eval_cmd.extend(f"{name}={scale}" for name, scale in block_scales.items())

    env = os.environ.copy()
    env.setdefault("BITDPM_FORCE_CPU", "1")
    print("[RegistryEval] Evaluation command:")
    print(shell_join(eval_cmd))
    if not args.dry_run:
        subprocess.run(eval_cmd, check=True, env=env)

    if args.dry_run:
        return

    report = latest_report(tag, reports_dir)
    print(f"[RegistryEval] Latest report: {report}")

    if not args.skip_safety:
        safety_cmd = [
            sys.executable,
            "scripts/analyze_v08_block_safety.py",
            "--report",
            report,
            "--tag",
            tag,
        ]
        mining_cmd = [
            sys.executable,
            "scripts/mine_v08_utility.py",
            "--report",
            report,
            "--tag",
            tag,
        ]
        run_cmd(safety_cmd, dry_run=False)
        run_cmd(mining_cmd, dry_run=False)


def main():
    parser = argparse.ArgumentParser(description="Run BitDPM eval from a block registry")
    parser.add_argument("--registry", default="configs/bitdpm_v10_admitted_pool.json")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--output", default="experiments/reports")
    parser.add_argument("--tag", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--benchmark-set", default="", choices=["", "core", "v08", "v14", "v15", "v1k", "v1k_clean"],
                        help="Override registry benchmark set.")
    parser.add_argument("--max-prompts-per-category", type=int, default=0,
                        help="Optional pilot subset size per category.")
    parser.add_argument("--skip-safety", action="store_true",
                        help="Skip safety/mining post-analysis.")
    parser.add_argument("--resume", action="store_true",
                        help="Enable run_v05 checkpoint/resume for long registry evaluations.")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
