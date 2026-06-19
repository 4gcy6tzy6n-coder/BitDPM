#!/usr/bin/env python3
"""BitDPM v0.4: Real routing gating + specialization matrix + NF4 recovery.

Experiments with CORRECT block gating:
  A: Router comparison (Keyword vs Entropy modes vs Always-All vs None)
  B: Per-block specialization matrix
  C: Active block budget scan
  D: NF4 recovery experiment

Usage:
    python scripts/run_v04_experiments.py             # Run router, specialization, budget
    python scripts/run_v04_experiments.py --no-spec --no-budget  # Just router
    python scripts/run_v04_experiments.py --no-router --no-budget  # Just specialization
    python scripts/run_v04_experiments.py --no-router --no-spec --budget  # Just budget
    python scripts/run_v04_experiments.py --nf4       # Include slow NF4 recovery
"""

from __future__ import annotations

import argparse
import json
import os
import random as _random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch

from bitdpm.eval.benchmark import (
    EVAL_PROMPTS,
    run_benchmark,
    format_benchmark_table,
    save_benchmark_results,
)
from bitdpm.eval.memory import measure_model_memory
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import BlockBank
from bitdpm.router.entropy_router import ComputeEntropy, EntropyRouter
from bitdpm.router.simple_router import SimpleRouter


def make_gated_generate(
    injector: BlockInjector,
    backbone: BackboneModel,
    router=None,
    entropy_router=None,
    all_block_ids: list[str] | None = None,
    random_k: int | None = None,
    random_seed: int = 0,
    max_tokens: int = 64,
    temperature: float = 0.1,
    deterministic: bool = False,
    device: str = "cpu",
):
    """Create a generate function that properly gates blocks via the injector.

    Args:
        injector: BlockInjector with blocks already injected.
        backbone: The backbone model.
        router: SimpleRouter for keyword routing.
        entropy_router: EntropyRouter for entropy-based routing.
        all_block_ids: All available block IDs.
        max_tokens: Max new tokens.
        temperature: Generation temperature.

    Returns:
        (generate_fn, stats_recorder) where stats_recorder is a list of dicts.
    """
    import time as _time_mod
    stats: list[dict] = []
    rng = _random.Random(random_seed)

    def gen_fn(prompt: str) -> str:
        selected: list[str] | None = None
        routing_time = 0.0

        if router:
            t0 = _time_mod.time()
            route_out = router.route(prompt, available_blocks=all_block_ids)
            routing_time = (_time_mod.time() - t0) * 1000
            selected = route_out.active_block_ids
        elif entropy_router:
            t0 = _time_mod.time()
            entropy = ComputeEntropy.from_model_and_prompt(
                backbone.model, backbone.tokenizer, prompt, device=device)
            route_out = entropy_router.route(
                prompt, entropy=entropy, available_blocks=all_block_ids)
            routing_time = (_time_mod.time() - t0) * 1000
            selected = route_out.active_block_ids
        elif random_k is not None:
            t0 = _time_mod.time()
            candidates = list(all_block_ids or [])
            k = min(max(random_k, 0), len(candidates))
            selected = rng.sample(candidates, k) if k else []
            routing_time = (_time_mod.time() - t0) * 1000
        # else: selected=None means all injected blocks are active (default behavior)

        # CRITICAL: Actually gate blocks via the injector
        # None = all blocks active; [] = no blocks; [...] = specific blocks
        injector.set_active_blocks(selected)

        result = backbone.generate(
            prompt,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=not deterministic,
        )

        # Count total active blocks across all composers
        total_active = sum(
            len(p.composer.active_block_ids) for p in injector.patches.values()
        ) if injector.patches else 0
        stats.append({
            "num_active": total_active,
            "active_ids": selected if selected is not None else [],
            "routing_time_ms": routing_time,
        })

        return result

    return gen_fn, stats


def build_block_type_map(bank: BlockBank) -> dict[str, list[str]]:
    type_map: dict[str, list[str]] = {}
    for meta in bank.list_blocks():
        type_map.setdefault(meta["block_type"], []).append(meta["block_id"])
    return type_map


