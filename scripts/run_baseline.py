#!/usr/bin/env python3
"""Run baseline evaluation of a backbone model.

Usage:
    python scripts/run_baseline.py --model Qwen/Qwen2.5-0.5B-Instruct
    python scripts/run_baseline.py --model Qwen/Qwen2.5-1.5B-Instruct --4bit
    python scripts/run_baseline.py --model Qwen/Qwen2.5-0.5B-Instruct --benchmark
"""

from __future__ import annotations

import argparse
import time

import torch

from bitdpm.eval.benchmark import (
    BenchmarkResult,
    EVAL_PROMPTS,
    format_benchmark_table,
    run_benchmark,
    save_benchmark_results,
)
from bitdpm.eval.latency import measure_generate_latency, measure_model_load_time
from bitdpm.eval.memory import get_device_info, measure_model_memory
from bitdpm.models.backbone import BackboneModel


def run(args):
    device = args.device or ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[Baseline] Device: {device}")
    print(f"[Baseline] Model: {args.model}")

    # Load model with timing
    load_start = time.time()
    model = BackboneModel(
        model_name=args.model,
        device=device,
        dtype=torch.float16 if not args.float32 else torch.float32,
        load_in_4bit=args.fourbit,
        load_in_8bit=args.eightbit,
        source=args.source,
    )
    load_time = time.time() - load_start
    print(f"[Baseline] Load time: {load_time:.2f}s")

    # Device info
    dev_info = get_device_info(device)
    print(f"[Baseline] Device info: {dev_info}")

    # Memory
    mem = measure_model_memory(model.model, device)
    print(f"[Baseline] Model memory: {mem.total_model_mb:.0f} MB (params: {mem.model_params_mb:.0f} MB)")

    # Interactive generation test
    if args.interactive:
        print(f"\n{'='*60}")
        print("Interactive mode — type prompts (or 'quit')")
        print(f"{'='*60}")
        while True:
            prompt = input("\nPrompt: ").strip()
            if prompt.lower() in ("quit", "exit", "q"):
                break
            start = time.time()
            output = model.generate(prompt, max_new_tokens=args.max_tokens, temperature=args.temperature)
            elapsed = time.time() - start
            tok_s = len(output.split()) / max(elapsed, 0.001)
            print(f"Response: {output}")
            print(f"[{elapsed:.2f}s | {tok_s:.1f} tok/s]")

    # Latency benchmark
    if args.latency:
        print(f"\n{'='*60}")
        print("Latency Benchmark")
        print(f"{'='*60}")
        metrics = measure_generate_latency(
            model.generate,
            prompt="What is the capital of France?",
            max_new_tokens=args.max_tokens,
            num_runs=args.runs,
            warmup_runs=args.warmup,
        )
        print(f"  Token/s:     {metrics.avg_tokens_per_second:.1f}")
        print(f"  Per-token:   {metrics.per_token_latency_ms:.1f} ms")
        print(f"  Generation:  {metrics.total_generation_time_s:.2f}s for {metrics.num_tokens_generated} tokens")
        print(f"  Runs:        {metrics.num_runs} (+ {metrics.warmup_runs} warmup)")

    # Full benchmark
    if args.benchmark:
        print(f"\n{'='*60}")
        print("Full Benchmark (all categories)")
        print(f"{'='*60}")

        def gen_fn(prompt: str) -> str:
            return model.generate(prompt, max_new_tokens=args.max_tokens, temperature=0.1)

        result = run_benchmark(gen_fn, verbose=True)
        result.model_name = args.model.split("/")[-1]
        result.quant = "INT4" if args.fourbit else "INT8" if args.eightbit else "FP16" if not args.float32 else "FP32"
        result.num_params = f"{model.num_params()/1e9:.1f}B"
        result.device = device
        result.peak_memory_mb = mem.peak_allocated_mb or mem.total_model_mb

        table = format_benchmark_table([result])
        print(f"\n{table}")

        # Save results
        if args.output:
            save_benchmark_results([result], args.output)

    print(f"\n[Baseline] Done.")


def main():
    parser = argparse.ArgumentParser(description="Run baseline model evaluation")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct",
                        help="HuggingFace model name (default: Qwen/Qwen2.5-0.5B-Instruct)")
    parser.add_argument("--device", type=str, default="",
                        help="Device: cpu, cuda, mps (auto-detect if empty)")
    parser.add_argument("--4bit", action="store_true", dest="fourbit",
                        help="Load in INT4 (requires bitsandbytes)")
    parser.add_argument("--8bit", action="store_true", dest="eightbit",
                        help="Load in INT8 (requires bitsandbytes)")
    parser.add_argument("--float32", action="store_true",
                        help="Load in FP32 instead of FP16")
    parser.add_argument("--max-tokens", type=int, default=128,
                        help="Max new tokens for generation (default: 128)")
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="Generation temperature (default: 0.7)")
    parser.add_argument("--interactive", action="store_true",
                        help="Interactive prompt mode")
    parser.add_argument("--latency", action="store_true",
                        help="Run latency benchmark")
    parser.add_argument("--benchmark", action="store_true",
                        help="Run full accuracy benchmark")
    parser.add_argument("--runs", type=int, default=3,
                        help="Number of runs for latency measurement (default: 3)")
    parser.add_argument("--warmup", type=int, default=1,
                        help="Warmup runs (default: 1)")
    parser.add_argument("--output", type=str, default="",
                        help="Save benchmark results to file")
    parser.add_argument("--source", type=str, default="auto",
                        choices=["auto", "hf", "modelscope"],
                        help="Model download source: hf, modelscope, or auto (default: auto)")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
