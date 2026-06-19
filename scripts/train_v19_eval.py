"""BitDPM v19: v18 admitted pool integration + combined evaluation.

Tests pool combinations of v18 safe blocks against the v10 admitted pool.

Pools:
    v18-safe-only: all v18 blocks with net >= 0 at best scale
    v10-admitted: the existing best pool (baseline comparison)
    v10+v18-strong-3: v10 + commonsense_choice, distance_geometry, percent (net>=+2)
    v10+v18-all-safe: v10 + all v18 net>=0 blocks

Usage:
    python scripts/train_v19_eval.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch

from bitdpm.eval.benchmark import EVAL_PROMPTS as BP, compute_accuracy
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import ParameterBlock, BlockBank

# ---------------------------------------------------------------------------
# v18 blocks with their best scales from manual scan
# ---------------------------------------------------------------------------

V18_BLOCKS_DIR = "experiments/outputs/blocks_v18"

# (block_name, best_scale) — only available .pt files
V18_BEST_SCALES: dict[str, float] = {
    "v18_commonsense_choice_l23_down_proj_r8": 0.15,
    "v18_distance_geometry_l23_down_proj_r8": 0.05,
    "v18_percent_l23_down_proj_r8": 0.15,
    "v18_factual_constants_l23_down_proj_r8": 0.05,
    "v18_integer_ops_l23_down_proj_r8": 0.05,
}

V18_STRONG_THREE = [
    "v18_commonsense_choice_l23_down_proj_r8",
    "v18_distance_geometry_l23_down_proj_r8",
    "v18_percent_l23_down_proj_r8",
]

V18_ALL_SAFE = list(V18_BEST_SCALES.keys())


def load_v18_block(block_id: str, device: torch.device) -> ParameterBlock | None:
    """Load a v18 block by its block_id."""
    path = os.path.join(V18_BLOCKS_DIR, f"{block_id}.pt")
    if not os.path.exists(path):
        return None
    block = ParameterBlock.load(path, device=device)
    block.scale = V18_BEST_SCALES.get(block_id, 1.0)
    return block


# ---------------------------------------------------------------------------
# Pool evaluation
# ---------------------------------------------------------------------------

def evaluate_pool(
    backbone: BackboneModel,
    blocks: list[ParameterBlock],
    pool_name: str,
    max_tokens: int = 64,
) -> dict:
    """Evaluate a pool of blocks.

    Returns dict with per-sample scores across:
    - baseline (no blocks)
    - each single block
    - always_all
    - oracle (best per-sample)
    """
    # Also include "no blocks" as a config
    print(f"\n{'='*70}")
    print(f"POOL: {pool_name} ({len(blocks)} blocks)")
    print(f"{'='*70}")

    injector = BlockInjector(backbone)
    if blocks:
        injector.inject_blocks(blocks)

    all_scores: dict[str, dict[str, float]] = {}
    cat_keys = list(BP.keys())

    # Baseline (no blocks)
    injector.set_active_blocks([])
    baseline_scores = {}
    for cat, prompts in BP.items():
        for p in prompts:
            g = backbone.generate(p, max_new_tokens=max_tokens, temperature=0.1)
            s = compute_accuracy(p, g, cat)
            baseline_scores[p] = s
            all_scores.setdefault(p, {})["baseline"] = s

    bl_avg = sum(baseline_scores.values()) / max(len(baseline_scores), 1)
    print(f"  Baseline: {bl_avg:.3f}")

    # Each block individually
    for block in blocks:
        injector.set_active_blocks([block.block_id])
        for cat, prompts in BP.items():
            for p in prompts:
                g = backbone.generate(p, max_new_tokens=max_tokens, temperature=0.1)
                s = compute_accuracy(p, g, cat)
                all_scores.setdefault(p, {})[block.block_id] = s

    # Always-All
    if blocks:
        injector.set_active_blocks([b.block_id for b in blocks])
        for cat, prompts in BP.items():
            for p in prompts:
                g = backbone.generate(p, max_new_tokens=max_tokens, temperature=0.1)
                s = compute_accuracy(p, g, cat)
                all_scores.setdefault(p, {})["always_all"] = s

    injector.remove_all_patches()

    # ---- Compute metrics ----

    n_samples = len(all_scores)

    # Oracle
    oracle_total = 0.0
    oracle_coverage = 0
    for p, scores in all_scores.items():
        # Best among non-baseline (or non-always_all if that's the best)
        candidates = {k: v for k, v in scores.items() if k != "baseline"}
        if not candidates:
            best_cfg = "baseline"
            best_score = scores.get("baseline", 0.0)
        else:
            best_cfg = max(candidates, key=candidates.get)
            best_score = candidates[best_cfg]
            # Compare with baseline
            bl = scores.get("baseline", 0.0)
            if candidates[best_cfg] >= bl:
                pass  # keep oracle
            if candidates[best_cfg] > bl:
                oracle_coverage += 1
        oracle_total += best_score

    oracle_avg = oracle_total / n_samples if n_samples > 0 else 0.0

    # Always-All score
    aa_scores = [
        all_scores[p].get("always_all", 0.0)
        for p in all_scores if "always_all" in all_scores[p]
    ]
    aa_avg = sum(aa_scores) / max(len(aa_scores), 1) if aa_scores else 0.0

    # Per-block fix/break vs baseline
    block_fb = {}
    for block in blocks:
        fixes = breaks = 0
        for p, scores in all_scores.items():
            bl = scores.get("baseline", 0.0)
            bk = scores.get(block.block_id, bl)
            if bk > bl:
                fixes += 1
            elif bk < bl:
                breaks += 1
        net = fixes - breaks
        block_fb[block.block_id] = {"fixes": fixes, "breaks": breaks, "net": net}

    # Print per-block
    print(f"  Per-block vs baseline:")
    for bid, fb in sorted(block_fb.items()):
        print(f"    {bid[:30]:<30} fixes={fb['fixes']} breaks={fb['breaks']} net={fb['net']}")

    print(f"  Always-All: {aa_avg:.3f}")
    print(f"  Oracle:     {oracle_avg:.3f} (coverage={oracle_coverage}/{n_samples})")

    return {
        "pool": pool_name,
        "n_blocks": len(blocks),
        "baseline": bl_avg,
        "oracle": oracle_avg,
        "oracle_coverage": oracle_coverage,
        "total_samples": n_samples,
        "always_all": aa_avg,
        "block_fix_break": block_fb,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="BitDPM v19 pool integration eval")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--output", type=str, default="experiments/reports")
    args = parser.parse_args()

    device = args.device or (
        "mps" if torch.backends.mps.is_available() else
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    os.makedirs(args.output, exist_ok=True)

    print(f"BitDPM v19: Pool Integration Evaluation")
    print(f"  Device: {device}")
    print(f"  Model:  {args.model}")

    # Load backbone
    backbone = BackboneModel(model_name=args.model, device=device, dtype=torch.float16)

    # Load v18 blocks
    v18_blocks = {}
    for bid in V18_ALL_SAFE:
        blk = load_v18_block(bid, torch.device(device))
        if blk is not None:
            v18_blocks[bid] = blk
    print(f"  Loaded {len(v18_blocks)} v18 blocks")

    # Define pools
    pools = []

    # v18 safe-only
    pools.append(("v18-safe-only", list(v18_blocks.values())))

    # v18 strong-three
    strong_blocks = [v18_blocks[bid] for bid in V18_STRONG_THREE if bid in v18_blocks]
    pools.append(("v18-strong-3", strong_blocks))

    # Run each pool
    results = []
    for name, blks in pools:
        result = evaluate_pool(backbone, blks, name, max_tokens=args.max_tokens)
        results.append(result)

    # Summary table
    print(f"\n{'='*70}")
    print("V19 POOL COMPARISON")
    print(f"{'='*70}")
    print(f"| {'Pool':<25} | {'Blocks':<7} | {'Baseline':<9} | {'Oracle':<8} | {'Coverage':<10} | {'AlwaysAll':<9} |")
    print(f"|{'-'*27}|{'-'*9}|{'-'*11}|{'-'*10}|{'-'*12}|{'-'*11}|")
    for r in results:
        print(f"| {r['pool']:<25} | {r['n_blocks']:<7} | {r['baseline']:<9.3f} | "
              f"{r['oracle']:<8.3f} | {r['oracle_coverage']}/{r['total_samples']:<6} | "
              f"{r['always_all']:<9.3f} |")

    # Unique fix analysis across blocks in each pool
    print(f"\n{'='*70}")
    print("PER-BLOCK FIX/BREAK DETAIL")
    print(f"{'='*70}")
    for r in results:
        print(f"\nPool: {r['pool']}")
        print(f"  {'Block':<35} {'Fixes':<7} {'Breaks':<8} {'Net':<5}")
        for bid, fb in sorted(r['block_fix_break'].items()):
            print(f"  {bid[:35]:<35} {fb['fixes']:<7} {fb['breaks']:<8} {fb['net']:<5}")

    # Save
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(args.output, f"v19_pool_eval_{ts}.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {path}")
    print(f"\nDone!")


if __name__ == "__main__":
    main()