def build_keyword_router(bank: BlockBank, block_type_map: dict[str, list[str]]) -> SimpleRouter:
    """Build a per-block keyword router that falls back to one general block."""
    general_blocks = block_type_map.get("general", [])
    default_block = general_blocks[0] if general_blocks else "general"
    router = SimpleRouter(default_block_id=default_block)
    kw_map = {
        "general": [],
        "math": ["计算", "数学", "equation", "calculate", "solve"],
        "code": ["代码", "编程", "python", "json", "function", "algorithm"],
        "chinese": ["中文", "汉语"],
    }
    for meta in bank.list_blocks():
        priority = 1 if meta["block_type"] == "general" else 3
        router.register_block(
            meta["block_id"],
            kw_map.get(meta["block_type"], []),
            priority=priority,
        )
    return router


def search_json(pattern_dir: str, prefix: str) -> str:
    """Find latest JSON file matching prefix."""
    import glob
    files = sorted(glob.glob(os.path.join(pattern_dir, f"{prefix}_*.json")))
    return files[-1] if files else ""


def run_router_comparison(backbone, bank, block_type_map, all_block_ids, device, args):
    """Experiment A: Router comparison with CORRECT block gating."""
    print(f"\n{'='*70}")
    print("EXPERIMENT A: ROUTER COMPARISON (with real block gating)")
    print(f"{'='*70}")
    results = []
    scale = args.block_scale
    n_blocks = len(all_block_ids)

    # Setup routers
    kw_router = build_keyword_router(bank, block_type_map)

    entropy_router_default = EntropyRouter(
        block_type_map, entropy_low=0.3, entropy_high=0.6,
        min_blocks=0, max_blocks=1, mode="hybrid")

    configs = [
        # (label, router_type, fixed_active)
        ("Baseline (no blocks)", "none", []),
        ("Always-All (8 blocks)", "all", all_block_ids),
    ]

    # Add per-block configs
    block_types = ["general", "math", "code", "chinese"]
    for bt in block_types:
        bids = block_type_map.get(bt, [])
        configs.append((f"Only {bt} blocks", "fixed", bids))

    # Keyword router
    configs.append(("Keyword router", "keyword", None))
    # Entropy router variants
    configs.append(("Entropy hybrid (max1, 0.3/0.6)", "entropy_hybrid", None))
    configs.append(("Random router (k=1)", "random", None))

    for label, rtype, fixed_ids in configs:
        print(f"\n--- {label} ---")
        injector = BlockInjector(backbone)

        if rtype == "none":
            pass  # no blocks
        elif rtype == "all":
            blocks = list(bank.blocks.values())
            for b in blocks: b.scale = scale / max(n_blocks, 1)
            injector.inject_blocks(blocks)
        elif rtype == "fixed":
            blocks = [bank.get_block(bid) for bid in fixed_ids if bid in bank.blocks]
            per_block = scale / max(len(blocks), 1)
            for b in blocks: b.scale = per_block
            injector.inject_blocks(blocks)
        elif rtype == "keyword":
            blocks = list(bank.blocks.values())
            for b in blocks: b.scale = scale / max(n_blocks, 1)
            injector.inject_blocks(blocks)
        elif rtype == "entropy_hybrid":
            blocks = list(bank.blocks.values())
            for b in blocks: b.scale = scale / max(n_blocks, 1)
            injector.inject_blocks(blocks)
        elif rtype == "random":
            blocks = list(bank.blocks.values())
            for b in blocks: b.scale = scale / max(n_blocks, 1)
            injector.inject_blocks(blocks)

        gen_fn, stats = make_gated_generate(
            injector, backbone,
            router=kw_router if rtype == "keyword" else None,
            entropy_router=entropy_router_default if rtype == "entropy_hybrid" else None,
            all_block_ids=all_block_ids,
            random_k=1 if rtype == "random" else None,
            random_seed=args.random_seed,
            max_tokens=args.max_tokens,
            deterministic=args.deterministic,
            device=device,
        )

        mem = measure_model_memory(backbone.model, device)
        r = run_benchmark(gen_fn, verbose=not args.quick)
        avg_active = sum(s["num_active"] for s in stats) / max(len(stats), 1)
        avg_routing = sum(s["routing_time_ms"] for s in stats) / max(len(stats), 1)
        r.model_name = label
        r.quant = "FP16+routed" if rtype not in ("none",) else "FP16"
        r.num_params = f"{backbone.num_params()/1e9:.1f}B"
        r.device = device
        r.peak_memory_mb = mem.total_model_mb
        r.metadata["router"] = rtype
        r.metadata["avg_active_blocks"] = avg_active
        r.metadata["avg_routing_ms"] = avg_routing
        results.append(r)
        print(f"  [Done] active={avg_active:.2f} routing={avg_routing:.3f}ms")

        injector.remove_all_patches()

    return results


