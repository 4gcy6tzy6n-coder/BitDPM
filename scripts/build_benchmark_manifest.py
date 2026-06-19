#!/usr/bin/env python3
"""Build an audit manifest for BitDPM benchmark prompt sets.

This is a static benchmark-quality report. It does not run models. It records
category balance, answer coverage, duplicate prompts, cross-benchmark overlap,
and a stable prompt-set fingerprint so paper runs can cite the exact validation
surface they used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bitdpm.eval.benchmark import EVAL_PROMPTS, EXPECTED_ANSWERS
from bitdpm.eval.v08_benchmark import V08_EVAL_PROMPTS, V08_EXPECTED_ANSWERS
from bitdpm.eval.v14_benchmark import V14_EVAL_PROMPTS, V14_EXPECTED_ANSWERS
from bitdpm.eval.v15_benchmark import V15_EVAL_PROMPTS, V15_EXPECTED_ANSWERS
from bitdpm.eval.v1k_benchmark import V1K_EVAL_PROMPTS, V1K_EXPECTED_ANSWERS
from bitdpm.eval.v1k_clean_benchmark import V1K_CLEAN_EVAL_PROMPTS, V1K_CLEAN_EXPECTED_ANSWERS


BENCHMARKS = {
    "core": (EVAL_PROMPTS, EXPECTED_ANSWERS),
    "v08": (V08_EVAL_PROMPTS, V08_EXPECTED_ANSWERS),
    "v14": (V14_EVAL_PROMPTS, V14_EXPECTED_ANSWERS),
    "v15": (V15_EVAL_PROMPTS, V15_EXPECTED_ANSWERS),
    "v1k": (V1K_EVAL_PROMPTS, V1K_EXPECTED_ANSWERS),
    "v1k_clean": (V1K_CLEAN_EVAL_PROMPTS, V1K_CLEAN_EXPECTED_ANSWERS),
}


@dataclass
class CategoryAudit:
    prompts: int
    expected_answers: int
    answer_coverage: float
    duplicate_prompts: int
    avg_prompt_chars: float
    max_prompt_chars: int


@dataclass
class BenchmarkAudit:
    benchmark: str
    total_prompts: int
    categories: dict[str, CategoryAudit]
    duplicate_prompts: int
    exact_fingerprint_sha256: str
    normalized_fingerprint_sha256: str


def normalize_prompt(prompt: str) -> str:
    return re.sub(r"\s+", " ", prompt.strip().lower())


def fingerprint(items: list[str]) -> str:
    payload = "\n".join(items).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def flatten_prompts(prompts_by_category: dict[str, list[str]], normalized: bool = False) -> list[str]:
    rows: list[str] = []
    for category in sorted(prompts_by_category):
        for prompt in prompts_by_category[category]:
            text = normalize_prompt(prompt) if normalized else prompt
            rows.append(f"{category}\t{text}")
    return rows


def audit_benchmark(
    benchmark: str,
    prompts_by_category: dict[str, list[str]],
    expected_answers: dict[str, list[str]],
) -> BenchmarkAudit:
    categories: dict[str, CategoryAudit] = {}
    all_prompts: list[str] = []
    for category, prompts in prompts_by_category.items():
        answers = expected_answers.get(category, [])
        duplicates = len(prompts) - len(set(normalize_prompt(prompt) for prompt in prompts))
        lengths = [len(prompt) for prompt in prompts]
        categories[category] = CategoryAudit(
            prompts=len(prompts),
            expected_answers=len(answers),
            answer_coverage=(len(answers) / len(prompts)) if prompts else 0.0,
            duplicate_prompts=duplicates,
            avg_prompt_chars=(sum(lengths) / len(lengths)) if lengths else 0.0,
            max_prompt_chars=max(lengths) if lengths else 0,
        )
        all_prompts.extend(prompts)

    normalized_prompts = [normalize_prompt(prompt) for prompt in all_prompts]
    return BenchmarkAudit(
        benchmark=benchmark,
        total_prompts=len(all_prompts),
        categories=categories,
        duplicate_prompts=len(normalized_prompts) - len(set(normalized_prompts)),
        exact_fingerprint_sha256=fingerprint(flatten_prompts(prompts_by_category, normalized=False)),
        normalized_fingerprint_sha256=fingerprint(flatten_prompts(prompts_by_category, normalized=True)),
    )


def overlap_matrix() -> dict[str, dict[str, int]]:
    normalized_sets = {
        name: {normalize_prompt(prompt) for prompts in prompts_by_category.values() for prompt in prompts}
        for name, (prompts_by_category, _) in BENCHMARKS.items()
    }
    matrix: dict[str, dict[str, int]] = {}
    for left, left_set in normalized_sets.items():
        matrix[left] = {}
        for right, right_set in normalized_sets.items():
            matrix[left][right] = len(left_set & right_set)
    return matrix


def make_payload() -> dict[str, Any]:
    audits = {
        name: asdict(audit_benchmark(name, prompts, answers))
        for name, (prompts, answers) in BENCHMARKS.items()
    }
    return {
        "benchmarks": audits,
        "overlap_matrix": overlap_matrix(),
        "interpretation": {
            "fingerprints": "SHA256 over category-tab-prompt rows sorted by category.",
            "answer_coverage": "0.0 for qualitative categories that use heuristic scoring.",
            "overlap": "Exact normalized prompt overlap; template-level similarity is not counted.",
        },
    }


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def make_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# BitDPM Benchmark Manifest",
        "",
        "This manifest audits the static benchmark prompt sets used by current",
        "BitDPM experiments. It is generated without model inference.",
        "",
        "## Benchmark Summary",
        "",
        "| Benchmark | N | Categories | Duplicate Prompts | Normalized SHA256 |",
        "|---|---:|---:|---:|---|",
    ]
    for name, audit in payload["benchmarks"].items():
        lines.append(
            f"| {name} | {audit['total_prompts']} | {len(audit['categories'])} | "
            f"{audit['duplicate_prompts']} | `{audit['normalized_fingerprint_sha256']}` |"
        )

    lines.extend(
        [
            "",
            "## Category Detail",
            "",
            "| Benchmark | Category | Prompts | Expected Answers | Answer Coverage | Duplicates | Avg Chars | Max Chars |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for name, audit in payload["benchmarks"].items():
        for category, detail in audit["categories"].items():
            lines.append(
                f"| {name} | {category} | {detail['prompts']} | {detail['expected_answers']} | "
                f"{fmt(detail['answer_coverage'])} | {detail['duplicate_prompts']} | "
                f"{fmt(detail['avg_prompt_chars'])} | {detail['max_prompt_chars']} |"
            )

    benchmarks = list(payload["benchmarks"].keys())
    lines.extend(["", "## Exact Normalized Prompt Overlap", ""])
    lines.append("| Benchmark | " + " | ".join(benchmarks) + " |")
    lines.append("|---|" + "|".join("---:" for _ in benchmarks) + "|")
    for left in benchmarks:
        cells = [str(payload["overlap_matrix"][left][right]) for right in benchmarks]
        lines.append(f"| {left} | " + " | ".join(cells) + " |")

    lines.extend(
        [
            "",
            "## Paper Use",
            "",
            "- Cite the normalized SHA256 fingerprint for any benchmark used as a fixed validation set.",
            "- Treat a 1k benchmark as held-out only if exact normalized prompt overlap with earlier validation sets is zero.",
            "- Qualitative categories with `0.000` answer coverage use the shared heuristic scorer; report that limitation.",
            "- Exact prompt overlap is reported here; semantic/template similarity should be discussed separately if needed.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build BitDPM benchmark manifest.")
    parser.add_argument("--out", type=Path, default=Path("experiments/reports/bitdpm_benchmark_manifest.md"))
    parser.add_argument("--json-out", type=Path, default=Path("experiments/reports/bitdpm_benchmark_manifest.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = make_payload()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(make_markdown(payload), encoding="utf-8")
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.json_out}")


if __name__ == "__main__":
    main()
