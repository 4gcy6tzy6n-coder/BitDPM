"""Latency and throughput measurement utilities.

Measures:
- Model load time
- First-token latency (TTFT)
- Generation throughput (token/s)
- Per-token latency
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

import torch


@dataclass
class LatencyMetrics:
    """Latency and throughput measurements."""
    model_load_time_s: float = 0.0
    first_token_latency_ms: float = 0.0
    tokens_per_second: float = 0.0
    avg_tokens_per_second: float = 0.0
    per_token_latency_ms: float = 0.0
    total_generation_time_s: float = 0.0
    num_tokens_generated: int = 0
    num_runs: int = 1
    warmup_runs: int = 0
    metadata: dict = field(default_factory=dict)


def measure_generate_latency(
    generate_fn: Callable[..., str],
    prompt: str = "What is the capital of France?",
    max_new_tokens: int = 128,
    num_runs: int = 3,
    warmup_runs: int = 1,
    **kwargs,
) -> LatencyMetrics:
    """Measure generation latency and throughput.

    Args:
        generate_fn: Function that takes prompt and max_new_tokens and returns text.
        prompt: Test prompt.
        max_new_tokens: Max tokens to generate.
        num_runs: Number of measured runs.
        warmup_runs: Number of warmup runs (not measured).
        **kwargs: Additional kwargs passed to generate_fn.

    Returns:
        LatencyMetrics with averaged measurements.
    """
    # Warmup
    for _ in range(warmup_runs):
        _ = generate_fn(prompt, max_new_tokens=max_new_tokens, **kwargs)

    # Measured runs
    total_time = 0.0
    total_tokens = 0
    first_token_times: list[float] = []

    for i in range(num_runs):
        start = time.time()
        generated = generate_fn(prompt, max_new_tokens=max_new_tokens, **kwargs)
        elapsed = time.time() - start

        # Estimate token count (rough: by space-split words)
        num_tokens = len(generated.split())
        if num_tokens == 0:
            num_tokens = 1

        total_time += elapsed
        total_tokens += num_tokens

    avg_time = total_time / num_runs
    avg_tokens = total_tokens / num_runs

    return LatencyMetrics(
        tokens_per_second=avg_tokens / max(avg_time, 0.001),
        avg_tokens_per_second=avg_tokens / max(avg_time, 0.001),
        per_token_latency_ms=(avg_time / max(avg_tokens, 1)) * 1000,
        total_generation_time_s=avg_time,
        num_tokens_generated=int(avg_tokens),
        num_runs=num_runs,
        warmup_runs=warmup_runs,
    )


def measure_model_load_time(
    load_fn: Callable[[], object],
    num_runs: int = 1,
) -> float:
    """Measure model loading time in seconds."""
    start = time.time()
    _ = load_fn()
    elapsed = time.time() - start
    return elapsed


def measure_generate_with_trace(
    model,
    tokenizer,
    prompt: str = "What is the capital of France?",
    max_new_tokens: int = 64,
    device: str = "cpu",
) -> dict:
    """Detailed per-token timing for a single generation.

    Returns timing breakdown for each generated token.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    input_len = inputs.input_ids.shape[1]

    # Prefill
    prefill_start = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            output_attentions=False,
            output_hidden_states=False,
            return_dict_infer=True,
        )
    prefill_time = time.time() - prefill_start

    generated_ids = outputs[0][input_len:] if isinstance(outputs, torch.Tensor) else outputs[0][input_len:]
    gen_tokens = len(generated_ids)
    total_time = time.time() - prefill_start

    return {
        "input_length": input_len,
        "generated_tokens": gen_tokens,
        "prefill_time_s": prefill_time,
        "total_generation_time_s": total_time,
        "tokens_per_second": gen_tokens / max(total_time, 0.001),
        "time_per_token_ms": (total_time / max(gen_tokens, 1)) * 1000,
    }


def format_latency_table(results: list[tuple[str, str, str, LatencyMetrics]]) -> str:
    """Format latency results as a markdown table.

    Each entry: (model_name, quant, device, metrics)
    """
    header = "| Model | Quant | Device | Token/s | Per-Token(ms) | Total(s) | Tokens | Runs |"
    sep = "|" + "---|" * 8
    rows = [header, sep]
    for name, quant, device, m in results:
        rows.append(
            f"| {name} | {quant} | {device} | {m.avg_tokens_per_second:.1f} | "
            f"{m.per_token_latency_ms:.2f} | {m.total_generation_time_s:.2f} | "
            f"{m.num_tokens_generated} | {m.num_runs} |"
        )
    return "\n".join(rows)
