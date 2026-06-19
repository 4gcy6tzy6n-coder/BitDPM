#!/usr/bin/env python3
"""Build an AAAI baseline/gap table from saved BitDPM report JSON.

This is report-only. It does not run model inference. It extracts baselines
that can be computed from saved per-sample block-pool scores and explicitly
marks external baselines that still require new runs.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


DEFAULT_REPORTS = [
    ("v14 full current pool", Path("experiments/reports/v14_full_v11_admitted_20260608_093845.json")),
    ("v15 targeted current pool", Path("experiments/reports/v15_router_validation_v11_admitted_20260608_113945.json")),
    ("v08 current pool", Path("experiments/reports/v11_merged_candidates_stable_sampling_LATEST.json")),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def best_fixed(data: dict[str, Any]) -> tuple[str, float]:
    baseline = float(data["config_results"]["baseline"]["overall"])
    best_name = "baseline"
    best_score = baseline
    for name, row in data["config_results"].items():
        if name in {"baseline", "always_all"}:
            continue
        score = float(row["overall"])
        if score > best_score:
            best_name = name
            best_score = score
    return best_name, best_score


def coverage(data: dict[str, Any]) -> int:
    selection = data.get("selection_frequency", {})
    return sum(int(count) for name, count in selection.items() if name != "baseline")


def fix_break_net(
    baseline_scores: list[float],
    candidate_scores: list[float],
    threshold: float,
) -> tuple[int, int, int]:
    fixes = 0
    breaks = 0
    for base, cand in zip(baseline_scores, candidate_scores):
        base_ok = base >= threshold
        cand_ok = cand >= threshold
        if cand_ok and not base_ok:
            fixes += 1
        elif base_ok and not cand_ok:
            breaks += 1
    return fixes, breaks, fixes - breaks


def random_router(
    data: dict[str, Any],
    seeds: int,
    threshold: float,
    include_baseline: bool,
    include_always_all: bool,
) -> dict[str, Any]:
    rows = data.get("per_sample", [])
    if not rows:
        return {
            "mean": 0.0,
            "std": 0.0,
            "fixes_mean": 0.0,
            "breaks_mean": 0.0,
            "net_mean": 0.0,
            "choices": [],
        }

    score_keys = list(rows[0]["scores"])
    choices = [
        key for key in score_keys
        if (include_baseline or key != "baseline")
        and (include_always_all or key != "always_all")
    ]
    if not choices:
        raise ValueError("Random router has no candidate configs.")

    baseline_scores = [float(row["scores"]["baseline"]) for row in rows]
    totals: list[float] = []
    fixes_values: list[int] = []
    breaks_values: list[int] = []
    net_values: list[int] = []

    for seed in range(seeds):
        rng = random.Random(seed)
        sampled_scores = [float(row["scores"][rng.choice(choices)]) for row in rows]
        totals.append(mean(sampled_scores))
        fixes, breaks, net = fix_break_net(baseline_scores, sampled_scores, threshold)
        fixes_values.append(fixes)
        breaks_values.append(breaks)
        net_values.append(net)

    return {
        "mean": mean(totals),
        "std": pstdev(totals) if len(totals) > 1 else 0.0,
        "fixes_mean": mean(fixes_values),
        "breaks_mean": mean(breaks_values),
        "net_mean": mean(net_values),
        "choices": choices,
    }


def report_summary(label: str, path: Path, data: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    best_name, best_score = best_fixed(data)
    rand = random_router(
        data,
        seeds=args.random_seeds,
        threshold=args.correct_threshold,
        include_baseline=args.random_include_baseline,
        include_always_all=args.random_include_always_all,
    )
    return {
        "label": label,
        "path": str(path),
        "benchmark": data.get("benchmark_set", ""),
        "n": int(data.get("total_prompts", len(data.get("per_sample", [])))),
        "baseline": float(data["config_results"]["baseline"]["overall"]),
        "best_fixed": best_score,
        "best_fixed_config": best_name,
        "oracle": float(data["oracle"]["overall"]),
        "coverage": coverage(data),
        "always_all": float(data["config_results"].get("always_all", {}).get("overall", 0.0)),
        "random_router": rand,
        "prompt_only": latest_prompt_only(data.get("benchmark_set", ""), args.prompt_only_dir),
        "lora": latest_lora(data.get("benchmark_set", ""), args.lora_dir),
    }


def latest_prompt_only(benchmark_set: str, prompt_only_dir: Path) -> dict[str, Any] | None:
    if not benchmark_set or not prompt_only_dir.exists():
        return None
    matches = sorted(
        prompt_only_dir.glob(f"prompt_only_*_{benchmark_set}_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        return None
    path = matches[0]
    data = load_json(path)
    summary = data.get("summary", {})
    return {
        "path": str(path),
        "policy": summary.get("prompt_policy"),
        "score": summary.get("prompted"),
        "baseline": summary.get("baseline"),
        "delta": summary.get("delta"),
        "fixes": summary.get("fixes"),
        "breaks": summary.get("breaks"),
        "net": summary.get("net"),
        "n": summary.get("total_prompts"),
    }


def latest_lora(benchmark_set: str, lora_dir: Path) -> dict[str, Any] | None:
    if not benchmark_set or not lora_dir.exists():
        return None
    matches = sorted(
        lora_dir.glob(f"lora_*_{benchmark_set}_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        return None
    path = matches[0]
    data = load_json(path)
    summary = data.get("summary", {})
    return {
        "path": str(path),
        "score": summary.get("lora"),
        "baseline": summary.get("baseline"),
        "delta": summary.get("delta"),
        "fixes": summary.get("fixes"),
        "breaks": summary.get("breaks"),
        "net": summary.get("net"),
        "n": summary.get("total_prompts"),
        "rank": summary.get("rank"),
        "epochs": summary.get("epochs"),
    }


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def make_markdown(rows: list[dict[str, Any]], args: argparse.Namespace) -> str:
    lines = [
        "# BitDPM AAAI Baseline and Gap Table",
        "",
        "This report is generated from saved block-pool JSON files. It includes",
        "baselines computable without new model inference and marks external",
        "baselines that still require new experiments.",
        "",
        "## Computable Baselines",
        "",
        f"- Random router seeds: {args.random_seeds}",
        f"- Random candidates include baseline: `{args.random_include_baseline}`",
        f"- Random candidates include Always-All: `{args.random_include_always_all}`",
        "",
        "| Setting | Benchmark | N | Frozen Backbone | Best Fixed | Best Fixed Config | Oracle | Coverage | Always-All | Random Router Mean | Random Std | Random Fixes | Random Breaks | Random Net | Prompt-Only | Prompt Net | LoRA | LoRA Net |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        rand = row["random_router"]
        prompt = row.get("prompt_only")
        if prompt:
            prompt_score = fmt(prompt.get("score"))
            prompt_net = fmt(prompt.get("net"))
        else:
            prompt_score = "pending"
            prompt_net = "pending"
        lora = row.get("lora")
        if lora:
            lora_score = fmt(lora.get("score"))
            lora_net = fmt(lora.get("net"))
        else:
            lora_score = "pending"
            lora_net = "pending"
        lines.append(
            f"| {row['label']} | {row['benchmark']} | {row['n']} | "
            f"{fmt(row['baseline'])} | {fmt(row['best_fixed'])} | `{row['best_fixed_config']}` | "
            f"{fmt(row['oracle'])} | {row['coverage']}/{row['n']} | {fmt(row['always_all'])} | "
            f"{fmt(rand['mean'])} | {fmt(rand['std'])} | {fmt(rand['fixes_mean'])} | "
            f"{fmt(rand['breaks_mean'])} | {fmt(rand['net_mean'])} | "
            f"{prompt_score} | {prompt_net} | {lora_score} | {lora_net} |"
        )

    prompt_rows = [row for row in rows if row.get("prompt_only")]
    lines.extend(["", "## Prompt-Only Baselines", ""])
    if prompt_rows:
        lines.extend(
            [
                "| Setting | Benchmark | Policy | Source | Prompted | Baseline | Delta | Fixes | Breaks | Net |",
                "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in prompt_rows:
            prompt = row["prompt_only"]
            lines.append(
                f"| {row['label']} | {row['benchmark']} | `{prompt.get('policy')}` | "
                f"`{prompt.get('path')}` | {fmt(prompt.get('score'))} | {fmt(prompt.get('baseline'))} | "
                f"{fmt(prompt.get('delta'))} | {fmt(prompt.get('fixes'))} | "
                f"{fmt(prompt.get('breaks'))} | {fmt(prompt.get('net'))} |"
            )
    else:
        lines.extend(
            [
                "No prompt-only result JSON files found yet.",
                "",
                "Run:",
                "",
                "```bash",
                "bash experiments/reports/external_baseline_commands.sh",
                "```",
            ]
        )

    lora_rows = [row for row in rows if row.get("lora")]
    lines.extend(["", "## Standard LoRA Baselines", ""])
    if lora_rows:
        lines.extend(
            [
                "| Setting | Benchmark | Rank | Epochs | Source | LoRA | Baseline | Delta | Fixes | Breaks | Net |",
                "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in lora_rows:
            lora = row["lora"]
            lines.append(
                f"| {row['label']} | {row['benchmark']} | {fmt(lora.get('rank'))} | "
                f"{fmt(lora.get('epochs'))} | `{lora.get('path')}` | {fmt(lora.get('score'))} | "
                f"{fmt(lora.get('baseline'))} | {fmt(lora.get('delta'))} | "
                f"{fmt(lora.get('fixes'))} | {fmt(lora.get('breaks'))} | {fmt(lora.get('net'))} |"
            )
    else:
        lines.extend(
            [
                "No LoRA baseline result JSON files found yet.",
                "",
                "Run after installing PEFT:",
                "",
                "```bash",
                "pip install -e '.[peft]'",
                "bash experiments/reports/lora_baseline_commands.sh",
                "```",
            ]
        )

    lines.extend(
        [
            "",
            "## Missing External Baselines",
            "",
            "| Baseline | Status | Required Evidence |",
            "|---|---|---|",
            "| Standard LoRA adapter | runnable pending | Install `.[peft]` and run `experiments/reports/lora_baseline_commands.sh`; this table will auto-ingest latest LoRA JSON outputs. |",
            "| Prompt-only rules | runnable pending | Run `experiments/reports/external_baseline_commands.sh`; this table will auto-ingest the latest prompt-only JSON outputs. |",
            "| Best fixed adapter/block | partially covered | Best fixed block is computed from current reports; a separately trained always-on LoRA adapter is still missing. |",
            "| Random router | covered from saved reports | This report simulates random selection from existing per-sample block scores. |",
            "| Frozen backbone | covered from saved reports | Baseline row in block-pool reports. |",
            "| Oracle upper bound | covered from saved reports | Per-sample best config from block-pool reports. |",
            "",
            "## Interpretation",
            "",
            "- The random router is a routing negative control, not a deployment strategy.",
            "- Always-All remains a parameter-interference negative control.",
            "- Prompt-only has a runnable evaluation path; completed outputs are auto-ingested when present.",
            "- LoRA has a runnable PEFT-based evaluation path; completed outputs are auto-ingested when present.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build BitDPM AAAI baseline/gap table.")
    parser.add_argument("--out", type=Path, default=Path("experiments/reports/bitdpm_aaai_baseline_gap_table.md"))
    parser.add_argument("--json-out", type=Path, default=Path("experiments/reports/bitdpm_aaai_baseline_gap_table.json"))
    parser.add_argument("--random-seeds", type=int, default=200)
    parser.add_argument("--correct-threshold", type=float, default=1.0)
    parser.add_argument("--random-include-baseline", action="store_true")
    parser.add_argument("--random-include-always-all", action="store_true")
    parser.add_argument("--prompt-only-dir", type=Path, default=Path("experiments/reports/prompt_only"))
    parser.add_argument("--lora-dir", type=Path, default=Path("experiments/reports/lora_baseline"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = []
    for label, path in DEFAULT_REPORTS:
        if path.exists():
            rows.append(report_summary(label, path, load_json(path), args))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(make_markdown(rows, args), encoding="utf-8")
    args.json_out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.json_out}")


if __name__ == "__main__":
    main()
