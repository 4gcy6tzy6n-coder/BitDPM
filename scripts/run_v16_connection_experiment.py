#!/usr/bin/env python3
"""BitDPM v16: GPU-Centric Connection Function Experiment.

Compares three connection functions on the same block pool:
  v1: HardAdd — current baseline (y = Wx + Σ g·ΔWx)
  v2: NormClip — clip Δy if ||Δy||/||y_base|| > ratio
  v3: TokenGate — apply Δy only to gated token positions

Metrics per connection variant:
  - Baseline score
  - Best fixed block score
  - Oracle score and coverage
  - Always-All score
  - Break counts (fixed blocks that hurt baseline)
  - Router gain (if utility router is provided)

Usage:
    python scripts/run_v16_connection_experiment.py \
      --model /path/to/Qwen2.5-0.5B-Instruct \
      --registry configs/bitdpm_v11_admitted_pool.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment for model loading
os.environ.setdefault("HF_HOME", "/tmp/claude-501/hf-cache")
os.environ.setdefault("TRANSFORMERS_CACHE", "/tmp/claude-501/hf-cache")
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", "/tmp/claude-501/hf-cache")

import torch

from bitdpm.eval.benchmark import (
    EVAL_PROMPTS as BASE_PROMPTS,
    compute_accuracy,
    save_benchmark_results,
)
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.composer import ConnectionMode, ExecutionPlan
from bitdpm.params.parameter_block import BlockBank, ParameterBlock


# ---------------------------------------------------------------------------
# Block loading helpers
# ---------------------------------------------------------------------------

def load_pool_blocks(registry_path: str, device: str) -> tuple[BlockBank, dict]:
    """Load blocks from registry config."""
    with open(registry_path) as f:
        config = json.load(f)

    bank = BlockBank()
    load_dirs = config.get("load_blocks", [])
    for d in load_dirs:
        if os.path.isdir(d):
            for fname in sorted(os.listdir(d)):
                if fname.endswith(".pt"):
                    fpath = os.path.join(d, fname)
                    try:
                        block = ParameterBlock.load(fpath, device=torch.device(device))
                        bank.add_block(block)
                    except Exception as e:
                        print(f"  [Warn] Failed to load {fpath}: {e}")

    print(f"  Loaded {len(bank)} blocks from {len(load_dirs)} directories")
    return bank, config


def get_block_scales(config: dict) -> dict[str, float]:
    """Extract per-block scales from registry or use default."""
    return config.get("block_scales", {})


def get_configs_to_run(config: dict) -> list[str]:
    """Get list of config names from registry."""
    return config.get("configs", ["baseline", "always_all"])


# ---------------------------------------------------------------------------
# Single-prompt evaluation with connection function
# ---------------------------------------------------------------------------

def evaluate_prompt(
    prompt: str,
    category: str,
    backbone: BackboneModel,
    injector: BlockInjector,
    config_name: str,
    block_bank: BlockBank,
    block_scales: dict[str, float],
    connection_mode: ConnectionMode,
    norm_clip_ratio: float,
    max_tokens: int,
) -> tuple[str, float]:
    """Evaluate a single prompt under a specific config and connection mode.

    Returns (config_name, score).
    """
    # Configure injector based on config name
    if config_name == "baseline" or config_name == "none":
        injector.set_active_blocks([])
    elif config_name == "always_all":
        injector.set_active_blocks(list(block_bank.blocks.keys()))
    elif config_name in block_bank.blocks:
        injector.set_active_blocks([config_name])
    else:
        # Try to find a block by type matching the config name
        type_blocks = block_bank.get_blocks_by_type(config_name)
        if type_blocks:
            injector.set_active_blocks([type_blocks[0].block_id])
        else:
            # Try matching by prefix
            matches = [bid for bid in block_bank.blocks if bid.startswith(config_name)]
            if matches:
                injector.set_active_blocks(matches[:1])
            else:
                injector.set_active_blocks([])

    # Set connection mode
    injector.set_connection(connection_mode, ratio=norm_clip_ratio)

    # Generate
    generated = backbone.generate(prompt, max_new_tokens=max_tokens, temperature=0.1)
    score = compute_accuracy(prompt, generated, category)

    return generated, score


# ---------------------------------------------------------------------------
# Main evaluation loop
# ---------------------------------------------------------------------------

def run_connection_eval(
    backbone: BackboneModel,
    block_bank: BlockBank,
    block_scales: dict[str, float],
    configs: list[str],
    connection_mode: ConnectionMode,
    norm_clip_ratio: float,
    max_tokens: int,
    bench_prompts: dict[str, list[str]],
    quick: bool = False,
) -> dict:
    """Run full evaluation for one connection mode.

    Accumulates per-sample scores across ALL configs first,
    then computes oracle, break counts, and aggregates.
    """
    injector = BlockInjector(backbone)
    injector.inject_blocks(list(block_bank.blocks.values()))

    for bid, blk in block_bank.blocks.items():
        blk.scale = block_scales.get(bid, block_scales.get(blk.block_type, 0.75))

    results = {"connection": connection_mode.value, "norm_clip_ratio": norm_clip_ratio, "configs": {}}

    # Accumulate sample_scores: prompt -> { config: score }
    all_sample_scores: dict[str, dict[str, float]] = {}
    all_sample_categories: dict[str, str] = {}
    all_sample_outputs: dict[str, dict[str, str]] = {}

    for cfg in configs:
        if quick and cfg not in ("baseline", "always_all"):
            continue

        print(f"  [{connection_mode.value}] Config: {cfg}...")
        cat_scores: dict[str, list[float]] = {}

        for cat, prompts in bench_prompts.items():
            cat_scores[cat] = []
            for prompt in prompts:
                generated, score = evaluate_prompt(
                    prompt, cat, backbone, injector, cfg,
                    block_bank, block_scales,
                    connection_mode, norm_clip_ratio, max_tokens,
                )
                cat_scores[cat].append(score)
                all_sample_scores.setdefault(prompt, {})[cfg] = score
                all_sample_categories[prompt] = cat
                all_sample_outputs.setdefault(prompt, {})[cfg] = generated[:200]

        avg_cat = {cat: sum(scores) / len(scores) for cat, scores in cat_scores.items()}
        overall = sum(avg_cat.values()) / len(avg_cat)
        results["configs"][cfg] = {"overall": overall, "category_scores": avg_cat}

    injector.remove_all_patches()

    # Oracle: best config per sample
    oracle_total = 0.0
    oracle_coverage = 0
    for prompt, cfg_scores in all_sample_scores.items():
        best_cfg = max(cfg_scores, key=cfg_scores.get)
        best_score = cfg_scores[best_cfg]
        oracle_total += best_score
        if best_cfg != "baseline":
            oracle_coverage += 1

    total_samples = len(all_sample_scores)
    results["oracle"] = {
        "overall": oracle_total / max(total_samples, 1),
        "coverage": oracle_coverage,
        "total_samples": total_samples,
    }

    # Break counts per fixed config
    baseline_scores = {p: s.get("baseline", 0.0) for p, s in all_sample_scores.items()}
    break_counts: dict[str, dict] = {}
    for cfg in configs:
        if cfg == "baseline" or cfg == "always_all" or quick:
            continue
        fixes = breaks = neutral = 0
        for prompt, cfg_scores in all_sample_scores.items():
            if cfg not in cfg_scores:
                continue
            bl_score = baseline_scores.get(prompt, 0.0)
            cs = cfg_scores[cfg]
            if cs > bl_score: fixes += 1
            elif cs < bl_score: breaks += 1
            else: neutral += 1
        break_counts[cfg] = {"fixes": fixes, "breaks": breaks, "neutral": neutral}
    results["break_counts"] = break_counts

    return results


# ---------------------------------------------------------------------------
def run(args):
    device = args.device or (
        "cuda" if torch.cuda.is_available() else
        "mps" if torch.backends.mps.is_available() else "cpu"
    )
    os.makedirs(args.output, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    print(f"{'='*70}")
    print("BitDPM v16: GPU-Centric Connection Function Experiment")
    print(f"{'='*70}")
    print(f"  Device:    {device}")
    print(f"  Model:     {args.model}")
    print(f"  Registry:  {args.registry}")
    print(f"  Max tokens: {args.max_tokens}")

    # 1. Load backbone
    backbone = BackboneModel(
        model_name=args.model, device=device,
        dtype=torch.float16,
    )

    # 2. Load blocks from registry
    block_bank, registry_config = load_pool_blocks(args.registry, device=device)
    block_scales = get_block_scales(registry_config)
    configs = get_configs_to_run(registry_config)
    print(f"  Configs: {configs}")

    # 3. Build benchmark prompt set
    import copy
    bench_prompts = {}
    for cat, prompts_list in BASE_PROMPTS.items():
        bench_prompts[cat] = prompts_list[:]
    print(f"  Benchmark: {sum(len(v) for v in bench_prompts.values())} prompts "
          f"across {len(bench_prompts)} categories")

    # 4. Connection function variants to compare
    connections = [
        ("hard_add", ConnectionMode.HARD_ADD, 0.5),
        ("norm_clip_0.3", ConnectionMode.NORM_CLIP, 0.3),
        ("norm_clip_0.5", ConnectionMode.NORM_CLIP, 0.5),
        ("norm_clip_0.7", ConnectionMode.NORM_CLIP, 0.7),
        ("token_gate_num", ConnectionMode.TOKEN_GATE, 0.5),
    ]

    if args.quick:
        connections = [
            ("hard_add", ConnectionMode.HARD_ADD, 0.5),
            ("norm_clip_0.5", ConnectionMode.NORM_CLIP, 0.5),
        ]

    all_results = {}

    for label, conn_mode, clip_ratio in connections:
        print(f"\n{'='*60}")
        print(f"CONNECTION: {label}")
        print(f"{'='*60}")
        r = run_connection_eval(
            backbone, block_bank, block_scales, configs,
            conn_mode, clip_ratio, args.max_tokens, bench_prompts,
            quick=args.quick,
        )
        all_results[label] = r

        # Print summary
        bl = r["configs"].get("baseline", {}).get("overall", 0)
        aa = r["configs"].get("always_all", {}).get("overall", 0)
        ora = r["oracle"]["overall"]
        cov = r["oracle"]["coverage"]
        print(f"  Baseline:     {bl:.3f}")
        print(f"  Always-All:   {aa:.3f}")
        print(f"  Oracle:       {ora:.3f} (coverage: {cov}/{r['oracle']['total_samples']})")
        print(f"  Breaks by block:")
        for cfg_name, bc in sorted(r["break_counts"].items()):
            if bc["breaks"] > 0 or bc["fixes"] > 0:
                print(f"    {cfg_name:<30} fixes={bc['fixes']:2d} breaks={bc['breaks']:2d}")

    # 5. Summary table
    print(f"\n{'='*70}")
    print("V16 CONNECTION FUNCTION COMPARISON")
    print(f"{'='*70}")
    print(f"| {'Connection':<20} | {'Baseline':<9} | {'Always-All':<10} | {'Oracle':<7} | {'Coverage':<8} |")
    print(f"|{'-'*22}|{'-'*11}|{'-'*12}|{'-'*9}|{'-'*10}|")
    for label, r in all_results.items():
        bl = r["configs"].get("baseline", {}).get("overall", 0)
        aa = r["configs"].get("always_all", {}).get("overall", 0)
        ora = r["oracle"]["overall"]
        cov = r["oracle"]["coverage"]
        tot = r["oracle"]["total_samples"]
        print(f"| {label:<20} | {bl:<9.3f} | {aa:<10.3f} | {ora:<7.3f} | {cov}/{tot:<6} |")

    # 6. Break comparison table
    print(f"\n{'='*70}")
    print("BREAK COUNT COMPARISON")
    print(f"{'='*70}")
    all_fix_configs = sorted(set(
        c for r in all_results.values()
        for c in r["break_counts"].keys()
    ))
    print(f"| {'Block':<30} |", end="")
    for label, _, _ in connections:
        print(f" {'fixes':<5} {'brk':<5} |", end="")
    print()
    print(f"|{'-'*32}|" + "|" + "|".join([f"{'-'*12}" for _ in connections]) + "|")
    for cfg_name in all_fix_configs:
        if cfg_name == "baseline" or cfg_name == "always_all":
            continue
        print(f"| {cfg_name:<30} |", end="")
        for label, _, _ in connections:
            bc = all_results.get(label, {}).get("break_counts", {}).get(cfg_name, {})
            fixes = bc.get("fixes", 0)
            breaks = bc.get("breaks", 0)
            print(f" {fixes:<5} {breaks:<5} |", end="")
        print()

    # 7. Save
    save_path = os.path.join(args.output, f"v16_connection_{timestamp}.json")
    with open(save_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved: {save_path}")


def main():
    parser = argparse.ArgumentParser(description="BitDPM v16 connection function experiment")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--registry", type=str, default="configs/bitdpm_v11_admitted_pool.json")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--output", type=str, default="experiments/reports")
    parser.add_argument("--quick", action="store_true",
                        help="Only hard_add and norm_clip_0.5")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