def run_budget_scan(backbone, bank, block_type_map, all_block_ids, device, args):
    """Experiment C: active block budget scan with CORRECT block gating."""
    print(f"\n{'='*70}")
    print("EXPERIMENT C: ACTIVE BLOCK BUDGET SCAN (with real block gating)")
    print(f"{'='*70}")
    results = []
    scale = args.block_scale
    n_blocks = len(all_block_ids)

    configs = [
        ("Budget no_blocks", "none", 0, None),
        ("Budget max1", "entropy", 1, (0.3, 0.6)),
        ("Budget max2", "entropy", 2, (0.3, 0.6)),
        ("Budget max3", "entropy", 3, (0.3, 0.6)),
        ("Budget max8", "all", 8, None),
    ]

    for label, mode, max_blocks, thresholds in configs:
        print(f"\n--- {label} ---")
        injector = BlockInjector(backbone)

        entropy_router = None
        if mode == "none":
            pass
        elif mode == "all":
            blocks = list(bank.blocks.values())
            for b in blocks:
                b.scale = scale / max(n_blocks, 1)
            injector.inject_blocks(blocks)
        elif mode == "entropy":
            blocks = list(bank.blocks.values())
            for b in blocks:
                b.scale = scale / max(n_blocks, 1)
            injector.inject_blocks(blocks)
            el, eh = thresholds or (0.3, 0.6)
            entropy_router = EntropyRouter(
                block_type_map,
                entropy_low=el,
                entropy_high=eh,
                min_blocks=1,
                max_blocks=max_blocks,
                mode="hybrid",
            )

        gen_fn, stats = make_gated_generate(
            injector,
            backbone,
            entropy_router=entropy_router,
            all_block_ids=all_block_ids,
            max_tokens=args.max_tokens,
            deterministic=args.deterministic,
            device=device,
        )

        mem = measure_model_memory(backbone.model, device)
        r = run_benchmark(gen_fn, verbose=not args.quick)
        avg_active = sum(s["num_active"] for s in stats) / max(len(stats), 1)
        avg_routing = sum(s["routing_time_ms"] for s in stats) / max(len(stats), 1)
        r.model_name = label
        r.quant = "FP16" if mode == "none" else "FP16+budget"
        r.num_params = f"{backbone.num_params()/1e9:.1f}B"
        r.device = device
        r.peak_memory_mb = mem.total_model_mb
        r.metadata["budget_mode"] = mode
        r.metadata["max_blocks"] = max_blocks
        r.metadata["avg_active_blocks"] = avg_active
        r.metadata["avg_routing_ms"] = avg_routing
        results.append(r)
        print(f"  [Done] active={avg_active:.2f} routing={avg_routing:.3f}ms")

        injector.remove_all_patches()

    return results


def run_specialization_matrix(backbone, bank, block_type_map, all_block_ids, device, args):
    """Experiment B: Per-block specialization matrix.

    Activate ONLY ONE block type at a time and measure per-category accuracy.
    """
    print(f"\n{'='*70}")
    print("EXPERIMENT B: BLOCK SPECIALIZATION MATRIX")
    print(f"{'='*70}")
    results = []

    block_types = ["general", "math", "code", "chinese"]

    # Baseline per category
    print("\n--- Baseline (no blocks) per category ---")
    mem = measure_model_memory(backbone.model, device)
    r = run_benchmark(
        lambda p: backbone.generate(
            p,
            max_new_tokens=args.max_tokens,
            temperature=0.1,
            do_sample=not args.deterministic,
        ),
        verbose=not args.quick)
    r.model_name = "Baseline"
    r.quant = "FP16"
    r.num_params = f"{backbone.num_params()/1e9:.1f}B"
    r.device = device
    r.peak_memory_mb = mem.total_model_mb
    results.append(r)

    # Per-block-type activation
    for bt in block_types:
        bids = block_type_map.get(bt, [])
        if not bids:
            continue

        print(f"\n--- Only {bt} blocks ({len(bids)} blocks) ---")
        injector = BlockInjector(backbone)
        blocks = [bank.get_block(bid) for bid in bids if bid in bank.blocks]
        per_block = args.block_scale / max(len(blocks), 1)
        for b in blocks: b.scale = per_block
        injector.inject_blocks(blocks)

        gen_fn, _ = make_gated_generate(
            injector, backbone,
            max_tokens=args.max_tokens,
            deterministic=args.deterministic,
            device=device,
        )

        mem = measure_model_memory(backbone.model, device)
        r = run_benchmark(gen_fn, verbose=not args.quick)
        r.model_name = f"Only {bt}"
        r.quant = "FP16+blocks"
        r.num_params = f"{backbone.num_params()/1e9:.1f}B"
        r.device = device
        r.peak_memory_mb = mem.total_model_mb
        r.metadata["active_type"] = bt
        r.metadata["num_active"] = len(bids)
        results.append(r)

        injector.remove_all_patches()

    return results


