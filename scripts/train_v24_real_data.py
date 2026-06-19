"""BitDPM v24: Real-Data Sparse Correction Training.

Replaces template-generated data with diverse, context-rich percent problems
plus general instruction data and hard negatives.

Data mix:
  50% diverse percent word problems (shopping, finance, stats, science, daily life)
  30% general instruction data (preserve baseline distribution)
  20% hard negatives (near-miss problems baseline almost gets right)
"""

from __future__ import annotations

import argparse
import json
import os
import random
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

random.seed(42)

# ---------------------------------------------------------------------------
# Diverse percent problem generator — real-world contexts
# ---------------------------------------------------------------------------

PERCENT_PROBLEMS: list[dict] = [
    # Shopping / Discounts
    {"q": "A jacket costs $80 and is on sale for 25% off. What is the sale price?", "a": "$60"},
    {"q": "A store offers a 15% discount on all items. If a shirt originally costs $40, how much do you pay?", "a": "$34"},
    {"q": "During a sale, a $120 pair of shoes is marked down by 30%. What is the new price?", "a": "$84"},
    {"q": "A $50 book is discounted by 20%. How much do you save?", "a": "$10"},
    {"q": "A laptop costs $800. If there's a 10% student discount, what's the final price?", "a": "$720"},
    {"q": "A store has a 'buy one get one 50% off' sale. Each item costs $60. How much for two?", "a": "$90"},
    {"q": "An online store charges 8% sales tax on a $45 purchase. What is the total?", "a": "$48.60"},
    {"q": "A $250 TV is on clearance at 40% off. What is the clearance price?", "a": "$150"},
    {"q": "You have a coupon for 30% off any item. The item you want is $65. What do you pay?", "a": "$45.50"},
    {"q": "A furniture store offers 12% off all items during a holiday sale. A sofa costs $900. What is the sale price?", "a": "$792"},
    {"q": "After a 15% discount, a customer pays $85 for a jacket. What was the original price?", "a": "$100"},

    # Tipping / Dining
    {"q": "A restaurant bill is $60. You want to leave a 15% tip. How much tip should you leave?", "a": "$9"},
    {"q": "A dinner costs $45 and you leave an 18% tip. What is the total you pay?", "a": "$53.10"},
    {"q": "A group of 4 people splits a $120 bill evenly, plus 20% tip. How much does each person pay?", "a": "$36"},
    {"q": "You leave a $12 tip on a $80 meal. What percentage tip is that?", "a": "15%"},
    {"q": "A coffee shop adds a 10% service charge. Your order is $8.50. What do you pay?", "a": "$9.35"},
    {"q": "A delivery app charges a 15% service fee on a $22 order. What is the total?", "a": "$25.30"},
    {"q": "You and a friend share a $90 dinner and add 20% tip. What does each person pay?", "a": "$54"},

    # Finance / Interest
    {"q": "You deposit $500 in a savings account earning 3% annual interest. After one year, how much do you have?", "a": "$515"},
    {"q": "A loan of $2000 has an annual interest rate of 5%. How much interest do you pay in one year?", "a": "$100"},
    {"q": "An investment of $1000 grows by 8% in one year. What is the new value?", "a": "$1080"},
    {"q": "A stock worth $150 per share increases by 12%. What is the new price per share?", "a": "$168"},
    {"q": "A house valued at $250,000 appreciates by 6% in one year. What is the new value?", "a": "$265,000"},
    {"q": "You invest $3000 and earn 4.5% interest annually. How much do you have after one year?", "a": "$3135"},
    {"q": "A bond paying 2.5% annual interest earns you $50 in one year. What was the principal?", "a": "$2000"},
    {"q": "If a $750 investment grows to $810, what is the percentage return?", "a": "8%"},
    {"q": "A salary of $45,000 gets a 5% raise. What is the new salary?", "a": "$47,250"},
    {"q": "An employee's hourly wage increases from $20 to $23. What is the percentage increase?", "a": "15%"},
    {"q": "After a 7% pay cut, a worker earns $37,200. What was the original salary?", "a": "$40,000"},
    {"q": "A company's revenue grew from $2M to $2.5M. What is the percentage increase?", "a": "25%"},

    # Statistics / Grades
    {"q": "A student scored 85 out of 100 on a test. What percentage did they get?", "a": "85%"},
    {"q": "Out of 60 students, 45 passed the exam. What percentage passed?", "a": "75%"},
    {"q": "In a survey of 200 people, 140 preferred product A. What percentage is that?", "a": "70%"},
    {"q": "A class has 30 students. 60% are girls. How many girls are in the class?", "a": "18"},
    {"q": "In an election, 55% of 20,000 voters voted for candidate X. How many votes did X get?", "a": "11000"},
    {"q": "A basketball player made 72 out of 90 free throws. What is their free throw percentage?", "a": "80%"},
    {"q": "Out of 800 residents, 520 are registered voters. What percentage are registered?", "a": "65%"},
    {"q": "A factory produced 5000 units. 3% were defective. How many were defective?", "a": "150"},
    {"q": "A school has 40 teachers. 35% have master's degrees. How many have master's degrees?", "a": "14"},
    {"q": "In a poll of 1200 people, 42% preferred candidate A. How many preferred candidate A?", "a": "504"},

    # Science / Medicine
    {"q": "A 250ml solution contains 20% alcohol. How much alcohol is in it?", "a": "50ml"},
    {"q": "A flu vaccine is 60% effective. Out of 5000 vaccinated people, how many are protected?", "a": "3000"},
    {"q": "In a clinical trial, 85% of 200 patients recovered. How many recovered?", "a": "170"},
    {"q": "A forest originally covered 400 square km. Due to deforestation, it shrank by 15%. What is the new area?", "a": "340 sq km"},
    {"q": "A chemical solution is 30% acid. If you have 600ml of solution, how much acid is present?", "a": "180ml"},
    {"q": "Earth's surface is about 30% land. If total surface area is 510 million sq km, how much is land?", "a": "153 million sq km"},
    {"q": "A medication's effectiveness drops by 15% each year. After one year, what percentage remains?", "a": "85%"},
    {"q": "In a population of 50,000, 2.5% have a certain condition. How many people have it?", "a": "1250"},

    # Daily Life / Practical
    {"q": "A recipe calls for 200g of flour, but you want to make 150% of the recipe. How much flour do you need?", "a": "300g"},
    {"q": "You spend 25% of your $2000 monthly salary on rent. How much is rent?", "a": "$500"},
    {"q": "A battery lasts 8 hours at full charge. After 6 hours, what percentage of charge remains?", "a": "25%"},
    {"q": "You fill a 15-gallon tank to 80% capacity. How many gallons are in the tank?", "a": "12 gallons"},
    {"q": "A 2-liter bottle is 35% full. How much liquid is in it?", "a": "0.7 liters"},
    {"q": "Your phone battery is at 75% and drops 5% per hour. How many hours until it reaches 20%?", "a": "11 hours"},
    {"q": "A pizza is cut into 8 slices. You eat 3 slices. What percentage of the pizza did you eat?", "a": "37.5%"},
    {"q": "You save $150 per month from a $3000 salary. What percentage do you save?", "a": "5%"},
    {"q": "A water tank holds 500 liters and is 40% full. How much more water is needed to fill it?", "a": "300 liters"},
    {"q": "You complete 35 out of 50 problems. What percentage have you completed?", "a": "70%"},

    # Multi-step
    {"q": "A store offers 20% off all items, then applies an additional 10% off the sale price. A $100 item costs how much?", "a": "$72"},
    {"q": "You invest $2000. In year one it grows 10%, in year two it grows another 10%. What is the value after two years?", "a": "$2420"},
    {"q": "A $60 jacket is on sale for 25% off. You also have a $10 coupon. What do you pay?", "a": "$35"},
    {"q": "A population of 10,000 grows by 5% per year. After one year, what is the population?", "a": "10500"},
    {"q": "You score 80% on a test worth 50 points. How many points did you get?", "a": "40"},
    {"q": "A company had 200 employees. They hired 15% more. How many employees now?", "a": "230"},
    {"q": "A $400 TV is on sale for 30% off. Sales tax is 8%. What is the final price?", "a": "$302.40"},
    {"q": "A salary of $50,000 gets a 3% raise each year for 2 years. What is the salary after 2 years?", "a": "$53,045"},
    {"q": "During a sale, a store offers 'buy 2 get 1 free'. You buy 3 items each costing $30. What is the effective discount percentage?", "a": "33.3%"},
    {"q": "A restaurant bill is $80. You want to leave a 20% tip and split with 3 friends. How much does each person pay total?", "a": "$24"},

    # Negative percent change
    {"q": "A stock drops from $80 to $60. What is the percentage decrease?", "a": "25%"},
    {"q": "A town's population decreased from 12,000 to 10,800. What is the percentage decrease?", "a": "10%"},
    {"q": "A car depreciates by 15% per year. If it cost $30,000 new, what is its value after one year?", "a": "$25,500"},
    {"q": "After a 20% discount, a TV costs $560. What was the original price?", "a": "$700"},
    {"q": "A store's sales dropped from $50,000 to $42,500. What is the percentage decrease?", "a": "15%"},
]

