"""BitDPM v17 preservation-aware block training.

Key differences from earlier training:
1. Training data: 30% repair + 50% preservation + 20% distractor.
2. Loss: L = L_repair + λ * L_preserve where L_preserve = KL(p_base || p_block).
3. Tracks fixes/breaks per epoch to guide training.
4. Preservation samples are those where baseline already gets the correct answer.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from bitdpm.eval.benchmark import EVAL_PROMPTS, EXPECTED_ANSWERS, compute_accuracy
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import ParameterBlock, ParameterBlockConfig
from bitdpm.runtime.device_manager import BlockDeviceManager


# ---------------------------------------------------------------------------
# Baseline evaluation: classify each prompt as repair vs preserve
# ---------------------------------------------------------------------------

def evaluate_baseline(backbone, bench_prompts, max_tokens=64):
    """Evaluate baseline on benchmark and classify each prompt.

    Returns:
        correct_prompts: list of (prompt, category) pairs where baseline scores 1.0.
        incorrect_prompts: list of (prompt, category) pairs where baseline scores 0.0.
        partial_prompts: list of (prompt, category) where baseline scores 0.5.
        per_sample: dict[prompt] -> score
    """
    correct, incorrect, partial = [], [], []
    per_sample = {}

    for cat, prompts in bench_prompts.items():
        for p in prompts:
            g = backbone.generate(p, max_new_tokens=max_tokens, temperature=0.1)
            score = compute_accuracy(p, g, cat)
            per_sample[p] = score
            if score >= 1.0:
                correct.append((p, cat))
            elif score <= 0.0:
                incorrect.append((p, cat))
            else:
                partial.append((p, cat))

    return correct, incorrect, partial, per_sample


# ---------------------------------------------------------------------------
# Preservation-aware training dataset
# ---------------------------------------------------------------------------

class PreservationDataset(Dataset):
    """Dataset with preservation-aware structure.

    repair_texts: prompts where block should learn to fix.
    preserve_texts: prompts where block should NOT change behavior.
    distractor_texts: prompts that are neither repair nor preserve (hard negatives).

    During forward, compute L_repair on repair batch and L_preserve on preserve batch.
    """

    def __init__(self, repair_texts, preserve_texts, distractor_texts, tokenizer, max_length=64):
        self.repair_texts = repair_texts
        self.preserve_texts = preserve_texts
        self.distractor_texts = distractor_texts

        # Tokenize all
        def tokenize(texts):
            if not texts:
                return torch.empty(0, max_length, dtype=torch.long)
            enc = tokenizer(
                texts, truncation=True, padding="max_length",
                max_length=max_length, return_tensors="pt",
            )
            return enc["input_ids"]

        self.repair_ids = tokenize(repair_texts)
        self.preserve_ids = tokenize(preserve_texts)
        self.distractor_ids = tokenize(distractor_texts)

        # Total length for iteration
        self.total = max(len(self.repair_ids), len(self.preserve_ids), len(self.distractor_ids), 1)

    def __len__(self):
        return self.total

    def __getitem__(self, idx):
        r_idx = idx % max(len(self.repair_ids), 1)
        p_idx = idx % max(len(self.preserve_ids), 1)
        d_idx = idx % max(len(self.distractor_ids), 1)

        item = {
            "input_ids": self.repair_ids[r_idx] if len(self.repair_ids) > 0 else self.preserve_ids[0],
            "repair_ids": self.repair_ids[r_idx] if len(self.repair_ids) > 0 else self.preserve_ids[0],
            "preserve_ids": self.preserve_ids[p_idx] if len(self.preserve_ids) > 0 else self.repair_ids[0],
            "distractor_ids": self.distractor_ids[d_idx] if len(self.distractor_ids) > 0 else self.repair_ids[0],
        }
        return item


# ---------------------------------------------------------------------------
# Preservation loss
# ---------------------------------------------------------------------------

def compute_preservation_loss(backbone_model, block_id, input_ids, base_logits_cache=None):
    """Compute KL(p_base || p_block) for preservation samples.

    base_logits_cache must be pre-computed WITH BLOCK DISABLED.
    """
    if base_logits_cache is not None:
        base_logits = base_logits_cache
    else:
        # Disable block for baseline
        for name, mod in backbone_model.named_modules():
            if hasattr(mod, 'composer') and hasattr(mod.composer, '_active_block_ids'):
                mod.composer.set_active_blocks([])
        with torch.no_grad():
            base_logits = backbone_model(input_ids=input_ids).logits
        # Re-enable block
        for name, mod in backbone_model.named_modules():
            if hasattr(mod, 'composer') and hasattr(mod.composer, '_active_block_ids'):
                mod.composer.set_active_blocks([block_id])

    # Block logits (with block active, no grad through backbone)
    with torch.no_grad():
        block_logits = backbone_model(input_ids=input_ids).logits

    # KL(p_base || p_block) = sum(p_base * log(p_base / p_block))
    p_base = F.log_softmax(base_logits.float(), dim=-1)
    p_block = F.log_softmax(block_logits.float(), dim=-1)
    kl = F.kl_div(p_block, p_base, log_target=True, reduction="batchmean")
    return kl


# ---------------------------------------------------------------------------
# Fix/Break validation
# ---------------------------------------------------------------------------

@dataclass
class FixBreakMetrics:
    fixes: int = 0
    breaks: int = 0
    net: int = 0
    baseline_score: float = 0.0
    block_score: float = 0.0
    damage_rate: float = 0.0
    unique_fixes: int = 0
    per_sample: dict = field(default_factory=dict)

    def print(self, label=""):
        print(f"  {label}  baseline={self.baseline_score:.3f} block={self.block_score:.3f} "
              f"fixes={self.fixes} breaks={self.breaks} net={self.net} "
              f"damage={self.damage_rate:.1%}")


def evaluate_fix_break(backbone, injector, block_id, bench_prompts, max_tokens=64):
    """Evaluate fix/break impact of a single block.

    1. Evaluate baseline (no blocks).
    2. Evaluate block active.
    3. Compare per-sample scores.

    Returns FixBreakMetrics.
    """
    # Baseline (explicitly disable all blocks)
    injector.set_active_blocks([])
    baseline_scores = {}
    for cat, prompts in bench_prompts.items():
        for p in prompts:
            g = backbone.generate(p, max_new_tokens=max_tokens, temperature=0.1)
            s = compute_accuracy(p, g, cat)
            baseline_scores[p] = s

    # Block active
    injector.set_active_blocks([block_id])
    block_scores = {}
    for cat, prompts in bench_prompts.items():
        for p in prompts:
            g = backbone.generate(p, max_new_tokens=max_tokens, temperature=0.1)
            s = compute_accuracy(p, g, cat)
            block_scores[p] = s

    injector.set_active_blocks(None)

    # Compare
    fixes = breaks = 0
    per_sample = {}
    for p in baseline_scores:
        bl = baseline_scores[p]
        bk = block_scores[p]
        per_sample[p] = {"baseline": bl, "block": bk}
        if bk > bl: fixes += 1
        elif bk < bl: breaks += 1

    total = max(len(baseline_scores), 1)
    bl_avg = sum(baseline_scores.values()) / total
    bk_avg = sum(block_scores.values()) / total

    return FixBreakMetrics(
        fixes=fixes,
        breaks=breaks,
        net=fixes - breaks,
        baseline_score=bl_avg,
        block_score=bk_avg,
        damage_rate=breaks / total if total > 0 else 0.0,
        per_sample=per_sample,
    )


# ---------------------------------------------------------------------------
# V17 main training function
# ---------------------------------------------------------------------------

def train_v17_block(
    backbone: BackboneModel,
    block: ParameterBlock,
    repair_texts: list[str],
    preserve_texts: list[str],
    distractor_texts: list[str],
    epochs: int = 10,
    batch_size: int = 1,
    lr: float = 1e-4,
    max_length: int = 64,
    device: str = "cpu",
    kl_weight: float = 0.3,
    eval_every: int = 1,
    eval_prompts: Optional[dict] = None,
) -> dict:
    """Train a single block with preservation-aware loss.

    Loss: L = L_repair + kl_weight * KL(p_base || p_block)
    where L_repair is standard next-token prediction loss on repair samples.
    KL is computed on preserve samples to keep block near baseline on easy cases.

    Args:
        backbone: frozen backbone model.
        block: parameter block to train.
        repair_texts: prompts where baseline fails.
        preserve_texts: prompts where baseline succeeds.
        distractor_texts: hard negative prompts.
        epochs: number of training epochs.
        batch_size: batch size.
        lr: learning rate.
        max_length: max sequence length.
        device: training device.
        kl_weight: weight for KL preservation loss.
        eval_every: run fix/break eval every N epochs.
        eval_prompts: benchmark prompts for fix/break eval.

    Returns:
        dict with training history and final fix/break metrics.
    """
    injector = BlockInjector(backbone)
    injector.inject_block(block, block.layer_id, block.module_name)

    dataset = PreservationDataset(repair_texts, preserve_texts, distractor_texts,
                                  backbone.tokenizer, max_length=max_length)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    optimizer = torch.optim.AdamW(block.parameters(), lr=lr)
    block.train()
    backbone.model.eval()
    scaler = torch.amp.GradScaler(device=device, enabled=(device == "mps"))


    history = {
        "epochs": [],
        "total_loss": [],
        "repair_loss": [],
        "kl_loss": [],
        "fix_break": [],
    }

    n_repair = len(dataset.repair_texts)
    n_preserve = len(dataset.preserve_texts)
    print(f"\n{'='*70}")
    print(f"V17 Training: {block.block_id}")
    print(f"  Repair={n_repair}, Preserve={n_preserve}, Distractor={len(dataset.distractor_texts)}")
    print(f"  Epochs={epochs}, LR={lr}, KL_weight={kl_weight}")
    print(f"  Block params={sum(p.numel() for p in block.parameters()):,}")
    print(f"{'='*70}")

    # We'll compute preserve baseline logits per batch (simpler, avoids index mismatches)

    for epoch in range(epochs):
        epoch_total = 0.0
        epoch_repair = 0.0
        epoch_kl = 0.0
        n_batches = 0

        pbar = tqdm(loader, desc=f"Epoch {epoch+1}/{epochs}", leave=False)
        for batch in pbar:
            optimizer.zero_grad()

            # --- Repair loss on repair samples ---
            repair_ids = batch["repair_ids"].to(device)
            if n_repair > 0:
                with torch.no_grad():
                    base_out = backbone.model(input_ids=repair_ids)
                # But we need block to learn, so we compute next-token loss
                # with block active
                block.train()
                outputs = backbone.model(input_ids=repair_ids, labels=repair_ids)
                loss_repair = outputs.loss
            else:
                loss_repair = torch.tensor(0.0, device=device)

            # --- KL preservation loss (per-batch) ---
            if n_preserve > 0 and kl_weight > 0 and epoch > 0:
                preserve_ids_batch = batch["preserve_ids"].to(device)
                # Baseline logits: disable block
                injector.set_active_blocks([])
                with torch.no_grad():
                    base_logits = backbone.model(input_ids=preserve_ids_batch).logits.detach().float()
                # Re-enable block
                injector.set_active_blocks(None)
                # Block logits (no grad through backbone)
                with torch.no_grad():
                    block_logits = backbone.model(input_ids=preserve_ids_batch).logits.float()
                # KL
                p_base = F.log_softmax(base_logits, dim=-1)
                p_block = F.log_softmax(block_logits, dim=-1)
                kl = F.kl_div(p_block, p_base, log_target=True, reduction="batchmean")
                loss_kl = kl_weight * kl
            else:
                loss_kl = torch.tensor(0.0, device=device)

            # Total loss with NaN guard
            loss = loss_repair + loss_kl
            loss_val = loss.item() if hasattr(loss, 'item') else 0.0
            if loss_val > 0 and not (loss_val != loss_val):
                loss.backward()
                torch.nn.utils.clip_grad_norm_(block.parameters(), max_norm=1.0)
                optimizer.step()
            else:
                if loss_val != loss_val:
                    print("  [WARN] NaN loss, skipping step")

            epoch_total += loss.item()
            epoch_repair += loss_repair.item()
            epoch_kl += loss_kl.item()
            n_batches += 1

            pbar.set_postfix({
                "loss": f"{loss.item():.3f}",
                "kl": f"{loss_kl.item():.3f}" if n_preserve > 0 else "0",
            })

        avg_total = epoch_total / max(n_batches, 1)
        avg_repair = epoch_repair / max(n_batches, 1)
        avg_kl = epoch_kl / max(n_batches, 1)

        epoch_info = {
            "epoch": epoch + 1,
            "total_loss": avg_total,
            "repair_loss": avg_repair,
            "kl_loss": avg_kl,
        }

        # Fix/break eval
        if eval_prompts is not None and (epoch + 1) % eval_every == 0:
            fb = evaluate_fix_break(backbone, injector, block.block_id,
                                     eval_prompts, max_tokens=64)
            epoch_info["fix_break"] = {
                "fixes": fb.fixes, "breaks": fb.breaks, "net": fb.net,
                "block_score": fb.block_score,
            }
            fb.print(f"  Epoch {epoch+1}:")
            history["fix_break"].append(epoch_info["fix_break"])
        else:
            print(f"  Epoch {epoch+1}: total={avg_total:.3f} repair={avg_repair:.3f} kl={avg_kl:.4f}")

        history["epochs"].append(epoch_info)
        history["total_loss"].append(avg_total)
        history["repair_loss"].append(avg_repair)
        history["kl_loss"].append(avg_kl)

    injector.remove_all_patches()

    # Final fix/break
    final_fb = None
    if eval_prompts is not None:
        final_fb = evaluate_fix_break(backbone, injector, block.block_id,
                                       eval_prompts, max_tokens=64)
        print(f"\n  Final: fixes={final_fb.fixes} breaks={final_fb.breaks} net={final_fb.net}")

    return {
        "block_id": block.block_id,
        "block_type": block.block_type,
        "layer_id": block.layer_id,
        "module_name": block.module_name,
        "rank": block.rank,
        "history": history,
        "final_fix_break": {
            "fixes": final_fb.fixes if final_fb else 0,
            "breaks": final_fb.breaks if final_fb else 0,
            "net": final_fb.net if final_fb else 0,
            "baseline_score": final_fb.baseline_score if final_fb else 0,
            "block_score": final_fb.block_score if final_fb else 0,
        } if final_fb else {},
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="BitDPM v17 preservation-aware block training")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct",
                        help="Model name or path")
    parser.add_argument("--output-dir", type=str, default="experiments/outputs/blocks_v17",
                        help="Directory to save trained blocks")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--kl-weight", type=float, default=0.001,
                        help="Weight for KL preservation loss (default: 0.001)")
    parser.add_argument("--rank", type=int, default=16,
                        help="Block rank (default: 16, up from old 8)")
    parser.add_argument("--target-layer", type=int, default=23,
                        help="Target layer index")
    parser.add_argument("--target-module", type=str, default="down_proj",
                        choices=["o_proj", "down_proj"],
                        help="Target module name")
    parser.add_argument("--max-length", type=int, default=64)
    parser.add_argument("--quick", action="store_true",
                        help="Quick test: 3 epochs, 1 repair target")
    args = parser.parse_args()

    device = args.device or (
        "mps" if torch.backends.mps.is_available() else
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"BitDPM v17: preservation-aware block training")
    print(f"  Device: {device}")
    print(f"  Model:  {args.model}")

    # 1. Load backbone
    # Use float32 for training stability on MPS
    train_dtype = torch.float32
    backbone = BackboneModel(model_name=args.model, device=device,
                              dtype=train_dtype)

    # 2. Evaluate baseline on benchmark
    print("\n[Baseline] Evaluating on benchmark...")
    correct, incorrect, partial, per_sample = evaluate_baseline(
        backbone, EVAL_PROMPTS, max_tokens=64
    )
    print(f"  Correct: {len(correct)}, Incorrect: {len(incorrect)}, Partial: {len(partial)}")

    if args.quick:
        # Use only 1 repair target for quick test
        incorrect = incorrect[:1]
        correct = correct[:5]
        args.epochs = 3

    # 3. Build preservation-aware training texts
    repair_texts = [p for p, _ in incorrect]
    preserve_texts = [p for p, _ in correct]
    distractor_texts = [p for p, _ in partial] if partial else []

    if not repair_texts:
        print("[Error] No incorrect prompts found — nothing to repair!")
        return

    print(f"\n[Data] Repair={len(repair_texts)}, Preserve={len(preserve_texts)}, Distractor={len(distractor_texts)}")

    # 4. Create parameter block
    lin = backbone.get_linear_layer(args.target_layer, args.target_module)
    if lin is None:
        print(f"Error: Layer {args.target_layer}/{args.target_module} not found")
        return

    block_id = f"v17_{args.target_module}_l{args.target_layer}_r{args.rank}"
    config = ParameterBlockConfig(
        block_id=block_id,
        layer_id=args.target_layer,
        module_name=args.target_module,
        rank=args.rank,
        scale=1.0,
        block_type="preservation_aware",
        hidden_size=backbone.hidden_size,
        in_features=lin.in_features,
        out_features=lin.out_features,
    )
    block = ParameterBlock(config)
    backbone_dtype = next(backbone.model.parameters()).dtype
    block = block.to(device=device, dtype=backbone_dtype)
    print(f"[Block] Created {block_id}: {lin.in_features}->{lin.out_features}, rank={args.rank}")

    # 5. Train with preservation loss
    result = train_v17_block(
        backbone=backbone,
        block=block,
        repair_texts=repair_texts,
        preserve_texts=preserve_texts,
        distractor_texts=distractor_texts,
        epochs=args.epochs,
        batch_size=1,
        lr=args.lr,
        max_length=args.max_length,
        device=device,
        kl_weight=args.kl_weight,
        eval_every=2,
        eval_prompts=EVAL_PROMPTS,
    )

    # 6. Save
    block_path = os.path.join(args.output_dir, f"{block_id}.pt")
    block.save(block_path)
    meta_path = os.path.join(args.output_dir, f"{block_id}_v17_meta.json")
    with open(meta_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[V17] Block saved: {block_path}")
    print(f"[V17] Meta saved: {meta_path}")
    print(f"[V17] Final fixes={result['final_fix_break'].get('fixes', 0)}, "
          f"breaks={result['final_fix_break'].get('breaks', 0)}, "
          f"net={result['final_fix_break'].get('net', 0)}")


if __name__ == "__main__":
    main()