def run_nf4_recovery(model_name, bank, block_type_map, all_block_ids, device, args):
    """Experiment D: NF4 recovery — FP16 vs NF4 vs NF4+BitDPM."""
    print(f"\n{'='*70}")
    print("EXPERIMENT D: NF4 RECOVERY")
    print(f"{'='*70}")
    results = []
    scale = args.block_scale
    n_blocks = len(all_block_ids)

    # Reload as NF4
    print("\n[NF4] Loading backbone with NF4 quantization...")
    nf4_model = BackboneModel(
        model_name=model_name, device=device,
        dtype=torch.float16, source=args.source,
        quantize_method="nf4",
    )
    device = nf4_model.device
    for block in bank.blocks.values():
        block.to(device=device)

    # NF4 baseline
    print("\n--- NF4 baseline ---")
    mem = measure_model_memory(nf4_model.model, device)
    r = run_benchmark(
        lambda p: nf4_model.generate(
            p,
            max_new_tokens=args.max_tokens,
            temperature=0.1,
            do_sample=not args.deterministic,
        ),
        verbose=not args.quick)
    r.model_name = "NF4 baseline"
    r.quant = "NF4"
    r.num_params = f"{nf4_model.num_params()/1e9:.1f}B"
    r.device = device
    r.peak_memory_mb = mem.total_model_mb
    results.append(r)

    # NF4 + all blocks
    if bank.blocks:
        print("\n--- NF4 + All blocks ---")
        injector = BlockInjector(nf4_model)
        blocks = list(bank.blocks.values())
        for b in blocks: b.scale = scale / max(n_blocks, 1)
        injector.inject_blocks(blocks)
        mem2 = measure_model_memory(nf4_model.model, device)
        r = run_benchmark(
            lambda p: nf4_model.generate(
                p,
                max_new_tokens=args.max_tokens,
                temperature=0.1,
                do_sample=not args.deterministic,
            ),
            verbose=not args.quick)
        r.model_name = "NF4 + all blocks"
        r.quant = "NF4+blocks"
        r.num_params = f"{nf4_model.num_params()/1e9:.1f}B"
        r.device = device
        r.peak_memory_mb = mem2.total_model_mb
        results.append(r)
        injector.remove_all_patches()

    # NF4 + best single block type
    best_type = args.best_block_type
    best_ids = block_type_map.get(best_type, [])
    if bank.blocks and best_ids:
        print(f"\n--- NF4 + only {best_type} blocks ---")
        injector = BlockInjector(nf4_model)
        blocks = [bank.get_block(bid) for bid in best_ids if bid in bank.blocks]
        for b in blocks:
            b.scale = scale / max(len(blocks), 1)
        injector.inject_blocks(blocks)
        gen_fn, stats = make_gated_generate(
            injector, nf4_model,
            all_block_ids=best_ids,
            max_tokens=args.max_tokens,
            deterministic=args.deterministic,
            device=device,
        )
        mem_best = measure_model_memory(nf4_model.model, device)
        r = run_benchmark(gen_fn, verbose=not args.quick)
        avg_active = sum(s["num_active"] for s in stats) / max(len(stats), 1)
        r.model_name = f"NF4 + only {best_type}"
        r.quant = "NF4+blocks"
        r.num_params = f"{nf4_model.num_params()/1e9:.1f}B"
        r.device = device
        r.peak_memory_mb = mem_best.total_model_mb
        r.metadata["active_type"] = best_type
        r.metadata["avg_active_blocks"] = avg_active
        results.append(r)
        print(f"  [Done] active={avg_active:.2f}")
        injector.remove_all_patches()

    # NF4 + keyword routed
    if bank.blocks:
        print("\n--- NF4 + keyword routed ---")
        injector = BlockInjector(nf4_model)
        blocks = list(bank.blocks.values())
        for b in blocks: b.scale = scale / max(n_blocks, 1)
        injector.inject_blocks(blocks)
        kw_router = build_keyword_router(bank, block_type_map)
        gen_fn, stats = make_gated_generate(
            injector, nf4_model, router=kw_router,
            all_block_ids=all_block_ids, max_tokens=args.max_tokens,
            deterministic=args.deterministic,
            device=device)
        mem3 = measure_model_memory(nf4_model.model, device)
        r = run_benchmark(gen_fn, verbose=not args.quick)
        avg_active = sum(s["num_active"] for s in stats) / max(len(stats), 1)
        r.model_name = "NF4 + keyword routed"
        r.quant = "NF4+routed"
        r.num_params = f"{nf4_model.num_params()/1e9:.1f}B"
        r.device = device
        r.peak_memory_mb = mem3.total_model_mb
        r.metadata["avg_active_blocks"] = avg_active
        results.append(r)
        print(f"  [Done] active={avg_active:.2f}")
        injector.remove_all_patches()

    return results


