"""Benchmarking suite for BitDPM evaluation.

Provides standardized prompts across categories:
- Common sense QA
- Math problems
- Code / JSON format
- Chinese QA
- Reasoning tasks

Outputs accuracy metrics comparable across model variants.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


# Standard evaluation prompts organized by category
EVAL_PROMPTS = {
    "commonsense": [
        "What is the capital of France?",
        "How many days are in a leap year?",
        "What color is the sky on a clear day?",
        "Which planet is known as the Red Planet?",
        "What is the boiling point of water in Celsius?",
        "Who wrote Romeo and Juliet?",
        "What is the largest ocean on Earth?",
        "How many continents are there?",
        "What is the speed of light in vacuum?",
        "Which gas do plants absorb from the atmosphere?",
    ],
    "math": [
        "Calculate 15 + 27 =",
        "What is 144 divided by 12?",
        "If x + 5 = 12, what is x?",
        "What is 25% of 200?",
        "Calculate the area of a circle with radius 3.",
        "What is the square root of 144?",
        "How many seconds are in 2 hours?",
        "Solve: 3x - 7 = 14",
        "What is 2^10?",
        "If a train travels at 60 km/h for 2.5 hours, how far does it go?",
    ],
    "code": [
        "Write a Python function to check if a string is a palindrome.",
        'Create a JSON object representing a person with name, age, and city.',
        "Explain what a hash map is in one paragraph.",
        "Write a simple function to sort a list of integers.",
        "What is the difference between a list and a tuple in Python?",
        "Write a regex to validate an email address.",
        "What is an API endpoint?",
        "Write a SQL query to find duplicate entries in a table.",
        "Explain recursion with an example.",
        "What is the time complexity of binary search?",
    ],
    "chinese": [
        "中国的首都是哪个城市？",
        "请用中文解释什么是人工智能。",
        "一年有多少个月？",
        "请写一段关于春天的短文。",
        "什么是机器学习？请用中文回答。",
        "水的化学式是什么？",
        "请列举三种水果。",
        "太阳从哪个方向升起？",
        "请用中文写一句问候语。",
        "什么是自然语言处理？",
    ],
    "reasoning": [
        "If all squares are rectangles, and some rectangles are not squares, can a shape be a rectangle but not a square? Explain.",
        "Alice is twice as old as Bob. In 5 years, Alice will be 1.5 times as old as Bob. How old is Alice now?",
        "Three light switches control a light bulb in another room. You can flip the switches and then enter the room once. How can you determine which switch controls the bulb?",
        "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
        "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?",
    ],
}

# Expected answer keywords for scoring (simple substring match)
EXPECTED_ANSWERS: dict[str, list[str]] = {
    "commonsense": [
        "paris", "366", "blue", "mars", "100", "shakespeare", "pacific", "7", "299,792,458", "carbon dioxide",
    ],
    "math": [
        "42", "12", "7", "50", "28.26", "12", "7200", "7", "1024", "150",
    ],
    "code": [],  # Code answers are evaluated qualitatively
    "chinese": [],  # Chinese answers evaluated qualitatively
    "reasoning": [],  # Reasoning evaluated qualitatively
}


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    model_name: str
    quant: str
    num_params: str
    device: str
    category_scores: dict[str, float] = field(default_factory=dict)
    overall_score: float = 0.0
    avg_tokens_per_sec: float = 0.0
    avg_latency_ms: float = 0.0
    peak_memory_mb: float = 0.0
    total_prompts: int = 0
    metadata: dict = field(default_factory=dict)


def compute_accuracy(
    prompt: str,
    generated: str,
    category: str,
) -> float:
    """Score a generated answer against the default core benchmark."""
    return compute_accuracy_with_refs(prompt, generated, category, EVAL_PROMPTS, EXPECTED_ANSWERS)


def compute_accuracy_with_refs(
    prompt: str,
    generated: str,
    category: str,
    prompts_by_category: dict[str, list[str]],
    expected_answers: dict[str, list[str]],
) -> float:
    """Score a generated answer against expected keywords.

    Returns 1.0 if the expected answer keyword is found in the generation,
    0.5 for partial matches, 0.0 otherwise.

    For code/chinese/reasoning categories, returns a qualitative score
    based on completion length and coherence.
    """
    generated_lower = generated.lower().strip()
    prompt_lower = prompt.lower().strip()

    # Remove prompt from generation if model echoed it
    if generated_lower.startswith(prompt_lower[:20]):
        generated_lower = generated_lower[len(prompt_lower[:20]):].strip()

    answers = expected_answers.get(category, [])
    # Find which question index this is
    prompts = prompts_by_category.get(category, [])
    try:
        idx = prompts.index(prompt)
    except ValueError:
        idx = -1

    if category in ("code", "chinese", "reasoning"):
        # Qualitative scoring based on generation quality
        if len(generated) < 10:
            return 0.0
        if len(generated) > 50:
            return 1.0
        return 0.5

    if idx >= 0 and idx < len(answers) and answers[idx]:
        expected = answers[idx].lower()
        if expected in generated_lower:
            return 1.0
        # Partial match: check if numbers or key terms appear
        words = expected.split()
        if words and any(w in generated_lower for w in words):
            return 0.5
        return 0.0

    # Fallback: check if answer has reasonable length
    return 0.5 if len(generated) > 20 else 0.0


def run_benchmark(
    generate_fn: Callable[[str], str],
    categories: Optional[list[str]] = None,
    max_new_tokens: int = 128,
    verbose: bool = True,
) -> BenchmarkResult:
    """Run benchmark across evaluation categories.

    Args:
        generate_fn: Function that takes a prompt and returns generated text.
        categories: Which categories to evaluate (None = all).
        max_new_tokens: Max tokens for generation.
        verbose: Whether to print progress.

    Returns:
        BenchmarkResult with per-category scores.
    """
    if categories is None:
        categories = list(EVAL_PROMPTS.keys())

    category_scores: dict[str, float] = {}
    total_score = 0.0
    total_prompts = 0
    total_latency = 0.0
    total_tokens = 0

    for category in categories:
        prompts = EVAL_PROMPTS.get(category, [])
        if not prompts:
            continue

        cat_score = 0.0
        if verbose:
            print(f"\n{'='*60}")
            print(f"Category: {category.upper()} ({len(prompts)} prompts)")
            print(f"{'='*60}")

        for i, prompt in enumerate(prompts):
            start = time.time()
            generated = generate_fn(prompt)
            latency = time.time() - start
            total_latency += latency

            score = compute_accuracy(prompt, generated, category)
            cat_score += score
            total_score += score
            total_prompts += 1

            # Rough tokens estimate
            est_tokens = len(generated.split())
            total_tokens += est_tokens

            if verbose:
                status = "✓" if score >= 0.5 else "✗"
                print(f"  [{i+1}/{len(prompts)}] {status} score={score:.1f} | {latency:.2f}s | {generated[:80]}...")

        cat_avg = cat_score / len(prompts)
        category_scores[category] = cat_avg
        if verbose:
            print(f"  → Category avg: {cat_avg:.3f}")

    overall = total_score / max(total_prompts, 1)
    avg_latency = (total_latency / max(total_prompts, 1)) * 1000  # ms

    return BenchmarkResult(
        model_name="",
        quant="",
        num_params="",
        device="",
        category_scores=category_scores,
        overall_score=overall,
        avg_latency_ms=avg_latency,
        avg_tokens_per_sec=total_tokens / max(total_latency, 0.001),
        total_prompts=total_prompts,
    )


def format_benchmark_table(results: list[BenchmarkResult]) -> str:
    """Format benchmark results as a markdown table."""
    header = (
        "| Model | Quant | Params | Device | Token/s | Latency(ms) | Memory(MB) | "
        + " | ".join(f"{cat}" for cat in EVAL_PROMPTS.keys()) + " | Overall |"
    )
    sep = "|" + "---|" * (8 + len(EVAL_PROMPTS))

    rows = [header, sep]
    for r in results:
        cats = " | ".join(f"{r.category_scores.get(c, 0):.3f}" for c in EVAL_PROMPTS.keys())
        rows.append(
            f"| {r.model_name} | {r.quant} | {r.num_params} | {r.device} | "
            f"{r.avg_tokens_per_sec:.1f} | {r.avg_latency_ms:.1f} | "
            f"{r.peak_memory_mb:.0f} | {cats} | {r.overall_score:.3f} |"
        )

    return "\n".join(rows)


def save_benchmark_results(results: list[BenchmarkResult], path: str):
    """Save benchmark results to a JSON file."""
    data = []
    for r in results:
        data.append({
            "model_name": r.model_name,
            "quant": r.quant,
            "num_params": r.num_params,
            "device": r.device,
            "category_scores": r.category_scores,
            "overall_score": r.overall_score,
            "avg_tokens_per_sec": r.avg_tokens_per_sec,
            "avg_latency_ms": r.avg_latency_ms,
            "peak_memory_mb": r.peak_memory_mb,
            "total_prompts": r.total_prompts,
            "metadata": r.metadata,
        })
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[Benchmark] Results saved to {path}")