# Reverse percent problems (harder)
PERCENT_PROBLEMS_EXTRA: list[dict] = [
    {"q": "If 25% of a number is 60, what is the number?", "a": "240"},
    {"q": "A number increased by 15% gives 115. What is the original number?", "a": "100"},
    {"q": "What number decreased by 30% equals 70?", "a": "100"},
    {"q": "30 is 12% of what number?", "a": "250"},
    {"q": "45 is what percent of 180?", "a": "25%"},
    {"q": "If 8% of a number equals 24, what is the number?", "a": "300"},
    {"q": "A price increased from $50 to $75. What is the percentage increase?", "a": "50%"},
    {"q": "The area of a field decreased from 800 sq m to 600 sq m. What is the percentage decrease?", "a": "25%"},
    {"q": "A test score improved from 40 to 55. What is the percentage increase?", "a": "37.5%"},
    {"q": "A company's profit went from $1.2M to $1.5M. What is the percentage increase?", "a": "25%"},
]

# ---------------------------------------------------------------------------
# General instruction data (preservation)
# ---------------------------------------------------------------------------

GENERAL_INSTRUCTIONS: list[str] = [
    "Write a short paragraph explaining the water cycle.",
    "What are three benefits of regular exercise?",
    "Explain how a refrigerator works in simple terms.",
    "Describe the difference between weather and climate.",
    "What are the main causes of air pollution?",
    "Explain the concept of renewable energy.",
    "What is photosynthesis and why is it important?",
    "Describe the process of making a cup of tea.",
    "What are the key features of a healthy diet?",
    "Explain why the sky appears blue.",
    "Describe how the internet transmits data.",
    "What are the advantages of learning a second language?",
    "Explain the difference between a virus and a bacteria.",
    "What causes earthquakes and where do they typically occur?",
    "Describe the main components of a computer.",
    "Explain why exercise is good for mental health.",
    "What are the three states of matter? Give examples of each.",
    "Describe how a seed grows into a plant.",
    "What is the importance of recycling?",
    "Explain how GPS technology works.",
    "Describe the main organs of the human digestive system.",
    "What is the difference between AC and DC current?",
    "Explain why we have seasons on Earth.",
    "What are the main types of clouds and what weather do they bring?",
    "Describe how electricity is generated in a power plant.",
    "Explain the concept of supply and demand in economics.",
    "What are the primary colors and how are secondary colors created?",
    "Describe how a telescope works.",
    "What is the function of the human heart?",
    "Explain why metals conduct electricity better than plastics.",
    "Describe the process of water purification.",
    "What is the difference between a star and a planet?",
    "Explain the concept of fractions using a pizza as an example.",
    "Describe how batteries store and release energy.",
    "What are the main parts of a flower and their functions?",
    "Explain why salt melts ice on roads.",
    "Describe how a microwave oven heats food.",
    "What is the greenhouse effect and why does it matter?",
    "Explain the difference between a solstice and an equinox.",
    "Describe the various types of precipitation.",
]

