#!/usr/bin/env python3
"""Train all parameter blocks for BitDPM experiments.

Trains independent blocks on category-specific data (general, math, code, chinese)
and saves them to disk for later evaluation.

Usage:
    python scripts/train_all_blocks.py
    python scripts/train_all_blocks.py --model /path/to/model --epochs 5 --rank 8
    python scripts/train_all_blocks.py --quick  # 2 epochs, rank 4 for testing
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitdpm.models.backbone import BackboneModel
from bitdpm.train.train_blocks import (
    create_block_for_layer,
    save_block_with_metadata,
    train_block,
)


def build_block_plan(
    backbone: BackboneModel,
    categories: list[str],
    target_layers: list[int],
    target_modules: list[str],
    rank: int = 8,
    scale: float = 1.0,
    device: str = "cpu",
):
    """Build a plan of (category, block) pairs to train.

    One block per (category, layer, module) combination.
    """
    plan = []
    for cat in categories:
        for lid in target_layers:
            for mname in target_modules:
                lin = backbone.get_linear_layer(lid, mname)
                if lin is None:
                    print(f"  [Skip] {lid}/{mname} not found in backbone")
                    continue

                block_id = f"{cat}_l{lid}_{mname}"
                block = create_block_for_layer(
                    backbone=backbone,
                    layer_id=lid,
                    module_name=mname,
                    block_id=block_id,
                    block_type=cat,
                    rank=rank,
                    scale=scale,
                    device=device,
                )
                plan.append((cat, block))

    return plan


def run(args):
    device = args.device or (
        "cuda" if torch.cuda.is_available() else
        "mps" if torch.backends.mps.is_available() else "cpu"
    )
    print(f"[TrainAll] Device: {device}")
    print(f"[TrainAll] Model: {args.model}")

    os.makedirs(args.output_dir, exist_ok=True)

    # 1. Load backbone (use float32 for stable CPU training)
    backbone = BackboneModel(
        model_name=args.model,
        device=device,
        dtype=torch.float32,  # Use float32 for training stability
        source=args.source,
    )
    device = backbone.device
    print(f"[TrainAll] Effective device: {device}")

    # 2. Build block plan
    num_layers = backbone.num_hidden_layers
    target_layers = list(range(max(0, num_layers - args.num_layers), num_layers))
    target_modules = args.modules
    categories = args.categories

    print(f"\n[TrainAll] Block training plan:")
    print(f"  Categories: {categories}")
    print(f"  Layers: {target_layers}")
    print(f"  Modules: {target_modules}")
    print(f"  Rank: {args.rank}")
    print(f"  Epochs per block: {args.epochs}")

    plan = build_block_plan(
        backbone, categories, target_layers, target_modules,
        rank=args.rank, scale=args.scale, device=device,
    )
    print(f"\n[TrainAll] Total blocks to train: {len(plan)}")

    if len(plan) == 0:
        print("[TrainAll] No blocks to train! Check layer/module names.")
        return

    # Save plan metadata
    plan_path = os.path.join(args.output_dir, "training_plan.json")
    with open(plan_path, "w") as f:
        json.dump({
            "model": args.model,
            "categories": categories,
            "target_layers": target_layers,
            "target_modules": target_modules,
            "rank": args.rank,
            "epochs": args.epochs,
            "num_blocks": len(plan),
            "device": device,
        }, f, indent=2)
    print(f"\n  Plan saved: {plan_path}")

    # 3. Train each block
    all_metrics = []
    total_start = time.time()

    for i, (category, block) in enumerate(plan):
        print(f"\n{'='*70}")
        print(f"Block {i+1}/{len(plan)}: [{category}] {block.block_id}")
        print(f"{'='*70}")

        metrics = train_block(
            backbone=backbone,
            block=block,
            category=category,
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            max_length=args.max_length,
            device=device,
            log_interval=5,
            num_augmented=args.num_augmented,
        )
        all_metrics.append(metrics)

        # Save block immediately
        save_block_with_metadata(block, metrics, args.output_dir)

    total_time = time.time() - total_start

    # 4. Summary
    print(f"\n{'='*70}")
    print(f"TRAINING COMPLETE")
    print(f"{'='*70}")
    print(f"  Total blocks: {len(all_metrics)}")
    print(f"  Total time: {total_time:.1f}s")
    print(f"  Output: {args.output_dir}")
    print()

    # Summary table
    print(f"| {'Block':<30} | {'Category':<10} | {'Loss':<8} | {'Time(s)':<8} |")
    print(f"|{'-'*32}|{'-'*12}|{'-'*10}|{'-'*10}|")
    for m in all_metrics:
        print(f"| {m.block_id:<30} | {m.category:<10} | {m.best_loss:<8.4f} | {m.training_time_s:<8.1f} |")

    # Save metadata summary
    summary_path = os.path.join(args.output_dir, "training_summary.json")
    with open(summary_path, "w") as f:
        json.dump([{
            "block_id": m.block_id,
            "category": m.category,
            "layer_id": m.layer_id,
            "module_name": m.module_name,
            "rank": m.rank,
            "final_loss": m.final_loss,
            "best_loss": m.best_loss,
            "epochs": m.epochs,
            "training_time_s": m.training_time_s,
        } for m in all_metrics], f, indent=2)
    print(f"\n  Summary saved: {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="Train all BitDPM parameter blocks")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct",
                        help="Model name or local path")
    parser.add_argument("--output-dir", type=str, default="experiments/outputs/blocks",
                        help="Directory to save trained blocks")
    parser.add_argument("--device", type=str, default="",
                        help="Device: cpu, cuda, mps (auto-detect)")
    parser.add_argument("--source", type=str, default="auto",
                        choices=["auto", "hf", "modelscope"],
                        help="Model download source")

    # Block configuration
    parser.add_argument("--categories", type=str, nargs="+",
                        default=["general", "math", "code", "chinese"],
                        help="Block categories to train")
    parser.add_argument("--modules", type=str, nargs="+",
                        default=["o_proj", "down_proj"],
                        help="Target module names")
    parser.add_argument("--num-layers", type=int, default=2,
                        help="Number of last layers to target (default: 2)")
    parser.add_argument("--rank", type=int, default=8,
                        help="LoRA rank (default: 8)")
    parser.add_argument("--scale", type=float, default=1.0,
                        help="Block scale (default: 1.0)")

    # Training hyperparameters
    parser.add_argument("--epochs", type=int, default=3,
                        help="Training epochs per block (default: 3)")
    parser.add_argument("--batch-size", type=int, default=1,
                        help="Batch size (default: 1)")
    parser.add_argument("--lr", type=float, default=2e-4,
                        help="Learning rate (default: 2e-4)")
    parser.add_argument("--max-length", type=int, default=64,
                        help="Max sequence length (default: 64)")
    parser.add_argument("--num-augmented", type=int, default=3,
                        help="Number of augmented prompts per topic (default: 3)")

    # Quick mode
    parser.add_argument("--quick", action="store_true",
                        help="Quick test: 2 epochs, rank 4, 1 category")

    args = parser.parse_args()

    if args.quick:
        args.epochs = 2
        args.rank = 4
        args.categories = ["general"]
        args.num_layers = 1
        args.max_length = 32

    run(args)


if __name__ == "__main__":
    main()
