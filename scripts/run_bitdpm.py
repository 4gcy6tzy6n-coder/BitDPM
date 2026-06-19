#!/usr/bin/env python3
"""Run BitDPM inference: backbone + parameter blocks + optional router.

Usage:
    python scripts/run_bitdpm.py --model Qwen/Qwen2.5-0.5B-Instruct --blocks ./experiments/outputs/blocks/
    python scripts/run_bitdpm.py --model Qwen/Qwen2.5-0.5B-Instruct --blocks ./blocks/ --router
    python scripts/run_bitdpm.py --model Qwen/Qwen2.5-0.5B-Instruct --blocks ./blocks/ --benchmark
"""

from __future__ import annotations

import argparse
import os
import time

import torch

from bitdpm.eval.benchmark import format_benchmark_table, run_benchmark, save_benchmark_results
from bitdpm.eval.latency import measure_generate_latency
from bitdpm.eval.memory import measure_model_memory
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.composer import CompositionMode
from bitdpm.params.parameter_block import ParameterBlock, ParameterBlockConfig, BlockBank
from bitdpm.router.simple_router import SimpleRouter


def build_per_block_router(blocks) -> SimpleRouter:
    """Build keyword router over concrete block IDs, with a general fallback."""
    kw_map = {
        "general": [],
        "math": ["计算", "数学", "equation", "calculate", "solve"],
        "code": ["代码", "编程", "python", "json", "function", "algorithm"],
        "chinese": ["中文", "汉语"],
        "factual": ["fact", "knowledge", "history", "science", "definition", "what is"],
    }
    general = [b.block_id for b in blocks if b.block_type == "general"]
    router = SimpleRouter(default_block_id=general[0] if general else "general")
    for block in blocks:
        priority = 1 if block.block_type == "general" else 3
        router.register_block(block.block_id, kw_map.get(block.block_type, []), priority=priority)
    return router


def build_simple_blocks(backbone, num_blocks: int = 3, device: str = "cpu") -> BlockBank:
    """Build simple test parameter blocks for demonstration.

    Creates blocks for the last few layers, targeting o_proj and down_proj.
    """
    bank = BlockBank()
    hidden_size = backbone.hidden_size
    num_layers = backbone.num_hidden_layers
    layer_offset = max(0, num_layers - 3)  # Use last 3 layers

    block_types = ["general", "math", "code"]

    for i, block_type in enumerate(block_types[:num_blocks]):
        for layer_off, module_name in enumerate(["o_proj", "down_proj"]):
            lid = layer_offset + layer_off
            bid = f"{block_type}_l{lid}_{module_name}"

            # Get actual dimensions from the backbone
            lin = backbone.get_linear_layer(lid, module_name)
            in_f = lin.in_features if lin else hidden_size
            out_f = lin.out_features if lin else hidden_size

            config = ParameterBlockConfig(
                block_id=bid,
                layer_id=lid,
                module_name=module_name,
                rank=8,
                scale=1.0,
                block_type=block_type,
                hidden_size=hidden_size,
                in_features=in_f,
                out_features=out_f,
            )
            block = ParameterBlock(config)
            backbone_dtype = next(backbone.model.parameters()).dtype
            block = block.to(device=device, dtype=backbone_dtype)
            bank.add_block(block)
            print(f"  Created block: {bid} ({module_name} @ layer {lid})")

    return bank