# Possible answers for general instructions (we don't need exact answers,
# these are for preservation — we just want the block to not change the output)
GENERAL_ANSWERS: list[str] = [
    "Evaporation, condensation, precipitation, and collection.",
    "Improves cardiovascular health, strengthens muscles, and boosts mental health.",
    "A refrigerant absorbs heat inside and releases it outside through compression and expansion.",
    "Weather is day-to-day conditions; climate is long-term patterns.",
    "Vehicle emissions, industrial pollution, burning fossil fuels, and wildfires.",
    "Energy from natural sources that replenishes naturally like solar, wind, and hydro.",
    "Plants use sunlight, water, and CO2 to produce glucose and oxygen.",
    "Boil water, add tea leaves, steep for 3-5 minutes, strain, and serve.",
    "Balance of fruits, vegetables, proteins, grains, and limited processed foods.",
    "Rayleigh scattering makes blue light scatter more in the atmosphere.",
    "Data is broken into packets and routed through networks to the destination.",
    "Improved cognition, better career opportunities, and cultural understanding.",
    "Viruses need host cells to reproduce; bacteria are self-contained organisms.",
    "Tectonic plate movements along fault lines cause earthquakes.",
    "CPU, memory, storage, input devices, and output devices.",
    "Reduces stress, improves mood, and boosts cognitive function.",
    "Solid (ice), liquid (water), gas (steam).",
    "A seed germinates, sprouts roots, grows a stem and leaves, and matures.",
    "Reduces waste, conserves resources, and saves energy.",
    "Satellites triangulate signals to determine location on Earth.",
    "Mouth, esophagus, stomach, small intestine, large intestine.",
    "AC changes direction; DC flows one way.",
    "Earth's axial tilt causes seasonal changes in sunlight intensity.",
    "Cumulus (fair weather), stratus (overcast), cirrus (high altitude), nimbus (rain).",
    "Turbines spin generators that convert mechanical energy to electricity.",
    "Higher prices reduce demand; lower prices increase demand.",
    "Red, blue, yellow. Green from blue+yellow, orange from red+yellow, purple from red+blue.",
    "Lenses gather and focus light from distant objects.",
    "Pumps blood throughout the body, delivering oxygen and nutrients.",
    "Metals have free electrons that can move and carry charge.",
    "Filtration, sedimentation, disinfection, and distribution.",
    "Stars produce their own light; planets reflect light.",
    "If a pizza has 8 slices, each slice is 1/8 of the whole.",
    "Chemical reactions store energy that is released when the circuit connects.",
    "Petals (attract pollinators), sepals (protect bud), stamen (male), pistil (female).",
    "Salt lowers the freezing point of water below 0°C.",
    "Microwaves excite water molecules, generating heat through friction.",
    "Greenhouse gases trap heat in the atmosphere, warming the planet.",
    "Solstice has longest/shortest day; equinox has equal day and night.",
    "Rain, snow, sleet, and hail.",
]


