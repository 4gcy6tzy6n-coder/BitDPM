#!/usr/bin/env python3
"""Low-bit backbone experiment (Milestone 5).

Simulates INT8/INT4 quantization of the backbone model weights
to compare FP16 vs quantized performance, with and without BitDPM blocks.

Usage:
    python scripts/run_quant_experiment.py
    python scripts/run_quant_experiment.py --model /path/to/model
"""

from __future__ import annotations

import argparse
import copy
import os
import sys
import time

import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitdpm.eval.benchmark import (
    BenchmarkResult,
    format_benchmark_table,
    run_benchmark,
    save_benchmark_results,
)
from bitdpm.eval.latency import measure_generate_latency
from bitdpm.eval.memory import measure_model_memory
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import BlockBank


def apply_simulated_quantization(model, bits: int = 8):
    """Quantize linear layer weights in-place (simulated).

    For each nn.Linear in the model:
    1. Quantize weights to int (INT4 or INT8)
    2. Dequantize back to float
    This simulates the effect of quantization without actual int kernels.
    """
    quantized_layers = 0
    for name, module in model.named_modules():
        if isinstance(module, nn.Linear):
            w = module.weight.data
            orig_dtype = w.dtype
            w_float = w.float()

            if bits == 8:
                # INT8 symmetric quantization
                scale = w_float.abs().max() / 127.0
                if scale > 0:
                    w_q = torch.clamp(torch.round(w_float / scale), -128, 127)
                    w_deq = w_q * scale
                else:
                    w_deq = w_float
            elif bits == 4:
                # INT4 symmetric quantization (NF4-like)
                scale = w_float.abs().max() / 7.0
                if scale > 0:
                    w_q = torch.clamp(torch.round(w_float / scale), -7, 7)
                    w_deq = w_q * scale
                else:
                    w_deq = w_float
            else:
                continue

            module.weight.data = w_deq.to(orig_dtype)
            quantized_layers += 1

    return quantized_layers


def run(args):
    device = args.device or (
        "cuda" if torch.cuda.is_available() else
        "mps" if torch.backends.mps.is_available() else "cpu"
    )
    print(f"[QuantExp] Device: {device}")
    print(f"[QuantExp] Model: {args.model}")
    os.makedirs(args.output, exist_ok=True)

    all_results = []

    # 1. Load backbone (FP16 for baseline)
    print(f"\n{'='*60}")
    print("Loading model...")
    backbone = BackboneModel(
        model_name=args.model,
        device=device,
        dtype=torch.float16,
        source=args.source,
    )

    # 2. Load blocks (if available)
    bank = None
    block_dir = args.load_blocks
    if block_dir and os.path.isdir(block_dir):
        try:
            bank = BlockBank.load_all(block_dir, device=torch.device(device))
            print(f"[QuantExp] Loaded {len(bank)} blocks from {block_dir}")
        except Exception as e:
            print(f"[QuantExp] No blocks found: {e}")

    # 3. Experiment: FP16 baseline
    def gen_fn_template(backbone_ref, blocks=None, scale=0.0):
        """Create a generate function."""
        def gen_fn(p: str) -> str:
            return backbone_ref.generate(p, max_new_tokens=args.max_tokens, temperature=0.1)
        return gen_fn

    # FP16 baseline
    print(f"\n{'='*60}")
    print("EXPERIMENT: FP16 baseline")
    mem_baseline = measure_model_memory(backbone.model, device)
    result_fp16 = run_benchmark(
        gen_fn_template(backbone), verbose=True
    )
    result_fp16.model_name = f"FP16 baseline"
    result_fp16.quant = "FP16"
    result_fp16.num_params = f"{backbone.num_params()/1e9:.1f}B"
    result_fp16.device = device
    result_fp16.peak_memory_mb = mem_baseline.total_model_mb
    all_results.append(result_fp16)

    # 4. Experiment: Simulated INT8
    print(f"\n{'='*60}")
    print("EXPERIMENT: Simulated INT8")
    q_layers = apply_simulated_quantization(backbone.model, bits=8)
    print(f"  Quantized {q_layers} linear layers to INT8")
    mem_int8 = measure_model_memory(backbone.model, device)
    result_int8 = run_benchmark(
        gen_fn_template(backbone), verbose=True
    )
    result_int8.model_name = f"INT8 simulated"
    result_int8.quant = "INT8"
    result_int8.num_params = f"{backbone.num_params()/1e9:.1f}B"
    result_int8.device = device
    result_int8.peak_memory_mb = mem_int8.total_model_mb
    all_results.append(result_int8)

    # 5. Experiment: Simulated INT4
    print(f"\n{'='*60}")
    print("EXPERIMENT: Simulated INT4")
    # Reload model for fresh FP16 weights, then quantize
    backbone2 = BackboneModel(
        model_name=args.model,
        device=device,
        dtype=torch.float16,
        source=args.source,
    )
    q_layers = apply_simulated_quantization(backbone2.model, bits=4)
    print(f"  Quantized {q_layers} linear layers to INT4")
    mem_int4 = measure_model_memory(backbone2.model, device)
    result_int4 = run_benchmark(
        gen_fn_template(backbone2), verbose=True
    )
    result_int4.model_name = f"INT4 simulated"
    result_int4.quant = "INT4"
    result_int4.num_params = f"{backbone2.num_params()/1e9:.1f}B"
    result_int4.device = device
    result_int4.peak_memory_mb = mem_int4.total_model_mb
    all_results.append(result_int4)

    # 6. Summary
    print(f"\n{'='*70}")
    print("QUANTIZATION EXPERIMENT SUMMARY")
    print(f"{'='*70}")
    print(format_benchmark_table(all_results))

    save_path = os.path.join(args.output, "quant_experiment_results.json")
    save_benchmark_results(all_results, save_path)
    print(f"  Results saved: {save_path}")


def main():
    parser = argparse.ArgumentParser(description="Run quantization experiments")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--load-blocks", type=str, default="experiments/outputs/blocks")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--source", type=str, default="auto")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--output", type=str, default="experiments/reports")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
