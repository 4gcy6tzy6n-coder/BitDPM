#!/usr/bin/env python3
"""Evaluate prompt-only baselines on BitDPM benchmarks.

This external baseline uses the frozen backbone without parameter blocks. It
compares the original prompt against a prompted variant under the same benchmark
and evaluator, then reports fixes/breaks/net. The goal is to separate gains from
parameter correction from gains obtainable through simple prompt instructions.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitdpm.eval.benchmark import EVAL_PROMPTS, EXPECTED_ANSWERS, compute_accuracy_with_refs
from bitdpm.eval.v08_benchmark import V08_EVAL_PROMPTS, V08_EXPECTED_ANSWERS
from bitdpm.eval.v14_benchmark import V14_EVAL_PROMPTS, V14_EXPECTED_ANSWERS
from bitdpm.eval.v15_benchmark import V15_EVAL_PROMPTS, V15_EXPECTED_ANSWERS
from bitdpm.eval.v1k_benchmark import V1K_EVAL_PROMPTS, V1K_EXPECTED_ANSWERS
from bitdpm.eval.v1k_clean_benchmark import V1K_CLEAN_EVAL_PROMPTS, V1K_CLEAN_EXPECTED_ANSWERS
from bitdpm.models.backbone import BackboneModel


@dataclass
class PromptOnlySummary:
    model: str
    benchmark_set: str
    prompt_policy: str
    total_prompts: int
    baseline: float
    prompted: float
    delta: float
    fixes: int
    breaks: int
    net: int
    max_tokens: int
    deterministic: bool


@dataclass
class PromptOnlyReport:
    summary: PromptOnlySummary
    category_scores: dict[str, dict[str, float]]
    rows: list[dict[str, Any]] = field(default_factory=list)


def get_benchmark_refs(benchmark_set: str) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    if benchmark_set == "core":
        return EVAL_PROMPTS, EXPECTED_ANSWERS
    if benchmark_set == "v08":
        return V08_EVAL_PROMPTS, V08_EXPECTED_ANSWERS
    if benchmark_set == "v14":
        return V14_EVAL_PROMPTS, V14_EXPECTED_ANSWERS
    if benchmark_set == "v15":
        return V15_EVAL_PROMPTS, V15_EXPECTED_ANSWERS
    if benchmark_set == "v1k":
        return V1K_EVAL_PROMPTS, V1K_EXPECTED_ANSWERS
    if benchmark_set == "v1k_clean":
        return V1K_CLEAN_EVAL_PROMPTS, V1K_CLEAN_EXPECTED_ANSWERS
    raise ValueError(f"Unknown benchmark set: {benchmark_set}")


def select_prompts(
    prompts_by_category: dict[str, list[str]],
    max_prompts_per_category: int,
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for category, prompts in prompts_by_category.items():
        use_prompts = prompts[:max_prompts_per_category] if max_prompts_per_category else prompts
        rows.extend((category, prompt) for prompt in use_prompts)
    return rows


def transform_prompt(prompt: str, category: str, policy: str) -> str:
    if policy == "short_answer":
        return f"{prompt}\n\nAnswer with only the final answer. Be concise."
    if policy == "category_aware":
        if any(token in category for token in ["arithmetic", "math", "router_core", "multiplication"]):
            return (
                f"{prompt}\n\nCompute carefully. Return only the final numeric answer, "
                "without explanation."
            )
        if "factual" in category or "commonsense" in category:
            return f"{prompt}\n\nGive the standard short answer only."
        if "chinese" in category:
            return f"{prompt}\n\n请只给出简短答案。"
        if "code" in category:
            return f"{prompt}\n\nUse concise, correct code or explanation."
        return f"{prompt}\n\nAnswer briefly and directly."
    if policy == "math_direct":
        return (
            f"{prompt}\n\nIf this is a math problem, compute step by step silently "
            "and output only the final answer."
        )
    raise ValueError(f"Unknown prompt policy: {policy}")


def aggregate_category(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    totals: dict[str, dict[str, float]] = {}
    counts: dict[str, int] = {}
    for row in rows:
        category = row["category"]
        totals.setdefault(category, {"baseline": 0.0, "prompted": 0.0})
        counts[category] = counts.get(category, 0) + 1
        totals[category]["baseline"] += float(row["baseline_score"])
        totals[category]["prompted"] += float(row["prompted_score"])
    return {
        category: {
            "baseline": values["baseline"] / counts[category],
            "prompted": values["prompted"] / counts[category],
            "delta": (values["prompted"] - values["baseline"]) / counts[category],
        }
        for category, values in totals.items()
    }


def run(args: argparse.Namespace) -> None:
    prompts_by_category, expected_answers = get_benchmark_refs(args.benchmark_set)
    prompts = select_prompts(prompts_by_category, args.max_prompts_per_category)

    if args.dry_run:
        print(f"benchmark={args.benchmark_set} total_prompts={len(prompts)} policy={args.prompt_policy}")
        for category, prompt in prompts[: min(8, len(prompts))]:
            print("---")
            print(f"category={category}")
            print(f"base={prompt}")
            print(f"prompted={transform_prompt(prompt, category, args.prompt_policy)}")
        return

    device = args.device or (
        "cuda" if torch.cuda.is_available() else
        "mps" if torch.backends.mps.is_available() else "cpu"
    )
    backbone = BackboneModel(
        model_name=args.model,
        device=device,
        dtype=torch.float32 if args.float32 else torch.float16,
        source=args.source,
    )

    rows: list[dict[str, Any]] = []
    baseline_total = 0.0
    prompted_total = 0.0
    fixes = 0
    breaks = 0
    threshold = args.correct_threshold

    for idx, (category, prompt) in enumerate(prompts, start=1):
        prompted = transform_prompt(prompt, category, args.prompt_policy)
        print(f"[{idx}/{len(prompts)}] {category}: {prompt[:72]}")

        base_start = time.time()
        baseline_output = backbone.generate(
            prompt,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
            do_sample=not args.deterministic,
        )
        base_elapsed = time.time() - base_start
        base_score = compute_accuracy_with_refs(prompt, baseline_output, category, prompts_by_category, expected_answers)

        prompt_start = time.time()
        prompted_output = backbone.generate(
            prompted,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
            do_sample=not args.deterministic,
        )
        prompt_elapsed = time.time() - prompt_start
        prompted_score = compute_accuracy_with_refs(prompt, prompted_output, category, prompts_by_category, expected_answers)

        base_ok = base_score >= threshold
        prompted_ok = prompted_score >= threshold
        if prompted_ok and not base_ok:
            fixes += 1
        elif base_ok and not prompted_ok:
            breaks += 1

        baseline_total += base_score
        prompted_total += prompted_score
        row = {
            "index": idx - 1,
            "category": category,
            "prompt": prompt,
            "prompted_prompt": prompted,
            "baseline_score": base_score,
            "prompted_score": prompted_score,
            "baseline_time": base_elapsed,
            "prompted_time": prompt_elapsed,
        }
        if args.save_outputs:
            row["baseline_output"] = baseline_output
            row["prompted_output"] = prompted_output
        rows.append(row)
        print(f"  baseline={base_score:.1f} prompted={prompted_score:.1f}")

    n = max(len(rows), 1)
    summary = PromptOnlySummary(
        model=args.model,
        benchmark_set=args.benchmark_set,
        prompt_policy=args.prompt_policy,
        total_prompts=len(rows),
        baseline=baseline_total / n,
        prompted=prompted_total / n,
        delta=(prompted_total - baseline_total) / n,
        fixes=fixes,
        breaks=breaks,
        net=fixes - breaks,
        max_tokens=args.max_tokens,
        deterministic=args.deterministic,
    )
    report = PromptOnlyReport(
        summary=summary,
        category_scores=aggregate_category(rows),
        rows=rows,
    )

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"{args.tag}_{ts}.json"
    md_path = out_dir / f"{args.tag}_{ts}.md"
    json_path.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(make_markdown(report), encoding="utf-8")

    print(
        f"prompted={summary.prompted:.3f} baseline={summary.baseline:.3f} "
        f"delta={summary.delta:+.3f} fixes={fixes} breaks={breaks} net={fixes - breaks}"
    )
    print(f"Saved JSON: {json_path}")
    print(f"Saved Markdown: {md_path}")


def make_markdown(report: PromptOnlyReport) -> str:
    s = report.summary
    lines = [
        "# BitDPM Prompt-Only Baseline",
        "",
        f"- Model: `{s.model}`",
        f"- Benchmark: `{s.benchmark_set}`",
        f"- Prompt policy: `{s.prompt_policy}`",
        f"- N: {s.total_prompts}",
        f"- Baseline: {s.baseline:.3f}",
        f"- Prompted: {s.prompted:.3f}",
        f"- Delta: {s.delta:+.3f}",
        f"- Fixes / breaks / net: {s.fixes}/{s.breaks}/{s.net}",
        "",
        "## Category Scores",
        "",
        "| Category | Baseline | Prompted | Delta |",
        "|---|---:|---:|---:|",
    ]
    for category, scores in sorted(report.category_scores.items()):
        lines.append(
            f"| {category} | {scores['baseline']:.3f} | {scores['prompted']:.3f} | {scores['delta']:+.3f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run prompt-only BitDPM external baseline.")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--device", default="")
    parser.add_argument("--source", default="auto", choices=["auto", "hf", "modelscope"])
    parser.add_argument("--benchmark-set", default="v14", choices=["core", "v08", "v14", "v15", "v1k", "v1k_clean"])
    parser.add_argument("--prompt-policy", default="category_aware", choices=["short_answer", "category_aware", "math_direct"])
    parser.add_argument("--output", default="experiments/reports/prompt_only")
    parser.add_argument("--tag", default="prompt_only")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--deterministic", action="store_true")
    parser.add_argument("--float32", action="store_true")
    parser.add_argument("--correct-threshold", type=float, default=1.0)
    parser.add_argument("--max-prompts-per-category", type=int, default=0)
    parser.add_argument("--save-outputs", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
