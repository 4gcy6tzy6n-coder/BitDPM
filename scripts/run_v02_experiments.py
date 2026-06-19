#!/usr/bin/env python3
"""BitDPM v0.2 experiments: INT4+Blocks, EntropyRouter, M6 Scheduler Metrics.

Combines all three v0.2 development tasks into one comprehensive experiment.

Usage:
    python scripts/run_v02_experiments.py
    python scripts/run_v02_experiments.py --quick
    python scripts/run_v02_experiments.py --entropy-only
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
    EVAL_PROMPTS,
    format_benchmark_table,
    run_benchmark,
    save_benchmark_results,
)
from bitdpm.eval.memory import measure_model_memory
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import BlockBank
from bitdpm.router.entropy_router import (
    ComputeEntropy,
    EntropyRouter,
    RouterOutput,
)
from bitdpm.router.simple_router import SimpleRouter


def apply_simulated_quantization(model, bits: int = 8):
    """Simulate INT8/INT4 quantization of linear layer weights."""
    quantized_layers = 0
    for module in model.modules():
        if isinstance(module, torch.nn.Linear):
            w = module.weight.data
            orig_dtype = w.dtype
            w_float = w.float()

            if bits == 8:
                scale = w_float.abs().max() / 127.0
                if scale > 0:
                    w_q = torch.clamp(torch.round(w_float / scale), -128, 127)
                    w_deq = w_q * scale
                else:
                    w_deq = w_float
            elif bits == 4:
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


class SchedulerMetricsCollector:
    """M6: Collects scheduler-level metrics during inference.

    Tracks:
    - Active block count per prompt
    - Routing overhead time (ms)
    - Block forward overhead vs total forward
    - Number of blocks skipped
    """

    def __init__(self):
        self.records: list[dict] = []
        self.reset()

    def reset(self):
        self.records = []

    def record_routing(self, router_output: RouterOutput, prompt: str):
        self.records.append({
            "prompt": prompt[:50],
            "active_blocks": router_output.active_block_ids,
            "num_active": len(router_output.active_block_ids),
            "routing_time_ms": router_output.routing_time_ms,
            "confidence": router_output.confidence,
            "entropy": router_output.metadata.get("entropy"),
        })

    def summary(self) -> dict:
        if not self.records:
            return {}

        num_active_list = [r["num_active"] for r in self.records]
        routing_times = [r["routing_time_ms"] for r in self.records]

        return {
            "total_prompts": len(self.records),
            "avg_active_blocks": sum(num_active_list) / len(num_active_list),
            "min_active_blocks": min(num_active_list),
            "max_active_blocks": max(num_active_list),
            "avg_routing_time_ms": sum(routing_times) / len(routing_times) if routing_times else 0,
            "total_routing_time_ms": sum(routing_times),
        }

    def print_summary(self, label: str = ""):
        s = self.summary()
        if not s:
            return
        print(f"\n  [M6 Scheduler] {label}")
        print(f"    Prompts:         {s['total_prompts']}")
        print(f"    Active blocks:   avg={s['avg_active_blocks']:.1f}, "
              f"min={s['min_active_blocks']}, max={s['max_active_blocks']}")
        print(f"    Routing time:    avg={s['avg_routing_time_ms']:.2f}ms, "
              f"total={s['total_routing_time_ms']:.1f}ms")


def build_block_type_map(bank: BlockBank) -> dict[str, list[str]]:
    """Build a block_type -> [block_ids] mapping from the block bank."""
    type_map: dict[str, list[str]] = {}
    for meta in bank.list_blocks():
        btype = meta["block_type"]
        bid = meta["block_id"]
        if btype not in type_map:
            type_map[btype] = []
        type_map[btype].append(bid)
    return type_map


def run(args):
    device = args.device or (
        "cuda" if torch.cuda.is_available() else
        "mps" if torch.backends.mps.is_available() else "cpu"
    )
    os.makedirs(args.output, exist_ok=True)
    all_results = []
    all_metrics: list[dict] = []
    scheduler = SchedulerMetricsCollector()

    print(f"{'='*70}")
    print(f"BitDPM v0.2 Experiments")
    print(f"{'='*70}")
    print(f"  Device:    {device}")
    print(f"  Model:     {args.model}")
    print(f"  Quant:     {'INT4' if args.int4 else 'INT8' if args.int8 else 'FP16'}")
    print(f"  Runtimes:  {args.num_runs} (+ {args.warmup} warmup)")

    # 1. Load backbone
    print(f"\n{'>>'*30}")
    print("[1/4] Loading backbone...")
    backbone_dtype = torch.float32 if device == "cpu" else torch.float16
    backbone = BackboneModel(
        model_name=args.model,
        device=device,
        dtype=backbone_dtype,
        source=args.source,
    )

    # 2. Quantize backbone (if requested)
    quant_label = "FP16"
    if args.int4:
        n_q = apply_simulated_quantization(backbone.model, bits=4)
        print(f"  Quantized {n_q} layers to INT4 (simulated)")
        quant_label = "INT4"
    elif args.int8:
        n_q = apply_simulated_quantization(backbone.model, bits=8)
        print(f"  Quantized {n_q} layers to INT8 (simulated)")
        quant_label = "INT8"

    # 3. Load blocks
    print(f"\n{'>>'*30}")
    print("[2/4] Loading parameter blocks...")
    bank = BlockBank()
    if args.load_blocks and os.path.isdir(args.load_blocks):
        bank = BlockBank.load_all(args.load_blocks, device=torch.device(device))
        print(f"  Loaded {len(bank)} blocks:")
        for meta in bank.list_blocks():
            print(f"    {meta['block_id']} (type={meta['block_type']})")
    else:
        print("  No blocks found — running baselines only.")

    # Build block type map for EntropyRouter
    type_map = build_block_type_map(bank)
    all_block_ids = [meta["block_id"] for meta in bank.list_blocks()]

    # 4. Build injectors for different configs
    def make_injector(config: str) -> tuple[BlockInjector, list[str]]:
        """Create injector and return (injector, active_block_ids)."""
        injector = BlockInjector(backbone)
        if config == "baseline" or config == "quant":
            return injector, []
        elif config == "all_blocks":
            blocks = list(bank.blocks.values())
            per_block_scale = args.block_scale / max(len(blocks), 1)
            for b in blocks:
                b.scale = per_block_scale
            injector.inject_blocks(blocks)
            return injector, [b.block_id for b in blocks]
        elif config == "single":
            blocks = [bank.get_block("general_l23_o_proj")]
            for b in blocks:
                b.scale = args.block_scale
            injector.inject_blocks(blocks)
            return injector, [b.block_id for b in blocks]
        else:
            return injector, []

    # ================================================================
    # Experiment Configs
    # ================================================================

    # SimpleRouter for keyword routing — register per-block-ID
    keyword_router = SimpleRouter(default_block_id="general")
    block_keywords = {
        "general": [],
        "math": [
            "计算", "数学", "equation", "formula", "calculate",
            "solve", "derivative", "integral", "algebra",
        ],
        "code": [
            "代码", "编程", "python", "json", "function", "algorithm",
            "bug", "compile", "api", "implementation",
        ],
        "chinese": [
            "中文", "汉语", "普通话", "中国",
        ],
    }
    for meta in bank.list_blocks():
        btype = meta["block_type"]
        bid = meta["block_id"]
        kws = block_keywords.get(btype, [])
        keyword_router.register_block(bid, kws, priority=2 if btype == "general" else 3)

    # EntropyRouter for entropy-based routing
    entropy_router = EntropyRouter(
        block_type_map=type_map,
        default_block_type="general",
        entropy_low=args.entropy_low,
        entropy_high=args.entropy_high,
        min_blocks=args.min_blocks,
        max_blocks=args.max_blocks,
        mode="hybrid",
    )

    configs_to_run = args.configs
    if not configs_to_run:
        configs_to_run = ["baseline"]
        if bank.blocks:
            configs_to_run += ["all_blocks", "keyword_routed", "entropy_routed"]

    # ================================================================
    for cfg in configs_to_run:
        print(f"\n{'='*70}")
        print(f"EXPERIMENT: {cfg}")
        print(f"{'='*70}")

        scheduler.reset()

        if cfg == "baseline":
            # Pure backbone, no blocks
            injector, _ = make_injector("baseline")

            def gen_baseline(p: str) -> str:
                return backbone.generate(p, max_new_tokens=args.max_tokens, temperature=0.1)

            mem = measure_model_memory(backbone.model, device)
            result = run_benchmark(gen_baseline, verbose=not args.quick)
            result.model_name = f"{quant_label} baseline"
            result.quant = quant_label
            result.num_params = f"{backbone.num_params()/1e9:.1f}B"
            result.device = device
            result.peak_memory_mb = mem.peak_allocated_mb or mem.total_model_mb
            all_results.append(result)
            all_metrics.append({"config": cfg, "num_active": 0, "routing_ms": 0})

        elif cfg == "all_blocks":
            # All blocks, uniform activation
            injector, active_ids = make_injector("all_blocks")
            block_forward_extra = len(active_ids)

            def gen_all_blocks(p: str) -> str:
                return backbone.generate(p, max_new_tokens=args.max_tokens, temperature=0.1)

            mem = measure_model_memory(backbone.model, device)
            result = run_benchmark(gen_all_blocks, verbose=not args.quick)
            result.model_name = f"{quant_label} all_blocks({len(active_ids)})"
            result.quant = f"{quant_label}+blocks"
            result.num_params = f"{backbone.num_params()/1e9:.1f}B"
            result.device = device
            result.peak_memory_mb = mem.peak_allocated_mb or mem.total_model_mb
            result.metadata["active_blocks"] = len(active_ids)
            all_results.append(result)
            all_metrics.append({
                "config": cfg,
                "num_active": len(active_ids),
                "routing_ms": 0,
            })

        elif cfg == "keyword_routed":
            # Keyword router
            injector, _ = make_injector("all_blocks")

            def gen_keyword(p: str) -> str:
                route_out = keyword_router.route(
                    p, available_blocks=all_block_ids if all_block_ids else None
                )
                scheduler.record_routing(route_out, p)
                return backbone.generate(p, max_new_tokens=args.max_tokens, temperature=0.1)

            mem = measure_model_memory(backbone.model, device)
            result = run_benchmark(gen_keyword, verbose=not args.quick)
            result.model_name = f"{quant_label} keyword_routed"
            result.quant = f"{quant_label}+routed"
            result.num_params = f"{backbone.num_params()/1e9:.1f}B"
            result.device = device
            result.peak_memory_mb = mem.peak_allocated_mb or mem.total_model_mb
            s = scheduler.summary()
            result.metadata = {
                **result.metadata,
                "router": "keyword",
                "avg_active_blocks": s.get("avg_active_blocks", 0),
                "avg_routing_time_ms": s.get("avg_routing_time_ms", 0),
            }
            all_results.append(result)
            scheduler.print_summary(label="keyword")
            all_metrics.append({
                "config": cfg,
                **s,
            })

        elif cfg == "entropy_routed":
            # Entropy router
            injector, _ = make_injector("all_blocks")

            def gen_entropy(p: str) -> str:
                # Compute entropy from model
                entropy = ComputeEntropy.from_model_and_prompt(
                    backbone.model, backbone.tokenizer, p, device=device
                )
                route_out = entropy_router.route(
                    p, entropy=entropy,
                    available_blocks=all_block_ids if all_block_ids else None,
                )
                scheduler.record_routing(route_out, p)
                return backbone.generate(p, max_new_tokens=args.max_tokens, temperature=0.1)

            mem = measure_model_memory(backbone.model, device)
            result = run_benchmark(gen_entropy, verbose=not args.quick)
            result.model_name = f"{quant_label} entropy_routed"
            result.quant = f"{quant_label}+routed"
            result.num_params = f"{backbone.num_params()/1e9:.1f}B"
            result.device = device
            result.peak_memory_mb = mem.peak_allocated_mb or mem.total_model_mb
            s = scheduler.summary()
            result.metadata = {
                **result.metadata,
                "router": "entropy",
                "avg_active_blocks": s.get("avg_active_blocks", 0),
                "avg_routing_time_ms": s.get("avg_routing_time_ms", 0),
            }
            all_results.append(result)
            scheduler.print_summary(label="entropy")
            all_metrics.append({
                "config": cfg,
                **s,
            })

    # ================================================================
    # Summary
    # ================================================================
    if all_results:
        print(f"\n{'='*70}")
        print("v0.2 EXPERIMENT SUMMARY")
        print(f"{'='*70}")
        print(format_benchmark_table(all_results))

        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(args.output, f"v02_results_{timestamp}.json")
        save_benchmark_results(all_results, save_path)

        # Save scheduler metrics
        metrics_path = os.path.join(args.output, f"v02_metrics_{timestamp}.json")
        with open(metrics_path, "w") as f:
            json.dump(all_metrics, f, indent=2)
        print(f"\n  Metrics:  {metrics_path}")
        print(f"  Results:  {save_path}")

        # Print M6 scheduler summary
        print(f"\n  {'='*50}")
        print("  M6 SCHEDULER METRICS SUMMARY")
        print(f"  {'='*50}")
        for m in all_metrics:
            if "avg_active_blocks" in m:
                print(f"  {m['config']:<25} active={m.get('avg_active_blocks', 0):.1f}  "
                      f"routing={m.get('avg_routing_time_ms', 0):.2f}ms")

    print(f"\n[BitDPM v0.2] Done.")


def main():
    parser = argparse.ArgumentParser(description="BitDPM v0.2 experiments")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--load-blocks", type=str, default="experiments/outputs/blocks")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--source", type=str, default="auto")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--output", type=str, default="experiments/reports")
    parser.add_argument("--num-runs", type=int, default=1)
    parser.add_argument("--warmup", type=int, default=1)

    # Quantization
    parser.add_argument("--int4", action="store_true", help="Simulate INT4 quantization")
    parser.add_argument("--int8", action="store_true", help="Simulate INT8 quantization")

    # Block config
    parser.add_argument("--block-scale", type=float, default=0.15)
    parser.add_argument("--configs", type=str, nargs="+", default=[],
                        choices=["baseline", "all_blocks", "keyword_routed", "entropy_routed"])

    # Entropy router config
    parser.add_argument("--entropy-low", type=float, default=0.3)
    parser.add_argument("--entropy-high", type=float, default=0.6)
    parser.add_argument("--min-blocks", type=int, default=0)
    parser.add_argument("--max-blocks", type=int, default=3)

    # Quick mode
    parser.add_argument("--quick", action="store_true", help="Less verbose output")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
