#!/usr/bin/env python3
"""BitDPM v0.7: train utility-coverage parameter blocks.

This script trains blocks from curated answer-bearing datasets and structure
plans designed for utility coverage expansion:

- hard-sample blocks: target benchmark-like misses.
- error-type blocks: target failure mechanisms instead of broad task domains.
- structure blocks: compare single-layer and contiguous FFN placements.

Examples:
    BITDPM_FORCE_CPU=1 python scripts/train_v07_blocks.py \
      --output-dir experiments/outputs/blocks_v07_hard_l23_down \
      --datasets hard_math hard_commonsense \
      --structure l23_down --rank 8 --epochs 5

    BITDPM_FORCE_CPU=1 python scripts/train_v07_blocks.py \
      --output-dir experiments/outputs/blocks_v07_error_l23_down \
      --datasets calculation_error commonsense_choice format_following chinese_semantic short_reasoning \
      --structure l23_down --rank 8 --epochs 5

    BITDPM_FORCE_CPU=1 python scripts/train_v07_blocks.py \
      --output-dir experiments/outputs/blocks_v07_hard_l22_l24_down \
      --datasets hard_math hard_commonsense \
      --structure l22_l24_down --rank 8 --epochs 5
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitdpm.models.backbone import BackboneModel
from bitdpm.params.parameter_block import ParameterBlock
from bitdpm.train.train_blocks import create_block_for_layer, save_block_with_metadata, train_block
from bitdpm.train.v07_data import get_v07_data, list_v07_categories


@dataclass
class BlockPlanItem:
    dataset: str
    layer_id: int
    module_name: str
    sample_count: int


def resolve_structure(
    structure: str,
    num_layers: int,
    custom_layers: list[int],
    custom_modules: list[str],
) -> tuple[list[int], list[str]]:
    """Resolve a named structure into zero-based layer ids and module names."""
    final_layer = num_layers - 1
    if structure == "l23_down":
        return [final_layer], ["down_proj"]
    if structure == "l22_l24_down":
        return list(range(max(0, num_layers - 3), num_layers)), ["down_proj"]
    if structure == "l23_ffn":
        return [final_layer], ["up_proj", "down_proj"]
    if structure == "l21_l24_ffn":
        return list(range(max(0, num_layers - 4), num_layers)), ["gate_proj", "up_proj", "down_proj"]
    if structure == "custom":
        if not custom_layers:
            raise ValueError("--layers is required when --structure custom")
        if not custom_modules:
            raise ValueError("--modules is required when --structure custom")
        return custom_layers, custom_modules
    raise ValueError(f"Unknown structure: {structure}")


def build_plan(
    backbone: BackboneModel,
    datasets: list[str],
    layers: list[int],
    modules: list[str],
) -> list[BlockPlanItem]:
    plan: list[BlockPlanItem] = []
    for dataset in datasets:
        texts = get_v07_data(dataset)
        for layer_id in layers:
            for module_name in modules:
                if backbone.get_linear_layer(layer_id, module_name) is None:
                    print(f"  [Skip] l{layer_id}/{module_name} not found")
                    continue
                plan.append(
                    BlockPlanItem(
                        dataset=dataset,
                        layer_id=layer_id,
                        module_name=module_name,
                        sample_count=len(texts),
                    )
                )
    return plan


def create_plan_block(
    backbone: BackboneModel,
    item: BlockPlanItem,
    rank: int,
    scale: float,
    device: str,
) -> ParameterBlock:
    block_id = f"{item.dataset}_l{item.layer_id}_{item.module_name}"
    return create_block_for_layer(
        backbone=backbone,
        layer_id=item.layer_id,
        module_name=item.module_name,
        block_id=block_id,
        block_type=item.dataset,
        rank=rank,
        scale=scale,
        device=device,
    )


def run(args):
    if args.device == "cpu":
        os.environ.setdefault("BITDPM_FORCE_CPU", "1")

    requested_device = args.device or (
        "cuda" if torch.cuda.is_available() else
        "mps" if torch.backends.mps.is_available() else "cpu"
    )
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"{'='*70}")
    print("BitDPM v0.7 Utility Coverage Block Training")
    print(f"{'='*70}")
    print(f"  Model: {args.model}")
    print(f"  Requested device: {requested_device}")
    print(f"  Output: {args.output_dir}")

    backbone = BackboneModel(
        model_name=args.model,
        device=requested_device,
        dtype=torch.float32,
        source=args.source,
    )
    device = backbone.device
    print(f"  Effective device: {device}")

    layers, modules = resolve_structure(args.structure, backbone.num_hidden_layers, args.layers, args.modules)
    datasets = args.datasets

    print("\n[Plan]")
    print(f"  Datasets: {datasets}")
    print(f"  Structure: {args.structure}")
    print(f"  Layers: {layers}")
    print(f"  Modules: {modules}")
    print(f"  Rank: {args.rank}")
    print(f"  Scale: {args.scale}")
    print(f"  Epochs: {args.epochs}")

    plan = build_plan(backbone, datasets, layers, modules)
    if not plan:
        print("[v0.7] No blocks to train. Check layer/module names.")
        return

    plan_path = os.path.join(args.output_dir, "training_plan.json")
    with open(plan_path, "w") as f:
        json.dump(
            {
                "model": args.model,
                "source": args.source,
                "device": str(device),
                "structure": args.structure,
                "datasets": datasets,
                "layers": layers,
                "modules": modules,
                "rank": args.rank,
                "scale": args.scale,
                "epochs": args.epochs,
                "batch_size": args.batch_size,
                "lr": args.lr,
                "max_length": args.max_length,
                "num_blocks": len(plan),
                "plan": [asdict(item) for item in plan],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"  Plan saved: {plan_path}")
    print(f"  Total blocks: {len(plan)}")

    all_metrics = []
    total_start = time.time()
    for idx, item in enumerate(plan, start=1):
        print(f"\n{'='*70}")
        print(f"Block {idx}/{len(plan)}: [{item.dataset}] l{item.layer_id}/{item.module_name}")
        print(f"{'='*70}")

        block = create_plan_block(backbone, item, args.rank, args.scale, str(device))
        texts = get_v07_data(item.dataset)
        metrics = train_block(
            backbone=backbone,
            block=block,
            category=item.dataset,
            texts=texts,
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            max_length=args.max_length,
            device=str(device),
            log_interval=args.log_interval,
            num_augmented=0,
        )
        all_metrics.append(metrics)
        save_block_with_metadata(block, metrics, args.output_dir)

    total_time = time.time() - total_start
    summary_path = os.path.join(args.output_dir, "training_summary.json")
    with open(summary_path, "w") as f:
        json.dump(
            [
                {
                    "block_id": m.block_id,
                    "dataset": m.category,
                    "layer_id": m.layer_id,
                    "module_name": m.module_name,
                    "rank": m.rank,
                    "final_loss": m.final_loss,
                    "best_loss": m.best_loss,
                    "epochs": m.epochs,
                    "total_steps": m.total_steps,
                    "training_time_s": m.training_time_s,
                }
                for m in all_metrics
            ],
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\n{'='*70}")
    print("v0.7 TRAINING COMPLETE")
    print(f"{'='*70}")
    print(f"  Blocks: {len(all_metrics)}")
    print(f"  Total time: {total_time:.1f}s")
    print(f"  Output: {args.output_dir}")
    print(f"  Summary saved: {summary_path}")
    print()
    print(f"| {'Block':<42} | {'Dataset':<20} | {'Loss':<8} |")
    print(f"|{'-'*44}|{'-'*22}|{'-'*10}|")
    for m in all_metrics:
        print(f"| {m.block_id:<42} | {m.category:<20} | {m.best_loss:<8.4f} |")


def main():
    parser = argparse.ArgumentParser(description="Train BitDPM v0.7 utility coverage blocks")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--output-dir", type=str, default="experiments/outputs/blocks_v07")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--source", type=str, default="auto")

    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["hard_math", "hard_commonsense"],
        choices=list_v07_categories(),
        help="v0.7 datasets to train",
    )
    parser.add_argument(
        "--structure",
        choices=["l23_down", "l22_l24_down", "l23_ffn", "l21_l24_ffn", "custom"],
        default="l23_down",
        help="Named block placement plan. Names follow the v0.6 final-layer convention.",
    )
    parser.add_argument("--layers", nargs="+", type=int, default=[], help="Zero-based layers for custom structure")
    parser.add_argument("--modules", nargs="+", default=[], help="Modules for custom structure")
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--scale", type=float, default=1.0)

    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-length", type=int, default=96)
    parser.add_argument("--log-interval", type=int, default=5)
    parser.add_argument("--quick", action="store_true")

    args = parser.parse_args()
    if args.quick:
        args.datasets = ["hard_math"]
        args.structure = "l23_down"
        args.epochs = 1
        args.rank = 4
        args.max_length = 64

    run(args)


if __name__ == "__main__":
    main()
