#!/usr/bin/env python3
"""Train and evaluate a single parameter block.

This script demonstrates:
1. Creating a single ParameterBlock for a target layer
2. Freezing the backbone
3. Training only the block's A/B matrices on a specific dataset
4. Evaluating before/after

Usage:
    python scripts/run_single_block.py --model Qwen/Qwen2.5-0.5B-Instruct
    python scripts/run_single_block.py --model Qwen/Qwen2.5-0.5B-Instruct --train
"""

from __future__ import annotations

import argparse
import os
import time

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer

from bitdpm.eval.benchmark import format_benchmark_table, run_benchmark, save_benchmark_results
from bitdpm.eval.latency import measure_generate_latency
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import ParameterBlock, ParameterBlockConfig

TRAIN_PROMPTS = [
    "What is the capital of France?",
    "Explain quantum computing in simple terms.",
    "Write a short poem about AI.",
    "What are the benefits of exercise?",
    "Describe the water cycle.",
    "What is machine learning?",
    "How does GPS work?",
    "Tell me about the solar system.",
    "What is photosynthesis?",
    "Explain the theory of relativity.",
]


class SimpleTextDataset(Dataset):
    """Minimal text dataset for block training."""

    def __init__(self, texts, tokenizer, max_length=64):
        self.encodings = tokenizer(
            texts,
            truncation=True,
            padding="max_length",
            max_length=max_length,
            return_tensors="pt",
        )

    def __len__(self):
        return len(self.encodings.input_ids)

    def __getitem__(self, idx):
        return {
            "input_ids": self.encodings.input_ids[idx],
            "attention_mask": self.encodings.attention_mask[idx],
            "labels": self.encodings.input_ids[idx],  # Language modeling objective
        }


def run(args):
    device = args.device or ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[SingleBlock] Device: {device}")
    print(f"[SingleBlock] Model: {args.model}")

    # 1. Load backbone
    model = BackboneModel(
        model_name=args.model,
        device=device,
        dtype=torch.float16,
        source=args.source,
    )

    # 2. Create a single parameter block
    target_layer = args.layer_id
    target_module = args.module_name
    lin = model.get_linear_layer(target_layer, target_module)
    if lin is None:
        print(f"Error: Linear layer {target_module} not found at layer {target_layer}")
        existing = model.get_layer_modules(target_layer)
        print(f"Available modules: {list(existing.keys())}")
        return

    config = ParameterBlockConfig(
        block_id=f"single_{target_module}_l{target_layer}",
        layer_id=target_layer,
        module_name=target_module,
        rank=args.rank,
        scale=1.0,
        block_type="general",
        hidden_size=model.hidden_size,
        in_features=lin.in_features,
        out_features=lin.out_features,
    )
    block = ParameterBlock(config).to(device)
    print(f"[SingleBlock] Created block: {block}")
    print(f"[SingleBlock] ΔW params: {sum(p.numel() for p in block.parameters()):,}")

    # 3. Inject block
    injector = BlockInjector(model)
    injector.inject_block(block, target_layer, target_module)
    print(f"[SingleBlock] Injected at layer {target_layer}, module {target_module}")

    # 4. Baseline evaluation (before training)
    if args.benchmark:
        print(f"\n{'='*60}")
        print("Baseline Evaluation (before training block)")
        print(f"{'='*60}")

        def gen_baseline(p: str) -> str:
            # Temporarily disable the patch
            key = (target_layer, target_module)
            if key in injector.patches:
                injector.patches[key].enabled = False
            result = model.generate(p, max_new_tokens=args.max_tokens, temperature=0.1)
            if key in injector.patches:
                injector.patches[key].enabled = True
            return result

        baseline_result = run_benchmark(gen_baseline, verbose=True)
        baseline_result.model_name = f"{args.model.split('/')[-1]}-baseline"
        baseline_result.quant = "FP16"
        baseline_result.num_params = f"{model.num_params()/1e9:.1f}B"
        baseline_result.device = device
        print(f"\nBaseline score: {baseline_result.overall_score:.3f}")

    # 5. Training the block
    if args.train:
        print(f"\n{'='*60}")
        print("Training parameter block...")
        print(f"{'='*60}")

        tokenizer = model.tokenizer

        # Training data
        dataset = SimpleTextDataset(TRAIN_PROMPTS, tokenizer, max_length=args.max_length)
        loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

        optimizer = torch.optim.AdamW(block.parameters(), lr=args.lr)

        block.train()
        num_steps = 0
        total_loss = 0.0
        loss_history = []

        for epoch in range(args.epochs):
            epoch_loss = 0.0
            for batch in loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels = batch["labels"].to(device)

                optimizer.zero_grad()

                # Forward through backbone with block active
                outputs = model.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )
                loss = outputs.loss
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()
                num_steps += 1
                total_loss += loss.item()

            avg_epoch_loss = epoch_loss / len(loader)
            loss_history.append(avg_epoch_loss)
            print(f"  Epoch {epoch + 1}/{args.epochs}: loss = {avg_epoch_loss:.4f}")

        # Save trained block
        if args.save_block:
            os.makedirs(os.path.dirname(args.save_block) or ".", exist_ok=True)
            block.save(args.save_block)
            print(f"[SingleBlock] Block saved to {args.save_block}")

    # 6. Post-training evaluation
    if args.benchmark and args.train:

        def gen_post(p: str) -> str:
            return model.generate(p, max_new_tokens=args.max_tokens, temperature=0.1)

        post_result = run_benchmark(gen_post, verbose=True)
        post_result.model_name = f"{args.model.split('/')[-1]}+single_block"
        post_result.quant = "FP16"
        post_result.num_params = f"{model.num_params()/1e9:.1f}B"
        post_result.device = device

        results = [baseline_result, post_result]
        print(f"\n{'='*60}")
        print("Comparison")
        print(f"{'='*60}")
        print(format_benchmark_table(results))

        if args.output:
            save_benchmark_results(results, args.output)

    print(f"\n[SingleBlock] Done.")


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate a single parameter block")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--layer-id", type=int, default=23,
                        help="Target layer index (default: 23, last layer for 0.5B)")
    parser.add_argument("--module-name", type=str, default="o_proj",
                        choices=["q_proj", "k_proj", "v_proj", "o_proj", "up_proj", "down_proj", "gate_proj"],
                        help="Target module name")
    parser.add_argument("--rank", type=int, default=8,
                        help="LoRA rank (default: 8)")
    parser.add_argument("--train", action="store_true",
                        help="Train the parameter block")
    parser.add_argument("--epochs", type=int, default=3,
                        help="Training epochs (default: 3)")
    parser.add_argument("--batch-size", type=int, default=2,
                        help="Training batch size (default: 2)")
    parser.add_argument("--lr", type=float, default=1e-3,
                        help="Learning rate (default: 1e-3)")
    parser.add_argument("--max-length", type=int, default=64,
                        help="Max sequence length for training (default: 64)")
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--benchmark", action="store_true",
                        help="Run before/after benchmark")
    parser.add_argument("--save-block", type=str, default="",
                        help="Save trained block to path")
    parser.add_argument("--output", type=str, default="",
                        help="Save benchmark results")
    parser.add_argument("--source", type=str, default="auto",
                        choices=["auto", "hf", "modelscope"],
                        help="Model download source: hf, modelscope, or auto (default: auto)")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