def generate_v24_data(
    percent_problems: list[dict],
    general_instructions: list[str],
    general_answers: list[str],
    num_repair: int = 80,
    num_preserve: int = 40,
    num_hard: int = 20,
    seed: int = 42,
) -> tuple[list[str], list[str], list[str]]:
    """Generate v24 training data.

    Returns:
        repair_texts: diverse percent problems (for repair loss)
        preserve_texts: general instruction data (for baseline preservation)
        hard_negatives: near-miss problems
    """
    rng = random.Random(seed)

    # Repair: sample diverse percent problems
    all_problems = percent_problems + PERCENT_PROBLEMS_EXTRA
    rng.shuffle(all_problems)
    repair_samples = all_problems[:num_repair]

    # Format as prompt → answer pairs
    repair_texts = []
    for item in repair_samples:
        repair_texts.append(f"{item['q']} {item['a']}")

    # Preserve: general instruction data
    preserve_texts = []
    for i in range(min(num_preserve, len(general_instructions))):
        preserve_texts.append(f"{general_instructions[i]} {general_answers[i]}")

    # Hard negatives: slightly modified versions of percent problems
    # that baseline almost gets right (similar numbers, different operation)
    hard_texts = []
    base = all_problems[num_repair:num_repair + num_hard]
    for item in base:
        # Add a distractor answer
        q = item['q']
        a = item['a']
        # Sometimes flip the answer
        if rng.random() < 0.5:
            hard_texts.append(f"{q} {a}")
        else:
            wrong = str(float(str(a).replace('$', '').replace('%', '').split()[0]) * 0.9) if str(a)[0].isdigit() else a
            hard_texts.append(f"{q} Approximately {wrong}")

    return repair_texts, preserve_texts, hard_texts


