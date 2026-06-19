#!/usr/bin/env python3
"""BitDPM experiment runner: baseline vs single vs multi vs routed.

Usage:
    python scripts/run_experiments.py
    python scripts/run_experiments.py --quick  # fewer prompts
    python scripts/run_experiments.py --load-blocks experiments/outputs/blocks
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitdpm.eval.benchmark import (
    BenchmarkResult,
    EVAL_PROMPTS,
    format_benchmark_table,
    run_benchmark,
    save_benchmark_results,
)
from bitdpm.eval.latency import measure_generate_latency, format_latency_table
from bitdpm.eval.memory import measure_model_memory
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import BlockBank, ParameterBlock
from bitdpm.router.simple_router import SimpleRouter


def build_per_block_router(block_bank: BlockBank) -> SimpleRouter:
    """Build keyword router over concrete block IDs, with a general fallback."""
    kw_map = {
        "general": [],
        "math": ["计算", "数学", "equation", "calculate", "solve"],
        "code": ["代码", "编程", "python", "json", "function", "algorithm"],
        "chinese": ["中文", "汉语"],
    }
    general = block_bank.get_blocks_by_type("general")
    router = SimpleRouter(default_block_id=general[0].block_id if general else "general")
    for block in block_bank:
        priority = 1 if block.block_type == "general" else 3
        router.register_block(block.block_id, kw_map.get(block.block_type, []), priority=priority)
    return router


def load_blocks(block_dir: str, device: str = "cpu") -> BlockBank:
    """Load saved parameter blocks from a directory."""
    bank = BlockBank.load_all(block_dir, device=torch.device(device))
    print(f"[Load] Loaded {len(bank)} blocks:")
    for meta in bank.list_blocks():
        print(f"  {meta['block_id']} (type={meta['block_type']})")
    return bank


def export_result_and_model(
    result: BenchmarkResult,
    model: BackboneModel,
    mem,
    label: str,
    quant: str = "FP16",
    extra_meta: dict | None = None,
) -> BenchmarkResult:
    """Fill in result metadata from model state."""
    result.model_name = label
    result.quant = quant
    result.num_params = f"{model.num_params()/1e9:.1f}B"
    result.device = model.device
    result.peak_memory_mb = mem.peak_allocated_mb or mem.total_model_mb
    if extra_meta:
        result.metadata.update(extra_meta)
    return result


def run_experiment(
    backbone: BackboneModel,
    block_bank: BlockBank,
    config: str,  # "baseline", "single", "multi", "routed"
    max_tokens: int = 64,
    device: str = "cpu",
    quick: bool = False,
    block_scale: float = 0.15,
) -> BenchmarkResult:
    """Run a specific experiment configuration."""
    injector = BlockInjector(backbone)

    if config == "baseline":
        # No blocks at all
        pass

    elif config == "single":
        # Only general_l23_o_proj block
        blocks = [block_bank.get_block("general_l23_o_proj")]
        for b in blocks: b.scale = block_scale
        injector.inject_blocks(blocks)
        print(f"  [Single block] general_l23_o_proj (scale={block_scale})")

    elif config == "single_down":
        blocks = [block_bank.get_block("general_l23_down_proj")]
        for b in blocks: b.scale = block_scale
        injector.inject_blocks(blocks)
        print(f"  [Single block] general_l23_down_proj (scale={block_scale})")

    elif config == "multi_all":
        # All blocks - adjust scale to keep total contribution consistent
        all_blocks = list(block_bank.blocks.values())
        per_block_scale = block_scale / max(len(all_blocks), 1)
        for b in all_blocks: b.scale = per_block_scale
        injector.inject_blocks(all_blocks)
        print(f"  [Multi block] {len(all_blocks)} blocks (per-block scale={per_block_scale:.4f})")

    elif config == "multi_general":
        # All general blocks
        blocks = block_bank.get_blocks_by_type("general")
        per_block_scale = block_scale / max(len(blocks), 1)
        for b in blocks: b.scale = per_block_scale
        injector.inject_blocks(blocks)
        print(f"  [Multi general] {len(blocks)} blocks (per-block scale={per_block_scale:.4f})")

    elif config == "routed":
        # All blocks + router - adjust scale for total contribution
        all_blocks = list(block_bank.blocks.values())
        per_block_scale = block_scale / max(len(all_blocks), 1)
        for b in all_blocks: b.scale = per_block_scale
        injector.inject_blocks(all_blocks)
        router = build_per_block_router(block_bank)

        route_info = []
        active_counts = []
        def gen_fn(p: str) -> str:
            route_out = router.route(p, available_blocks=[b.block_id for b in all_blocks])
            injector.set_active_blocks(route_out.active_block_ids)
            route_info.append((p, route_out.active_block_ids))
            active_counts.append(len(route_out.active_block_ids))
            return backbone.generate(p, max_new_tokens=max_tokens, temperature=0.1)

        mem = measure_model_memory(backbone.model, device)
        result = run_benchmark(gen_fn, verbose=not quick)
        export_result_and_model(result, backbone, mem, "routed", quant="FP16+routed",
                                extra_meta={
                                    "num_blocks": len(all_blocks),
                                    "router": True,
                                    "avg_active_blocks": sum(active_counts) / max(len(active_counts), 1),
                                })
        injector.remove_all_patches()
        return result

    else:
        raise ValueError(f"Unknown config: {config}")

    # Default: generate function using backbone
    # After removing injections, we need to re-inject for non-baseline
    def gen_fn(p: str) -> str:
        return backbone.generate(p, max_new_tokens=max_tokens, temperature=0.1)

    mem = measure_model_memory(backbone.model, device)

    if config == "baseline":
        label = f"baseline"
        quant = "FP16"
    else:
        label = f"{config}"
        quant = "FP16+blocks"

    result = run_benchmark(gen_fn, verbose=not quick)
    export_result_and_model(result, backbone, mem, label, quant=quant)

    injector.remove_all_patches()
    return result


def run(args):
    device = args.device or (
        "cuda" if torch.cuda.is_available() else
        "mps" if torch.backends.mps.is_available() else "cpu"
    )
    print(f"[Experiments] Device: {device}")
    print(f"[Experiments] Model: {args.model}")
    os.makedirs(args.output, exist_ok=True)

    # 1. Load backbone
    backbone = BackboneModel(
        model_name=args.model,
        device=device,
        dtype=torch.float32,
        source=args.source,
    )
    device = backbone.device
    print(f"[Experiments] Effective device: {device}")

    # 2. Load blocks
    bank = load_blocks(args.load_blocks, device=device)

    # 3. Run experiments
    configs = args.configs
    if not configs:
        configs = ["baseline", "single", "multi_all", "routed"]

    results: list[BenchmarkResult] = []

    for cfg in configs:
        print(f"\n{'='*70}")
        print(f"EXPERIMENT: {cfg}")
        print(f"{'='*70}")
        try:
            result = run_experiment(
                backbone, bank, cfg,
                max_tokens=args.max_tokens,
                device=device,
                quick=args.quick,
                block_scale=args.block_scale,
            )
            results.append(result)
        except Exception as e:
            print(f"  [ERROR] {cfg}: {e}")
            import traceback
            traceback.print_exc()

    # 4. Summary
    if results:
        print(f"\n{'='*70}")
        print("EXPERIMENT SUMMARY TABLE")
        print(f"{'='*70}")
        table = format_benchmark_table(results)
        print(f"\n{table}")

        # Save
        save_path = os.path.join(args.output, "experiment_results.json")
        save_benchmark_results(results, save_path)

        table_path = os.path.join(args.output, "experiment_table.md")
        with open(table_path, "w") as f:
            f.write(table)
        print(f"  Table saved: {table_path}")

    print(f"\n[Experiments] Done. Results in {args.output}/")


def main():
    parser = argparse.ArgumentParser(description="Run BitDPM experiments comparison")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct",
                        help="Model name or path")
    parser.add_argument("--load-blocks", type=str, default="experiments/outputs/blocks",
                        help="Directory with saved .pt blocks")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--source", type=str, default="auto")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--output", type=str, default="experiments/reports")
    parser.add_argument("--quick", action="store_true",
                        help="Use fewer prompts for faster testing")
    parser.add_argument("--configs", type=str, nargs="+",
                        choices=["baseline", "single", "single_down", "multi_all", "multi_general", "routed"],
                        default=[],
                        help="Which experiments to run (default: all)")
    parser.add_argument("--block-scale", type=float, default=0.15,
                        help="Block scale during inference (default: 0.15)")
    args = parser.parse_args()

    if not args.configs:
        args.configs = ["baseline", "single", "multi_all", "routed"]

    run(args)


if __name__ == "__main__":
    main()
