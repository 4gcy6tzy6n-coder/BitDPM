#!/usr/bin/env python3
"""Run all evaluations and generate a comparison report.

Tests across:
- Model sizes (0.5B, 1.5B)
- Quantization levels (FP16, INT4)
- BitDPM modes (baseline, single block, multi block, routed)

Usage:
    python scripts/eval_all.py --quick
    python scripts/eval_all.py --full
    python scripts/eval_all.py --report
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Optional

import torch

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitdpm.eval.benchmark import (
    BenchmarkResult,
    EVAL_PROMPTS,
    format_benchmark_table,
    run_benchmark,
    save_benchmark_results,
)
from bitdpm.eval.latency import measure_generate_latency, format_latency_table
from bitdpm.eval.memory import measure_model_memory, format_memory_table
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import ParameterBlock, ParameterBlockConfig
from bitdpm.router.simple_router import SimpleRouter


def build_per_block_router(blocks) -> SimpleRouter:
    """Build keyword router over concrete block IDs, with a general fallback."""
    kw_map = {
        "general": [],
        "math": ["计算", "数学", "equation", "calculate", "solve"],
        "code": ["代码", "编程", "python", "json", "function", "algorithm"],
        "chinese": ["中文", "汉语"],
    }
    general = [b.block_id for b in blocks if b.block_type == "general"]
    router = SimpleRouter(default_block_id=general[0] if general else "general")
    for block in blocks:
        priority = 1 if block.block_type == "general" else 3
        router.register_block(block.block_id, kw_map.get(block.block_type, []), priority=priority)
    return router


def eval_baseline(
    model_name: str,
    device: str,
    load_in_4bit: bool = False,
    max_tokens: int = 128,
    model_path: str = "",
    source: str = "auto",
) -> tuple[BackboneModel, BenchmarkResult]:
    use_model = model_path or model_name
    """Evaluate a baseline model (no blocks)."""
    quant = "INT4" if load_in_4bit else "FP16"
    print(f"\n{'='*70}")
    print(f"BASELINE: {model_name.split('/')[-1]} ({quant})")
    print(f"{'='*70}")

    model = BackboneModel(
        model_name=use_model,
        device=device,
        dtype=torch.float16,
        load_in_4bit=load_in_4bit,
        source=source,
    )
    device = model.device

    def gen_fn(p: str) -> str:
        return model.generate(p, max_new_tokens=max_tokens, temperature=0.1)

    mem = measure_model_memory(model.model, device)
    result = run_benchmark(gen_fn, verbose=True)
    result.model_name = model_name.split("/")[-1]
    result.quant = quant
    result.num_params = f"{model.num_params()/1e9:.1f}B"
    result.device = device
    result.peak_memory_mb = mem.peak_allocated_mb or mem.total_model_mb

    return model, result


def add_blocks_and_eval(
    model: BackboneModel,
    model_name: str,
    device: str,
    num_blocks: int = 3,
    use_router: bool = False,
    max_tokens: int = 128,
    block_dir: Optional[str] = None,
) -> BenchmarkResult:
    """Add parameter blocks to a model and evaluate."""
    label = f"{model_name.split('/')[-1]}+{num_blocks}blocks"
    if use_router:
        label += "+router"

    print(f"\n{'='*70}")
    print(f"BITDPM: {label}")
    print(f"{'='*70}")

    # Build blocks
    hidden_size = model.hidden_size
    num_layers = model.num_hidden_layers
    layer_offset = max(0, num_layers - 3)
    block_types = ["general", "math", "code"]

    from bitdpm.params.parameter_block import BlockBank
    bank = BlockBank()

    for i, block_type in enumerate(block_types[:num_blocks]):
        for layer_off, module_name in enumerate(["o_proj", "down_proj"]):
            lid = layer_offset + layer_off
            bid = f"{block_type}_l{lid}_{module_name}"
            lin = model.get_linear_layer(lid, module_name)
            if lin is None:
                continue

            config = ParameterBlockConfig(
                block_id=bid,
                layer_id=lid,
                module_name=module_name,
                rank=8,
                scale=1.0,
                block_type=block_type,
                hidden_size=hidden_size,
                in_features=lin.in_features,
                out_features=lin.out_features,
            )
            block = ParameterBlock(config)
            backbone_dtype = next(model.model.parameters()).dtype
            block = block.to(device=device, dtype=backbone_dtype)
            bank.add_block(block)

    # Inject
    injector = BlockInjector(model)
    injector.inject_blocks(list(bank.blocks.values()))

    # Router setup
    router = None
    if use_router:
        router = build_per_block_router(list(bank.blocks.values()))

    # Generate with routing
    active_counts = []
    def gen_fn(p: str) -> str:
        if router is not None:
            route_out = router.route(p, available_blocks=list(bank.blocks.keys()))
            injector.set_active_blocks(route_out.active_block_ids)
            active_counts.append(len(route_out.active_block_ids))
        else:
            injector.set_active_blocks(None)
        return model.generate(p, max_new_tokens=max_tokens, temperature=0.1)

    mem = measure_model_memory(model.model, device)
    result = run_benchmark(gen_fn, verbose=True)
    result.model_name = label
    result.quant = "FP16+blocks"
    result.num_params = f"{model.num_params()/1e9:.1f}B"
    result.device = device
    result.peak_memory_mb = mem.peak_allocated_mb or mem.total_model_mb
    result.metadata["num_blocks"] = len(bank)
    result.metadata["router"] = use_router

    # Cleanup patches for next run
    injector.remove_all_patches()
    if use_router:
        result.metadata["avg_active_blocks"] = sum(active_counts) / max(len(active_counts), 1)

    return result


def run_quick(device: str, output_dir: str, model_path: str = "", source: str = "auto"):
    """Quick evaluation: baseline + 1 block mode."""
    results: list[BenchmarkResult] = []
    qwen_model = model_path or "Qwen/Qwen2.5-0.5B-Instruct"

    # Baseline: Qwen0.5B FP16
    model, baseline = eval_baseline(qwen_model, device, max_tokens=64, model_path=model_path, source=source)
    results.append(baseline)

    # Multi-block (3 blocks, no router)
    bitdpm_result = add_blocks_and_eval(
        model, qwen_model, device,
        num_blocks=3, use_router=False, max_tokens=64,
    )
    results.append(bitdpm_result)

    # Multi-block (3 blocks, with router)
    bitdpm_router = add_blocks_and_eval(
        model, qwen_model, device,
        num_blocks=3, use_router=True, max_tokens=64,
    )
    results.append(bitdpm_router)

    # Output
    print(f"\n{'='*70}")
    print("SUMMARY TABLE")
    print(f"{'='*70}")
    print(format_benchmark_table(results))

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, "eval_quick_results.json")
        save_benchmark_results(results, path)

    return results


def run_full(device: str, output_dir: str, model_path: str = "", source: str = "auto"):
    """Full evaluation across all configurations."""
    all_results: list[BenchmarkResult] = []
    qwen_model = model_path or "Qwen/Qwen2.5-0.5B-Instruct"
    configs = [
        (qwen_model, False),
        (qwen_model, True),  # INT4 if available
        ("Qwen/Qwen2.5-1.5B-Instruct", False),
    ]

    for model_name, use_4bit in configs:
        try:
            model, baseline = eval_baseline(model_name, device, load_in_4bit=use_4bit, model_path=model_path, source=source)
            all_results.append(baseline)

            # Single block
            single = add_blocks_and_eval(
                model, model_name, device, num_blocks=1, use_router=False,
            )
            all_results.append(single)

            # Multi block, no router
            multi = add_blocks_and_eval(
                model, model_name, device, num_blocks=3, use_router=False,
            )
            all_results.append(multi)

            # Multi block, with router
            routed = add_blocks_and_eval(
                model, model_name, device, num_blocks=3, use_router=True,
            )
            all_results.append(routed)

        except Exception as e:
            print(f"[Error] Failed config {model_name} 4bit={use_4bit}: {e}")
            continue

    print(f"\n{'='*70}")
    print("FINAL SUMMARY TABLE")
    print(f"{'='*70}")
    print(format_benchmark_table(all_results))

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, "eval_full_results.json")
        save_benchmark_results(all_results, path)
        table_path = os.path.join(output_dir, "eval_full_table.md")
        with open(table_path, "w") as f:
            f.write(format_benchmark_table(all_results))
        print(f"[Report] Saved to {table_path}")

    return all_results


def main():
    parser = argparse.ArgumentParser(description="Run all BitDPM evaluations")
    parser.add_argument("--quick", action="store_true", help="Quick eval (0.5B only)")
    parser.add_argument("--full", action="store_true", help="Full eval across configs")
    parser.add_argument("--device", type=str, default="",
                        help="Device (auto-detect if empty)")
    parser.add_argument("--output", type=str, default="experiments/reports",
                        help="Output directory for results")
    parser.add_argument("--model-path", type=str, default="",
                        help="Local path to model (bypasses download)")
    parser.add_argument("--source", type=str, default="auto",
                        choices=["auto", "hf", "modelscope"],
                        help="Model download source: hf, modelscope, or auto (default: auto)")
    args = parser.parse_args()

    device = args.device or ("cuda" if torch.cuda.is_available() else
                             "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[EvalAll] Device: {device}")
    print(f"[EvalAll] Output: {args.output}")

    if not args.quick and not args.full:
        args.quick = True

    try:
        if args.full:
            run_full(device, args.output, model_path=args.model_path, source=args.source)
        else:
            run_quick(device, args.output, model_path=args.model_path, source=args.source)

        print(f"\n[EvalAll] Done. Results in {args.output}/")
    except KeyboardInterrupt:
        print("\n[EvalAll] Interrupted.")
    except Exception as e:
        print(f"\n[EvalAll] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