def run(args):
    device = args.device or ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[BitDPM] Device: {device}")
    print(f"[BitDPM] Model: {args.model}")

    # 1. Load backbone
    model = BackboneModel(
        model_name=args.model,
        device=device,
        dtype=torch.float16,
        load_in_4bit=args.fourbit,
        load_in_8bit=args.eightbit,
        source=args.source,
    )
    device = model.device
    print(f"[BitDPM] Effective device: {device}")

    # 2. Load or create parameter blocks
    bank = BlockBank()
    if args.blocks and os.path.isdir(args.blocks):
        print(f"[BitDPM] Loading blocks from {args.blocks}")
        bank = BlockBank.load_all(args.blocks, device=torch.device(device))
        print(f"  Loaded {len(bank)} blocks:")
        for meta in bank.list_blocks():
            print(f"    {meta['block_id']} (type={meta['block_type']}, layer={meta['layer_id']})")
    else:
        print(f"[BitDPM] Creating {args.num_blocks} test blocks...")
        bank = build_simple_blocks(model, num_blocks=args.num_blocks, device=device)
        if args.save_blocks:
            os.makedirs(args.save_blocks, exist_ok=True)
            bank.save_all(args.save_blocks)
            print(f"  Blocks saved to {args.save_blocks}")

    # 3. Inject blocks into backbone
    injector = BlockInjector(model)
    all_blocks = list(bank.blocks.values())
    injector.inject_blocks(all_blocks)
    print(f"[BitDPM] Injected {injector.num_patches} patches across layers")

    # 4. Setup router
    router = None
    if args.router:
        print("[BitDPM] Setting up Router v0 (keyword-based)...")
        router = build_per_block_router(all_blocks)
        print(f"  Registered blocks: {list(router.keyword_map.keys())}")

    # 5. Generate function that uses routing
    def generate_with_bitdpm(prompt: str, max_new_tokens: int = 128, temperature: float = args.temperature) -> str:
        # Determine active blocks via router (if available)
        if router is not None:
            route_output = router.route(prompt, available_blocks=[b.block_id for b in all_blocks])
            active_block_ids = route_output.active_block_ids
            injector.set_active_blocks(active_block_ids)
            if active_block_ids:
                print(f"  [Router] Selected blocks: {active_block_ids} (confidence={route_output.confidence:.2f})")
        else:
            injector.set_active_blocks(None)
        return model.generate(prompt, max_new_tokens=max_new_tokens, temperature=temperature)

    # 6. Interactive test
    if args.interactive:
        print(f"\n{'='*60}")
        print("Interactive mode with BitDPM blocks")
        print(f"{'='*60}")
        while True:
            prompt = input("\nPrompt: ").strip()
            if prompt.lower() in ("quit", "exit", "q"):
                break
            start = time.time()
            output = generate_with_bitdpm(prompt, max_new_tokens=args.max_tokens)
            elapsed = time.time() - start
            tok_s = len(output.split()) / max(elapsed, 0.001)
            print(f"Response: {output}")
            print(f"[{elapsed:.2f}s | {tok_s:.1f} tok/s]")

    # 7. Latency benchmark
    if args.latency or args.benchmark:
        print(f"\n{'='*60}")
        print("Latency Benchmark (BitDPM)")
        print(f"{'='*60}")
        metrics = measure_generate_latency(
            lambda p, **kw: generate_with_bitdpm(p, **kw),
            prompt="What is the capital of France?",
            max_new_tokens=args.max_tokens,
            num_runs=args.runs,
            warmup_runs=args.warmup,
        )
        print(f"  Token/s:     {metrics.avg_tokens_per_second:.1f}")
        print(f"  Per-token:   {metrics.per_token_latency_ms:.1f} ms")
        print(f"  Tokens:      {metrics.num_tokens_generated}")

    # 8. Full benchmark
    if args.benchmark:
        print(f"\n{'='*60}")
        print("Full Benchmark (BitDPM)")
        print(f"{'='*60}")

        def gen_fn(p: str) -> str:
            return generate_with_bitdpm(p, max_new_tokens=args.max_tokens, temperature=0.1)

        mem = measure_model_memory(model.model, device)
        result = run_benchmark(gen_fn, verbose=True)
        result.model_name = f"BitDPM-{args.model.split('/')[-1]}"
        result.quant = "INT4" if args.fourbit else "INT8" if args.eightbit else "FP16"
        result.num_params = f"{model.num_params()/1e9:.1f}B"
        result.device = device
        result.peak_memory_mb = mem.peak_allocated_mb or mem.total_model_mb

        # Add block info
        result.metadata["num_blocks"] = len(all_blocks)
        result.metadata["router"] = args.router

        table = format_benchmark_table([result])
        print(f"\n{table}")

        if args.output:
            save_benchmark_results([result], args.output)

    print(f"\n[BitDPM] Done.")


def main():
    parser = argparse.ArgumentParser(description="Run BitDPM inference with parameter blocks")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--blocks", type=str, default="",
                        help="Directory with saved .pt parameter blocks")
    parser.add_argument("--num-blocks", type=int, default=3,
                        help="Number of test blocks to create (if no blocks loaded)")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--4bit", action="store_true", dest="fourbit")
    parser.add_argument("--8bit", action="store_true", dest="eightbit")
    parser.add_argument("--router", action="store_true",
                        help="Enable keyword-based routing")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--latency", action="store_true")
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--output", type=str, default="")
    parser.add_argument("--save-blocks", type=str, default="",
                        help="Save created blocks to directory")
    parser.add_argument("--source", type=str, default="auto",
                        choices=["auto", "hf", "modelscope"],
                        help="Model download source: hf, modelscope, or auto (default: auto)")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
