"""BitDPM v21: Large-Scale Deterministic Block Amplification.

Scales training data to 1000-2000 prompts/class, saves per-epoch checkpoints,
scans scales with greedy decoding, and reports deterministic fix/break metrics.

Usage:
    python scripts/train_v21_blocks.py
    python scripts/train_v21_blocks.py --direction percent
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from bitdpm.eval.benchmark import EVAL_PROMPTS as BP, compute_accuracy
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import ParameterBlock, ParameterBlockConfig

# ---------------------------------------------------------------------------
# Inherit the same REPAIR_DIRECTIONS and GENERAL_TEXTS from v18
# ---------------------------------------------------------------------------

REPAIR_DIRECTIONS = {
    "percent": {
        "templates": [
            "What is {}% of {}?",
            "Calculate {}% of {}",
            "Find {}% of {}",
            "What percent of {} is {}?",
            "A {}% increase of {} is what?",
            "A {}% decrease of {} is what?",
            "After a {}% discount, a ${} item costs what?",
            "With {}% tax on ${}, what is the total?",
            "If {} out of {} students passed, what percentage passed?",
            "{} percent of {} equals what?",
            "How much is {} percent of {}?",
            "What is {} percent off of {}?",
        ],
        "fill": [
            ("5", "200"), ("10", "50"), ("15", "300"), ("20", "100"),
            ("25", "80"), ("30", "150"), ("35", "400"), ("40", "250"),
            ("45", "60"), ("50", "500"), ("55", "200"), ("60", "350"),
            ("65", "80"), ("70", "120"), ("75", "40"), ("80", "90"),
            ("85", "200"), ("90", "300"), ("95", "100"), ("12", "250"),
            ("18", "500"), ("22", "75"), ("33", "600"), ("8", "125"),
            ("15", "200", "30"), ("25", "60", "15"),
            ("10", "350", ""), ("50", "120", ""),
        ],
    },
    "integer_ops": {
        "templates": [
            "What is {} + {}?", "Calculate {} + {}",
            "What is {} - {}?", "Calculate {} - {}",
            "What is {} * {}?", "Multiply {} by {}",
            "What is {} / {}?", "Divide {} by {}",
            "What is the remainder when {} is divided by {}?",
            "What is the GCD of {} and {}?",
            "What is the LCM of {} and {}?",
            "What is {} factorial?", "Calculate {}!",
            "What is the mean of {} and {}?",
            "What is the square root of {}?",
            "What is {} to the power of {}?",
            "What is 2 to the power of {}?",
            "What is log base 10 of {}?",
            "What is the absolute value of {}?",
        ],
        "fill": [
            ("15", "27"), ("34", "56"), ("128", "64"), ("256", "128"),
            ("1000", "500"), ("45", "35"), ("89", "11"), ("77", "33"),
            ("60", "45"), ("120", "80"), ("25", "18"), ("100", "37"),
            ("81", "9"), ("49", "14"), ("50", "4"), ("1000", "125"),
            ("12", "18"), ("24", "36"), ("7", "11"), ("15", "25"),
            ("8", "12"), ("30", "42"), ("9", "15"), ("144", ""),
            ("100", ""), ("169", ""), ("225", ""), ("400", ""),
            ("2", "10"), ("3", "5"), ("2", "8"), ("5", "4"),
            ("10", "3"), ("10", "4"), ("10", "6"),
            ("-5", ""), ("-12", ""), ("-100", ""),
        ],
    },
    "distance_geometry": {
        "templates": [
            "What is the distance between ({}, {}) and ({}, {})?",
            "Calculate the distance from ({}, {}) to ({}, {})",
            "What is the area of a circle with radius {}?",
            "Calculate the area of a circle with radius {}",
            "What is the circumference of a circle with radius {}?",
            "What is the area of a rectangle with length {} and width {}?",
            "What is the perimeter of a rectangle with length {} and width {}?",
            "What is the area of a triangle with base {} and height {}?",
            "What is the volume of a sphere with radius {}?",
            "What is the slope of the line through ({}, {}) and ({}, {})?",
            "What is the midpoint of ({}, {}) and ({}, {})?",
            "What is the hypotenuse of a right triangle with legs {} and {}?",
        ],
        "fill": [
            ("0", "0", "3", "4"), ("0", "0", "5", "12"), ("0", "0", "6", "8"),
            ("0", "0", "8", "15"), ("1", "2", "4", "6"), ("1", "1", "4", "5"),
            ("2", "3", "7", "15"), ("3", "7", "8", "12"), ("0", "0", "9", "40"),
            ("1", "", "", ""), ("2", "", "", ""), ("3", "", "", ""),
            ("5", "", "", ""), ("7", "", "", ""), ("10", "", "", ""),
            ("3", "4", "", ""), ("6", "8", "", ""), ("9", "12", "", ""),
            ("3", "", "", ""), ("5", "", "", ""), ("7", "", "", ""),
            ("1", "2", "3", "4"), ("0", "0", "12", "16"),
            ("0", "0", "7", "24"), ("0", "0", "15", "8"),
            ("1", "3", "6", "11"), ("2", "5", "10", "13"),
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
            "How many centimeters are in a meter?",
            "How many meters are in a kilometer?",
            "What is the value of pi?",
            "What is the value of e?",
            "What is the atomic number of carbon?",
            "What is the atomic number of oxygen?",
            "What is the atomic number of hydrogen?",
            "What is the chemical formula for water?",
            "What year did World War II end?",
            "What year did the Berlin Wall fall?",
            "When was the United Nations founded?",
            "What is the largest planet in the solar system?",
            "What is the most abundant gas in Earth's atmosphere?",
            "What is normal human body temperature in Celsius?",
            "How many bones are in the adult human body?",
        ],
        "fill": [],
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
            "Which is the fastest land animal?",
            "Which is the largest animal in the world?",
            "What planet is known as the Red Planet?",
            "What is the chemical symbol for gold?",
            "What is the chemical symbol for iron?",
            "Who was the first person on the Moon?",
            "Who wrote Hamlet?",
            "Who was the first president of the United States?",
            "Which country has the largest population?",
            "Which country has the largest area?",
            "What is the currency of Japan?",
            "What is the currency of the United Kingdom?",
            "How many legs does a spider have?",
            "How many teeth does an adult human have?",
            "What is the smallest planet in our solar system?",
            "Who invented the light bulb?",
            "What did Marie Curie discover?",
            "When did World War I begin?",
        ],
        "fill": [],
    },
}

GENERAL_TEXTS = [
    "The capital of France is Paris.",
    "Water boils at 100 degrees Celsius.",
    "The Pacific Ocean is the largest ocean on Earth.",
    "Python is a high-level programming language.",
    "A function is a reusable block of code.",
    "The Earth orbits the Sun once every 365.25 days.",
    "DNA contains genetic information.",
    "The chemical symbol for water is H2O.",
    "Sound travels faster in water than in air.",
    "The atomic number of carbon is 6.",
    "The sum of angles in a triangle is 180 degrees.",
    "Multiplication is repeated addition.",
    "A magnet has a north pole and a south pole.",
    "Electricity flows through conductive materials.",
    "The Moon orbits the Earth approximately every 27 days.",
    "Photosynthesis converts sunlight into chemical energy.",
    "Gravity is a force that attracts objects toward each other.",
    "The human body has 206 bones.",
    "Shakespeare wrote many famous plays and sonnets.",
    "The Renaissance was a period of cultural rebirth in Europe.",
]


def generate_training_texts(direction: str, target: int = 1500) -> list[str]:
    """Generate training texts for a direction, up to target count, with 50% general mix."""
    dir_data = REPAIR_DIRECTIONS.get(direction)
    if dir_data is None:
        return []

    templates = dir_data["templates"]
    fills = dir_data.get("fill", [])
    texts, seen = [], set()

    # Step 1: all template-fill combinations
    for tmpl in templates:
        n_ph = tmpl.count("{}")
        if n_ph == 0:
            if tmpl not in seen:
                texts.append(tmpl); seen.add(tmpl)
            continue
        for fill in fills:
            if len(fill) < n_ph:
                continue
            try:
                if n_ph == 1:
                    prompt = tmpl.format(fill[0])
                elif n_ph == 2:
                    prompt = tmpl.format(fill[0], fill[1])
                elif n_ph == 4:
                    prompt = tmpl.format(fill[0], fill[1], fill[2], fill[3])
                else:
                    continue
            except (IndexError, KeyError, ValueError):
                continue
            if prompt not in seen:
                texts.append(prompt); seen.add(prompt)

    # Step 2: rotate to reach target
    if len(texts) < target and fills:
        for rot in range(1, 50):
            if len(texts) >= target:
                break
            for tmpl in templates:
                n_ph = tmpl.count("{}")
                if n_ph == 0:
                    continue
                for fill in fills:
                    if len(texts) >= target:
                        break
                    if len(fill) < n_ph:
                        continue
                    try:
                        if n_ph == 1:
                            prompt = tmpl.format(f"{fill[0]}_{rot}")
                        elif n_ph == 2:
                            prompt = tmpl.format(str(int(fill[0]) + rot), fill[1])
                        elif n_ph == 4:
                            prompt = tmpl.format(str(int(fill[0]) + rot),
                                                  str(int(fill[1]) + rot),
                                                  fill[2], fill[3])
                        else:
                            continue
                    except (ValueError, IndexError):
                        continue
                    if prompt not in seen:
                        texts.append(prompt); seen.add(prompt)

    # Step 3: 50% general mix
    import random; random.seed(42)
    n_gen = min(len(GENERAL_TEXTS), len(texts))
    mixed = texts[:] + random.sample(GENERAL_TEXTS, n_gen)
    random.shuffle(mixed)
    return mixed


class SimpleTextDataset(Dataset):
    def __init__(self, texts, tokenizer, max_length=64):
        self.enc = tokenizer(texts, truncation=True, padding="max_length",
                             max_length=max_length, return_tensors="pt")

    def __len__(self):
        return len(self.enc.input_ids)

    def __getitem__(self, idx):
        return {"input_ids": self.enc.input_ids[idx],
                "attention_mask": self.enc.attention_mask[idx]}


def evaluate_deterministic(backbone, injector, block_id=None, bench=BP, max_tokens=64):
    """Evaluate with greedy decoding (do_sample=False). Returns (avg_score, fixes, breaks)."""
    if block_id:
        injector.set_active_blocks([block_id])
    else:
        injector.set_active_blocks([])

    scores = {}
    for cat, prompts in bench.items():
        for p in prompts:
            g = backbone.generate(p, max_new_tokens=max_tokens, do_sample=False)
            scores[p] = compute_accuracy(p, g, cat)
    return scores


def compute_fb(baseline, block_scores):
    fixes = breaks = 0
    for p in baseline:
        if block_scores[p] > baseline[p]: fixes += 1
        elif block_scores[p] < baseline[p]: breaks += 1
    return fixes, breaks


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_v21(backbone, block, train_texts, epochs=10, lr=2e-4, device="mps",
              output_dir=None, block_id=None):
    """Train with per-epoch checkpointing."""
    injector = BlockInjector(backbone)
    injector.inject_block(block, block.layer_id, block.module_name)

    dataset = SimpleTextDataset(train_texts, backbone.tokenizer, max_length=64)
    loader = DataLoader(dataset, batch_size=2, shuffle=True)
    optimizer = torch.optim.AdamW(block.parameters(), lr=lr)
    block.train()
    backbone.model.eval()

    history = []
    print(f"\n  Training: {len(dataset)} samples, {epochs} epochs")

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

        avg = epoch_loss / max(n_batches, 1)
        history.append(avg)
        print(f"  Epoch {epoch+1}: loss={avg:.3f}")

        # Save checkpoint
        if output_dir and block_id:
            ckpt_path = os.path.join(output_dir, f"{block_id}_ep{epoch+1}.pt")
            block.save(ckpt_path)

    injector.remove_all_patches()
    return history


def scale_scan_deterministic(backbone, block, scales, bench=BP, max_tokens=64):
    """Scan multiple scales with greedy decoding. Returns list of (scale, fixes, breaks, avg)."""
    # Baseline
    inj = BlockInjector(backbone)
    inj.inject_block(block, block.layer_id, block.module_name)
    baseline = evaluate_deterministic(backbone, inj, block_id=None, bench=bench, max_tokens=max_tokens)
    inj.remove_all_patches()

    results = []
    for scale in scales:
        block.scale = scale
        inj2 = BlockInjector(backbone)
        inj2.inject_block(block, block.layer_id, block.module_name)
        block_scores = evaluate_deterministic(backbone, inj2, block_id=block.block_id,
                                               bench=bench, max_tokens=max_tokens)
        inj2.remove_all_patches()

        fixes, breaks = compute_fb(baseline, block_scores)
        avg = sum(block_scores.values()) / max(len(block_scores), 1)
        results.append({"scale": scale, "avg": avg, "fixes": fixes, "breaks": breaks, "net": fixes - breaks})
        print(f"    scale={scale:.3f}  avg={avg:.3f}  fixes={fixes}  breaks={breaks}  net={fixes-breaks}")

    return baseline, results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="BitDPM v21 large-scale deterministic block training")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--output-dir", type=str, default="experiments/outputs/blocks_v21")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--direction", type=str, default="percent",
                        choices=list(REPAIR_DIRECTIONS.keys()))
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--target-layer", type=int, default=23)
    parser.add_argument("--target-module", type=str, default="down_proj",
                        choices=["o_proj", "down_proj"])
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--target-samples", type=int, default=1500)
    parser.add_argument("--max-length", type=int, default=64)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    device = args.device or ("mps" if torch.backends.mps.is_available() else "cpu")
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"BitDPM v21: {args.direction} ({args.rank}, {args.epochs} epochs, {args.target_samples} samples)")
    print(f"  Device: {device}")

    backbone = BackboneModel(model_name=args.model, device=device, dtype=torch.float32)

    # Generate data
    train_texts = generate_training_texts(args.direction, target=args.target_samples)
    print(f"  Training texts: {len(train_texts)}")

    # Create block
    lin = backbone.get_linear_layer(args.target_layer, args.target_module)
    block_id = f"v21_{args.direction}_l{args.target_layer}_{args.target_module}_r{args.rank}"
    config = ParameterBlockConfig(
        block_id=block_id, layer_id=args.target_layer,
        module_name=args.target_module, rank=args.rank,
        scale=1.0, block_type=args.direction,
        hidden_size=backbone.hidden_size,
        in_features=lin.in_features, out_features=lin.out_features,
    )
    block = ParameterBlock(config).to(device=device, dtype=torch.float32)
    print(f"  Block: {block_id}, params={sum(p.numel() for p in block.parameters()):,}")

    # Train
    loss_hist = train_v21(backbone, block, train_texts, epochs=args.epochs,
                          lr=args.lr, device=device,
                          output_dir=args.output_dir, block_id=block_id)

    # Save final block
    final_path = os.path.join(args.output_dir, f"{block_id}_final.pt")
    block.save(final_path)
    print(f"  Saved final: {final_path}")

    # Scale scan with deterministic evaluation
    scales = [0.03, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50]
    print(f"\n  Scale scan (do_sample=False, {len(scales)} scales):")
    baseline, scan = scale_scan_deterministic(backbone, block, scales, bench=BP, max_tokens=64)
    bl_avg = sum(baseline.values()) / max(len(baseline), 1)
    print(f"  Baseline: {bl_avg:.3f}")

    # Find best
    best = max(scan, key=lambda r: (r["net"], r["fixes"]))
    print(f"\n  Best: scale={best['scale']}, fixes={best['fixes']}, breaks={best['breaks']}, net={best['net']}")

    # Save report
    result = {
        "block_id": block_id,
        "direction": args.direction,
        "train_samples": len(train_texts),
        "rank": args.rank,
        "epochs": args.epochs,
        "loss_history": loss_hist,
        "baseline": bl_avg,
        "scale_scan": scan,
        "best": best,
    }
    report_path = os.path.join(args.output_dir, f"{block_id}_report.json")
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"  Report: {report_path}")
    print(f"\nDone!")


if __name__ == "__main__":
    main()