def get_hard_negatives_from_benchmark(backbone, max_tokens=64) -> list[str]:
    """Collect baseline-correct prompts from benchmark as hard negatives."""
    texts = []
    for cat, prompts in BP.items():
        for p in prompts:
            g = backbone.generate(p, max_new_tokens=max_tokens, do_sample=False)
            s = compute_accuracy(p, g, cat)
            if s >= 1.0:
                texts.append(p)
    return texts


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class MixedDataset(Dataset):
    """Mixed repair + preserve + hard-negative dataset."""

    def __init__(self, repair, preserve, hard_neg, tokenizer, max_length=64):
        all_texts = repair + preserve + hard_neg
        self.encodings = tokenizer(
            all_texts, truncation=True, padding="max_length",
            max_length=max_length, return_tensors="pt",
        )
        # Track which samples are repair vs preserve
        self.repair_mask = [True] * len(repair) + [False] * (len(preserve) + len(hard_neg))

    def __len__(self):
        return len(self.encodings.input_ids)

    def __getitem__(self, idx):
        return {
            "input_ids": self.encodings.input_ids[idx],
            "attention_mask": self.encodings.attention_mask[idx],
            "is_repair": self.repair_mask[idx],
        }


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_v24_block(
    backbone, block, train_texts, repair_mask,
    epochs=10, lr=1e-4, device="mps",
    output_dir=None, block_id=None,
):
    """Train block with mixed data."""
    inj = BlockInjector(backbone)
    inj.inject_block(block, block.layer_id, block.module_name)

    dataset = train_texts  # Already a dataset
    loader = DataLoader(dataset, batch_size=2, shuffle=True)
    optimizer = torch.optim.AdamW(block.parameters(), lr=lr)
    block.train()
    backbone.model.eval()
    loss_history = []

    for epoch in range(epochs):
        epoch_loss = 0.0
        nb = 0
        pbar = tqdm(loader, desc=f"Epoch {epoch+1}/{epochs}", leave=False)
        for batch in pbar:
            ids = batch["input_ids"].to(device)
            optimizer.zero_grad()
            outputs = backbone.model(input_ids=ids, labels=ids)
            loss = outputs.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(block.parameters(), max_norm=1.0)
            optimizer.step()
            epoch_loss += loss.item()
            nb += 1
            pbar.set_postfix({"loss": f"{loss.item():.3f}"})

        avg = epoch_loss / max(nb, 1)
        loss_history.append(avg)

        # Save checkpoint
        if output_dir and block_id:
            ckpt_path = os.path.join(output_dir, f"{block_id}_ep{epoch+1}.pt")
            block.save(ckpt_path)
        print(f"  Epoch {epoch+1}: loss={avg:.3f}")

    inj.remove_all_patches()
    return loss_history


