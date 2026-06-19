#!/usr/bin/env python3
"""BitDPM v0.3: Real NF4 backbone + Router comparison + Block budget scan.

Three experiments:
  A: NF4 backbone baseline vs NF4 + Routed BitDPM
  B: All router modes compared (None, Random, AlwaysAll, Keyword, Entropy)
  C: Block budget sweep (min/max blocks, entropy thresholds)

Usage:
    python scripts/run_v03_experiments.py             # Run all
    python scripts/run_v03_experiments.py --quick     # Quick validation
    python scripts/run_v03_experiments.py --only nf4  # Just NF4
    python scripts/run_v03_experiments.py --only router  # Just router comparison
    python scripts/run_v03_experiments.py --only budget  # Just budget sweep
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitdpm.eval.benchmark import (
    BenchmarkResult,
    format_benchmark_table,
    run_benchmark,
    save_benchmark_results,
)
from bitdpm.eval.memory import measure_model_memory
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import BlockBank
from bitdpm.router.entropy_router import ComputeEntropy, EntropyRouter, RouterOutput as EntropyRouterOutput
from bitdpm.router.simple_router import RouterOutput, SimpleRouter


def build_block_type_map(bank: BlockBank) -> dict[str, list[str]]:
    """block_type -> [block_ids]"""
    type_map: dict[str, list[str]] = {}
    for meta in bank.list_blocks():
        btype = meta["block_type"]
        bid = meta["block_id"]
        type_map.setdefault(btype, []).append(bid)
    return type_map


class SchedulerMetrics:
    """M6 scheduler metrics collector."""
    def __init__(self):
        self.records: list[dict] = []

    def record(self, active_ids: list[str], routing_time_ms: float = 0, **kw):
        self.records.append({
            "num_active": len(active_ids),
            "routing_time_ms": routing_time_ms,
            **kw,
        })

    def summary(self) -> dict:
        if not self.records:
            return {}
        na = [r["num_active"] for r in self.records]
        rt = [r["routing_time_ms"] for r in self.records]
        return {
            "avg_active": sum(na) / len(na),
            "min_active": min(na),
            "max_active": max(na),
            "avg_routing_ms": sum(rt) / len(rt),
        }

    def print_summary(self, label: str = ""):
        s = self.summary()
        if not s:
            return
        print(f"  [Scheduler] {label}: active={s['avg_active']:.1f} "
              f"({s['min_active']}-{s['max_active']}), "
              f"routing={s['avg_routing_ms']:.3f}ms")


# ======================================================================
# Experiment A: NF4 quantization
# ======================================================================

def experiment_nf4(backbone, bank, device, block_type_map, all_block_ids, args):
    """NF4 baseline vs NF4 + Keyword routed vs NF4 + Entropy routed."""
    print(f"\n{'='*70}")
    print("EXPERIMENT A: NF4 QUANTIZATION")
    print(f"{'='*70}")
    results: list[BenchmarkResult] = []

    # Reload backbone in FP16, then quantize to NF4
    print("\n[NF4] Loading FP16 backbone and quantizing to NF4...")
    nf4_backbone = BackboneModel(
        model_name=args.model, device=device, dtype=torch.float16,
        source=args.source, quantize_method="nf4",
    )
    mem = measure_model_memory(nf4_backbone.model, device)

    # NF4 baseline
    def gen_nf4(p):
        return nf4_backbone.generate(p, max_new_tokens=args.max_tokens, temperature=0.1)
    r = run_benchmark(gen_nf4, verbose=not args.quick)
    r.model_name = "NF4 baseline"
    r.quant = "NF4"
    r.num_params = f"{nf4_backbone.num_params()/1e9:.1f}B"
    r.device = device
    r.peak_memory_mb = mem.total_model_mb
    results.append(r)

    # NF4 + All blocks
    if bank.blocks:
        injector = BlockInjector(nf4_backbone)
        blocks = list(bank.blocks.values())
        for b in blocks:
            b.scale = args.block_scale / max(len(blocks), 1)
        injector.inject_blocks(blocks)
        mem2 = measure_model_memory(nf4_backbone.model, device)
        def gen_all(p):
            return nf4_backbone.generate(p, max_new_tokens=args.max_tokens, temperature=0.1)
        r = run_benchmark(gen_all, verbose=not args.quick)
        r.model_name = "NF4 all_blocks"
        r.quant = "NF4+blocks"
        r.num_params = f"{nf4_backbone.num_params()/1e9:.1f}B"
        r.device = device
        r.peak_memory_mb = mem2.total_model_mb
        results.append(r)
        injector.remove_all_patches()

    # NF4 + Keyword routed
    if bank.blocks:
        injector = BlockInjector(nf4_backbone)
        blocks = list(bank.blocks.values())
        for b in blocks:
            b.scale = args.block_scale / max(len(blocks), 1)
        injector.inject_blocks(blocks)
        kw_router = SimpleRouter(default_block_id="general")
        kw_map = {
            "general": [], "math": ["计算","数学","equation","calculate","solve"],
            "code": ["代码","编程","python","json","function","algorithm"],
            "chinese": ["中文","汉语"],
        }
        for meta in bank.list_blocks():
            kws = kw_map.get(meta["block_type"], [])
            kw_router.register_block(meta["block_id"], kws, priority=3)
        scheduler = SchedulerMetrics()
        def gen_kw(p):
            o = kw_router.route(p, available_blocks=all_block_ids if all_block_ids else None)
            scheduler.record(o.active_block_ids, o.routing_time_ms)
            return nf4_backbone.generate(p, max_new_tokens=args.max_tokens, temperature=0.1)
        r = run_benchmark(gen_kw, verbose=not args.quick)
        s = scheduler.summary()
        r.model_name = "NF4 keyword_routed"
        r.quant = "NF4+routed"
        r.num_params = f"{nf4_backbone.num_params()/1e9:.1f}B"
        r.device = device
        r.peak_memory_mb = mem2.total_model_mb
        r.metadata["router"] = "keyword"
        r.metadata["avg_active_blocks"] = s.get("avg_active", 0)
        results.append(r)
        scheduler.print_summary("NF4 keyword")
        injector.remove_all_patches()

    # NF4 + Entropy routed
    if bank.blocks:
        injector = BlockInjector(nf4_backbone)
        blocks = list(bank.blocks.values())
        for b in blocks:
            b.scale = args.block_scale / max(len(blocks), 1)
        injector.inject_blocks(blocks)
        e_router = EntropyRouter(block_type_map, entropy_low=0.3, entropy_high=0.6,
                                  min_blocks=0, max_blocks=3, mode="hybrid")
        scheduler = SchedulerMetrics()
        def gen_entropy(p):
            entropy = ComputeEntropy.from_model_and_prompt(
                nf4_backbone.model, nf4_backbone.tokenizer, p, device=device)
            o = e_router.route(p, entropy=entropy, available_blocks=all_block_ids if all_block_ids else None)
            scheduler.record(o.active_block_ids, o.routing_time_ms)
            return nf4_backbone.generate(p, max_new_tokens=args.max_tokens, temperature=0.1)
        r = run_benchmark(gen_entropy, verbose=not args.quick)
        s = scheduler.summary()
        r.model_name = "NF4 entropy_routed"
        r.quant = "NF4+routed"
        r.num_params = f"{nf4_backbone.num_params()/1e9:.1f}B"
        r.device = device
        r.peak_memory_mb = mem2.total_model_mb
        r.metadata["router"] = "entropy"
        r.metadata["avg_active_blocks"] = s.get("avg_active", 0)
        results.append(r)
        scheduler.print_summary("NF4 entropy")
        injector.remove_all_patches()

    return results


# ======================================================================
# Experiment B: Router comparison
# ======================================================================

def experiment_router_compare(backbone, bank, device, block_type_map, all_block_ids, args):
    """Compare Baseline, Random, AlwaysAll, Keyword, Entropy routers."""
    print(f"\n{'='*70}")
    print("EXPERIMENT B: ROUTER COMPARISON")
    print(f"{'='*70}")
    results: list[BenchmarkResult] = []

    # Setup keyword router
    kw_router = SimpleRouter(default_block_id="general")
    kw_map = {
        "general": [], "math": ["计算","数学","equation","calculate","solve"],
        "code": ["代码","编程","python","json","function","algorithm"],
        "chinese": ["中文","汉语"],
    }
    for meta in bank.list_blocks():
        kw_router.register_block(meta["block_id"], kw_map.get(meta["block_type"], []), priority=3)

    # Setup entropy router
    e_router = EntropyRouter(block_type_map, entropy_low=0.3, entropy_high=0.6,
                              min_blocks=0, max_blocks=3, mode="hybrid")

    # Configurations to run
    configs = [
        ("FP16 baseline", "none", 0),
        ("Random router", "random", 2),
        ("Always-All(8)", "all", 8),
        ("Keyword router", "keyword", 0),
        ("Entropy router", "entropy", 0),
    ]

    for label, mode, fixed_blocks in configs:
        print(f"\n--- {label} ---")
        injector = BlockInjector(backbone)
        if mode in ("all",):
            blocks = list(bank.blocks.values())
            for b in blocks:
                b.scale = args.block_scale / max(len(blocks), 1)
            injector.inject_blocks(blocks)
        elif mode in ("random", "keyword", "entropy"):
            blocks = list(bank.blocks.values())
            for b in blocks:
                b.scale = args.block_scale / max(len(blocks), 1)
            injector.inject_blocks(blocks)

        scheduler = SchedulerMetrics()
        def make_gen(m, fb, sched):
            def gen_fn(p: str) -> str:
                if m == "none":
                    pass
                elif m == "random":
                    k = min(fb, len(all_block_ids))
                    selected = random.sample(all_block_ids, k) if k > 0 else []
                    sched.record(selected)
                elif m == "keyword":
                    o = kw_router.route(p, available_blocks=all_block_ids if all_block_ids else None)
                    sched.record(o.active_block_ids, o.routing_time_ms)
                elif m == "entropy":
                    entropy = ComputeEntropy.from_model_and_prompt(
                        backbone.model, backbone.tokenizer, p, device=device)
                    o = e_router.route(p, entropy=entropy,
                                       available_blocks=all_block_ids if all_block_ids else None)
                    sched.record(o.active_block_ids, o.routing_time_ms)
                return backbone.generate(p, max_new_tokens=args.max_tokens, temperature=0.1)
            return gen_fn

        mem = measure_model_memory(backbone.model, device)
        r = run_benchmark(make_gen(mode, fixed_blocks, scheduler), verbose=not args.quick)
        s = scheduler.summary()
        r.model_name = label
        r.quant = "FP16+routed" if mode != "none" else "FP16"
        r.num_params = f"{backbone.num_params()/1e9:.1f}B"
        r.device = device
        r.peak_memory_mb = mem.total_model_mb
        r.metadata["router"] = mode
        r.metadata["avg_active_blocks"] = s.get("avg_active", 0)
        r.metadata["avg_routing_ms"] = s.get("avg_routing_ms", 0)
        results.append(r)
        scheduler.print_summary(label)

        injector.remove_all_patches()

    return results


# ======================================================================
# Experiment C: Block budget scan
# ======================================================================

def experiment_budget_scan(backbone, bank, device, block_type_map, all_block_ids, args):
    """Sweep entropy thresholds and block budgets."""
    print(f"\n{'='*70}")
    print("EXPERIMENT C: BLOCK BUDGET SCAN")
    print(f"{'='*70}")
    results: list[BenchmarkResult] = []

    budgets = [
        # (max_blocks, entropy_low, entropy_high, min_blocks)
        (0, 0.0, 1.0, 0),   # no blocks
        (1, 0.3, 0.6, 0),   # conservative
        (2, 0.3, 0.6, 0),   # moderate
        (3, 0.3, 0.6, 0),   # default
        (4, 0.2, 0.5, 0),   # aggressive low threshold
        (4, 0.4, 0.7, 1),   # cautious with min
        (8, 0.0, 1.0, 0),   # always all (fixed_blocks=8)
    ]

    for max_b, el, eh, min_b in budgets:
        label = f"{'no_blocks' if max_b == 0 else 'always_all' if max_b == 8 else f'max{max_b}_el{el}_eh{eh}'}"
        print(f"\n--- Budget: {label} (max={max_b}, low={el}, high={eh}, min={min_b}) ---")

        if max_b == 0:
            # No blocks
            mem = measure_model_memory(backbone.model, device)
            r = run_benchmark(
                lambda p: backbone.generate(p, max_new_tokens=args.max_tokens, temperature=0.1),
                verbose=not args.quick,
            )
            r.model_name = f"no_blocks"
            r.quant = "FP16"
            r.num_params = f"{backbone.num_params()/1e9:.1f}B"
            r.device = device
            r.peak_memory_mb = mem.total_model_mb
            r.metadata["max_blocks"] = 0
            r.metadata["active_blocks"] = 0
            results.append(r)

        elif max_b == 8:
            # Always all blocks
            injector = BlockInjector(backbone)
            blocks = list(bank.blocks.values())
            for b in blocks:
                b.scale = args.block_scale / max(len(blocks), 1)
            injector.inject_blocks(blocks)
            mem = measure_model_memory(backbone.model, device)
            r = run_benchmark(
                lambda p: backbone.generate(p, max_new_tokens=args.max_tokens, temperature=0.1),
                verbose=not args.quick,
            )
            r.model_name = f"always_all"
            r.quant = "FP16+blocks"
            r.num_params = f"{backbone.num_params()/1e9:.1f}B"
            r.device = device
            r.peak_memory_mb = mem.total_model_mb
            r.metadata["max_blocks"] = 8
            r.metadata["active_blocks"] = 8
            results.append(r)
            injector.remove_all_patches()

        else:
            # Entropy router with budget
            injector = BlockInjector(backbone)
            blocks = list(bank.blocks.values())
            for b in blocks:
                b.scale = args.block_scale / max(len(blocks), 1)
            injector.inject_blocks(blocks)
            router = EntropyRouter(block_type_map, entropy_low=el, entropy_high=eh,
                                    min_blocks=min_b, max_blocks=max_b, mode="hybrid")
            scheduler = SchedulerMetrics()
            def make_gen(rtr, sched):
                def fn(p):
                    entropy = ComputeEntropy.from_model_and_prompt(
                        backbone.model, backbone.tokenizer, p, device=device)
                    o = rtr.route(p, entropy=entropy,
                                  available_blocks=all_block_ids if all_block_ids else None)
                    sched.record(o.active_block_ids, o.routing_time_ms)
                    return backbone.generate(p, max_new_tokens=args.max_tokens, temperature=0.1)
                return fn
            mem = measure_model_memory(backbone.model, device)
            r = run_benchmark(make_gen(router, scheduler), verbose=not args.quick)
            s = scheduler.summary()
            r.model_name = label
            r.quant = "FP16+routed"
            r.num_params = f"{backbone.num_params()/1e9:.1f}B"
            r.device = device
            r.peak_memory_mb = mem.total_model_mb
            r.metadata["max_blocks"] = max_b
            r.metadata["entropy_low"] = el
            r.metadata["entropy_high"] = eh
            r.metadata["min_blocks"] = min_b
            r.metadata["avg_active_blocks"] = s.get("avg_active", 0)
            results.append(r)
            scheduler.print_summary(label)
            injector.remove_all_patches()

    return results


# ======================================================================
def run(args):
    device = args.device or (
        "cuda" if torch.cuda.is_available() else
        "mps" if torch.backends.mps.is_available() else "cpu"
    )
    os.makedirs(args.output, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    print(f"{'='*70}")
    print("BitDPM v0.3 Experiments")
    print(f"{'='*70}")
    print(f"  Device: {device}")
    print(f"  Model:  {args.model}")

    # Load FP16 backbone (shared between experiments B & C)
    backbone = BackboneModel(
        model_name=args.model, device=device,
        dtype=torch.float16, source=args.source,
    )

    # Load blocks
    bank = BlockBank()
    if args.load_blocks and os.path.isdir(args.load_blocks):
        bank = BlockBank.load_all(args.load_blocks, device=torch.device(device))
        print(f"\n[Blocks] Loaded {len(bank)} blocks")

    type_map = build_block_type_map(bank)
    all_ids = [m["block_id"] for m in bank.list_blocks()]

    all_results = {}

    # Experiment A: NF4
    if "nf4" in args.only or "all" in args.only:
        nf4_results = experiment_nf4(backbone, bank, device, type_map, all_ids, args)
        all_results["nf4"] = nf4_results
        print(f"\n{'='*70}")
        print("NF4 EXPERIMENT TABLE")
        print(f"{'='*70}")
        print(format_benchmark_table(nf4_results))
        save_benchmark_results(nf4_results,
            os.path.join(args.output, f"v03_nf4_{timestamp}.json"))

    # Experiment B: Router comparison
    if "router" in args.only or "all" in args.only:
        router_results = experiment_router_compare(backbone, bank, device, type_map, all_ids, args)
        all_results["router"] = router_results
        print(f"\n{'='*70}")
        print("ROUTER COMPARISON TABLE")
        print(f"{'='*70}")
        print(format_benchmark_table(router_results))
        save_benchmark_results(router_results,
            os.path.join(args.output, f"v03_router_{timestamp}.json"))

    # Experiment C: Budget scan
    if "budget" in args.only or "all" in args.only:
        budget_results = experiment_budget_scan(backbone, bank, device, type_map, all_ids, args)
        all_results["budget"] = budget_results
        print(f"\n{'='*70}")
        print("BUDGET SCAN TABLE")
        print(f"{'='*70}")
        print(format_benchmark_table(budget_results))
        save_benchmark_results(budget_results,
            os.path.join(args.output, f"v03_budget_{timestamp}.json"))


def main():
    parser = argparse.ArgumentParser(description="BitDPM v0.3 experiments")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--load-blocks", type=str, default="experiments/outputs/blocks")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--source", type=str, default="auto")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--block-scale", type=float, default=0.15)
    parser.add_argument("--output", type=str, default="experiments/reports")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--only", type=str, nargs="+",
                        default=["all"],
                        choices=["all", "nf4", "router", "budget"])
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