def run(args):
    device = args.device or (
        "cuda" if torch.cuda.is_available() else
        "mps" if torch.backends.mps.is_available() else "cpu"
    )
    os.makedirs(args.output, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")

    print(f"{'='*70}")
    print("BitDPM v0.4 Experiments (with CORRECT block gating)")
    print(f"{'='*70}")
    print(f"  Device: {device}")
    print(f"  Model:  {args.model}")

    nf4_only = args.nf4 and not args.router and not args.specialization and not args.budget
    backbone = None
    if not nf4_only:
        # Load FP16 backbone
        backbone = BackboneModel(
            model_name=args.model, device=device,
            dtype=torch.float16, source=args.source,
        )
        device = backbone.device
        print(f"  Effective device: {device}")

    # Load blocks
    bank = BlockBank()
    if args.load_blocks and os.path.isdir(args.load_blocks):
        bank = BlockBank.load_all(args.load_blocks, device=torch.device(device))
        print(f"\n[Blocks] {len(bank)} blocks loaded")

    type_map = build_block_type_map(bank)
    all_ids = [m["block_id"] for m in bank.list_blocks()]

    if args.router:
        r = run_router_comparison(backbone, bank, type_map, all_ids, device, args)
        print(f"\n{'='*70}\nROUTER COMPARISON\n{'='*70}")
        print(format_benchmark_table(r))
        save_benchmark_results(r, os.path.join(args.output, f"v04_router_{ts}.json"))

    if args.specialization:
        r = run_specialization_matrix(backbone, bank, type_map, all_ids, device, args)
        print(f"\n{'='*70}\nSPECIALIZATION MATRIX\n{'='*70}")
        print(format_benchmark_table(r))
        save_benchmark_results(r, os.path.join(args.output, f"v04_spec_{ts}.json"))

    if args.budget:
        r = run_budget_scan(backbone, bank, type_map, all_ids, device, args)
        print(f"\n{'='*70}\nBUDGET SCAN\n{'='*70}")
        print(format_benchmark_table(r))
        save_benchmark_results(r, os.path.join(args.output, f"v04_budget_{ts}.json"))

    if args.nf4:
        r = run_nf4_recovery(args.model, bank, type_map, all_ids, device, args)
        print(f"\n{'='*70}\nNF4 RECOVERY\n{'='*70}")
        print(format_benchmark_table(r))
        save_benchmark_results(r, os.path.join(args.output, f"v04_nf4_{ts}.json"))


def main():
    parser = argparse.ArgumentParser(description="BitDPM v0.4 experiments")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--load-blocks", type=str, default="experiments/outputs/blocks")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--source", type=str, default="auto")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--block-scale", type=float, default=0.15)
    parser.add_argument("--best-block-type", type=str, default="math",
                        choices=["general", "math", "code", "chinese"],
                        help="Block type used for NF4 best-single recovery")
    parser.add_argument("--random-seed", type=int, default=0)
    parser.add_argument("--output", type=str, default="experiments/reports")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--deterministic", action="store_true",
                        help="Use greedy/deterministic generation for matched-protocol checks")
    parser.add_argument("--no-router", action="store_false", dest="router", help="Skip router comparison")
    parser.add_argument("--no-spec", action="store_false", dest="specialization", help="Skip specialization matrix")
    parser.add_argument("--budget", action="store_true", help="Run active block budget scan")
    parser.add_argument("--no-budget", action="store_false", dest="budget", help="Skip active block budget scan")
    parser.add_argument("--nf4", action="store_true", help="Include NF4 recovery experiment (slow)")
    parser.set_defaults(router=True, specialization=True, budget=True)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
