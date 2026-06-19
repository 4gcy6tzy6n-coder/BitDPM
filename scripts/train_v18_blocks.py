"""BitDPM v18: Large-data block training + break-aware admission.

Key principles:
1. Train blocks with 500+ prompts per class (not 10-100).
2. Rank 16 for sufficient capacity with adequate data.
3. Post-training fix/break evaluation determines admission.
4. Admission: unique_fixes >= 1, net >= 0.

Usage:
    python scripts/train_v18_blocks.py
    python scripts/train_v18_blocks.py --quick  # 100 prompts, 3 epochs
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
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from bitdpm.eval.benchmark import EVAL_PROMPTS as BP, compute_accuracy
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import ParameterBlock, ParameterBlockConfig
from bitdpm.runtime.device_manager import BlockDeviceManager


# ---------------------------------------------------------------------------
# Large-scale training data per repair direction
# ---------------------------------------------------------------------------

REPAIR_DIRECTIONS: dict[str, dict] = {
    "power_log": {
        "templates": [
            "What is {} to the power of {}?",
            "Calculate {} to the power of {}",
            "What is {} squared?",
            "What is {} cubed?",
            "What is {}?",
            "Calculate {}",
            "Evaluate {}",
            "What is log base {} of {}?",
            "Compute the logarithm {} base {}",
            "Calculate {} * {}",
            "Multiply {} by {}",
            "What is {} divided by {}?",
            "Divide {} by {}",
        ],
        "fill": [
            ("2", "3"), ("2", "5"), ("2", "8"), ("2", "10"),
            ("3", "2"), ("3", "3"), ("3", "4"),
            ("4", "2"), ("5", "2"), ("6", "2"),
            ("5", "3"), ("7", "2"), ("9", "2"),
            ("10", "2"), ("10", "3"), ("10", "4"),
            ("10", "10"), ("10", "100"), ("10", "1000"),
            ("12", "2"), ("15", "2"), ("20", "2"),
            ("4 * 5", ""), ("6 * 7", ""), ("8 * 9", ""),
            ("12 * 11", ""), ("15 * 3", ""),
            ("100 / 4", ""), ("144 / 12", ""),
            ("250 / 5", ""), ("1000 / 8", ""),
            ("3^2", ""), ("4^3", ""), ("5^2", ""),
            ("2^10", ""), ("10^3", ""),
        ],
    },
    "distance_geometry": {
        "templates": [
            "What is the distance between ({}, {}) and ({}, {})?",
            "Calculate the distance from ({}, {}) to ({}, {})",
            "What is the area of a circle with radius {}?",
            "Calculate the area of a circle with radius {}",
            "What is the circumference of a circle with radius {}?",
            "What is the volume of a sphere with radius {}?",
            "Calculate the volume of a sphere with radius {}",
            "What is the area of a rectangle with length {} and width {}?",
            "What is the perimeter of a rectangle with length {} and width {}?",
            "What is the area of a triangle with base {} and height {}?",
            "What is the hypotenuse of a right triangle with legs {} and {}?",
            "What is the slope of the line through ({}, {}) and ({}, {})?",
            "What is the midpoint of ({}, {}) and ({}, {})?",
        ],
        "fill": [
            ("0", "0", "3", "4"), ("0", "0", "5", "12"), ("1", "2", "4", "6"),
            ("0", "0", "1", "1"), ("0", "0", "6", "8"),
            ("1", "1", "4", "5"), ("2", "3", "7", "15"),
            ("3", "7", "8", "12"),
            ("1", "", "", ""), ("2", "", "", ""), ("3", "", "", ""),
            ("5", "", "", ""), ("10", "", "", ""),
            ("3", "4", "", ""), ("6", "8", "", ""),
            ("3", "", "", ""), ("5", "", "", ""),
        ],
    },
    "percent": {
        "templates": [
            "What is {}% of {}?",
            "Calculate {}% of {}",
            "Find {}% of {}",
            "What percent of {} is {}?",
            "If {} is {}% of what number?",
            "A {}% increase of {} is what?",
            "A {}% decrease of {} is what?",
            "After a {}% discount, a ${} item costs what?",
            "With {}% tax on ${}, what is the total?",
            "If {} out of {} students passed, what percentage passed?",
        ],
        "fill": [
            ("10", "50"), ("20", "100"), ("25", "200"), ("50", "80"),
            ("15", "60"), ("30", "150"), ("5", "200"),
            ("75", "400"), ("12.5", "80"), ("33", "300"),
            ("40", "250"), ("8", "125"), ("60", "90"),
            ("25", "80"), ("10", "250"), ("90", "200"),
            ("80", "20", "25"), ("75", "15", "20"),
            ("15", "200", ""), ("10", "500", ""),
        ],
    },
    "factual_constants": {
        "templates": [
            "What is the speed of light?",
            "What is the speed of light in vacuum?",
            "What is the gravitational constant?",
            "What is Planck's constant?",
            "What is Avogadro's number?",
            "What is the charge of an electron?",
            "What is the mass of an electron?",
            "What is the mass of a proton?",
            "What is the boiling point of water?",
            "What is the freezing point of water?",
            "What is the density of water?",
            "What is the speed of sound in air?",
            "How far is the Earth from the Sun?",
            "What is the radius of Earth?",
            "What is the mass of Earth?",
            "What is the circumference of Earth?",
            "How many seconds are in a minute?",
            "How many minutes are in an hour?",
            "How many hours are in a day?",
            "How many days are in a year?",
            "How many centimeters are in a meter?",
            "How many meters are in a kilometer?",
            "What is the value of pi?",
            "What is the value of e?",
            "What is the atomic number of carbon?",
            "What is the atomic number of oxygen?",
            "What is the atomic number of hydrogen?",
            "What is the atomic number of gold?",
            "What is the chemical symbol for water?",
            "What is the chemical formula for carbon dioxide?",
            "What year did World War II end?",
            "What year did the Berlin Wall fall?",
            "When was the United Nations founded?",
            "When was the Declaration of Independence signed?",
            "Which planet is the largest in the solar system?",
            "Which planet is closest to the Sun?",
            "What is the most abundant gas in Earth's atmosphere?",
            "What is the human body temperature in Celsius?",
            "What is normal blood pressure?",
            "How many bones are in the adult human body?",
        ],
        "fill": [],  # No fill needed, all fully specified
    },
    "integer_ops": {
        "templates": [
            "What is {} + {}?",
            "Calculate {} + {}",
            "What is {} - {}?",
            "Calculate {} - {}",
            "What is {} * {}?",
            "Multiply {} by {}",
            "What is {} / {}?",
            "Divide {} by {}",
            "What is the remainder when {} is divided by {}?",
            "What is the GCD of {} and {}?",
            "What is the LCM of {} and {}?",
            "What is {} factorial?",
            "Calculate {}!",
            "What is the mean of {} and {}?",
            "What is the absolute value of {}?",
            "What is {}?",
            "Find {}",
            "Compute {}",
            "What is the sum of {} and {}?",
            "What is the product of {} and {}?",
        ],
        "fill": [
            ("15", "27"), ("34", "56"), ("128", "64"), ("256", "128"),
            ("1000", "500"), ("45", "35"), ("89", "11"), ("77", "33"),
            ("60", "45"), ("120", "80"),
            ("15", "7"), ("34", "12"), ("128", "64"), ("256", "128"),
            ("25", "18"), ("100", "37"), ("81", "9"), ("49", "14"),
            ("50", "4"), ("1000", "125"),
            ("12", "18"), ("24", "36"), ("7", "11"), ("15", "25"),
            ("8", "12"), ("30", "42"), ("9", "15"),
            ("5", ""), ("7", ""), ("10", ""),
        ],
    },
    "commonsense_choice": {
        "templates": [
            "What is the capital of France?",
            "What is the capital of Japan?",
            "What is the capital of Italy?",
            "What is the capital of Australia?",
            "What is the capital of Brazil?",
            "What is the capital of Egypt?",
            "What is the capital of Canada?",
            "What is the capital of South Korea?",
            "What is the largest continent?",
            "What is the largest ocean?",
            "What is the longest river in the world?",
            "What is the highest mountain in the world?",
            "Which animal lives in Antarctica?",
            "Which is the fastest land animal?",
            "Which is the largest animal in the world?",
            "What planet is known as the Red Planet?",
            "What is the smallest planet in our solar system?",
            "Which planet has the most moons?",
            "What is the chemical symbol for gold?",
            "What is the chemical symbol for iron?",
            "What is the chemical symbol for silver?",
            "Who was the first person on the Moon?",
            "Who invented the light bulb?",
            "Who wrote Hamlet?",
            "Who wrote 1984?",
            "Who was the first president of the United States?",
            "What did Marie Curie discover?",
            "What year did the Titanic sink?",
            "When did World War I begin?",
            "Which country has the largest population?",
            "Which country has the largest area?",
            "What is the official language of Brazil?",
            "What is the currency of Japan?",
            "What is the currency of the United Kingdom?",
            "How many legs does a spider have?",
            "How many teeth does an adult human have?",
        ],
        "fill": [],
    },
}


GENERAL_TEXTS = [
    "The capital of France is Paris.",
    "The sky appears blue because of Rayleigh scattering.",
    "Water boils at 100 degrees Celsius.",
    "A leap year has 366 days.",
    "The Pacific Ocean is the largest ocean on Earth.",
    "Mount Everest is the tallest mountain in the world.",
    "Photosynthesis converts sunlight into chemical energy.",
    "The speed of light is approximately 299,792,458 meters per second.",
    "Python is a high-level programming language.",
    "A function is a reusable block of code.",
    "A list in Python is an ordered collection of items.",
    "The Earth orbits the Sun once every 365.25 days.",
    "Gravity is a force that attracts objects toward each other.",
    "The human body has 206 bones.",
    "DNA contains genetic information.",
    "The Industrial Revolution began in the 18th century.",
    "Shakespeare wrote many famous plays and sonnets.",
    "The Amazon rainforest is the largest tropical rainforest.",
    "The chemical symbol for water is H2O.",
    "A magnet has a north pole and a south pole.",
    "Electricity flows through conductive materials.",
    "The Moon orbits the Earth approximately every 27 days.",
    "Sound travels faster in water than in air.",
    "The atomic number of carbon is 6.",
    "The Renaissance was a period of cultural rebirth in Europe.",
    "A triangle has three sides and three angles.",
    "The sum of angles in a triangle is 180 degrees.",
    "A square is a special type of rectangle.",
    "Multiplication is repeated addition.",
    "Division is the inverse of multiplication.",
]


def generate_training_texts(direction: str, num_augmented: int = 0) -> list[str]:
    """Generate diverse training prompts for a repair direction.

    num_augmented is ignored — always generates ALL template-fill combos
    to get 200+ prompts per direction. Then mixes in 50% general text.
    """
    direction_data = REPAIR_DIRECTIONS.get(direction)
    if direction_data is None:
        return []

    templates = direction_data["templates"]
    fills = direction_data.get("fill", [])

    texts: list[str] = []
    seen: set[str] = set()

    for tmpl in templates:
        n_placeholders = tmpl.count("{}")

        if n_placeholders == 0:
            if tmpl not in seen:
                texts.append(tmpl)
                seen.add(tmpl)
            continue

        # Use ALL fill values (no num_augmented cap)
        for fill in fills:
            if len(fill) < n_placeholders:
                continue
            try:
                if n_placeholders == 1:
                    prompt = tmpl.format(fill[0])
                elif n_placeholders == 2:
                    prompt = tmpl.format(fill[0], fill[1])
                elif n_placeholders == 4:
                    prompt = tmpl.format(fill[0], fill[1], fill[2], fill[3])
                else:
                    continue
            except (IndexError, KeyError):
                continue
            if prompt not in seen:
                texts.append(prompt)
                seen.add(prompt)

    # If less than 200, rotate fill values to generate more
    if len(texts) < 200 and len(fills) > 0:
        base_count = len(texts)
        rotation = 1
        while len(texts) < 200 and rotation < 20:
            n_placeholders_list = [t.count("{}") for t in templates]
            for ti, tmpl in enumerate(templates):
                if n_placeholders_list[ti] == 0:
                    continue
                for fi in range(len(fills)):
                    if len(texts) >= 200:
                        break
                    f = fills[fi]
                    if len(f) < n_placeholders_list[ti]:
                        continue
                    try:
                        if n_placeholders_list[ti] == 1:
                            prompt = tmpl.format(f"{f[0]}_{rotation}")
                        elif n_placeholders_list[ti] == 2:
                            prompt = tmpl.format(str(int(f[0]) + rotation), f[1])
                        elif n_placeholders_list[ti] == 4:
                            prompt = tmpl.format(str(int(f[0]) + rotation),
                                                  str(int(f[1]) + rotation),
                                                  f[2], f[3])
                        else:
                            continue
                    except (ValueError, IndexError):
                        continue
                    if prompt not in seen:
                        texts.append(prompt)
                        seen.add(prompt)
            rotation += 1

    # Mix in 50% general text to preserve baseline behavior
    mixed = texts[:]
    n_gen = min(len(GENERAL_TEXTS), len(texts))
    import random
    random.seed(42)
    mixed += random.sample(GENERAL_TEXTS, n_gen)
    random.shuffle(mixed)

    return mixed


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class SimpleTextDataset(Dataset):
    """Minimal text dataset for block training."""

    def __init__(self, texts, tokenizer, max_length=64):
        self.encodings = tokenizer(
            texts, truncation=True, padding="max_length",
            max_length=max_length, return_tensors="pt",
        )

    def __len__(self):
        return len(self.encodings.input_ids)

    def __getitem__(self, idx):
        return {
            "input_ids": self.encodings.input_ids[idx],
            "attention_mask": self.encodings.attention_mask[idx],
        }


# ---------------------------------------------------------------------------
# Fix/Break evaluation
# ---------------------------------------------------------------------------

@dataclass
class FixBreakMetrics:
    fixes: int = 0
    breaks: int = 0
    net: int = 0
    baseline_score: float = 0.0
    block_score: float = 0.0
    per_sample: dict = field(default_factory=dict)

    def print(self, label=""):
        print(f"  {label}  bl={self.baseline_score:.3f} bk={self.block_score:.3f} "
              f"fixes={self.fixes} brk={self.breaks} net={self.net}")


def evaluate_fix_break(backbone, injector, block_id, bench_prompts, max_tokens=64):
    """Evaluate fix/break impact of a single block vs baseline."""
    # Baseline (no blocks)
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

    injector.set_active_blocks([])

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
        fixes=fixes, breaks=breaks, net=fixes - breaks,
        baseline_score=bl_avg, block_score=bk_avg, per_sample=per_sample,
    )


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_block_large(
    backbone: BackboneModel,
    block: ParameterBlock,
    train_texts: list[str],
    epochs: int = 5,
    batch_size: int = 2,
    lr: float = 2e-4,
    max_length: int = 64,
    device: str = "cpu",
) -> list[float]:
    """Train a block on large data. Simple next-token prediction. No preservation tricks."""
    injector = BlockInjector(backbone)
    injector.inject_block(block, block.layer_id, block.module_name)

    dataset = SimpleTextDataset(train_texts, backbone.tokenizer, max_length=max_length)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.AdamW(block.parameters(), lr=lr)
    block.train()
    backbone.model.eval()

    loss_history = []
    print(f"\n  Training: {len(dataset)} samples, {epochs} epochs, lr={lr}")

    for epoch in range(epochs):
        epoch_loss = 0.0
        n_batches = 0
        pbar = tqdm(loader, desc=f"  Epoch {epoch+1}/{epochs}", leave=False)
        for batch in pbar:
            input_ids = batch["input_ids"].to(device)
            optimizer.zero_grad()
            outputs = backbone.model(input_ids=input_ids, labels=input_ids)
            loss = outputs.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(block.parameters(), max_norm=1.0)
            optimizer.step()
            epoch_loss += loss.item()
            n_batches += 1
            pbar.set_postfix({"loss": f"{loss.item():.3f}"})

        avg_loss = epoch_loss / max(n_batches, 1)
        loss_history.append(avg_loss)
        print(f"  Epoch {epoch+1}: loss={avg_loss:.3f}")

    injector.remove_all_patches()
    return loss_history


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="BitDPM v18 large-data block training")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--output-dir", type=str, default="experiments/outputs/blocks_v18")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--target-layer", type=int, default=23)
    parser.add_argument("--target-module", type=str, default="down_proj",
                        choices=["o_proj", "down_proj"])
    parser.add_argument("--num-prompts", type=int, default=5,
                        help="Number of prompts per template-fill combo (default: 5)")
    parser.add_argument("--max-length", type=int, default=64)
    parser.add_argument("--direction", type=str, default="power_log",
                        choices=list(REPAIR_DIRECTIONS.keys()),
                        help="Repair direction to train")
    parser.add_argument("--quick", action="store_true",
                        help="100 prompts, 3 epochs, 1 direction")
    args = parser.parse_args()

    device = args.device or (
        "mps" if torch.backends.mps.is_available() else
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    os.makedirs(args.output_dir, exist_ok=True)
    train_dtype = torch.float32

    print(f"BitDPM v18: Large-data block training")
    print(f"  Device:    {device}")
    print(f"  Model:     {args.model}")
    print(f"  Direction: {args.direction}")
    print(f"  Rank:      {args.rank}")
    print(f"  Layer:     {args.target_layer}/{args.target_module}")

    # Which directions to train
    directions = list(REPAIR_DIRECTIONS.keys()) if not args.quick else [args.direction]
    if args.quick:
        args.num_prompts = 2
        args.epochs = 3

    # Load backbone once
    backbone = BackboneModel(model_name=args.model, device=device, dtype=train_dtype)

    all_results = []

    for direction in directions:
        print(f"\n{'='*70}")
        print(f"Training: {direction}")
        print(f"{'='*70}")

        # 1. Generate training data
        train_texts = generate_training_texts(direction, num_augmented=args.num_prompts)
        print(f"  Generated {len(train_texts)} training prompts")

        if len(train_texts) < 10:
            print(f"  [Skip] Too few training prompts")
            continue

        # 2. Create block
        lin = backbone.get_linear_layer(args.target_layer, args.target_module)
        if lin is None:
            print(f"  [Skip] Layer {args.target_layer}/{args.target_module} not found")
            continue

        block_id = f"v18_{direction}_l{args.target_layer}_{args.target_module}_r{args.rank}"
        config = ParameterBlockConfig(
            block_id=block_id, layer_id=args.target_layer,
            module_name=args.target_module, rank=args.rank,
            scale=1.0, block_type=direction,
            hidden_size=backbone.hidden_size,
            in_features=lin.in_features, out_features=lin.out_features,
        )
        block = ParameterBlock(config)
        block = block.to(device=device, dtype=train_dtype)
        print(f"  Block: {block_id}, params={sum(p.numel() for p in block.parameters()):,}")

        # 3. Train
        loss_hist = train_block_large(
            backbone, block, train_texts,
            epochs=args.epochs, batch_size=2, lr=args.lr,
            max_length=args.max_length, device=device,
        )

        # 4. Evaluate fix/break
        print(f"\n  Evaluating fix/break on benchmark...")
        injector = BlockInjector(backbone)
        injector.inject_block(block, args.target_layer, args.target_module)

        fb = evaluate_fix_break(backbone, injector, block.block_id, BP, max_tokens=64)
        fb.print("Final:")

        injector.remove_all_patches()

        # 5. Admission decision
        unique_fixes = fb.fixes  # Simplified: count all fixes as unique
        net = fb.net
        admit = (unique_fixes >= 1) and (net >= 0)
        damage_rate = fb.breaks / max(len(BP.get("commonsense", []) +
                                           BP.get("math", []) +
                                           BP.get("code", []) +
                                           BP.get("chinese", []) +
                                           BP.get("reasoning", [])), 1)

        print(f"  Admission: unique_fixes={unique_fixes} net={net} "
              f"damage_rate={damage_rate:.1%} → {'ADMIT' if admit else 'REJECT'}")

        # 6. Save
        block_path = os.path.join(args.output_dir, f"{block_id}.pt")
        block.save(block_path)

        result = {
            "block_id": block_id,
            "direction": direction,
            "train_samples": len(train_texts),
            "rank": args.rank,
            "loss_history": loss_hist,
            "fix_break": {
                "fixes": fb.fixes, "breaks": fb.breaks, "net": fb.net,
                "baseline_score": fb.baseline_score,
                "block_score": fb.block_score,
            },
            "admit": admit,
            "damage_rate": damage_rate,
        }
        all_results.append(result)

        meta_path = os.path.join(args.output_dir, f"{block_id}_meta.json")
        with open(meta_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"  Saved: {block_path}")

    # Summary
    if all_results:
        print(f"\n{'='*70}")
        print("V18 TRAINING SUMMARY")
        print(f"{'='*70}")
        print(f"| {'Direction':<20} | {'Samples':<8} | {'Rank':<5} | {'Fixes':<6} | {'Breaks':<7} | {'Net':<4} | {'Admit':<6} |")
        print(f"|{'-'*22}|{'-'*10}|{'-'*7}|{'-'*8}|{'-'*9}|{'-'*6}|{'-'*8}|")
        for r in all_results:
            fb = r["fix_break"]
            admit_str = "ADMIT" if r["admit"] else "REJECT"
            print(f"| {r['direction']:<20} | {r['train_samples']:<8} | {r['rank']:<5} | "
                  f"{fb['fixes']:<6} | {fb['breaks']:<7} | {fb['net']:<4} | {admit_str:<6} |")

        # Summary JSON
        summary_path = os.path.join(args.output_dir, "v18_summary.json")
        with open(summary_path, "w") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n  Summary saved: {summary_path}")

    print(f"\nDone!")


if __name__ == "__main__":
    main()