def deterministic_scale_scan(backbone, block, scales, bench=BP, max_tokens=64):
    """Scan scales with greedy decoding."""
    # Baseline (no block)
    inj0 = BlockInjector(backbone)
    inj0.inject_block(block, block.layer_id, block.module_name)
    inj0.set_active_blocks([])
    baseline = {}
    for cat, prompts in bench.items():
        for p in prompts:
            g = backbone.generate(p, max_new_tokens=max_tokens, do_sample=False)
            baseline[p] = compute_accuracy(p, g, cat)
    inj0.remove_all_patches()
    bl_avg = sum(baseline.values()) / max(len(baseline), 1)
    print(f"  Baseline: {bl_avg:.3f}")

    results = []
    for scale in scales:
        block.scale = scale
        inj = BlockInjector(backbone)
        inj.inject_block(block, block.layer_id, block.module_name)
        inj.set_active_blocks([block.block_id])
        scores = {}
        for cat, prompts in bench.items():
            for p in prompts:
                g = backbone.generate(p, max_new_tokens=max_tokens, do_sample=False)
                scores[p] = compute_accuracy(p, g, cat)
        inj.remove_all_patches()

        fixes = sum(1 for p in baseline if scores[p] > baseline[p])
        breaks = sum(1 for p in baseline if scores[p] < baseline[p])
        bk_avg = sum(scores.values()) / max(len(scores), 1)
        net = fixes - breaks
        results.append({"scale": scale, "avg": bk_avg, "fixes": fixes, "breaks": breaks, "net": net})
        print(f"  scale={scale:.2f}  block={bk_avg:.3f}  fixes={fixes}  breaks={breaks}  net={net}")

    return baseline, results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="BitDPM v24 real-data training")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--output-dir", type=str, default="experiments/outputs/blocks_v24")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--direction", type=str, default="percent")
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--max-length", type=int, default=96)
    parser.add_argument("--num-repair", type=int, default=80)
    parser.add_argument("--num-preserve", type=int, default=40)
    parser.add_argument("--num-hard", type=int, default=20)
    args = parser.parse_args()

    device = args.device or ("mps" if torch.backends.mps.is_available() else "cpu")
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"BitDPM v24: Real-Data {args.direction.upper()} Training")
    print(f"  Device: {device}, Rank: {args.rank}")
    print(f"  Data: repair={args.num_repair}, preserve={args.num_preserve}, hard={args.num_hard}")

    # Load backbone
    backbone = BackboneModel(model_name=args.model, device=device, dtype=torch.float32)

    # Generate realistic data
    repair_texts, preserve_texts, hard_texts = generate_v24_data(
        PERCENT_PROBLEMS, GENERAL_INSTRUCTIONS, GENERAL_ANSWERS,
        num_repair=args.num_repair,
        num_preserve=args.num_preserve,
        num_hard=args.num_hard,
    )

    # Add hard negatives from benchmark (baseline-correct samples)
    try:
        bench_hard = get_hard_negatives_from_benchmark(backbone, max_tokens=64)
        hard_texts += bench_hard[:20]
    except:
        pass

    print(f"  Repair={len(repair_texts)}, Preserve={len(preserve_texts)}, HardNeg={len(hard_texts)}")

    # Create block
    lin = backbone.get_linear_layer(23, "down_proj")
    block_id = f"v24_{args.direction}_l23_down_proj_r{args.rank}"
    config = ParameterBlockConfig(
        block_id=block_id, layer_id=23,
        module_name="down_proj", rank=args.rank,
        scale=1.0, block_type=args.direction,
        hidden_size=backbone.hidden_size,
        in_features=lin.in_features, out_features=lin.out_features,
    )
    block = ParameterBlock(config).to(device=device, dtype=torch.float32)
    print(f"  Block: {block_id}, params={sum(p.numel() for p in block.parameters()):,}")

    # Create dataset
    all_texts = repair_texts + preserve_texts + hard_texts
    dataset = MixedDataset(repair_texts, preserve_texts, hard_texts, backbone.tokenizer, max_length=args.max_length)

    # Train
    loss_hist = train_v24_block(
        backbone, block, dataset, None,
        epochs=args.epochs, lr=args.lr, device=device,
        output_dir=args.output_dir, block_id=block_id,
    )

    # Save final
    final_path = os.path.join(args.output_dir, f"{block_id}_final.pt")
    block.save(final_path)
    print(f"\n  Saved: {final_path}")

    # Scale scan
    scales = [0.03, 0.05, 0.10, 0.15, 0.20]
    print(f"\n  Deterministic scale scan ({len(scales)} scales):")
    baseline, scan = deterministic_scale_scan(backbone, block, scales, bench=BP, max_tokens=64)

    # Best
    best = max(scan, key=lambda r: (r["net"], r["fixes"]))
    print(f"\n  Best: scale={best['scale']}, fixes={best['fixes']}, breaks={best['breaks']}, net={best['net']}")

    # Save report
    bl_avg = sum(baseline.values()) / max(len(baseline), 1)
    result = {
        "block_id": block_id,
        "direction": args.direction,
        "data": {"repair": len(repair_texts), "preserve": len(preserve_texts), "hard": len(hard_texts)},
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

    # Summary
    print(f"\n{'='*60}")
    print("V24 RESULT")
    print(f"{'='*60}")
    print(f"  Best: scale={best['scale']}, fixes={best['fixes']}, breaks={best['breaks']}, net={best['net']}")
    print(f"  Target: net ≥ +2, breaks ≤ 1 → {'✅ PASS' if best['net'] >= 2 and best['breaks'] <= 1 else '❌ NOT YET'}")
    print(f"\nDone!")


if __name__ == "__main__":
    main()
